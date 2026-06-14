import os
from base_scraper import RSSScraper
import logging

logger = logging.getLogger(__name__)

class RegulatoryScraper(RSSScraper):
    """
    Scraper for regulatory and drug-related updates (EMA, FDA, NICE).
    """
    def run(self):
        # We'll use these as our primary RSS sources
        sources = [
            {"name": "FDA", "url": "https://www.fda.gov/rss/drug-safety.xml"},
            {"format": "EMA", "url": "https://www.ema.europa.eu/rss/news.xml"}, # Note: This is a placeholder structure to show complexity
            {"name": "NICE", "url": "https://www.nice.org.uk/rss/guidelines.xml"},
        ]

        # We'll store them in the 'guidelines.json' file
        DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/guidelines.json'))

        for source in sources:
            name = source.get('name') or source.get('format')
            if not name:
                continue
            logger.info(f"Running scraper for {name}")
            scraper = RSSScraper(name, source['url'], DATA_PATH)
            scraper.run()

if __name__ == "__main__":
    scraper = RegulatoryScraper("Regulatory", "", "")
    scraper.run()
