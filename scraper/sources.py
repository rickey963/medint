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


def _google_news_url_named(name_query, when="3d", locale=True):
    # Plain name search instead of site:-scoped - for sources whose own
    # domain returns 0 Google News results even unfiltered (confirmed for
    # endpointsnews.com), but whose real articles surface fine under a
    # quoted publication-name search.
    query = f"{name_query} when:{when}"
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
    # doz.pl is mainly an online pharmacy storefront - site: alone would
    # mostly return product pages, so this is scoped to its "Czytelnia"
    # (DozNews) editorial section specifically.
    ("DOZ.pl", _google_news_url("doz.pl", extra="czytelnia"), "google_news"),
    ("Serwis Zdrowie (PAP)", _google_news_url("zdrowie.pap.pl"), "google_news"),
    # Moved here from the Wytyczne tile (see that section's comment) - both
    # cover the Polish health *system*/policy beat (workforce, hospital
    # closures, funding, rankings, salary disputes) as general reporting, not
    # actual guidelines/recommendations, which is what that tile's name
    # promises. Confirmed by inspecting real output: these two sources were
    # filling 18 of that tile's ~20 slots with exactly this kind of general
    # policy news, crowding out the tile's actual subject matter.
    ("Polityka Zdrowotna", _google_news_url("politykazdrowotna.com"), "google_news"),
    ("Remedium.md", _google_news_url("remedium.md"), "google_news"),
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
    # A site:cochranelibrary.com query is unusable - that domain's Google News
    # index is polluted with SEO spam (IPTV-subscription and supplement-review
    # pages that somehow rank under the domain), and real Cochrane reviews
    # don't surface at all. A named "Cochrane systematic review" search returns
    # the genuine articles instead (confirmed: real reviews on breast-cancer
    # risk models, opioids for low back pain, etc.), same named-search approach
    # used for Endpoints News below where site: also fails. when:30d because
    # Cochrane publishes far less frequently than a daily news wire.
    ("Cochrane Library", _google_news_url_named("Cochrane systematic review", when="30d", locale=False), "google_news", 30 * 24),
]

# --- 3. Epidemiologia i zdrowie publiczne -------------------------------------
SOURCES_EPIDEMIOLOGIA = [
    # who.int also feeds the "Świat" tile above - this query is scoped to the
    # Disease Outbreak News stream specifically, not WHO's general news.
    ("WHO Disease Outbreak News", _google_news_url("who.int", locale=False, extra='"Disease Outbreak News"'), "google_news"),
    ("ECDC", _google_news_url("ecdc.europa.eu", locale=False), "google_news"),
    ("CDC Outbreaks", _google_news_url("cdc.gov", locale=False, extra="outbreak"), "google_news"),
    # ProMED (promedmail.org) and HealthMap (healthmap.org) were dropped here:
    # both are genuinely unreachable - zero results under any site:/named
    # Google News query AND no working native RSS feed (every candidate feed
    # URL returns 0 entries / bozo=1). Replaced with two infectious-disease
    # surveillance outlets that serve the same purpose and actually index:
    # CIDRAP (strong, ~28 fresh outbreak items: measles, Ebola, Legionnaires')
    # and Outbreak News Today. when:14d - outbreak reporting is less frequent
    # than a daily news wire, matching the local freshness override.
    ("CIDRAP", _google_news_url("cidrap.umn.edu", when="14d", locale=False), "google_news", 14 * 24),
    ("Outbreak News Today", _google_news_url("outbreaknewstoday.com", when="14d", locale=False), "google_news", 14 * 24),
]

# --- 4. Badania kliniczne ------------------------------------------------------
# Not part of the user's original source list (no category covers clinical
# trials) - filled with the official trial registry plus trade press on the
# user's explicit instruction to broaden this tile's source coverage.
# EU Clinical Trials Register deliberately dropped (tested, not just left
# unused): its Google News results are all generic CTIS portal/navigation
# pages ("Clinical Trials in the European Union - EMA" repeated verbatim),
# never an individual trial - unlike ClinicalTrials.gov, whose per-study
# detail pages ("Study Details | NCTxxxxx | <real study name>") index fine.
SOURCES_BADANIA_KLINICZNE = [
    ("ClinicalTrials.gov", _google_news_url("clinicaltrials.gov", locale=False), "google_news"),
    ("Clinical Trials Arena", _google_news_url("clinicaltrialsarena.com", locale=False, when="14d"), "google_news"),
    ("Applied Clinical Trials", _google_news_url("appliedclinicaltrialsonline.com", locale=False, when="14d"), "google_news"),
    ("TrialSite News", _google_news_url("trialsitenews.com", locale=False, when="14d"), "google_news"),
]

# --- 5. Rynek farmaceutyczny i Biotech ------------------------------------------
SOURCES_RYNEK_FARMACEUTYCZNY = [
    ("Drugs.com", _google_news_url("drugs.com", locale=False), "google_news"),
    ("EMA", _google_news_url("ema.europa.eu", locale=False), "google_news"),
    ("FDA Drug News", _google_news_url("fda.gov", locale=False, extra="drug"), "google_news"),
    ("Pink Sheet", _google_news_url("pink.pharmaintelligence.informa.com", locale=False), "google_news"),
    # A site:endpointsnews.com query returns 0 results (tested: Google News
    # has nothing indexed under that domain restriction) even though the
    # publication's real articles - now hosted at endpoints.news - show up
    # immediately under a plain name search. Named search instead of site:.
    ("Endpoints News", _google_news_url_named('"Endpoints News"', locale=False), "google_news"),
    # Added on request to broaden this tile beyond the original 5 - all
    # three verified by direct query before adding (real, current pharma/
    # biotech trade-press headlines, not landing pages).
    ("FiercePharma", _google_news_url("fiercepharma.com", locale=False, when="7d"), "google_news"),
    ("BioPharma Dive", _google_news_url("biopharmadive.com", locale=False, when="7d"), "google_news"),
    ("BioSpace", _google_news_url("biospace.com", locale=False, when="7d"), "google_news"),
]

# --- 6. Wytyczne i rekomendacje --------------------------------------------------
# "Rynek Zdrowia" from the user's legal-changes list is deliberately not
# repeated here - it already lives in the Polska tile above, and the user
# asked not to duplicate sources across tiles.
#
# Scoped strictly to sources that actually publish guidelines/recommendations
# (binding legal acts, or a professional body's own position statements) -
# not general health-system reporting. Polityka Zdrowotna and Remedium.md
# were removed from here and moved to the Polska tile: real output showed
# their Google News results are almost entirely general policy/system news
# (hospital closures, staffing crises, rankings, salary disputes), not
# guidelines, which mismatched this tile's stated purpose even though the
# articles themselves were legitimate health news belonging somewhere on the
# dashboard.
# This tile must cover actual guidelines/recommendations across the whole of
# medicine from Poland, Europe and the world. It mixes two kinds of source:
#
#  (a) General legal registries (ISAP, Dziennik Ustaw, EUR-Lex) - they publish
#      every law, not just health ones, so fetch_data.py additionally requires
#      medical relevance for them (see LEGAL_REGISTRY_SOURCES there). The query
#      itself is also scoped to health-related acts so that filter has health
#      items to work with.
#
#  (b) Dedicated medical guideline bodies (AOTMiT, NICE, ESC, ESMO, CDC, AHA/
#      ACC, plus a cross-specialty "clinical practice guideline" search). These
#      are inherently medical, so they DON'T get the Polish-keyword relevance
#      gate (it would wrongly drop their English guideline titles). They do get
#      a congress/e-learning/award promo filter instead (_is_guideline_event_junk).
#
# Every entry carries a 4th field overriding fetch_data.py's global 72h
# freshness cutoff: guidelines and recommendations publish far too infrequently
# for a 72h window to ever have anything to show, so the local freshness check
# is widened to match each source's Google News when: window.
SOURCES_WYTYCZNE = [
    # --- Poland: binding legal acts (general registries - medical-filtered) ---
    ("ISAP", _google_news_url("isap.sejm.gov.pl", when="30d", extra='"Minister Zdrowia" OR zdrowia OR zdrowotn'), "google_news", 30 * 24),
    ("Dziennik Ustaw RP", _google_news_url("dziennikustaw.gov.pl", when="30d", extra='"Minister Zdrowia" OR zdrowia OR zdrowotn'), "google_news", 30 * 24),
    # --- Poland: HTA recommendations (AOTMiT) + professional body (NIL) ---
    # AOTMiT is the Polish HTA agency - "Rekomendacja Prezesa"/"Stanowisko Rady"
    # are exactly the kind of formal recommendations this tile is named for.
    ("AOTMiT", _google_news_url("aotm.gov.pl", when="30d"), "google_news", 30 * 24),
    # Most of NIL's Google-News-indexed articles route straight to a PDF
    # download (nil.org.pl/articleToPdf/...) with no HTML version - those get
    # dropped by the no-PDFs quality gate, so this one often contributes
    # nothing. Left in (an explicitly requested, genuinely medical source).
    ("Naczelna Izba Lekarska", _google_news_url("nil.org.pl", when="30d"), "google_news", 30 * 24),
    # --- Europe: binding EU health law (general registry - medical-filtered) ---
    # No "extra" topic keyword - tested: combining when: with an extra keyword
    # phrase against this low-volume domain reliably returns 0 results, while
    # site: + when: alone returns real EU legal items. The medical-relevance
    # filter is what keeps these on-topic instead.
    ("EUR-Lex Health Law", _google_news_url("eur-lex.europa.eu", when="14d"), "google_news", 14 * 24),
    # --- Europe: medical-society clinical guidelines ---
    ("NICE", _google_news_url("nice.org.uk", when="30d", locale=False), "google_news", 30 * 24),
    ("ESC (kardiologia)", _google_news_url("escardio.org", when="30d", locale=False), "google_news", 30 * 24),
    ("ESMO (onkologia)", _google_news_url("esmo.org", when="30d", locale=False), "google_news", 30 * 24),
    # --- World: public-health recommendations + cross-specialty guidelines ---
    # CDC scoped to guideline/recommendation content - distinct from the
    # outbreak-scoped "CDC Outbreaks" entry in the epidemiology tile.
    ("CDC (rekomendacje)", _google_news_url("cdc.gov", when="30d", locale=False, extra="guideline OR recommendations"), "google_news", 30 * 24),
    # Named searches (not site:-scoped): the highest-precision guideline feeds
    # in testing - "<x> guideline"/"clinical practice guideline" returns real,
    # freshly issued guidelines across every specialty (cardiology, oncology,
    # endocrinology, nephrology, neurology...) from many publishers at once.
    ("Wytyczne AHA/ACC", _google_news_url_named('"American Heart Association" guideline', when="30d", locale=False), "google_news", 30 * 24),
    ("Wytyczne kliniczne", _google_news_url_named('"clinical practice guideline"', when="30d", locale=False), "google_news", 30 * 24),
]

ALL_SECTIONS = {
    "poland": SOURCES_POLSKA,
    "world": SOURCES_SWIAT,
    "epidemiology": SOURCES_EPIDEMIOLOGIA,
    "clinical_trials": SOURCES_BADANIA_KLINICZNE,
    "pharma_market": SOURCES_RYNEK_FARMACEUTYCZNY,
    "guidelines": SOURCES_WYTYCZNE,
}
