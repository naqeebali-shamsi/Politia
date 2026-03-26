'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import PoliticianCard from './PoliticianCard';
import type { PoliticianSummary, LeaderboardEntry } from '@/types';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function HomeContent() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<PoliticianSummary[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const wrapperRef = useRef<HTMLDivElement>(null);

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

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    try {
      const res = await fetch(`${API}/api/politicians?q=${encodeURIComponent(q)}&limit=6`);
      if (!res.ok) return;
      const data = await res.json();
      setSuggestions(data.results || []);
      setShowSuggestions((data.results || []).length > 0);
      setActiveIndex(-1);
    } catch {
      // Silently fail — autocomplete is a nice-to-have
    }
  }, []);

  const handleInputChange = (value: string) => {
    setQuery(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(value), 250);
  };

  const handleSelect = (politician: PoliticianSummary) => {
    setShowSuggestions(false);
    setQuery('');
    router.push(`/politician/${politician.id}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault();
      handleSelect(suggestions[activeIndex]);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setShowSuggestions(false);
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <>
      {/* Search */}
      <form onSubmit={handleSearch} style={{ maxWidth: '600px', margin: '0 auto 2rem' }}>
        <div ref={wrapperRef} className="search-autocomplete">
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="text"
              placeholder="Search by MP name, constituency, or state..."
              value={query}
              onChange={(e) => handleInputChange(e.target.value)}
              onFocus={() => { if (suggestions.length > 0) setShowSuggestions(true); }}
              onKeyDown={handleKeyDown}
              autoComplete="off"
              role="combobox"
              aria-expanded={showSuggestions}
              aria-autocomplete="list"
              aria-controls="search-suggestions"
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
          {showSuggestions && suggestions.length > 0 && (
            <ul id="search-suggestions" className="search-dropdown" role="listbox">
              {suggestions.map((p, i) => (
                <li
                  key={p.id}
                  role="option"
                  aria-selected={i === activeIndex}
                  className={`search-dropdown-item${i === activeIndex ? ' search-dropdown-item-active' : ''}`}
                  onMouseDown={() => handleSelect(p)}
                  onMouseEnter={() => setActiveIndex(i)}
                >
                  <div className="search-dropdown-name">{p.full_name}</div>
                  <div className="search-dropdown-meta">
                    {p.party}{p.state ? ` · ${p.state}` : ''}{p.constituency ? ` · ${p.constituency}` : ''}
                  </div>
                </li>
              ))}
              <li
                className="search-dropdown-footer"
                onMouseDown={() => { setShowSuggestions(false); router.push(`/search?q=${encodeURIComponent(query.trim())}`); }}
              >
                View all results for &ldquo;{query.trim()}&rdquo;
              </li>
            </ul>
          )}
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
