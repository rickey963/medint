import os
import requests
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

class PubMedScraper(BaseScraper):
    """
    Scraper for PubMed RSS feed to get the latest medical research.
    """
    def parse(self, html):
        # Use lxml-xml parser for robust RSS/XML parsing
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
                # Split by . ! or ? followed by whitespace
                sentences = re.split(r'(?<=[.!?])\s+', clean_desc)
                summary = " ".join(sentences[:3])
                if len(sentences) > 3:
                    summary += "..."

                items.append({
                    'title': title,
                    'url': link,
                    'date': pub_date,
                    'summary': summary,
                    'source': 'PubMed'
                })

        return items

if __name__ == "__main__":
    # Path to target JSON in the src/data folder
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/pubmed_news.json'))
    # PubMed RSS search for 'medicine'
    RSS_URL = "https://pubmed.ncbi.nlm.nih.gov/rss/search?term=medicine"

    scraper = PubMedScraper("PubMed", RSS_URL, DATA_PATH)
    scraper.run()
