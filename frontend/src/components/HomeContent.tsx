'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import PoliticianCard from './PoliticianCard';
import type { LeaderboardEntry } from '@/types';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function HomeContent() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const res = await fetch(`${API}/api/leaderboards?limit=10`);
        if (!res.ok) throw new Error(`API ${res.status}`);
        const data = await res.json();
        if (!cancelled) {
          setLeaderboard(data.results || []);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError('Backend is waking up — free-tier servers sleep after inactivity. Retrying...');
          // Auto-retry after 5 seconds (Render cold start)
          setTimeout(() => {
            if (!cancelled) {
              setError(null);
              load();
            }
          }, 5000);
        }
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <>
      {/* Search */}
      <form onSubmit={handleSearch} style={{ maxWidth: '600px', margin: '0 auto 2rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            type="text"
            placeholder="Search by MP name, constituency, or state..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{
              flex: 1, padding: '0.75rem 1rem', border: '1px solid var(--border)',
              borderRadius: '6px', fontSize: '0.9375rem', background: 'var(--bg)',
            }}
          />
          <button
            type="submit"
            style={{
              padding: '0.75rem 1.5rem', background: 'var(--text)', color: 'var(--bg)',
              border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer',
            }}
          >
            Search
          </button>
        </div>
      </form>

      {/* Leaderboard */}
      <section style={{ marginTop: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Top Ranked MPs</h2>
          <Link href="/leaderboard" style={{ fontSize: '0.8125rem', fontWeight: 500 }}>
            View full leaderboard
          </Link>
        </div>

        {loading && !error && (
          <p className="empty-state">Loading leaderboard...</p>
        )}

        {error && (
          <div className="empty-state">
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && (
          <div className="grid-auto">
            {leaderboard.map((p, i) => (
              <PoliticianCard key={p.id} politician={p} rank={p.rank ?? i + 1} />
            ))}
          </div>
        )}

        {!loading && !error && leaderboard.length === 0 && (
          <p className="empty-state">No leaderboard data available yet.</p>
        )}
      </section>
    </>
  );
}
