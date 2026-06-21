import React, { useState, useEffect, useMemo, useRef } from 'react';
import NewsSection from './components/NewsSection';
import ClinicalIntelligenceFeed from './components/ClinicalIntelligenceFeed';
import ResearchSectionV2 from './components/ResearchSectionV2';
import ClinicalTrialsSection from './components/ClinicalTrialsSection';
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

const DATA_FILES = [
  'news_pl.json',
  'news_world.json',
  'research.json',
  'clinical_trials.json',
  'regulatory_safety.json',
  'guidelines.json',
  'ai_medicine.json',
  'legal.json',
  'drugs.json',
  'clinical_intelligence.json',
  'alerts.json',
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
 * Score = (prestige_weight * 0.5) + recency_factor.
 * Recency_factor decays linearly from 5 (today) to 0 (7 days old).
 */
const selectArticleOfDay = (allData) => {
  const pools = [
    'research',
    'clinical_intelligence',
    'news_world',
    'news_pl',
    'clinical_trials',
    'regulatory_safety',
    'ai_medicine',
    'guidelines',
    'legal',
    'drugs',
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
    'drugs',
    'news_pl',
    'news_world',
    'legal',
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
  const itemsText = activeAlerts
    .map((item) => `🚨 ${item.title} — ${item.source || 'MEDINT'}`)
    .join('   •   ');

  useEffect(() => {
    if (!trackRef.current) return;
    const width = trackRef.current.scrollWidth / 2;
    setDuration(Math.max(20, width / TICKER_SPEED_PX_PER_SEC));
  }, [itemsText]);

  if (activeAlerts.length === 0) return null;

  return (
    <div className="bg-red-700 text-white h-10 md:h-11 overflow-hidden whitespace-nowrap relative shadow-lg shadow-red-950/40 z-50 flex items-center">
      <div
        ref={trackRef}
        className="animate-marquee absolute top-1/2 -translate-y-1/2 whitespace-nowrap hover:pause"
        style={{ animationDuration: `${duration}s` }}
      >
        <span className="text-sm md:text-base font-bold uppercase tracking-wide leading-none">
          {itemsText}    •    {itemsText}
        </span>
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
          display: inline-block;
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
              // Centralised: filter to last 7 days + sort newest first + assign id.
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

      {/* High Priority Section: Alerts ticker + Hero article of the day */}
      <div className="shrink-0">
        <AlertsTicker data={alerts} />
        <div className="max-w-7xl mx-auto px-4 py-4">
          {articleOfDay && <ArticleOfDay data={articleOfDay} />}
        </div>
      </div>

      <main className="flex-1 p-4 custom-scrollbar overflow-y-auto">
        <div className="max-w-7xl mx-auto space-y-6">
          <ClinicalIntelligenceFeed data={getDataFor('clinical_intelligence')} />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <NewsSection title="Polska" data={getDataFor('news_pl')} />
            <NewsSection title="Świat" data={getDataFor('news_world')} />
            <ResearchSectionV2
              title="Badania"
              data={getDataFor('research')}
            />
            <ClinicalTrialsSection
              title="Badania Kliniczne"
              data={getDataFor('clinical_trials')}
            />
            <RegulatorySafetySection
              title="Sygnały Bezpieczeństwa"
              data={getDataFor('regulatory_safety')}
            />
            <GuidelinesSectionV2
              title="Wytyczne"
              data={getDataFor('guidelines')}
            />
            <AISection
              title="AI w Medycynie"
              data={getDataFor('ai_medicine')}
            />
            <NewsSection
              title="Zmiany Prawne"
              data={getDataFor('legal')}
            />
            <NewsSection title="Leki" data={getDataFor('drugs')} />
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
