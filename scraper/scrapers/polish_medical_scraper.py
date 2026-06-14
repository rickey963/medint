import os
import requests
from base_scraper import RSSScraper
import logging

logger = logging.getLogger(__name__)

class PolishMedicalScraper(RSSScraper):
    """
    Scraper for various Polish medical RSS feeds.
    """
    def run(self):
        # We'll use these as our primary RSS sources (real ones found via research)
        sources = [
            {"name": "MP.pl", "url": "https://www.mp.pl/rss"},
            {"name": "PZH", "url": "https://pzh.gov.pl/rss"},
            {"name": "NFZ", "url": "https://www.nfz.gov.pl/rss"},
        ]

        DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/news_pl.json'))

        for source in sources:
            logger.info(f"Running scraper for {source['name']}")
            scraper = RSSScraper(source['name'], source['url'], DATA_PATH)
            scraper.run()

if __name__ == "__main__":
    scraper = PolishMedicalScraper("PolishMedical", "", "")
    scraper.run()
