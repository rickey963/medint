import os
import requests
from base_scraper import RSSScraper
import logging

logger = logging.getLogger(__name__)

class EpidemicScraper(RSSScraper):
    """
    Scraper for epidemic and infectious disease sources (CDC, ECDC).
    """
    def run(self):
        # Placeholder URLs - in a real implementation, we would use actual RSS endpoints
        sources = [
            {"name": "CDC", "url": "https://www.cdc.gov/rss/index.xml"},
            {"name": "ECDC", "url": "https://www.ecdc.europa.eu/rss/news.xml"},
        ]

        DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/alerts.json'))

        for source in sources:
            logger.info(f"Running scraper for {source['name']}")
            scraper = RSSScraper(source['name'], source['url'], DATA_PATH)
            scraper.run()

if __name__ == "__main__":
    # We use a dummy name/URL since run() overrides them
    scraper = EpidemicScraper("Epidemic", "", "")
    scraper.run()
