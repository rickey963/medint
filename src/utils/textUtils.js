/**
 * Returns a clean summary that does NOT duplicate the title.
 * The first 50 chars of `summary` are compared against the title (case-insensitive);
 * if they look like a duplicate they are stripped.
 */
export const cleanSummary = (summary, title) => {
  if (!summary) return '';
  let out = String(summary).trim();
  if (!title) return out;
  const t = String(title).toLowerCase().trim();
  const head = out.toLowerCase().slice(0, 50);
  if (head.startsWith(t)) {
    out = out.slice(t.length).replace(/^[\s\-,–—:.;]+/, '').trim();
  }

  // Google News RSS often has no real excerpt, just "<title>  <outlet>" as the
  // description. If what's left carries no information beyond the title itself,
  // don't show a redundant near-duplicate line under the headline.
  const normalize = (s) => new Set(s.toLowerCase().replace(/[^\w\s]/g, ' ').split(/\s+/).filter(Boolean));
  const titleWords = normalize(t);
  const summaryWords = normalize(out);
  if (summaryWords.size === 0) return '';
  let overlap = 0;
  summaryWords.forEach((w) => {
    if (titleWords.has(w)) overlap += 1;
  });
  if (overlap / summaryWords.size > 0.8) return '';

  return out;
};
