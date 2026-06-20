import React, { useState, useEffect } from 'react';

const ArticleList = ({ items }) => {
  const isRecent = (dateStr) => {
    if (!dateStr || dateStr === "Recent") return false;
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const oneHourAgo = new Date(now.getTime() - 60 * 60000);
      return date > oneHourAgo;
    } catch (e) {
      return false;
    }
  };

  return (
    <div className="h-[400px] overflow-y-auto pr-2 custom-scrollbar">
      <div className="space-y-3">
        {items.map((item, index) => {
          const recent = isRecent(item.date);
          return (
            <div
              key={index}
              className={`p-3 rounded-lg transition-colors duration-300 border ${
                recent
                  ? 'bg-blue-50 border-blue-200'
                  : 'bg-white border-gray-100 hover:shadow-sm'
              }`}
            >
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block group"
              >
                <h3 className="text-md font-semibold text-blue-900 leading-tight mb-1 group-hover:text-blue-700 transition-colors">
                  {item.title}
                </h3>

                {item.summary && (
                  <p className="text-gray-600 text-xs mb-2 line-clamp-3">
                    {item.summary}
                  </p>
                )}

                <div className="flex items-center justify-between mt-2 text-[10px] text-gray-500">
                  <span className={`px-1.5 py-0.5 rounded ${recent ? 'bg-blue-200 text-blue-800 font-medium' : 'bg-gray-100 text-gray-600'}`}>
                    {item.source || 'Info'}
                  </span>
                  <span className="font-medium">{item.date}</span>
                </div>
              </a>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const NewsSection = ({ title, filename, refreshTrigger }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`./data/${filename}?t=${refreshTrigger}`)
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
  }, [filename, refreshTrigger]);

  if (loading) return (
    <div className="bg-gray-50 p-4 rounded-xl shadow-sm h-[450px]">
      <h2 className="text-xl font-bold text-gray-800 mb-4 border-b-2 border-blue-500 pb-2">{title}</h2>
      <p className="text-gray-400 text-center mt-10">Ładowanie...</p>
    </div>
  );

  if (items.length === 0) return (
    <div className="bg-gray-50 p-4 rounded-xl shadow-sm h-[450px]">
      <h2 className="text-xl font-bold text-gray-800 mb-4 border-b-2 border-blue-500 pb-2">{title}</h2>
      <p className="text-gray-400 text-center mt-10">Brak aktualnych informacji.</p>
    </div>
  );

  return (
    <div className="bg-gray-50 p-4 rounded-xl shadow-sm h-[450px] flex flex-col">
      <h2 className="text-xl font-bold text-gray-800 mb-4 border-b-2 border-blue-500 pb-2 shrink-0">
        {title}
      </h2>
      <ArticleList items={items} />
    </div>
  );
};

export default NewsSection;
