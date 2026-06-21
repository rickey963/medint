import os
import sys

sys.path.append(os.path.dirname(__file__))

import logging

import collectors
import classify

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_all_scrapers():
    logger.info("Collecting articles from PL / World / PubMed / GIS sources...")
    items_with_origin = collectors.fetch_all()
    logger.info("Collected %d raw items.", len(items_with_origin))

    classify.classify_and_save(items_with_origin)
    logger.info("Classification and save complete.")


if __name__ == "__main__":
    run_all_scrapers()
