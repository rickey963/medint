import os
from base_scraper import RSSScraper

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/guidelines.json'))

    # Focus on major medical societies and guidelines
    QUERY = '(site:esc-ap.org OR site:esmo.org OR site:asco.org OR site:nice.org.uk OR site:cdc.gov OR site:ptk.org.pl OR site:pto.org.pl) +guidelines+wytyczne+recommendations'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}&hl=pl&gl=PL&ceid=PL:pl"

    class GuidelinesV2Scraper(RSSScraper):
        def parse(self, html):
            items = super().parse(html)

            for item in items:
                text = (item['title'] + " " + item['summary']).lower()

                # Change detection logic (Keywords for updates/new versions)
                change_keywords = ['updated', 'revised', 'new version', 'nowe wytyczne', 'aktualizacja', 'znowelizowano', 'nowe rekomendacje']

                if any(kw in text for kw in change_keywords):
                    item['is_update'] = True
                    item['change_type'] = 'Aktualizacja'
                else:
                    item['is_update'] = False
                    item['change_type'] = 'Nowa Rekomendacja'

            return items

    scraper = GuidelinesV2Scraper("Wytyczne", RSS_URL, DATA_PATH)
    scraper.run()
