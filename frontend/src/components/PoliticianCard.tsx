import Link from 'next/link';
import ScoreBadge from './ScoreBadge';

interface CardPolitician {
  id: number;
  full_name: string;
  party: string;
  state: string;
  constituency?: string;
  photo_url?: string | null;
  score?: number | null;
}

export default function PoliticianCard({
  politician,
  rank,
}: {
  politician: CardPolitician;
  rank?: number;
}) {
  const p = politician;
  return (
    <Link href={`/politician/${p.id}`} className="card-link">
      <div className="card" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        {rank != null && (
          <span
            style={{
              fontSize: '0.8125rem',
              fontWeight: 700,
              color: 'var(--text-muted)',
              minWidth: '1.5rem',
              textAlign: 'center',
            }}
          >
            {rank}
          </span>
        )}
        <div
          style={{
            width: '44px',
            height: '44px',
            borderRadius: '50%',
            background: 'var(--bg-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            fontSize: '1.125rem',
            color: 'var(--text-muted)',
            overflow: 'hidden',
          }}
        >
          {p.photo_url ? (
            <img
              src={p.photo_url}
              alt=""
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          ) : (
            p.full_name?.charAt(0) || '?'
          )}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: '0.9375rem', lineHeight: 1.3 }}>
            {p.full_name}
          </div>
          <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.125rem' }}>
            {p.party} · {p.state}
            {p.constituency ? ` · ${p.constituency}` : ''}
          </div>
        </div>
        <ScoreBadge score={p.score} />
      </div>
    </Link>
  );
}
