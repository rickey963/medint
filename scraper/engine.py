import os
import sys

# Add the scraper directory to the path so we can import base_scraper and other modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'scrapers'))

import logging
import runpy
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_all_scrapers():
    scrapers_dir = os.path.join(os.path.dirname(__file__), 'scrapers')

    if not os.path.exists(scrapers_dir):
        logger.error(f"Scrapers directory not found: {scrapers_dir}")
        return

    # Get all .py files in the scrapers directory, excluding __init__.py and base classes if any
    scraper_files = [f for f in os.listdir(scrapers_dir) if f.endswith('.py') and not f.startswith('__')]

    if not scraper_files:
        logger.warning("No scrapers found to run.")
        return

    for scraper_file in scraper_files:
        scraper_path = os.path.join(scrapers_dir, scraper_file)
        module_name = scraper_file[:-3] # remove .py

        try:
            logger.info(f"Attempting to run scraper module: {module_name}")
            runpy.run_path(scraper_path, run_name="__main__")
            logger.info(f"Successfully executed scraper module: {module_name}")

        except Exception as e:
            logger.error(f"Failed to run scraper {scraper_file}: {e}", exc_info=True)

if __name__ == "__main__":
    run_all_scrapers()
