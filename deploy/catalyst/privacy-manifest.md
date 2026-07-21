# Catalyst Privacy Deployment Manifest

This offline manifest applies to the primary dataset-focused application, gateway, AppSail logs, report output, and frontend responses.

## Never project in primary responses

- age, gender, caste, religion, blood group, disability, full date of birth;
- phone values, IMEI values, vehicle details, legacy identifier values used only for compatibility;
- raw source payloads, original source values, checksums, headers, endpoint details, credentials, tokens, or demo passwords.

## Required controls

- Backend policy enforces role, purpose, jurisdiction, selected-source, and access-class decisions before Data Store response shaping.
- Masking is backend-enforced; frontend controls are presentation only.
- Data Store access is private to AppSail. The browser and frontend hosting service do not receive direct table credentials or table access.
- Source Passport and reports expose only authorised safe provenance metadata and freshness/availability limitations.
- Audit metadata records bounded action categories, identifiers, source selections, counts, and request IDs; it does not store raw report bodies, payloads, passwords, or protected display values.
- AppSail/Gateway logs must redact authorization material, transport bodies, source payloads, and raw exceptions.

## Data Store expectations

Canonical IDs are application-owned. Catalyst system row identifiers remain internal and are never substituted for ANVAYA canonical IDs. Foreign-key, uniqueness, text/JSON-size, and access controls require sandbox verification; this document makes no provider feature claim.
