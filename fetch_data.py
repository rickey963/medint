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
from concurrent.futures import ThreadPoolExecutor

import feedparser
from deep_translator import GoogleTranslator

from scraper import sources

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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


def _decode_google_news_url(url):
    if not url or 'news.google.com' not in url:
        return url
    try:
        from googlenewsdecoder import gnewsdecoder
        result = gnewsdecoder(url, interval=0)
        if result and result.get('status') and result.get('decoded_url'):
            return result['decoded_url']
    except Exception as e:
        logger.warning(f"Google News URL decode failed: {e}")
    return url


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


def fetch_source(name, url, kind):
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
            if age_hours < 0 or age_hours > FRESHNESS_WINDOW_HOURS:
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


def fetch_section(name_to_url_kind):
    """Fetches every source in a section concurrently, dedupes, caps, decodes
    + quality-filters, then translates only the items that actually survive
    (cheaper and avoids wasting a translation call on something we're about
    to drop)."""
    with ThreadPoolExecutor(max_workers=max(1, len(name_to_url_kind))) as executor:
        futures = [executor.submit(fetch_source, name, url, kind) for name, url, kind in name_to_url_kind]
        all_items = [item for f in futures for item in f.result()]

    all_items.sort(key=lambda it: it['date'], reverse=True)
    deduped = _dedupe(all_items)[:MAX_ARTICLES_PER_SECTION]

    # Decode the real publisher URL and drop low-quality items *before*
    # translating - PDFs, login walls, search/tool pages and garbled titles
    # are exactly the kind of "old reference page Google re-crawled today"
    # results that made stale content look freshly dated, and there's no
    # point spending a translation call on something about to be dropped.
    survivors = []
    for item in deduped:
        if item['kind'] == 'google_news':
            item['url'] = _decode_google_news_url(item['url'])
        if not _is_low_quality(item):
            survivors.append(item)

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
            key: executor.submit(fetch_section, source_list)
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
    logger.info("Done - data.json updated.")


if __name__ == '__main__':
    main()
