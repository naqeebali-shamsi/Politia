import Link from 'next/link';
import { getLeaderboard, getFilters } from '@/lib/api';
import LeaderboardTable from './LeaderboardTable';

export default async function LeaderboardPage({
  searchParams,
}: {
  searchParams: Promise<{
    chamber?: string;
    state?: string;
    party?: string;
    sort_by?: string;
    page?: string;
  }>;
}) {
  const params = await searchParams;
  const chamber = params.chamber ?? '';
  const state = params.state ?? '';
  const party = params.party ?? '';
  const sortBy = params.sort_by ?? 'overall_score';
  const page = Math.max(1, parseInt(params.page ?? '1', 10));
  const limit = 30;
  const offset = (page - 1) * limit;

  let leaderboard;
  let filters;
  try {
    [leaderboard, filters] = await Promise.all([
      getLeaderboard({ chamber, state, party, sort_by: sortBy, offset, limit }),
      getFilters(),
    ]);
  } catch {
    return (
      <div className="empty-state">
        <p>Unable to reach the API.</p>
      </div>
    );
  }

  const entries = leaderboard?.results ?? [];
  const total = leaderboard?.total ?? entries.length;
  const totalPages = Math.ceil(total / limit);

  return (
    <div>
      <div className="breadcrumb">
        <Link href="/">Home</Link>
        <span className="breadcrumb-sep">/</span>
        <span>Leaderboard</span>
      </div>

      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.25rem' }}>
        MP Accountability Leaderboard
      </h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
        Ranked by composite accountability score. Higher is better.{' '}
        <Link href="/methodology" style={{ fontSize: '0.8125rem' }}>
          How scores work
        </Link>
      </p>

      <LeaderboardTable
        entries={entries}
        states={filters?.states ?? []}
        parties={filters?.parties ?? []}
        currentChamber={chamber}
        currentState={state}
        currentParty={party}
        currentSort={sortBy}
        page={page}
        totalPages={totalPages}
      />
    </div>
  );
}
