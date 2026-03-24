/* ── Politia API Client ── */

import type {
  PoliticianProfile,
  SearchResponse,
  LeaderboardResponse,
  FiltersResponse,
  CompareResponse,
} from '@/types';

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { next: { revalidate: 300 } });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${path}`);
  }
  return res.json() as Promise<T>;
}

/* Client-side fetch (no caching directives) */
async function clientGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${path}`);
  }
  return res.json() as Promise<T>;
}

/* ── Endpoints ── */

export function searchPoliticians(params: {
  q?: string;
  state?: string;
  party?: string;
  chamber?: string;
  offset?: number;
  limit?: number;
}): Promise<SearchResponse> {
  const sp = new URLSearchParams();
  if (params.q) sp.set('q', params.q);
  if (params.state) sp.set('state', params.state);
  if (params.party) sp.set('party', params.party);
  if (params.chamber) sp.set('chamber', params.chamber);
  sp.set('offset', String(params.offset ?? 0));
  sp.set('limit', String(params.limit ?? 20));
  return get<SearchResponse>(`/api/politicians?${sp}`);
}

export function getPolitician(id: number | string): Promise<PoliticianProfile> {
  return get<PoliticianProfile>(`/api/politicians/${id}`);
}

export function getFilters(): Promise<FiltersResponse> {
  return get<FiltersResponse>('/api/politicians/filters');
}

export function getLeaderboard(params?: {
  chamber?: string;
  state?: string;
  party?: string;
  sort_by?: string;
  offset?: number;
  limit?: number;
}): Promise<LeaderboardResponse> {
  const sp = new URLSearchParams();
  if (params?.chamber) sp.set('chamber', params.chamber);
  if (params?.state) sp.set('state', params.state);
  if (params?.party) sp.set('party', params.party);
  if (params?.sort_by) sp.set('sort_by', params.sort_by);
  sp.set('offset', String(params?.offset ?? 0));
  sp.set('limit', String(params?.limit ?? 20));
  return get<LeaderboardResponse>(`/api/leaderboards?${sp}`);
}

export function comparePoliticians(ids: number[]): Promise<CompareResponse> {
  return clientGet<CompareResponse>(`/api/compare?${ids.map(id => `politician_ids=${id}`).join('&')}`);
}

export async function comparePoliticiansPost(ids: number[]): Promise<CompareResponse> {
  const res = await fetch(`${BASE}/api/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ politician_ids: ids }),
  });
  if (!res.ok) throw new Error(`API ${res.status}: /api/compare`);
  return res.json();
}

/* Re-export for client components that need BASE */
export const API_BASE = BASE;
