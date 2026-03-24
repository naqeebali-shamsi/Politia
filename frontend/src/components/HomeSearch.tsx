'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function HomeSearch({
  states,
  parties,
}: {
  states: string[];
  parties: string[];
}) {
  const router = useRouter();
  const [q, setQ] = useState('');
  const [state, setState] = useState('');
  const [party, setParty] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (q.trim()) params.set('q', q.trim());
    if (state) params.set('state', state);
    if (party) params.set('party', party);
    router.push(`/search?${params}`);
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '600px', margin: '0 auto' }}>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <input
          className="input"
          type="text"
          placeholder="Search by name, constituency..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search politicians"
        />
        <button type="submit" className="btn btn-primary">
          Search
        </button>
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
        <select
          className="select"
          value={state}
          onChange={(e) => setState(e.target.value)}
          aria-label="Filter by state"
          style={{ flex: 1, maxWidth: '200px' }}
        >
          <option value="">All States</option>
          {states.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          className="select"
          value={party}
          onChange={(e) => setParty(e.target.value)}
          aria-label="Filter by party"
          style={{ flex: 1, maxWidth: '200px' }}
        >
          <option value="">All Parties</option>
          {parties.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>
    </form>
  );
}
