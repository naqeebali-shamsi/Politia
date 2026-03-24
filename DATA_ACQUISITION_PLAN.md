# Politia — Data Acquisition Master Plan

## Research Summary (2026-03-23)

All data sources for Indian MP accountability have been mapped. The landscape is far better than expected — significant structured datasets already exist on GitHub, Kaggle, and academic portals. We do NOT need to build everything from scratch.

---

## Phase 1: Immediate Downloads (Day 1 — No Scraping Required)

These datasets are structured, downloadable, and cover the core data needs:

### 1.1 MP Legislative Activity (Attendance, Questions, Debates, Bills)
| Dataset | Source | Format | Coverage |
|---------|--------|--------|----------|
| **Vonter/india-representatives-activity** | GitHub | JSON + CSV | PRS India data — attendance, debates, questions, private bills per Lok Sabha |
| **data.gov.in — Attendance** | OGD Portal | CSV/ZIP | Session-wise attendance per Lok Sabha |
| **data.gov.in — Committee Membership** | OGD Portal | CSV | Committee assignments per MP |
| **data.gov.in — Parliamentary Bills** | OGD Portal | CSV/ZIP | Bills introduced, private member bills |
| **sammitjain/loksabha-questions** | GitHub | Dataset | Lok Sabha questions parsed from PDFs |
| **TCPD-IPD** | Ashoka University | CSV | All questions & answers 1999-2019 |

### 1.2 Election Results & Candidate Data
| Dataset | Source | Format | Coverage |
|---------|--------|--------|----------|
| **datameet/india-election-data** | GitHub | CSV | `parliament.csv` — ALL Lok Sabha results + `assembly.csv` |
| **TCPD-IED** | Ashoka/LokDhaba | CSV | Election results 1962-present with unique politician IDs |
| **Kaggle 2024 complete** | Kaggle | CSV | 2024 Lok Sabha constituency-wise results |
| **Harvard Dataverse** | Academic | CSV | Candidate-level data 1977-2015 |

### 1.3 Candidate Affidavits (Criminal Cases, Assets, Liabilities)
| Dataset | Source | Format | Coverage |
|---------|--------|--------|----------|
| **bkamapantula/parliamentary-candidates-affidavit-data** | GitHub | CSV | 2004-2019 Lok Sabha, richest field set, has `unique_id` |
| **Vonter/india-election-affidavits** | GitHub | CSV | Multi-election affidavit data |
| **datameet affidavits** | GitHub | CSV | 2004, 2009, 2014 MyNeta-sourced |

### 1.4 MP Profiles & Identity
| Dataset | Source | Format | Coverage |
|---------|--------|--------|----------|
| **OpenSanctions — in_sansad** | OpenSanctions | JSON + tabular | All current LS + RS members |
| **in-rolls/indian-politician-bios** | GitHub | Scraped data | Biographical data from archive.india.gov.in + MyNeta |

### 1.5 Constituency Geography
| Dataset | Source | Format | Coverage |
|---------|--------|--------|----------|
| **india-geodata** | GitHub | GeoJSON | 543 Lok Sabha + State Assembly boundaries |
| **HindustanTimesLabs/parliament-shape-scrape** | GitHub | GeoJSON | Parliamentary constituency boundaries from ECI |

---

## Phase 2: Targeted Scraping (Days 2-7)

For data NOT available as downloads, build lightweight scrapers:

### 2.1 MyNeta.info — 2024 Lok Sabha Affidavits
- **Why:** Pre-scraped datasets cover up to 2019. Need 2024 data.
- **Approach:** httpx + BeautifulSoup4 (structured HTML, very scrape-friendly)
- **Fields:** 22+ per candidate (criminal cases, assets, liabilities, education, profession, PAN/IT)
- **URL pattern:** `myneta.info/LokSabha2024/candidate.php?candidate_id={ID}`
- **Reference scraper:** kracekumar/myneta (Python CLI)
- **Estimated effort:** 1-2 days
- **Legal risk:** LOW (public government data, ADR's mission is open access)

### 2.2 PRS India — Current 18th Lok Sabha Data
- **Why:** Vonter's dataset may not have latest session data
- **Approach:** httpx + BeautifulSoup4
- **URL pattern:** `prsindia.org/mptrack/18th-lok-sabha/{name-slug}`
- **Fields:** Attendance %, questions count, debates count, bills introduced
- **Reference:** Vonter/india-representatives-activity scraper code
- **Estimated effort:** 1-2 days

### 2.3 sansad.in — Official MP Profiles (If Needed)
- **Challenge:** ASP.NET ViewState forms, requires Playwright/Selenium
- **Fields:** Bio-data, constituency info, participation stats
- **Estimated effort:** 2-3 days (harder due to JS rendering)
- **Recommendation:** SKIP for MVP if OpenSanctions + PRS covers profile needs

---

## Phase 3: Entity Resolution (Days 5-8, Overlaps with Phase 2)

The hardest problem: matching politicians across different data sources.

### Strategy:
1. **Primary key:** Use TCPD-IED's `unique_id` as the canonical politician identifier (tracks careers across elections)
2. **Secondary matching:** RapidFuzz (Jaro-Winkler for names, Token Sort for reordered names)
3. **Tertiary:** dedupe library for ML-based multi-field matching (name + constituency + party + year)
4. **Manual alias table:** For known high-profile variants and transliteration differences

### Indian Name Challenges:
- Strip titles: "Shri", "Smt.", "Dr.", "Adv."
- Handle transliterations: "Sharma" / "Sharman" / "Sarmaa"
- Handle reordering: "Narendra Modi" vs "Modi, Narendra"
- Constituency name variants across sources

---

## Tech Stack (Zero Budget)

| Layer | Tool | Cost |
|-------|------|------|
| **Scraping** | httpx + BeautifulSoup4 + Playwright (JS fallback) | Free |
| **PDF Parsing** | pdfplumber + Camelot | Free |
| **Database** | PostgreSQL on Neon | Free (0.5 GB, auto-suspend) |
| **Search** | PostgreSQL FTS + pg_trgm | Free (built-in) |
| **Backend API** | FastAPI on Render | Free (750 hrs/mo) |
| **Frontend** | Next.js on Vercel | Free |
| **Artifact Storage** | Cloudflare R2 | Free (10 GB, zero egress) |
| **Entity Resolution** | RapidFuzz + dedupe | Free |
| **Nightly Jobs** | GitHub Actions cron | Free (public repo) |
| **Total** | | **$0/month** |

---

## Data Schema Overview (Maps to PRD Section 13)

```
politicians         — Canonical person record (name, name_variants[], photo_url)
offices             — MP terms (chamber, constituency, party, term_start, term_end, active)
constituencies      — Name, chamber, state, geo_data
election_records    — Year, constituency, party, result, votes, margin, affidavit_link
activity_records    — Attendance%, questions, debates, committees, session, source
disclosure_records  — Assets, liabilities, criminal_cases, education, affidavit_source
source_records      — Raw URL, snapshot_url (R2), checksum, fetch_ts, parser_version
score_records       — Overall, participation, disclosure, integrity, formula_version, computed_ts
```

---

## Priority Order for MVP Data

1. **MP Identity + Profiles** — OpenSanctions + in-rolls bios → `politicians` + `offices`
2. **Election Results** — datameet parliament.csv + TCPD-IED → `election_records`
3. **Legislative Activity** — Vonter's PRS data + data.gov.in attendance → `activity_records`
4. **Affidavits** — bkamapantula CSVs (2004-2019) + MyNeta scrape (2024) → `disclosure_records`
5. **Scoring** — Compute from activity + disclosure data → `score_records`
6. **Constituency Maps** — india-geodata GeoJSON → `constituencies`

---

## Key GitHub Repositories (Bookmarked)

### Must-Use (Pre-scraped Data)
- https://github.com/Vonter/india-representatives-activity
- https://github.com/datameet/india-election-data
- https://github.com/bkamapantula/parliamentary-candidates-affidavit-data
- https://github.com/Vonter/india-election-affidavits
- https://github.com/tcpd (TCPD datasets)

### Useful Scrapers (Reference Code)
- https://github.com/kracekumar/myneta
- https://github.com/thecont1/india-votes-data
- https://github.com/saurabhp75/netainfo
- https://github.com/anon-d3v/know-your-neta

### Constituency Maps
- https://github.com/yashveeeeeer/india-geodata
- https://github.com/HindustanTimesLabs/parliament-shape-scrape

### Supplementary
- https://github.com/sammitjain/loksabha-questions
- https://github.com/in-rolls/indian-politician-bios
- https://opensanctions.org/datasets/in_sansad/
- https://lokdhaba.ashoka.edu.in/

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Pre-scraped datasets may be outdated | Verify freshness, supplement with targeted scraping |
| Entity resolution errors (bad joins) | Start with TCPD unique IDs, manual review for top 543 MPs |
| Government site structure changes | Cache raw artifacts in R2, version all parsers |
| Neon free tier limits (0.5 GB) | Sufficient for ~50K records; upgrade only if needed |
| Render cold starts (30s) | Acceptable for MVP; cache hot paths |
| Rate limiting on scrape targets | 2-5 second delays, respect robots.txt |
