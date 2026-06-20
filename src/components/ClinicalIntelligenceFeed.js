import React, { useState, useEffect } from 'react';

const IntelligenceCard = ({ item }) => {
  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border-l-4 border-blue-600 hover:shadow-md transition-all duration-300 group">
      <a href={item.url} target="_blank" rel="noopener noreferrer" className="block">
        <div className="flex justify-between items-start mb-2">
          <span className="text-[10px] font-bold uppercase text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
            {item.source}
          </span>
          <span className="text-[10px] text-gray-400">{item.date}</span>
        </div>
        <h3 className="text-lg font-bold text-gray-800 leading-tight mb-2 group-hover:text-blue-700 transition-colors">
          {item.title}
        </h3>
        <p className="text-sm text-gray-600 line-clamp-3 italic">
          "{item.summary}"
        </p>
      </a>
    </div>
  );
};

const ClinicalIntelligenceFeed = ({ filename, refreshTrigger }) => {
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
        console.error("Error loading Intelligence Feed:", e);
        setLoading(false);
      });
  }, [filename, refreshTrigger]);

  if (loading) return (
    <div className="w-full bg-blue-50 p-6 rounded-2xl border-2 border-blue-100 mb-8">
      <h2 className="text-xl font-black text-blue-900 mb-4 uppercase tracking-wider">Clinical Intelligence Feed</h2>
      <p className="text-center text-blue-400 animate-pulse">Przeszukiwanie elitarnych czasopism medycznych...</p>
    </div>
  );

  if (items.length === 0) return null;

  return (
    <div className="w-full bg-blue-50 p-6 rounded-2xl border-2 border-blue-100 mb-8 shadow-inner">
      <div className="flex items-center mb-6">
        <div className="w-2 h-8 bg-blue-600 rounded-full mr-3"></div>
        <h2 className="text-2xl font-black text-blue-900 uppercase tracking-tighter italic">
          Clinical Intelligence Feed
        </h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item, i) => (
          <IntelligenceCard key={i} item={item} />
        ))}
      </div>
    </div>
  );
};

export default ClinicalIntelligenceFeed;
