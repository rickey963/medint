import React, { useState, useEffect } from 'react';

const ArticleList = ({ items }) => {
  const isRecent = (dateStr) => {
    if (!dateStr || dateStr === "Recent") return false;
    const date = new Date(dateStr);
    const now = new Date();
    const thirtyMinutesAgo = new Date(now.getTime() - 30 * 60000);
    return date > thirtyMinutesAgo;
  };

  return (
    <div className="max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
      <div className="space-y-4">
        {items.map((item, index) => {
          const recent = isRecent(item.date);
          return (
            <div
              key={index}
              className={`p-4 rounded-lg transition-colors duration-300 border ${
                recent
                  ? 'bg-blue-50 border-blue-200'
                  : 'bg-white border-gray-100 hover:shadow-md'
              }`}
            >
              <h3 className="text-lg font-semibold text-blue-900 leading-tight mb-2">
                {item.title}
              </h3>

              {item.summary && (
                <p className="text-gray-600 text-sm mb-3 line-clamp-3">
                  {item.summary}
                </p>
              )}

              {item.description && (
                <p className="text-gray-700 text-sm mb-3">
                  {item.description}
                </p>
              )}

              <div className="flex items-center justify-between mt-4 text-xs text-gray-50
                <span className={`px-2 py-1 rounded ${recent ? 'bg-blue-200 text-blue-800' : 'bg-blue-50 text-blue-700'}`}>
                  {item.source || 'Info'}
                </span>
                <span>{item.date}</span>
              </div>

              {item.url && (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-block text-blue-600 hover:text-blue-800 text-xs font-bold transition-colors"
                >
                  Czytaj więcej →
                </a>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const NewsSection = ({ title, filename }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`./data/${filename}`)
      .then((response) => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then((data) => {
        setItems(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error(`Error fetching ${filename}:`, error);
        setLoading(false);
      });
  }, [filename]);

  if (loading) return null;
  if (items.length === 0) return null;

  return (
    <div className="mb-8 bg-gray-50 p-4 rounded-xl shadow-sm">
      <h2 className="text-2xl font-bold text-gray-800 mb-4 border-b-2 border-blue-500 pb-2">
        {title}
      </h2>
      <ArticleList items={items} />
    </div>
  );
};

export default NewsSection;
