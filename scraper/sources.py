"""
Central registry of medical source domains used by the broad collectors.

Replaces the old per-tile narrow Google News queries (one query per topic tile)
with two broad queries (PL / World) that pull every recent article from the
approved domain list. Classification into topical tiles happens afterwards
in classify.py, so an article is never lost just because it didn't match a
narrow per-tile keyword query.
"""

SOURCES_PL = [
    "mp.pl",
    "pulsmedycyny.pl",
    "termedia.pl",
    "rynekzdrowia.pl",
    "medonet.pl",
    "nfz.gov.pl",
    "pacjent.gov.pl",
    "gov.pl/zdrowie",
    "isap.gov.pl",
    "dziennikurzedowy.gov.pl",
    "nil.org.pl",
    "urpl.gov.pl",
    "ptk.org.pl",
    "pto.org.pl",
]

SOURCES_WORLD = [
    "nejm.org",
    "thelancet.com",
    "jamanetwork.com",
    "bmj.com",
    "nature.com",
    "science.org",
    "translationalscience.org",
    "cochranelibrary.com",
    "medscape.com",
    "statnews.com",
    "who.int",
    "fda.gov",
    "ema.europa.eu",
    "cdc.gov",
    "ecdc.europa.eu",
    "clinicaltrials.gov",
    "clinicaltrialsregister.eu",
    "drugs.com",
    "endpointsnews.com",
    "arxiv.org",
    "medrxiv.org",
    "nice.org.uk",
    "esmo.org",
    "asco.org",
    "pubmed.ncbi.nlm.nih.gov",
    "europepmc.org",
]


def build_site_query(domains):
    return "(" + " OR ".join(f"site:{d}" for d in domains) + ")"


PL_QUERY = f"{build_site_query(SOURCES_PL)}+medycyna"
WORLD_QUERY = f"{build_site_query(SOURCES_WORLD)}+medicine"

PL_RSS_URL = f"https://news.google.com/rss/search?q={PL_QUERY}&hl=pl&gl=PL&ceid=PL:pl"
WORLD_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY}&hl=en-US&gl=US&ceid=US:en"

PUBMED_RSS_URL = "https://pubmed.ncbi.nlm.nih.gov/rss/search?term=medicine"

GIS_WARNINGS_URL = "https://www.gov.pl/web/gis/ostrzezenia"
