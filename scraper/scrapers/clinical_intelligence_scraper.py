import os
from base_scraper import RSSScraper

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/clinical_intelligence.json'))
    # High-impact a search query combining the elite journals provided in the plan
    # NEJM, Lancet, JAMA, BMJ, Nature Medicine, Science Translational Medicine
    QUERY = '(site:nejm.org OR site:thelancet.com OR site:jamanetwork.com OR site:bmj.com OR site:nature.com/medicine OR site:translationalscience.org)'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}+medicine+breakthrough+clinical+trial&hl=en-US&gl=US&ceid=US:en"

    scraper = RSSScraper("Clinical Intelligence", RSS_URL, DATA_PATH)
    scraper.run()
