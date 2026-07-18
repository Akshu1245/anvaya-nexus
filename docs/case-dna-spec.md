# Case DNA Specification

Classification: **P0**.

## Purpose

Case DNA discovers explainable behavioural similarity between cases. It does not profile people or confirm common offender identity.

## Factor weights

| Feature | Maximum |
|---|---:|
| Offence category | 5 |
| Modus operandi | 20 |
| Approach/entry | 10 |
| Escape/exit | 10 |
| Time window | 10 |
| Geographic proximity | 10 |
| Target type | 10 |
| Vehicle type | 5 |
| Digital identifier pattern | 15 |
| Evidence pattern | 5 |

## Locked bands

| Score | Band | Meaning |
|---:|---|---|
| 0–24 | Weak similarity | Insufficient behavioural overlap |
| 25–49 | Limited similarity | Some overlap; weak investigative value |
| 50–69 | Moderate similarity | Meaningful overlap requiring independent verification |
| 70–84 | Strong candidate similarity | Strong overlap or hard identifier with visible unresolved conflicts |
| 85–100 | Very strong candidate similarity | Multiple strong factors or verified hard link; still not confirmed identity |

## Rules

- Verified IMEI, complete vehicle registration, or confirmed phone reference dominates weak description.
- Hard identifiers raise candidate priority but never create a confirmed-offender conclusion.
- Material source conflicts remain visible and apply documented penalties.
- Different offence families are excluded in P0.
- Weights, band thresholds, penalties, and calculation version are configuration/specification data.
- Output lists strong similarities, hard links, differences, conflict penalties, final score, band, and source references.

Required label: **Prototype ranking aid — not an offender, guilt, or identity probability.**

## Ground-truth tests

Shared IMEI plus similar MO plus vehicle conflict → strong candidate requiring verification; similar names with conflicting birth year/address → rejected identity candidate; same MO/time without hard ID → behavioural similarity only; different offence family → excluded.
