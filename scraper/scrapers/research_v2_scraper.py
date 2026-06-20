import os
from base_scraper import RSSScraper
import re

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/research.json'))

    # Target high-impact research portals and journals
    # We focus on the "most cited" and "most impactful" categories
    QUERY = '(site:pubmed.ncbi.nlm.nih.gov OR site:europepmc.org OR site:nature.com OR site:science.org OR site:nejm.org OR site:thelancet.com) +clinical+trial+RCT+meta-analysis'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}&hl=pl&gl=PL&ceid=PL:pl"

    class ResearchV2Scraper(RSSScraper):
        def parse(self, html):
            # Call parent parse to get the basic items
            items = super().parse(html)

            for item in items:
                # Basic classification based on title/summary keywords
                text = (item['title'] + " " + item['summary']).lower()

                if 'meta-analysis' in text or 'metaanaliza' in text:
                    item['study_type'] = 'Meta-analiza'
                elif 'randomized controlled trial' in text or 'badanie z randomizacją' in text or 'rct' in text:
                    item['study_type'] = 'RCT'
                elif 'cohort' in text or 'badanie kohortowe' in text:
                    item['study_type'] = 'Badanie kohortowe'
                elif 'case report' in text or 'opis przypadku' in text:
                    item['study_type'] = 'Case Report'
                elif 'systematic review' in text or 'przegląd systematyczny' in text:
                    item['study_type'] = 'Systematic Review'
                else:
                    item['study_type'] = 'Inne'

                # Mock Impact Factor/Citations for now since RSS doesn't provide them
                # In a full API version, we would fetch this from CrossRef
                item['impact_factor'] = "High" if any(s in item['source'] for s in ['Nature', 'Lancet', 'NEJM', 'JAMA']) else "Standard"

            return items

    scraper = ResearchV2Scraper("Badania", RSS_URL, DATA_PATH)
    scraper.run()
