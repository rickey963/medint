import os
from base_scraper import RSSScraper

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/research.json'))
    # Google News RSS search for high impact research (NEJM, Lancet, Nature, etc.)
    QUERY = '(site:nejm.org OR site:thelancet.com OR site:nature.com OR site:bmj.com OR site:pubmed.ncbi.nlm.nih.gov)'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}+research+study+clinical+trial&hl=pl&gl=PL&ceid=PL:pl"

    scraper = RSSScraper("Badania", RSS_URL, DATA_PATH)
    scraper.run()
