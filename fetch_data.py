"""
MEDINT Dashboard data pipeline.

fetch (per source, concurrently) -> clean/trim -> dedupe within each section
(same story reported by multiple outlets collapses into one card, annotated
"potwierdzone przez N źródeł") -> translate to Polish -> derive critical
medical alerts and the daily "must-know" top 5 from the collected text ->
write data.json.

Only sources listed in scraper/sources.py are used - see that file's
docstring for why every one of them goes through Google News instead of a
native feed.
"""
import re
import json
import logging
import datetime
import warnings
from concurrent.futures import ThreadPoolExecutor

import feedparser
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from deep_translator import GoogleTranslator

from scraper import sources

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# A handful of enrichment targets (EUR-Lex) serve XML, not HTML - harmless
# with html.parser, just noisy in the logs without this.
warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)

MAX_ARTICLES_PER_SOURCE = 8
MAX_ARTICLES_PER_SECTION = 30
FRESHNESS_WINDOW_HOURS = 72
DEDUPE_OVERLAP_THRESHOLD = 0.5

# Shared across all sections (which fetch concurrently - see main()) so the
# total number of simultaneous Google Translate requests stays capped even
# though several sections are finalizing items at the same time. Without this
# cap, N sections each opening their own translate pool multiplies concurrent
# requests against Google's free endpoint and triggers connection resets.
TRANSLATE_EXECUTOR = ThreadPoolExecutor(max_workers=8)

# Every source here is fetched through Google News (see scraper/sources.py),
# whose RSS <description> is always just "<title> - <source>" - never real
# article text. Enriching with the publisher's own page content (real
# summary, and for some sites a real headline) needs one extra HTTP GET per
# surviving item, so it gets its own capped, shared pool for the same reason
# TRANSLATE_EXECUTOR is shared - several sections enrich concurrently.
ENRICH_EXECUTOR = ThreadPoolExecutor(max_workers=10)
ENRICH_TIMEOUT_SECONDS = 8

# Sources whose native content is already Polish (see scraper/sources.py) -
# running these through Google Translate anyway would just be a slow PL->PL
# round trip for nothing, so _finalize() skips translation for them entirely.
POLISH_SOURCES = frozenset({
    'Medycyna Praktyczna', 'Puls Medycyny', 'Termedia', 'Medycyna po Dyplomie',
    'Rynek Zdrowia', 'Medonet', 'Narodowy Fundusz Zdrowia',
    'Internetowe Konto Pacjenta', 'Ministerstwo Zdrowia RP', 'alertmedyczny.pl',
    'ISAP', 'Dziennik Ustaw RP', 'Naczelna Izba Lekarska',
})


# ---------------------------------------------------------------------------
# Fetch / clean / translate
# ---------------------------------------------------------------------------

def _clean_html(raw):
    if not raw:
        return ""
    text = re.sub(r'<[^<]+?>', '', raw)
    text = (text.replace('&nbsp;', ' ').replace('&amp;', '&')
                .replace('&quot;', '"').replace('&#39;', "'").replace('&apos;', "'"))
    return ' '.join(text.split())


def _trim_sentences(text, max_sentences=3):
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    snippet = ' '.join(sentences[:max_sentences])
    if snippet and snippet[-1] not in '.!?':
        snippet += '.'
    return snippet


def _parse_date(entry):
    for key in ('published_parsed', 'updated_parsed'):
        v = entry.get(key)
        if v:
            try:
                return datetime.datetime(*v[:6], tzinfo=datetime.timezone.utc)
            except (TypeError, ValueError):
                continue
    return datetime.datetime.now(datetime.timezone.utc)


URL_DECODE_CACHE_PATH = 'url_decode_cache.json'
_url_decode_cache = None

# Decoding is 2 HTTP requests to Google per URL (confirmed by reading
# googlenewsdecoder's source - a GET for a signature/timestamp pair, then a
# POST to batchexecute). With ~30 items per section across 6 concurrently
# running sections, an uncached run was issuing 100+ simultaneous decode
# requests and Google started returning 429 Too Many Requests for *all* of
# them - which is the actual root cause behind links not resolving (the item
# silently keeps the raw, undecoded news.google.com redirect). Two
# mitigations: (1) cache successful decodes to disk so the same article -
# which typically recurs across many consecutive fetch cycles within the
# freshness window - only ever needs decoding once; (2) a small shared
# executor caps how many decode requests are in flight at once, regardless
# of how many sections are fetching concurrently.
DECODE_EXECUTOR = ThreadPoolExecutor(max_workers=3)


def _load_url_decode_cache():
    global _url_decode_cache
    if _url_decode_cache is None:
        try:
            with open(URL_DECODE_CACHE_PATH, 'r', encoding='utf-8') as f:
                _url_decode_cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            _url_decode_cache = {}
    return _url_decode_cache


def save_url_decode_cache():
    if _url_decode_cache is not None:
        with open(URL_DECODE_CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(_url_decode_cache, f, ensure_ascii=False)


def _decode_google_news_url_uncached(url):
    from googlenewsdecoder import gnewsdecoder
    # One retry, with a short pause first - a transient/rate-limited failure
    # here silently leaves the raw Google redirect URL in place, and
    # enrichment would then fetch *Google's own* interstitial/cookie-consent
    # page instead of the real article (confirmed during testing).
    for attempt in range(2):
        try:
            result = gnewsdecoder(url, interval=1)
            if result and result.get('status') and result.get('decoded_url'):
                return result['decoded_url']
        except Exception as e:
            logger.warning(f"Google News URL decode failed (attempt {attempt + 1}): {e}")
    return url


def _decode_google_news_url(url):
    if not url or 'news.google.com' not in url:
        return url
    cache = _load_url_decode_cache()
    if url in cache:
        return cache[url]
    decoded = DECODE_EXECUTOR.submit(_decode_google_news_url_uncached, url).result()
    if decoded != url:
        cache[url] = decoded
    return decoded


def _translate(text, target='pl'):
    if not text:
        return ''
    try:
        return GoogleTranslator(source='auto', target=target).translate(text)
    except Exception as e:
        logger.warning(f"Translation error: {e}")
        return text


FEED_USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')


def _extract_jsonld_description(soup):
    import json as _json
    for script in soup.find_all('script', attrs={'type': 'application/ld+json'}):
        try:
            data = _json.loads(script.string or '')
        except (ValueError, TypeError):
            continue
        candidates = data if isinstance(data, list) else [data]
        for entry in candidates:
            if isinstance(entry, dict) and entry.get('description'):
                return entry['description']
    return None


def _enrich_sejm_legislative_template(soup):
    """dziennikustaw.gov.pl (Dziennik Ustaw *and* Monitor Polski) and
    isap.sejm.gov.pl share the Sejm's legislative-document template, which
    never puts the actual act name in <title>/<h1> - that's always just
    "Dziennik Ustaw 2026 r. poz. 828", which tells a reader nothing. The
    real act title ("Rozporządzenie Ministra ... w sprawie ...") sits in the
    <h2> right after the #h_title heading. Tried unconditionally (cheap, and
    returns None immediately) rather than gated on domain, since it's the
    same template across at least two different domains."""
    h1 = soup.find(id='h_title')
    if not h1:
        return None
    h2 = h1.find_next('h2')
    if not h2:
        return None
    real_title = ' '.join(h2.get_text(' ', strip=True).split())
    return real_title or None


# Bot-wall/CAPTCHA interstitials (Cloudflare, PerimeterX, Akamai...) return
# HTTP 200 with a real <p>/meta description - their own, about *us* being
# suspected of being a bot, not the article. Caught for real on isap.sejm.gov.pl.
BOT_WALL_PHRASES = [
    'were browsing', 'made us think you were a bot', 'are you a robot',
    'verify you are human', 'access to this page has been denied', 'captcha',
    'checking your browser', 'enable javascript and cookies',
    # Cookie-consent banner boilerplate - the other recurring false "summary"
    # the generic <p> fallback grabs when a page's real content isn't a
    # plain server-rendered paragraph (confirmed on dziennikustaw.gov.pl).
    'accept all', 'we will also use cookies', 'this site uses cookies',
    'this website uses cookies', 'używamy plików cookies', 'plikow cookies',
    'zgadzasz się na ich użycie', 'polityce prywatności',
]


def _looks_like_bot_wall(text):
    text_lower = text.lower()
    return any(p in text_lower for p in BOT_WALL_PHRASES)


def _enrich_generic(soup):
    og = soup.find('meta', attrs={'property': 'og:description'})
    if og and og.get('content') and not _looks_like_bot_wall(og['content']):
        return og['content']
    meta = soup.find('meta', attrs={'name': 'description'})
    if meta and meta.get('content') and 'error 404' not in meta['content'].lower() and not _looks_like_bot_wall(meta['content']):
        return meta['content']
    jsonld_desc = _extract_jsonld_description(soup)
    if jsonld_desc and not _looks_like_bot_wall(jsonld_desc):
        return jsonld_desc
    for p in soup.find_all('p'):
        text = p.get_text(' ', strip=True)
        if len(text) > 60 and not _looks_like_bot_wall(text):
            return text
    return None


def _enrich_real_content(item):
    """Google News' own <description> is always just "<title> - <source>",
    never real article text (confirmed for every source here, since they're
    all fetched via Google News - see scraper/sources.py), so the publisher's
    own page has to be fetched to get an actual summary. Best-effort: on any
    failure (timeout, paywall, blocked bot, no usable content found) the
    item keeps its original title/summary_raw untouched."""
    url = item.get('url') or ''
    if not url or not url.startswith('http'):
        return item
    if 'news.google.com' in url:
        # URL decode failed upstream (see _decode_google_news_url's retry) -
        # fetching this would hit Google's own redirect/consent interstitial,
        # not the real article, and that interstitial's boilerplate text has
        # been mistaken for a real summary before. Leave the item alone.
        return item
    try:
        resp = requests.get(url, timeout=ENRICH_TIMEOUT_SECONDS, headers={'User-Agent': FEED_USER_AGENT})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        real_title = _enrich_sejm_legislative_template(soup)
        if real_title:
            item['title'] = real_title
            item['summary_raw'] = _trim_sentences(_clean_html(real_title), 3)
            return item

        description = _enrich_generic(soup)
        if description:
            item['summary_raw'] = _trim_sentences(_clean_html(description), 3)
    except Exception as e:
        logger.warning(f"Enrichment failed for {url}: {e}")
    return item


def fetch_source(name, url, kind, max_age_hours=None):
    max_age_hours = FRESHNESS_WINDOW_HOURS if max_age_hours is None else max_age_hours
    feed = None
    last_err = None
    # One retry with a browser-like UA covers both intermittent connection
    # resets and sites whose edge protection drops feedparser's default UA.
    for attempt in range(2):
        try:
            feed = feedparser.parse(url, agent=FEED_USER_AGENT)
            if feed.entries or not feed.get('bozo_exception'):
                break
            last_err = feed.get('bozo_exception')
        except Exception as e:
            last_err = e
            feed = None
    if feed is None:
        logger.error(f"Failed to fetch {name} ({url}): {last_err}")
        return []
    try:
        items = []
        for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
            title = _clean_html(entry.get('title', ''))
            if not title:
                continue
            summary_raw = _clean_html(entry.get('summary', entry.get('description', '')))
            link = entry.get('link', '')
            date = _parse_date(entry)
            age_hours = (datetime.datetime.now(datetime.timezone.utc) - date).total_seconds() / 3600
            if age_hours < 0 or age_hours > max_age_hours:
                continue
            items.append({
                'title': title,
                'summary_raw': _trim_sentences(summary_raw, 3),
                'url': link,
                'kind': kind,
                'date': date,
                'source': name,
            })
        return items
    except Exception as e:
        logger.error(f"Failed to fetch {name} ({url}): {e}")
        return []


def _word_set(text):
    return set(re.sub(r'[^\w\s]', ' ', (text or '').lower()).split())


def _title_overlap(a, b):
    wa, wb = _word_set(a), _word_set(b)
    if not wa or not wb:
        return 0
    return len(wa & wb) / min(len(wa), len(wb))


def _dedupe(items):
    """Same story reported by several outlets collapses into one card - the
    first (most recent, since items are pre-sorted) survives and gets a
    confirmed_by count of how many distinct sources reported it."""
    kept = []
    for item in items:
        match = next((k for k in kept if k['source'] != item['source']
                       and _title_overlap(item['title'], k['title']) > DEDUPE_OVERLAP_THRESHOLD), None)
        if match:
            match['confirmed_by'] = match.get('confirmed_by', 1) + 1
        else:
            item['confirmed_by'] = 1
            kept.append(item)
    return kept


def fetch_section(name_to_url_kind, section_key=None):
    """Fetches every source in a section concurrently, dedupes, caps, decodes
    + quality-filters, enriches with the real page content, then translates
    only the items that actually survive (cheaper and avoids wasting a
    translation call on something we're about to drop)."""
    with ThreadPoolExecutor(max_workers=max(1, len(name_to_url_kind))) as executor:
        # Entries are (name, url, kind) or (name, url, kind, max_age_hours) -
        # the optional 4th field overrides FRESHNESS_WINDOW_HOURS for sources
        # that publish too infrequently for the global 72h cutoff (see
        # scraper/sources.py's SOURCES_WYTYCZNE).
        futures = [executor.submit(fetch_source, *entry) for entry in name_to_url_kind]
        all_items = [item for f in futures for item in f.result()]

    all_items.sort(key=lambda it: it['date'], reverse=True)
    deduped = _dedupe(all_items)[:MAX_ARTICLES_PER_SECTION]

    # Decode the real publisher URL and drop low-quality items *before*
    # enriching/translating - PDFs, login walls, search/tool pages and
    # garbled titles are exactly the kind of "old reference page Google
    # re-crawled today" results that made stale content look freshly dated,
    # and there's no point spending an extra page fetch + translation call
    # on something about to be dropped.
    survivors = []
    for item in deduped:
        if item['kind'] == 'google_news':
            item['url'] = _decode_google_news_url(item['url'])
        if not _is_low_quality(item):
            survivors.append(item)

    survivors = list(ENRICH_EXECUTOR.map(_enrich_real_content, survivors))

    # The "Wytyczne i rekomendacje" sources (ISAP, Dziennik Ustaw, EUR-Lex)
    # are general legal registries, not medical-specific outlets - without
    # this they surface every law/EU act published that day (an agricultural
    # import rule, a merger notification...), not just health-related ones.
    # Checked *after* enrichment - Dziennik Ustaw's real act title (the only
    # place the actual subject matter appears - see _enrich_dziennik_ustaw)
    # only exists once enrichment has run.
    if section_key == 'guidelines':
        survivors = [it for it in survivors if _is_medically_relevant(f"{it['title']} {it['summary_raw']}")]

    def _finalize(item):
        title_original = item['title']
        if item['source'] in POLISH_SOURCES:
            item['title'] = title_original
            item['summary'] = item['summary_raw']
        else:
            item['title'] = _translate(title_original)
            item['summary'] = _translate(item['summary_raw'])
        item['date'] = item['date'].strftime('%Y-%m-%dT%H:%M:%SZ')
        del item['summary_raw']
        del item['kind']
        return item

    finalized = list(TRANSLATE_EXECUTOR.map(_finalize, survivors))
    return finalized


# ISAP/Dziennik Ustaw/EUR-Lex publish every law, not just health-related
# ones - this keeps "Wytyczne i rekomendacje" scoped to medicine specifically.
MEDICAL_RELEVANCE_PATTERNS = [
    r'zdrow\w*', r'lekarz\w*', r'\blek\w*', r'leczy\w*', r'leczen\w*',
    r'pacjent\w*', r'medyc\w*', r'szpital\w*', r'farmaceut\w*', r'farmacj\w*', r'apte\w*',
    r'szczepion\w*', r'\bnfz\b', r'minister\w+ zdrowia', r'chorob\w*', r'klinicz\w*',
    r'sanitar\w*', r'epidemi\w*', r'pandemi\w*', r'psychiatr\w*', r'stomatolog\w*',
    r'pielęgniar\w*', r'ratownictw\w* medyczn\w*', r'niepełnosprawn\w*', r'zdrowotn\w*',
    r'diagnoz\w*', r'terapeut\w*', r'rehabilitacj\w*', r'\bcovid\w*', r'wirus\w*', r'\bgrypa\b',
    r'\bwho\b', r'\bema\b', r'\bfda\b', r'\becdc\b', r'badani\w* klinicz\w*', r'wyrob\w* medyczn\w*',
]


def _is_medically_relevant(text):
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in MEDICAL_RELEVANCE_PATTERNS)


# Reference/tool/login pages that Google News sometimes surfaces with
# today's crawl date even though the underlying content is old or isn't an
# article at all - this is the actual root cause of "data says today but the
# article is from years ago" (confirmed during testing: e.g. mp.pl paywall
# redirects, a PDF download, a pill-lookup tool page, a font asset URL).
JUNK_URL_PATTERNS = [
    r'\.pdf(?:[?#]|$)', r'/articletopdf/', r'\.docx?(?:[?#]|$)', r'\.pptx?(?:[?#]|$)',
    r'\.xml(?:[?#]|$)', r'\.fmx\d*(?:[?#]|$)',
    r'\.(?:woff2?|ttf|eot|css|js|png|jpe?g|svg|ico|gif)(?:[?#]|$)',
    r'/(?:login|logowanie|signin|sign-in)(?:[/?]|$)', r'/auth/login', r'konto/logowanie',
    r'/search(?:[/?]|$)', r'imprints\.php',
]

JUNK_TITLE_SUBSTRINGS = [
    'subscribe', 'log in', 'sign in', 'cookie policy', 'just a moment',
    'access denied', 'page not found', '404', 'search results',
    'wyszukiwanie', 'wyszukaj', 'strona nie znaleziona', 'błąd 404',
    'akt prawny - sejm',
]

# A raw filename embedded in the title (e.g. "C_202603170PL.000101.fmx.xml")
# instead of a real headline - Google sometimes indexes a legal database's
# document-export filename as if it were the article title.
FILENAME_TITLE_RE = re.compile(r'\b[\w\-]+\.(?:xml|fmx\d*|pdf|docx?|xlsx?|pptx?)\b', re.IGNORECASE)

# An article whose only year reference is years in the past is an archived/
# reindexed document, not news - this is the actual root cause behind
# "today's date but the article is from 1946/2024": Google News' pubDate
# reflects when it (re)crawled the page, not the document's real date, and
# for static legal/reference archives that's often today even though the
# content itself - and the year printed right in its own title - is not.
STALE_TITLE_YEAR_MAX_AGE = 3


def _has_only_stale_years(title):
    years = [int(y) for y in re.findall(r'\b(19\d{2}|20\d{2})\b', title)]
    if not years:
        return False
    current_year = datetime.datetime.now(datetime.timezone.utc).year
    return all(current_year - y > STALE_TITLE_YEAR_MAX_AGE for y in years)


def _is_low_quality(item):
    url_lower = (item.get('url') or '').lower()
    if any(re.search(p, url_lower) for p in JUNK_URL_PATTERNS):
        return True
    title = (item.get('title') or '').strip()
    if len(title) < 10 or title.startswith('-'):
        return True
    # A Polish-source title starting with a lowercase letter is a truncated
    # mid-sentence fragment (Google News occasionally indexes just the part
    # of a longer title that matched the search query), not a real headline -
    # confirmed for "szpitalnego oddziału ratunkowego - Sejm" from ISAP.
    # Scoped to Polish sources only: legitimate English headlines sometimes
    # start with a lowercase gene/brand name (e.g. "mRNA vaccine...").
    if item.get('source') in POLISH_SOURCES and title[0].islower():
        return True
    if FILENAME_TITLE_RE.search(title):
        return True
    if _has_only_stale_years(title):
        return True
    title_lower = title.lower()
    if any(s in title_lower for s in JUNK_TITLE_SUBSTRINGS):
        return True
    # The source name appearing twice in its own title (e.g. "NL - EUR-Lex -
    # Unia Europejska - EUR-Lex") is a generic nav/locale page, not an article.
    source_lower = (item.get('source') or '').lower()
    if source_lower and title_lower.count(source_lower) >= 2:
        return True
    # Garbled titles like "h t t p s - ISAP - Sejm" - many single-character
    # "words" in a row, a pattern feedparser/Google News occasionally produces
    # for non-article pages instead of a real headline.
    tokens = title.split()
    if tokens and sum(1 for t in tokens if len(t) == 1) / len(tokens) > 0.4:
        return True
    return False


# ---------------------------------------------------------------------------
# Derived intelligence: critical medical alerts / daily top 5
# ---------------------------------------------------------------------------

CRITICAL_KEYWORDS = [
    'wycofano lek', 'wycofanie leku', 'wycofanie serii', 'wycofanie partii',
    'wstrzymanie dystrybucji', 'recall leku', 'ostrzeżenie who', 'ostrzeżenie fda',
    'ostrzeżenie ema', 'czarna skrzynka', 'black box', 'nowe ognisko epidemiczne',
    'ognisko epidemiczne', 'wybuch epidemii', 'epidemia', 'pandemia',
    'zakażenie szpitalne', 'alarm epidemiologiczny', 'zagrożenie zdrowia publicznego',
    'zanieczyszczona partia', 'skażona partia', 'kontaminacja leku', 'wycofanie zgody',
    'wstrzymanie badania klinicznego', 'przerwanie badania klinicznego', 'zatrucie pokarmowe',
]

ALERT_SECTIONS = ('poland', 'world', 'guidelines', 'epidemiology', 'clinical_trials', 'pharma_market')


def _all_text(sections, *keys):
    out = []
    for key in keys:
        for item in sections.get(key, []):
            out.append((item, f"{item['title']} {item['summary']}".lower()))
    return out


def build_critical_alerts(sections):
    """Returns full article objects (not just titles) since these feed both
    the scrolling ticker and the standalone "Alerty medyczne" card widget."""
    alerts = []
    seen_titles = set()
    for item, text in _all_text(sections, *ALERT_SECTIONS):
        if item['title'] in seen_titles:
            continue
        if any(kw in text for kw in CRITICAL_KEYWORDS):
            alerts.append(item)
            seen_titles.add(item['title'])
    alerts.sort(key=lambda it: it['date'], reverse=True)
    if not alerts:
        now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        return [{
            'title': 'Sytuacja stabilna - brak nowych alertów medycznych',
            'summary': '', 'url': '', 'source': '', 'date': now,
        }]
    return alerts[:8]


# Heuristic weighting for "Co musisz wiedzieć dzisiaj" - no AI API call (no
# per-run cost), scored locally like osint's build_instability(). Higher
# source prestige + fresher + matches more high-importance keywords -> wins.
SOURCE_PRESTIGE = {
    'WHO': 3, 'WHO Disease Outbreak News': 3, 'The Lancet': 3, 'NEJM': 3,
    'The BMJ': 2, 'Nature Medicine': 2, 'ECDC': 2, 'CDC Outbreaks': 2,
    'Cochrane Library': 2, 'EMA': 2, 'FDA Drug News': 2, 'Medscape': 2,
    'Ministerstwo Zdrowia RP': 2, 'STAT News': 1,
}

HIGH_IMPORTANCE_KEYWORDS = [
    ('przełom', 4), ('zatwierdz', 3), ('wytyczne', 3), ('nowe wytyczne', 4),
    ('alert', 4), ('alarm', 4), ('wycofan', 4), ('ostrzeżenie', 4),
    ('pandemi', 5), ('epidemi', 4), ('ognisko', 4), ('rekomendacj', 2),
    ('badanie kliniczne', 2), ('faza iii', 2), ('zatrucie', 3),
    ('skażon', 3), ('szczepionk', 2),
]


def _score_item(item):
    try:
        date = datetime.datetime.strptime(item['date'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)
        age_hours = max(0, (datetime.datetime.now(datetime.timezone.utc) - date).total_seconds() / 3600)
    except (TypeError, ValueError):
        age_hours = 999
    score = SOURCE_PRESTIGE.get(item['source'], 1) * 2
    score += max(0, 24 - age_hours) / 24 * 3
    text = f"{item['title']} {item['summary']}".lower()
    score += sum(weight for kw, weight in HIGH_IMPORTANCE_KEYWORDS if kw in text)
    return score


def build_daily_top5(sections):
    all_items = [item for key in ALERT_SECTIONS for item in sections.get(key, [])]
    if not all_items:
        return []
    ranked = sorted(all_items, key=_score_item, reverse=True)
    return ranked[:5]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # All sections are independent I/O-bound fetches, so they run
    # concurrently rather than one-after-another - wall-clock time becomes
    # the slowest single section instead of the sum of all of them.
    with ThreadPoolExecutor(max_workers=len(sources.ALL_SECTIONS)) as executor:
        logger.info(f"Fetching {len(sources.ALL_SECTIONS)} sections concurrently...")
        section_futures = {
            key: executor.submit(fetch_section, source_list, key)
            for key, source_list in sources.ALL_SECTIONS.items()
        }
        sections = {key: f.result() for key, f in section_futures.items()}

    output = {
        'last_updated': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'poland': sections['poland'],
        'world': sections['world'],
        'guidelines': sections['guidelines'],
        'epidemiology': sections['epidemiology'],
        'clinical_trials': sections['clinical_trials'],
        'pharma_market': sections['pharma_market'],
        'critical_alerts': build_critical_alerts(sections),
        'daily_top5': build_daily_top5(sections),
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    save_url_decode_cache()
    logger.info("Done - data.json updated.")


if __name__ == '__main__':
    main()
