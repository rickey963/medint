import React from 'react';
import { formatToPolishFormat } from '../utils/dateUtils';
import { cleanSummary } from '../utils/textUtils';

const IntelligenceRow = ({ item }) => {
  const summary = cleanSummary(item.summary, item.title);
  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-3 px-3 py-2 border-b border-slate-800 last:border-b-0 hover:bg-blue-500/10 transition-colors group"
    >
      <span className="text-[10px] font-bold uppercase text-blue-300 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded shrink-0">
        {item.source || 'MEDINT'}
      </span>
      <h3 className="text-sm font-semibold text-slate-200 leading-tight truncate group-hover:text-blue-400 transition-colors flex-1">
        {item.title}
      </h3>
      {summary && (
        <p className="hidden lg:block text-xs text-slate-500 italic truncate flex-1">
          {summary}
        </p>
      )}
      <span className="text-[10px] text-slate-500 shrink-0">{formatToPolishFormat(item.date)}</span>
    </a>
  );
};

const ClinicalIntelligenceFeed = ({ data }) => {
  const items = data || [];

  if (items.length === 0) return null;

  return (
    <div className="w-full bg-slate-900/60 rounded-2xl border-2 border-blue-900/30 shadow-lg shadow-black/20 overflow-hidden">
      <div className="flex items-center gap-3 px-4 pt-3 pb-2">
        <div className="w-2 h-6 bg-blue-600 rounded-full"></div>
        <h2 className="text-base font-black text-blue-300 uppercase tracking-tight italic">
          Clinical Intelligence Feed
        </h2>
      </div>
      <div className="max-h-[200px] overflow-y-auto custom-scrollbar">
        {items.map((item, i) => (
          <IntelligenceRow key={item.id || i} item={item} />
        ))}
      </div>
    </div>
  );
};

export default ClinicalIntelligenceFeed;
