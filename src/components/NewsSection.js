import React from 'react';
import { formatToPolishFormat } from '../utils/dateUtils';
import { cleanSummary } from '../utils/textUtils';

const NewsSection = ({ title, data }) => {
  return (
    <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 h-[450px] flex flex-col">
      <h2 className="text-xl font-bold text-gray-800 mb-4 border-b-2 border-blue-500 pb-2 shrink-0">{title}</h2>
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="space-y-3">
          {data && data.length > 0 ? (
            data.map((item, index) => (
              <div
                key={index}
                className="p-3 rounded-lg transition-colors duration-300 border border-gray-100 hover:shadow-sm bg-white group"
              >
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  <h3 className="text-md font-semibold text-blue-900 leading-tight mb-1 group-hover:text-blue-700 transition-colors">
                    {item.title}
                  </h3>

                  {item.summary && (
                    <p className="text-gray-600 text-xs mb-2 line-clamp-3">
                      {cleanSummary(item.summary, item.title)}
                    </p>
                  )}

                  <div className="flex items-center justify-between mt-2 text-[10px] text-gray-500">
                    <span className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 font-medium">
                      {item.source || 'Info'}
                    </span>
                    <span className="font-medium">{formatToPolishFormat(item.date)}</span>
                  </div>
                </a>
              </div>
            ))
          ) : (
            <p className="text-gray-400 text-center mt-10 text-sm">Brak dostępnych informacji.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default NewsSection;
