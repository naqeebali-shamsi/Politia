import { scoreColor, fmtScore } from '@/lib/utils';

export default function ScoreBar({
  label,
  score,
  max = 100,
}: {
  label: string;
  score: number | null | undefined;
  max?: number;
}) {
  const pct = score != null ? Math.min((score / max) * 100, 100) : 0;
  const color = scoreColor(score);

  return (
    <div style={{ marginBottom: '1rem' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: '0.375rem',
          fontSize: '0.875rem',
        }}
      >
        <span style={{ fontWeight: 500 }}>{label}</span>
        <span style={{ fontWeight: 600, color }}>{fmtScore(score)}</span>
      </div>
      <div className="score-bar-track">
        <div
          className="score-bar-fill"
          style={{
            width: `${pct}%`,
            background: color,
          }}
        />
      </div>
    </div>
  );
}
