"""
Topical classification for articles collected by the broad collectors.

Each article collected from the PL / World / PubMed feeds is routed to exactly
one primary tile (target JSON file) using the same keyword rules that used to
live inside the individual per-tile scrapers (research_v2, clinical_trials,
regulatory_safety, ai_medicine, guidelines_v2). Those rules are reused
verbatim here so behaviour does not change, only where the source data comes
from.

Alert-worthy articles (recalls, black-box warnings, outbreaks...) are
*additionally* appended to alerts.json regardless of their primary tile, since
"medical alert" is a cross-cutting concern rather than a topic of its own.
"""

import os
import re
import json
import logging
import requests
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/data'))

# Google News RSS only ever gives us "<title>  <outlet>" as a description, never a
# real excerpt. To produce a genuine, non-redundant 3-4 sentence Polish summary we
# follow the link once and read the publisher's own <meta description> instead of
# inventing text. Bounded per run so a single classify_and_save() call can't turn
# into hundreds of outbound requests against a 5-minute cron.
_ENRICH_SESSION = requests.Session()
_ENRICH_SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Chrome/91.0.4472.124) Safari/537.36'
})
ENRICH_BUDGET_PER_RUN = 200

# Processing order for _merge_and_save - deliberately not dict insertion order
# (which follows whichever collector's ThreadPoolExecutor future happened to
# resolve first, i.e. random per run). clinical_intelligence.json is the hero
# tile, so it gets first claim on the shared enrich_budget; anything not
# listed here keeps whatever order buckets.items() yields.
TILE_SAVE_PRIORITY = ['clinical_intelligence.json', 'clinical_research.json', 'regulatory_safety.json']


def _looks_redundant(summary, title):
    """True if `summary` carries no information beyond `title` (e.g. Google News'
    "<title>  <outlet>" placeholder description)."""
    if not summary:
        return True
    norm = lambda s: set(re.sub(r'[^\w\s]', ' ', s.lower()).split())
    title_words = norm(title)
    summary_words = norm(summary)
    if not summary_words:
        return True
    overlap = len(title_words & summary_words) / len(summary_words)
    return overlap > 0.8


# deep_translator's free GoogleTranslator wraps the legacy translate_a/single
# endpoint, which has a hard request-length ceiling - some publishers (WHO
# press releases especially) stuff their entire article into og:description,
# and a long-enough one makes the call fail outright (observed: a ~1500-char
# WHO description errored every time). The UI only ever shows a few clamped
# lines anyway, so cut to a sentence boundary near MAX_TRANSLATE_CHARS before
# translating rather than 0% of a too-long summary winning over 100% of a
# safely-sized one.
MAX_TRANSLATE_CHARS = 600


def _truncate_for_translation(text, max_chars=MAX_TRANSLATE_CHARS):
    if len(text) <= max_chars:
        return text
    sentences = re.split(r'(?<=[.!?])\s+', text)
    out = ''
    for s in sentences:
        if len(out) + len(s) + 1 > max_chars:
            break
        out = f'{out} {s}'.strip()
    return out or text[:max_chars]


# These publishers sit behind Cloudflare's bot challenge ("Just a moment...")
# and return a 403 to every plain-requests fetch, no matter the User-Agent -
# verified directly (curl-equivalent request to each). Skipping them outright
# means the shared enrich_budget isn't burned on a 6s timeout that was always
# going to fail, leaving more of it for sources that actually work.
ENRICH_BLOCKED_DOMAINS = (
    'nejm.org', 'jamanetwork.com', 'thelancet.com', 'jacc.org',
    'ahajournals.org', 'annals.org', 'ashpublications.org',
)


def _fetch_meta_description(url):
    if any(d in (url or '') for d in ENRICH_BLOCKED_DOMAINS):
        return None
    try:
        resp = _ENRICH_SESSION.get(url, timeout=6, allow_redirects=True)
        resp.raise_for_status()
        # requests falls back to ISO-8859-1 whenever the server omits a charset in
        # Content-Type, which mangles every Polish page served as UTF-8 without one.
        # apparent_encoding sniffs the actual bytes instead of trusting that header.
        if resp.encoding is None or resp.encoding.lower() == 'iso-8859-1':
            resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, 'html.parser')
        tag = soup.find('meta', attrs={'property': 'og:description'}) or soup.find('meta', attrs={'name': 'description'})
        content = (tag.get('content') if tag else '') or ''
        content = content.strip()
        return content or None
    except Exception:
        return None


def _decode_google_news_url(url):
    """Google News RSS links are JS-redirect interstitials (Google's consent wall
    blocks a plain requests.get follow), so the only reliable way to reach the real
    publisher URL is to decode the base64 payload in the link path."""
    if not url or 'news.google.com' not in url:
        return url
    try:
        from googlenewsdecoder import gnewsdecoder
        result = gnewsdecoder(url, interval=0)
        if result and result.get('status') and result.get('decoded_url'):
            return result['decoded_url']
    except Exception as e:
        logger.warning("Google News URL decode failed: %s", e)
    return url


def enrich_redundant_summaries(items, translate_fn, budget):
    """Resolves the real publisher URL behind the Google News redirect link and,
    when the RSS feed gave us no real excerpt (the common case - Google News
    descriptions are just "<title>  <outlet>"), replaces the summary with the
    publisher's own meta description, translated to Polish.

    `budget` is a shared [remaining] single-element list, decremented in place, so
    a caller processing several buckets in one run can cap total outbound requests
    across all of them rather than per-bucket.
    Mutates and returns `items`. Budget bookkeeping (deciding which items qualify)
    stays sequential - it's pure bookkeeping, not network I/O - but the actual
    decode+fetch+translate work for the items that earned a slot runs concurrently,
    since each one is an independent outbound request that was otherwise waiting
    on every previous one for no reason."""
    to_process = []
    for item in items:
        if budget[0] <= 0:
            break
        url = item.get('url')
        if not url:
            continue
        needs_summary = _looks_redundant(item.get('summary'), item.get('title', ''))
        if not needs_summary and 'news.google.com' not in url:
            continue
        budget[0] -= 1
        to_process.append((item, needs_summary))

    def _process(entry):
        item, needs_summary = entry
        real_url = _decode_google_news_url(item['url'])
        item['url'] = real_url
        if needs_summary:
            description = _fetch_meta_description(real_url)
            if description:
                item['summary'] = translate_fn(_truncate_for_translation(description))

    if to_process:
        with ThreadPoolExecutor(max_workers=min(10, len(to_process))) as executor:
            list(executor.map(_process, to_process))

    return items

# Kept in sync with src/App.js's ALERT_KEYWORDS. Deliberately specific phrases,
# not loose single words like "alert"/"zagrożenie"/"epidemi" - those false-positive
# on historical or unrelated coverage (e.g. an article *about* epidemiology, or
# "zagrożenie" used loosely) and turn the ticker into noise instead of signal.
ALERT_KEYWORDS = [
    'wycofanie z obrotu', 'wycofanie leku', 'wycofanie serii', 'black box', 'black-box',
    'nowe ognisko', 'ognisko zakażeń', 'wybuch epidemii', 'pandemi', 'nowy wariant',
    'nowe zakażenia', 'nowy wirus', 'outbreak', 'recall', 'fda warning', 'who alert',
    'disease outbreak',
]

MAX_AGE_DAYS = 7


def _text_of(item):
    return f"{item.get('title', '')} {item.get('summary', '')}".lower()


def classify_regulatory_safety(text):
    if 'recall' in text or 'wycofanie' in text:
        return '🔴 WYCOFanie'
    if 'warning' in text and 'black box' in text:
        return '🟠 BLACK BOX'
    if 'safety' in text or 'bezpieczeństwo' in text:
        return '🟡 ALERT'
    if 'registration' in text or 'approval' in text or 'rejestracja' in text:
        return '🟢 REJESTRACJA'
    return None


def classify_clinical_trial(text):
    registry_kw = ['clinicaltrials.gov', 'clinical trial', 'recruitment', 'faza i', 'faza ii',
                   'faza iii', 'faza iv', 'phase 1', 'phase 2', 'phase 3', 'phase 4', 'rekrutacja']
    if not any(kw in text for kw in registry_kw):
        return None
    if 'phase 1' in text or 'faza 1' in text:
        phase = 'Faza I'
    elif 'phase 2' in text or 'faza 2' in text:
        phase = 'Faza II'
    elif 'phase 3' in text or 'faza 3' in text:
        phase = 'Faza III'
    elif 'phase 4' in text or 'faza 4' in text:
        phase = 'Faza IV'
    else:
        phase = 'Nieokreślona'

    if 'cancer' in text or 'oncology' in text or 'onkologia' in text:
        specialization = 'Onkologia'
    elif 'heart' in text or 'cardiology' in text or 'kardiologia' in text:
        specialization = 'Kardiologia'
    elif 'brain' in text or 'neurology' in text or 'neurologia' in text:
        specialization = 'Neurologia'
    elif 'diabetes' in text or 'diabetologia' in text:
        specialization = 'Diabetologia'
    elif 'ai' in text or 'artificial intelligence' in text or 'machine learning' in text:
        specialization = 'AI w Medycynie'
    else:
        specialization = 'Ogólne'
    return {'phase': phase, 'specialization': specialization}


def classify_ai_medicine(text):
    ai_kw = ['llm', 'gpt', 'claude', 'llama', 'foundation model', 'model fundamentowy',
             'artificial intelligence', 'machine learning', 'digital health', 'zdrowie cyfrowe']
    if not any(kw in text for kw in ai_kw):
        return None
    if any(w in text for w in ['approval', 'fda', 'ema', 'zatwierdzono', 'rejestracja']):
        category = 'Zatwierdzenia/Regulacje'
    elif any(w in text for w in ['llm', 'gpt', 'claude', 'llama', 'foundation model', 'model fundamentowy']):
        category = 'Modele LLM'
    elif any(w in text for w in ['app', 'software', 'digital health', 'zdrowie cyfrowe', 'aplikacja']):
        category = 'Digital Health'
    else:
        category = 'Badania AI'
    return {'ai_category': category}


def classify_guidelines(text):
    guideline_kw = ['guideline', 'wytyczne', 'recommendation', 'rekomendacj']
    if not any(kw in text for kw in guideline_kw):
        return None
    change_kw = ['updated', 'revised', 'new version', 'nowe wytyczne', 'aktualizacja',
                 'znowelizowano', 'nowe rekomendacje']
    if any(kw in text for kw in change_kw):
        return {'is_update': True, 'change_type': 'Aktualizacja'}
    return {'is_update': False, 'change_type': 'Nowa Rekomendacja'}


def classify_legal(text):
    legal_kw = ['prawo medyczne', 'ustawa', 'rozporządzenie', 'dziennik ustaw',
                'isap.gov.pl', 'eur-lex', 'nil.org.pl', 'dziennikustaw.gov.pl',
                'sejm', 'senat', 'głosowanie', 'nowelizacja', 'projekt ustawy',
                'nowe przepisy', 'zmiana przepisów', 'obowiązek ujawniania', 'pesel']
    return any(kw in text for kw in legal_kw)


def classify_drugs(text):
    drug_kw = ['pharmacy', 'farmacj', 'drug', 'lek ', 'leku', 'leki', 'pharmaceutical']
    return any(kw in text for kw in drug_kw)


def classify_epidemiology(text):
    epi_kw = [
        'outbreak', 'ognisko choroby', 'ognisko zakażeń', 'epidemi', 'pandemi',
        'zachorowania', 'choroby zakaźne', 'zoonoza', 'zoonotic', 'antybiotykoopornoś',
        'antibiotic resistance', 'antimicrobial resistance', 'szczepion', 'vaccination',
        'vaccine', 'travel alert', 'alert podróżny', 'disease outbreak',
        # Specific outbreak-prone diseases - real coverage rarely says "outbreak"
        # explicitly (e.g. "W Kongo rośnie bilans ofiar eboli"), it just names the disease.
        # Polish inflects disease names ("ofiar eboli", "zarażeni cholerą"), so a
        # bare 'ebola'/'cholera' substring check would miss every grammatical case
        # except nominative. Short stems like 'odr'/'choler' would overmatch
        # unrelated words ("podróż", "choleryk"), so spell out the inflected forms
        # actually used in Polish coverage instead of guessing a safe stem.
        'ebol', 'cholera', 'cholerą', 'cholerze', 'cholery', 'odra ', 'odrę', 'odrą', 'odry',
        'grypa ptaków', 'ptasia grypa', 'ospa wietrzn', 'mpox', 'dengue', 'malari',
        'listerioz', 'salmonell', 'gorączk krwotoczn', 'marburg', 'żółt gorączk',
        'dżum', 'wąglik', 'wściekliz',
    ]
    if not any(kw in text for kw in epi_kw):
        return None
    return {'category': 'Epidemiologia'}


def classify_pharma_market(text):
    market_kw = ['merger', 'acquisition', 'fuzj', 'przejęci', 'ipo', 'strategic partnership',
                 'partnerstwo strategiczne', 'funding round', 'finansowanie startup', 'venture capital',
                 'wyniki finansowe', 'earnings', 'drug pipeline', 'pipeline leków', 'inwestycj',
                 'biotech', 'spółk']
    if not any(kw in text for kw in market_kw):
        return None
    return {'category': 'Rynek'}


def classify_research(text):
    research_kw = ['meta-analysis', 'metaanaliza', 'randomized controlled trial',
                    'badanie z randomizacją', 'rct', 'cohort', 'badanie kohortowe',
                    'case report', 'opis przypadku', 'systematic review', 'przegląd systematyczny',
                    'study', 'badanie']
    if not any(kw in text for kw in research_kw):
        return None
    if 'meta-analysis' in text or 'metaanaliza' in text:
        study_type = 'Meta-analiza'
    elif 'randomized controlled trial' in text or 'badanie z randomizacją' in text or 'rct' in text:
        study_type = 'RCT'
    elif 'cohort' in text or 'badanie kohortowe' in text:
        study_type = 'Badanie kohortowe'
    elif 'case report' in text or 'opis przypadku' in text:
        study_type = 'Case Report'
    elif 'systematic review' in text or 'przegląd systematyczny' in text:
        study_type = 'Systematic Review'
    else:
        study_type = 'Inne'
    return {'study_type': study_type}


def _source_contains(source, *hints):
    s = (source or '').lower()
    return any(h in s for h in hints)


# Google News' <source> tag is rarely the bare publisher name we'd expect - NEJM
# shows up as "The New England Journal of Medicine", Science as "Science | AAAS",
# and every BMJ specialty journal (Frontline Gastroenterology, Annals of the
# Rheumatic Diseases, thorax.bmj.com...) under its own sub-journal name. Exact-set
# membership silently missed all of these, so HIGH_IMPACT/fallback routing matched
# almost nothing; substring hints catch the family regardless of which exact title
# Google News attaches.
HIGH_IMPACT_NAME_HINTS = (
    'nejm', 'new england journal of medicine', 'lancet', 'jama', 'nature medicine',
    'bmj', 'science translational medicine',
    # Elite specialty journals (see SOURCES_WORLD_TOP_JOURNALS) - each domain
    # hosts only journals in its own single specialty, so trusting the whole
    # family by name doesn't risk pulling in off-topic non-medical content the
    # way a broad "cell"/"science" hint would.
    'annals of internal medicine', 'annals.org', 'circulation', 'jacc',
    'american heart association', 'journal of the american college of cardiology',
    'blood advances', 'blood', 'ashpublications.org',
)


def _is_high_impact_source(source):
    return _source_contains(source, *HIGH_IMPACT_NAME_HINTS)


# Home tile for an approved source when nothing more specific matched (no safety/
# trial/AI/epidemic/market/guideline keyword hit). Without this, an NEJM or WHO
# item with a plain headline ("Daraxonrasib in Pancreatic Cancer") falls through to
# the generic Świat/Polska catch-all and "Badania Kliniczne"/"Epidemiologia" stay
# empty even though approved-source content for them existed in this run. Sources
# that are inherently general-purpose outlets (Medonet, Puls Medycyny, Termedia,
# Podyplomie...) are deliberately absent - their natural home already is Polska/Świat.
# Checked in order, substring match against the lowercased outlet name.
SOURCE_FALLBACK_HINTS = [
    # Badania Kliniczne
    ('new england journal of medicine', 'clinical_research.json'),
    ('nejm', 'clinical_research.json'),
    ('lancet', 'clinical_research.json'),
    ('jama', 'clinical_research.json'),
    ('cochrane', 'clinical_research.json'),
    ('pubmed', 'clinical_research.json'),
    ('europe pmc', 'clinical_research.json'),
    ('clinicaltrials.gov', 'clinical_research.json'),
    ('esmo', 'clinical_research.json'),
    ('asco', 'clinical_research.json'),
    ('bmj', 'clinical_research.json'),
    # Regulatory & Drug Safety
    ('fda', 'regulatory_safety.json'),
    ('ema', 'regulatory_safety.json'),
    ('drugs.com', 'regulatory_safety.json'),
    ('urpl', 'regulatory_safety.json'),
    # Wytyczne i Rekomendacje
    ('nice', 'guidelines.json'),
    ('eur-lex', 'guidelines.json'),
    ('nil', 'guidelines.json'),
    ('isap', 'guidelines.json'),
    ('european society of cardiology', 'guidelines.json'),
    ('escardio', 'guidelines.json'),
    ('infectious diseases society', 'guidelines.json'),
    ('idsa', 'guidelines.json'),
    ('agencja oceny technologii medycznych', 'guidelines.json'),
    ('aotmit', 'guidelines.json'),
    # AI w Medycynie
    ('medscape', 'ai_medicine.json'),
    ('nejm ai', 'ai_medicine.json'),
    # Epidemiologia i Zdrowie Publiczne
    ('world health organization', 'epidemiology.json'),
    ('cdc', 'epidemiology.json'),
    ('ecdc', 'epidemiology.json'),
    ('promed', 'epidemiology.json'),
    ('healthmap', 'epidemiology.json'),
    ('eurosurveillance', 'epidemiology.json'),
    ('outbreak news today', 'epidemiology.json'),
    # Rynek Farmaceutyczny i Biotech
    ('stat news', 'pharma_market.json'),
    ('stat | aaas', 'pharma_market.json'),
    ('endpoints news', 'pharma_market.json'),
    ('pink sheet', 'pharma_market.json'),
    ('fiercepharma', 'pharma_market.json'),
    ('fierce pharma', 'pharma_market.json'),
    ('biopharma dive', 'pharma_market.json'),
    ('biospace', 'pharma_market.json'),
    ('rynek aptek', 'pharma_market.json'),
    # --- User-provided source list additions below ---
    # Regulatory & Drug Safety
    ('yellow card', 'regulatory_safety.json'),
    ('mhra', 'regulatory_safety.json'),
    ('drugbank', 'regulatory_safety.json'),
    ('centers for medicare', 'regulatory_safety.json'),
    ('cms.gov', 'regulatory_safety.json'),
    # Wytyczne i Rekomendacje
    ('british national formulary', 'guidelines.json'),
    ('trip database', 'guidelines.json'),
    ('bmj best practice', 'guidelines.json'),
    ('uptodate', 'guidelines.json'),
    ('agencja badań medycznych', 'guidelines.json'),
    ('centrum medyczne kształcenia podyplomowego', 'guidelines.json'),
    ('rzecznik praw pacjenta', 'guidelines.json'),
    ('european commission', 'guidelines.json'),
    ('health.ec.europa.eu', 'guidelines.json'),
    # Epidemiologia i Zdrowie Publiczne
    ('european food safety authority', 'epidemiology.json'),
    ('efsa', 'epidemiology.json'),
    ('pan american health organization', 'epidemiology.json'),
    ('paho', 'epidemiology.json'),
    ('unicef', 'epidemiology.json'),
    ('unaids', 'epidemiology.json'),
    ('iarc', 'epidemiology.json'),
    ('our world in data', 'epidemiology.json'),
    ('narodowy instytut zdrowia publicznego', 'epidemiology.json'),
    ('pzh', 'epidemiology.json'),
    ('główny inspektorat sanitarny', 'epidemiology.json'),
    # Badania Kliniczne (US research bodies + academic publishers)
    ('national institutes of health', 'clinical_research.json'),
    ('national library of medicine', 'clinical_research.json'),
    ('medlineplus', 'clinical_research.json'),
    ('national cancer institute', 'clinical_research.json'),
    ('niaid', 'clinical_research.json'),
    ('nichd', 'clinical_research.json'),
    ('agency for healthcare research and quality', 'clinical_research.json'),
    ('ahrq', 'clinical_research.json'),
    ('mdpi', 'clinical_research.json'),
    ('frontiers in', 'clinical_research.json'),
    ('sciencedirect', 'clinical_research.json'),
    ('springer', 'clinical_research.json'),
    ('wiley', 'clinical_research.json'),
    ('oecd', 'clinical_research.json'),
    ('world bank', 'clinical_research.json'),
    # Polska (PL professional/government bodies without a more specific home)
    ('centrum e-zdrowia', 'news_pl.json'),
    ('naczelna izba pielęgniarek', 'news_pl.json'),
]


def _source_fallback_tile(source):
    s = (source or '').lower()
    if s == 'who':
        return 'epidemiology.json'
    for hint, tile in SOURCE_FALLBACK_HINTS:
        if hint in s:
            return tile
    return None

# Nature and Science cover all of science, not just medicine (astronomy, materials,
# pure biology...). They're on the approved domain list (sources.py), so Google
# News legitimately returns them - but an article about asteroid chemistry doesn't
# belong in a medical tile just because it ran on nature.com. Anything from these
# multi-disciplinary publishers needs an extra medical-relevance check; single-purpose
# medical outlets (NEJM, Lancet, Medonet, Termedia...) don't. Substring match so it
# catches "Science | AAAS" too - but excludes anything with "Medicine" in the name
# (Nature Medicine, Science Translational Medicine), since those self-declare a
# medical-only focus and shouldn't be held to the broader relevance check.
BROAD_SCIENCE_NAME_HINTS = (
    'nature', 'science', 'mdpi', 'frontiers', 'sciencedirect', 'springer', 'wiley',
)


def _is_broad_science_source(source):
    s = (source or '').lower()
    if 'medicine' in s:
        return False
    return any(h in s for h in BROAD_SCIENCE_NAME_HINTS)

MEDICAL_RELEVANCE_KEYWORDS = [
    # Deliberately excludes generic 'health'/'zdrowi' - matches consumer lifestyle
    # pieces ("zdrowy styl życia") just as readily as actual clinical content. But
    # 'medycyn'/'medicine' is kept - specific enough to be a real signal (an AI
    # article that explicitly says "sztuczna inteligencja medyczna" is on-topic).
    'patient', 'pacjent', 'clinical', 'klinicz', 'disease', 'chorob', 'treatment', 'leczeni',
    'therapy', 'terapi', 'drug', 'lek ', 'leku', 'leki', 'cancer', 'nowotwor', 'rak ', 'vaccine',
    'szczepion', 'diagnos', 'surgery', 'chirurgi', 'hospital', 'szpital', 'doctor', 'lekarz',
    'trial', 'badanie klinicz', 'syndrome', 'zespół', 'infection', 'infekcj', 'virus', 'wirus',
    'mutation', 'mutacj', 'genom', 'biomarker', 'wytyczne', 'refundacj', 'recepta', 'antybiotyk',
    'medicine', 'medycyn', 'statyn', 'farmakolog',
]


def _is_medically_relevant(text):
    return any(kw in text for kw in MEDICAL_RELEVANCE_KEYWORDS)


# This is meant to be a useful tool for doctors and medical students, not a
# consumer health-lifestyle feed. Medonet (unlike the rest of SOURCES_PL, which
# are professional/government outlets) mixes real clinical news with curiosity-bait
# lifestyle pieces ("Czy można bezpiecznie jeść smalec?", "Co najbardziej przyciąga
# komary?") - those are approved-domain but not useful here, so they're dropped
# rather than left to clutter the Polska tile.
CONSUMER_PRESS_SOURCES = ('Medonet',)

CLICKBAIT_PATTERNS = [
    'sprawdzamy, czy', 'zagadka rozwiązana', 'wielki powrót', 'co najbardziej przyciąga',
    'ruszała się', 'czy można bezpiecznie', 'to działa jak magnes', 'naprawdę wystarczy',
    'dieta', 'przepis na', 'jak schudnąć', 'odżywianie', 'czy warto', 'sprawdź, czy',
]


def _looks_like_clickbait(text):
    return any(p in text for p in CLICKBAIT_PATTERNS)


# Some PL trade outlets (Termedia's "Przewodnik Lekarza" archive especially) get
# re-indexed by Google News with a fresh crawl date even though the article itself
# is years old ("Opieka długoterminowa w geriatrii ..., Przewodnik Lekarza 10/2006").
# The RSS pubDate alone can't catch this - it reflects when Google (re-)discovered
# the page, not when the underlying issue was published - so check the title itself
# for an old journal-issue citation.
_STALE_CITATION_RE = re.compile(r'/((?:19|20)\d{2})\b')
STALE_CITATION_MAX_AGE_YEARS = 3


def _has_stale_citation_year(title):
    match = _STALE_CITATION_RE.search(title or '')
    if not match:
        return False
    year = int(match.group(1))
    return year <= datetime.now(timezone.utc).year - STALE_CITATION_MAX_AGE_YEARS


# Some government sub-sites (NFZ's "Diety" newsletter section especially) get
# crawled by Google News down to UI chrome, not just articles - "Wyszukaj"
# (Search), "Biuletyn" (Newsletter), "Menu" etc. show up as if they were
# headlines. A real article title is essentially never this short.
MIN_TITLE_LENGTH = 15


def _is_nav_chrome_title(title):
    return len((title or '').strip()) < MIN_TITLE_LENGTH


# Google News occasionally indexes a publisher's account/paywall/login page as
# if it were an article (e.g. NEJM's "Subskrypcje i zakupy" subscriptions
# page) - long enough to pass MIN_TITLE_LENGTH, but it's site chrome, not
# content. Checked against the *translated* Polish title, so both language
# variants are listed.
SITE_CHROME_TITLE_HINTS = (
    'subskrypcje i zakupy', 'subscriptions and purchases', 'subscribe to',
    'zaloguj się', 'log in', 'sign in', 'create your free account',
    'utwórz darmowe konto', 'cookie policy', 'polityka cookie',
    'newsletter sign', 'zapisz się do newslettera', 'privacy policy',
    'polityka prywatności', 'page not found', 'strona nie została znaleziona',
    'access denied', 'odmowa dostępu',
)


def _is_site_chrome_title(title):
    t = (title or '').strip().lower()
    return any(h in t for h in SITE_CHROME_TITLE_HINTS)


# Keyword dictionary for the "Specjalizacja" mode (spec lists 19 fields). An item
# can legitimately match more than one (e.g. "pediatric oncology"), so this tags
# every match rather than picking a single best one.
SPECIALIZATION_KEYWORDS = {
    'Kardiologia': ['cardio', 'kardiolog', 'heart', 'serc', 'coronary', 'arrhythmia', 'arytmi', 'myocard', 'zawał'],
    'Onkologia': ['oncolog', 'onkolog', 'cancer', 'nowotwor', 'rak ', 'tumor', 'guz ', 'chemotherap', 'chemioterap'],
    'Neurologia': ['neurolog', 'brain', 'mózg', 'stroke', 'udar', 'epilep', 'padaczk', 'parkinson', 'alzheimer', 'demencj'],
    'Psychiatria': ['psychiatr', 'depress', 'depresj', 'anxiety', 'lęk', 'schizophren', 'schizofreni', 'mental health', 'zdrowie psychiczne'],
    'Endokrynologia i diabetologia': ['endocrin', 'endokrynolog', 'diabet', 'cukrzyc', 'thyroid', 'tarczyc', 'insulin', 'hormon'],
    'Gastroenterologia i hepatologia': ['gastroenterolog', 'hepatolog', 'liver', 'wątrob', 'stomach', 'żołądk', 'bowel', 'jelit', 'cirrhosis', 'marskoś'],
    'Nefrologia': ['nephrolog', 'nefrolog', 'kidney', 'nerk', 'dialysis', 'dializ', 'renal'],
    'Pulmonologia': ['pulmonolog', 'lung', 'płuc', 'respiratory', 'oddechow', 'asthma', 'astma', 'copd', 'pochp'],
    'Hematologia': ['hematolog', 'blood', 'krwi', 'anemia', 'anemi', 'leukemia', 'leukemi', 'lymphoma', 'chłoniak'],
    'Choroby zakaźne': ['infectious disease', 'choroby zakaźne', 'infection', 'infekcj', 'virus', 'wirus', 'bacteria', 'bakteri', 'sepsis', 'sepsa'],
    'Reumatologia i immunologia': ['rheumatolog', 'reumatolog', 'arthritis', 'zapalenie staw', 'autoimmune', 'autoimmunolog', 'lupus', 'toczeń'],
    'Pediatria': ['pediatr', 'children', 'dzieci', 'child ', 'infant', 'niemowl', 'newborn', 'noworod'],
    'Ginekologia i położnictwo': ['gynecolog', 'ginekolog', 'obstetric', 'położnictw', 'pregnan', 'ciąż', 'menstrual', 'menopaus', 'menopauz'],
    'Chirurgia': ['surgery', 'chirurgi', 'surgical', 'operacj', 'transplant', 'przeszczep'],
    'Ortopedia i traumatologia': ['orthoped', 'ortoped', 'fracture', 'złaman', 'joint replacement', 'bone', 'kość', 'trauma'],
    'Urologia': ['urolog', 'prostate', 'prostat', 'bladder', 'pęcherz moczow'],
    'Dermatologia': ['dermatolog', 'skin', 'skór', 'eczema', 'egzem', 'psoriasis', 'łuszczyc', 'melanoma', 'czerniak'],
    'Okulistyka': ['ophthalm', 'okulist', 'eye ', 'oko ', 'retina', 'siatkówk', 'glaucoma', 'jaglic', 'cataract', 'zaćm'],
    'Anestezjologia i intensywna terapia': ['anesthes', 'anestezjolog', 'intensive care', 'intensywn', ' icu ', 'sedation', 'sedacj'],
    'Radiologia i diagnostyka obrazowa': ['radiolog', 'imaging', 'obrazow', 'mri', 'rezonans', 'ct scan', 'tomograf', 'ultrasound', 'ultrasonograf', 'x-ray', 'rentgen'],
}


def detect_specializations(text):
    return [spec for spec, kws in SPECIALIZATION_KEYWORDS.items() if any(kw in text for kw in kws)]


def is_alert(item, text):
    return any(kw in text for kw in ALERT_KEYWORDS)


def classify(item, origin):
    """
    Mutates `item` with tile-specific fields and returns the target filename
    (without directory) it should be saved to, or None if the item should be
    dropped entirely (off-topic content from a multi-disciplinary publisher).
    `origin` is 'pl', 'world' or 'pubmed' and decides the fallback news bucket.

    Tiles follow the 7-tile spec: Polska (news_pl), Badania Kliniczne
    (clinical_research.json - trial registrations + RCT/meta-analysis/cohort/case
    report results, merged into one bucket so neither half sits empty), Regulatory
    & Drug Safety (regulatory_safety.json, now also covers drug news), Wytyczne i
    Rekomendacje (guidelines.json, now also covers legal/regulatory-text changes),
    AI w Medycynie (ai_medicine.json), Epidemiologia i Zdrowie Publiczne
    (epidemiology.json), Rynek Farmaceutyczny i Biotech (pharma_market.json).
    """
    text = _text_of(item)
    source = item.get('source', '')

    if _is_nav_chrome_title(item.get('title', '')) or _is_site_chrome_title(item.get('title', '')):
        return None

    if _has_stale_citation_year(item.get('title', '')):
        return None

    if _is_broad_science_source(source) and not _is_medically_relevant(text):
        return None

    # Tagged on every item regardless of tile, so the "Specjalizacja" view can
    # filter the whole dashboard (hero + all tiles) down to one medical field.
    item['specializations'] = detect_specializations(text)

    safety_level = classify_regulatory_safety(text)
    if safety_level:
        item['safety_level'] = safety_level
        return 'regulatory_safety.json'

    trial_info = classify_clinical_trial(text)
    research_info = classify_research(text)
    if trial_info or research_info:
        if research_info:
            item.update(research_info)
        if trial_info:
            item.update(trial_info)
        if _is_high_impact_source(source):
            return 'clinical_intelligence.json'
        return 'clinical_research.json'

    ai_info = classify_ai_medicine(text)
    if ai_info:
        item.update(ai_info)
        return 'ai_medicine.json'

    epi_info = classify_epidemiology(text)
    if epi_info:
        item.update(epi_info)
        return 'epidemiology.json'

    pharma_info = classify_pharma_market(text)
    if pharma_info:
        item.update(pharma_info)
        return 'pharma_market.json'

    guideline_info = classify_guidelines(text)
    if guideline_info:
        item.update(guideline_info)
        return 'guidelines.json'

    if classify_legal(text):
        # Polish legal/parliamentary news about practice obligations (e.g. Sejm
        # requiring doctors to disclose patients' PESEL numbers for billing) is
        # exactly what a PL doctor expects to find in the Polska tile, not buried
        # in Wytyczne i Rekomendacje (which is for clinical-practice guidelines,
        # international ones especially). Non-PL legal sources (EUR-Lex...) still
        # belong in Wytyczne.
        return 'news_pl.json' if origin == 'pl' else 'guidelines.json'

    if classify_drugs(text):
        return 'regulatory_safety.json'

    if _is_high_impact_source(source):
        return 'clinical_intelligence.json'

    fallback_tile = _source_fallback_tile(source)
    if fallback_tile:
        return fallback_tile

    # Nothing specific matched - this is the generic Polska/Świat catch-all. This
    # is a tool for doctors and medical students, not a consumer health-lifestyle
    # feed, so a consumer-press item only earns a spot here if it has *some* real
    # clinical substance or is obvious clickbait-phrased; "Co najbardziej przyciąga
    # komary?" doesn't, "Opieka długoterminowa w geriatrii" does. Professional/
    # government PL sources (mp.pl, Termedia, NFZ, MZ...) are never subject to this -
    # they don't run lifestyle clickbait in the first place.
    if any(s in source for s in CONSUMER_PRESS_SOURCES):
        if _looks_like_clickbait(text) or not _is_medically_relevant(text):
            return None

    return 'news_pl.json' if origin == 'pl' else 'news_world.json'


def _parse_date(date_str):
    if not date_str or date_str == 'Recent':
        return None
    try:
        parsed = date_parser.parse(date_str)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return None


def _is_recent(date_str, window_days=MAX_AGE_DAYS):
    parsed = _parse_date(date_str)
    if not parsed:
        return False
    now = datetime.now(timezone.utc)
    age = now - parsed
    return timedelta(0) <= age <= timedelta(days=window_days)


def _load(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def _save(path, items):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def _passes_quality_gate(item, is_catchall):
    """Re-applies the relevance/clickbait gates from classify() to *already
    saved* items too, not just freshly collected ones. Without this, an item
    saved before a quality rule existed (or before a rule was tightened) would
    keep reappearing on every merge for up to MAX_AGE_DAYS, since _merge_and_save
    normally only classifies new items - existing ones are trusted as-is.
    `is_catchall` mirrors classify()'s consumer-press check, which only applies to
    the generic Polska/Świat bucket - an item already routed into a specific tile
    earned that spot via a strong keyword signal and shouldn't be second-guessed."""
    text = _text_of(item)
    source = item.get('source', '')
    if _is_nav_chrome_title(item.get('title', '')) or _is_site_chrome_title(item.get('title', '')):
        return False
    if _has_stale_citation_year(item.get('title', '')):
        return False
    if _is_broad_science_source(source) and not _is_medically_relevant(text):
        return False
    if is_catchall:
        if any(s in source for s in CONSUMER_PRESS_SOURCES):
            if _looks_like_clickbait(text) or not _is_medically_relevant(text):
                return False
        # An item sitting in the generic Polska/Świat catch-all that would now
        # match a specific tile's classifier belongs there instead - e.g. a
        # Medonet piece about an Ebola outbreak in DRC is "Epidemiologia", not
        # "Polska", even though Medonet is a PL source. Re-checking this against
        # *today's* classifiers (not just the ones active when it was first
        # saved) is what keeps already-persisted items from drifting out of sync
        # as the rules get tightened.
        if (classify_regulatory_safety(text) or classify_clinical_trial(text) or classify_research(text)
                or classify_ai_medicine(text) or classify_epidemiology(text) or classify_pharma_market(text)
                or classify_guidelines(text) or classify_legal(text) or classify_drugs(text)):
            return False
    return True


def _merge_and_save(path, new_items, enrich_budget=None, window_days=MAX_AGE_DAYS):
    is_catchall = os.path.basename(path) in ('news_pl.json', 'news_world.json')
    existing = [it for it in _load(path) if _passes_quality_gate(it, is_catchall)]
    combined = new_items + existing
    seen = set()
    deduped = []
    for it in combined:
        # Title first: enrichment (see enrich_redundant_summaries) can rewrite an
        # item's `url` from a Google News redirect to the decoded publisher URL on
        # a later run, which would otherwise make the same article dedupe as "new"
        # every time and double up in the feed.
        key = (it.get('title') or it.get('url') or '').strip().lower()
        if not key or key in seen:
            continue
        if not _is_recent(it.get('date'), window_days=window_days):
            continue
        seen.add(key)
        deduped.append(it)

    def sort_key(it):
        parsed = _parse_date(it.get('date'))
        return parsed.timestamp() if parsed else 0

    deduped.sort(key=sort_key, reverse=True)
    final_items = deduped[:20]

    # Only the items that actually survive dedup/recency/truncation are ever shown,
    # so only spend the enrichment budget (one outbound fetch per item) on those -
    # not on the hundreds of raw candidates (including years-old ones) that classify()
    # bucketed but that never make it past this filter. `enrich_budget` is a shared
    # [remaining] counter mutated in place across all buckets in one run.
    if enrich_budget is not None:
        enrich_redundant_summaries(final_items, _translate_to_pl, budget=enrich_budget)

    _save(path, final_items)
    logger.info("Saved %d items to %s", len(final_items), path)


def _translate_to_pl(text):
    from deep_translator import GoogleTranslator
    try:
        return GoogleTranslator(source='auto', target='pl').translate(text)
    except Exception as e:
        logger.error("Translation error during enrichment: %s", e)
        return text


def classify_and_save(items_with_origin):
    """
    items_with_origin: list of (item, origin) tuples.
    Buckets every item into its target tile file and additionally collects
    alert-worthy items into alerts.json.
    """
    buckets = {}
    alert_items = []

    for item, origin in items_with_origin:
        target = classify(item, origin)
        if target is None:
            continue  # off-topic content from a multi-disciplinary publisher
        buckets.setdefault(target, []).append(item)

        # Ticker is for breaking/current threats only - restrict candidates to the
        # tiles whose entire purpose is safety/outbreak signals, not every tile
        # (a loosely-worded "alert" keyword hit in, say, Polska news isn't one).
        if target in ('regulatory_safety.json', 'epidemiology.json'):
            text = _text_of(item)
            if is_alert(item, text):
                alert_items.append({**item, 'type': 'ALERT'})

    # Strict 7-day freshness window everywhere - the user wants the dashboard to
    # only ever show the newest medical news, never older "evergreen" coverage,
    # even at the cost of a tile sometimes having few or no items in a given run.
    enrich_budget = [ENRICH_BUDGET_PER_RUN]
    ordered_targets = sorted(
        buckets.keys(),
        key=lambda t: TILE_SAVE_PRIORITY.index(t) if t in TILE_SAVE_PRIORITY else len(TILE_SAVE_PRIORITY),
    )
    for target in ordered_targets:
        _merge_and_save(os.path.join(DATA_DIR, target), buckets[target], enrich_budget=enrich_budget)

    if alert_items:
        # Tighter than the regular 7-day tile window - the ticker is for breaking
        # threats happening *now*, not anything still technically "this week".
        _merge_and_save(os.path.join(DATA_DIR, 'alerts.json'), alert_items, window_days=2)
