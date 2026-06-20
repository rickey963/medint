import os
from base_scraper import RSSScraper

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/guidelines.json'))
    # Google News RSS search focusing on guidelines from medical portals
    QUERY = '(site:mp.pl OR site:nejm.org OR site:bmj.com OR site:who.int OR site:thelancet.com)'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}+guidelines+wytyczne&hl=pl&gl=PL&ceid=PL:pl"

    scraper = RSSScraper("Wytyczne", RSS_URL, DATA_PATH)
    scraper.run()
