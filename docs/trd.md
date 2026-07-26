# Technical Requirements Document

## Locked stack

| Layer | Technology | Class |
|---|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS | P0 |
| API state | React Query | P0 |
| Investigation state | Zustand or React Context | P0 |
| Graph | Cytoscape.js with textual fallback | P0 |
| Optional map | Leaflet | P1 |
| Backend | Python 3.11, Flask, Pydantic | P0 |
| Local data | SQLite | P0 |
| Production data | Zoho Catalyst Data Store/ZCQL adapter | P0 |
| Compute | Zoho Catalyst AppSail | P0 |
| Authentication | Prototype authentication adapter | P0 |
| Authentication | Catalyst Authentication | P1 optional |
| Report | Print-ready HTML | P0 |
| PDF | WeasyPrint/ReportLab conversion | P1 |
| Tests | Pytest, frontend unit tests, Playwright or Cypress | P0 |

## Modules

Authentication and Policy Engine; Source Registry and Connector Manager; Data Readiness service; Query Interpreter and Validator; Evidence Retrieval; Case DNA; Record Assurance; Graph; Action Impact; Report; Audit and Observability.

## Constraints

- Model and browser never execute SQL/ZCQL or receive database credentials.
- Connectors are read-only; source records are immutable.
- Critical factual text is template-grounded from retrieved objects.
- Connector failures cannot silently disappear.
- Graph traversal is at most three hops, 20 visible nodes, and 15 nodes in the main demo.
- Repository root is used directly; no nested `anvaya/` directory.
- External AI is optional and cannot make policy or provenance decisions.
- Local deterministic behavior remains available after Catalyst deployment.

## Repository abstraction

Services consume repository contracts rather than SQLite/ZCQL directly. Contract tests must run against SQLite and Catalyst adapters. Catalyst work starts only after the local P0 workflow is stable.

## Security architecture

Backend order: authenticate → validate purpose → validate intent/schema → enforce role/jurisdiction/source policy → retrieve bounded records → apply field masking → derive findings → attach provenance → audit → respond.

## Error contract

Errors contain a stable code, safe message, request ID, retryability, and permitted limitation details. They never expose stack traces, credentials, SQL, or unmasked records.
