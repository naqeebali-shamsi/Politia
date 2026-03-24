# MVP PRD

**Product:** India Public Accountability Dashboard
**Version:** MVP v0.1
**Status:** Draft
**Primary intent:** Build a public, transparent, evidence-backed accountability dashboard for Indian politicians using official public data, with clear methodology, explainable rankings, and constituency-level discovery.

## 1. Product summary

This product helps citizens, journalists, researchers, and civic-minded voters quickly understand how a politician is performing based on publicly available records.

It is not a “best politician” app. It is a public record explorer with transparent scorecards.

Every score, deduction, badge, and ranking must be traceable to source data. Users should always be able to inspect the raw basis behind any metric.

The MVP will prioritize **trust, clarity, and defensibility** over breadth.

---

## 2. Problem

Public data about politicians exists, but it is fragmented, hard to compare, hard to search, and almost impossible for ordinary users to turn into a usable picture.

Today, a citizen who wants to evaluate a politician has to jump across multiple sites, inconsistent records, PDF disclosures, and scattered reports. Even when data exists, it is not normalized, ranked, or explained in one place.

The result is that public opinion gets shaped more by noise, narrative, and social media than by structured public evidence.

---

## 3. Product thesis

If we collect official public data, normalize it into one entity graph, and present it as transparent scorecards with source-linked evidence, users will trust and use the product as a civic utility.

The product becomes valuable only if it is:

* searchable
* comparable
* explainable
* source-backed
* politically neutral in tone
* careful about attribution

---

## 4. Scope decision for MVP

### Hard decision

The MVP will **not** cover all politicians in India from day one.

### MVP coverage

Start with **Members of Parliament only**, across India.

This gives:

* centralized and relatively structured official data
* cleaner entity resolution
* a manageable scope
* a product that can launch with credibility

### Why not include everything yet

FIR counts, pothole complaints, local issue reports, budgets, and social media sentiment all sound useful, but many of them are noisy, indirectly attributable, or hard to map fairly to a single politician. That makes them dangerous in a ranking product unless handled very carefully.

For MVP, only include data that is:

* official or primary-source
* attributable to a specific politician
* structurally consistent enough to normalize nightly
* fair enough to score

---

## 5. Goals

### Product goals

* Make politician data understandable in under 60 seconds
* Let users search and compare politicians quickly
* Publish a transparent ranking methodology
* Show raw evidence behind every metric
* Create a credible public-facing civic dashboard

### Engineering goals

* Build reliable nightly ingestion from multiple public sources
* Maintain raw-source provenance for every derived metric
* Version all scoring formulas
* Support reproducible backfills and re-computations
* Showcase clean data, backend, infra, and frontend architecture

---

## 6. Non-goals for MVP

The MVP will not:

* score politicians using Twitter/X sentiment
* infer corruption from unverified reports
* assign blame for general crime rates in a constituency
* include user-generated accusations
* rank politicians using opaque AI summaries
* cover MLAs, municipal corporators, panchayat leaders, or ministers separately
* include predictive claims such as “will win next election”
* generate narrative verdicts like “good” or “bad”

---

## 7. Core principle: score only what is attributable

All data in the system falls into one of three classes.

### Tier A: directly attributable and scoreable

Used in the MVP score.
Examples:

* attendance in Parliament
* number of questions asked
* debates participated in
* committee memberships
* self-declared criminal cases from affidavits
* self-declared assets and liabilities from affidavits
* re-election and office history

### Tier B: official but indirectly attributable

Visible in profiles or constituency pages, but **not** included in the core score in MVP.
Examples:

* constituency development indicators
* scheme/budget allocations
* local complaints and public works status
* issue-reporting volumes like potholes or civic complaints

### Tier C: noisy or non-official signals

Not used in MVP. May appear later as clearly labeled external signals.
Examples:

* Twitter/X chatter
* media sentiment
* non-official allegation trackers
* crowdsourced rating systems

This rule is critical. It protects fairness.

---

## 8. Target users

### Citizens

They want a fast, clear view of their representative.

### Journalists and researchers

They want searchable, source-backed data and comparisons.

### Civic organizations

They want evidence-backed dashboards and exports.

### Engineers and recruiters

This is secondary but useful. The product also serves as a portfolio-grade showcase of data systems, ETL, provenance, ranking systems, and public product design.

---

## 9. MVP user stories

A user can:

* search a politician by name, constituency, party, or state
* open a politician profile and see a structured accountability scorecard
* inspect the raw factors behind the score
* compare multiple politicians side by side
* browse leaderboards by state, party, and chamber
* open a constituency page and see its representatives
* read the methodology in plain language
* click through to official sources for verification

---

## 10. MVP features

## 10.1 Search and filters

Users can search by:

* politician name
* constituency
* state
* party
* chamber
* current vs former member

Filters:

* state
* party
* chamber
* score range
* criminal-case disclosure status
* attendance range
* asset range

## 10.2 Politician profile page

Each profile includes:

* full name
* photo if officially available
* current office and chamber
* constituency
* party
* state
* tenure history
* election history
* accountability score
* score breakdown
* attendance
* debates
* questions
* committee participation
* declared criminal cases
* declared assets and liabilities
* raw-source links
* last updated timestamp

## 10.3 Leaderboards

Leaderboards available by:

* all MPs
* state
* party
* chamber
* constituency ranking view

Leaderboards must allow sorting by:

* overall score
* attendance
* questions
* debates
* criminal-case disclosure count
* assets

## 10.4 Comparison view

Users can compare 2 to 5 politicians on:

* overall score
* attendance
* debates
* questions
* criminal-case disclosures
* assets and liabilities
* tenure
* election history

## 10.5 Constituency page

Each constituency page includes:

* current representative
* previous representatives
* state
* chamber
* constituency rank view
* linked official records
* contextual, non-scored public data if available

For MVP, constituency pages should stay simple. Do not overpromise local governance analytics yet.

## 10.6 Methodology page

Must include:

* what the score means
* what it does not mean
* data classes
* what counts toward score
* what is excluded
* score weights
* source list
* freshness policy
* data limitations
* dispute/correction process

## 10.7 Source evidence drawer

Every metric shown on the site must have:

* source label
* source URL or source document reference
* fetch timestamp
* parser version or ingestion batch ID
* last derived timestamp

This is non-negotiable.

---

## 11. Scoring model for MVP

The score should be simple, transparent, and stable.

### Recommended score structure

**Overall Score = Participation Score + Disclosure Score + Integrity Risk Adjustment**

### A. Participation Score (60%)

Measures visible parliamentary activity.
Includes:

* attendance
* questions asked
* debates participated in
* committee participation

Normalize each against chamber/session baselines to reduce distortion.

### B. Disclosure Score (25%)

Measures completeness and availability of public disclosures.
Includes:

* affidavit completeness
* consistent election record linkage
* assets/liabilities declared
* whether mandatory public record fields are available and parseable

This is less about moral judgment and more about usable public transparency.

### C. Integrity Risk Adjustment (15%)

Based only on self-declared official disclosures.
Includes:

* criminal-case counts from affidavit disclosures
* optional severity buckets later, if classification is reliable

Important: this should be an adjustment, not a moral verdict. The UI must explicitly state that these are self-declared cases from official filings and not convictions.

### Excluded from MVP score

* Twitter/X sentiment
* pothole complaint volume
* generic FIR counts in the constituency
* media coverage tone
* complaint portals unless politician linkage is direct and defensible
* budgets where attribution is too weak

---

## 12. Data sources for MVP

### Primary source categories

* Parliament / member profile data
* attendance data
* debates and questions data
* committee data
* election result data
* candidate affidavits and disclosures
* government open data catalog where directly relevant

### Source handling policy

Use API first where available.
Use structured scrape second.
Use PDF extraction only when no structured alternative exists.
Archive every raw file or page version.

---

## 13. Data model

Core entities:

### Politician

Canonical person record.

### Office

MP, chamber, term, party, constituency, active status.

### Constituency

Name, chamber, state, geography metadata.

### Election Record

Election year, constituency, party, result, vote stats, affidavit linkage.

### Activity Record

Attendance, debates, questions, committees, session metadata.

### Disclosure Record

Assets, liabilities, criminal-case disclosures, filing metadata.

### Source Record

Raw URL, document snapshot, checksum, fetch timestamp, parse status.

### Score Record

Overall score, component scores, formula version, computed timestamp.

---

## 14. Functional requirements

The system must:

* support nightly scheduled data ingestion
* detect source changes and reprocess only changed records where possible
* preserve raw source artifacts
* normalize politician identities across years and party changes
* recalculate all scores after ingestion
* expose public read APIs for the frontend
* support sorting, filtering, and comparison at scale
* log parse failures and source drift
* show freshness timestamps on every page

---

## 15. Non-functional requirements

### Transparency

Every displayed metric must be traceable.

### Explainability

Every score must show a breakdown and formula version.

### Freshness

Nightly updates for supported sources.

### Reliability

A broken source should degrade gracefully, not break the entire product.

### Auditability

Past scores must remain reproducible.

### Performance

Search should feel instant. Profile pages should load fast enough for public sharing.

### Neutrality

Language must remain descriptive, not rhetorical.

---

## 16. System architecture

## 16.1 Ingestion layer

Source adapters run nightly.
Each adapter:

* fetches source data
* stores raw artifact
* validates shape
* emits parse output
* logs failures

## 16.2 Raw data store

Stores:

* HTML snapshots
* PDFs
* CSVs
* JSON payloads
* fetch metadata
* checksums

## 16.3 Normalization layer

Resolves:

* person identity
* constituency naming variants
* party naming variants
* election cycle alignment
* session alignment

## 16.4 Derived metrics layer

Produces:

* normalized politician stats
* score components
* leaderboards
* compare views
* cached aggregates

## 16.5 API layer

Public read API for:

* search
* profile
* leaderboard
* comparison
* constituency

## 16.6 Frontend

Web-first public app.
No mobile app in MVP.

---

## 17. Recommended stack

Keep it boring and strong.

* **Frontend:** Next.js
* **Backend API:** FastAPI or Go
* **ETL / ingestion:** Python
* **Primary DB:** Postgres
* **Search:** Meilisearch or OpenSearch
* **Raw artifact storage:** S3-compatible object store
* **Job scheduling:** Temporal, Dagster, or cron-based workers initially
* **Observability:** structured logs + metrics + alerting
* **Caching:** Redis if needed

The point is not flashy infra. The point is trustworthy data operations.

---

## 18. UX principles

The UI must feel:

* clean
* serious
* non-partisan
* minimal
* information-dense without clutter

No hero fluff.
No AI-generated summaries pretending to be truth.
No decorative noise.

Every important block should answer one question:

* who is this person
* what is their score
* why
* where did this come from
* how do they compare

---

## 19. Success metrics for MVP

### Product metrics

* searches per active user
* profile views per session
* compare usage rate
* methodology page open rate
* source-link clickthrough rate
* return visitor rate

### Engineering metrics

* nightly pipeline success rate
* parser failure rate
* identity resolution error rate
* median page response time
* source freshness lag

---

## 20. Risks

### 1. Attribution risk

Some public problems cannot fairly be mapped to one politician.

### 2. Source inconsistency

Government data structures may change without notice.

### 3. Identity resolution risk

Name variants across years and elections can create bad joins.

### 4. Political sensitivity

Even accurate data products can trigger accusations of bias.

### 5. Legal and reputational risk

Labels and language must be precise. Never imply guilt from case disclosures.

---

## 21. Guardrails

* Never use non-official allegations in scoring
* Never use opaque AI judgment in scoring
* Never show “best” or “worst” labels without clear metric context
* Always link to source evidence
* Always disclose limitations
* Keep score formula public
* Version formulas and preserve historical reproducibility

---

## 22. MVP launch criteria

The MVP is ready when:

* all current MPs are ingested
* politician identity resolution is stable enough for public trust
* profiles render with source-backed metrics
* search and filters work reliably
* compare view works
* leaderboards work
* methodology page is complete
* nightly refresh pipeline is operational
* source failures are monitored
* score explanations are visible and understandable

---

## 23. Post-MVP roadmap

### Phase 2

* add MLA support state by state
* add budget and scheme-linked contextual tabs
* add public issue trend data as non-scored signals
* improve criminal-case severity classification
* add exports for researchers and journalists

### Phase 3

* add municipal data where official structures are stable
* add grievance and civic-issue trend overlays
* add district and city drilldowns
* add public API

### Phase 4

* add external signal panels clearly separated from official score
* add alerting and “what changed” feeds
* add watchdog and newsroom workflows

---

## 24. Final MVP recommendation

Build **one strong thing first**:

A national MP accountability dashboard with:

* search
* profile pages
* transparent scorecards
* compare mode
* leaderboards
* source evidence
* nightly refresh

Do **not** put FIR trends, potholes, budget claims, and Twitter into the ranking yet.

Include them later as clearly labeled contextual layers once attribution and sourcing are strong enough.
