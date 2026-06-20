import os
from base_scraper import RSSScraper

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/news_pl.json'))
    # Strictly limiting to provided domains only. Adding +medycyna to avoid general news.
    QUERY = '(site:mp.pl OR site:pulsmedycyny.pl OR site:termedia.pl OR site:rynekzdrowia.pl OR site:medonet.pl OR site:nfz.gov.pl OR site:pacjent.gov.pl OR site:gov.pl/zdrowie) +medycyna'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}&hl=pl&gl=PL&ceid=PL:pl"

    scraper = RSSScraper("Polska", RSS_URL, DATA_PATH)
    scraper.run()
