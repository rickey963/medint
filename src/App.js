import React, { useState, useEffect, useMemo, useRef } from 'react';
import NewsSection from './components/NewsSection';
import ClinicalIntelligenceFeed from './components/ClinicalIntelligenceFeed';
import ClinicalResearchSection from './components/ClinicalResearchSection';
import RegulatorySafetySection from './components/RegulatorySafetySection';
import AISection from './components/AISection';
import GuidelinesSectionV2 from './components/GuidelinesSectionV2';
import {
  isRecent,
  formatToPolishFormat,
  normalizeDateKey,
  ageInDays,
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

// Mirrors scraper/classify.py's SLOW_MOVING_TILES: research/guideline/market press
// coverage trails the underlying event by days or weeks, unlike breaking news, so
// it shouldn't be held to the same 7-day window or the tile starves for no reason.
const SLOW_MOVING_WINDOW_DAYS = 90;
const SLOW_MOVING_FILES = new Set([
  'clinical_research.json',
  'guidelines.json',
  'ai_medicine.json',
  'pharma_market.json',
]);

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
 * Score = (prestige_weight * 0.5) + recency_factor.
 * Recency_factor decays linearly from 5 (today) to 0 (7 days old).
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
  let best = null;
  let bestScore = -Infinity;

  pools.forEach((key) => {
    const list = allData[key];
    if (!Array.isArray(list)) return;
    list.forEach((item) => {
      const date = normalizeDateKey(item.date);
      if (!date) return;
      const ageDays = ageInDays(item.date);
      if (ageDays < 0 || ageDays > 7) return;
      const recencyFactor = Math.max(0, 5 * (1 - ageDays / 7));
      const prestige = getSourceWeight(item);
      const score = prestige * 0.5 + recencyFactor;
      if (score > bestScore) {
        bestScore = score;
        best = item;
      }
    });
  });

  return best;
};

/**
 * Generates the list of medical alerts shown in the red ticker.
 * Sources:
 *  - regulatory_safety with safety_level containing "WYCOFANIE", "BLACK BOX" or "ALERT"
 *  - any other category whose title or summary contains safety keywords
 *  - explicit alerts.json as fallback (kept empty by default).
 */
const ALERT_KEYWORDS = [
  'wycofan',
  'black box',
  'ostrzeżenie',
  'zagrożenie',
  'epidemi',
  'recall',
  'fda warning',
  'black-box',
  'alert',
];

const isAlertItem = (item) => {
  if (!item || !item.title) return false;
  if (item.type === 'ALERT') return true;
  const safety = String(item.safety_level || '').toLowerCase();
  if (
    safety.includes('wycofanie') ||
    safety.includes('wycofan') ||
    safety.includes('black box') ||
    safety.includes('alert')
  ) {
    return true;
  }
  const text = (
    (item.title || '') +
    ' ' +
    (item.summary || '') +
    ' ' +
    (item.drug_status || '')
  ).toLowerCase();
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

  [
    'alerts',
    'regulatory_safety',
    'epidemiology',
    'news_pl',
    'news_world',
    'guidelines',
    'clinical_intelligence',
  ].forEach((k) => {
    const list = allData[k];
    if (Array.isArray(list)) list.forEach(addItem);
  });

  // Recency-bounded alerts (last 7 days) sorted newest first.
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
    <div className="bg-gradient-to-br from-blue-950 via-slate-900 to-slate-950 text-white p-6 rounded-xl shadow-2xl shadow-black/40 ring-1 ring-blue-500/20">
      <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
        <h2 className="text-xs font-black uppercase tracking-[0.2em] text-blue-400">
          Artykuł Dnia
        </h2>
        <div className="flex items-center gap-3">
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
        className="block hover:opacity-90 transition-opacity"
      >
        <h3 className="text-xl font-bold mb-3 leading-tight text-slate-50">{data.title}</h3>
        <p className="text-sm text-blue-200/90 leading-relaxed italic mb-4">
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

function App() {
  const [allData, setAllData] = useState({});

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
              // Centralised: filter to recency window + sort newest first + assign id.
              const windowDays = SLOW_MOVING_FILES.has(file) ? SLOW_MOVING_WINDOW_DAYS : 7;
              const filtered = json
                .filter((item) => isRecent(item.date, new Date(), windowDays))
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

  const getDataFor = (key) => allData[key] || [];

  // Derived values: article of the day and ticker alerts.
  const articleOfDay = useMemo(() => selectArticleOfDay(allData), [allData]);
  const alerts = useMemo(() => generateAlerts(allData), [allData]);

  return (
    <div className="min-h-screen bg-transparent flex flex-col">
      <header className="bg-slate-950/80 backdrop-blur border-b border-blue-900/30 text-white py-6 shadow-lg shadow-black/30 text-center shrink-0">
        <h1 className="text-4xl font-black tracking-tighter uppercase italic text-blue-100">
          MEDINT
        </h1>
        <p className="text-blue-400/80 text-sm font-medium">
          Monitoring Medycyny i Nauk Klinicznych
        </p>
      </header>

      {/* High Priority Section: Alerts ticker + hero (Clinical Intelligence Feed left, Article of the day right) */}
      <div className="shrink-0">
        <AlertsTicker data={alerts} />
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
            <ClinicalIntelligenceFeed data={getDataFor('clinical_intelligence')} />
            {articleOfDay && <ArticleOfDay data={articleOfDay} />}
          </div>
        </div>
      </div>

      <main className="flex-1 p-4 custom-scrollbar overflow-y-auto">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <NewsSection title="Polska" data={getDataFor('news_pl')} />
            <ClinicalResearchSection
              title="Badania Kliniczne"
              data={getDataFor('clinical_research')}
            />
            <RegulatorySafetySection
              title="Regulatory & Drug Safety"
              data={getDataFor('regulatory_safety')}
            />
            <GuidelinesSectionV2
              title="Wytyczne i Rekomendacje"
              data={getDataFor('guidelines')}
            />
            <AISection
              title="AI w Medycynie"
              data={getDataFor('ai_medicine')}
            />
            <NewsSection
              title="Epidemiologia i Zdrowie Publiczne"
              data={getDataFor('epidemiology')}
            />
            <NewsSection
              title="Rynek Farmaceutyczny i Biotech"
              data={getDataFor('pharma_market')}
            />
            <NewsSection title="Świat" data={getDataFor('news_world')} />
          </div>
        </div>
      </main>

      <footer className="py-4 text-center text-slate-500 text-xs border-t border-slate-800 shrink-0 bg-slate-950/60">
        &copy; {new Date().getFullYear()} MEDINT - Wszystkie prawa zastrzeżone.
      </footer>
    </div>
  );
}

export default App;
