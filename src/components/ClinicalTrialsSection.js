import React, { useState } from 'react';
import { formatToPolishFormat } from '../utils/dateUtils';
import { cleanSummary } from '../utils/textUtils';

const ClinicalTrialsSection = ({ title, data }) => {
  const [filter, setFilter] = useState('Wszystkie');

  const specializations = ['Wszystkie', 'Onkologia', 'Kardiologia', 'Neurologia', 'Diabetologia', 'AI w Medycynie'];

  const filteredData = data.filter(item =>
    filter === 'Wszystkie' || item.specialization === filter
  );

  return (
    <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 h-[450px] flex flex-col">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 border-b-2 border-blue-500 pb-2 shrink-0">
        <h2 className="text-xl font-bold text-gray-800 shrink-0">{title}</h2>
        <div className="flex flex-wrap gap-1 max-w-[200px]">
          {specializations.map(spec => (
            <button
              key={spec}
              onClick={() => setFilter(spec)}
              className={`text-[9px] px-2 py-1 rounded-full transition-colors ${
                filter === spec
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
              }`}
            >
              {spec}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="space-y-3">
          {filteredData.length > 0 ? (
            filteredData.map((item, index) => (
              <div key={index} className="p-3 rounded-lg transition-all duration-300 border border-gray-100 hover:shadow-sm bg-white group">
                <a href={item.url} target="_blank" rel="noopener noreferrer" className="block">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-100">
                      {item.specialization || 'Badanie'}
                    </span>
                    <span className="text-[10px] text-gray-400">{formatToPolishFormat(item.date)}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-blue-900 leading-tight mb-2 group-hover:text-blue-700 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs text-gray-600 line-clamp-3 mb-3">
                    {cleanSummary(item.summary, item.title)}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-gray-500 font-medium">{item.source}</span>
                    <span className="text-blue-600 text-[10px] font-bold">Szczegóły →</span>
                  </div>
                </a>
              </div>
            ))
          ) : (
            <p className="text-gray-400 text-center mt-10 text-sm">Brak wyników dla wybranej specjalizacji.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClinicalTrialsSection;
