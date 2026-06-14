import requests
from bs4 import BeautifulSoup
import json
import os
import logging
import re

logger = logging.getLogger(__name__)

class BaseScraper:
    """
    Base class for all MEDINT scrapers.
    Provides common functionality like HTML fetching and error handling.
    """
    def __init__(self, name, source_url, target_json_path):
        self.name = name
        self.source_url = source_url
        self.target_json_path = target_json_path
        self.session = requests.Session()
        # Set a common User-Agent to avoid simple bot detection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Chrome/91.0.4472.124) Safari/537.36'
        })

    def fetch_html(self):
        """Fetches the HTML content of the source URL."""
        try:
            logger.info(f"[{self.name}] Fetching: {self.source_url}")
            response = self.session.get(self.source_url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.name}] Failed to fetch {self.source_url}: {e}")
            return None

    def parse(self, html):
        """
        To be implemented by subclasses.
        Should return a list of dictionaries representing news/alerts/etc.
        """
        raise NotImplementedError("Subclasses must implement the parse method.")

    def save_data(self, data):
        """Savess the parsed data to the target JSON file."""
        if not data:
            logger.warning(f"[{self.name}] No data to save.")
            return

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.target_json_path), exist_ok=True)

            # Load existing data if it exists (to avoid overwriting everything)
            existing_data = []
            if os.path.exists(self.target_json_path):
                with open(self.target_json_path, 'r', encoding='utf-8') as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        existing_data = []

            # Merge and deduplicate (simple approach: use a unique ID if available, or just append)
            combined_data = data + existing_data

            # In a real implementation, we would add complex deduplication here.
            # For now, let's just take the new data and ensure no exact duplicates by title/date.
            seen_titles = set()
            final_data = []
            for item in combined_data:
                title = item.get('title')
                if title and title not in seen_titles:
                    final_data.append(item)
                    seen_titles.add(title)

            # Limit to 20 latest items as requested by user
            final_data = final_data[:20]

            with open(self.target_json_path, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)

            logger.info(f"[{self.name}] Successfully saved {len(final_data)} items to {self.target_json_path}")

        except Exception as e:
            logger.error(f"[{self.name}] Error saving data: {e}")

    def run(self):
        """The main execution loop for the scraper."""
        html = self.fetch_html()
        if html:
            parsed_items = self.parse(html)
            if parsed_items:
                self.save_data(parsed_items)
            else:
                logger.warning(f"[{self.name}] No items parsed.")
        else:
            logger.error(f"[{self.name}] Scraper failed due to fetch error.")

class RSSScraper(BaseScraper):
    """
    Generic RSS scraper for any standard RSS feed.
    """
    def parse(self, html):
        soup = BeautifulSoup(html, 'lxml-xml')
        items = []
        articles = soup.find_all('item')

        for article in articles:
            title_tag = article.find('title')
            link_tag = article.find('link')
            pub_date_tag = article.find('pubDate')
            description_tag = article.find('description')

            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                link = link_tag.get_text(strip=True)
                pub_date = pub_date_tag.get_text(strip=True) if pub_date_tag else "Recent"
                description = description_tag.get_text(strip=True) if description_tag else ""

                # Clean up HTML tags/entities in description for a clean summary
                clean_desc = BeautifulSoup(description, "html.parser").get_text()

                # Get first 3 sentences
                sentences = re.split(r'(?<=[.!?])\s+', clean_desc)
                summary = " ".join(sentences[:3])
                if len(sentences) > 3:
                    summary += "..."

                items.append({
                    'title': title,
                    'url': link,
                    'date': pub_date,
                    'summary': summary,
                    'source': self.name
                })
        return items
