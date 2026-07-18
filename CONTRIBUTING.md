# Contributing to ANVAYA

## Source of truth

This GitHub repository is the only source of truth. Base44 may provide visual references but not production backend, database, authentication, or parallel source code. Lovable is permitted only as a fallback reference for one isolated screen.

## Milestone discipline

- Work on one approved milestone at a time.
- Create a separate branch and pull request for every milestone.
- Never work directly on `main` and never merge automatically.
- Inspect before editing; do not assume files, endpoints, tables, or dependencies.
- Preserve completed behavior and do not add P1/FUTURE/OUT features to P0.

## Security and data

- Synthetic data only.
- Never commit `.env`, credentials, passwords, API keys, tokens, real personal information, or live police records.
- Connectors are read-only; source records are immutable.
- Optional AI must not execute database commands, invent records, bypass policy, merge identity, assign guilt/risk, or hide conflicts.

## Required verification

Run milestone-relevant unit, integration, E2E, security, benchmark, and consistency checks. Report actual commands and results; never invent test outcomes.

## Pull-request handoff

Report branch, completed scope, changed files, database/migrations, commands, tests and actual results, failures, preview evidence, limitations, exact commit, PR status, and recommended next milestone.

## Product wording

Use: **SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE** on P0 reports. Similarity is a ranking aid, not offender identity or guilt probability. The officer makes the final decision.
