import React, { useState, useEffect } from 'react';

const TrialCard = ({ item }) => {
  return (
    <div className="bg-white p-3 rounded-lg transition-all duration-300 border border-gray-100 hover:shadow-sm group">
      <a href={item.url} target="_blank" rel="noopener noreferrer" className="block">
        <div className="flex justify-between items-start mb-2">
          <div className="flex gap-2">
            <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-green-100 text-green-700">
              {item.phase || 'Faza ?'}
            </span>
            <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700">
              {item.specialization || 'Ogólne'}
            </span>
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
          <span className="text-blue-600 text-[10px] font-bold">Szczegóły →</span>
        </div>
      </a>
    </div>
  );
};

const ClinicalTrialsSection = ({ title, filename, refreshTrigger }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('Wszystkie');

  const specializations = ['Wszystkie', 'Onkologia', 'Kardiologia', 'Neurologia', 'Diabetologia', 'AI w Medycynie'];

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

  const filteredItems = items.filter(item => {
    const specMatch = filter === 'Wszystkie' || item.specialization === filter;
    return specMatch;
  });

  if (loading) return (
    <div className="bg-gray-50 p-4 rounded-xl shadow-sm h-[450px]">
      <h2 className="text-xl font-bold text-gray-800 mb-4 border-b-2 border-blue-500 pb-2">{title}</h2>
      <p className="text-gray-400 text-center mt-10">Ładowanie badań klinicznych...</p>
    </div>
  );

  return (
    <div className="bg-gray-50 p-4 rounded-xl shadow-sm h-[450px] flex flex-col">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 border-b-2 border-blue-500 pb-2 gap-2">
        <h2 className="text-xl font-bold text-gray-800 shrink-0">{title}</h2>
        <div className="flex flex-wrap gap-1">
          {specializations.map(spec => (
            <button
              key={spec}
              onClick={() => setFilter(spec)}
              className={`text-[10px] px-2 py-1 rounded-full transition-colors ${
                filter === spec
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-100'
              }`}
            >
              {spec}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="space-y-3">
          {filteredItems.length > 0 ? (
            filteredItems.map((item, i) => <TrialCard key={i} item={item} />)
          ) : (
            <p className="text-gray-400 text-center mt-10 text-sm">Brak wyników dla wybranej specjalizacji.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClinicalTrialsSection;
