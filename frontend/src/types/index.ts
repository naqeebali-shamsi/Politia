/* ── Politia Type Definitions ── */

export interface PoliticianSummary {
  id: number;
  full_name: string;
  party: string;
  state: string;
  chamber: string;
  constituency: string;
  photo_url: string | null;
  is_active: boolean;
  score: number | null;
}

/* Keep backward-compat alias used by existing pages */
export type Politician = PoliticianSummary;

export interface ParticipationBreakdown {
  attendance_score: number | null;
  questions_score: number | null;
  debates_score: number | null;
  bills_score: number | null;
  [key: string]: number | null | undefined;
}

export interface DisclosureBreakdown {
  affidavit_completeness: number | null;
  assets_declared: number | null;
  liabilities_declared: number | null;
  [key: string]: number | null | undefined;
}

export interface IntegrityBreakdown {
  criminal_cases_penalty: number | null;
  serious_cases_penalty: number | null;
  [key: string]: number | null | undefined;
}

export interface ScoreData {
  overall: number | null;
  participation: number | null;
  disclosure: number | null;
  integrity_risk: number | null;
  formula_version: string | null;
  computed_at: string | null;
  participation_breakdown: ParticipationBreakdown | null;
  disclosure_breakdown: DisclosureBreakdown | null;
  integrity_breakdown: IntegrityBreakdown | null;
}

export interface Activity {
  term_number: number | null;
  session_name: string | null;
  attendance_percentage: number | null;
  questions_asked: number | null;
  debates_participated: number | null;
  private_bills_introduced: number | null;
  committee_memberships: number | null;
}

export interface Disclosure {
  election_year: number;
  total_assets: number | null;
  movable_assets: number | null;
  immovable_assets: number | null;
  total_liabilities: number | null;
  criminal_cases: number | null;
  serious_criminal_cases: number | null;
  affidavit_complete: boolean | null;
}

export interface Election {
  election_year: number;
  party: string;
  result: string;
  votes: number | null;
  vote_share: number | null;
  margin: number | null;
}

export interface PoliticianProfile {
  id: number;
  full_name: string;
  party: string;
  state: string;
  chamber: string;
  constituency: string;
  photo_url: string | null;
  gender: string | null;
  education: string | null;
  profession: string | null;
  is_active: boolean;
  last_updated: string | null;
  scores: ScoreData | null;
  activities: Activity[];
  disclosures: Disclosure[];
  elections: Election[];
}

export interface LeaderboardEntry {
  rank: number;
  id: number;
  full_name: string;
  party: string;
  state: string;
  chamber: string;
  constituency: string;
  score: number | null;
  participation_score: number | null;
  disclosure_score: number | null;
  integrity_risk_adjustment: number | null;
}

export interface FiltersResponse {
  states: string[];
  parties: string[];
}

export interface SearchResponse {
  results: PoliticianSummary[];
  total: number;
  offset: number;
  limit: number;
}

export interface LeaderboardResponse {
  results: LeaderboardEntry[];
  total?: number;
  offset?: number;
  limit?: number;
}

export interface CompareResponse {
  politicians: PoliticianProfile[];
}
