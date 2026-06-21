import requests
import logging
import pytz
from dateutil import parser
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

class BaseScraper:
    """
    Shared helper used by the collectors (see collectors.py).
    Provides HTML fetching, translation, and Warsaw-time date formatting.
    Topic classification and JSON persistence live in classify.py.
    """
    def __init__(self, name, source_url, target_json_path='', lang='pl'):
        self.name = name
        self.source_url = source_url
        self.target_json_path = target_json_path
        self.target_lang = lang
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Chrome/91.0.4472.124) Safari/537.36'
        })

    def translate_text(self, text):
        """Translates text to the target language if it's not already in that language."""
        if not text:
            return ""
        try:
            return GoogleTranslator(source='auto', target=self.target_lang).translate(text)
        except Exception as e:
            logger.error(f"[{self.name}] Translation error: {e}")
            return text

    def format_date(self, date_str):
        """Parses date and converts it to Warsaw time (GMT+1) in the machine-readable
        format "YYYY-MM-DD HH:MM" expected by classify.py's recency filter and by the
        frontend's parseAnyDate(). Polish display formatting happens only in the UI
        (dateUtils.formatToPolishFormat) - never bake a locale-specific string here."""
        if not date_str or date_str == "Recent":
            return "Recent"
        try:
            parsed_date = parser.parse(date_str)
            if parsed_date.tzinfo is None:
                parsed_date = pytz.utc.localize(parsed_date)

            warsaw_tz = pytz.timezone('Europe/Warsaw')
            warsaw_date = parsed_date.astimezone(warsaw_tz)
            return warsaw_date.strftime('%Y-%m-%d %H:%M')
        except Exception as e:
            logger.error(f"[{self.name}] Date parsing error for {date_str}: {e}")
            return date_str

    def fetch_html(self):
        """Fetches the HTML content of the source URL."""
        try:
            logger.info(f"[{self.name}] Fetching: {self.source_url}")
            response = self.session.get(self.source_url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.name}] Failed to fetch {self.source_url}: {e}")
            return None
