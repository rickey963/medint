import React, { useState, useEffect } from 'react';

const ResearchCard = ({ item }) => {
  return (
    <div className="bg-white p-3 rounded-lg transition-all duration-300 border border-gray-100 hover:shadow-sm group">
      <a href={item.url} target="_blank" rel="noopener noreferrer" className="block">
        <div className="flex justify-between items-start mb-2">
          <div className="flex gap-2">
            <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">
              {item.study_type || 'Badanie'}
            </span>
            {item.impact_factor && (
              <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-amber-100 text-amber-700">
                IF: {item.impact_factor}
              </span>
            )}
          </div>
          <span className="text-[10px] text-gray-400">{item.date}</span>
        </div>
        <h3 className="text-sm font-semibold text-blue-900 leading-tight mb-2 group-hover:text-blue-700 transition-colors">
          {item.title}
        </h3>
        <p className="text-xs text-gray-600 line-clamp-3 mb-3">
          {item.summary}
        </p>
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-gray-500 font-medium">{item.source}</span>
          <span className="text-blue-600 text-[10px] font-bold">Czytaj →</span>
        </div>
      </a>
    </div>
  );
};

const ResearchSectionV2 = ({ title, filename, refreshTrigger }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('Wszystkie');

  const categories = ['Wszystkie', 'RCT', 'Meta-analiza', 'Systematic Review', 'Badanie kohortowe', 'Case Report'];

  useEffect(() => {
    fetch(`./data/${filename}?t=${refreshTrigger}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        setItems(data || []);
        setLoading(false);
      })
      .catch(e => {
        console.error(`Error fetching ${filename}:`, e);
        setLoading(false);
      });
  }, [filename, refreshTrigger]);

  const filteredItems = filter === 'Wszystkie'
    ? items
    : items.filter(item => item.study_type === filter);

  if (loading) return (
    <div className="bg-gray-50 p-4 rounded-xl shadow-sm h-[450px]">
      <h2 className="text-xl font-bold text-gray-800 mb-4 border-b-2 border-blue-500 pb-2">{title}</h2>
      <p className="text-gray-400 text-center mt-10">Ładowanie badań...</p>
    </div>
  );

  return (
    <div className="bg-gray-50 p-4 rounded-xl shadow-sm h-[450px] flex flex-col">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 border-b-2 border-blue-500 pb-2 gap-2">
        <h2 className="text-xl font-bold text-gray-800 shrink-0">{title}</h2>
        <div className="flex flex-wrap gap-1">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`text-[10px] px-2 py-1 rounded-full transition-colors ${
                filter === cat
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-100'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="space-y-3">
          {filteredItems.length > 0 ? (
            filteredItems.map((item, i) => <ResearchCard key={i} item={item} />)
          ) : (
            <p className="text-gray-400 text-center mt-10 text-sm">Brak publikacji w tej kategorii.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResearchSectionV2;
