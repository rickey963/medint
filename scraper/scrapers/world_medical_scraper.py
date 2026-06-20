import os
from base_scraper import RSSScraper

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/news_world.json'))
    # Strictly limiting to provided world domains.
    QUERY = '(site:medscape.com OR site:nejm.org OR site:bmj.com OR site:statnews.com OR site:nature.com OR site:who.int OR site:thelancet.com OR site:cochranelibrary.com) +medicine'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}&hl=en-US&gl=US&ceid=US:en"

    scraper = RSSScraper("Świat", RSS_URL, DATA_PATH)
    scraper.run()
