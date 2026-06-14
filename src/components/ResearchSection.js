import React, { useState, useEffect } from 'react';

const ResearchSection = ({ title, filename }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`./data/${filename}`)
      .then((response) => response.json())
      .then((data) => {
        setItems(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error(`Error fetching research:`, error);
        setLoading(false);
      });
  }, [filename]);

  const isRecent = (dateStr) => {
    if (!dateStr || dateStr === "Recent") return false;
    const date = new Date(dateStr);
    const now = new Date();
    const thirtyMinutesAgo = new Date(now.getTime() - 30 * 60000);
    return date > thirtyMinutesAgo;
  };

  if (loading) return null;
  if (items.length === 0) return null;

  return (
    <div className="mb-8 bg-gray-50 p-4 rounded-xl shadow-sm">
      <h2 className="text-2xl font-bold text-gray-80
        text-gray-800 mb-4 border-b-2 border-green-500 pb-2">
        {title}
      </h2>
      <div className="max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
        <div className="space-y-4">
          {items.map((item, index) => {
            const recent = isRecent(item.date);
            return (
              <div
                key={index}
                className={`p-6 rounded-lg transition-colors duration-300 border ${
                  recent
                    ? 'bg-green-50 border-green-20<0xA0>'
                    : 'bg-white border-gray-100 hover:shadow-md'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-xl font-bold text-gray-900">{item.title}</h3>
                  <span className="bg-green-100 text-green-800 text-xs font-bold px-2 py-1 rounded uppercase">
                    {item.type || 'Badanie'}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 text-sm">
                  <div className="bg-gray-50 p-2 rounded">
                    <span className="block text-gray_500 font-bold uppercase text-[10px]">Pacjenci</span>
                    <span className="text-gray_800">{item.patient_count || 'N/A'}</span>
                  </div>
                  <div className="bg-gray-50 p-2 rounded">
                    <span className="block text-gray-500 font-bold uppercase text-[10px]">Dowody</span>
                    <span className="text-gray_800">{item.evidence_level || 'N/A'}</span>
                  </div>
                  <div className="bg-gray-50 p-2 rounded">
                    <span className="block text-gray-500 font-bold uppercase text-[10px]">Źródło</span>
                    <span className="text-gray_800">{item.source || 'N/A'}</span>
                  </div>
                </div>

                <div className="mt-4 text-gray-70
                  text-gray-700 italic">
                  "{item.conclusion}"
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ResearchSection;
