import React, { useState } from 'react';
import { formatToPolishFormat } from '../utils/dateUtils';
import { cleanSummary } from '../utils/textUtils';

const ResearchSectionV2 = ({ title, data }) => {
  const [filter, setFilter] = useState('Wszystkie');

  const categories = ['Wszystkie', 'RCT', 'Meta-analiza', 'Systematic Review', 'Badanie kohortowe', 'Case Report'];

  const filteredData = data.filter(item =>
    filter === 'Wszystkie' || item.study_type === filter
  );

  return (
    <div className="bg-slate-900/60 p-4 rounded-xl shadow-lg shadow-black/20 border border-slate-800 h-[450px] flex flex-col">
      <div className="flex items-center justify-between mb-4 border-b-2 border-blue-500 pb-2 shrink-0">
        <h2 className="text-xl font-bold text-slate-100">{title}</h2>
        <div className="flex flex-wrap gap-1 max-w-[150px]">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`text-[9px] px-2 py-0.5 rounded-full transition-colors ${
                filter === cat
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="space-y-3">
          {filteredData.length > 0 ? (
            filteredData.map((item, index) => (
              <div key={index} className="bg-slate-800/30 p-3 rounded-lg transition-all duration-300 border border-slate-800 hover:border-blue-700/50 hover:bg-slate-800/60 group">
                <a href={item.url} target="_blank" rel="noopener noreferrer" className="block">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex gap-2">
                      <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20">
                        {item.study_type || 'Badanie'}
                      </span>
                      {item.impact_factor && (
                        <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                          IF: {item.impact_factor}
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-slate-500">{formatToPolishFormat(item.date)}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-blue-100 leading-tight mb-2 group-hover:text-blue-400 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-400 line-clamp-3 mb-3">
                    {cleanSummary(item.summary, item.title)}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-slate-500 font-medium">{item.source}</span>
                    <span className="text-blue-400 text-[10px] font-bold">Czytaj →</span>
                  </div>
                </a>
              </div>
            ))
          ) : (
            <p className="text-slate-500 text-center mt-10 text-sm">Brak wyników dla wybranej kategorii.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResearchSectionV2;
