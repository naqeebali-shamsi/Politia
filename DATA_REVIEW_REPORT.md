# Politia Data Meaningfulness & Richness Review

**Date:** 2026-03-24
**Methodology:** 8 specialist agents performed independent forensic analysis against the SQLite database (57,240 politicians, 74,810 elections, 10,342 disclosures, 1,458 activity records, 57,240 scores)

---

## Executive Summary

The data that exists is **publication-quality accurate** (within 0.01% of known national vote totals, exact seat count matches). The insights mined from it are **genuinely newsworthy** (crime-pays-at-the-ballot-box, Scindia's 104x wealth growth, crorepati quadrupling). But the way we're currently presenting it has **three critical problems** that must be fixed before launch:

1. **The 2014-2024 election gap** — the most recent 15 years of elections are missing
2. **98.8% of scores are meaningless** — 41,473 politicians share the exact score of 17.50
3. **7.6% of election records are corrupted** by entity over-merging

---

## WHAT'S GOLD (Keep & Amplify)

### Election Data (1951-2009): Publication Quality
- 74,810 records across 17 election years
- INC 2009 seat count: exact 206 match
- National vote totals: within 0.01% of known figures
- All major state seat allocations: exact matches
- Historical edge cases correct (1985 Assam delayed election, 1992 Punjab, multi-member constituencies)

### Disclosure Data: Investigative Gold
- Crorepati trend: 12.6% (2004) → 45.7% (2019) — real, verifiable, newsworthy
- Criminal case winners: 2.3x win rate vs clean candidates
- Scindia 104x wealth growth, Chidambaram 99.7% asset "disappearance"
- Top 50 richest candidates with exact figures
- Party-level criminal case rankings (Shiv Sena highest at 2.33 avg)

### Activity Data: Genuine Differentiation (for the 1,010 MPs who have it)
- 868 distinct scores out of 1,010 MPs — excellent differentiation
- Range: 17.5 to 85.28 — real spread
- Bhairon Prasad Mishra: 100% attendance, 2,095 debates — genuinely exceptional
- 147 "Ghost MPs" who never spoke — real, verifiable finding
- First-timers 40% more active than veterans — genuine pattern

### Cross-Dimensional Insights
- Communist MPs: poorest (0.3 Cr avg) but most disciplined (85% attendance)
- TMC: worst attendance of any major party (63.7%)
- Criminals ask 17% MORE questions than clean MPs
- Chhindwara: 58 years of unbroken INC victories

---

## WHAT'S GARBAGE (Fix or Remove)

### Scores for Data-Less Politicians: MISLEADING
- **41,473 politicians (72.5%) have the exact same score: 17.50**
- This score means "we have zero data" but is displayed as a real number
- Only 670 politicians (1.2%) have genuinely meaningful multi-dimensional scores
- The intended 60/25/15 weighting effectively becomes **2/25/72** due to missing participation data

### Ghost Fields in the Scoring Formula
- **committee_memberships: ALL ZEROS** across every record — carries 9% of total score weight
- **pan_declared: 0% populated** — carries weight in disclosure score
- **serious_criminal_cases: 0% populated** — integrity formula references it but it's always 0
- These ghost fields cap the maximum achievable score and dilute results

### 100% Null Fields
- **date_of_birth: NULL for every record**
- **photo_url: NULL for every record**

---

## WHAT'S DANGEROUS (Fix Before Launch)

### Entity Over-Merging: Data Corruption
- **460 politicians** have election records from 6+ different constituencies — clearly multiple people merged
- "OM PRAKASH" has 79 elections from 63 constituencies spanning 6 decades — ~30 different people
- **5,721 election records (7.6%)** are attached to the wrong politician
- **2,427 politicians** have elections in multiple states — many are false merges

### Entity Under-Matching: Lost Data
- **62.3% of affidavit data was lost** during ingestion (17K out of 27K rows)
- PRS match rate decays from 94% (15th LS) to 50% (18th LS)
- 30+ confirmed duplicate pairs from DR./SHRI title handling
- 20 of 30 sampled unmatched 2009 winners had close fuzzy matches — normalization failures

### False Matches in Disclosures
- **237 disclosure records from 2014** are linked to politicians whose last election was pre-2000
- These are almost certainly different people with common Indian names
- Example: "NARINDER SINGH" from Punjab — 2014 affidavit linked to a 1962-1999 politician

### Legacy State Names
- 269 constituencies under BOMBAY, MADRAS, MYSORE, HYDERABAD not mapped to modern states
- BOMBAY NORTH and MUMBAI NORTH exist as separate constituency records

---

## ACTION ITEMS (Priority Order)

### P0: Critical (Before Credible Launch)

1. **Ingest 2014/2019/2024 election results**
   - Kaggle 2024 dataset is ready to download
   - datameet may have 2014 data in a different file
   - This alone would fix the biggest data gap and unlock cross-referencing for all years

2. **Stop scoring data-less politicians**
   - Show "Insufficient data" instead of 17.50 for politicians without activity OR disclosure data
   - Only display numeric scores for politicians with at least one non-election data source (~9,336 politicians)
   - Add a "data coverage" indicator alongside each score

3. **Fix entity over-merging**
   - Add (constituency, year) as part of the dedup key, not just (name, constituency)
   - Split the 460 over-merged records
   - Re-run entity resolution with stricter matching

### P1: Important (Before Public Trust)

4. **Remove ghost fields from scoring formula**
   - Drop committee_memberships sub-weight (always 0) — redistribute to attendance/questions/debates
   - Drop pan_declared from disclosure score (always false)
   - Drop serious_criminal_cases from integrity (always 0)
   - Or: source this data from the raw PRS/MyNeta CSVs where it exists

5. **Fix the nondeterministic scoring bug**
   - `ingest.py` line ~686 takes `activities[0]` from an unordered query
   - Different runs produce different scores for multi-term MPs
   - Fix: explicit ORDER BY term_number DESC, or aggregate across terms

6. **Clean up entity resolution**
   - Strip DR./SHRI/SMT from stored names (not just matching keys)
   - Merge the 30+ confirmed duplicate pairs
   - Add constituency rename mapping (BOMBAY→MUMBAI, MADRAS→CHENNAI)

### P2: Enhancement (For Rich Experience)

7. **Add data provenance indicators to the UI**
   - Show which data sources back each metric
   - Flag when disclosure data is from a different election than the profile
   - Show "last election: 2009" prominently for stale records

8. **Separate historical from current**
   - Only show current MPs (latest election winners) on the leaderboard
   - Archive historical politicians in a separate section
   - Don't rank 1951 politicians alongside 2009 MPs

9. **Surface the gold insights**
   - Add a "Key Findings" or "Spotlight" section showing the newsworthy patterns
   - Crorepati trend chart, criminal case trends, wealth growth leaders
   - These are the features that would make the platform go viral

---

## FINAL VERDICT

| Dimension | Rating | Explanation |
|-----------|--------|-------------|
| **Data Accuracy** | A | Publication-quality where data exists. Within 0.01% of known totals. |
| **Data Completeness** | D | Missing 2014-2024. Only 1.8% have activity data. 62% of affidavits lost. |
| **Score Meaningfulness** | F | 72.5% share the same score. Only 1.2% have multi-dimensional scores. |
| **Entity Resolution** | D | 7.6% of elections corrupted. 237+ false matches. 30+ duplicate pairs. |
| **Insight Richness** | A+ | Genuinely newsworthy findings. Crime-pays pattern. Wealth explosion data. |
| **Production Readiness** | D | Cannot launch credibly with 17.50 scores for 41K politicians. |

**Bottom line:** The raw data is gold. The architecture and scoring engine are correct. But we're showing a score for every politician when we only have meaningful data for ~2% of them. Fix the three P0 items and this becomes a genuinely powerful civic tool.
