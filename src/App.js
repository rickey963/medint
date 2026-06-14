import React, { useState, useEffect } from 'react';
import Alerts from './components/Alerts';
import NewsSection from './components/NewsSection';
import ResearchSection from './components/ResearchSection';

const LegalCard = ({ title, effective_date, changes }) => (
  <div className="bg-white p-4 rounded shadow border-l-4 border-purple-500 mb-4">
    <h3 className="font-bold text-gray-800 text-lg">{title}</h3>
    <p className="text-sm text-gray-500 mb-2">Data wejścia: {effective_date}</p>
    <ul className="list-disc list-inside text-sm text-gray-700">
      {changes.map((c, i) => <li key={i}>{c}</li>)}
    </ul>
  </div>
);

const GuidelinesCard = ({ title, changes }) => (
  <div className="bg-white p-4 rounded shadow border-l-4 border-orange-500 mb-4">
    <h3 className="font-bold text-gray-800">{title}</h3>
    <ul className="mt-2 space-y-1 text-sm text-gray-700">
      {changes.map((c, i) => <li key={i}>• {c}</li>)}
    </ul>
  </div>
);

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
  const [legalData, setLegalData] = useState([]);
  const [guidelinesData, setGuidelinesData] = useState([]);
  const [articleData, setArticleData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [legalRes, guidelinesRes, articleRes] = await Promise.all([
          fetch('./data/legal.json').then(r => r.ok ? r.json() : null),
          fetch('./data/guidelines.json').then(r => r.ok ? r.json() : null),
          fetch('./data/daily_article.json').then(r => r.ok ? r.json() : null)
        ]);

        if (legalRes) setLegalData(legalRes);
        if (guidelinesRes) setGuidelinesData(guidelinesRes);
        if (articleRes) setArticleData(articleRes);
      } catch (error) {
        console.error("Error loading dynamic content:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 pb-12">
      <header className="bg-blue-900 text-white py-8 shadow-lg mb-8 text-center">
        <h1 className="text-5xl font-black tracking-tighter uppercase italic">MEDINT</h1>
        <p className="mt-2 text-blue-200 font-medium opacity-80">Monitoring Medycyny i Nauk Klinicznych</p>
      </header>

      <main className="max-w-6xl mx-auto px-4">
        {/* Section 1: Alerts */}
        <Alerts />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left & Center Columns: News and Research */}
          <div className="lg:col-span-2 space-y-8">
            <NewsSection title="Polska" filename="news_pl.json" />
            <NewsSection title="Świat" filename="news_world.json" />
            <ResearchSection title="Nowe Badania (EBM)" filename="research.json" />
          </div>

          {/* Sidebar: Legal and Guidelines */}
          <div className="space-y-8">
             <div>
                <h2 className="text-xl font-bold text-gray-800 mb-4 border-b-2 border-purple-500 pb-2">Zmiany Prawne</h2>
                {loading ? <p>Ładowanie...</p> : legalData.map((item, i) => (
                  <LegalCard key={i} {...item} />
                ))}
             </div>

             <div>
                <h2 className="text-xl font-bold text-gray-800 mb-4 border-b-2 border-orange-500 pb-2">Wytyczne</h2>
                {loading ? <p>Ładowanie...</p> : guidelinesData.map((item, i) => (
                  <GuidelinesCard key={i} {...item} />
                ))}
             </div>

             {/* Article of the Day */}
             <ArticleOfDay data={articleData} />
          </div>
        </div>
      </main>

      <footer className="mt-16 py-8 text-center text-gray-400 text-sm border-t border-gray-200">
        &copy; {new Date().getFullYear()} MEDINT - Wszystkie prawa zastrzeżone.
      </footer>
    </div>
  );
}

export default App;
