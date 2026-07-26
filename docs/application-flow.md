# Application Flow

## Dataset-focused primary journey

1. A synthetic Investigator signs in and opens or creates an investigation with a stated purpose.
2. The Source Control Centre keeps the selected, authorised sources visible and shows unavailable or stale limitations.
3. **FIR Search** accepts one or more bounded FIR filters and returns policy-scoped case summaries.
4. The user opens **Case 360** for FIR Summary, Incident, People, Acts & Sections, Classification, Police & Court, events, evidence, provenance, and Data Quality.
5. **Related Cases** displays only fixed factual matching reasons and a non-guilt disclaimer.
6. **FIR Relationship Graph** presents bounded source-backed relationships with a keyboard-accessible text fallback.
7. **Record Assurance** evaluates deterministic rules, materialises one stable finding per rule/record, and exposes controlled acknowledgement/resolution actions.
8. **Report** first offers the native generated cited Case 360 brief PDF. The separate report lifecycle selects a deterministic FIR report catalogue and provides a print-friendly masked HTML preview; browser **Print → Save as PDF** applies only to that HTML preview.
9. Submitted report versions are immutable. A Supervisor reviews the version and the bounded audit trail.

## Primary labels

The primary product uses Investigation Home, FIR Search, Case 360, Related Cases, FIR Relationship Graph, Record Assurance, Reports, Supervisor Review, Sources & Provenance, and Data Quality. Case DNA, VERIFY, Hypothesis Challenge, Action Impact Preview, and generic Evidence Graph are compatibility-only until their D-11 removal gate.

## Degraded and access-controlled behavior

| Condition | Required behavior |
|---|---|
| No selected sources or no search filters | Show an actionable validation state; do not run an unbounded query. |
| No result / no related case / empty graph | Show a clear empty state without implying missing evidence. |
| Source stale, unavailable, or restricted | Continue only with authorised available data and show a limitation notice. |
| Optional case section absent | Render an empty section; do not fail the entire Case 360 page. |
| Graph cap reached | Show truncation metadata and retain the structured text fallback. |
| Assurance has no findings | Show “No deterministic issues found”; do not fabricate a score. |
| Session expires or request fails | Return a safe error and request identifier where available; never expose a stack trace. |

## Safety boundary

All policy, jurisdiction, masking, selected-source, and action decisions are server-owned. Primary FIR output excludes legacy sensitive entity values, raw source payloads, protected demographics, prediction, risk/guilt language, and recommendations. SQLite is the local default and the final Docker/AppSail prototype uses ephemeral synthetic SQLite workflow state; Catalyst Data Store and Catalyst Authentication are not wired in this flow.
