import React, { useState, useEffect } from 'react';

const SafetyCard = ({ item }) => {
  const getLevelColor = (level) => {
    if (level === '🔴 WYCOFanie') return 'bg-red-100 text-red-700 border-red-200';
    if (level === '🟠 BLACK BOX') return 'bg-orange-100 text-orange-700 border-orange-200';
    if (level === '🟡 ALERT') return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    if (level === '🟢 REJESTRACJA') return 'bg-green-100 text-green-700 border-green-200';
    return 'bg-gray-100 text-gray-700 border-gray-200';
  };

  return (
    <div className="bg-white p-3 rounded-lg transition-all duration-300 border border-gray-100 hover:shadow-sm group">
      <a href={item.url} target="_blank" rel="noopener noreferrer" className="block">
        <div className="flex justify-between items-start mb-2">
          <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${getLevelColor(item.safety_level)}`}>
            {item.safety_level || 'INFO'}
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
    </div >
  );
};

const RegulatorySafetySection = ({ title, filename, refreshTrigger }) => {
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
      <h2 className="text-xl font-bold text-gray-800 mb-4 border-b-2 border-blue-500 pb-2">{title}</h2>
      <p className="text-gray-400 text-center mt-10">Ładowanie danych regulacyjnych...</p>
    </div>
  );

  return (
    <div className="bg-gray-50 p-4 rounded-xl shadow-sm h-[450px] flex flex-col">
      <div className="flex items-center justify-between mb-4 border-b-2 border-blue-500 pb-2">
        <h2 className="text-xl font-bold text-gray-800">{title}</h2>
      </div>
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="space-y-3">
          {items.length > 0 ? (
            items.map((item, i) => <SafetyCard key={i} item={item} />)
          ) : (
            <p className="text-gray-400 text-center mt-10 text-sm">Brak aktualnych komunikatów.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default RegulatorySafetySection;
