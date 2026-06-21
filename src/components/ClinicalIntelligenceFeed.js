import React from 'react';
import { formatToPolishFormat, isWithinLastHour } from '../utils/dateUtils';
import { cleanSummary } from '../utils/textUtils';

const IntelligenceRow = ({ item }) => {
  const summary = cleanSummary(item.summary, item.title);
  const fresh = isWithinLastHour(item.date);
  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className={`block px-3 py-1.5 border-b border-slate-800 last:border-b-0 hover:bg-blue-500/10 transition-colors group ${
        fresh ? 'bg-blue-500/10' : ''
      }`}
    >
      <div className="flex items-center justify-between gap-2 mb-0.5">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="text-[9px] font-bold uppercase text-blue-300 bg-blue-500/10 border border-blue-500/20 px-1.5 py-0.5 rounded shrink-0">
            {item.source || 'MEDINT'}
          </span>
          {fresh && (
            <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-blue-400/20 text-blue-200 border border-blue-400/40 animate-pulse shrink-0">
              ● Nowe
            </span>
          )}
        </div>
        <span className="text-[9px] text-slate-500 shrink-0">{formatToPolishFormat(item.date)}</span>
      </div>
      <h3 className="text-xs font-semibold text-slate-200 leading-tight truncate group-hover:text-blue-400 transition-colors">
        {item.title}
      </h3>
      {summary && (
        <p className="text-[11px] text-slate-500 leading-snug line-clamp-2 mt-0.5">
          {summary}
        </p>
      )}
    </a>
  );
};

const ClinicalIntelligenceFeed = ({ data }) => {
  const items = data || [];

  if (items.length === 0) return null;

  return (
    <div className="w-full bg-slate-900/60 rounded-2xl border-2 border-blue-900/30 shadow-lg shadow-black/20 overflow-hidden flex flex-col">
      <div className="flex items-center gap-2 px-4 pt-2.5 pb-1.5 shrink-0">
        <div className="w-1.5 h-4 bg-blue-600 rounded-full"></div>
        <h2 className="text-sm font-black text-blue-300 uppercase tracking-tight italic">
          🧠 Clinical Intelligence Feed
        </h2>
      </div>
      <div className="max-h-[140px] overflow-y-auto custom-scrollbar">
        {items.map((item, i) => (
          <IntelligenceRow key={item.id || i} item={item} />
        ))}
      </div>
    </div>
  );
};

export default ClinicalIntelligenceFeed;
