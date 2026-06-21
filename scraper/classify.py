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
ENRICH_BUDGET_PER_RUN = 70


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


def _fetch_meta_description(url):
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
    Mutates and returns `items`."""
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
        real_url = _decode_google_news_url(url)
        item['url'] = real_url
        if needs_summary:
            description = _fetch_meta_description(real_url)
            if description:
                item['summary'] = translate_fn(description)
    return items

# Same keywords previously hard-coded in src/App.js ALERT_KEYWORDS (kept in sync).
ALERT_KEYWORDS = [
    'wycofan', 'black box', 'ostrzeżenie', 'zagrożenie', 'epidemi',
    'recall', 'fda warning', 'black-box', 'alert', 'outbreak', 'wybuch',
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
                'isap.gov.pl', 'eur-lex', 'nil.org.pl', 'dziennikustaw.gov.pl']
    return any(kw in text for kw in legal_kw)


def classify_drugs(text):
    drug_kw = ['pharmacy', 'farmacj', 'drug', 'lek ', 'leku', 'leki', 'pharmaceutical']
    return any(kw in text for kw in drug_kw)


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


HIGH_IMPACT_SOURCES = {'NEJM', 'The Lancet', 'JAMA', 'Nature Medicine', 'BMJ',
                       'Science Translational Medicine', 'Nature', 'Science'}


def is_alert(item, text):
    return any(kw in text for kw in ALERT_KEYWORDS)


def classify(item, origin):
    """
    Mutates `item` with tile-specific fields and returns the target filename
    (without directory) it should be saved to. `origin` is 'pl', 'world' or
    'pubmed' and decides the fallback news bucket / language.
    """
    text = _text_of(item)

    safety_level = classify_regulatory_safety(text)
    if safety_level:
        item['safety_level'] = safety_level
        return 'regulatory_safety.json'

    trial_info = classify_clinical_trial(text)
    if trial_info:
        item.update(trial_info)
        return 'clinical_trials.json'

    ai_info = classify_ai_medicine(text)
    if ai_info:
        item.update(ai_info)
        return 'ai_medicine.json'

    guideline_info = classify_guidelines(text)
    if guideline_info:
        item.update(guideline_info)
        return 'guidelines.json'

    if classify_legal(text):
        return 'legal.json'

    if classify_drugs(text):
        return 'drugs.json'

    research_info = classify_research(text)
    if research_info:
        item.update(research_info)
        if item.get('source') in HIGH_IMPACT_SOURCES:
            return 'clinical_intelligence.json'
        return 'research.json'

    if item.get('source') in HIGH_IMPACT_SOURCES:
        return 'clinical_intelligence.json'

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


def _merge_and_save(path, new_items, enrich_budget=None):
    existing = _load(path)
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
        if not _is_recent(it.get('date')):
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
        text = _text_of(item)
        target = classify(item, origin)
        buckets.setdefault(target, []).append(item)

        if is_alert(item, text):
            alert_items.append({**item, 'type': 'ALERT'})

    enrich_budget = [ENRICH_BUDGET_PER_RUN]
    for target, bucket_items in buckets.items():
        _merge_and_save(os.path.join(DATA_DIR, target), bucket_items, enrich_budget=enrich_budget)

    if alert_items:
        _merge_and_save(os.path.join(DATA_DIR, 'alerts.json'), alert_items)
