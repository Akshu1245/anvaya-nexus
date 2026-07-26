# Risk Register

| ID | Risk/unresolved external matter | Impact | Mitigation/owner milestone | Status |
|---|---|---|---|---|
| R-01 | Exact official challenge wording not verified | Scope mismatch | Verify before M1 claim freeze; M0/M8 | Open external |
| R-02 | Official judging rubric unavailable | Optimisation mismatch | Obtain and map to traceability; M8 | Open external |
| R-03 | Submission deadline/portal requirements unconfirmed | Submission failure | Confirm early; M8 | Open external |
| R-04 | Sponsor/deployment conditions unconfirmed | Catalyst mismatch | Verify before M7 | Open external |
| R-05 | Organiser dataset schema/permitted use unknown | Import mismatch | Data Readiness adapter and canonical mapping; M2 | Open external |
| R-06 | Official-logo permission unknown | Branding risk | Use no official logo until confirmed; M8 | Open external |
| R-07 | Catalyst project access/region/credentials unavailable | Hosted deployment blocked | Early smoke test; retain local fallback; M7 | Open external |
| R-08 | Synthetic station/district names not selected | Demo inconsistency | Freeze non-personal synthetic jurisdictions in M2 | Open decision |
| R-09 | Offline context fixture version/geographic coverage not selected | Reproducibility gap | Freeze fixture metadata in M2 | Open decision |
| R-10 | Demo usernames not selected | Demo friction | Choose synthetic usernames; secrets outside Git; M3 | Open decision |
| R-11 | Repository license unspecified | Reuse ambiguity | Owner decision before submission; M8 | Open external |
| R-12 | Private/public repository requirement unknown | Judge access risk | Confirm submission access rules; M8 | Open external |
| R-13 | Kannada interpretation quality | Golden-path failure | Protected tokens, editable preview, 4+6 benchmark; M3/M8 | Controlled |
| R-14 | Entity false positive | Investigative harm | Candidate state, conflict display, no auto-merge; M5 | Controlled |
| R-15 | Synthetic demo appears hardcoded | Credibility loss | Reproducible generator, ground truth, mutation tests; M2/M5 | Controlled |
| R-16 | Source outage/Catalyst failure | Demo failure | Visible degraded and local continuity modes; M6/M7 | Controlled |
| R-17 | Optional AI hallucination | Invented facts | Deterministic factual templates and retrieved IDs only; M3/M8 | Controlled |
| R-18 | Graph hairball | Poor usability | 3 hops, 15 demo/20 maximum, shortest path; M5 | Controlled |
| R-19 | P1 work leaks into P0 | Schedule failure | Traceability and milestone gates; all milestones | Controlled |

None of R-01–R-12 blocks M0 documentation or the M1 local foundation. R-07 can block hosted M7; R-12 can block judge access at submission.
