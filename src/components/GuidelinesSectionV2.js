import React from 'react';
import { formatToPolishFormat, isWithinLastHour, isWithinLastTwoHours } from '../utils/dateUtils';
import { cleanSummary } from '../utils/textUtils';
import ImportanceBadge from './ImportanceBadge';

const GuidelinesSectionV2 = ({ title, data }) => {
  return (
    <div className="bg-slate-900/60 p-4 rounded-xl shadow-lg shadow-black/20 border border-slate-800 h-[450px] flex flex-col">
      <h2 className="text-xl font-bold text-slate-100 mb-4 border-b-2 border-orange-500 pb-2 shrink-0">{title}</h2>
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="space-y-3">
          {data && data.length > 0 ? (
            data.map((item, index) => {
              const fresh = isWithinLastHour(item.date);
              const recent = isWithinLastTwoHours(item.date);
              return (
              <div key={index} className={`p-3 rounded-lg transition-all duration-300 border hover:border-blue-700/50 hover:bg-slate-800/60 group ${
                fresh ? 'border-emerald-400 bg-emerald-500/15 ring-2 ring-emerald-400/50 shadow-[0_0_16px_rgba(16,185,129,0.4)]'
                  : recent ? 'border-emerald-500/40 bg-emerald-500/5 ring-1 ring-emerald-400/20'
                  : item.is_update ? 'bg-amber-500/10 border-amber-500/30' : 'bg-slate-800/30 border-slate-800'
              }`}>
                <a href={item.url} target="_blank" rel="noopener noreferrer" className="block">
                  <div className="flex justify-between items-start mb-2 gap-2">
                    <div className="flex gap-2 flex-wrap">
                      <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${item.is_update ? 'bg-amber-500/20 text-amber-300 border-amber-500/30 animate-pulse' : 'bg-slate-800 text-slate-400 border-slate-700'}`}>
                        {item.change_type || 'Rekomendacja'}
                      </span>
                      {fresh && (
                        <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-emerald-400/25 text-emerald-200 border border-emerald-400/60 animate-pulse">
                          ● Nowe
                        </span>
                      )}
                      <ImportanceBadge item={item} />
                    </div>
                    <span className="text-[10px] text-slate-500 shrink-0">{formatToPolishFormat(item.date)}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-blue-100 leading-tight mb-2 group-hover:text-blue-400 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-400 line-clamp-3 mb-3">
                    {cleanSummary(item.summary, item.title)}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-slate-500 font-medium">{item.source}</span>
                    <span className="text-blue-400 text-[10px] font-bold">Szczegóły →</span>
                  </div>
                </a>
              </div>
              );
            })
          ) : (
            <p className="text-slate-500 text-center mt-10 text-sm">Brak aktualnych wytycznych.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default GuidelinesSectionV2;
