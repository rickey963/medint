import os
from base_scraper import RSSScraper

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/news_pl.json'))
    # Google News RSS search for top Polish medical sites
    QUERY = '(site:mp.pl OR site:pulsmedycyny.pl OR site:termedia.pl OR site:rynekzdrowia.pl OR site:medonet.pl OR site:nfz.gov.pl OR site:pacjent.gov.pl OR site:gov.pl/zdrowie)'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}+medicine&hl=pl&gl=PL&ceid=PL:pl"

    scraper = RSSScraper("Polska", RSS_URL, DATA_PATH)
    scraper.run()
