'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function SearchControls({
  q: initQ,
  state: initState,
  party: initParty,
  states,
  parties,
}: {
  q: string;
  state: string;
  party: string;
  states: string[];
  parties: string[];
}) {
  const router = useRouter();
  const [q, setQ] = useState(initQ);
  const [state, setState] = useState(initState);
  const [party, setParty] = useState(initParty);

  const apply = () => {
    const sp = new URLSearchParams();
    if (q.trim()) sp.set('q', q.trim());
    if (state) sp.set('state', state);
    if (party) sp.set('party', party);
    router.push(`/search?${sp}`);
  };

  return (
    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
      <input
        className="input"
        type="text"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && apply()}
        placeholder="Name, constituency..."
        aria-label="Search"
        style={{ flex: '1 1 200px', maxWidth: '300px' }}
      />
      <select
        className="select"
        value={state}
        onChange={(e) => { setState(e.target.value); }}
        aria-label="State"
      >
        <option value="">All States</option>
        {states.map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>
      <select
        className="select"
        value={party}
        onChange={(e) => { setParty(e.target.value); }}
        aria-label="Party"
      >
        <option value="">All Parties</option>
        {parties.map((p) => (
          <option key={p} value={p}>{p}</option>
        ))}
      </select>
      <button className="btn btn-primary" onClick={apply}>
        Apply
      </button>
    </div>
  );
}
