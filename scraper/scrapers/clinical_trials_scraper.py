import os
from base_scraper import RSSScraper

if __name__ == "__main__":
    DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/data/clinical_trials.json'))

    # Targeting the major clinical trial registries via focused search
    # ClinicalTrials.gov, EU CTR, WHO ICTRP
    QUERY = '(site:clinicaltrials.gov OR site:clinicaltrialsregister.eu OR site:who.int/aictrp) +clinical+trial+recruitment'
    RSS_URL = f"https://news.google.com/rss/search?q={QUERY}&hl=pl&gl=PL&ceid=PL:pl"

    class ClinicalTrialsScraper(RSSScraper):
        def parse(self, html):
            items = super().parse(html)

            for item in items:
                text = (item['title'] + " " + item['summary']).lower()

                # Phase detection
                if 'phase 1' in text or 'faza 1' in text: item['phase'] = 'Faza I'
                elif 'phase 2' in text or 'faza 2' in text: item['phase'] = 'Faza II'
                elif 'phase 3' in text or 'faza 3' in text: item['phase'] = 'Faza III'
                elif 'phase 4' in text or 'faza 4' in text: item['phase'] = 'Faza IV'
                else: item['phase'] = 'Nieokreślona'

                # Specialization detection
                if 'cancer' in text or 'oncology' in text or 'onkologia' in text: item['specialization'] = 'Onkologia'
                elif 'heart' in text or 'cardiology' in text or 'kardiologia' in text: item['specialization'] = 'Kardiologia'
                elif 'brain' in text or 'neurology' in text or 'neurologia' in text: item['specialization'] = 'Neurologia'
                elif 'diabetes' in text or 'diabetologia' in text: item['specialization'] = 'Diabetologia'
                elif 'ai' in text or 'artificial intelligence' in text or 'machine learning' in text: item['specialization'] = 'AI w Medycynie'
                else: item['specialization'] = 'Ogólne'

            return items

    scraper = ClinicalTrialsScraper("Badania Kliniczne", RSS_URL, DATA_PATH)
    scraper.run()
