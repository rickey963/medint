import os
import requests
from base_scraper import RSSScraper
import logging

logger = logging.getLogger(__name__)

class WorldMedicalScraper(RSSScraper):
    """
    Scraper for various global medical RSS feeds (WHO, Lancet, etc.)
    """
    def run(self):
        sources = [
            {"name": "WHO", "url": "https://www.who.int/rss-feeds/news-in-english.xml"},
            {"name": "Lancet", "url": "https://www.thelancet.com/rss/recent"},
            {"name": "Cochrane", "url": "https://www.cochrane.org/rss/news"}, # Placeholder
        ]

        DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/news_world.json'))

        for source in sources:
            logger.info(f"Running scraper for {source['name']}")
            scraper = RSSScraper(source['name'], source['url'], DATA_PATH)
            scraper.run()

if __name__ == "__main__":
    scraper = WorldMedicalScraper("WorldMedical", "", "")
    scraper.run()
