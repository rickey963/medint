import time
import uuid
import random
import requests
import logging
import pytz
from dateutil import parser
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

# Rotated per-request (see fetch_html) in case Google's caching/ranking keys
# on a UA+IP fingerprint specifically, rather than (or in addition to) the
# URL string the existing cache-busting param already varies.
_USER_AGENTS = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
)


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
        # A fresh Session (not a shared/module-level one) per scraper instance,
        # and Connection: close below, so nothing about this request can ride
        # an already-established (and possibly cache-pinned) TCP/TLS session
        # from a previous call.
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(_USER_AGENTS),
            # Identical Google News RSS query strings kept returning the exact
            # same ~100 results for hours from GitHub Actions while the same
            # query from a residential connection kept advancing normally -
            # consistent with an intermediate cache keyed on the literal URL
            # (CDN/proxy level, not Google's own ranking) rather than on
            # requester identity. no-cache headers ask any such cache to
            # revalidate instead of serving its stored copy, and Connection:
            # close prevents reusing a pooled connection that might be pinned
            # to whichever cache/edge node served the last stale response.
            'Cache-Control': 'no-cache, no-store, max-age=0',
            'Pragma': 'no-cache',
            'Connection': 'close',
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

    def _cache_busted_url(self, url):
        """Appends a never-repeating query param so an intermediate cache
        keyed on the exact URL string (rather than on freshness/identity)
        can't serve a stored response - see the Cache-Control comment above
        for why this exists."""
        parts = urlsplit(url)
        query = parse_qsl(parts.query, keep_blank_values=True)
        query.append(('_cb', f'{int(time.time())}-{uuid.uuid4().hex[:8]}'))
        return urlunsplit(parts._replace(query=urlencode(query)))

    def fetch_html(self):
        """Fetches the HTML content of the source URL."""
        try:
            url = self._cache_busted_url(self.source_url)
            logger.info(f"[{self.name}] Fetching: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.name}] Failed to fetch {self.source_url}: {e}")
            return None
