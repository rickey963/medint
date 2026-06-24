"""
Central registry of approved MEDINT dashboard sources, grouped by tile.

Every source listed here was explicitly requested by the user - no others
are used. Each entry is (display_name, feed_url, kind):
  - kind == 'rss': the publisher's own native RSS feed.
  - kind == 'google_news': the source is reached through a site:-scoped
    Google News query instead of a native feed. This mirrors the approach
    already proven in this exact project before the rewrite (the old
    scraper/sources.py used Google News for literally every medical source,
    because native RSS for these domains is either absent, unstable, or
    sits behind bot protection) - so every source here uses it uniformly
    for predictable, low-maintenance behaviour.

One query per individual source (not grouped multi-domain queries) - the old
version of this file had to split sources into volume tiers because lumping
many domains into a single Google News query let the highest-volume ones
crowd out the rest. With one dedicated query per source that problem can't
occur, matching the same technique osint/scraper/sources.py uses for its
handful of Google-News-backed sources.
"""
import urllib.parse

GOOGLE_NEWS_BASE = "https://news.google.com/rss/search?q={query}{locale}"
GOOGLE_NEWS_LOCALE_PL = "&hl=pl&gl=PL&ceid=PL:pl"
GOOGLE_NEWS_LOCALE_EN = "&hl=en-US&gl=US&ceid=US:en"


def _google_news_url(domain, when="3d", locale=True, extra=None):
    # 3d (not 1d) so low-volume domains reliably return candidates -
    # fetch_data.py's own FRESHNESS_WINDOW_HOURS=72 already enforces the
    # real cutoff, so widening this just gives the dedupe/freshness filter
    # more to work with instead of starving it.
    #
    # locale=True (Polish edition) for Polish-language sources; locale=False
    # (global/English edition) for international medical sources, the same
    # split osint uses between its Polish outlets and global wire services.
    query = f"site:{domain}"
    if extra:
        query += f" {extra}"
    query += f" when:{when}"
    return GOOGLE_NEWS_BASE.format(
        query=urllib.parse.quote_plus(query),
        locale=GOOGLE_NEWS_LOCALE_PL if locale else GOOGLE_NEWS_LOCALE_EN,
    )


# --- 1. Polska ---------------------------------------------------------------
SOURCES_POLSKA = [
    ("Medycyna Praktyczna", _google_news_url("mp.pl"), "google_news"),
    ("Puls Medycyny", _google_news_url("pulsmedycyny.pl"), "google_news"),
    ("Termedia", _google_news_url("termedia.pl"), "google_news"),
    ("Medycyna po Dyplomie", _google_news_url("podyplomie.pl"), "google_news"),
    ("Rynek Zdrowia", _google_news_url("rynekzdrowia.pl"), "google_news"),
    ("Medonet", _google_news_url("medonet.pl"), "google_news"),
    ("Narodowy Fundusz Zdrowia", _google_news_url("nfz.gov.pl"), "google_news"),
    ("Internetowe Konto Pacjenta", _google_news_url("pacjent.gov.pl"), "google_news"),
    # gov.pl hosts every ministry under one domain, so site: alone is too
    # broad - the ministry name keeps the query scoped to actual MZ news.
    ("Ministerstwo Zdrowia RP", _google_news_url("gov.pl", extra='"Ministerstwo Zdrowia"'), "google_news"),
    ("alertmedyczny.pl", _google_news_url("alertmedyczny.pl"), "google_news"),
]

# --- 2. Świat -----------------------------------------------------------------
SOURCES_SWIAT = [
    ("Medscape", _google_news_url("medscape.com", locale=False), "google_news"),
    ("NEJM", _google_news_url("nejm.org", locale=False), "google_news"),
    ("The BMJ", _google_news_url("bmj.com", locale=False), "google_news"),
    ("STAT News", _google_news_url("statnews.com", locale=False), "google_news"),
    # nature.com hosts every Nature-family journal, so the journal name keeps
    # this scoped to Nature Medicine instead of Nature's full science output.
    ("Nature Medicine", _google_news_url("nature.com", locale=False, extra='"Nature Medicine"'), "google_news"),
    ("WHO", _google_news_url("who.int", locale=False), "google_news"),
    ("The Lancet", _google_news_url("thelancet.com", locale=False), "google_news"),
    ("Cochrane Library", _google_news_url("cochranelibrary.com", locale=False), "google_news"),
]

# --- 3. Epidemiologia i zdrowie publiczne -------------------------------------
SOURCES_EPIDEMIOLOGIA = [
    # who.int also feeds the "Świat" tile above - this query is scoped to the
    # Disease Outbreak News stream specifically, not WHO's general news.
    ("WHO Disease Outbreak News", _google_news_url("who.int", locale=False, extra='"Disease Outbreak News"'), "google_news"),
    ("ECDC", _google_news_url("ecdc.europa.eu", locale=False), "google_news"),
    ("CDC Outbreaks", _google_news_url("cdc.gov", locale=False, extra="outbreak"), "google_news"),
    ("ProMED", _google_news_url("promedmail.org", locale=False), "google_news"),
    ("HealthMap", _google_news_url("healthmap.org", locale=False), "google_news"),
]

# --- 4. Badania kliniczne ------------------------------------------------------
# Not part of the user's original source list (no category covers clinical
# trials) - filled with the two official trial registries on the user's
# explicit instruction, since both already proved reliable in the old
# version of this project.
SOURCES_BADANIA_KLINICZNE = [
    ("ClinicalTrials.gov", _google_news_url("clinicaltrials.gov", locale=False), "google_news"),
    ("EU Clinical Trials Register", _google_news_url("euclinicaltrials.eu", locale=False), "google_news"),
]

# --- 5. Rynek farmaceutyczny i Biotech ------------------------------------------
SOURCES_RYNEK_FARMACEUTYCZNY = [
    ("Drugs.com", _google_news_url("drugs.com", locale=False), "google_news"),
    ("EMA", _google_news_url("ema.europa.eu", locale=False), "google_news"),
    ("FDA Drug News", _google_news_url("fda.gov", locale=False, extra="drug"), "google_news"),
    ("Pink Sheet", _google_news_url("pink.pharmaintelligence.informa.com", locale=False), "google_news"),
    ("Endpoints News", _google_news_url("endpointsnews.com", locale=False), "google_news"),
]

# --- 6. Wytyczne i rekomendacje --------------------------------------------------
# "Rynek Zdrowia" from the user's legal-changes list is deliberately not
# repeated here - it already lives in the Polska tile above, and the user
# asked not to duplicate sources across tiles.
SOURCES_WYTYCZNE = [
    ("ISAP", _google_news_url("isap.sejm.gov.pl"), "google_news"),
    ("Dziennik Ustaw RP", _google_news_url("dziennikustaw.gov.pl"), "google_news"),
    ("Naczelna Izba Lekarska", _google_news_url("nil.org.pl"), "google_news"),
    ("EUR-Lex Health Law", _google_news_url("eur-lex.europa.eu", extra='zdrowie OR "health law"'), "google_news"),
]

ALL_SECTIONS = {
    "poland": SOURCES_POLSKA,
    "world": SOURCES_SWIAT,
    "epidemiology": SOURCES_EPIDEMIOLOGIA,
    "clinical_trials": SOURCES_BADANIA_KLINICZNE,
    "pharma_market": SOURCES_RYNEK_FARMACEUTYCZNY,
    "guidelines": SOURCES_WYTYCZNE,
}
