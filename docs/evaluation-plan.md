# Evaluation and Definition of Done

## Synthetic scale — P0

800–1,200 cases; 1,200–1,800 persons/aliases; 400–600 vehicles; 700–1,000 phones/devices; 300–500 locations; 800–1,200 evidence/forensic records; 2,000–3,500 edges; approximately 5,000–9,000 relational rows.

## Ground truth — P0

Separate manifest of true links, deliberate false similarities, seeded defects, expected source conflicts, expected query results, and expected permission denials.

## Benchmark composition

| Category | Count |
|---|---:|
| English | 10 |
| Pure Kannada | 4 |
| Kannada-English code-mixed | 6 |
| Contextual follow-ups | 5 |
| Cross-source verification | 8 |
| Unauthorised/malicious | 5 |
| Total | 38 |

## Submission targets

| Metric | Target |
|---|---:|
| Invented FIR/source IDs | 0 |
| Factual claims with source | 100% |
| Tested unauthorised detail blocked | 100% |
| Seeded P0 defect detection | ≥95% |
| Supported-intent accuracy | ≥90% |
| Top-five similar-case precision | ≥85% |
| Ordinary local query median | <2 seconds |
| Graph-path median | <4 seconds |
| Consecutive golden runs | 10 |

## Automated layers

Backend unit, frontend unit, repository contracts, connector contracts, import validation, integration, E2E, benchmark, security, resilience, performance, accessibility, and deterministic-regression tests.

## Definition of done

Golden path works locally and on Catalyst; contradiction emerges from data/rules rather than hardcoded story text; paraphrase works; searched/unsearched sources are shown; permission denial is real; HTML report is complete with PDF disabled; documentation, architecture, screenshots, pitch, and build agree.
