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

# General-interest PL news outlets (not medical-specific), unlike everything
# else in SOURCES_PL - a bare site: query against them would return mostly
# politics/sports/weather, so this group's query (see build_general_news_query)
# adds a medical-topic keyword constraint that the other (already
# medical-only) PL/world groups deliberately don't need.
SOURCES_PL_GENERAL_NEWS = [
    "polsatnews.pl",
    "pap.pl",                # Polska Agencja Prasowa
    "polskieradio24.pl",
]

SOURCES_PL = SOURCES_PL_MAJOR + SOURCES_PL_GOV_POLICY + SOURCES_PL_GENERAL_NEWS

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

# This used to be one 24-domain group. Tested with when:1d: Drugs.com (58) and
# ClinicalTrials.gov (40) alone filled the entire 100-result page - the other
# 22 domains (NICE, ESMO, ASCO, ESC, IDSA, UpToDate, PubMed, EuropePMC, arXiv,
# medRxiv, ProMED, HealthMap, Eurosurveillance...) got *zero*. Split by rough
# publishing-volume tier, each with its own query.
SOURCES_TRIAL_REGISTRIES = [
    "clinicaltrials.gov",
    "clinicaltrialsregister.eu",
    "euclinicaltrials.eu",
    "drugs.com",
]

SOURCES_GUIDELINE_BODIES = [
    "nice.org.uk",
    "esmo.org",
    "asco.org",
    "escardio.org",          # European Society of Cardiology -> Wytyczne
    "idsociety.org",         # Infectious Diseases Society of America -> Wytyczne
    "bnf.nice.org.uk",       # British National Formulary -> Wytyczne
    "tripdatabase.com",      # EBM search engine -> Wytyczne
    "bestpractice.bmj.com",  # BMJ Best Practice -> Wytyczne
    "uptodate.com",          # UpToDate -> Wytyczne
]

SOURCES_RESEARCH_LITERATURE = [
    "pubmed.ncbi.nlm.nih.gov",
    "europepmc.org",
    "arxiv.org",
    "medrxiv.org",
    "translationalscience.org",
    "eur-lex.europa.eu",
]

SOURCES_OUTBREAK_TRACKING = [
    "promedmail.org",
    "healthmap.org",
    "eurosurveillance.org",   # ECDC's own peer-reviewed epidemiology journal -> Epidemiologia
    "outbreaknewstoday.com",  # dedicated outbreak-tracking trade press -> Epidemiologia
]

SOURCES_DRUG_REFERENCE = [
    "yellowcard.mhra.gov.uk",  # UK pharmacovigilance reporting -> Regulatory & Drug Safety
    "go.drugbank.com",         # DrugBank -> Regulatory & Drug Safety
]

# More elite-tier specialty journals for the Clinical Intelligence Feed
# ("top of the top"), split into their own query so they don't get crowded out
# by the high-volume SOURCES_WORLD_MAJOR group the same way ESC/IDSA did.
# ahajournals.org deliberately excluded: tested and it alone filled 100/100
# results in this group (crowding out the other three entirely) AND its own
# items are routinely just a raw guideline PDF filename as the "title"
# ("cir.0000000000001415.9956256.pdf") with no real headline - not worth a
# dedicated query of its own either, the quality floor is too low.
# Tested with when:1d: 0 results, even on their own - these three publish too
# rarely for a 1-day window; given their own query window:7d in sources_rss_urls.
SOURCES_WORLD_TOP_JOURNALS = [
    "annals.org",            # Annals of Internal Medicine
    "jacc.org",              # Journal of the American College of Cardiology
    "ashpublications.org",   # Blood / Blood Advances (hematology)
]

# Tested with when:1d: BioSpace (72) and statnews.com (13) dominate;
# endpointsnews.com and pink.pharmaintelligence.informa.com got zero. Split off
# the lower-volume two into their own (wider-window) query.
SOURCES_WORLD_MARKET = [
    "statnews.com",
    "fiercepharma.com",     # pharma/biotech trade press -> Rynek
    "biopharmadive.com",    # pharma/biotech trade press -> Rynek
    "biospace.com",         # pharma/biotech trade press -> Rynek
]

SOURCES_WORLD_MARKET_MINOR = [
    "endpointsnews.com",
    "pink.pharmaintelligence.informa.com",
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

# US federal health agencies beyond CDC/FDA (already in REGULATORS). Tested
# with when:1d: nih.gov alone took 86/100, the other 7 domains shared the rest
# (most landing on zero) - split nih.gov off into its own query.
SOURCES_US_GOV = [
    "nih.gov",
]

SOURCES_US_GOV_MINOR = [
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
# Tested with when:1d: MDPI took 97/100 on its own - split off the other four.
SOURCES_ACADEMIC_PUBLISHERS = [
    "mdpi.com",
]

SOURCES_ACADEMIC_PUBLISHERS_MINOR = [
    "frontiersin.org",
    "sciencedirect.com",
    "link.springer.com",
    "onlinelibrary.wiley.com",
]

SOURCES_WORLD = (
    SOURCES_WORLD_MAJOR + SOURCES_WORLD_REGULATORS
    + SOURCES_TRIAL_REGISTRIES + SOURCES_GUIDELINE_BODIES + SOURCES_RESEARCH_LITERATURE
    + SOURCES_OUTBREAK_TRACKING + SOURCES_DRUG_REFERENCE
    + SOURCES_WORLD_MARKET + SOURCES_WORLD_MARKET_MINOR
    + SOURCES_WORLD_INTL_ORGS
    + SOURCES_US_GOV + SOURCES_US_GOV_MINOR
    + SOURCES_ACADEMIC_PUBLISHERS + SOURCES_ACADEMIC_PUBLISHERS_MINOR
    + SOURCES_WORLD_TOP_JOURNALS
)


def build_site_query(domains, when='1d'):
    # Google News RSS ranks by its own relevance/popularity signal, not by date -
    # confirmed empirically: an unfiltered query's 100 results were almost all
    # "evergreen" pages Google re-crawled, with only 1-2 actually from today.
    # "when:Nd" is a real Google Search time-range operator that News RSS
    # honours, so this turns each query into "everything from this site in the
    # last N days" instead of "whatever Google currently ranks highest" - the
    # difference between a feed that updates hourly and one that looks frozen.
    # Lower-volume domain groups use a wider window (when:5d/7d) - tested with
    # when:1d, several (the new split-off "_MINOR" groups, SOURCES_WORLD_TOP_JOURNALS)
    # came back with literally 0 results; they just don't publish daily.
    return "(" + " OR ".join(f"site:{d}" for d in domains) + f") when:{when}"


# General-interest outlets aren't medical-specific the way every other approved
# domain is, so (unlike build_site_query) this adds a topic constraint -
# otherwise site:polsatnews.pl etc. returns mostly politics/sports/weather.
GENERAL_NEWS_MEDICAL_TOPIC_QUERY = (
    "(zdrowie OR medycyna OR szpital OR pacjent OR lekarz OR choroba OR lek OR "
    "szczepionka OR epidemia OR NFZ OR Ministerstwo Zdrowia)"
)


def build_general_news_query(domains, when='1d'):
    site_part = "(" + " OR ".join(f"site:{d}" for d in domains) + ")"
    return f"{site_part} {GENERAL_NEWS_MEDICAL_TOPIC_QUERY} when:{when}"


# No "+medycyna"/"+medicine" keyword suffix - every domain here is already a
# medical/health-specific outlet (that's what makes it "approved" in the first
# place), so requiring the literal word too was a second, redundant filter that
# silently starved entire sources (verified: removing it took a 0-article test
# query against ESC/NICE/Fierce Pharma/BioSpace from 0 to 100 results).
PL_QUERY = build_site_query(SOURCES_PL_MAJOR)
PL_QUERY_GOV_POLICY = build_site_query(SOURCES_PL_GOV_POLICY)
PL_QUERY_GENERAL_NEWS = build_general_news_query(SOURCES_PL_GENERAL_NEWS)
WORLD_QUERY = build_site_query(SOURCES_WORLD_MAJOR)
WORLD_QUERY_REGULATORS = build_site_query(SOURCES_WORLD_REGULATORS)
WORLD_QUERY_TRIAL_REGISTRIES = build_site_query(SOURCES_TRIAL_REGISTRIES)
WORLD_QUERY_GUIDELINE_BODIES = build_site_query(SOURCES_GUIDELINE_BODIES, when='5d')
WORLD_QUERY_RESEARCH_LITERATURE = build_site_query(SOURCES_RESEARCH_LITERATURE, when='5d')
WORLD_QUERY_OUTBREAK_TRACKING = build_site_query(SOURCES_OUTBREAK_TRACKING, when='5d')
WORLD_QUERY_DRUG_REFERENCE = build_site_query(SOURCES_DRUG_REFERENCE, when='5d')
WORLD_QUERY_MARKET = build_site_query(SOURCES_WORLD_MARKET)
WORLD_QUERY_MARKET_MINOR = build_site_query(SOURCES_WORLD_MARKET_MINOR, when='5d')
WORLD_QUERY_INTL_ORGS = build_site_query(SOURCES_WORLD_INTL_ORGS)
WORLD_QUERY_US_GOV = build_site_query(SOURCES_US_GOV)
WORLD_QUERY_US_GOV_MINOR = build_site_query(SOURCES_US_GOV_MINOR, when='5d')
WORLD_QUERY_ACADEMIC_PUBLISHERS = build_site_query(SOURCES_ACADEMIC_PUBLISHERS)
WORLD_QUERY_ACADEMIC_PUBLISHERS_MINOR = build_site_query(SOURCES_ACADEMIC_PUBLISHERS_MINOR, when='5d')
WORLD_QUERY_TOP_JOURNALS = build_site_query(SOURCES_WORLD_TOP_JOURNALS, when='7d')

PL_RSS_URL = f"https://news.google.com/rss/search?q={PL_QUERY}&hl=pl&gl=PL&ceid=PL:pl"
PL_GOV_POLICY_RSS_URL = f"https://news.google.com/rss/search?q={PL_QUERY_GOV_POLICY}&hl=pl&gl=PL&ceid=PL:pl"
PL_GENERAL_NEWS_RSS_URL = f"https://news.google.com/rss/search?q={PL_QUERY_GENERAL_NEWS}&hl=pl&gl=PL&ceid=PL:pl"
WORLD_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY}&hl=en-US&gl=US&ceid=US:en"
WORLD_REGULATORS_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_REGULATORS}&hl=en-US&gl=US&ceid=US:en"
WORLD_TRIAL_REGISTRIES_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_TRIAL_REGISTRIES}&hl=en-US&gl=US&ceid=US:en"
WORLD_GUIDELINE_BODIES_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_GUIDELINE_BODIES}&hl=en-US&gl=US&ceid=US:en"
WORLD_RESEARCH_LITERATURE_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_RESEARCH_LITERATURE}&hl=en-US&gl=US&ceid=US:en"
WORLD_OUTBREAK_TRACKING_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_OUTBREAK_TRACKING}&hl=en-US&gl=US&ceid=US:en"
WORLD_DRUG_REFERENCE_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_DRUG_REFERENCE}&hl=en-US&gl=US&ceid=US:en"
WORLD_MARKET_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_MARKET}&hl=en-US&gl=US&ceid=US:en"
WORLD_MARKET_MINOR_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_MARKET_MINOR}&hl=en-US&gl=US&ceid=US:en"
WORLD_INTL_ORGS_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_INTL_ORGS}&hl=en-US&gl=US&ceid=US:en"
WORLD_US_GOV_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_US_GOV}&hl=en-US&gl=US&ceid=US:en"
WORLD_US_GOV_MINOR_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_US_GOV_MINOR}&hl=en-US&gl=US&ceid=US:en"
WORLD_ACADEMIC_PUBLISHERS_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_ACADEMIC_PUBLISHERS}&hl=en-US&gl=US&ceid=US:en"
WORLD_ACADEMIC_PUBLISHERS_MINOR_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_ACADEMIC_PUBLISHERS_MINOR}&hl=en-US&gl=US&ceid=US:en"
WORLD_TOP_JOURNALS_RSS_URL = f"https://news.google.com/rss/search?q={WORLD_QUERY_TOP_JOURNALS}&hl=en-US&gl=US&ceid=US:en"

PUBMED_RSS_URL = "https://pubmed.ncbi.nlm.nih.gov/rss/search?term=medicine"

GIS_WARNINGS_URL = "https://www.gov.pl/web/gis/ostrzezenia"

# Bypasses Google News entirely for Termedia - see collectors.fetch_via_sitemap.
# Google's own crawl-then-index pipeline for this domain lags real publish
# time by hours (confirmed repeatedly); reading the site's own sitemap +
# each article's NewsArticle JSON-LD doesn't have that lag at all.
TERMEDIA_SITEMAP_URL = "https://www.termedia.pl/sitemap-new.xml"
