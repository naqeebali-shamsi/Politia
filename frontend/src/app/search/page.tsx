import Link from 'next/link';
import { searchPoliticians, getFilters } from '@/lib/api';
import PoliticianCard from '@/components/PoliticianCard';
import SearchControls from './SearchControls';

export const dynamic = 'force-dynamic';
export const maxDuration = 30;

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; state?: string; party?: string; page?: string }>;
}) {
  const params = await searchParams;
  const q = params.q ?? '';
  const state = params.state ?? '';
  const party = params.party ?? '';
  const page = Math.max(1, parseInt(params.page ?? '1', 10));
  const limit = 20;
  const offset = (page - 1) * limit;

  let results;
  let filters;
  try {
    [results, filters] = await Promise.all([
      searchPoliticians({ q, state, party, offset, limit }),
      getFilters(),
    ]);
  } catch {
    return (
      <div className="empty-state">
        <p>Unable to reach the API.</p>
      </div>
    );
  }

  const politicians = results?.results ?? [];
  const total = results?.total ?? 0;
  const totalPages = Math.ceil(total / limit);

  /* Build URL for a given page */
  function pageUrl(p: number): string {
    const sp = new URLSearchParams();
    if (q) sp.set('q', q);
    if (state) sp.set('state', state);
    if (party) sp.set('party', party);
    sp.set('page', String(p));
    return `/search?${sp}`;
  }

  return (
    <div>
      <div className="breadcrumb">
        <Link href="/">Home</Link>
        <span className="breadcrumb-sep">/</span>
        <span>Search</span>
      </div>

      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.25rem' }}>
        Search Results
      </h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
        {total} result{total !== 1 ? 's' : ''}
        {q ? ` for "${q}"` : ''}
        {state ? ` in ${state}` : ''}
        {party ? ` from ${party}` : ''}
      </p>

      <SearchControls
        q={q}
        state={state}
        party={party}
        states={filters?.states ?? []}
        parties={filters?.parties ?? []}
      />

      {politicians.length > 0 ? (
        <div className="grid-auto" style={{ marginTop: '1.5rem' }}>
          {politicians.map((p) => (
            <PoliticianCard key={p.id} politician={p} />
          ))}
        </div>
      ) : (
        <div className="empty-state" style={{ marginTop: '2rem' }}>
          <p>No politicians found matching your criteria.</p>
          <Link href="/" style={{ display: 'inline-block', marginTop: '0.75rem' }}>
            Back to home
          </Link>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          {page > 1 && (
            <Link href={pageUrl(page - 1)}>
              <button>Previous</button>
            </Link>
          )}
          {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
            let p: number;
            if (totalPages <= 7) {
              p = i + 1;
            } else if (page <= 4) {
              p = i + 1;
            } else if (page >= totalPages - 3) {
              p = totalPages - 6 + i;
            } else {
              p = page - 3 + i;
            }
            return (
              <Link key={p} href={pageUrl(p)}>
                <button className={p === page ? 'page-current' : ''}>
                  {p}
                </button>
              </Link>
            );
          })}
          {page < totalPages && (
            <Link href={pageUrl(page + 1)}>
              <button>Next</button>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
