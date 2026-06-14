import os
import json
import random
from datetime import datetime, timedelta

class MockScraper:
    """
    A scraper that generates fake but realistic medical data for development.
    This allows us to build the frontend without depending on live websites.
    """
    def __init__(self, name, target_json_path):
        self.name = name
        self.target_json_path = target_json_path

    def parse(self, html=None):
        # We don't actually need the HTML because we are generating fake data
        items = []

        if "alerts" in self.target_json_path:
            items = [
                {
                    "title": "Wycofano serię leku X!",
                    "url": "https://example.com/alert1",
                    "date": datetime.now().strftime("%d.%m.%Y"),
                    "type": "ALERT",
                    "source": "GIS"
                },
                {
                    "title": "Nowe zagrożenie epidemiologiczne: Grypa",
                    "url": "https://example.com/alert2",
                    "date": datetime.now().strftime("%d.%m.%Y"),
                    "type": "ALERT",
                    "source": "WHO"
                }
            ]
        elif "news_pl" in self.target_json_path:
            items = [
                {
                    "title": "Nowe wytyczne dla lekarzy rodzinnych",
                    "summary": "Ministerstwo Zdrowia ogłosiło nowe procedury w zakresie...",
                    "url": "https://example.com/news1",
                    "date": datetime.now().strftime("%d.%m.%Y"),
                    "source": "MZ"
                },
                {
                    "title": "Zmiany w refundacji leków 2026",
                    "summary": "Nowa lista leków refundowanych obejmuje...",
                    "url": "https://example.com/news2",
                    "date": datetime.nowder_date_format() if False else datetime.now().strftime("%d.%m.%Y"),
                    "source": "NFZ"
                }
            ]
        elif "news_world" in self.target_json_path:
            items = [
                {
                    "title": "Breakthrough in Alzheimer's Treatment",
                    "summary": "A new study published in Lancet shows significant...",
                    "url": "https://example.com/world1",
                    "date": datetime.now().strftime("%d.%m.%Y"),
                    "source": "Lancet",
                    "translation_needed": True
                }
            ]
        elif "research" in self.target_json_path:
            items = [
                {
                    "title": "New study on mRNA vaccines",
                    "type": "RCT",
                    "patient_count": 5000,
                    "conclusion": "Vaccines are effective against new variants.",
                    "evidence_level": "★★★★★",
                    "url": "https://example.com/res1",
                    "date": datetime.now().strftime("%d.%m.%Y"),
                    "source": "NEJM"
                }
            ]
        else:
            items = []

        return items

    def run(self):
        # Since it's a mock, we just generate data and save it.
        # In a real scraper, this would follow the BaseScraper pattern.
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"[Mock] Generating fake data for {self.target_json_path}")
        items = self.parse()

        if items:
            # Re-use the saving logic from the engine's perspective or just implement it here
            os.makedirs(os.path.dirname(self.target_json_path), exist_ok=True)
            with open(self.target_json_path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            logger.info(f"[Mock] Saved {len(items)} items.")

if __name__ == "__main__":
    # Test the mock scraper
    test_path = "C:/Users/rickty/Github/medint/src/data/alerts.json" # Note: I'll use relative path in engine
    scraper = MockScraper("Mock", test_path)
    scraper.run()
