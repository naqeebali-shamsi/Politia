'use client';

import { useState } from 'react';
import type { Activity, Disclosure, Election } from '@/types';
import { formatINR, formatNumber, fmtPct } from '@/lib/utils';

type Tab = 'activity' | 'disclosure' | 'elections';

export default function ProfileTabs({
  activities,
  disclosures,
  elections,
}: {
  activities: Activity[];
  disclosures: Disclosure[];
  elections: Election[];
}) {
  const [tab, setTab] = useState<Tab>('activity');

  return (
    <div>
      <div className="tabs">
        <button
          className={`tab ${tab === 'activity' ? 'tab-active' : ''}`}
          onClick={() => setTab('activity')}
        >
          Parliamentary Activity ({activities.length})
        </button>
        <button
          className={`tab ${tab === 'disclosure' ? 'tab-active' : ''}`}
          onClick={() => setTab('disclosure')}
        >
          Financial Disclosures ({disclosures.length})
        </button>
        <button
          className={`tab ${tab === 'elections' ? 'tab-active' : ''}`}
          onClick={() => setTab('elections')}
        >
          Election History ({elections.length})
        </button>
      </div>

      {tab === 'activity' && <ActivityTable data={activities} />}
      {tab === 'disclosure' && <DisclosureTable data={disclosures} />}
      {tab === 'elections' && <ElectionTable data={elections} />}
    </div>
  );
}

function ActivityTable({ data }: { data: Activity[] }) {
  if (data.length === 0)
    return <p className="empty-state">No parliamentary activity data available.</p>;

  return (
    <div className="table-wrapper">
      <table className="table">
        <thead>
          <tr>
            <th>Term</th>
            <th>Session</th>
            <th>Attendance</th>
            <th>Questions</th>
            <th>Debates</th>
            <th>Bills</th>
            <th>Committees</th>
          </tr>
        </thead>
        <tbody>
          {data.map((a, i) => (
            <tr key={i}>
              <td>{a.term_number ?? 'N/A'}</td>
              <td>{a.session_name ?? 'N/A'}</td>
              <td>{fmtPct(a.attendance_percentage)}</td>
              <td>{a.questions_asked ?? 'N/A'}</td>
              <td>{a.debates_participated ?? 'N/A'}</td>
              <td>{a.private_bills_introduced ?? 'N/A'}</td>
              <td>{a.committee_memberships ?? 'N/A'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DisclosureTable({ data }: { data: Disclosure[] }) {
  if (data.length === 0)
    return <p className="empty-state">No financial disclosure data available.</p>;

  const sorted = [...data].sort((a, b) => b.election_year - a.election_year);

  return (
    <div className="table-wrapper">
      <table className="table">
        <thead>
          <tr>
            <th>Year</th>
            <th>Total Assets</th>
            <th>Movable</th>
            <th>Immovable</th>
            <th>Liabilities</th>
            <th>Criminal Cases</th>
            <th>Serious Cases</th>
            <th>Affidavit</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((d) => (
            <tr key={d.election_year}>
              <td style={{ fontWeight: 500 }}>{d.election_year}</td>
              <td>{formatINR(d.total_assets)}</td>
              <td>{formatINR(d.movable_assets)}</td>
              <td>{formatINR(d.immovable_assets)}</td>
              <td>{formatINR(d.total_liabilities)}</td>
              <td>
                {d.criminal_cases != null ? (
                  <span style={{ color: d.criminal_cases > 0 ? 'var(--red)' : undefined, fontWeight: d.criminal_cases > 0 ? 600 : undefined }}>
                    {d.criminal_cases}
                  </span>
                ) : 'N/A'}
              </td>
              <td>
                {d.serious_criminal_cases != null ? (
                  <span style={{ color: d.serious_criminal_cases > 0 ? 'var(--red)' : undefined, fontWeight: d.serious_criminal_cases > 0 ? 600 : undefined }}>
                    {d.serious_criminal_cases}
                  </span>
                ) : 'N/A'}
              </td>
              <td>
                {d.affidavit_complete == null
                  ? 'N/A'
                  : d.affidavit_complete
                    ? <span style={{ color: 'var(--green)' }}>Complete</span>
                    : <span style={{ color: 'var(--orange)' }}>Incomplete</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ElectionTable({ data }: { data: Election[] }) {
  if (data.length === 0)
    return <p className="empty-state">No election history data available.</p>;

  const sorted = [...data].sort((a, b) => b.election_year - a.election_year);

  return (
    <div className="table-wrapper">
      <table className="table">
        <thead>
          <tr>
            <th>Year</th>
            <th>Party</th>
            <th>Result</th>
            <th>Votes</th>
            <th>Vote Share</th>
            <th>Margin</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((e, i) => (
            <tr key={i}>
              <td style={{ fontWeight: 500 }}>{e.election_year}</td>
              <td>{e.party}</td>
              <td>
                <span className={`tag ${e.result?.toLowerCase() === 'won' ? 'tag-won' : e.result?.toLowerCase() === 'lost' ? 'tag-lost' : ''}`}>
                  {e.result || 'N/A'}
                </span>
              </td>
              <td>{formatNumber(e.votes)}</td>
              <td>{e.vote_share != null ? `${e.vote_share.toFixed(1)}%` : 'N/A'}</td>
              <td>{e.margin != null ? formatNumber(e.margin) : 'N/A'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
