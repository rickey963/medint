import requests
from bs4 import BeautifulSoup
import json
import os
import logging
import re
from datetime import datetime
import pytz
from dateutil import parser
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

class BaseScraper:
    """
    Base class for all MEDINT scrapers.
    Provides common functionality like HTML fetching, translation, and date formatting.
    """
    def __init__(self, name, source_url, target_json_path, lang='pl'):
        self.name = name
        self.source_url = source_url
        self.target_json_path = target_json_path
        self.target_lang = lang
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Chrome/91.0.4472.124) Safari/537.36'
        })

    def translate_text(self, text):
        """Translates text to the target language if it's not already in that language."""
        if not text:
            return ""
        try:
            # Simple check: if it's already Polish, don't translate
            # Note: This is a naive check. GoogleTranslator handles auto-detection.
            return GoogleTranslator(source='auto', target=self.target_lang).translate(text)
        except Exception as e:
            logger.error(f"[{self.name}] Translation error: {e}")
            return text

    def format_date(self, date_str):
        """Parses date and converts it to Warsaw time (GMT+1)."""
        if not date_str or date_str == "Recent":
            return "Recent"
        try:
            # Parse date
            parsed_date = parser.parse(date_str)
            if parsed_date.tzinfo is None:
                parsed_date = pytz.utc.localize(parsed_date)

            warsaw_tz = pytz.timezone('Europe/Warsaw')
            warsaw_date = parsed_date.astimezone(warsaw_tz)
            return warsaw_date.strftime('%Y-%m-%d %H:%M')
        except Exception as e:
            logger.error(f"[{self.name}] Date parsing error for {date_str}: {e}")
            return date_str

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
        """To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement the parse method.")

    def save_data(self, data):
        """Saves the parsed data to the target JSON file, sorted by date newest first."""
        if not data:
            logger.warning(f"[{self.name}] No data to save.")
            return

        try:
            os.makedirs(os.path.dirname(self.target_json_path), exist_ok=True)

            existing_data = []
            if os.path.exists(self.target_json_path):
                with open(self.target_json_path, 'r', encoding='utf-8') as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        existing_data = []

            combined_data = data + existing_data
            seen_titles = set()
            final_data = []
            for item in combined_data:
                title = item.get('title')
                if title and title not in seen_titles:
                    final_data.append(item)
                    seen_titles.add(title)

            # Sort by date newest first
            # Note: This requires dates to be in a sortable format (like ISO) or we sort before formatting
            # For now, we assume the 'date' field is a sortable string or datetime object if provided
            try:
                final_data.sort(key=lambda x: x.get('date', ''), reverse=True)
            except Exception as e:
                logger.error(f"[{self.name}] Sorting error: {e}")

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
    Generic RSS scraper with translation and date formatting.
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
                raw_title = title_tag.get_text(strip=True)
                link = link_tag.get_text(strip=True)
                raw_date = pub_date_tag.get_text(strip=True) if pub_date_tag else "Recent"
                description = description_tag.get_text(strip=True) if description_tag else ""

                clean_desc = BeautifulSoup(description, "html.parser").get_text()
                sentences = re.split(r'(?<=[.!?])\s+', clean_desc)
                summary_raw = " ".join(sentences[:3])
                if len(sentences) > 3:
                    summary_raw += "..."

                # Translate and format
                title = self.translate_text(raw_title)
                summary = self.translate_text(summary_raw)
                date = self.format_date(raw_date)

                items.append({
                    'title': title,
                    'url': link,
                    'date': date,
                    'summary': summary,
                    'source': self.name
                })
        return items
