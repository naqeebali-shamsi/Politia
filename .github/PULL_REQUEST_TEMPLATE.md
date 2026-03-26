## What does this PR do?

<!-- Describe the change and why it's needed. Link to the relevant issue if applicable. -->

Closes #

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Data source (new or updated data ingestion)
- [ ] Scoring change (modifies the scoring formula or display)
- [ ] Refactoring (no functional change)
- [ ] Documentation
- [ ] Tests
- [ ] Infrastructure / CI

## How to Test

<!-- Step-by-step instructions for reviewers to verify this change works. -->

1.
2.
3.

## Checklist

### Required for All PRs

- [ ] All existing tests pass (`pytest` — 204+ tests)
- [ ] New tests added for new functionality (TDD: tests written first)
- [ ] Code follows existing patterns and conventions
- [ ] No `any` types introduced (TypeScript) / type hints present (Python)

### Neutrality Review (required if PR touches user-facing content)

- [ ] All UI copy, labels, tooltips, and descriptions use neutral language
- [ ] No adjectives implying moral judgment (corrupt, honest, best, worst)
- [ ] Criminal case references say "declared in affidavit" not "has cases" or "is criminal"
- [ ] Scoring outputs are labeled as algorithmic/formula-based, not as verdicts
- [ ] N/A — this PR does not touch user-facing language

### Data Changes (required if PR modifies data ingestion or sources)

- [ ] Every new data point has a `SourceRecord` with an official source URL
- [ ] Entity resolution tested against known false-merge cases
- [ ] Ingestion is idempotent (safe to run multiple times)
- [ ] Null values handled explicitly (not zero, not empty string)
- [ ] N/A — this PR does not modify data

### Scoring Changes (required if PR modifies scoring formula)

- [ ] ADR (Architecture Decision Record) written and included
- [ ] Formula version bumped
- [ ] Documentation updated to reflect new formula
- [ ] All affected scores re-computed
- [ ] N/A — this PR does not modify scoring

## Screenshots

<!-- If this PR changes the UI, include before/after screenshots. -->

## Additional Notes

<!-- Anything reviewers should know — edge cases, known limitations, follow-up work needed. -->
