import React from 'react';
import { formatToPolishFormat } from '../utils/dateUtils';
import { cleanSummary } from '../utils/textUtils';
import ImportanceBadge from './ImportanceBadge';

const AISection = ({ title, data }) => {
  return (
    <div className="bg-slate-900/60 p-4 rounded-xl shadow-lg shadow-black/20 border border-slate-800 h-[450px] flex flex-col">
      <h2 className="text-xl font-bold text-slate-100 mb-4 border-b-2 border-indigo-500 pb-2 shrink-0">{title}</h2>
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="space-y-3">
          {data && data.length > 0 ? (
            data.map((item, index) => (
              <div key={index} className="p-3 rounded-lg transition-all duration-300 border border-indigo-500/20 hover:border-indigo-400/40 hover:bg-slate-800/60 bg-slate-800/30 group">
                <a href={item.url} target="_blank" rel="noopener noreferrer" className="block">
                  <div className="flex justify-between items-start mb-2 gap-2">
                    <div className="flex gap-2 flex-wrap">
                      <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                        {item.ai_category || 'AI Research'}
                      </span>
                      <ImportanceBadge item={item} />
                    </div>
                    <span className="text-[10px] text-slate-500 shrink-0">{formatToPolishFormat(item.date)}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-indigo-200 leading-tight mb-2 group-hover:text-indigo-400 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-400 line-clamp-3 mb-3">
                    {cleanSummary(item.summary, item.title)}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-slate-500 font-medium">{item.source}</span>
                    <span className="text-indigo-400 text-[10px] font-bold">Explore →</span>
                  </div>
                </a>
              </div>
            ))
          ) : (
            <p className="text-slate-500 text-center mt-10 text-sm">Brak aktualnych informacji o AI.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default AISection;
