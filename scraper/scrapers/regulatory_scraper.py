import os
from base_scraper import RSSScraper

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/legal.json'))
    # Strictly limiting to legal sources provided.
    QUERY = '(site:isap.gov.pl OR site:dziennikurzedowy.gov.pl OR site:rynekzdrowia.pl OR site:nil.org.pl OR site:eur-lex.europa.eu) +prawo+medyczne'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}&hl=pl&gl=PL&ceid=PL:pl"

    scraper = RSSScraper("Zmiany Prawne", RSS_URL, DATA_PATH)
    scraper.run()
