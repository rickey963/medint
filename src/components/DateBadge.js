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
        'text-[10px] font-bold uppercase text-gray-500 bg-gray-50 px-2 py-0.5 rounded border border-gray-200 whitespace-nowrap ' +
        className
      }
    >
      {label || 'Brak daty'}
    </span>
  );
};

export default DateBadge;
