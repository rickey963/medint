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
import json
import logging
from dateutil import parser as date_parser
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/data'))

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
                'isap.gov.pl', 'eur-lex', 'nil.org.pl']
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


def _merge_and_save(path, new_items):
    existing = _load(path)
    combined = new_items + existing
    seen = set()
    deduped = []
    for it in combined:
        key = (it.get('url') or it.get('title') or '').strip().lower()
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
    _save(path, deduped[:20])
    logger.info("Saved %d items to %s", len(deduped[:20]), path)


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

    for target, bucket_items in buckets.items():
        _merge_and_save(os.path.join(DATA_DIR, target), bucket_items)

    if alert_items:
        _merge_and_save(os.path.join(DATA_DIR, 'alerts.json'), alert_items)
