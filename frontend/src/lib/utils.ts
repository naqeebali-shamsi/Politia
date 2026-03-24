/* ── Utility Functions ── */

/** Return the CSS class for a score value */
export function scoreClass(score: number | null | undefined): string {
  if (score == null) return 'score-na';
  if (score >= 60) return 'score-good';
  if (score >= 35) return 'score-mid';
  return 'score-low';
}

/** Return the CSS color variable for a score */
export function scoreColor(score: number | null | undefined): string {
  if (score == null) return 'var(--text-muted)';
  if (score >= 60) return 'var(--green)';
  if (score >= 35) return 'var(--orange)';
  return 'var(--red)';
}

/** Format a number with commas (Indian format for large numbers) */
export function formatNumber(n: number | null | undefined): string {
  if (n == null) return 'N/A';
  return n.toLocaleString('en-IN');
}

/** Format currency (INR) */
export function formatINR(n: number | null | undefined): string {
  if (n == null) return 'N/A';
  if (n >= 1_00_00_000) return `${(n / 1_00_00_000).toFixed(2)} Cr`;
  if (n >= 1_00_000) return `${(n / 1_00_000).toFixed(2)} L`;
  return `${n.toLocaleString('en-IN')}`;
}

/** Format a score with one decimal */
export function fmtScore(score: number | null | undefined): string {
  if (score == null) return 'N/A';
  return score.toFixed(1);
}

/** Display a percentage */
export function fmtPct(n: number | null | undefined): string {
  if (n == null) return 'N/A';
  return `${n.toFixed(1)}%`;
}

/** Pretty-print a breakdown key */
export function breakdownLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}
