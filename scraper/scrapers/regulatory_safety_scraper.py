import os
from base_scraper import RSSScraper

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/regulatory_safety.json'))

    # Target EMA, FDA, and URPL specifically for safety, recalls, and registrations
    QUERY = '(site:ema.europa.eu OR site:fda.gov OR site:urpl.gov.pl) +recalls+warnings+safety+registration'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}&hl=pl&gl=PL&ceid=PL:pl"

    class RegulatorySafetyScraper(RSSScraper):
        def parse(self, html):
            items = super().parse(html)

            for item in items:
                text = (item['title'] + " " + item['summary']).lower()

                # Safety classification
                if 'recall' in text or 'wycofanie' in text:
                    item['safety_level'] = '🔴 WYCOFanie'
                elif 'warning' in text and 'black box' in text:
                    item['safety_level'] = '🟠 BLACK BOX'
                elif 'safety' in text or 'bezpieczeństwo' in text:
                    item['safety_level'] = '🟡 ALERT'
                elif 'registration' in text or 'approval' in text or 'rejestracja' in text:
                    item['safety_level'] = '🟢 REJESTRACJA'
                else:
                    item['safety_level'] = 'INFO'

            return items

    scraper = RegulatorySafetyScraper("Sygnały Bezpieczeństwa", RSS_URL, DATA_PATH)
    scraper.run()
