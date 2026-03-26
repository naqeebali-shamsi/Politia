# Contributing to Politia

Politia is an open-source civic accountability dashboard for Indian Members of Parliament. Every contribution helps citizens, journalists, and researchers access structured, source-backed public data about their representatives.

**Before contributing, please read the [Code of Conduct](CODE_OF_CONDUCT.md).**

This guide is designed so you can clone the repo and submit your first PR within an hour.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Architecture Overview](#architecture-overview)
3. [Contribution Areas](#contribution-areas)
4. [Code Standards](#code-standards)
5. [Data Contribution Guidelines](#data-contribution-guidelines)
6. [Guardrails — Read This Carefully](#guardrails)
7. [Infrastructure Needs](#infrastructure-needs)
8. [Submitting a Pull Request](#submitting-a-pull-request)

---

## Getting Started

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | Backend API and data processing |
| Node.js | 20+ | Frontend (Next.js 16) |
| PostgreSQL | 15+ | Production database; SQLite works for local dev |
| Git | 2.30+ | Conventional commits required |

### Clone and Set Up the Backend

```bash
git clone https://github.com/naqeebali-shamsi/Politia.git
cd Politia/backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Edit with your database URL if using PostgreSQL
# For local development, SQLite works out of the box (politia.db)

# Run the API server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Swagger docs are at `http://localhost:8000/docs`.

### Run the Tests

```bash
cd Politia/backend
pytest
```

All 204+ tests must pass before submitting a PR. Tests run against an in-memory SQLite database, so no external services are needed.

### Set Up the Frontend

```bash
cd Politia/frontend

npm install
npm run dev
```

The frontend runs at `http://localhost:3000` and expects the backend API at `http://localhost:8000`.

### Database Options

- **SQLite (default for local dev):** No setup needed. The backend creates `politia.db` automatically.
- **PostgreSQL (production-like):** Set `DATABASE_URL=postgresql://user:pass@localhost:5432/politia` in your `.env` file. Run Alembic migrations with `alembic upgrade head`.

---

## Architecture Overview

Politia follows **hexagonal architecture** (ports and adapters). This means business logic is isolated from infrastructure concerns like databases, APIs, and web frameworks.

```
backend/app/
  domain/           # Pure business logic — no framework imports
    entities/        # Politician, ElectionRecord, ScoreRecord, etc.
    interfaces/      # Repository ports (abstract base classes)
    value_objects/   # Immutable domain primitives

  application/       # Use cases and orchestration
    services/        # Application services that coordinate domain logic
    dto/             # Data transfer objects between layers

  infrastructure/    # Adapters that implement domain interfaces
    database/        # SQLAlchemy repository implementations
    ingestion/       # Data source adapters (BaseSourceAdapter pattern)
      adapters/      # Concrete adapters: CSV imports, scrapers
    scoring/         # Scoring engine, formulas, strategies
    ml/              # Anomaly detection, entity resolution

  api/               # HTTP layer (FastAPI)
    v1/              # Versioned REST endpoints
    schemas/         # Pydantic request/response schemas

frontend/src/
  app/               # Next.js App Router pages
  components/        # React components (CSS Modules, server-first)
  lib/               # API client, utilities
  types/             # TypeScript type definitions
```

### Key Design Principles

- **Dependency rule:** Dependencies point inward. `domain/` imports nothing from `infrastructure/` or `api/`. Infrastructure implements domain interfaces.
- **Open/Closed Principle for data sources:** New data sources are added by creating a new adapter that extends `BaseSourceAdapter`. No existing code needs to change.
- **Repository pattern:** All database access goes through repository interfaces defined in `domain/interfaces/`. Tests use fake implementations from `tests/fakes.py`.

### How the Scoring Engine Works

The scoring engine lives in `infrastructure/scoring/`. It computes a composite score for each politician based on three dimensions:

1. **Participation** (weight: 60%) — Attendance, debates, questions asked
2. **Disclosure** (weight: 25%) — Asset transparency, criminal case declarations
3. **Integrity** (weight: 15%) — Derived from self-declared affidavit data

Formulas are versioned in `infrastructure/scoring/formulas/`. Any formula change requires a version bump and documentation update. See the [Guardrails](#guardrails) section.

### How Data Ingestion Works

1. A **source adapter** (extending `BaseSourceAdapter`) fetches and parses raw data from an official source.
2. The **entity resolver** (`ingestion/entity_resolver.py`) matches incoming records to existing politicians using fuzzy matching (rapidfuzz).
3. Records are persisted through domain repository interfaces.
4. A **SourceRecord** is created for every piece of ingested data, maintaining full provenance.

Ingestion scripts live in `backend/scripts/` (e.g., `ingest.py`, `ingest_questions.py`, `ingest_assembly.py`).

---

## Contribution Areas

### Good First Issue

These require minimal context and are great for your first contribution:

- Fix typos or improve docstrings
- Add type hints to functions missing them
- Write tests for untested edge cases
- Improve error messages
- Add missing API endpoint documentation
- Frontend accessibility improvements (aria labels, keyboard navigation)

### Medium

These require understanding one subsystem:

- New API endpoints (following the existing v1 pattern)
- New frontend components (CSS Modules, server components by default)
- Additional data source adapters (see [Data Contribution Guidelines](#data-contribution-guidelines))
- Dashboard visualization improvements
- Search and filtering enhancements
- Alembic migration scripts for schema changes

### Advanced

These touch core systems and require deep context:

- Entity resolution improvements (reducing false merges/missed matches)
- ML anomaly detection models (`infrastructure/ml/`)
- Scoring formula changes (requires ADR + version bump)
- Audio transcription pipeline (Whisper on 17K hours of Sansad audio)
- PDF extraction from 500K+ MyNeta affidavits
- DuckDB lakehouse architecture (`backend/lakehouse/`)
- Semantic search with sentence-transformers and pgvector

---

## Code Standards

### Test-Driven Development (TDD) Is Mandatory

Every code change must include tests. The expected workflow:

1. Write a failing test that describes the desired behavior.
2. Write the minimal code to make it pass.
3. Refactor while keeping tests green.

PRs without tests will not be merged. The only exceptions are pure documentation or configuration changes.

### Python (Backend)

- **Type hints** on all function signatures and return types.
- **Docstrings** on all public classes and functions.
- Follow existing patterns — look at neighboring files before inventing new conventions.
- Use `httpx` for HTTP requests (not `requests`).
- Use `pydantic` for data validation at API boundaries.
- Keep domain entities free of framework imports.

### TypeScript / React (Frontend)

- **CSS Modules** for styling. No Tailwind, no styled-components, no inline styles.
- **Server Components by default.** Only use `"use client"` when you need browser APIs or interactivity.
- Follow Next.js App Router conventions (file-based routing in `src/app/`).
- TypeScript strict mode is enabled. No `any` types without justification.

### Git Conventions

- **Conventional commits:** `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`
- Examples:
  - `feat: add parliamentary question search endpoint`
  - `fix: correct entity resolution for hyphenated names`
  - `docs: add data source adapter tutorial`
  - `test: add edge cases for scoring engine zero-data politicians`
- PRs go against `master` branch.
- Keep commits atomic — one logical change per commit.

### Linting and Formatting

- Backend: Follow PEP 8. Use your editor's Python formatter.
- Frontend: ESLint is configured. Run `npm run lint` before submitting.

---

## Data Contribution Guidelines

### Adding a New Data Source

Politia's data comes exclusively from official public sources. If you want to add a new data source:

1. **Open an issue first** using the [Data Contribution template](https://github.com/naqeebali-shamsi/Politia/issues/new?template=data_contribution.md). Describe the source, its official provenance, data format, and estimated volume.
2. **Get approval** before writing code. Data sources must meet these criteria:
   - Official or primary-source (government websites, election commission, parliament records)
   - Attributable to a specific politician
   - Structurally consistent enough to normalize
   - Publicly accessible without violating terms of service

### Writing a Source Adapter

All data ingestion follows the `BaseSourceAdapter` pattern in `backend/app/infrastructure/ingestion/base_adapter.py`:

```python
from app.infrastructure.ingestion.base_adapter import BaseSourceAdapter, IngestionResult

class MyNewSourceAdapter(BaseSourceAdapter):
    @property
    def source_name(self) -> str:
        return "my_source_name"  # Unique identifier

    def fetch(self) -> list[dict]:
        """Fetch raw data from the source."""
        # Download CSV, scrape HTML, parse PDF, etc.
        # Return list of raw record dicts
        ...

    def parse(self, raw_records: list[dict]) -> list[dict]:
        """Normalize raw records into domain-ready dicts."""
        # Clean names, normalize dates, validate fields
        ...
```

Place your adapter in `backend/app/infrastructure/ingestion/adapters/`.

### Entity Resolution Requirements

Every ingested record must be linked to a politician through entity resolution. The resolver uses fuzzy matching (rapidfuzz) on name + constituency + election year. When adding new data:

- Normalize names: strip titles (Shri/Smt/Dr.), normalize whitespace, handle transliteration variants.
- Include as many disambiguating fields as possible (constituency, state, year, party).
- Test against known false-merge cases (common names like "Ram Kumar" or "Om Prakash").
- Log unmatched records — do not silently drop them.

### Data Quality Standards

- Every record must have a `SourceRecord` linking it to an official URL or file.
- Null/missing values must be explicitly represented (not zero, not empty string).
- Date formats must be ISO 8601.
- Currency values must be stored in paisa (integer) to avoid floating-point issues.
- All ingestion scripts must be idempotent — running them twice produces the same result.

---

## Guardrails

These are non-negotiable rules for every contribution. PRs that violate any of these will be rejected regardless of code quality.

### Political Neutrality

The platform must never endorse, condemn, rank morally, or editorialize about any politician, party, or ideology. Politia presents data. It does not take sides.

- No adjectives that imply moral judgment ("corrupt", "honest", "best", "worst").
- No comparisons framed as endorsements ("X outperforms Y" is acceptable in a data context; "X is better than Y" is not).
- UI copy, tooltips, labels, and documentation must be neutral in tone.
- If you are unsure whether phrasing is neutral, err on the side of drier, more clinical language.

### Data Attribution

Every metric displayed on the platform must trace to an official, verifiable source. This is a hard requirement.

- Every data point must link to a `SourceRecord` with a URL or file reference.
- No crowd-sourced accusations, social media claims, or unverified reports.
- If a data source becomes unavailable, the platform must indicate "source unavailable" rather than silently dropping the data.

### Precise Language Around Criminal Data

Criminal case data comes from **self-declared affidavits** filed by candidates with the Election Commission. These are declarations, not convictions.

- CORRECT: "X declared Y criminal cases in their 2024 affidavit"
- INCORRECT: "X has Y criminal cases" (implies active legal proceedings)
- NEVER: "X is a criminal" or any language implying guilt

This distinction is legally significant. Defamation law in India places the burden of proof on the publisher. Imprecise language creates legal risk for the project and its contributors.

### No AI-Generated Verdicts

The platform presents data for users to interpret. It does not render conclusions.

- ML models (anomaly detection, scoring) must be clearly labeled as algorithmic outputs, not facts.
- Anomaly flags must say "statistically unusual" not "suspicious" or "problematic".
- The scoring formula is a transparency tool, not a judgment. Documentation must make this clear.

### Privacy

No personal data beyond what appears in official public records (election commission filings, parliamentary records, government gazettes).

- No personal phone numbers, home addresses, family member details (unless declared in official affidavits).
- No social media scraping for personal information.
- If a data source contains personal data mixed with public records, strip the personal data during ingestion.

### Scraping Ethics

- Respect `robots.txt` on every domain.
- Rate-limit all scrapers to avoid overloading public infrastructure.
- Do not scrape sites whose terms of service prohibit it.
- Cache aggressively — never re-scrape data you already have.
- Prefer official APIs and bulk data downloads over scraping when available.

### Score Transparency

The scoring formula is a core trust mechanism. Changes require:

1. An ADR (Architecture Decision Record) documenting the rationale.
2. A version bump in the formula (e.g., v2.1 to v2.2).
3. Public documentation of what changed and why.
4. Re-computation of all affected scores.
5. A migration path so historical scores remain comparable.

### Defamation Risk Awareness

India's defamation laws (both civil and criminal under IPC Section 499/500) are strict. Every contributor should understand:

- Never use language that implies guilt, corruption, or criminal behavior beyond what official records state.
- "Declared" is not the same as "convicted". "Filed" is not the same as "proven".
- When in doubt, quote the source verbatim rather than paraphrasing.
- If you are writing UI copy or documentation that references criminal cases, assets, or controversies, have another contributor review the language.

---

## Infrastructure Needs

Politia runs on a zero budget. We actively need sponsors or contributors for:

| Need | Why | Estimated Cost |
|------|-----|----------------|
| GPU compute (Whisper transcription) | 17,000 hours of parliament audio to transcribe | ~$500-1000 one-time on cloud GPU |
| Larger PostgreSQL instance | Current Neon free tier is 512MB; we have 200K+ records growing | $0-20/mo (Neon Pro or self-hosted) |
| Object storage | PDFs (500K affidavits) and audio files (2-3 TB) | ~$5-15/mo on Cloudflare R2 or Hetzner |
| CI/CD improvements | Automated testing on PRs, staging deployments | GitHub Actions free tier may suffice |
| DuckDB/analytics hosting | Lakehouse queries for large-scale analysis | Self-hostable, needs a small VPS |

If you can sponsor compute, storage, or hosting, please open an issue or reach out to the maintainers.

---

## Submitting a Pull Request

1. **Fork the repository** and create a feature branch from `master`.
2. **Write tests first** (TDD). Make sure they fail before writing implementation code.
3. **Make your changes.** Follow the code standards and guardrails above.
4. **Run the full test suite:** `cd backend && pytest` — all 204+ tests must pass.
5. **Lint the frontend** if you touched it: `cd frontend && npm run lint`.
6. **Write a clear PR description** using the [PR template](.github/PULL_REQUEST_TEMPLATE.md). Include:
   - What you changed and why
   - How to test it
   - Whether it touches data, scoring, or user-facing language (triggers neutrality review)
7. **Submit the PR against `master`.** A maintainer will review it.

### Review Criteria

Every PR is evaluated on:

- **Tests pass** — Non-negotiable.
- **Neutrality** — Language in UI, docs, and code comments is checked for bias.
- **Source attribution** — Data changes must include provenance.
- **Architecture fit** — Changes respect hexagonal architecture boundaries.
- **Simplicity** — The simplest solution that works is preferred.

### Response Times

This is a volunteer-run project. Please allow a few days for review. If your PR has not received attention after a week, it is fine to leave a polite comment pinging the maintainers.

---

## Questions?

- Open a [GitHub Discussion](https://github.com/naqeebali-shamsi/Politia/discussions) for general questions.
- Open an [Issue](https://github.com/naqeebali-shamsi/Politia/issues) for bugs or feature requests.
- Review the [PRD](PRD.md) to understand product direction.
- Review the [Big Data Architecture](backend/docs/BIG-DATA-ARCHITECTURE.md) for infrastructure plans.

Thank you for contributing to transparent democracy.
