'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { PoliticianProfile, PoliticianSummary } from '@/types';
import ScoreBadge from '@/components/ScoreBadge';
import ScoreBar from '@/components/ScoreBar';
import { fmtScore, formatINR, fmtPct, scoreColor } from '@/lib/utils';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function CompareClient({ initialIds }: { initialIds: number[] }) {
  const router = useRouter();
  const [ids, setIds] = useState<number[]>(initialIds);
  const [politicians, setPoliticians] = useState<PoliticianProfile[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<PoliticianSummary[]>([]);
  const [searchOpen, setSearchOpen] = useState(false);

  /* Fetch comparison data */
  useEffect(() => {
    if (ids.length === 0) {
      setPoliticians([]);
      return;
    }
    setLoading(true);
    fetch(`${API_URL}/api/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ politician_ids: ids }),
    })
      .then((r) => r.json())
      .then((data) => {
        setPoliticians(data.politicians || []);
      })
      .catch(() => setPoliticians([]))
      .finally(() => setLoading(false));
  }, [ids]);

  /* Search */
  useEffect(() => {
    if (searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(() => {
      fetch(`${API_URL}/api/politicians?q=${encodeURIComponent(searchQuery)}&limit=8`)
        .then((r) => r.json())
        .then((data) => setSearchResults(data.results || []))
        .catch(() => setSearchResults([]));
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  function addPolitician(id: number) {
    if (ids.includes(id) || ids.length >= 3) return;
    const next = [...ids, id];
    setIds(next);
    setSearchQuery('');
    setSearchResults([]);
    setSearchOpen(false);
    router.replace(`/compare?ids=${next.join(',')}`);
  }

  function removePolitician(id: number) {
    const next = ids.filter((i) => i !== id);
    setIds(next);
    router.replace(next.length ? `/compare?ids=${next.join(',')}` : '/compare');
  }

  return (
    <div>
      {/* Search to add */}
      {ids.length < 3 && (
        <div style={{ marginBottom: '2rem', position: 'relative', maxWidth: '400px' }}>
          <input
            className="input"
            type="text"
            placeholder="Search to add an MP..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setSearchOpen(true);
            }}
            onFocus={() => setSearchOpen(true)}
            aria-label="Search to add politician"
          />
          {searchOpen && searchResults.length > 0 && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                background: 'var(--bg-white)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius)',
                boxShadow: 'var(--shadow-lg)',
                zIndex: 50,
                maxHeight: '300px',
                overflow: 'auto',
              }}
            >
              {searchResults.map((p) => (
                <button
                  key={p.id}
                  onClick={() => addPolitician(p.id)}
                  disabled={ids.includes(p.id)}
                  style={{
                    display: 'block',
                    width: '100%',
                    padding: '0.625rem 0.875rem',
                    border: 'none',
                    background: ids.includes(p.id) ? 'var(--bg-muted)' : 'transparent',
                    textAlign: 'left',
                    fontSize: '0.875rem',
                    cursor: ids.includes(p.id) ? 'default' : 'pointer',
                    borderBottom: '1px solid var(--border-light)',
                  }}
                >
                  <span style={{ fontWeight: 500 }}>{p.full_name}</span>
                  <span style={{ color: 'var(--text-secondary)', marginLeft: '0.5rem' }}>
                    {p.party} &middot; {p.state}
                  </span>
                  {ids.includes(p.id) && (
                    <span style={{ color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                      (already added)
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="loading">
          <div className="loading-spinner" />
          <p>Loading comparison...</p>
        </div>
      )}

      {/* Empty state */}
      {!loading && ids.length === 0 && (
        <div className="empty-state">
          <p>Search and add MPs above to compare them side by side.</p>
        </div>
      )}

      {/* Comparison cards */}
      {!loading && politicians.length > 0 && (
        <div>
          {/* Score overview row */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: `repeat(${politicians.length}, 1fr)`,
              gap: '1rem',
              marginBottom: '1.5rem',
            }}
          >
            {politicians.map((p) => (
              <div key={p.id} className="card" style={{ textAlign: 'center' }}>
                <button
                  onClick={() => removePolitician(p.id)}
                  style={{
                    position: 'absolute',
                    top: '0.5rem',
                    right: '0.75rem',
                    background: 'none',
                    border: 'none',
                    fontSize: '1.25rem',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    lineHeight: 1,
                  }}
                  aria-label={`Remove ${p.full_name}`}
                  title="Remove"
                >
                  &times;
                </button>
                <div
                  style={{
                    width: '56px',
                    height: '56px',
                    borderRadius: '50%',
                    background: 'var(--bg-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 0.75rem',
                    fontSize: '1.5rem',
                    color: 'var(--text-muted)',
                    position: 'relative',
                  }}
                >
                  {p.full_name?.charAt(0) || '?'}
                </div>
                <Link
                  href={`/politician/${p.id}`}
                  style={{ fontWeight: 600, fontSize: '1rem' }}
                >
                  {p.full_name}
                </Link>
                <div
                  style={{
                    fontSize: '0.8125rem',
                    color: 'var(--text-secondary)',
                    marginTop: '0.25rem',
                    marginBottom: '0.75rem',
                  }}
                >
                  {p.party} &middot; {p.state}
                </div>
                <ScoreBadge score={p.scores?.overall} large />
              </div>
            ))}
          </div>

          {/* Score comparison */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, marginBottom: '1rem' }}>
              Score Comparison
            </h3>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: `repeat(${politicians.length}, 1fr)`,
                gap: '1.5rem',
              }}
            >
              {politicians.map((p) => (
                <div key={p.id}>
                  <div style={{ fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.75rem' }}>
                    {p.full_name}
                  </div>
                  <ScoreBar label="Participation" score={p.scores?.participation} />
                  <ScoreBar label="Disclosure" score={p.scores?.disclosure} />
                  <div style={{ marginBottom: '0.5rem' }}>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        fontSize: '0.875rem',
                        marginBottom: '0.375rem',
                      }}
                    >
                      <span style={{ fontWeight: 500 }}>Integrity Risk</span>
                      <span style={{ fontWeight: 600, color: 'var(--red)' }}>
                        -{fmtScore(p.scores?.integrity_risk)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Key facts */}
          <div className="card">
            <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, marginBottom: '1rem' }}>
              Key Facts
            </h3>
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>Metric</th>
                    {politicians.map((p) => (
                      <th key={p.id}>{p.full_name}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Chamber</td>
                    {politicians.map((p) => <td key={p.id}>{p.chamber}</td>)}
                  </tr>
                  <tr>
                    <td>Constituency</td>
                    {politicians.map((p) => <td key={p.id}>{p.constituency || 'N/A'}</td>)}
                  </tr>
                  <tr>
                    <td>Education</td>
                    {politicians.map((p) => <td key={p.id}>{p.education || 'N/A'}</td>)}
                  </tr>
                  <tr>
                    <td>Criminal Cases (latest)</td>
                    {politicians.map((p) => {
                      const latest = p.disclosures?.sort(
                        (a, b) => b.election_year - a.election_year
                      )[0];
                      return (
                        <td key={p.id} style={{ color: latest?.criminal_cases ? 'var(--red)' : undefined, fontWeight: latest?.criminal_cases ? 600 : undefined }}>
                          {latest?.criminal_cases ?? 'N/A'}
                        </td>
                      );
                    })}
                  </tr>
                  <tr>
                    <td>Total Assets (latest)</td>
                    {politicians.map((p) => {
                      const latest = p.disclosures?.sort(
                        (a, b) => b.election_year - a.election_year
                      )[0];
                      return <td key={p.id}>{formatINR(latest?.total_assets)}</td>;
                    })}
                  </tr>
                  <tr>
                    <td>Elections Contested</td>
                    {politicians.map((p) => (
                      <td key={p.id}>{p.elections?.length ?? 'N/A'}</td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
