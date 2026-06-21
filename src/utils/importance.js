/**
 * Importance scoring (Critical/High/Medium/Low) and patient-group heuristics.
 *
 * Deliberately limited to signals we can compute honestly from structured fields
 * already set by scraper/classify.py (safety_level, study_type, is_update, category,
 * source) plus keyword matches on title/summary - no fabricated clinical judgement.
 */

const CRITICAL_SAFETY_HINTS = ['wycofanie', 'black box'];
const EPIDEMIC_THREAT_KEYWORDS = ['pandemi', 'outbreak', 'ognisko', 'epidemi'];
const TOP_JOURNAL_SOURCES = ['NEJM', 'The Lancet', 'JAMA', 'Nature Medicine', 'BMJ'];
const TOP_STUDY_TYPES = ['RCT', 'Meta-analiza', 'Systematic Review'];
const REGULATOR_SOURCES = ['FDA', 'EMA', 'WHO'];

const textOf = (item) => `${item?.title || ''} ${item?.summary || ''}`.toLowerCase();

/**
 * Returns 'Critical' | 'High' | 'Medium' | 'Low'.
 */
export const scoreImportance = (item) => {
  if (!item) return 'Low';
  const safety = String(item.safety_level || '').toLowerCase();
  const text = textOf(item);
  const source = item.source || '';

  if (CRITICAL_SAFETY_HINTS.some((kw) => safety.includes(kw))) return 'Critical';
  if (item.category === 'Epidemiologia' && EPIDEMIC_THREAT_KEYWORDS.some((kw) => text.includes(kw))) {
    return 'Critical';
  }

  const isRegulatorDecision =
    safety.includes('rejestracja') || safety.includes('alert') || REGULATOR_SOURCES.includes(source);
  const isGuidelineUpdate = item.is_update === true;
  const isTopJournalTrial =
    TOP_JOURNAL_SOURCES.includes(source) && TOP_STUDY_TYPES.includes(item.study_type);
  if (isRegulatorDecision || isGuidelineUpdate || isTopJournalTrial) return 'High';

  if (item.study_type || item.change_type || item.ai_category || item.category || item.phase) {
    return 'Medium';
  }

  return 'Low';
};

export const IMPORTANCE_STYLES = {
  Critical: 'bg-red-500/15 text-red-300 border-red-500/30',
  High: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  Medium: 'bg-blue-500/10 text-blue-300 border-blue-500/20',
  Low: 'bg-slate-800 text-slate-400 border-slate-700',
};

export const IMPORTANCE_LABELS = {
  Critical: 'Krytyczny',
  High: 'Wysoki',
  Medium: 'Średni',
  Low: 'Niski',
};

const PATIENT_GROUPS = [
  { label: 'Dzieci i młodzież', kws: ['pediatr', 'dzieci', 'dziecię', 'młodzież', 'noworod', 'niemowl'] },
  { label: 'Seniorzy', kws: ['geriatr', 'senior', 'osoby starsze', 'starszych', 'starszej'] },
  { label: 'Kobiety w ciąży', kws: ['ciąż', 'pregnan', 'położnic'] },
  { label: 'Pacjenci onkologiczni', kws: ['nowotwor', 'rak ', 'oncolog', 'cancer', 'onkolog'] },
  { label: 'Pacjenci kardiologiczni', kws: ['serc', 'cardio', 'kardio'] },
  { label: 'Pacjenci z cukrzycą', kws: ['cukrzyc', 'diabet'] },
];

/**
 * Returns a human-readable patient-group label, or null when none is detectable.
 */
export const detectPatientGroup = (item) => {
  const text = textOf(item);
  const hit = PATIENT_GROUPS.find(({ kws }) => kws.some((kw) => text.includes(kw)));
  return hit ? hit.label : null;
};
