import React, { useState, useEffect } from 'react';

const GuidelineCard = ({ item }) => {
  return (
    <div className={`p-3 rounded-lg transition-all duration-300 border ${item.is_update ? 'bg-amber-50 border-amber-200' : 'bg-white border-gray-100'} hover:shadow-sm group`}>
      <a href={item.url} target="_blank" rel="noopener noreferrer" className="block">
        <div className="flex justify-between items-start mb-2">
          <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${item.is_update ? 'bg-amber-200 text-amber-800 border-amber-300 animate-pulse' : 'bg-gray-100 text-gray-600 border-gray-200'}`}>
            {item.change_type || 'Rekomendacja'}
          </span>
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

const GuidelinesSectionV2 = ({ title, filename, refreshTrigger }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

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

  if (loading) return (
    <div className="bg-gray-50 p-4 rounded-xl shadow-sm h-[450px]">
      <h2 className="text-xl font-bold text-gray-800 mb-4 border-b-2 border-orange-500 pb-2">{title}</h2>
      <p className="text-gray-400 text-center mt-10">Weryfikacja wytycznych...</p>
    </div>
  );

  return (
    <div className="bg-gray-50 p-4 rounded-xl shadow-sm h-[450px] flex flex-col">
      <div className="flex items-center justify-between mb-4 border-b-2 border-orange-500 pb-2">
        <h2 className="text-xl font-bold text-gray-800">{title}</h2>
        <span className="text-orange-600 text-[10px] font-bold uppercase">Official Standards</span>
      </div>
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="space-y-3">
          {items.length > 0 ? (
            items.map((item, i) => <GuidelineCard key={i} item={item} />)
          ) : (
            <p className="text-gray-400 text-center mt-10 text-sm">Brak nowych rekomendacji.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default GuidelinesSectionV2;
