import React, { useState, useEffect } from 'react';

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In a real GitHub Pages deployment, the path is relative to the base URL.
    // We fetch from the public-accessible data folder.
    fetch('./data/alerts.json')
      .then((response) => response.json())
      .then((data) => {
        setAlerts(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching alerts:', error);
        setLoading(false);
      });
  }, []);

  if (loading) return null;
  if (alerts.length === 0) return null;

  return (
    <div className="mb-8 space-y-3">
      <h2 className="text-lg font-bold text-red-700 uppercase tracking-wider flex items-center">
        <span className="flex h-3 w-3 mr-2">
          <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-red-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
        </span>
        Alerty Medyczne
      </h2>
      <div className="space-import">
        {alerts.map((alert, index) => (
          <div
            key={index}
            className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-md shadow-sm animate-pulse-slow"
          >
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <span className="text-red-600 font-bold text-xl">🔴</span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-bold text-red-80_0 uppercase tracking-tight">
                  {alert.type || 'ALERT'}
                </p>
                <p className="text-md text-red-900 font-semibold leading-tight mt-1">
                  {alert.title}
                </p>
                <div className="mt-2 flex items-center text-xs text-red-700">
                  <span className="font-medium uppercase mr-2">{alert.source}</span>
                  <span>•</span>
                  <span className="ml-2">{alert.date}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <style>{`
        @keyframes pulse-slow {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.8; }
        }
        .animate-pulse-slow {
          animation: pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
      `}</style>
    </div>
  );
};

export default Alerts;
