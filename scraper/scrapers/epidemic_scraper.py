import os
from base_scraper import RSSScraper

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/alerts.json'))
    # Google News RSS search for epidemic/outbreak sources
    QUERY = '(site:who.int/emergencies/disease-outbreak-news OR site:ecdc.europa.eu OR site:cdc.gov OR site:promed.org OR site:healthmap.org)'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}+epidemic+outbreak&hl=pl&gl=PL&ceid=PL:pl"

    scraper = RSSScraper("Alerty", RSS_URL, DATA_PATH)
    scraper.run()
