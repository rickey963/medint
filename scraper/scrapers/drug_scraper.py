import os
from base_scraper import RSSScraper

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/drugs.json'))
    # Strictly limiting to pharmaceutical sources provided.
    QUERY = '(site:drugs.com OR site:ema.europa.eu OR site:fda.gov OR site:pinksheet.com OR site:endpointsnews.com) +pharmacy'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}&hl=pl&gl=PL&ceid=PL:pl"

    scraper = RSSScraper("Leki", RSS_URL, DATA_PATH)
    scraper.run()
