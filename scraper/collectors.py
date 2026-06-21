"""
Broad collectors: pull every recent medical article from the approved source
list (sources.py) without pre-filtering by topic. Topic assignment happens
later in classify.py.

Replaces the old one-narrow-query-per-tile scrapers, which could silently
drop a relevant article just because it didn't match that tile's specific
keyword query.
"""

import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

from base_scraper import BaseScraper
import sources

logger = logging.getLogger(__name__)


def _strip_outlet_suffix(text, outlet):
    """Google News appends the outlet name to both <title> (" - Outlet") and
    <description> ("  Outlet", no dash) of every item. Left in place, that suffix
    gets fed to the translator together with the real title and can come back
    mistranslated (e.g. "... - Nature" -> "... - Natura"), so strip it first."""
    if not text or not outlet:
        return text
    stripped = text.rstrip()
    for sep in (f" - {outlet}", outlet):
        if stripped.lower().endswith(sep.lower()):
            stripped = stripped[: len(stripped) - len(sep)].rstrip(' -–—')
            break
    return stripped


def _clean_summary(description, raw_title, outlet=None):
    # Google News RSS <description> is itself HTML-as-text (an <a> with the title,
    # then "&nbsp;&nbsp;<font>Outlet</font>"). It must be unescaped/stripped to plain
    # text BEFORE we try to remove the trailing outlet name - removing the suffix on
    # the raw markup string just leaves "</font>" at the end and does nothing.
    clean_desc = BeautifulSoup(description, "html.parser").get_text().strip()
    clean_desc = _strip_outlet_suffix(clean_desc, outlet)
    if clean_desc.lower().startswith(raw_title.lower()):
        clean_desc = clean_desc[len(raw_title):].strip()
    sentences = re.split(r'(?<=[.!?])\s+', clean_desc)
    summary = " ".join(sentences[:4])
    if len(sentences) > 4:
        summary += "..."
    return summary


def _parse_google_news_rss(html, helper, default_source):
    """Parses a Google News RSS feed, pulling the real outlet name from the
    <source> tag (Google News always includes it) instead of a generic label,
    so source-prestige based ranking actually works."""
    soup = BeautifulSoup(html, 'lxml-xml')
    items = []
    for article in soup.find_all('item'):
        title_tag = article.find('title')
        link_tag = article.find('link')
        pub_date_tag = article.find('pubDate')
        description_tag = article.find('description')
        source_tag = article.find('source')

        if not (title_tag and link_tag):
            continue

        raw_title = title_tag.get_text(strip=True)
        link = link_tag.get_text(strip=True)
        raw_date = pub_date_tag.get_text(strip=True) if pub_date_tag else "Recent"
        description = description_tag.get_text(strip=True) if description_tag else ""
        outlet = source_tag.get_text(strip=True) if source_tag else default_source

        raw_title = _strip_outlet_suffix(raw_title, outlet)
        summary_raw = _clean_summary(description, raw_title, outlet)

        items.append({
            'title': helper.translate_text(raw_title),
            'url': link,
            'date': helper.format_date(raw_date),
            'summary': helper.translate_text(summary_raw),
            'source': outlet,
        })
    return items


def fetch_pl():
    helper = BaseScraper('PL-Collector', sources.PL_RSS_URL, '', lang='pl')
    html = helper.fetch_html()
    if not html:
        return []
    return _parse_google_news_rss(html, helper, default_source='Polska')


def fetch_pl_gov_policy():
    """Separate query for PL government/policy/legal sources (NFZ, Sejm, MZ,
    AOTM, URPL, NIL, prawo.pl...) - Termedia/Medonet/Medycyna Praktyczna alone
    filled the combined query's 100-result cap, so these never appeared. See
    sources.py."""
    helper = BaseScraper('PL-Gov-Policy-Collector', sources.PL_GOV_POLICY_RSS_URL, '', lang='pl')
    html = helper.fetch_html()
    if not html:
        return []
    return _parse_google_news_rss(html, helper, default_source='Polska')


def fetch_world():
    helper = BaseScraper('World-Collector', sources.WORLD_RSS_URL, '', lang='pl')
    html = helper.fetch_html()
    if not html:
        return []
    return _parse_google_news_rss(html, helper, default_source='Świat')


def fetch_world_regulators():
    """Separate query for high-volume government regulators (WHO/CDC/FDA/EMA/ECDC) -
    see sources.py for why this can't just be folded into fetch_world()."""
    helper = BaseScraper('World-Regulators-Collector', sources.WORLD_REGULATORS_RSS_URL, '', lang='pl')
    html = helper.fetch_html()
    if not html:
        return []
    return _parse_google_news_rss(html, helper, default_source='Świat')


def fetch_world_guidelines_research():
    """Separate query for smaller guideline bodies/research repositories - would
    otherwise get crowded out by WHO/CDC/FDA's publication volume. See sources.py."""
    helper = BaseScraper('World-Guidelines-Research-Collector', sources.WORLD_GUIDELINES_RESEARCH_RSS_URL, '', lang='pl')
    html = helper.fetch_html()
    if not html:
        return []
    return _parse_google_news_rss(html, helper, default_source='Świat')


def fetch_world_market():
    """Separate query for pharma/biotech market trade press - see sources.py."""
    helper = BaseScraper('World-Market-Collector', sources.WORLD_MARKET_RSS_URL, '', lang='pl')
    html = helper.fetch_html()
    if not html:
        return []
    return _parse_google_news_rss(html, helper, default_source='Świat')


def fetch_world_intl_orgs():
    """Separate query for EU/international health bodies (EFSA, PAHO, UNICEF,
    OECD, World Bank, UNAIDS, IARC...) - see sources.py."""
    helper = BaseScraper('World-Intl-Orgs-Collector', sources.WORLD_INTL_ORGS_RSS_URL, '', lang='pl')
    html = helper.fetch_html()
    if not html:
        return []
    return _parse_google_news_rss(html, helper, default_source='Świat')


def fetch_world_us_gov():
    """Separate query for US federal health agencies beyond CDC/FDA (NIH, NLM,
    MedlinePlus, AHRQ, CMS, NCI, NIAID, NICHD) - see sources.py."""
    helper = BaseScraper('World-US-Gov-Collector', sources.WORLD_US_GOV_RSS_URL, '', lang='pl')
    html = helper.fetch_html()
    if not html:
        return []
    return _parse_google_news_rss(html, helper, default_source='Świat')


def fetch_world_academic_publishers():
    """Separate query for large multi-disciplinary academic publishers (MDPI,
    Frontiers, ScienceDirect, Springer, Wiley) - see sources.py for why these
    need their own query (high volume) and the off-topic relevance gate."""
    helper = BaseScraper('World-Academic-Publishers-Collector', sources.WORLD_ACADEMIC_PUBLISHERS_RSS_URL, '', lang='pl')
    html = helper.fetch_html()
    if not html:
        return []
    return _parse_google_news_rss(html, helper, default_source='Świat')


def fetch_pubmed():
    helper = BaseScraper('PubMed-Collector', sources.PUBMED_RSS_URL, '', lang='pl')
    html = helper.fetch_html()
    if not html:
        return []
    soup = BeautifulSoup(html, 'lxml-xml')
    items = []
    for article in soup.find_all('item'):
        title_tag = article.find('title')
        link_tag = article.find('link')
        pub_date_tag = article.find('pubDate')
        description_tag = article.find('description')
        if not (title_tag and link_tag):
            continue
        raw_title = title_tag.get_text(strip=True)
        link = link_tag.get_text(strip=True)
        raw_date = pub_date_tag.get_text(strip=True) if pub_date_tag else "Recent"
        description = description_tag.get_text(strip=True) if description_tag else ""
        summary_raw = _clean_summary(description, raw_title)
        items.append({
            'title': helper.translate_text(raw_title),
            'url': link,
            'date': helper.format_date(raw_date),
            'summary': helper.translate_text(summary_raw),
            'source': 'PubMed',
        })
    return items


def fetch_gis_warnings():
    """
    GIS (Główny Inspektorat Sanitarny) has no RSS feed; warnings are listed at
    gov.pl/web/gis/ostrzezenia (previously this pointed at the now-defunct
    /komunikaty path). Each entry shows a title, link and a "DD.MM.YYYY" date.
    """
    helper = BaseScraper('GIS-Collector', sources.GIS_WARNINGS_URL, '', lang='pl')
    html = helper.fetch_html()
    if not html:
        return []
    soup = BeautifulSoup(html, 'lxml')
    items = []
    for link_tag in soup.select('a[href*="/gis/"]'):
        title = link_tag.get_text(strip=True)
        href = link_tag.get('href', '')
        if not title or len(title) < 10 or not href:
            continue
        if not href.startswith('http'):
            href = f"https://www.gov.pl{href}"

        date_str = "Recent"
        container = link_tag.find_parent(['article', 'li', 'div'])
        if container:
            date_match = re.search(r'\b\d{2}\.\d{2}\.\d{4}\b', container.get_text(' ', strip=True))
            if date_match:
                date_str = date_match.group(0)

        items.append({
            'title': title,
            'url': href,
            'date': helper.format_date(date_str),
            'summary': '',
            'source': 'GIS',
        })
    return items


def fetch_all():
    """Returns a list of (item, origin) tuples ready for classify.classify_and_save.

    The ~10 Google News queries are independent HTTP round-trips (split across
    multiple requests in the first place specifically so big publishers don't
    crowd out small ones - see sources.py), so there's no reason to run them
    one after another: that was turning a ~70s slowest-request into a ~12-minute
    sequential wait. Running them concurrently bounds the whole collection step
    to roughly the slowest single request instead of the sum of all of them.
    """
    jobs = [
        (fetch_pl, 'pl'),
        (fetch_pl_gov_policy, 'pl'),
        (fetch_world, 'world'),
        (fetch_world_regulators, 'world'),
        (fetch_world_guidelines_research, 'world'),
        (fetch_world_market, 'world'),
        (fetch_world_intl_orgs, 'world'),
        (fetch_world_us_gov, 'world'),
        (fetch_world_academic_publishers, 'world'),
        (fetch_pubmed, 'pubmed'),
        (fetch_gis_warnings, 'pl'),
    ]
    collected = []
    with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
        future_to_origin = {executor.submit(fn): origin for fn, origin in jobs}
        for future in as_completed(future_to_origin):
            origin = future_to_origin[future]
            try:
                items = future.result()
            except Exception as e:
                logger.error("Collector failed: %s", e)
                items = []
            for item in items:
                collected.append((item, origin))
    return collected
