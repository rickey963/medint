import React, { useState, useEffect } from 'react';
import NewsSection from './components/NewsSection';
import ClinicalIntelligenceFeed from './components/ClinicalIntelligenceFeed';
import ResearchSectionV2 from './components/ResearchSectionV2';
import ClinicalTrialsSection from './components/ClinicalTrialsSection';
import RegulatorySafetySection from './components/RegulatorySafetySection';
import AISection from './components/AISection';
import GuidelinesSectionV2 from './components/GuidelinesSectionV2';

const AlertsTicker = ({ data }) => {
  if (!data || data.length === 0) return null;

  const alertText = data
    .map(item => `🚨 ${item.title} — ${item.summary}`)
    .join('   |   ');

  return (
    <div className="bg-red-600 text-white py-2 overflow-hidden whitespace-nowrap relative shadow-md">
      <div className="animate-marquee absolute whitespace-nowrap hover:pause">
        <span className="text-sm font-bold uppercase tracking-wide">
          {alertText} {alertText}
        </span>
      </div>
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-marquee {
          animation: marquee 40s linear infinite;
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
  if (!data) return null;
  return (
    <div className="bg-blue-900 text-white p-6 rounded-xl shadow-2xl ring-4 ring-blue-100">
      <h2 className="text-xs font-black uppercase tracking-[0.2em] text-blue-300 mb-2">Artykuł Dnia</h2>
      <h3 className="text-xl font-bold mb-4 leading-tight">{data.title}</h3>
      <p className="text-sm text-blue-100 opacity-90 mb-4 italic">"{data.why_read}"</p>
      <div className="border-t border-blue-800 pt-4 mt-4">
        <span className="text-[10px] font-bold uppercase text-blue-400">Poziom dowodów: {data.evidence_level}</span>
      </div>
    </div>
  );
};

function App() {
  const [alertsData, setAlertsData] = useState([]);
  const [articleData, setArticleData] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(Date.now());

  const fetchData = async () => {
    try {
      const [alertsRes, articleRes] = await Promise.all([
        fetch(`./data/alerts.json?t=${Date.now()}`).then(r => r.ok ? r.json() : null),
        fetch(`./data/daily_article.json?t=${Date.now()}`).then(r => r.ok ? r.json() : null)
      ]);

      if (alertsRes) setAlertsData(alertsRes);
      if (articleRes) setArticleData(articleRes);
    } catch (error) {
      console.error("Error loading dynamic content:", error);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
      fetchData();
      setRefreshTrigger(Date.now());
    }, 120000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-screen bg-gray-100 flex flex-col overflow-hidden">
      <header className="bg-blue-900 text-white py-6 shadow-lg text-center shrink-0">
        <h1 className="text-4xl font-black tracking-tighter uppercase italic">MEDINT</h1>
        <p className="text-blue-200 text-sm font-medium opacity-80">Monitoring Medycyny i Nauk Klinicznych</p>
      </header>

      <AlertsTicker data={alertsData} />

      <main className="flex-1 overflow-y-auto p-4 custom-scrollbar">
        <div className="max-w-7xl mx-auto">
          {/* v2 Step 1: Hero Section - Clinical Intelligence Feed */}
          <ClinicalIntelligenceFeed filename="clinical_intelligence.json" refreshTrigger={refreshTrigger} />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Tile 1: Polska */}
            <NewsSection title="Polska" filename="news_pl.json" refreshTrigger={refreshTrigger} />

            {/* Tile 2: Świat */}
            <NewsSection title="Świat" filename="news_world.json" refreshTrigger={refreshTrigger} />

            {/* Tile 3: Badania (v2) */}
            <ResearchSectionV2 title="Nowe Publikacje Naukowe" filename="research.json" refreshTrigger={refreshTrigger} />

            {/* Tile 4: Badania Kliniczne (v2) */}
            <ClinicalTrialsSection title="Badania Kliniczne" filename="clinical_trials.json" refreshTrigger={refreshTrigger} />

            {/* Tile 5: Bezpieczeństwo i Regulacje (v2) */}
            <RegulatorySafetySection title="Bezpieczeństwo i Regulacje" filename="regulatory_safety.json" refreshTrigger={refreshTrigger} />

            {/* Tile 6: Wytyczne (v2) */}
            <GuidelinesSectionV2 title="Wytyczne i Rekomendacje" filename="guidelines.json" refreshTrigger={refreshTrigger} />

            {/* Tile 7: AI w Medycynie (v2) */}
            <AISection title="AI w Medycynie" filename="ai_medicine.json" refreshTrigger={refreshTrigger} />

            {/* Tile 8: Zmiany Prawne */}
            <NewsSection title="Zmiany Prawne" filename="legal.json" refreshTrigger={refreshTrigger} />

            {/* Tile 9: Leki */}
            <NewsSection title="Leki" filename="drugs.json" refreshTrigger={refreshTrigger} />

            {/* Tile 10: Alerty Medyczne (Full list) */}
            <NewsSection title="Alerty Medyczne" filename="alerts.json" refreshTrigger={refreshTrigger} />

            {/* Bottom Section: Article of the Day */}
            <div className="lg:col-span-2 flex items-center justify-center">
               <ArticleOfDay data={articleData} />
            </div
          </div
        </div>
      </main>

      <footer className="py-4 text-center text-gray-400 text-xs border-t border-gray-200 shrink-0 bg-gray-100">
        &copy; {new Date().getFullYear()} MEDINT - Wszystkie prawa zastrzeżone.
      </footer>
    </div>
  );
}

export default App;
