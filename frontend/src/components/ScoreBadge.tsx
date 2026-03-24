import { scoreClass, fmtScore } from '@/lib/utils';

export default function ScoreBadge({
  score,
  large,
}: {
  score: number | null | undefined;
  large?: boolean;
}) {
  const cls = `score-badge ${large ? 'score-badge-lg' : ''} ${scoreClass(score)}`;
  return <span className={cls}>{fmtScore(score)}</span>;
}
