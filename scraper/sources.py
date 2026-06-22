"""
Central registry of medical source domains used by the broad collectors.

Replaces the old per-tile narrow Google News queries (one query per topic tile)
with two broad queries (PL / World) that pull every recent article from the
approved domain list. Classification into topical tiles happens afterwards
in classify.py, so an article is never lost just because it didn't match a
narrow per-tile keyword query.
"""

# Same crowding problem as the world sources (Google News caps a query at ~100
# results, ranked by its own volume/authority signal): Termedia/Medonet/Medycyna
# Praktyczna/Podyplomie alone filled the entire page, so NFZ, Sejm, prawo.pl,
# AOTM, URPL, NIL and every other government/policy source never appeared at
# all - confirmed empirically (one combined query returned 0 of them). Split
# into its own group so government/legal/policy sources get a dedicated page.
SOURCES_PL_MAJOR = [
    "mp.pl",
    "pulsmedycyny.pl",
    "termedia.pl",
    "podyplomie.pl",
    "medonet.pl",
]

SOURCES_PL_GOV_POLICY = [
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
    "rynekzdrowia.pl",
    # Added so Polish health-law votes/changes (e.g. Sejm requiring doctors to
    # disclose patients' PESEL numbers for billing, or doctors' pay) actually get
    # collected - Sejm itself, plus the two main PL legal/health-policy outlets.
    "sejm.gov.pl",
    "prawo.pl",
    "politykazdrowotna.com",
    # User-provided list of additional PL government/professional health bodies.
    "cez.gov.pl",            # Centrum e-Zdrowia
    "pzh.gov.pl",            # Narodowy Instytut Zdrowia Publicznego PZH
    "gov.pl/web/gis",        # Główny Inspektorat Sanitarny (already scraped separately for warnings; now also in the general feed)
    "gov.pl/web/rpp",        # Rzecznik Praw Pacjenta
    "cmkp.edu.pl",           # Centrum Medyczne Kształcenia Podyplomowego
    "gov.pl/web/abm",        # Agencja Badań Medycznych
    "nipip.pl",              # Naczelna Izba Pielęgniarek i Położnych
    "gov.pl/web/konsultanci-krajowi",
]

SOURCES_PL = SOURCES_PL_MAJOR + SOURCES_PL_GOV_POLICY

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
    "euclinicaltrials.eu",
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
    # User-provided drug/EBM reference sites - low Google News volume, safe to
    # fold into this group rather than giving each its own query.
    "yellowcard.mhra.gov.uk",  # UK pharmacovigilance reporting -> Regulatory & Drug Safety
    "go.drugbank.com",         # DrugBank -> Regulatory & Drug Safety
    "bnf.nice.org.uk",         # British National Formulary -> Wytyczne
    "tripdatabase.com",        # EBM search engine -> Wytyczne
    "bestpractice.bmj.com",    # BMJ Best Practice -> Wytyczne
    "uptodate.com",            # UpToDate -> Wytyczne
]

# More elite-tier specialty journals for the Clinical Intelligence Feed
# ("top of the top"), split into their own query so they don't get crowded out
# by the high-volume SOURCES_WORLD_MAJOR group the same way ESC/IDSA did.
SOURCES_WORLD_TOP_JOURNALS = [
    "annals.org",            # Annals of Internal Medicine
    "ahajournals.org",       # AHA family: Circulation, Stroke, Hypertension
    "jacc.org",              # Journal of the American College of Cardiology
    "ashpublications.org",   # Blood / Blood Advances (hematology)
]

SOURCES_WORLD_MARKET = [
    "statnews.com",
    "endpointsnews.com",
    "pink.pharmaintelligence.informa.com",
    "fiercepharma.com",     # pharma/biotech trade press -> Rynek
    "biopharmadive.com",    # pharma/biotech trade press -> Rynek
    "biospace.com",         # pharma/biotech trade press -> Rynek
]

# International/EU health bodies beyond EMA/ECDC (already in REGULATORS) - lower
# Google News volume than WHO/CDC/FDA, so they get their own group rather than
# being swallowed by those.
SOURCES_WORLD_INTL_ORGS = [
    "health.ec.europa.eu",
    "efsa.europa.eu",
    "paho.org",
    "unicef.org",
    "oecd.org",
    "worldbank.org",
    "unaids.org",
    "iarc.who.int",
    "data.europa.eu",
    "ourworldindata.org",
]

# US federal health agencies beyond CDC/FDA (already in REGULATORS).
SOURCES_US_GOV = [
    "nih.gov",
    "nlm.nih.gov",
    "medlineplus.gov",
    "ahrq.gov",
    "cms.gov",
    "cancer.gov",
    "niaid.nih.gov",
    "nichd.nih.gov",
]

# Large multi-disciplinary academic publishers (MDPI, Frontiers, ScienceDirect,
# Springer, Wiley) - like Nature/Science, these publish across every scientific
# field, not just medicine, and are prolific enough to need their own query plus
# the same off-topic relevance gate (see _is_broad_science_source in classify.py).
SOURCES_ACADEMIC_PUBLISHERS = [
    "mdpi.com",
    "frontiersin.org",
    "sciencedirect.com",
    "link.springer.com",
    "onlinelibrary.wiley.com",
]

SOURCES_WORLD = (
    SOURCES_WORLD_MAJOR + SOURCES_WORLD_REGULATORS + SOURCES_WORLD_GUIDELINES_RESEARCH
    + SOURCES_WORLD_MARKET + SOURCES_WORLD_INTL_ORGS + SOURCES_US_GOV + SOURCES_ACADEMIC_PUBLISHERS
    + SOURCES_WORLD_TOP_JOURNALS
)


def build_site_query(domains):
    return "(" + " OR ".join(f"site:{d}" for d in domains) + ")"


# No "+medycyna"/"+medicine" keyword suffix - every domain here is already a
# medical/health-specific outlet (that's what makes it "approved" in the first
# place), so requiring the literal word too was a second, redundant filter that
# silently starved entire sources (verified: removing it took a 0-article test
# query against ESC/NICE/Fierce Pharma/BioSpace from 0 to 100 results).
PL_QUERY = build_site_query(SOURCES_PL_MAJOR)
PL_QUERY_GOV_POLICY = build_site_query(SOURCES_PL_GOV_POLICY)
WORLD_QUERY = build_site_query(SOURCES_WORLD_MAJOR)
WORLD_QUERY_REGULATORS = build_site_query(SOURCES_WORLD_REGULATORS)
WORLD_QUERY_GUIDELINES_RESEARCH = build_site_query(SOURCES_WORLD_GUIDELINES_RESEARCH)
WORLD_QUERY_MARKET = build_site_query(SOURCES_WORLD_MARKET)
WORLD_QUERY_INTL_ORGS = build_site_query(SOURCES_WORLD_INTL_ORGS)
WORLD_QUERY_US_GOV = build_site_query(SOURCES_US_GOV)
WORLD_QUERY_ACADEMIC_PUBLISHERS = build_site_query(SOURCES_ACADEMIC_PUBLISHERS)
WORLD_QUERY_TOP_JOURNALS = build_site_query(SOURCES_WORLD_TOP_JOURNALS)

PL_RSS_URL = f"https://news.google.com/rss/search?q={PL_QUERY}&hl=pl&gl=PL&ceid=PL:pl"
PL_GOV_POLICY_RSS_URL = f"https://news.google.com/rss/search?q={PL_QUERY_GOV_POLICY}&hl=pl&gl=PL&ceid=PL:pl"
WORLD_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY}&hl=en-US&gl=US&ceid=US:en"
WORLD_REGULATORS_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_REGULATORS}&hl=en-US&gl=US&ceid=US:en"
WORLD_GUIDELINES_RESEARCH_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_GUIDELINES_RESEARCH}&hl=en-US&gl=US&ceid=US:en"
WORLD_MARKET_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_MARKET}&hl=en-US&gl=US&ceid=US:en"
WORLD_INTL_ORGS_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_INTL_ORGS}&hl=en-US&gl=US&ceid=US:en"
WORLD_US_GOV_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_US_GOV}&hl=en-US&gl=US&ceid=US:en"
WORLD_ACADEMIC_PUBLISHERS_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_ACADEMIC_PUBLISHERS}&hl=en-US&gl=US&ceid=US:en"
WORLD_TOP_JOURNALS_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_TOP_JOURNALS}&hl=en-US&gl=US&ceid=US:en"

PUBMED_RSS_URL = "https://pubmed.ncbi.nlm.nih.gov/rss/search?term=medicine"

GIS_WARNINGS_URL = "https://www.gov.pl/web/gis/ostrzezenia"
