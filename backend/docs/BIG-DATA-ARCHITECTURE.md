# Politia Big Data Architecture
## Comprehensive Design Document — March 2026

---

## Table of Contents
1. [Current State Assessment](#1-current-state-assessment)
2. [Data Source Inventory & Scale](#2-data-source-inventory--scale)
3. [Storage Architecture](#3-storage-architecture)
4. [Database Strategy](#4-database-strategy)
5. [Compute & Processing](#5-compute--processing)
6. [PDF Processing Pipeline](#6-pdf-processing-pipeline)
7. [Audio Processing Pipeline](#7-audio-processing-pipeline)
8. [Search Architecture](#8-search-architecture)
9. [ETL Orchestration](#9-etl-orchestration)
10. [Real-time & Streaming](#10-real-time--streaming)
11. [ML/AI Capabilities](#11-mlai-capabilities)
12. [GeoJSON & Mapping](#12-geojson--mapping)
13. [Free Tier Limits & Breaking Points](#13-free-tier-limits--breaking-points)
14. [Zero-Budget Architecture](#14-zero-budget-architecture)
15. [Phased Implementation Roadmap](#15-phased-implementation-roadmap)
16. [Cost Projections](#16-cost-projections)

---

## 1. Current State Assessment

### What We Have Today
| Component        | Technology            | Tier     | Capacity        |
|------------------|-----------------------|----------|-----------------|
| Database         | PostgreSQL on Neon    | Free     | 0.5 GB          |
| Backend API      | FastAPI on Render     | Free     | 750 hrs/mo      |
| Frontend         | Next.js on Vercel     | Hobby    | 100 GB transfer |
| Local DB         | SQLite (politia.db)   | Local    | Unbounded       |
| Data processing  | Python scripts        | Local    | Single machine  |

### Current Data Volume
| Table               | Records   | Est. Size |
|---------------------|-----------|-----------|
| Politicians         | 86,000    | ~8 MB     |
| Election records    | 101,000   | ~12 MB    |
| Disclosures         | 10,000    | ~2 MB     |
| Activity records    | 1,500     | ~0.5 MB   |
| Source records       | Various   | ~5 MB     |
| **Total**           | **~200K** | **~50 MB**|

### Current Schema (models.py)
- Politician, Office, Constituency, ElectionRecord, ActivityRecord, DisclosureRecord, ScoreRecord, SourceRecord
- SQLAlchemy ORM with PostgreSQL/SQLite dual support
- Entity resolution via rapidfuzz
- PDF parsing via pdfplumber

### Key Constraint
**Zero budget.** Every architectural choice must have a free tier or be self-hostable on the cheapest possible infrastructure.

---

## 2. Data Source Inventory & Scale

### 2.1 Booth-Level Voting Data
- **Source:** ECI (Election Commission of India), datameet/india-election-data
- **Scale:** 1M+ polling stations, 900M+ voter interactions across all elections
- **Format:** CSV, HTML scraping
- **Current:** datameet assembly.csv has 398,702 records (assembly elections)
- **Growth:** ~50K new records per general election cycle (5 years)
- **Estimated storage:** 5-10 GB as structured data, 50+ GB raw HTML snapshots

### 2.2 Parliamentary Questions
- **Source:** Lok Sabha website (PDF parsing), OGD Platform India, loksabha-questions scrapers
- **Scale:** 400K+ questions (starred + unstarred) with full text
- **Format:** PDFs requiring parsing, no official API available
- **Estimated storage:** 2-3 GB text, 20+ GB raw PDFs

### 2.3 State Assembly Elections
- **Source:** datameet assembly.csv (398K records already local), ECI
- **Scale:** 398K historical + ongoing state elections
- **Format:** CSV (available), booth-wise results in separate files
- **Estimated storage:** 500 MB structured, 5 GB with booth-level data

### 2.4 MyNeta Affidavit PDFs
- **Source:** myneta.info (ADR/National Election Watch)
- **Scale:** 50K+ scanned PDFs, many handwritten in Hindi
- **Fields:** Criminal cases, assets, liabilities, education, income
- **Challenge:** Mixed languages (English/Hindi), handwritten forms, inconsistent layouts
- **Existing:** 27,447 records in 2004-2019-affidavits.csv (already scraped structured data)
- **Estimated storage:** 100-200 GB raw PDFs, 2-3 GB extracted structured data

### 2.5 Parliament Proceedings (Sansad Audio)
- **Source:** kalpalabs/sansad on HuggingFace (CC0 license)
- **Scale:** 18K sessions, 17K hours of audio, ~3,200 speakers, 1992-2024
- **Features:** ~50% have weakly-labeled timestamped transcripts, most have speaker labels
- **Languages:** Mixed Hindi and English
- **Estimated storage:** 2-3 TB raw audio, 5-10 GB transcripts

### 2.6 Real-time Parliament Data
- **Source:** Lok Sabha/Rajya Sabha websites, ECI updates, committee reports
- **Scale:** ~100 session days/year, daily question lists, committee reports
- **Format:** HTML scraping, PDF downloads
- **Estimated storage:** 1-2 GB/year incremental

### 2.7 GeoJSON Constituency Maps
- **Source:** DataMeet Community Maps (projects.datameet.org/maps/)
- **Scale:** 543 Lok Sabha + 4,000+ assembly constituencies
- **Format:** GeoJSON, Shapefiles (WGS84, EPSG4326)
- **Additional:** ML Infomap has pre/post-delimitation boundaries
- **Estimated storage:** 500 MB - 1 GB GeoJSON files

### 2.8 Media Monitoring (Future)
- **Source:** News APIs, RSS feeds, social media
- **Scale:** Thousands of articles/day mentioning politicians
- **Estimated storage:** 5-10 GB/year text, potentially more with snapshots

### Total Estimated Data
| Category          | Raw Storage | Structured Storage |
|-------------------|-------------|-------------------|
| Election data     | 60 GB       | 15 GB             |
| Parliamentary Q&A | 25 GB       | 3 GB              |
| Affidavit PDFs    | 200 GB      | 3 GB              |
| Audio proceedings  | 3 TB        | 10 GB transcripts |
| Maps/GeoJSON      | 1 GB        | 1 GB              |
| Media (year 1)    | 10 GB       | 5 GB              |
| **Total**         | **~3.3 TB** | **~37 GB**        |

---

## 3. Storage Architecture

### 3.1 Object Storage Comparison (for raw data: PDFs, audio, HTML)

| Provider           | Free Tier         | 1 TB/mo   | 5 TB/mo    | 10 TB/mo   | Egress        |
|--------------------|-------------------|-----------|------------|------------|---------------|
| **Cloudflare R2**  | 10 GB free        | $15/mo    | $75/mo     | $150/mo    | **$0 (free)** |
| **Backblaze B2**   | 10 GB free        | $6/mo     | $30/mo     | $60/mo     | Free up to 3x storage |
| **Hetzner Object** | None              | ~$5/mo    | ~$25/mo    | ~$50/mo    | 1 TB free, then €1.19/TB |
| **Hetzner Storage Box** | None         | €4.50/mo  | €15.50/mo  | €20.80/mo  | Unlimited     |
| **MinIO (self-hosted)** | Free software | VPS cost  | VPS cost   | VPS cost   | Bandwidth cost |

### 3.2 Recommendation: Tiered Storage Strategy

**Phase 1 (Free, 0-10 GB):** Cloudflare R2 free tier
- 10 GB free storage, 0 egress cost
- 1M Class A (write) + 10M Class B (read) operations/month
- S3-compatible API
- Use for: GeoJSON maps, processed data exports, small datasets

**Phase 2 (Budget, 10 GB - 1 TB):** Cloudflare R2 paid
- $15/mo for 1 TB storage, still $0 egress
- Best value for read-heavy workloads (serving data to frontend)

**Phase 3 (Scale, 1-5 TB):** Hetzner Storage Box + Cloudflare R2
- Hetzner Storage Box BX21 (5 TB): €15.50/mo — for cold archive (PDFs, audio)
- Cloudflare R2 (100 GB): $1.50/mo — for hot serving layer
- Total: ~$18/mo for 5 TB archive + fast serving

**Why not Backblaze B2?**
B2 is cheaper for storage ($6/TB vs $15/TB) but charges for egress beyond 3x storage. Since Politia serves data publicly, R2's zero egress wins for the serving layer. B2 is viable for pure archive/backup.

**Why not MinIO self-hosted?**
MinIO is free software but requires a VPS (~$4-8/mo minimum on Hetzner). At that price, managed solutions (R2/B2) provide better reliability. MinIO makes sense only if you already have a VPS for other workloads.

---

## 4. Database Strategy

### 4.1 PostgreSQL at Scale — Can It Handle 1B+ Records?

**Yes, with proper architecture.** PostgreSQL can handle billions of rows with:

1. **Table Partitioning** — Range partition by election_year or state
   - election_records: partition by year (1 partition per election cycle)
   - voter_records: partition by state (28 states + 8 UTs)
   - Enables partition pruning — queries touching one year/state scan only that partition
   - pg_partman extension automates partition creation and maintenance

2. **BRIN Indexes** — Block Range Indexes for naturally ordered data (timestamps, years)
   - Tiny index size (MBs, not GBs) for billion-row tables
   - Perfect for time-range queries on election/voting data

3. **Partial Indexes** — Index only the data you frequently query
   - E.g., index only "Won" results, or only current-term politicians

4. **Resource Requirements for 1B rows:**
   - Storage: ~50-100 GB for 1B election records (columnar estimate)
   - RAM: 8-16 GB recommended for good index caching
   - This exceeds Neon's 0.5 GB free tier dramatically

### 4.2 When to Add Specialized Databases

| Use Case | Tool | Why | When |
|----------|------|-----|------|
| Primary OLTP | PostgreSQL (Neon/Supabase) | Already in use, strong ecosystem | Now |
| Analytical queries | **DuckDB** | In-process, zero infrastructure, reads Parquet directly | Phase 1 |
| Full-text search | **Typesense** (self-hosted) | Lightweight, sub-50ms search, easy to operate | Phase 2 |
| Time-series voting data | PostgreSQL + partitioning | No need for TimescaleDB at this scale | Phase 2 |
| Semantic search | **SQLite + sqlite-vss** or PostgreSQL + pgvector | Vector search without separate infrastructure | Phase 3 |
| Large-scale analytics | **ClickHouse** | Only if concurrent analytical queries become a bottleneck | Phase 4+ |

### 4.3 DuckDB as the Analytics Engine

DuckDB is the single most impactful tool for Politia's zero-budget constraint.

**Why DuckDB:**
- In-process (no server to run or pay for)
- Reads Parquet, CSV, JSON files directly from disk or R2
- 5-10x faster than Pandas for analytical queries
- TPC-H benchmark: 1 min 16 sec (DuckDB single machine) vs 8 min (Spark 32-node cluster)
- Handles datasets up to ~100-500 GB on a single machine
- Perfect for: election analytics, cross-referencing affidavit data, constituency analysis

**DuckDB + Parquet Lakehouse Pattern:**
```
Cloudflare R2 (or local disk)
  └── raw/           ← Raw CSVs, scraped HTML, PDFs
  └── bronze/        ← Cleaned Parquet files (schema-enforced)
  └── silver/        ← Joined/enriched Parquet files
  └── gold/          ← Pre-aggregated Parquet files for API
        ├── politician_scores.parquet
        ├── constituency_results.parquet
        └── question_topics.parquet
```

DuckDB queries these Parquet files directly. No database server needed. The API can read gold-layer Parquet files on startup or on-demand.

**DuckLake (New, 2025):**
DuckDB Labs released DuckLake — a lakehouse format using SQL database for metadata + Parquet for data. Provides ACID transactions over Parquet files. Experimental but promising for Politia's future.

### 4.4 PostgreSQL Capacity Planning

**Neon Free Tier (0.5 GB storage):**
- Current 50 MB usage = 10% of capacity
- 86K politicians + 101K elections = ~200K rows uses ~50 MB
- At current schema density: ~0.5 GB holds ~2M records
- **Breaking point: ~1.5-2M total records**

**When to upgrade from Neon Free:**
- Adding 398K assembly election records pushes to ~350 MB — still fits
- Adding 400K parliamentary questions with text — exceeds 0.5 GB
- Adding booth-level data (1M+ records) — definitely exceeds

**Strategy:** Keep PostgreSQL for OLTP (API serving, user-facing queries). Move analytics and bulk data to DuckDB + Parquet files on R2.

---

## 5. Compute & Processing

### 5.1 GitHub Actions for ETL

**Free tier (public repos):** Unlimited minutes on Linux runners
**Free tier (private repos):** 2,000 minutes/month

**2026 pricing changes:**
- Runner prices reduced by up to 39% (effective Jan 1, 2026)
- New $0.002/min cloud platform charge for self-hosted runners (March 1, 2026)
- Public repo standard runners remain FREE

**Specs per runner:** 4 vCPU, 16 GB RAM, 14 GB SSD
**Job timeout:** 6 hours max per job
**Concurrent jobs:** 20 (free tier)

**What you can do in 6 hours:**
- Parse ~50K CSV files and write Parquet
- Process ~10K PDFs with Tesseract OCR
- Run DuckDB analytics on 10+ GB of Parquet
- Entity resolution across 100K+ records

**Recommendation:** Use GitHub Actions as the primary ETL compute for Phase 1-2. Public repo = unlimited free minutes. Structure pipelines as matrix jobs to parallelize.

### 5.2 Modal.com for GPU Workloads

**Free tier:** $30/month in compute credits
- Starter plan: 100 containers, 10 concurrent GPUs
- Sub-second cold starts, instant autoscaling
- No data ingress/egress fees

**What $30/month buys:**
- RTX T4 GPU: ~$0.16/hr = ~187 GPU-hours/month
- Enough for: ~500 hours of Whisper transcription, or ~5K PDF pages OCR with GPU models
- Startup/academic credits: up to $25K free

**Use for:** Whisper audio transcription batches, GPU-accelerated OCR, embedding generation

### 5.3 Polars vs Pandas

**For Politia's data processing, use Polars:**
- 5x faster CSV loading (1 GB file: Polars ~4s vs Pandas ~20s)
- 4.6x faster filtering
- 2.6x faster group-by aggregations
- 11x faster sorting
- 3-8x faster joins
- Uses 80% less memory (1 GB CSV: Polars 179 MB vs Pandas 1.4 GB)
- Lazy evaluation + automatic parallelism
- Streaming execution for datasets larger than RAM

**Decision:** Replace all Pandas usage with Polars in data pipelines. Keep Pandas only for ML libraries that require it (scikit-learn, etc.).

### 5.4 Processing Framework Decision

| Workload | Tool | Why |
|----------|------|-----|
| CSV/Parquet transforms | Polars | Fastest single-machine dataframe library |
| SQL analytics | DuckDB | Reads Parquet, columnar engine, zero-config |
| Large joins (100M+ rows) | DuckDB | Handles out-of-core joins |
| ML feature engineering | Polars + DuckDB | Pipeline: Polars for transforms, DuckDB for aggregations |
| Distributed processing | NOT NEEDED YET | DuckDB + Polars handle 100GB+ on single machine |

**Apache Spark/Dask are NOT needed.** DuckDB completed TPC-H faster on one machine than Spark on 32 nodes. Politia's structured data (~37 GB) fits comfortably in single-machine processing.

---

## 6. PDF Processing Pipeline

### 6.1 The MyNeta Affidavit Challenge

**Scale:** 50K+ PDFs
**Challenges:**
- Scanned documents (not digital PDFs) — requires OCR
- Mixed languages: English + Hindi (Devanagari script)
- Handwritten entries in many forms
- Inconsistent layouts across states and years
- Tables with nested financial data

### 6.2 OCR Tool Comparison

| Tool | Hindi Support | Accuracy (printed) | Accuracy (handwritten) | Speed | Cost |
|------|--------------|-------------------|----------------------|-------|------|
| **Tesseract 5** | Yes (hin model) | 85-90% | Poor (40-60%) | Fast (CPU) | Free |
| **PaddleOCR** | Yes (109 langs) | 92-95% | Good (75-85%) | Fast (GPU preferred) | Free |
| **Surya** | Yes (90+ langs) | 93-96% | Good (80-88%) | Medium (GPU) | Free |
| **Google Vision** | Excellent | 98% | Good (85%) | Fast | $1.50/1K pages |
| **Amazon Textract** | Limited Hindi | 95% | Fair (70%) | Fast | $1.50/1K pages |

### 6.3 Recommended Pipeline

```
Stage 1: Classification (CPU, GitHub Actions)
  └── Classify each PDF: scanned vs digital, language, layout type
  └── Tool: pdfplumber (already in requirements.txt) for digital PDFs
  └── Route scanned PDFs to OCR pipeline

Stage 2: OCR (GPU, Modal.com)
  └── Primary: Surya (best open-source for multi-language, layout-aware)
  └── Fallback: PaddleOCR (109 languages, good table extraction)
  └── PP-StructureV3 for table recognition with nested data
  └── For handwritten Hindi: PaddleOCR-VL (vision-language model)

Stage 3: Structured Extraction (CPU, GitHub Actions)
  └── Regex + template matching for known affidavit formats
  └── Extract: name, constituency, assets, liabilities, criminal cases, education
  └── Validation against existing MyNeta structured data (27K records)

Stage 4: Quality Assurance
  └── Cross-reference extracted data with myneta.info scraped data
  └── Flag discrepancies for manual review
  └── Confidence scores per field
```

### 6.4 Cost Estimate for 50K PDFs

| Approach | Cost | Time |
|----------|------|------|
| Tesseract on GitHub Actions | $0 (public repo) | ~50 hours across jobs |
| Surya on Modal.com ($30/mo credit) | $0-30 | ~10 hours GPU time |
| PaddleOCR on Modal.com | $0-30 | ~8 hours GPU time |
| Google Vision API | $75 (50K pages) | ~2 hours |

**Recommendation:** Start with Tesseract (free, CPU) for digital PDFs. Use Surya/PaddleOCR on Modal for scanned/handwritten PDFs. Reserve Google Vision as a fallback for low-confidence results.

---

## 7. Audio Processing Pipeline

### 7.1 The Sansad Dataset

- 18K sessions, 17K hours of audio
- ~3,200 unique speakers (MPs) from 1992-2024
- ~50% already have weak transcripts (timestamped subtitles)
- Mixed Hindi/English (code-switching common in Indian Parliament)
- Contains background noise, clapping, shouting
- CC0 license — no copyright restrictions

### 7.2 Transcription Strategy

**Phase 1: Use Existing Transcripts**
- ~8,500 hours already have weak transcripts
- Clean and structure these first (text processing, no GPU needed)
- Extract speaker labels, timestamps, language tags
- Cost: $0 (CPU processing on GitHub Actions)

**Phase 2: Transcribe Remaining Audio**
- ~8,500 hours without transcripts
- Whisper Large V3 Turbo for high accuracy on Hindi/English
- WhisperX for word-level timestamps and alignment

**Whisper Compute Requirements:**
- Whisper Large V3 on RTX 3060: ~30x real-time (1 hour audio = 2 min processing)
- 8,500 hours / 30x speed = ~283 GPU-hours
- On SaladCloud: $1 = 200 hours of audio → 8,500 hours = ~$42.50
- On Modal.com ($30/mo credit): ~4 months of free-tier processing
- On dedicated RTX 3060 (Vast.ai ~$0.10/hr): ~$28

### 7.3 Speaker Diarization

**pyannote.audio 4.0 (community-1)** — Best open-source diarization model (2025)
- Identifies "who spoke when"
- Pipeline: Whisper (transcription) + pyannote (diarization) → speaker-attributed transcripts
- Can map speakers to known MP voice profiles over time
- Runs on CPU (slower) or GPU (faster)

**Pipeline:**
```
Raw Audio (HuggingFace)
  → pyannote.audio 4.0 (speaker segments)
  → Whisper Large V3 (transcription per segment)
  → Speaker identification (match to MP database)
  → Structured output: {speaker: "MP Name", text: "...", timestamp: ...}
```

### 7.4 Cost Summary for Audio

| Phase | Hours | Cost | Timeline |
|-------|-------|------|----------|
| Clean existing transcripts | 8,500 hrs of audio | $0 | 1-2 months |
| Transcribe remaining (Modal free) | 2,125 hrs/month | $0 | 4 months |
| Transcribe remaining (SaladCloud) | All 8,500 hrs | ~$43 | 1 week |
| Speaker diarization | 17K hrs | ~$50-100 | 2-3 weeks |
| **Total** | **17K hours** | **$43-100** | **1-5 months** |

---

## 8. Search Architecture

### 8.1 Requirements

1. **Full-text search** across 400K+ parliamentary questions (2-3 GB text)
2. **Fuzzy search** for politician names (already using rapidfuzz)
3. **Semantic search** — find questions about "farmer distress" even if text says "agricultural crisis"
4. **Faceted search** — filter by year, MP, party, state, topic
5. **Autocomplete** — instant suggestions while typing

### 8.2 Search Engine Comparison

| Feature | pg_trgm | Typesense | Meilisearch | Elasticsearch |
|---------|---------|-----------|-------------|---------------|
| Setup complexity | Zero (PG extension) | Low (single binary) | Low (single binary) | High (JVM cluster) |
| RAM for 400K docs | 0 (shared with PG) | ~200-400 MB | ~200-400 MB | 2-4 GB minimum |
| Query latency | 50-500ms | 1-10ms | 1-50ms | 10-50ms |
| Fuzzy/typo tolerance | Basic | Excellent | Excellent | Good |
| Faceted search | No (manual) | Built-in | Built-in | Built-in |
| Hindi/Devanagari | Poor (no non-ASCII trigrams) | Good | Good | Good |
| Semantic search | No | No (needs embedding) | No (needs embedding) | With vector plugin |
| Self-hosted cost | $0 (in PG) | $0 (single binary) | $0 (single binary) | $0 but needs 4GB+ RAM |
| Production overhead | Zero | Minimal | Minimal | Significant |

### 8.3 Recommendation: Typesense

**Why Typesense over alternatives:**
- 400K parliamentary questions (~200MB index) needs only ~400 MB RAM
- Sub-10ms search latency — fastest for the use case
- Typo tolerance built-in (critical for politician name search)
- Query-time search parameter configuration (no re-indexing)
- Single binary, runs on a $4/mo Hetzner VPS
- 4 vCPU node handles 100+ concurrent searches with 2M records

**Deployment:**
- Phase 1: Use PostgreSQL pg_trgm for basic search (free, zero setup)
- Phase 2: Deploy Typesense on Hetzner CAX11 (€3.79/mo) alongside other services
- Phase 3: Add semantic search layer with embeddings

### 8.4 Semantic Search Architecture

**Embedding Model: Vyakyarth-1-Indic-Embedding**
- Built by Ola Krutrim AI Labs specifically for Indian languages
- Supports Hindi, Bengali, Gujarati, Kannada, Malayalam, Marathi, Tamil, Telugu + English
- 768-dimensional dense vectors
- Fine-tuned on multilingual data with contrastive loss
- Alternative: AI4Bharat IndicBERT (multilingual ALBERT, 12 languages)

**Vector Storage:**
- Phase 2: PostgreSQL + pgvector extension (free, no new infra)
- Phase 3: Dedicated vector search if queries exceed 10K/day

**Pipeline:**
```
Parliamentary Question → Vyakyarth embedding (768-dim) → pgvector
User Query → Vyakyarth embedding → cosine similarity search → top-K results
```

Generate embeddings in batch on Modal.com (free tier) or GitHub Actions.
Store in pgvector column alongside Typesense full-text index.
Hybrid search: combine Typesense keyword score + pgvector semantic score.

---

## 9. ETL Orchestration

### 9.1 Orchestrator Comparison

| Feature | GitHub Actions | Dagster | Prefect | Airflow |
|---------|---------------|---------|---------|---------|
| Cost (self-hosted) | Free (public repo) | Free (OSS) | Free (OSS) | Free (OSS) |
| Managed free tier | Unlimited (public) | None free | Limited | None |
| Setup complexity | Zero | Medium (needs K8s or Docker) | Low | High |
| Asset-aware | No | **Yes** (core concept) | No | No |
| Data lineage | No | **Yes** | No | Limited |
| Testing | Basic | **Excellent** | Good | Poor |
| Recovery/retry | Basic | Good | **Excellent** | Good |
| Scheduling | Cron syntax | Cron + sensors | Cron + events | Cron |
| Dependency mgmt | Manual (workflow files) | Declarative | Decorators | DAG definition |

### 9.2 Recommended: GitHub Actions (Phase 1-2) + Dagster (Phase 3+)

**Phase 1-2: GitHub Actions as orchestrator**
- Zero cost on public repos
- 20 concurrent jobs, 6-hour timeout per job
- Matrix strategy for parallel processing (e.g., one job per state for election data)
- Cron-triggered schedules for daily/weekly scraping
- Workflow dispatch for ad-hoc runs
- Secrets management built in

**Pipeline structure with GitHub Actions:**
```yaml
# .github/workflows/etl-daily.yml
# Runs daily: scrape Parliament questions, ECI updates

# .github/workflows/etl-weekly.yml
# Runs weekly: re-score politicians, rebuild Parquet files

# .github/workflows/etl-assembly.yml
# Triggered manually: process a state's assembly election data

# .github/workflows/etl-affidavits.yml
# Matrix job: process PDFs in batches of 1000
```

**Phase 3+: Dagster**
- When pipeline count exceeds ~20 and inter-dependencies become complex
- Asset-aware: define "politician_scores" as an asset, Dagster tracks freshness
- Data lineage: visualize which sources feed which outputs
- Self-host on Hetzner VPS (€3.79/mo) alongside Typesense
- Dagster is Apache 2.0 licensed, fully free

### 9.3 Data Pipeline Inventory (50+ sources)

| Pipeline | Frequency | Compute | Duration |
|----------|-----------|---------|----------|
| ECI election results scraper | On-election | GitHub Actions | 2-4 hrs |
| Parliament questions scraper | Daily | GitHub Actions | 30 min |
| MyNeta affidavit download | Monthly | GitHub Actions | 2 hrs |
| Affidavit PDF OCR | Batch (on new PDFs) | Modal.com | 2-10 hrs |
| Sansad audio transcription | Batch | Modal.com | Days (free tier) |
| Assembly election CSV ingest | On-update | GitHub Actions | 1 hr |
| Politician entity resolution | Weekly | GitHub Actions | 1-2 hrs |
| Score computation | Weekly | GitHub Actions | 30 min |
| Parquet file generation (gold layer) | Weekly | GitHub Actions | 1 hr |
| Typesense index rebuild | Weekly | GitHub Actions | 30 min |
| Embedding generation | On new data | Modal.com | 1-2 hrs |
| GeoJSON enrichment | Quarterly | GitHub Actions | 30 min |
| Media monitoring scraper | Daily (future) | GitHub Actions | 1 hr |

---

## 10. Real-time & Streaming

### 10.1 Monitoring Government Websites

**Approach: Polling with Change Detection**

Government websites (Lok Sabha, Rajya Sabha, ECI) do not offer webhooks or real-time APIs. The only viable approach is periodic polling with change detection.

```
Scraper (GitHub Actions cron, every 15 min during sessions)
  → Fetch page → compute checksum
  → Compare with last checksum (stored in PostgreSQL source_records table)
  → If changed: download, parse, store raw in R2, update PostgreSQL
  → Trigger downstream pipelines
```

### 10.2 Message Queue Recommendation

**For Politia's scale, a message queue is NOT needed in Phase 1-2.**

Current data flows are batch-oriented. When real-time becomes necessary:

| Tool | Verdict |
|------|---------|
| Redis Streams | Best if already using Redis (caching). Lightweight, persistent. |
| NATS JetStream | Best for low-latency microservices. Minimal footprint (~30 MB RAM). |
| RabbitMQ | Overkill for this use case. |
| Apache Kafka | Way overkill. Designed for millions of events/sec. |

**Recommendation:** If caching is added (Redis on Render or Upstash), use Redis Streams as the message broker. Otherwise, NATS JetStream for its tiny footprint.

**Upstash Redis (free tier):** 10K commands/day, 256 MB — sufficient for CDC notifications.

### 10.3 Change Data Capture Pattern

```
Government Website
  → Scraper (polling every 15-60 min)
  → Detect changes (checksum comparison)
  → Write to "changes" stream (Redis/NATS)
  → Consumer 1: Update PostgreSQL
  → Consumer 2: Rebuild search index
  → Consumer 3: Send notifications (future)
```

---

## 11. ML/AI Capabilities

### 11.1 Anomaly Detection on Wealth Declarations

**Goal:** Flag politicians with suspicious asset growth between election cycles.

**Approach:**
1. Calculate asset growth rate per politician per cycle
2. Use Isolation Forest (sklearn) to flag outliers
3. Compare against peer group (same state, same party, same office type)
4. Generate "anomaly score" per politician

**Tools:**
- PyOD 2 (45 algorithms, including Isolation Forest, Autoencoders)
- Finomaly (financial-specific anomaly detection)
- ADTK (time-series anomaly detection for year-over-year changes)

**Data required:** DisclosureRecord table (assets, liabilities, filing_year)
**Compute:** CPU only, runs on GitHub Actions
**Output:** anomaly_score field on ScoreRecord

### 11.2 Topic Modeling on Parliamentary Questions

**Goal:** Classify 400K questions into topics (agriculture, defense, health, etc.) and track which MP focuses on what.

**Approach:**
- BERTopic with Vyakyarth/IndicBERT embeddings
- Handles Hindi/English code-switching
- Dynamic topic modeling to track topic evolution over time
- BERTopic consistently outperforms LDA for political text

**Pipeline:**
```
Questions → Vyakyarth embeddings → UMAP dimensionality reduction
  → HDBSCAN clustering → BERTopic topic extraction
  → Topic labels: "Agricultural Pricing", "Defense Budget", etc.
  → Per-MP topic distribution
```

**Compute:** Embedding generation on Modal.com; clustering on GitHub Actions (CPU)

### 11.3 Sentiment Analysis on Debate Transcripts

**Goal:** Gauge tone of parliamentary debates (aggressive, constructive, etc.)

**Tools:**
- AI4Bharat IndicBERT fine-tuned for sentiment (Hindi/English)
- Zero-shot classification with multilingual models
- Applied to Sansad transcripts (after Stage 7 processing)

### 11.4 Named Entity Recognition (NER)

**Goal:** Extract mentioned entities from parliamentary text (people, places, policies, bills).

**Tools:**
- AI4Bharat IndicNER (trained on Indian languages)
- spaCy with custom Indian political entity patterns
- Link extracted entities to Politia's politician/constituency database

### 11.5 Vote Prediction Models

**Goal:** Predict election outcomes based on historical patterns, attendance, financial disclosures.

**Approach:** Gradient boosting (XGBoost/LightGBM) with features:
- Incumbent advantage
- Asset growth
- Attendance record
- Criminal case count
- Margin of victory in last election
- Party swing in state

**All ML runs on CPU. No GPU needed except for embedding generation.**

---

## 12. GeoJSON & Mapping

### 12.1 Data Sources

| Source | Coverage | Format |
|--------|----------|--------|
| DataMeet Community Maps | 543 LS + 4000+ AC | GeoJSON, Shapefile |
| ECI boundary data | Post-delimitation | KML (convert to GeoJSON) |
| Hindustan Times Labs | Assembly constituency | JSON, KML (GitHub) |
| ML Infomap | Pre/post-delimitation | Shapefile |

### 12.2 Architecture

```
GeoJSON files (stored on Cloudflare R2, ~500 MB)
  → Served directly via R2 public bucket (zero egress cost)
  → Frontend: Mapbox GL JS / MapLibre GL JS (free, open-source)
  → Tile generation: tippecanoe for vector tiles (PMTiles format)
  → PMTiles hosted on R2 — single file, HTTP range requests

Demographic Overlays:
  → Census data joined with constituency boundaries
  → Pre-computed as properties in GeoJSON
  → Or served as separate data layer from PostgreSQL/DuckDB
```

**PMTiles on Cloudflare R2** = zero-cost map hosting. No tile server needed.

### 12.3 Cost

| Component | Cost |
|-----------|------|
| GeoJSON storage (R2) | $0 (within 10 GB free) |
| PMTiles hosting | $0 (R2 free tier) |
| MapLibre GL JS | $0 (open source) |
| Tile generation | $0 (tippecanoe on GitHub Actions) |

---

## 13. Free Tier Limits & Breaking Points

### 13.1 When Each Free Tier Breaks

| Service | Free Limit | Breaking Point | Trigger |
|---------|-----------|----------------|---------|
| **Neon PostgreSQL** | 0.5 GB storage | ~1.5-2M records | Adding parliamentary questions with full text |
| **Render (backend)** | 750 hrs/mo, sleeps after 15 min | Any production traffic needing instant response | Users hitting sleeping service = 10-30s cold start |
| **Vercel (frontend)** | 100 GB bandwidth, 4 hrs CPU | ~50K monthly visitors with heavy map usage | GeoJSON tile requests eat bandwidth fast |
| **Cloudflare R2** | 10 GB storage | Storing >10 GB of PDFs/audio | Affidavit PDF batch exceeds 10 GB |
| **GitHub Actions** | Unlimited (public), 2K min (private) | Private repo exceeds 2K min/month | Keep repo public to avoid this |
| **Modal.com** | $30/mo credits | GPU-heavy months (audio transcription) | 17K hours of audio needs ~$43+ total |

### 13.2 First Paid Tier Costs

| Service | First Paid Tier | Monthly Cost |
|---------|----------------|-------------|
| Neon PostgreSQL (Launch) | 10 GB storage, 300 CU-hrs | ~$19/mo |
| Render (Starter) | 512 MB RAM, no sleep | $7/mo |
| Vercel (Pro) | 1 TB bandwidth, 1000 hrs CPU | $20/mo |
| Cloudflare R2 (Pay-as-go) | $0.015/GB/mo + operations | ~$1-15/mo |
| Hetzner VPS (CX22) | 2 vCPU, 4 GB RAM | ~€3.79/mo |
| Hetzner Storage Box (1 TB) | 1 TB, unlimited transfer | €4.50/mo |

### 13.3 Critical Path to Paid

The **first service to need upgrading** will be Render, because the 15-minute sleep timeout makes the API unusable for real users (10-30 second cold starts).

**Priority order for paid upgrades:**
1. **Render → Hetzner VPS (€3.79/mo):** Self-host FastAPI with uvicorn. Always-on. 4 GB RAM. Also hosts Typesense.
2. **Neon → Self-hosted PostgreSQL on same Hetzner VPS ($0 incremental):** No storage limit.
3. **R2 paid ($1-15/mo):** When raw data exceeds 10 GB.
4. **Hetzner Storage Box (€4.50/mo):** When audio/PDF archive exceeds 100 GB.

**Total minimum paid infrastructure: ~€12/mo (~$13/mo)**

---

## 14. Zero-Budget Architecture

### 14.1 Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│ ECI      │ Lok Sabha│ MyNeta   │ Sansad   │ DataMeet │ News     │
│ Elections│ Questions│ PDFs     │ Audio    │ Maps     │ (Future) │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘
     │          │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│               INGESTION LAYER (GitHub Actions)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ Scrapers │ │ CSV      │ │ PDF      │ │ Audio Downloader │   │
│  │ (httpx,  │ │ Parsers  │ │ Download │ │ (HuggingFace)    │   │
│  │ bs4)     │ │ (Polars) │ │          │ │                  │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────────────┘   │
└───────┼────────────┼────────────┼─────────────┼─────────────────┘
        │            │            │             │
        ▼            ▼            ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RAW ZONE (Cloudflare R2)                       │
│  raw/elections/  raw/questions/  raw/pdfs/  raw/audio/           │
│  raw/maps/       raw/media/                                      │
└───────┬────────────┬────────────┬─────────────┬─────────────────┘
        │            │            │             │
        ▼            ▼            ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│              PROCESSING LAYER                                    │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │ GitHub Actions  │  │ Modal.com      │  │ GitHub Actions   │   │
│  │ (CPU tasks)     │  │ (GPU tasks)    │  │ (Analytics)      │   │
│  │                 │  │                │  │                  │   │
│  │ - CSV → Parquet │  │ - PDF OCR      │  │ - DuckDB queries │   │
│  │ - Entity resol. │  │   (Surya/      │  │ - Polars joins   │   │
│  │ - Score calc    │  │    PaddleOCR)  │  │ - Aggregations   │   │
│  │ - Web scraping  │  │ - Whisper      │  │ - Score compute  │   │
│  │                 │  │   transcription│  │                  │   │
│  │                 │  │ - Embeddings   │  │                  │   │
│  │                 │  │   (Vyakyarth)  │  │                  │   │
│  └────────┬───────┘  └────────┬───────┘  └────────┬─────────┘   │
└───────────┼───────────────────┼───────────────────┼─────────────┘
            │                   │                   │
            ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CURATED ZONE (Cloudflare R2)                    │
│                                                                  │
│  bronze/                silver/                gold/              │
│  ├── elections.parquet  ├── enriched_          ├── scores.parquet │
│  ├── questions.parquet  │   elections.parquet  ├── rankings.pqt  │
│  ├── affidavits.parquet ├── politician_        ├── topics.parquet │
│  ├── transcripts.pqt    │   profiles.parquet   ├── anomalies.pqt │
│  └── maps.geojson       └── questions_         └── api_cache.pqt │
│                             enriched.parquet                     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SERVING LAYER                                │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ PostgreSQL (Neon) │  │ Typesense    │  │ Cloudflare R2    │   │
│  │                   │  │ (search)     │  │ (static assets)  │   │
│  │ - Politicians     │  │              │  │                  │   │
│  │ - Elections (hot) │  │ - Questions  │  │ - GeoJSON/       │   │
│  │ - Scores          │  │ - Politicians│  │   PMTiles        │   │
│  │ - Disclosures     │  │ - Fuzzy name │  │ - Gold Parquet   │   │
│  │ - pgvector        │  │   search     │  │   files          │   │
│  │   (embeddings)    │  │              │  │ - PDF downloads  │   │
│  └────────┬─────────┘  └──────┬───────┘  └────────┬─────────┘   │
│           │                   │                    │             │
│           ▼                   ▼                    ▼             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              FastAPI Backend (Render / Hetzner)          │    │
│  │                                                         │    │
│  │  /api/politicians  /api/search  /api/maps  /api/scores  │    │
│  │  /api/questions    /api/anomalies  /api/topics          │    │
│  └────────────────────────────┬────────────────────────────┘    │
└───────────────────────────────┼─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│               FRONTEND (Vercel / Next.js)                        │
│                                                                  │
│  - Politician profiles with scores                               │
│  - Constituency maps (MapLibre + PMTiles)                        │
│  - Search (Typesense JS client → direct to Typesense)            │
│  - Parliamentary question explorer                               │
│  - Anomaly dashboard                                             │
│  - Election history visualization                                │
└─────────────────────────────────────────────────────────────────┘
```

### 14.2 Technology Stack Summary

| Layer | Technology | Cost |
|-------|-----------|------|
| **Object Storage** | Cloudflare R2 | $0 (10 GB free) |
| **OLTP Database** | PostgreSQL on Neon | $0 (0.5 GB free) |
| **Analytics Engine** | DuckDB (in-process) | $0 |
| **Data Processing** | Polars + DuckDB | $0 |
| **ETL Orchestration** | GitHub Actions | $0 (public repo) |
| **GPU Compute** | Modal.com | $0 ($30/mo credits) |
| **Full-Text Search** | PostgreSQL pg_trgm → Typesense | $0 → €3.79/mo |
| **Semantic Search** | pgvector + Vyakyarth embeddings | $0 |
| **OCR** | Surya + PaddleOCR | $0 |
| **Transcription** | Whisper Large V3 + pyannote | $0 (Modal credits) |
| **Topic Modeling** | BERTopic + Vyakyarth | $0 |
| **Anomaly Detection** | PyOD / Isolation Forest | $0 |
| **Maps** | MapLibre GL + PMTiles on R2 | $0 |
| **Backend** | FastAPI on Render | $0 |
| **Frontend** | Next.js on Vercel | $0 |
| **Message Queue** | Upstash Redis (when needed) | $0 (free tier) |
| **TOTAL Phase 1** | | **$0/month** |

---

## 15. Phased Implementation Roadmap

### Phase 1: Foundation (Months 1-2) — $0/month

**Goal:** Lakehouse skeleton, expanded data ingestion, DuckDB analytics

**Tasks:**
1. Set up Cloudflare R2 bucket with raw/bronze/silver/gold zones
2. Convert existing CSV data to Parquet (Polars scripts)
3. Ingest datameet assembly.csv (398K records) → bronze/elections.parquet
4. Ingest existing affidavit CSV (27K records) → bronze/affidavits.parquet
5. Set up DuckDB analytics scripts (election cross-tabulations)
6. Create GitHub Actions ETL pipelines for:
   - Daily Parliament question scraper
   - Weekly score recomputation
   - Parquet file generation
7. Migrate data processing from Pandas to Polars
8. Keep PostgreSQL (Neon) for API-serving hot data only

**Deliverables:**
- Lakehouse structure on R2
- 500K+ records in Parquet format
- Automated daily/weekly pipelines
- DuckDB analytics layer

### Phase 2: Search + Maps (Months 3-4) — $0/month

**Goal:** Full-text search, constituency maps, parliamentary questions

**Tasks:**
1. Build Parliament question scraper (PDF parser + web scraper)
2. Ingest 400K+ questions → Parquet → PostgreSQL (or Typesense)
3. Implement pg_trgm full-text search on questions table
4. Process DataMeet GeoJSON files → PMTiles → R2
5. Build MapLibre constituency map component
6. Generate Vyakyarth embeddings for questions (Modal.com)
7. Store embeddings in pgvector for semantic search
8. Add ScoreRecord anomaly detection (PyOD)

**Deliverables:**
- Searchable parliamentary question database
- Interactive constituency maps
- Semantic search ("farmer distress" finds "agricultural crisis")
- Anomaly flags on politician wealth declarations

### Phase 3: PDF + Audio Processing (Months 5-8) — $0-30/month

**Goal:** OCR all affidavits, start audio transcription

**Tasks:**
1. Download 50K MyNeta PDFs → R2 raw zone
2. Classify PDFs (digital vs scanned, language)
3. OCR pipeline: pdfplumber (digital) + Surya (scanned) on Modal.com
4. Structured extraction: regex templates for affidavit fields
5. Cross-reference with existing 27K structured records
6. Begin Sansad audio transcription:
   - Clean existing 8.5K hours of weak transcripts (CPU)
   - Transcribe remaining with Whisper on Modal.com ($30/mo credit)
7. Speaker diarization with pyannote.audio 4.0
8. Topic modeling with BERTopic on question corpus

**Deliverables:**
- 50K affidavits digitized and structured
- 8.5K hours of cleaned parliamentary transcripts
- Speaker-attributed debate transcripts (in progress)
- Topic analysis per MP

### Phase 4: Scale + Self-Host (Months 9-12) — ~$13/month

**Goal:** Production-grade infrastructure, full data platform

**Tasks:**
1. Provision Hetzner VPS (CX22, €3.79/mo)
2. Self-host: FastAPI + PostgreSQL + Typesense on single VPS
3. Migrate from Render free tier (eliminate cold starts)
4. Migrate from Neon to self-hosted PostgreSQL (eliminate 0.5 GB limit)
5. Deploy Typesense with full question + politician index
6. Add Hetzner Storage Box (€4.50/mo) for audio archive
7. Complete remaining audio transcription
8. Build media monitoring pipeline (RSS + news scraping)
9. Implement vote prediction models
10. NER on parliamentary proceedings

**Deliverables:**
- Always-on API (no cold starts)
- Full-text + semantic search
- 17K hours of transcribed parliamentary audio
- Complete ML feature suite
- 1B+ queryable records (via DuckDB + Parquet)

### Phase 5: Growth (Year 2+) — $20-50/month

**Goal:** Handle real traffic, add real-time features

**Tasks:**
1. Add Redis caching layer (Upstash or self-hosted)
2. Implement CDC with Redis Streams or NATS
3. Real-time Parliament session monitoring
4. Booth-level voting data (900M+ voter interactions)
5. Consider ClickHouse if analytical query load justifies it
6. CDN optimization for map tiles
7. Scale Hetzner VPS if needed (CX32: €7.59/mo)

---

## 16. Cost Projections

### Monthly Cost by Phase

| Phase | Timeline | Monthly Cost | Cumulative Data |
|-------|----------|-------------|-----------------|
| Phase 1 | Month 1-2 | **$0** | 500K records, 2 GB |
| Phase 2 | Month 3-4 | **$0** | 1M records, 10 GB |
| Phase 3 | Month 5-8 | **$0-30** (Modal GPU) | 2M records, 300 GB |
| Phase 4 | Month 9-12 | **~$13** | 5M+ records, 1 TB |
| Phase 5 | Year 2+ | **$20-50** | 1B+ records, 3+ TB |

### Cost Comparison: Politia vs Enterprise Approach

| Component | Enterprise Cost | Politia Cost |
|-----------|----------------|-------------|
| Data warehouse (Snowflake/BigQuery) | $500-5,000/mo | $0 (DuckDB + Parquet) |
| Search (Algolia/Elastic Cloud) | $100-500/mo | $0-4/mo (Typesense) |
| ETL (Fivetran/dbt Cloud) | $200-2,000/mo | $0 (GitHub Actions) |
| Object storage (AWS S3) | $50-500/mo | $0-15/mo (R2) |
| Audio transcription (managed) | $6,120/17K hrs | $43-100 (self-hosted Whisper) |
| OCR (Google Vision) | $75/50K pages | $0-30 (Surya/PaddleOCR) |
| GPU compute (AWS) | $500+/mo | $0 (Modal free tier) |
| VPS/hosting | $100-500/mo | $0-13/mo |
| **Total** | **$1,500-9,000/mo** | **$0-50/mo** |

### Production-Grade Deployment (Full Vision)

If money were no object, a production deployment for all 8 data sources with real-time capabilities and high availability:

| Component | Spec | Monthly Cost |
|-----------|------|-------------|
| Hetzner CX32 VPS (app + DB) | 4 vCPU, 8 GB RAM | €7.59 |
| Hetzner Storage Box 5TB | Audio + PDF archive | €15.50 |
| Cloudflare R2 (200 GB hot) | Serving layer | $3.00 |
| Domain + Cloudflare proxy | DDoS, CDN | $0 |
| Modal.com | GPU bursts | $0-30 |
| **Total production** | | **~$30-55/month** |

---

## Appendix A: Key Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Analytics engine | DuckDB over Spark/Trino | Single-machine, zero-config, faster for <500 GB |
| Dataframe library | Polars over Pandas | 3-10x faster, 80% less memory |
| Search engine | Typesense over Elasticsearch | 1/10th resource usage, faster, simpler |
| OCR engine | Surya + PaddleOCR over Tesseract | Better Hindi support, layout-aware, table extraction |
| Transcription | Whisper + pyannote over Google STT | Free, better Hindi/English code-switching |
| Embedding model | Vyakyarth-1-Indic over sentence-transformers | Purpose-built for Indian languages |
| Topic model | BERTopic over LDA | Higher quality topics, handles multilingual text |
| Orchestrator | GitHub Actions over Airflow | Zero cost, sufficient for 50+ pipelines |
| Object storage | Cloudflare R2 over S3/B2 | Zero egress, generous free tier |
| VPS (when needed) | Hetzner over AWS/GCP | 5-10x cheaper for equivalent specs |
| Lakehouse format | Parquet files (DuckDB-native) | Simplest, no server needed. Consider DuckLake when it matures |
| Vector search | pgvector over Pinecone/Weaviate | Free, lives in existing PostgreSQL |
| Maps | MapLibre + PMTiles over Mapbox | Fully open source, zero tile server cost |

## Appendix B: Data Model Evolution

### New Tables/Entities for Target State

```
-- Booth-level voting (partitioned by state)
booth_results (booth_id, constituency_id, state, election_year,
               candidate_name, party, votes, total_voters)

-- Parliamentary questions
parliamentary_questions (id, session, question_type, member_id,
                        ministry, subject, full_text, date_asked,
                        answer_text, embedding vector(768))

-- Affidavit structured data (expanded from DisclosureRecord)
affidavit_details (id, politician_id, election_year,
                   movable_assets, immovable_assets, total_assets,
                   total_liabilities, criminal_cases_pending,
                   criminal_cases_convicted, education, profession,
                   source_pdf_url, ocr_confidence, extraction_method)

-- Parliamentary transcripts
transcripts (id, session_id, speaker_id, start_time, end_time,
            text, language, confidence, topic_id)

-- Topic model outputs
topics (id, label, keywords, description, model_version)
question_topics (question_id, topic_id, score)
mp_topics (politician_id, topic_id, question_count, session_range)

-- Anomaly flags
anomaly_flags (id, politician_id, flag_type, description,
              severity, detection_method, detected_at)

-- GeoJSON references
constituency_geo (constituency_id, geojson_url, centroid_lat,
                 centroid_lng, area_sq_km, population, literacy_rate)
```

## Appendix C: Similar Platforms & Case Studies

| Platform | Country | Approach | Scale |
|----------|---------|----------|-------|
| **CivicDataLab** | India | CKAN + Next.js + Python + D3 | Open data for governance |
| **CIVIC Platform** | USA (Portland) | Open data analytics, volunteer-built | Community data platform |
| **Lok Dhaba** (Ashoka Univ) | India | Parliamentary questions searchable | ~100K questions |
| **Decide Madrid** | Spain | Open source civic participation | 100+ cities, UN award |
| **TheyWorkForYou** | UK | Parliament monitoring | 20+ years of data |
| **OpenSecrets** | USA | Political money tracking | Billions in contributions |

## Appendix D: Reference Links & Sources

### Storage Pricing
- [Cloudflare R2 vs Backblaze B2 Comparison (2026)](https://themedev.net/blog/cloudflare-r2-vs-backblaze-b2/)
- [Cloudflare R2 Pricing](https://developers.cloudflare.com/r2/pricing/)
- [Backblaze B2 Pricing](https://www.backblaze.com/cloud-storage/pricing)
- [Hetzner Storage Box Pricing](https://www.hetzner.com/storage/storage-box/)
- [Hetzner Cloud VPS Pricing](https://costgoat.com/pricing/hetzner)

### Database & Analytics
- [How to Optimize PostgreSQL for Billion-Row Tables](https://oneuptime.com/blog/post/2026-01-25-postgresql-optimize-billion-row-tables/view)
- [PostgreSQL Partitioning for Billion-Row Tables (2026)](https://www.youngju.dev/blog/database/2026-03-07-database-postgresql-partitioning-billion-row-tables.en)
- [ClickHouse vs DuckDB 2026 Comparison](https://tasrieit.com/blog/clickhouse-vs-duckdb-2026)
- [DuckLake: SQL as a Lakehouse Format](https://duckdb.org/2025/05/27/ducklake)
- [DuckDB Medallion Lakehouse Pattern](https://github.com/datatomas/duckdb-medallion)

### Search
- [Typesense System Requirements](https://typesense.org/docs/guide/system-requirements.html)
- [PostgreSQL Full-Text Search Limitations](https://blog.meilisearch.com/postgres-full-text-search-limitations/)
- [Typesense vs Algolia vs Elasticsearch vs Meilisearch](https://typesense.org/typesense-vs-algolia-vs-elasticsearch-vs-meilisearch/)

### OCR & PDF Processing
- [8 Top Open-Source OCR Models Compared](https://modal.com/blog/8-top-open-source-ocr-models-compared)
- [Surya OCR (90+ languages)](https://github.com/datalab-to/surya)
- [PaddleOCR (109 languages)](https://github.com/PaddlePaddle/PaddleOCR)
- [7 Best Open-Source OCR Models 2025](https://www.e2enetworks.com/blog/complete-guide-open-source-ocr-models-2025)

### Audio Transcription
- [Whisper Large V3 Benchmark: 1M hours for $5110](https://blog.salad.com/whisper-large-v3/)
- [kalpalabs/sansad Dataset](https://huggingface.co/datasets/kalpalabs/sansad)
- [pyannote.audio 4.0 Speaker Diarization](https://www.pyannote.ai/blog/community-1)
- [WhisperX Benchmarks](https://brasstranscripts.com/blog/whisperx-vs-competitors-accuracy-benchmark)

### ML/AI
- [BERTopic for Political Discourse](https://arxiv.org/abs/2510.22904)
- [Vyakyarth-1-Indic-Embedding](https://ai-labs.olakrutrim.com/models/Vyakyarth-1-Indic-Embedding)
- [AI4Bharat Indic NLP Catalog](https://github.com/AI4Bharat/indicnlp_catalog)
- [PyOD 2: Outlier Detection Library](https://dl.acm.org/doi/10.1145/3701716.3715196)
- [Mann Ki Baat Topic Modeling (LDA vs BERTopic)](https://link.springer.com/content/pdf/10.1007/978-981-96-0692-4_18.pdf)

### Platform Tiers
- [Neon Plans & Pricing](https://neon.com/docs/introduction/plans)
- [Render Pricing](https://render.com/pricing)
- [Vercel Pricing](https://vercel.com/pricing)
- [Modal.com Pricing](https://modal.com/pricing)
- [GitHub Actions Billing](https://docs.github.com/en/actions/concepts/billing-and-usage)

### Data Sources
- [DataMeet India Election Data](https://github.com/datameet/india-election-data)
- [DataMeet Community Maps (GeoJSON)](https://projects.datameet.org/maps/)
- [MyNeta.info](https://www.myneta.info/)
- [Lok Sabha Questions Scraper](https://github.com/sammitjain/loksabha-questions)
- [Parliamentary Questions (Lok Dhaba)](https://qh.lokdhaba.ashoka.edu.in/)
- [OGD Platform India](https://www.data.gov.in/)

### Compute & Infrastructure
- [Polars vs Pandas 2026 Benchmarks](https://tildalice.io/polars-vs-pandas-2026-benchmarks/)
- [GitHub Actions 2026 Pricing Changes](https://resources.github.com/actions/2026-pricing-changes-for-github-actions/)
- [Dagster Open Source](https://github.com/dagster-io/dagster)
- [NATS vs Kafka vs Redis Streams](https://www.javacodegeeks.com/2026/03/nats-vs-kafka-vs-redis-streams-for-java-microservices-when-simpler-actually-wins.html)

### Civic Tech Case Studies
- [CivicDataLab: Open Data Platforms in India](https://ckan.org/blog/civic-data-lab-pioneering-open-data-platforms-in-india)
- [CIVIC Platform](https://civicplatform.org/)
- [Awesome Civic Tech (GitHub)](https://github.com/awesomelistsio/awesome-civic-tech)
