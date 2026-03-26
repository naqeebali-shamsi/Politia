# Politia

**Open-source accountability dashboard for Indian Members of Parliament.**

![CI](https://github.com/naqeebali-shamsi/Politia/actions/workflows/ci.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What is Politia?

Politia aggregates official public data about Indian MPs into a single, searchable, source-backed dashboard. Every metric traces to an official record. The platform takes no political position -- it presents data and lets citizens, journalists, and researchers draw their own conclusions.

**Live:** [politia.in](https://politia.in) | **API:** [api.politia.in/docs](https://api.politia.in/docs) | **Blog:** [blog.politia.in](https://blog.politia.in)

---

## Key Numbers

| Metric | Count |
|--------|-------|
| Election records ingested | 500,000+ |
| Parliamentary questions indexed | 296,000+ |
| Semantic embeddings generated | 42,000+ |
| Automated tests | 204+ |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| Frontend | Next.js 16, React 19, TypeScript, CSS Modules |
| Database | PostgreSQL (Neon), DuckDB (analytics lakehouse) |
| Search | sentence-transformers, pgvector |
| Entity Resolution | rapidfuzz |
| Infrastructure | Vercel (frontend), Render (API), GitHub Actions (CI) |

---

## Quick Start

### Backend

```bash
git clone https://github.com/naqeebali-shamsi/Politia.git
cd Politia/backend

python -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
cp .env.example .env       # SQLite works out of the box for local dev

# Run tests
pytest

# Start the API server
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`.

### Frontend

```bash
cd Politia/frontend

npm install
npm run dev
```

Frontend runs at `http://localhost:3000`, expects the API at `http://localhost:8000`.

---

## Architecture

Politia follows **hexagonal architecture** (ports and adapters). Domain logic is isolated from infrastructure.

```
backend/app/
  domain/           Pure business logic, no framework imports
  application/      Use cases and service orchestration
  infrastructure/   Database repos, ingestion adapters, scoring engine
  api/              FastAPI HTTP layer with Pydantic schemas

frontend/src/
  app/              Next.js App Router pages
  components/       React components (CSS Modules, server-first)
  lib/              API client and utilities
  types/            TypeScript type definitions
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full architecture guide.

---

## Contributing

Contributions are welcome. Read the [Contributing Guide](CONTRIBUTING.md) to get started -- it covers architecture, code standards, TDD requirements, data contribution guidelines, and the guardrails that keep the platform politically neutral.

**TDD is mandatory.** Every code change ships with tests.

---

## Blog

- [Building Politia: From Idea to 500K Records](https://blog.politia.in)
- [Entity Resolution for Indian Politicians](https://blog.politia.in)
- [Scoring Formula v2: Design Decisions](https://blog.politia.in)

---

## License

[MIT](LICENSE) -- Copyright 2026 Naqeeb Ali Shamsi
