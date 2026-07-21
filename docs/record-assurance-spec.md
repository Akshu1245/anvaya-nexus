# Record Assurance Specification

Classification: **P0**.

## Checks

| Check | Example | Materiality |
|---|---|---|
| Missing source | Complaint document unavailable | Important or blocking when material |
| Duplicate identifier | Crime number repeated across distinct records | Critical |
| Invalid chronology | Arrest before incident; forensic submission before seizure | Critical |
| Conflicting value | Vehicle black in one source and blue in another | Important or critical |
| Candidate identity | Similar alias with conflicting DOB/address | Manual review |

## Result classes

SOURCE-SUPPORTED, REQUIRES VERIFICATION, CONFLICTED, CANDIDATE, INSUFFICIENT SUPPORT.

## Materiality

Formatting differences are informational. Missing optional data is important only when relevant to the current question. Critical conflicts can block confirmation. Rules are deterministic, versioned, source-backed, and question-aware.

## Source fusion

Primary evidence, authoritative administrative records, derived analytics, and context are displayed separately. Conflicting values are preserved. Public context never proves an individual-case connection.

## Challenge output

Every assessed hypothesis separates supporting, weakening, conflicting, and missing information and includes an alternative explanation. Candidate identities are never auto-merged.

## Acceptance invariant

Changing a seeded source value, such as vehicle colour, must change the assurance classification without a code change.
