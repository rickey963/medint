import React from 'react';
import { formatToPolishFormat } from '../utils/dateUtils';

/**
 * Single, consistent date pill rendered in the top-right corner of every card.
 * Format is always "DD.MM.YYYY g. HH:MM" in Europe/Warsaw.
 */
const DateBadge = ({ date, className = '' }) => {
  const label = formatToPolishFormat(date);
  return (
    <span
      className={
        'text-[10px] font-bold uppercase text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700 whitespace-nowrap ' +
        className
      }
    >
      {label || 'Brak daty'}
    </span>
  );
};

export default DateBadge;
