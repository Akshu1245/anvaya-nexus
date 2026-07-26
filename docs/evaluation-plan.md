# Evaluation and Definition of Done

## Synthetic scale — P0

800–1,200 cases; 1,200–1,800 persons/aliases; 400–600 vehicles; 700–1,000 phones/devices; 300–500 locations; 800–1,200 evidence/forensic records; 2,000–3,500 edges; approximately 5,000–9,000 relational rows.

## Ground truth — P0

Separate manifest of true links, deliberate false similarities, seeded defects, expected source conflicts, expected query results, and expected permission denials.

## Planned benchmark composition — not yet executed

| Category | Count |
|---|---:|
| English | 10 |
| Pure Kannada | 4 |
| Kannada-English code-mixed | 6 |
| Contextual follow-ups | 5 |
| Cross-source verification | 8 |
| Unauthorised/malicious | 5 |
| Total | 38 |

## Aspirational targets — do not present as measured results

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

Currently implemented: backend unit/integration and repository-contract tests; frontend component tests, TypeScript checking, and production build. Full browser E2E, the 38-query benchmark, performance, automated accessibility, and independent security testing remain submission gaps unless separately recorded in `SUBMISSION_EVIDENCE_TEMPLATE.md`.

## Definition of done

Golden path works locally and on Catalyst; searched/unsearched sources are shown; permission denial is real; native cited PDF generation works; aggregate trends disclose their method and limitations; documentation, architecture, screenshots, pitch, and build agree. Scripted Case DNA and Action Impact fixture behavior is excluded from the finalist demo and clearly labeled non-validated in its legacy API response.
