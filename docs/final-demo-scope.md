# ANVAYA NEXUS — Deployment-ready synthetic datathon prototype

## Final scope

ANVAYA NEXUS is defined for the final submission as a deployment-ready synthetic datathon prototype. The final demo must present a coherent investigation workflow using synthetic data only. Production readiness is not claimed.

## P0 — Required for the final demo

The following capabilities are mandatory and must be available in the final demo:

- Prototype role login
- FIR search
- Case 360
- Related-case discovery
- Source Passport
- Grounded investigation brief
- Editable natural-language interpretation
- Descriptive aggregate trends and recorded hotspots
- Record Assurance
- Synthetic-data banner
- Backend health status

## Final demo flow

1. Confirm backend health status and show the synthetic-data banner.
2. Sign in through the prototype role login.
3. Search for a synthetic FIR and open its Case 360 view.
4. Review related-case discovery results and their Source Passports.
5. Show descriptive aggregate trends and explain small-cell suppression and source-scope limitations.
6. Review deterministic Record Assurance findings.
7. Generate a grounded investigation brief from traceable synthetic sources.
8. State the non-operational limitations and log out.

## Success criteria

The final demo succeeds when:

- Every P0 capability is visible and usable in the demonstrated workflow.
- The workflow completes end to end with synthetic data only.
- Generated briefs and reports remain grounded in displayed source records and Source Passports.
- Backend health is verified before the demo and the live public-demo path completes without private credentials.
- No real police, citizen, FIR, or CCTNS data is accessed, processed, or displayed.

## Deferred — Not required for final submission

The following items are explicitly outside the final-demo scope:

- Catalyst Authentication
- API Gateway
- Production deployment
- Real FIR/CCTNS integration
- Real police or citizen data
- Predictive policing
- Guilt or risk scoring
- Advanced AI chatbot
- Full production security certification
- Report lifecycle and Supervisor review UI
- Offline mock-data fallback

## Limitations

- Only synthetic data may be used. Real police, citizen, FIR, CCTNS, or other operational data is prohibited.
- Authentication and authorization are prototype demonstrations, not production identity controls.
- Related-case discovery and generated content are decision-support demonstrations and require human review.
- The prototype must not perform predictive policing or produce guilt, threat, or risk scores.
- Static shell caching does not cache FIR/API responses; there is no offline mock-data fallback.
- The verified AppSail evaluator deployment demonstrates prototype hosting, not production operational fitness.
- Production readiness, operational fitness, regulatory compliance, and full security certification are not claimed.
