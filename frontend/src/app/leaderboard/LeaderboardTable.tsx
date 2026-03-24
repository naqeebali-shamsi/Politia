'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import type { LeaderboardEntry } from '@/types';
import ScoreBadge from '@/components/ScoreBadge';
import { fmtScore, scoreColor } from '@/lib/utils';

export default function LeaderboardTable({
  entries,
  states,
  parties,
  currentChamber,
  currentState,
  currentParty,
  currentSort,
  page,
  totalPages,
}: {
  entries: LeaderboardEntry[];
  states: string[];
  parties: string[];
  currentChamber: string;
  currentState: string;
  currentParty: string;
  currentSort: string;
  page: number;
  totalPages: number;
}) {
  const router = useRouter();
  const [chamber, setChamber] = useState(currentChamber);
  const [state, setState] = useState(currentState);
  const [party, setParty] = useState(currentParty);

  function buildUrl(overrides: Record<string, string> = {}) {
    const sp = new URLSearchParams();
    const c = overrides.chamber ?? chamber;
    const s = overrides.state ?? state;
    const p = overrides.party ?? party;
    const sort = overrides.sort_by ?? currentSort;
    const pg = overrides.page ?? String(page);
    if (c) sp.set('chamber', c);
    if (s) sp.set('state', s);
    if (p) sp.set('party', p);
    if (sort && sort !== 'overall_score') sp.set('sort_by', sort);
    if (pg !== '1') sp.set('page', pg);
    return `/leaderboard?${sp}`;
  }

  function applyFilters() {
    router.push(buildUrl({ page: '1' }));
  }

  function sortBy(col: string) {
    router.push(buildUrl({ sort_by: col, page: '1' }));
  }

  return (
    <div>
      {/* Filters */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
        <select
          className="select"
          value={chamber}
          onChange={(e) => setChamber(e.target.value)}
          aria-label="Chamber"
        >
          <option value="">All Chambers</option>
          <option value="Lok Sabha">Lok Sabha</option>
          <option value="Rajya Sabha">Rajya Sabha</option>
        </select>
        <select
          className="select"
          value={state}
          onChange={(e) => setState(e.target.value)}
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
          onChange={(e) => setParty(e.target.value)}
          aria-label="Party"
        >
          <option value="">All Parties</option>
          {parties.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <button className="btn btn-primary btn-sm" onClick={applyFilters}>
          Apply
        </button>
      </div>

      {/* Table */}
      {entries.length === 0 ? (
        <p className="empty-state">No results match your filters.</p>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: '3rem' }}>#</th>
                <th>Name</th>
                <th className="hide-mobile">Party</th>
                <th className="hide-mobile">State</th>
                <th className="hide-mobile">Constituency</th>
                <th
                  className="sortable"
                  onClick={() => sortBy('overall_score')}
                  style={{ textAlign: 'right' }}
                >
                  Overall {currentSort === 'overall_score' ? '\u25BC' : ''}
                </th>
                <th
                  className="sortable hide-mobile"
                  onClick={() => sortBy('participation_score')}
                  style={{ textAlign: 'right' }}
                >
                  Participation {currentSort === 'participation_score' ? '\u25BC' : ''}
                </th>
                <th
                  className="sortable hide-mobile"
                  onClick={() => sortBy('disclosure_score')}
                  style={{ textAlign: 'right' }}
                >
                  Disclosure {currentSort === 'disclosure_score' ? '\u25BC' : ''}
                </th>
                <th className="hide-mobile" style={{ textAlign: 'right' }}>
                  Risk
                </th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id}>
                  <td style={{ fontWeight: 600, color: 'var(--text-muted)' }}>{e.rank}</td>
                  <td>
                    <Link
                      href={`/politician/${e.id}`}
                      style={{ fontWeight: 500 }}
                    >
                      {e.full_name}
                    </Link>
                  </td>
                  <td className="hide-mobile">{e.party}</td>
                  <td className="hide-mobile">{e.state}</td>
                  <td className="hide-mobile">{e.constituency}</td>
                  <td style={{ textAlign: 'right' }}>
                    <ScoreBadge score={e.score} />
                  </td>
                  <td className="hide-mobile" style={{ textAlign: 'right', color: scoreColor(e.participation_score) }}>
                    {fmtScore(e.participation_score)}
                  </td>
                  <td className="hide-mobile" style={{ textAlign: 'right', color: scoreColor(e.disclosure_score) }}>
                    {fmtScore(e.disclosure_score)}
                  </td>
                  <td className="hide-mobile" style={{ textAlign: 'right', color: e.integrity_risk_adjustment ? 'var(--red)' : 'var(--text-muted)' }}>
                    {e.integrity_risk_adjustment ? `-${fmtScore(e.integrity_risk_adjustment)}` : '0.0'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          {page > 1 && (
            <Link href={buildUrl({ page: String(page - 1) })}>
              <button>Previous</button>
            </Link>
          )}
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', padding: '0 0.5rem' }}>
            Page {page} of {totalPages}
          </span>
          {page < totalPages && (
            <Link href={buildUrl({ page: String(page + 1) })}>
              <button>Next</button>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
