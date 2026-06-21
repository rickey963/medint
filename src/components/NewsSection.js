import React from 'react';
import { formatToPolishFormat } from '../utils/dateUtils';
import { cleanSummary } from '../utils/textUtils';

const NewsSection = ({ title, data }) => {
  return (
    <div className="bg-slate-900/60 p-4 rounded-xl shadow-lg shadow-black/20 border border-slate-800 h-[450px] flex flex-col">
      <h2 className="text-xl font-bold text-slate-100 mb-4 border-b-2 border-blue-500 pb-2 shrink-0">{title}</h2>
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="space-y-3">
          {data && data.length > 0 ? (
            data.map((item, index) => (
              <div
                key={index}
                className="p-3 rounded-lg transition-colors duration-300 border border-slate-800 hover:border-blue-700/50 hover:bg-slate-800/60 bg-slate-800/30 group"
              >
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  <h3 className="text-md font-semibold text-blue-100 leading-tight mb-1 group-hover:text-blue-400 transition-colors">
                    {item.title}
                  </h3>

                  {item.summary && (
                    <p className="text-slate-400 text-xs mb-2 line-clamp-3">
                      {cleanSummary(item.summary, item.title)}
                    </p>
                  )}

                  <div className="flex items-center justify-between mt-2 text-[10px] text-slate-500">
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">
                      {item.source || 'Info'}
                    </span>
                    <span className="font-medium">{formatToPolishFormat(item.date)}</span>
                  </div>
                </a>
              </div>
            ))
          ) : (
            <p className="text-slate-500 text-center mt-10 text-sm">Brak dostępnych informacji.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default NewsSection;
