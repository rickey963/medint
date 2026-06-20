import os
from base_scraper import RSSScraper

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/ai_medicine.json'))

    # Focus on AI, LLMs, Digital Health from specialized sources
    QUERY = '(site:nature.com/digitalmedicine OR site:arxiv.org OR site:medrxiv.org OR site:fda.gov) +medical+AI+LLM+foundation+model+digital+health'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}&hl=pl&gl=PL&ceid=PL:pl"

    class AIMedicineScraper(RSSScraper):
        def parse(self, html):
            items = super().parse(html)

            for item in items:
                text = (item['title'] + " " + item['summary']).lower()

                # Classification of AI news
                if any(word in text for word in ['approval', 'fda', 'ema', 'zatwierdzono', 'rejestracja']):
                    item['ai_category'] = 'Zatwierdzenia/Regulacje'
                elif any(word in text for word in ['llm', 'gpt', 'claude', 'llama', 'foundation model', 'model fundamentowy']):
                    item['ai_category'] = 'Modele LLM'
                elif any(word in text for word in ['app', 'software', 'digital health', 'zdrowie cyfrowe', 'aplikacja']):
                    item['ai_category'] = 'Digital Health'
                else:
                    item['ai_category'] = 'Badania AI'

            return items

    scraper = AIMedicineScraper("AI w Medycynie", RSS_URL, DATA_PATH)
    scraper.run()
