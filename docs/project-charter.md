# ANVAYA Project Charter

Status: **M0 locked specification**

Product: **ANVAYA — Multi-Source AI Investigation and Data Integrity Layer for CCTNS**

Event: **Karnataka State Police Datathon 2026**

## Mission

ANVAYA gives authorised officers a single, permission-aware workspace to search synthetic CCTNS-style and connected-source replicas, discover explainable case similarities, verify relationships against source integrity, prioritise verification gaps, and generate a source-backed investigation brief.

## Problem statement

Investigators need a fast, multilingual way to search across authorised criminal-justice data sources and discover relevant relationships. Every suggested connection must remain traceable to its source, distinguish evidence from similarity, expose conflicts and missing information, respect source-specific permissions, and remain useful when a source or optional AI service is unavailable.

## Locked principles

- No source, no factual claim.
- No verification, no confirmed connection.
- The officer always makes the final decision.
- Similarity is a ranking aid, never guilt or offender probability.
- P0 uses synthetic/replica data only and claims no live police integration.
- The deterministic workflow must work without an external AI API or API key.

## Workflow

**Ask → Select Sources → Discover → Verify → Prioritise → Report**

## P0 outcome

A complete local-first and Catalyst-portable investigation workflow using CCTNS, Forensics, Vehicle, and offline Public Context/GIS replicas; three backend-enforced roles; multilingual query preview; Case DNA; Record Assurance; a bounded evidence graph; a basic Action Impact Preview; a watermarked HTML report; audit events; degraded operation; synthetic ground truth; and measured evaluation.

## Priority boundaries

- **P0:** complete demonstrable workflow and required controls.
- **P1:** voice, map, Court/Prosecution synthetic adapters, PDF, advanced Action Impact UI, expanded Supervisor analytics, IPC–BNS cross-reference, downloadable graph fallback, and additional assurance rules.
- **FUTURE:** authorised operational integrations and departmental pilots.
- **OUT:** facial recognition, predictive policing, guilt scoring, automatic identity merging, coercive recommendations, social scraping, live CCTNS/ICJS, full OCR, Neo4j, multi-agent architecture, and generic police-system rebuilding.

## Success targets

Zero invented IDs; 100% factual claims sourced; 100% tested unauthorised detail blocked; at least 95% seeded-defect detection; at least 90% supported-intent accuracy; at least 85% top-five similar-case precision; local median query below two seconds; graph median below four seconds; ten consecutive golden-path runs.

## Governance

GitHub is the only source of truth. Each milestone uses a separate branch and reviewable pull request. No milestone is merged automatically. Secrets, real personal information, and live police data are prohibited.
