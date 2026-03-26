---
name: Data Contribution
about: Propose adding a new data source to Politia
title: "data: "
labels: data-source
assignees: ""
---

## Data Source Overview

- **Source name:**
- **Official URL:**
- **Maintained by:** (e.g., Election Commission of India, Lok Sabha Secretariat, ADR/MyNeta)
- **License / Terms of use:**

## Why This Data Matters

How does this data source improve the platform's ability to present accountability information?

## Data Details

- **Format:** (CSV, PDF, HTML scraping, API, etc.)
- **Estimated record count:**
- **Historical range:** (e.g., 2004-2024)
- **Update frequency:** (one-time historical import, per election cycle, daily, etc.)
- **Languages:** (English, Hindi, mixed, etc.)
- **Estimated storage:** (MB/GB)

## Data Fields

List the key fields available in this source:

| Field | Type | Example | Maps to Politia Entity |
|-------|------|---------|----------------------|
| | | | |
| | | | |

## Entity Resolution

How can records in this source be linked to existing politicians in Politia?

- **Matching fields available:** (Name, Constituency, Party, Year, etc.)
- **Name format:** (e.g., "LAST, FIRST" or "SHRI FIRST LAST")
- **Known challenges:** (common names, transliteration variants, title prefixes, etc.)

## Data Quality Assessment

- [ ] I have manually verified a sample of records against official sources
- [ ] The data contains unique identifiers that can be cross-referenced
- [ ] Null/missing values are clearly distinguishable from zero values
- [ ] Date formats are consistent throughout the dataset

## Provenance Requirements

Every data point in Politia must trace to an official source. For this data:

- **Can each record link to a specific official URL or document?** (yes/no)
- **If bulk data, is the original download URL stable?**
- **Who originally collected/scraped this data?** (if not directly from the official source)

## Neutrality Check

- [ ] This data does not come from a politically affiliated organization
- [ ] The data is factual (not opinion, ratings, or editorial content)
- [ ] The source does not editorialize (or we will strip editorial content during ingestion)

## Scraping Requirements

If the data requires scraping:

- [ ] The source's `robots.txt` permits scraping the relevant pages
- [ ] The source's Terms of Service do not prohibit automated access
- [ ] A rate-limiting strategy is planned
- [ ] Caching will be implemented to avoid redundant requests

## Implementation Notes

Any technical considerations for building the adapter (authentication, pagination, encoding issues, etc.).

## Sample Data

Paste a small sample (3-5 rows) of the raw data here, or link to a sample file:

```
(paste sample data here)
```

## Checklist

- [ ] I have read the [Data Contribution Guidelines](../../CONTRIBUTING.md#data-contribution-guidelines)
- [ ] I have read the [Guardrails](../../CONTRIBUTING.md#guardrails)
- [ ] This source meets the criteria: official, attributable, structurally consistent, publicly accessible
- [ ] I am willing to implement the source adapter (or I am requesting help)
