import os
import requests
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
import logging
import re

logger = logging.getLogger(__name__)

class GoogleNewsScraper(BaseScraper):
    """
    Scraper for Google News RSS feed to get the latest global medical news.
    """
    def parse(self, html):
        soup = BeautifulSoup(html, 'lxml-xml')
        items = []

        articles = soup.find_all('item')

        for article in articles:
            title_tag = article.find('title')
            link_tag = article.find('link')
            pub_date_tag = article.find('pubDate')
            description_tag = article.find('description')

            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                link = link_tag.get_text(strip=True)
                pub_date = pub_date_tag.get_text(strip=True) if pub_date_tag else "Recent"
                description = description_tag.get_text(strip=True) if description_tag else ""

                # Clean up HTML tags in description if any
                clean_desc = BeautifulSoup(description, "html.parser").get_text()

                # Get first 3 sentences
                sentences = re.split(r'(?<=[.!?])\s+', clean_desc)
                summary = " ".join(sentences[:3])
                if len(sentences) > 3:
                    summary += "..."

                items.append({
                    'title': title,
                    'url': link,
                    'date': pub_date,
                    'summary': summary,
                    'source': 'Google News'
                })

        return items

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/news_world.json'))
    RSS_URL = "https://news.google.com/rss/search?q=medicine+when:1d&hl=en-US&gl=US&ceid=US:en"

    scraper = GoogleNewsScraper("GoogleNews", RSS_URL, DATA_PATH)
    scraper.run()
