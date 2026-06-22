import React, { useState, useEffect, useMemo, useRef } from 'react';
import NewsSection from './components/NewsSection';
import ClinicalIntelligenceFeed from './components/ClinicalIntelligenceFeed';
import ClinicalResearchSection from './components/ClinicalResearchSection';
import RegulatorySafetySection from './components/RegulatorySafetySection';
import AISection from './components/AISection';
import GuidelinesSectionV2 from './components/GuidelinesSectionV2';
import SearchView from './components/SearchView';
import {
  isRecent,
  formatToPolishFormat,
  normalizeDateKey,
  ageInDays,
  isToday,
  makeStableId,
} from './utils/dateUtils';

// 7 thematic tiles per spec, plus the supplementary Clinical Intelligence Feed
// (hero) and "Świat" catch-all for approved-domain world news that doesn't fit
// any of the 7 (kept rather than dropped - see plan).
const DATA_FILES = [
  'news_pl.json',
  'news_world.json',
  'clinical_research.json',
  'regulatory_safety.json',
  'guidelines.json',
  'ai_medicine.json',
  'epidemiology.json',
  'pharma_market.json',
  'clinical_intelligence.json',
  'alerts.json',
];

// Human labels for each data file, used by the global search view's "Kafelek" filter.
const TILE_LABELS = {
  news_pl: 'Polska',
  news_world: 'Świat',
  clinical_research: 'Badania Kliniczne',
  regulatory_safety: 'Regulatory & Drug Safety',
  guidelines: 'Wytyczne i Rekomendacje',
  ai_medicine: 'AI w Medycynie',
  epidemiology: 'Epidemiologia i Zdrowie Publiczne',
  pharma_market: 'Rynek Farmaceutyczny i Biotech',
  clinical_intelligence: 'Clinical Intelligence Feed',
};

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard', icon: '🏠' },
  { key: 'specialization', label: 'Specjalizacja', icon: '🩺' },
  { key: 'search', label: 'Wyszukiwarka', icon: '🔍' },
];

// Mirrors scraper/classify.py's SPECIALIZATION_KEYWORDS list/order.
const SPECIALTIES = [
  'Kardiologia',
  'Onkologia',
  'Neurologia',
  'Psychiatria',
  'Endokrynologia i diabetologia',
  'Gastroenterologia i hepatologia',
  'Nefrologia',
  'Pulmonologia',
  'Hematologia',
  'Choroby zakaźne',
  'Reumatologia i immunologia',
  'Pediatria',
  'Ginekologia i położnictwo',
  'Chirurgia',
  'Ortopedia i traumatologia',
  'Urologia',
  'Dermatologia',
  'Okulistyka',
  'Anestezjologia i intensywna terapia',
  'Radiologia i diagnostyka obrazowa',
];

// Source prestige weights used by the "Article of the day" ranker.
const SOURCE_WEIGHTS = {
  NEJM: 5,
  'The Lancet': 5,
  JAMA: 5,
  'Nature Medicine': 5,
  'Nature Digital Medicine': 4,
  BMJ: 4,
  'Science Translational Medicine': 4,
  Nature: 4,
  Science: 4,
  FDA: 4,
  EMA: 4,
  WHO: 3,
  Research: 3,
  Badania: 3,
  Default: 2,
};

const getSourceWeight = (item) => {
  if (!item) return 0;
  if (typeof item.priority === 'number') return item.priority;
  const src = String(item.source || '');
  return SOURCE_WEIGHTS[src] ?? SOURCE_WEIGHTS.Default;
};

/**
 * Picks the single most relevant article across all categories.
 *
 * Restricted to today's (Europe/Warsaw calendar day) articles first, ranked
 * purely by source prestige (ties broken by how recent within today) - this
 * is meant to reset every morning to "today's top medical story", not drift
 * toward whatever the highest-prestige item of the last week was. Falls back
 * to the old 7-day recency-weighted scoring only for the rare case where
 * nothing has been published yet today (e.g. right after local midnight).
 */
const selectArticleOfDay = (allData) => {
  const pools = [
    'clinical_research',
    'clinical_intelligence',
    'news_world',
    'news_pl',
    'regulatory_safety',
    'ai_medicine',
    'guidelines',
    'epidemiology',
    'pharma_market',
  ];

  let bestToday = null;
  let bestTodayScore = -Infinity;
  let bestFallback = null;
  let bestFallbackScore = -Infinity;

  pools.forEach((key) => {
    const list = allData[key];
    if (!Array.isArray(list)) return;
    list.forEach((item) => {
      const date = normalizeDateKey(item.date);
      if (!date) return;
      const ageDays = ageInDays(item.date);
      if (ageDays < 0 || ageDays > 7) return;
      const prestige = getSourceWeight(item);

      if (isToday(item.date)) {
        // Among today's articles, rank by prestige; recency only breaks ties
        // between equally-prestigious same-day items.
        const recencyTiebreak = Math.max(0, 1 - ageDays);
        const score = prestige * 10 + recencyTiebreak;
        if (score > bestTodayScore) {
          bestTodayScore = score;
          bestToday = item;
        }
      }

      const recencyFactor = Math.max(0, 5 * (1 - ageDays / 7));
      const fallbackScore = prestige * 0.5 + recencyFactor;
      if (fallbackScore > bestFallbackScore) {
        bestFallbackScore = fallbackScore;
        bestFallback = item;
      }
    });
  });

  return bestToday || bestFallback;
};

/**
 * Generates the list of medical alerts shown in the red ticker. This is meant
 * for *current* threats - active outbreaks, viruses, infections, drug recalls/
 * black-box warnings - never loosely-worded historical or unrelated coverage that
 * happens to contain a word like "alert" or "zagrożenie". Sources are restricted
 * to the tiles whose entire purpose is safety/outbreak signals (alerts.json,
 * regulatory_safety, epidemiology). An ongoing outbreak (e.g. Ebola in DRC) stays
 * "critical" for as long as it's in the news, not just its first 48h, so the
 * window matches the dashboard's general 7-day freshness window rather than being
 * tighter than it.
 */
const ALERT_KEYWORDS = [
  'wycofanie z obrotu',
  'wycofanie leku',
  'wycofanie serii',
  'black box',
  'black-box',
  'nowe ognisko',
  'ognisko zakażeń',
  'wybuch epidemii',
  'pandemi',
  'nowy wariant',
  'nowe zakażenia',
  'nowy wirus',
  'outbreak',
  'recall',
  'fda warning',
  'who alert',
  'disease outbreak',
];

const ALERT_MAX_AGE_HOURS = 7 * 24;

const isAlertItem = (item) => {
  if (!item || !item.title) return false;
  if (item.type === 'ALERT') return true;
  const ageHours = ageInDays(item.date) * 24;
  if (ageHours < 0 || ageHours > ALERT_MAX_AGE_HOURS) return false;
  // Trust the backend's own classification first (scraper/classify.py already
  // decided this is an active outbreak or a recall/black-box item) rather than
  // re-deriving it from English/Polish keyword phrasing alone, which misses
  // named-disease coverage that doesn't literally say "outbreak"/"epidemia".
  if (item.category === 'Epidemiologia') return true;
  const safety = String(item.safety_level || '').toLowerCase();
  if (safety.includes('wycofanie') || safety.includes('black box')) {
    return true;
  }
  const text = ((item.title || '') + ' ' + (item.summary || '')).toLowerCase();
  return ALERT_KEYWORDS.some((kw) => text.includes(kw));
};

const generateAlerts = (allData) => {
  const collected = [];
  const seen = new Set();
  const addItem = (item) => {
    if (!isAlertItem(item)) return;
    const key = (item.title || '').toLowerCase().trim();
    if (!key || seen.has(key)) return;
    seen.add(key);
    collected.push({
      title: item.title,
      url: item.url || '#',
      source: item.source || 'MEDINT',
      date: item.date || '',
    });
  };

  ['alerts', 'regulatory_safety', 'epidemiology'].forEach((k) => {
    const list = allData[k];
    if (Array.isArray(list)) list.forEach(addItem);
  });

  // Recency-bounded alerts (last 48h) sorted newest first.
  collected.sort((a, b) => {
    const da = normalizeDateKey(a.date) || 0;
    const db = normalizeDateKey(b.date) || 0;
    return db - da;
  });
  return collected.slice(0, 8);
};

// Constant scroll speed (px/s) so the ticker is always comfortably readable,
// regardless of how many alerts are currently loaded.
const TICKER_SPEED_PX_PER_SEC = 40;

const AlertsTicker = ({ data }) => {
  const trackRef = useRef(null);
  const [duration, setDuration] = useState(60);

  const activeAlerts = (data || []).filter((a) => a.title);
  const itemsKey = activeAlerts.map((a) => a.title).join('|');

  useEffect(() => {
    if (!trackRef.current) return;
    const width = trackRef.current.scrollWidth / 2;
    setDuration(Math.max(20, width / TICKER_SPEED_PX_PER_SEC));
  }, [itemsKey]);

  if (activeAlerts.length === 0) return null;

  const renderAlertRow = (keyPrefix) =>
    activeAlerts.map((item, i) => (
      <React.Fragment key={`${keyPrefix}-${i}`}>
        <a
          href={item.url || '#'}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center text-sm md:text-base font-bold uppercase tracking-wide leading-none hover:underline shrink-0"
        >
          🚨 {item.title} — {item.source || 'MEDINT'}
        </a>
        <span className="mx-4 opacity-50 shrink-0">•</span>
      </React.Fragment>
    ));

  return (
    <div className="bg-red-700 text-white h-10 md:h-11 overflow-hidden whitespace-nowrap relative shadow-lg shadow-red-950/40 z-50 flex items-center">
      <div
        ref={trackRef}
        className="animate-marquee flex items-center whitespace-nowrap hover:pause"
        style={{ animationDuration: `${duration}s` }}
      >
        {renderAlertRow('a')}
        {renderAlertRow('b')}
      </div>
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-marquee {
          animation-name: marquee;
          animation-timing-function: linear;
          animation-iteration-count: infinite;
          padding-left: 100%;
        }
        .hover\\:pause:hover {
          animation-play-state: paused;
        }
      `}} />
    </div>
  );
};

const ArticleOfDay = ({ data }) => {
  if (!data || !data.title) return null;

  const dateLabel = formatToPolishFormat(data.date);
  const prestige = getSourceWeight(data);
  const star = '★'.repeat(Math.max(1, Math.min(5, prestige))) +
    '☆'.repeat(5 - Math.max(1, Math.min(5, prestige)));

  return (
    <div className="bg-gradient-to-br from-blue-950 via-slate-900 to-slate-950 text-white p-4 rounded-xl shadow-2xl shadow-black/40 ring-1 ring-blue-500/20 h-[450px] flex flex-col lg:col-span-1">
      <div className="flex items-center justify-between mb-3 flex-wrap gap-1.5 shrink-0">
        <h2 className="text-xs font-black uppercase tracking-[0.2em] text-blue-400">
          📰 Artykuł Dnia
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold uppercase text-blue-400/80">
            {data.source || 'MEDINT'}
          </span>
          <span className="text-[10px] font-bold uppercase text-blue-400/80">
            {dateLabel}
          </span>
        </div>
      </div>
      <a
        href={data.url || '#'}
        target="_blank"
        rel="noopener noreferrer"
        className="block hover:opacity-90 transition-opacity flex-1 overflow-y-auto custom-scrollbar"
      >
        <h3 className="text-lg font-bold mb-3 leading-tight text-slate-50">{data.title}</h3>
        <p className="text-sm text-blue-200/90 leading-relaxed italic mb-3">
          {data.summary ||
            data.conclusion ||
            'Najnowsze doniesienie medyczne wybrane na podstawie prestiżu źródła i daty publikacji.'}
        </p>
        <div className="border-t border-blue-900/60 pt-3 flex items-center justify-between">
          <span className="text-[10px] font-bold uppercase text-blue-400/80">
            Prestiż źródła: {star}
          </span>
          <span className="text-[10px] font-bold uppercase text-blue-400">
            Przeczytaj pełny artykuł →
          </span>
        </div>
      </a>
    </div>
  );
};

const NavBar = ({ activeView, setActiveView, selectedSpecialization, onClearSpecialization }) => (
  <nav className="bg-slate-900/80 backdrop-blur border-b border-slate-800 shrink-0">
    <div className="max-w-7xl mx-auto px-4 flex items-center gap-1 overflow-x-auto">
      {NAV_ITEMS.map(({ key, label, icon }) => (
        <button
          key={key}
          onClick={() => setActiveView(key)}
          className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors whitespace-nowrap ${
            activeView === key
              ? 'border-blue-500 text-blue-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          {icon} {label}
        </button>
      ))}
      {selectedSpecialization && (
        <button
          onClick={onClearSpecialization}
          className="ml-auto my-1.5 px-3 py-1 text-[11px] font-bold uppercase rounded-full bg-blue-500/10 text-blue-300 border border-blue-500/30 hover:bg-blue-500/20 transition-colors whitespace-nowrap"
        >
          Filtr: {selectedSpecialization} ✕
        </button>
      )}
    </div>
  </nav>
);

const SpecializationPicker = ({ selected, onSelect }) => (
  <div className="max-w-7xl mx-auto px-4 py-6">
    <h2 className="text-lg font-bold text-slate-100 mb-1">🩺 Wybierz specjalizację</h2>
    <p className="text-sm text-slate-400 mb-4">
      Dashboard, Clinical Intelligence Feed i wszystkie kafelki pokażą wyłącznie treści związane z wybraną dziedziną.
    </p>
    <div className="flex flex-wrap gap-2">
      {SPECIALTIES.map((spec) => (
        <button
          key={spec}
          onClick={() => onSelect(spec)}
          className={`px-3 py-2 text-sm font-medium rounded-lg border transition-colors ${
            selected === spec
              ? 'bg-blue-600 text-white border-blue-500'
              : 'bg-slate-900/60 text-slate-300 border-slate-800 hover:border-blue-700/50 hover:bg-slate-800/60'
          }`}
        >
          {spec}
        </button>
      ))}
    </div>
  </div>
);

function App() {
  const [allData, setAllData] = useState({});
  const [activeView, setActiveView] = useState('dashboard');
  const [selectedSpecialization, setSelectedSpecialization] = useState(null);

  const loadAllData = async () => {
    try {
      const loaded = {};
      await Promise.all(
        DATA_FILES.map(async (file) => {
          try {
            const response = await fetch(`./data/${file}?t=${Date.now()}`);
            if (!response.ok) return;
            const json = await response.json();
            const key = file.replace('.json', '');
            if (Array.isArray(json)) {
              // Centralised: strict 7-day freshness window + sort newest first + assign id.
              const filtered = json
                .filter((item) => isRecent(item.date))
                .map((item) => ({ ...item, id: makeStableId(item) }))
                .sort((a, b) => {
                  const da = normalizeDateKey(a.date) || 0;
                  const db = normalizeDateKey(b.date) || 0;
                  return db - da;
                });
              loaded[key] = filtered;
            } else {
              loaded[key] = json;
            }
          } catch (err) {
            console.error(`Error loading ${file}:`, err);
          }
        })
      );
      setAllData(loaded);
    } catch (error) {
      console.error('Error loading central data:', error);
    }
  };

  useEffect(() => {
    loadAllData();
    const interval = setInterval(loadAllData, 120000); // 2 minutes - picks up new data without a manual page reload
    return () => clearInterval(interval);
  }, []);

  // When a specialization is active, it filters the whole dashboard (hero + every
  // tile) - computed once here so getDataFor/articleOfDay/alerts all see it.
  const filteredData = useMemo(() => {
    if (!selectedSpecialization) return allData;
    const out = {};
    Object.keys(allData).forEach((key) => {
      const list = allData[key];
      out[key] = Array.isArray(list)
        ? list.filter((item) => (item.specializations || []).includes(selectedSpecialization))
        : list;
    });
    return out;
  }, [allData, selectedSpecialization]);

  const getDataFor = (key) => filteredData[key] || [];

  // Derived values: article of the day and ticker alerts.
  const articleOfDay = useMemo(() => selectArticleOfDay(filteredData), [filteredData]);
  const alerts = useMemo(() => generateAlerts(filteredData), [filteredData]);

  // Global search operates over everything, unfiltered by the specialization
  // toggle (it has its own filters) - "alerts" is excluded, it's a derived stub
  // list (title/source/date only), not real articles. Deduped by id: the same
  // article can legitimately sit in both its primary tile and the supplementary
  // Clinical Intelligence Feed, which would otherwise show up twice in results.
  const searchableArticles = useMemo(() => {
    const combined = [];
    const seenIds = new Set();
    Object.keys(TILE_LABELS).forEach((key) => {
      const list = allData[key];
      if (!Array.isArray(list)) return;
      list.forEach((item) => {
        if (seenIds.has(item.id)) return;
        seenIds.add(item.id);
        combined.push({ ...item, _tileLabel: TILE_LABELS[key] });
      });
    });
    return combined;
  }, [allData]);

  const handleSelectSpecialization = (spec) => {
    setSelectedSpecialization(spec);
    setActiveView('dashboard');
  };

  return (
    <div className="min-h-screen bg-transparent flex flex-col">
      <header className="medical-pattern bg-slate-950/80 backdrop-blur border-b border-blue-900/30 text-white py-6 shadow-lg shadow-black/30 text-center shrink-0">
        <h1 className="text-4xl font-black tracking-tighter uppercase italic text-blue-100">
          ⚕️ MEDINT
        </h1>
        <p className="text-blue-400/80 text-sm font-medium">
          Monitoring Medycyny i Nauk Klinicznych
        </p>
      </header>

      <NavBar
        activeView={activeView}
        setActiveView={setActiveView}
        selectedSpecialization={selectedSpecialization}
        onClearSpecialization={() => setSelectedSpecialization(null)}
      />

      {activeView === 'specialization' && (
        <SpecializationPicker selected={selectedSpecialization} onSelect={handleSelectSpecialization} />
      )}
      {activeView === 'search' && (
        <SearchView articles={searchableArticles} specialties={SPECIALTIES} tileLabels={TILE_LABELS} />
      )}

      {activeView === 'dashboard' && (
        <>
          {/* High Priority Section: Alerts ticker + hero (Clinical Intelligence Feed left, Article of the day right) */}
          <div className="shrink-0">
            <AlertsTicker data={alerts} />
            <div className="p-4 pb-0">
              <div className="max-w-7xl mx-auto">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <ClinicalIntelligenceFeed data={getDataFor('clinical_intelligence')} />
                  {articleOfDay && <ArticleOfDay data={articleOfDay} />}
                </div>
              </div>
            </div>
          </div>

          <main className="flex-1 p-4 custom-scrollbar overflow-y-auto">
            <div className="max-w-7xl mx-auto space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <NewsSection title={<>🏥 Polska</>} data={getDataFor('news_pl')} />
                <ClinicalResearchSection
                  title={<>🔬 Badania Kliniczne</>}
                  data={getDataFor('clinical_research')}
                />
                <RegulatorySafetySection
                  title={<>🛡️ Regulatory & Drug Safety</>}
                  data={getDataFor('regulatory_safety')}
                />
                <GuidelinesSectionV2
                  title={<>📋 Wytyczne i Rekomendacje</>}
                  data={getDataFor('guidelines')}
                />
                <AISection
                  title={<>🤖 AI w Medycynie</>}
                  data={getDataFor('ai_medicine')}
                />
                <NewsSection
                  title={<>🦠 Epidemiologia i Zdrowie Publiczne</>}
                  data={getDataFor('epidemiology')}
                />
                <NewsSection
                  title={<>🧬 Rynek Farmaceutyczny i Biotech</>}
                  data={getDataFor('pharma_market')}
                />
                <NewsSection title={<>🌍 Świat</>} data={getDataFor('news_world')} />
              </div>
            </div>
          </main>
        </>
      )}

      <footer className="py-4 text-center text-slate-500 text-xs border-t border-slate-800 shrink-0 bg-slate-950/60">
        &copy; {new Date().getFullYear()} MEDINT - Wszystkie prawa zastrzeżone.
      </footer>
    </div>
  );
}

export default App;
