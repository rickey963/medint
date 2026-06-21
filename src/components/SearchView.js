import React, { useMemo, useState } from 'react';
import { formatToPolishFormat, ageInDays } from '../utils/dateUtils';
import { cleanSummary } from '../utils/textUtils';
import { scoreImportance, IMPORTANCE_STYLES, IMPORTANCE_LABELS } from '../utils/importance';

const ALL = 'Wszystkie';

const DATE_RANGES = [
  { key: ALL, label: 'Wszystkie daty', maxDays: Infinity },
  { key: '24h', label: 'Ostatnie 24h', maxDays: 1 },
  { key: '3d', label: 'Ostatnie 3 dni', maxDays: 3 },
  { key: '7d', label: 'Ostatnie 7 dni', maxDays: 7 },
];

const IMPORTANCE_LEVELS = [ALL, 'Critical', 'High', 'Medium', 'Low'];

const SelectFilter = ({ label, value, onChange, options }) => (
  <label className="flex flex-col gap-1 text-xs text-slate-400">
    {label}
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-2 py-1.5 focus:outline-none focus:border-blue-500"
    >
      {options.map((opt) => (
        <option key={opt.value ?? opt} value={opt.value ?? opt}>
          {opt.label ?? opt}
        </option>
      ))}
    </select>
  </label>
);

const SearchView = ({ articles, specialties, tileLabels }) => {
  const [query, setQuery] = useState('');
  const [tile, setTile] = useState(ALL);
  const [specialization, setSpecialization] = useState(ALL);
  const [source, setSource] = useState(ALL);
  const [importance, setImportance] = useState(ALL);
  const [dateRangeKey, setDateRangeKey] = useState(ALL);

  const sourceOptions = useMemo(() => {
    const set = new Set(articles.map((a) => a.source).filter(Boolean));
    return [ALL, ...Array.from(set).sort((a, b) => a.localeCompare(b))];
  }, [articles]);

  const tileOptions = useMemo(
    () => [ALL, ...Object.values(tileLabels)],
    [tileLabels]
  );

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    const range = DATE_RANGES.find((r) => r.key === dateRangeKey) || DATE_RANGES[0];

    return articles
      .filter((item) => {
        if (q) {
          const text = `${item.title || ''} ${item.summary || ''}`.toLowerCase();
          if (!text.includes(q)) return false;
        }
        if (tile !== ALL && item._tileLabel !== tile) return false;
        if (source !== ALL && item.source !== source) return false;
        if (specialization !== ALL && !(item.specializations || []).includes(specialization)) return false;
        if (importance !== ALL && scoreImportance(item) !== importance) return false;
        if (range.maxDays !== Infinity) {
          const age = ageInDays(item.date);
          if (age < 0 || age > range.maxDays) return false;
        }
        return true;
      })
      .sort((a, b) => (ageInDays(a.date) ?? Infinity) - (ageInDays(b.date) ?? Infinity))
      .slice(0, 100);
  }, [articles, query, tile, source, specialization, importance, dateRangeKey]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <h2 className="text-lg font-bold text-slate-100 mb-4">🔍 Wyszukiwarka globalna</h2>

      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Szukaj po tytule lub treści streszczenia..."
        className="w-full bg-slate-800 border border-slate-700 text-slate-100 text-sm rounded-lg px-3 py-2.5 mb-4 focus:outline-none focus:border-blue-500 placeholder:text-slate-500"
      />

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        <SelectFilter label="Kafelek" value={tile} onChange={setTile} options={tileOptions} />
        <SelectFilter label="Źródło" value={source} onChange={setSource} options={sourceOptions} />
        <SelectFilter
          label="Specjalizacja"
          value={specialization}
          onChange={setSpecialization}
          options={[ALL, ...specialties]}
        />
        <SelectFilter
          label="Poziom ważności"
          value={importance}
          onChange={setImportance}
          options={IMPORTANCE_LEVELS.map((lvl) => ({
            value: lvl,
            label: lvl === ALL ? ALL : IMPORTANCE_LABELS[lvl],
          }))}
        />
        <SelectFilter
          label="Zakres dat"
          value={dateRangeKey}
          onChange={setDateRangeKey}
          options={DATE_RANGES.map((r) => ({ value: r.key, label: r.label }))}
        />
      </div>

      <p className="text-xs text-slate-500 mb-3">
        Znaleziono {results.length} {results.length === 1 ? 'wynik' : 'wyników'}
        {results.length === 100 ? ' (pokazano pierwsze 100)' : ''}.
      </p>

      <div className="space-y-3">
        {results.map((item) => {
          const level = scoreImportance(item);
          return (
            <a
              key={`${item._tileLabel}-${item.id}`}
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-3 rounded-lg border border-slate-800 bg-slate-900/60 hover:border-blue-700/50 hover:bg-slate-800/60 transition-colors group"
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20">
                    {item._tileLabel}
                  </span>
                  <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${IMPORTANCE_STYLES[level]}`}>
                    {IMPORTANCE_LABELS[level]}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 shrink-0">{formatToPolishFormat(item.date)}</span>
              </div>
              <h3 className="text-sm font-semibold text-blue-100 leading-tight mb-1 group-hover:text-blue-400 transition-colors">
                {item.title}
              </h3>
              {item.summary && (
                <p className="text-xs text-slate-400 line-clamp-2 mb-1.5">
                  {cleanSummary(item.summary, item.title)}
                </p>
              )}
              <span className="text-[10px] text-slate-500 font-medium">{item.source || 'MEDINT'}</span>
            </a>
          );
        })}
        {results.length === 0 && (
          <p className="text-slate-500 text-center mt-10 text-sm">
            Brak wyników dla podanych kryteriów.
          </p>
        )}
      </div>
    </div>
  );
};

export default SearchView;
