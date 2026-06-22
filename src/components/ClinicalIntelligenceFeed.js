import React from 'react';
import { formatToPolishFormat, isWithinLastHour, isWithinLastTwoHours } from '../utils/dateUtils';
import { cleanSummary } from '../utils/textUtils';

const IntelligenceRow = ({ item }) => {
  const summary = cleanSummary(item.summary, item.title);
  const fresh = isWithinLastHour(item.date);
  const recent = isWithinLastTwoHours(item.date);
  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className={`block px-3 py-2 border-b last:border-b-0 hover:bg-blue-500/10 transition-colors group ${
        fresh ? 'bg-emerald-500/15 border-emerald-400/50 border-l-2 border-l-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.3)]'
          : recent ? 'bg-emerald-500/5 border-emerald-500/30 border-l-2 border-l-emerald-500/40'
          : 'border-slate-800'
      }`}
    >
      <div className="flex items-center justify-between gap-2 mb-1">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="text-[9px] font-bold uppercase text-blue-300 bg-blue-500/10 border border-blue-500/20 px-1.5 py-0.5 rounded shrink-0">
            {item.source || 'MEDINT'}
          </span>
          {fresh && (
            <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-emerald-400/25 text-emerald-200 border border-emerald-400/60 animate-pulse shrink-0">
              ● Nowe
            </span>
          )}
        </div>
        <span className="text-[10px] text-slate-500 shrink-0">{formatToPolishFormat(item.date)}</span>
      </div>
      <h3 className="text-sm font-semibold text-slate-200 leading-tight mb-1 group-hover:text-blue-400 transition-colors">
        {item.title}
      </h3>
      {summary && (
        <p className="text-xs text-slate-500 leading-snug line-clamp-2">
          {summary}
        </p>
      )}
    </a>
  );
};

const ClinicalIntelligenceFeed = ({ data }) => {
  const items = data || [];

  return (
    <div className="bg-slate-900/60 rounded-2xl border-2 border-blue-900/30 shadow-lg shadow-black/20 h-[450px] flex flex-col lg:col-span-2">
      <div className="flex items-center gap-2 px-4 pt-4 pb-2 shrink-0 border-b-2 border-blue-900/30">
        <div className="w-1.5 h-4 bg-blue-600 rounded-full"></div>
        <h2 className="text-base font-black text-blue-300 uppercase tracking-tight italic">
          🧠 Clinical Intelligence Feed
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {items.length > 0 ? (
          items.map((item, i) => <IntelligenceRow key={item.id || i} item={item} />)
        ) : (
          <p className="text-slate-500 text-center mt-10 text-sm">Brak dostępnych informacji.</p>
        )}
      </div>
    </div>
  );
};

export default ClinicalIntelligenceFeed;
