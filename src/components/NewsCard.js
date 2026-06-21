import React from 'react';
import DateBadge from './DateBadge';
import { cleanSummary } from '../utils/textUtils';

const ACCENTS = {
  blue: {
    title: 'text-blue-900 group-hover:text-blue-700',
    tag: 'bg-blue-50 text-blue-700 border-blue-100',
    link: 'text-blue-600',
    card: 'border-gray-100',
  },
  red: {
    title: 'text-red-900 group-hover:text-red-700',
    tag: 'bg-red-50 text-red-700 border-red-100',
    link: 'text-red-600',
    card: 'border-red-100',
  },
  green: {
    title: 'text-green-900 group-hover:text-green-700',
    tag: 'bg-green-50 text-green-700 border-green-100',
    link: 'text-green-600',
    card: 'border-green-100',
  },
  indigo: {
    title: 'text-indigo-900 group-hover:text-indigo-700',
    tag: 'bg-indigo-50 text-indigo-700 border-indigo-100',
    link: 'text-indigo-600',
    card: 'border-indigo-100',
  },
  amber: {
    title: 'text-amber-900 group-hover:text-amber-700',
    tag: 'bg-amber-50 text-amber-700 border-amber-200',
    link: 'text-amber-600',
    card: 'border-amber-200',
  },
  slate: {
    title: 'text-slate-900 group-hover:text-slate-700',
    tag: 'bg-slate-50 text-slate-700 border-slate-100',
    link: 'text-slate-600',
    card: 'border-slate-100',
  },
};

const NewsCard = ({ item, accent = 'blue', tagLabel, tagClass = '', showTag = true }) => {
  const palette = ACCENTS[accent] || ACCENTS.blue;
  const summary = cleanSummary(item.summary, item.title);
  const tagText = tagLabel || item.study_type || item.specialization || item.safety_level || item.ai_category || item.change_type || item.drug_status || item.source || 'Info';

  return (
    <div
      className={`p-3 rounded-lg transition-all duration-300 border ${palette.card} hover:shadow-sm bg-white group`}
    >
      <a
        href={item.url || '#'}
        target="_blank"
        rel="noopener noreferrer"
        className="block"
      >
        {/* Top row: tag + date badge */}
        <div className="flex items-center justify-between mb-2 gap-2">
          {showTag && (
            <span
              className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${tagClass || palette.tag}`}
            >
              {tagText}
            </span>
          )}
          <DateBadge date={item.date} />
        </div>

        {/* Title */}
        <h3
          className={`text-sm font-semibold leading-tight mb-2 ${palette.title} transition-colors`}
        >
          {item.title}
        </h3>

        {/* Summary - never duplicates the title */}
        {summary && (
          <p className="text-xs text-gray-600 line-clamp-3 mb-2 leading-relaxed">
            {summary}
          </p>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between mt-2">
          <span className="text-[10px] text-gray-500 font-medium">
            {item.source || 'MEDINT'}
          </span>
          <span className={`text-[10px] font-bold ${palette.link}`}>
            Czytaj →
          </span>
        </div>
      </a>
    </div>
  );
};

export default NewsCard;
