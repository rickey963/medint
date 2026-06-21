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
  return out;
};
