import os
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

class GISScraper(BaseScraper):
    """
    Scraper for GIS (Główny Inspektorat Sanitarny) alerts and announcements.
    """
    def parse(self, html):
        soup = BeautifulSoup(html, 'lxml')
        items = []

        # This selector is a placeholder. In reality, we'd inspect the GIS site structure.
        # Let's assume they have news items in <article> tags with a class 'news-item'.
        articles = soup.find_all('article')

        for article in articles:
            title_tag = article.find('h2')
            link_tag = article.find('a')
            date_tag = article.find('time') or article.find('span', class_='date')

            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                link = link_tag['href']
                # Handle relative URLs
                if not link.startswith('http'):
                    link = f"https://www.gov.pl/web/gis{link}"

                date_str = date_tag.get_text(strip=True) if date_tag else "Brak daty"

                items.append({
                    'title': title,
                    'url': link,
                    'date': date_str,
                    'type': 'ALERT', # We can refine this later based on content
                    'source': 'GIS'
                })

        return items

if __name__ == "__main__":
    # For testing purposes
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/alerts.json'))
    scraper = GISScraper("GIS", "https://www.gov.pl/web/gis/komunikaty", DATA_PATH)
    scraper.run()
