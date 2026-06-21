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
    "podyplomie.pl",
    "rynekzdrowia.pl",
    "medonet.pl",
    "nfz.gov.pl",
    "pacjent.gov.pl",
    "gov.pl/zdrowie",
    "isap.gov.pl",
    "dziennikustaw.gov.pl",
    "nil.org.pl",
    "urpl.gov.pl",
    "ptk.org.pl",
    "pto.org.pl",
    # Added on request to keep every tile populated: still professional/government
    # bodies, not random blogs - HTA/guidelines authority and pharma trade press.
    "aotm.gov.pl",
    "rynekaptek.pl",
]

# Google News RSS caps results at ~100 items per query and ranks by its own
# relevance/authority signal, not by domain count - lumping all ~35 world domains
# into one query meant NEJM/Nature/JAMA/BMJ/Science/Medscape/Cochrane (high
# publication volume, high "authority") filled the entire 100-item page every
# time, and smaller-but-still-credible outlets (ESC, IDSA, Eurosurveillance,
# Fierce Pharma, BioSpace...) never appeared at all - confirmed by querying them
# alone and getting 100 results back instantly. Splitting into separate queries
# per group gives each its own dedicated result page instead of competing in one.
SOURCES_WORLD_MAJOR = [
    "nejm.org",
    "thelancet.com",
    "jamanetwork.com",
    "bmj.com",
    "nature.com",
    "science.org",
    "cochranelibrary.com",
    "medscape.com",
]

# WHO/CDC/FDA alone are prolific enough (government press output) to fill the
# 100-result cap on their own, so they get split out from the smaller guideline
# bodies/repositories below - otherwise the latter never appear either, exactly
# like the major journals crowded out everyone in the original single query.
SOURCES_WORLD_REGULATORS = [
    "who.int",
    "fda.gov",
    "ema.europa.eu",
    "cdc.gov",
    "ecdc.europa.eu",
]

SOURCES_WORLD_GUIDELINES_RESEARCH = [
    "translationalscience.org",
    "promedmail.org",
    "healthmap.org",
    "clinicaltrials.gov",
    "clinicaltrialsregister.eu",
    "drugs.com",
    "eur-lex.europa.eu",
    "arxiv.org",
    "medrxiv.org",
    "nice.org.uk",
    "esmo.org",
    "asco.org",
    "pubmed.ncbi.nlm.nih.gov",
    "europepmc.org",
    "escardio.org",          # European Society of Cardiology guidelines -> Wytyczne
    "idsociety.org",         # Infectious Diseases Society of America guidelines -> Wytyczne
    "eurosurveillance.org",  # ECDC's own peer-reviewed epidemiology journal -> Epidemiologia
    "outbreaknewstoday.com",  # dedicated outbreak-tracking trade press -> Epidemiologia
]

SOURCES_WORLD_MARKET = [
    "statnews.com",
    "endpointsnews.com",
    "pink.pharmaintelligence.informa.com",
    "fiercepharma.com",     # pharma/biotech trade press -> Rynek
    "biopharmadive.com",    # pharma/biotech trade press -> Rynek
    "biospace.com",         # pharma/biotech trade press -> Rynek
]

SOURCES_WORLD = (
    SOURCES_WORLD_MAJOR + SOURCES_WORLD_REGULATORS + SOURCES_WORLD_GUIDELINES_RESEARCH + SOURCES_WORLD_MARKET
)


def build_site_query(domains):
    return "(" + " OR ".join(f"site:{d}" for d in domains) + ")"


# No "+medycyna"/"+medicine" keyword suffix - every domain here is already a
# medical/health-specific outlet (that's what makes it "approved" in the first
# place), so requiring the literal word too was a second, redundant filter that
# silently starved entire sources (verified: removing it took a 0-article test
# query against ESC/NICE/Fierce Pharma/BioSpace from 0 to 100 results).
PL_QUERY = build_site_query(SOURCES_PL)
WORLD_QUERY = build_site_query(SOURCES_WORLD_MAJOR)
WORLD_QUERY_REGULATORS = build_site_query(SOURCES_WORLD_REGULATORS)
WORLD_QUERY_GUIDELINES_RESEARCH = build_site_query(SOURCES_WORLD_GUIDELINES_RESEARCH)
WORLD_QUERY_MARKET = build_site_query(SOURCES_WORLD_MARKET)

PL_RSS_URL = f"https://news.google.com/rss/search?q={PL_QUERY}&hl=pl&gl=PL&ceid=PL:pl"
WORLD_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY}&hl=en-US&gl=US&ceid=US:en"
WORLD_REGULATORS_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_REGULATORS}&hl=en-US&gl=US&ceid=US:en"
WORLD_GUIDELINES_RESEARCH_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_GUIDELINES_RESEARCH}&hl=en-US&gl=US&ceid=US:en"
WORLD_MARKET_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_MARKET}&hl=en-US&gl=US&ceid=US:en"

PUBMED_RSS_URL = "https://pubmed.ncbi.nlm.nih.gov/rss/search?term=medicine"

GIS_WARNINGS_URL = "https://www.gov.pl/web/gis/ostrzezenia"
