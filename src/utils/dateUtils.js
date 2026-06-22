/**
 * Utility functions for date handling across the MEDINT dashboard.
 *
 * All dates on the UI must:
 *  - be displayed in Europe/Warsaw timezone,
 *  - use the canonical format:  `DD.MM.YYYY g. HH:MM`
 *  - be sorted / filtered in the JavaScript layer (frontend) using normalizeDateKey
 *    so we never depend on the source's date string shape.
 */

/**
 * Tries to parse any of the supported input formats into a valid Date.
 * Returns null if the value is empty / invalid.
 *
 * Accepted input shapes (and any RFC 2822 / ISO 8601 variant):
 *  - "YYYY-MM-DD HH:mm"   (scraper internal format)
 *  - "YYYY-MM-DDTHH:mm"   (ISO without seconds)
 *  - "Wed, 10 Jun 2026 12:58:46 +0000"   (RSS / RFC 2822)
 *  - "Recent"             (placeholder)  -> null
 *  - "" or null/undefined -> null
 */
export const parseAnyDate = (dateStr) => {
  if (!dateStr) return null;
  if (dateStr === 'Recent') return null;

  const trimmed = String(dateStr).trim();
  if (!trimmed) return null;

  // Fast-path: the "YYYY-MM-DD HH:mm" scraper format. Replace space with T
  // so the JS Date constructor interprets it as local-UTC, then we force UTC.
  let isoCandidate = trimmed;
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?$/.test(trimmed)) {
    isoCandidate = trimmed.replace(' ', 'T');
  }

  // The native Date constructor handles ISO 8601 and RFC 2822 reasonably well.
  const parsed = new Date(isoCandidate);
  if (!isNaN(parsed.getTime())) {
    return parsed;
  }

  // Last-resort fallback for non-standard strings.
  return null;
};

/**
 * Canonical formatter.  Always returns "DD.MM.YYYY g. HH:MM" in Europe/Warsaw.
 * Returns "" for invalid / missing input.
 */
export const formatToPolishFormat = (dateStr) => {
  const parsed = parseAnyDate(dateStr);
  if (!parsed) return '';

  const parts = new Intl.DateTimeFormat('pl-PL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Europe/Warsaw',
    hour12: false,
  }).formatToParts(parsed);

  const get = (type) => (parts.find((p) => p.type === type) || {}).value || '';
  const day = get('day');
  const month = get('month');
  const year = get('year');
  const hour = get('hour');
  const minute = get('minute');

  if (!day || !month || !year || !hour || !minute) return '';
  return `${day}.${month}.${year} g. ${hour}:${minute}`;
};

/**
 * Returns a normalized Date for sorting / filtering.  Returns null when invalid.
 */
export const normalizeDateKey = (dateStr) => parseAnyDate(dateStr);

/**
 * Returns true if the date is within the last `windowDays` days from `referenceDate`
 * AND is not in the future.  Defaults to a 7-day window.
 */
export const isRecent = (dateStr, referenceDate = new Date(), windowDays = 7) => {
  const parsed = parseAnyDate(dateStr);
  if (!parsed) return false;

  const diff = referenceDate.getTime() - parsed.getTime();
  const windowMs = windowDays * 24 * 60 * 60 * 1000;
  return diff >= 0 && diff <= windowMs;
};

/**
 * Number of full days between the given date and `referenceDate`.  Returns Infinity
 * for invalid input so the value sorts to the end of the list.
 */
export const ageInDays = (dateStr, referenceDate = new Date()) => {
  const parsed = parseAnyDate(dateStr);
  if (!parsed) return Infinity;
  return (referenceDate.getTime() - parsed.getTime()) / (1000 * 60 * 60 * 24);
};

/**
 * True if the item was published within the last 60 minutes - used to give the
 * very newest cards a subtle highlight so they stand out from the rest of the tile.
 */
export const isWithinLastHour = (dateStr, referenceDate = new Date()) => {
  const parsed = parseAnyDate(dateStr);
  if (!parsed) return false;
  const diff = referenceDate.getTime() - parsed.getTime();
  return diff >= 0 && diff <= 60 * 60 * 1000;
};

/**
 * True if the date falls on the same Europe/Warsaw calendar day as
 * `referenceDate` (today by default). Used for the "Article of the day" pick,
 * which must reset at local midnight rather than drift on a rolling 24h/7d
 * window - otherwise a high-prestige item from yesterday can keep winning
 * over everything published today.
 */
const warsawDayKey = (date) =>
  new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Warsaw' }).format(date);

export const isToday = (dateStr, referenceDate = new Date()) => {
  const parsed = parseAnyDate(dateStr);
  if (!parsed) return false;
  if (parsed.getTime() > referenceDate.getTime()) return false;
  return warsawDayKey(parsed) === warsawDayKey(referenceDate);
};

/**
 * Stable id derived from the title + url.  Used for React keys so that updates
 * with the same content don't re-mount cards.
 */
export const makeStableId = (item) => {
  const base = `${item?.title || ''}::${item?.url || ''}`;
  // Simple non-crypto hash - we just need determinism, not security.
  let h = 0;
  for (let i = 0; i < base.length; i += 1) {
    h = (h << 5) - h + base.charCodeAt(i);
    h |= 0;
  }
  return `i_${h}`;
};
