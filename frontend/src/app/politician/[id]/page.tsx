import Link from 'next/link';
import { getPolitician } from '@/lib/api';
import type { PoliticianProfile } from '@/types';
import ScoreBadge from '@/components/ScoreBadge';
import ScoreBar from '@/components/ScoreBar';
import ProfileTabs from './ProfileTabs';
import { fmtScore, scoreColor, breakdownLabel } from '@/lib/utils';

export default async function PoliticianPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let data: PoliticianProfile;
  try {
    data = await getPolitician(id);
  } catch {
    return (
      <div className="empty-state">
        <p>Politician not found or API unavailable.</p>
        <Link href="/" style={{ display: 'inline-block', marginTop: '0.75rem' }}>
          Back to home
        </Link>
      </div>
    );
  }

  if (!data || (data as any).detail) {
    return (
      <div className="empty-state">
        <p>Politician not found.</p>
        <Link href="/" style={{ display: 'inline-block', marginTop: '0.75rem' }}>
          Back to home
        </Link>
      </div>
    );
  }

  const s = data.scores;

  return (
    <div>
      {/* Breadcrumb */}
      <div className="breadcrumb">
        <Link href="/">Home</Link>
        <span className="breadcrumb-sep">/</span>
        <span>{data.full_name}</span>
      </div>

      {/* ── Header Card ── */}
      <div
        className="card"
        style={{
          display: 'flex',
          gap: '1.5rem',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          marginBottom: '1.5rem',
        }}
      >
        {/* Avatar */}
        <div
          style={{
            width: '80px',
            height: '80px',
            borderRadius: '50%',
            background: 'var(--bg-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '2rem',
            color: 'var(--text-muted)',
            flexShrink: 0,
            overflow: 'hidden',
          }}
        >
          {data.photo_url ? (
            <img
              src={data.photo_url}
              alt={data.full_name}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          ) : (
            data.full_name?.charAt(0) || '?'
          )}
        </div>

        {/* Info */}
        <div style={{ flex: 1, minWidth: '200px' }}>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, lineHeight: 1.2, marginBottom: '0.375rem' }}>
            {data.full_name}
          </h1>
          <div style={{ fontSize: '0.9375rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
            {data.party} &middot; {data.state} &middot; {data.chamber}
            {data.constituency ? ` &middot; ${data.constituency}` : ''}
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', fontSize: '0.8125rem' }}>
            {data.gender && (
              <span className="tag">{data.gender}</span>
            )}
            {data.education && (
              <span className="tag">{data.education}</span>
            )}
            {data.profession && (
              <span className="tag">{data.profession}</span>
            )}
            <span className={`tag ${data.is_active ? 'tag-active' : ''}`}>
              {data.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>

        {/* Overall Score */}
        <div style={{ textAlign: 'center', minWidth: '100px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.375rem' }}>
            Overall Score
          </div>
          <ScoreBadge score={s?.overall} large />
        </div>
      </div>

      {/* ── Score Breakdown ── */}
      <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
        {/* Participation */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600 }}>Participation</h3>
            <span style={{ fontWeight: 700, color: scoreColor(s?.participation) }}>
              {fmtScore(s?.participation)}
            </span>
          </div>
          <ScoreBar label="Score" score={s?.participation} />
          {s?.participation_breakdown && (
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-light)', paddingTop: '0.75rem', marginTop: '0.5rem' }}>
              <div style={{ fontWeight: 500, marginBottom: '0.375rem', color: 'var(--text)' }}>Breakdown</div>
              {Object.entries(s.participation_breakdown).map(([k, v]) => (
                v != null && (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.125rem 0' }}>
                    <span>{breakdownLabel(k)}</span>
                    <span style={{ fontWeight: 500 }}>{typeof v === 'number' ? v.toFixed(1) : v}</span>
                  </div>
                )
              ))}
            </div>
          )}
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            Based on attendance, questions asked, debates, and bills introduced.
          </p>
        </div>

        {/* Disclosure */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600 }}>Disclosure</h3>
            <span style={{ fontWeight: 700, color: scoreColor(s?.disclosure) }}>
              {fmtScore(s?.disclosure)}
            </span>
          </div>
          <ScoreBar label="Score" score={s?.disclosure} />
          {s?.disclosure_breakdown && (
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-light)', paddingTop: '0.75rem', marginTop: '0.5rem' }}>
              <div style={{ fontWeight: 500, marginBottom: '0.375rem', color: 'var(--text)' }}>Breakdown</div>
              {Object.entries(s.disclosure_breakdown).map(([k, v]) => (
                v != null && (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.125rem 0' }}>
                    <span>{breakdownLabel(k)}</span>
                    <span style={{ fontWeight: 500 }}>{typeof v === 'number' ? v.toFixed(1) : v}</span>
                  </div>
                )
              ))}
            </div>
          )}
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            Based on affidavit completeness, asset and liability declarations.
          </p>
        </div>

        {/* Integrity Risk */}
        <div className="card" style={{ borderColor: s?.integrity_risk ? 'var(--red-light)' : undefined }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600 }}>Integrity Risk</h3>
            <span style={{ fontWeight: 700, color: 'var(--red)' }}>
              -{fmtScore(s?.integrity_risk)}
            </span>
          </div>
          <ScoreBar label="Penalty" score={s?.integrity_risk} />
          {s?.integrity_breakdown && (
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-light)', paddingTop: '0.75rem', marginTop: '0.5rem' }}>
              <div style={{ fontWeight: 500, marginBottom: '0.375rem', color: 'var(--text)' }}>Breakdown</div>
              {Object.entries(s.integrity_breakdown).map(([k, v]) => (
                v != null && (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.125rem 0' }}>
                    <span>{breakdownLabel(k)}</span>
                    <span style={{ fontWeight: 500 }}>{typeof v === 'number' ? v.toFixed(1) : v}</span>
                  </div>
                )
              ))}
            </div>
          )}
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            Penalty based on self-declared criminal cases in election affidavits.
          </p>
        </div>
      </div>

      {/* ── Score Formula ── */}
      {s && (
        <div className="card" style={{ marginBottom: '1.5rem', fontSize: '0.8125rem' }}>
          <div style={{ fontWeight: 600, marginBottom: '0.375rem' }}>Score Formula</div>
          <code style={{ display: 'block', padding: '0.5rem 0.75rem', background: 'var(--bg-muted)', borderRadius: 'var(--radius)', color: 'var(--text-secondary)' }}>
            Overall = Participation ({fmtScore(s.participation)}) + Disclosure ({fmtScore(s.disclosure)}) - Integrity Risk ({fmtScore(s.integrity_risk)}) = {fmtScore(s.overall)}
          </code>
          <div style={{ marginTop: '0.5rem', color: 'var(--text-muted)' }}>
            {s.formula_version && <>Formula version: {s.formula_version}. </>}
            {s.computed_at && <>Last computed: {new Date(s.computed_at).toLocaleDateString('en-IN')}. </>}
            {data.last_updated && <>Data last updated: {new Date(data.last_updated).toLocaleDateString('en-IN')}.</>}
          </div>
        </div>
      )}

      {/* ── Tabbed Data ── */}
      <ProfileTabs
        activities={data.activities}
        disclosures={data.disclosures}
        elections={data.elections}
      />

      {/* ── Sources ── */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, marginBottom: '0.5rem' }}>
          Data Sources
        </h3>
        <ul style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', paddingLeft: '1.25rem', lineHeight: 1.8 }}>
          <li>Parliamentary attendance and activity data from Lok Sabha / Rajya Sabha official records</li>
          <li>Election affidavit data from Election Commission of India / MyNeta.info</li>
          <li>Criminal case declarations from candidate self-disclosure affidavits</li>
          <li>Asset and liability data from sworn affidavits filed during elections</li>
        </ul>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.75rem' }}>
          This data is compiled from publicly available official sources. It may
          be incomplete, delayed, or contain transcription errors. See the{' '}
          <Link href="/methodology">methodology page</Link> for details.
        </p>
      </div>
    </div>
  );
}
