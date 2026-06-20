import os
from base_scraper import RSSScraper

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/alerts.json'))
    # Strictly limiting to epidemic/outbreak sources provided.
    QUERY = '(site:who.int/emergencies/disease-outbreak-news OR site:ecdc.europa.eu OR site:cdc.gov OR site:promed.org OR site:healthmap.org) +outbreak'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}&hl=pl&gl=PL&ceid=PL:pl"

    scraper = RSSScraper("Alerty", RSS_URL, DATA_PATH)
    scraper.run()
