# M7.2B-0 — Catalyst Data Store Compatibility Design

## D-12A offline deployment package

The deployment manifest at `deploy/catalyst/datastore-manifest.json` and fixed-query manifest at `deploy/catalyst/query-template-manifest.json` are planning artifacts only. They enumerate the D-1 through D-10 canonical SQLite model, bounded offline fake-client reads, expected seed order, and future write atomicity gates. They do not validate Data Store schema syntax, table limits, joins, IN-list binding, ordering, pagination, transactions, authentication, Gateway, or hosting behavior. No schema has been created and no ZCQL has been executed.

Explicit Catalyst runtime mode remains fail-closed and placeholder-backed. It must never use SQLite as a hidden fallback. Live D-12B requires separate authorization, sandbox access, approved secret handling, and completion of `docs/m7-catalyst-live-validation-checklist.md`.

**Status:** design only. This document makes no network call, creates no Catalyst resource, and does not make Catalyst persistence available. SQLite remains ANVAYA's default and only working persistence implementation.

**M7.2B-1 implementation note:** an offline client protocol, fixed-template registry, logical binder, row normalizer, safe error translator, fake client, and standalone read gateway now exist. They are dependency-injected test infrastructure only: no HTTP/SDK transport, credentials, endpoint construction, ZCQL execution, schema bootstrap, repository wiring, or write-capable Catalyst operation exists.

**Design baseline:** `feat/m7-zoho-catalyst-deployment` at `55f1006c068b786dcca5d2b39f274e31b0e252fa`.

## Evidence and terminology

The plan uses Catalyst Cloud Scale primary Data Store, not the optional OLAP database. Official documentation verifies that primary Data Store supports CRUD while OLAP is read-only, that tables and columns must already exist for the Data Store APIs, and that each table receives Catalyst-managed `ROWID`, `CREATORID`, `CREATEDTIME`, and `MODIFIEDTIME` columns. It also verifies the supported column types and limits: `Var Char` <=255 characters; `Text` and `Encrypted Text` <=10,000 characters; `Int`, `BigInt`, `Double`, `Boolean`, `Date`, `DateTime`, and `Foreign Key` are available. [Columns](https://docs.catalyst.zoho.com/en/cloud-scale/help/data-store/columns/) · [Data Store REST overview](https://docs.catalyst.zoho.com/en/api/introduction/overview-and-prerequisites/) · [Primary Data Store vs OLAP](https://docs.catalyst.zoho.com/en/cloud-scale/help/data-store/olap-database/introduction/)

ZCQL is treated as a **fixed server-authored template language**, never as a client input. Official limits materially affect this design: a SELECT returns at most 20 columns and 300 rows; a query may use at most five WHERE conditions; and a query may use at most four joins, with one condition per JOIN. `LIMIT offset,value` is documented. ZCQL V2 documents subqueries in WHERE, but adoption/version and practical behavior need sandbox validation. [SELECT](https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/select/) · [WHERE](https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/where/) · [JOIN](https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/joins/) · [LIMIT](https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/limit/) · [ZCQL V2](https://docs.catalyst.zoho.com/en/cloud-scale/help/zcql/syntax-exceptions/)

| Label | Meaning in this document |
|---|---|
| Verified | Directly stated in the official documentation above. |
| Sandbox gate | Must be proven in the target project before an adapter relies on it. |
| Design decision | ANVAYA choice, not a Catalyst product claim. |
| Unsupported parity | SQLite behavior with no verified Catalyst equivalent yet. |

## 1. Canonical SQLite schema inventory

Source of truth is migrations `001_initial.sql` through `004_reports_review.sql`, plus the current `SQLiteRepository`. All timestamps are currently ISO-8601 text; JSON is serialized text. `id` is the canonical, synthetic application ID used in API responses.

| Table | Key / columns | Constraints, indexes, lifecycle | Filters, ordering, sensitive or JSON fields |
|---|---|---|---|
| `schema_versions` | PK `version INTEGER`; `applied_at TEXT NOT NULL` | Migration ledger; inserted once/version. | `MAX(version)`; ordered by version implicitly. |
| `users` | PK `id`; `username`, `password_hash`, `role`, `assigned_station?`, `assigned_district?`, `active INTEGER DEFAULT 1` | `username UNIQUE`; role CHECK; sessions/reports/investigations reference it. | username and role lookup; password hash is secret; station/district are scope data. |
| `sessions` | PK `id`; FK `user_id`; `token_hash`, `created_at`, `expires_at`, `revoked_at?` | `token_hash UNIQUE`; index `idx_sessions_token`; mutable revocation only. | token hash lookup; token hash is sensitive. |
| `source_systems` | PK `id`; name/tier/access/reliability/status/sync/freshness/version/connector/description/priority | `status` and `priority` CHECKs; source metadata is upserted. | ordered `priority,id`; status and access drive policy. |
| `source_records` | PK `id`; FK source system; external ID/version/timestamps/access/reliability/freshness/checksum/payload JSON | composite UNIQUE `(source_system_id,external_id,version)`; SQLite triggers prohibit update/delete. | source, external ID, version; `payload_json` can contain maskable source data. |
| `transformation_events` | PK `id`; FK source record; operation/source field?/target field?/rule version/time/outcome | Append-only by application convention. | ordered `occurred_at,id`; provenance. |
| `import_jobs` | PK `id`; FK source system; format/checksum/source version/status/mapped JSON/accepted rows JSON/counts/times | Status changes from staged to committed/rejected by workflow. | job ID; `mapped_fields_json`, `accepted_rows_json` are potentially large. |
| `import_failures` | PK `id`; FK import job; row number/category/safe reason | Append-only validation output. | ordered `row_number`; safe error text only. |
| `cases` | PK `id`; FIR/crime/station/district/offence/incident/registered/status; FK source record | Canonical record; no unique FIR/crime constraint in schema. | SEARCH filters and stable `incident_at DESC,id`; IDs/FIR/crime are maskable. |
| `persons` | PK `id`; display name/birth year/address/identity status; FK source record | Entity source record provenance. | Name/address/birth year are sensitive. |
| `aliases` | PK `id`; FK person; alias; FK source record | Entity provenance. | person lookup; alias sensitive. |
| `organisations` | PK `id`; name/kind; FK source record | Entity provenance. | name may be sensitive. |
| `phones` | PK `id`; synthetic number/number hash; FK source record | Entity provenance. | both values sensitive/maskable. |
| `devices` | PK `id`; synthetic IMEI/IMEI hash/type; FK source record | Entity provenance. | IMEI sensitive/maskable. |
| `vehicles` | PK `id`; registration/hash/type/colour; FK source record | Entity provenance. | registration sensitive/maskable. |
| `locations` | PK `id`; locality/station/district/latitude/longitude; FK source record | Entity provenance. | locality/coordinates may be jurisdiction/maskable. |
| `documents` | PK `id`; FK case nullable; type/status; FK source record | Current Case 360/support record. | case lookup; document metadata. |
| `evidence_records` | PK `id`; FK case; type/description/status/sensitivity; FK source record | Current Case 360/assurance record. | ordered by ID; description sensitive. |
| `forensic_events` | PK `id`; FK case; type/time/result; FK source record | Current Case 360 record. | ordered by ID; result may be sensitive. |
| `public_context` | PK `id`; FK location; type/value/publication version; FK source record | Context only, not offence proof. | value may be public but must retain source classification. |
| `entity_edges` | PK `id`; source type/ID, target type/ID, relationship type/class; FK source record | Edge source provenance; no relational FK to polymorphic endpoints. | ordered ID; graph/path and DISCOVER; source/target IDs sensitive. |
| `case_dna_features` | PK `id`; FK case; feature type/value/weight; FK source record | Seeded deterministic features. | similarity source data; value can be sensitive. |
| `trust_issues` | PK `id`; FK case nullable; issue type/severity/description/source record IDs JSON/status | Seeded/imported assurance input. | ordered ID; JSON provenance. |
| `investigations` | PK `id`; FK owner; title/purpose/selected sources JSON/assigned station?/district?/times | Owner scope; selected source snapshot updated atomically. | owner, updated time; title/purpose maskable; JSON source selection. |
| `investigation_messages` | PK `id`; FK investigation; original text/query-plan JSON/confirmed/default 0/created; parent FK?/intent?/result count?/request ID? | Append-only except confirmation/plan update; M3/M4 query history. | ordered `created_at`; user query text and plan are sensitive; JSON. |
| `reports` | PK `id`; FK investigation/owner/reviewer?; title/status/current version/times | Lifecycle aggregate; reviewer assignment/status mutable only through transitions. | list owner/reviewer `updated_at DESC,id`; report scope. |
| `report_versions` | PK `id`; FK report; version/status/sections JSON/notes/HTML/creator/time/immutable default 0 | UNIQUE `(report_id,version_number)`; submitted/approved immutable through repository logic. | ordered `version_number DESC`; HTML and notes can be large/sensitive. |
| `report_reviews` | PK `id`; FK report version/reviewer; decision/note/time | Append-only; exact version binding. | ordered `created_at,id`; reviewer note sensitive. |
| `audit_events` | PK `id`; user? / type/outcome/request ID/safe metadata JSON/time | Append-only only through repository contract; index `idx_audit_type`. | ordered `occurred_at DESC,id DESC`; metadata deliberately sanitised. |
| `investigation_sources` | **No SQLite table exists.** | Selected sources are serialized in `investigations.selected_sources_json`; do not invent a table in parity phase. | A normalized child table is an optional future compatibility migration, not M7.2B-0. |

Additional canonical tables deliberately included for completeness: `aliases`, `organisations`, `documents`, `public_context`, and `case_dna_features`. No schema-level secondary indexes exist for the majority of current joins; SQLite test-volume behavior must not be extrapolated to Catalyst.

## 2. Proposed Catalyst type and naming mapping

### Naming and identifiers

Verified: table names may contain alphanumeric characters and underscores and may not begin with a number; Catalyst allocates a Table ID and default system columns. Existing lower-case `snake_case` names therefore fit the documented table-name rule. Column-name restrictions are not sufficiently explicit in the current official page; retain lower-case ASCII snake_case but validate the full manifest in a sandbox before provision. [Tables](https://docs.catalyst.zoho.com/en/cloud-scale/help/data-store/tables/)

**Design decision:** retain every canonical ANVAYA `id` as a mandatory, unique `Var Char(128)` application column. Catalyst `ROWID` remains an adapter-private physical locator. API/domain IDs stay `SYN-*`; no response returns a Catalyst row ID. A per-table mapping cache may map canonical ID to `ROWID` after lookup, but it is not persisted unless profiling shows that it is necessary.

### Column-manifest mapping (complete)

Notation: `V(n)` = `Var Char(n)`; `T` = `Text` (maximum 10,000 documented characters); `DT?` = DateTime only after timezone/offset validation, otherwise `V(35)` canonical UTC; `FK?` = optional Catalyst foreign key only after string-canonical-ID/ROWID behavior is validated. All listed `id` columns are mandatory unique `V(128)` application IDs unless stated otherwise. `PII` means enable Catalyst's PII/ePHI marker only after target-project governance validation; it does not replace ANVAYA masking.

| SQLite table | Exact SQLite columns → proposed Catalyst columns | Notes / verification |
|---|---|---|
| `schema_versions` | `version INTEGER → Int UNIQUE mandatory`; `applied_at TEXT → DT?` | ledger unique is enough; `ROWID` is not the schema version. |
| `users` | `id→V(128) unique`; `username TEXT→V(128) unique`; `password_hash→V(128) PII`; `role→V(32)`; assigned station/district→`V(128)` nullable; `active INTEGER→Boolean default true` | role check stays application allowlist. |
| `sessions` | `id→V(128) unique`; `user_id→V(128)` / `FK?`; `token_hash→V(128) unique PII`; created/expires/revoked→`DT?`, revoked nullable | token lookup index/unique is required. |
| `source_systems` | `id→V(128)`; name/tier/access/reliability/status/version/connector/priority→`V(255)`; sync→`DT?` nullable; threshold→`Int`; description→`T` | enum checks become service allowlists. |
| `source_records` | `id→V(128)`; source system ID→`V(128)` / `FK?`; external ID/version/access/reliability/freshness→`V(255)`; source/imported time→`DT?`; checksum→`V(64)`; payload JSON→`T` PII; derived `source_record_key→V(255) unique` | composite unique is represented by the derived key. |
| `transformation_events` | `id→V(128)`; source record ID→`V(128)` / `FK?`; operation/source field/target field/rule version/outcome→`V(255)` (source/target nullable); occurred→`DT?` | append-only application contract. |
| `locations` | `id→V(128)`; locality/station/district→`V(255)` PII; latitude/longitude→`Double`; source record ID→`V(128)` / `FK?` | coordinates can be sensitive/masked. |
| `cases` | `id→V(128)`; FIR/crime/station/district/offence/status→`V(255)`; incident/registered→`DT?`; source record ID→`V(128)` / `FK?` | FIR/crime not schema-unique today. |
| `persons` | `id→V(128)`; display name/address→`T` PII; birth year→`Int` PII; identity status→`V(64)`; source record→`V(128)` / `FK?` | avoid encrypted type if fields need equality/order queries without sandbox proof. |
| `aliases` | `id→V(128)`; person ID/source record ID→`V(128)` / `FK?`; alias→`V(255)` PII | fixed entity lookup only. |
| `organisations` | `id→V(128)`; name→`V(255)` PII where required; kind→`V(128)`; source record→`V(128)` / `FK?` |  |
| `phones` | `id→V(128)`; synthetic number/number hash→`V(255)` PII; source record→`V(128)` / `FK?` | exact matching needs non-encrypted/hash column behavior validation. |
| `devices` | `id→V(128)`; IMEI/IMEI hash→`V(255)` PII; device type→`V(128)`; source record→`V(128)` / `FK?` |  |
| `vehicles` | `id→V(128)`; registration/hash→`V(255)` PII; type/colour→`V(128)`; source record→`V(128)` / `FK?` |  |
| `documents` | `id→V(128)`; case ID→`V(128)` nullable / `FK?`; document type/status→`V(128)`; source record→`V(128)` / `FK?` |  |
| `evidence_records` | `id→V(128)`; case/source record IDs→`V(128)` / `FK?`; evidence type/status/sensitivity→`V(128)`; description→`T` PII |  |
| `forensic_events` | `id→V(128)`; case/source record IDs→`V(128)` / `FK?`; event type/result status→`V(128)`; occurred→`DT?` |  |
| `public_context` | `id→V(128)`; location/source record IDs→`V(128)` / `FK?`; context type→`V(128)`; value→`T`; publication version→`V(128)` | remains context, not offence evidence. |
| `entity_edges` | `id→V(128)`; source/target type→`V(64)`; source/target ID→`V(128)` PII/maskable; relationship type/edge class→`V(128)`; source record ID→`V(128)` / `FK?` | polymorphic ends stay canonical IDs, not a Catalyst FK. |
| `case_dna_features` | `id→V(128)`; case/source record IDs→`V(128)` / `FK?`; feature type/value→`V(255)` PII as needed; weight→`Double` | no client-controlled weights. |
| `trust_issues` | `id→V(128)`; case ID→`V(128)` nullable / `FK?`; issue/severity/status→`V(128)`; description→`T`; source-record IDs JSON→`T` | safe JSON; deterministic ordering by ID. |
| `import_jobs` | `id→V(128)`; source ID→`V(128)` / `FK?`; format/version/status→`V(128)`; checksum→`V(64)`; mapped/accepted JSON→`T`; counts→`Int`; all times→`DT?` nullable where currently nullable | accepted-row size is a hard gate. |
| `import_failures` | `id→V(128)`; job ID→`V(128)` / `FK?`; row number→`Int`; category→`V(128)`; safe reason→`T` | append-only. |
| `investigations` | `id→V(128)`; user ID→`V(128)` / `FK?`; title/purpose→`T` PII; selection JSON→`T`; assigned station/district→`V(128)` nullable; times→`DT?` | no `investigation_sources` table in parity manifest. |
| `investigation_messages` | `id→V(128)`; investigation/parent IDs→`V(128)` / `FK?` nullable parent; original text/query-plan JSON→`T` PII; confirmed→`Boolean`; time→`DT?`; execution intent→`V(64)` nullable; result count→`Int` nullable; request ID→`V(128)` nullable | append-only except existing confirmation update. |
| `reports` | `id→V(128)`; investigation/owner/reviewer IDs→`V(128)` / `FK?` nullable reviewer; title→`T`; status→`V(64)`; current version→`Int`; times→`DT?` | workflow invariants application-owned. |
| `report_versions` | `id→V(128)`; report/creator IDs→`V(128)` / `FK?`; version→`Int`; status→`V(64)`; sections JSON/notes/HTML→`T` PII; created→`DT?`; immutable→`Boolean`; derived `report_version_key→V(255) unique` | HTML size is a blocker; submitted/approved status stays immutable. |
| `report_reviews` | `id→V(128)`; report-version/reviewer IDs→`V(128)` / `FK?`; decision→`V(64)`; note→`T` PII; created→`DT?` | append-only and exact version binding. |
| `audit_events` | `id→V(128)`; user ID→`V(128)` nullable / `FK?`; event/outcome→`V(128)`; request ID→`V(128)` nullable; metadata JSON→`T`; occurred→`DT?` | keep sanitized only; report/investigation references are not first-class columns today. |

| SQLite category / affected columns | Proposed Catalyst mapping | Transformation and query implication | Status / risk |
|---|---|---|---|
| Short IDs, enums, hashes, station/district, names <=255 | `Var Char`, explicit max length (64/128/255 by field) | Validate length before write; use canonical-ID exact comparisons. | Verified type; actual maximum/design manifest must be sandboxed. |
| General `TEXT` strings: descriptions, notes, query plans, JSON, payloads | `Text` up to 10,000 chars | UTF-8 JSON serialized compactly; reject/route overflow instead of truncating. | Verified 10k cap; source payload/report overflow is blocker. |
| Password/token hashes | `Var Char(128)` plus PII/ePHI classification where appropriate | Never select into logs or health; exact match only. | Type verified; project governance classification sandbox gate. |
| Human names, address, phone, IMEI, registration | `Var Char` or `Text` plus PII/ePHI validator | Preserve masking in application; mark sensitive columns. | Validator verified; must validate console/API access behavior. |
| ISO timestamps currently stored as TEXT | `DateTime` **only after format/time-zone sandbox proof**; otherwise canonical UTC `Var Char(35)` | Normalize to UTC; avoid local-time ambiguity. Catalyst docs state date/time format but do not establish offset acceptance. | Sandbox gate. |
| Date-only filter fields if added | `Date` | Use only `YYYY-MM-DD`; do not derive client timezone. | Verified type; not required for parity. |
| INTEGER counts, flags, version numbers | `Int`; `Boolean` for `active`, `confirmed`, `immutable` | Convert 0/1 consistently; query boolean with equality, not IN/LIKE. | Verified types; `Int` is 10 digits. |
| SQL `REAL` case DNA weight / latitude/longitude | `Double` | Preserve finite numeric validation. | Verified type (17 digits including decimal). |
| Foreign-key-like IDs | `Var Char(128)` first; optionally Catalyst `Foreign Key` only after manifest proof | Canonical IDs are strings while Catalyst FK refers to its primary `ROWID`; using application IDs avoids API-domain rewrite. | Catalyst FK exists, but string-ID parity and cascade behavior need sandbox proof. |
| Checksums | `Var Char(64)` SHA-256 hex | Mandatory; exact matching only. | Low risk. |
| JSON fields listed above | `Text` with versioned JSON schema and max byte/character guard | No JSON path predicates; filter through normalized columns or application read. | No JSON column type documented; sandbox gate. |
| `report_versions.html` | `Text` only if <=10,000 chars; otherwise **do not implement Data Store parity** | Keep deterministic HTML renderable from section data; artifact storage decision deferred. | Major blocker: current output size must be measured. |
| large `source_records.payload_json`, `accepted_rows_json` | `Text` only if <=10,000 chars; otherwise normalized child rows or later artifact service | Never silently truncate. | Major blocker. |

**No implicit JSON type exists in the documented type list.** This design therefore treats JSON as bounded serialized `Text`, with a size check and schema version, until sandbox validation proves an alternative.

### Constraint compatibility

| SQLite expectation | Proposed Catalyst enforcement | Compatibility / race risk |
|---|---|---|
| Canonical application PK (`id`) | mandatory unique canonical-ID column; system `ROWID` remains physical PK | Unique column is documented; test concurrent duplicate insert and error translation. |
| `users.username`, session token hash unique | mandatory unique columns | Native unique documented; test case sensitivity and concurrent writes. |
| source record composite unique `(source_system_id,external_id,version)` | No verified composite unique rule: add a mandatory unique derived key `source_record_key = source|external|version` | Application must generate canonical escaped/hash key; sandbox verify unique behavior. |
| report `(report_id,version_number)` unique and monotonic | unique derived `report_version_key`; create-next-draft with compare-and-reconcile | Monotonicity is application-level; concurrency requires idempotency/reconciliation. |
| investigation source uniqueness | Existing JSON snapshot stays canonical for parity | Atomic replacement depends on write semantics; normalized table is later migration only. |
| FK references | Store canonical ID values; optionally add Catalyst FK only after target validation | Catalyst FK refers primary key and offers Null/Cascade behavior, but parity/not-null/canonical IDs need validation. |
| SQLite CHECK enums | application allowlists before write | CHECK is not documented; unsupported until proven. |
| immutable `source_records` | repository offers no update/delete methods; service identity only gets read/insert ability | Storage trigger parity unsupported; console/admin mutation cannot be fully prevented by adapter. |
| immutable submitted/approved versions | conditional update plus immutable flag/status validation in repository; reconciliation after timeout | Requires compare-and-set semantics/row update result validation. |
| append-only reports reviews/audit | no update/delete methods, least-privilege identity, immutable canonical ID | API contract guarantees, but console/admin mutation protection needs governance verification. |
| cascades | avoid reliance; no destructive deletes in normal lifecycle | Catalyst supports FK Null/Cascade in docs, but no operation requires it. |

## 3. Transaction and write compatibility matrix

Official material confirms primary Data Store is transaction-oriented/CRUD capable, but this research did **not** find an explicit transaction API, isolation level, or multi-table rollback contract. Every multi-table operation below is therefore a sandbox gate, not a claim of atomic Catalyst parity.

| Operation | SQLite boundary / tables | Required outcome | Catalyst status and safe alternative |
|---|---|---|---|
| Session creation | one insert: `sessions` | unique token hash, no partial record | single write; idempotency key=session ID; verify duplicate handling. |
| Session revocation | one update: `sessions` | monotonic revoked timestamp | conditional update/retry; no compensation needed. |
| Source registry upsert | multiple `source_systems` writes | all supplied source statuses consistent | batch behavior unverified; per-row idempotent upsert + manifest reconciliation. |
| Import job creation | `import_jobs` + `import_failures` | job and failures agree | write job first with `STAGING`, append failures; retry by job ID; reconcile incomplete job. |
| Canonical import commit | `source_records` + transforms + cases + import job | all canonical rows visible together or none | **High-risk blocker.** Stage with deterministic IDs, append a commit journal/state, idempotent writes, final state only after verification; operator reconciliation required if no transaction. |
| Source selection replace | one `investigations` update | no partial selection | single conditional write; optimistic updated-at/version needed if concurrent. |
| Query confirmation/history | insert/update `investigation_messages` | exact request/plan attached to owner investigation | single write/conditional update; retry keyed by message ID. |
| Report creation + v1 | `reports` + `report_versions` | report never visible without v1 | **High-risk.** create report `CREATING`, insert v1, mark ready; reads hide incomplete state; reconcile abandoned creation. |
| Reviewer assignment | one `reports` update | valid reviewer only, no partial update | service validates reviewer then conditional write; assignment audit is separately append-only. |
| Submission | report version + report status/current version | immutable submitted v and IN_REVIEW status agree | **High-risk.** requires verified conditional multi-row transaction; otherwise durable operation journal + read repair. Do not enable in Catalyst before proof. |
| Review decision | review append + report status/version linkage | exact submitted version, one valid terminal transition | **High-risk.** same constraint; idempotency key decision ID and reconciliation. |
| New draft after changes | new version + report current/status | old immutable, new editable monotonic v | **High-risk.** use derived unique version key; verify duplicate/race behavior. |
| Audit append | one `audit_events` insert | append only | single idempotent insert; storage-level no-update is unverified. |

**Design decision:** M7.2B implementation order must keep writes that require cross-table atomicity disabled/`unavailable` until a target-project sandbox proves a usable transaction/conditional-update primitive. No fake success and no SQLite fallback in explicit Catalyst mode.

## 4. Fixed repository-to-ZCQL mapping

All templates live server-side and interpolate only validated, encoded values into fixed table/column/ordering strings. Because ZCQL's documented WHERE limit is five conditions, methods with more filters must split into a primary restrictive query plus application-side trusted filtering, or use a tested V2 subquery—not concatenate unrestricted predicates.

| Repository category / methods | Tables and fixed pattern | ZCQL / assembly status |
|---|---|---|
| Health/schema (`health_check`, `schema_version`, `table_count`) | `anvaya_schema_versions`; fixed `MAX(version)`, bounded counts | Aggregate SELECT documented; table metadata is available through REST. Sandbox table/column metadata permissions. |
| Users/sessions (`find_*`, create/revoke session, seed users) | `anvaya_users`, `anvaya_sessions`; exact canonical/username/token match; one user/session join | One join; fixed equality/order; write by row API preferred. Test token uniqueness and update targeting by ROWID. |
| Source registry/readiness | `source_systems`, `source_records`, `import_jobs`, `import_failures`, transformations, cases | exact/list reads; imports are multiple fixed writes, not one ZCQL mega-query | ZCQL reads feasible; write/transaction parity is sandbox gated. |
| Investigations/query history | `investigations`, `investigation_messages`, `users` | owner-scoped list ordered `updated_at,id`; message history `created_at,id` | One join max; fixed offset/limit. |
| SEARCH (`search_case_candidates`) | cases + source record plus optional fixed entity-edge/entity existence checks | issue bounded candidate queries per supported identifier then intersect/rank in service | Avoid one query with variable optional joins/conditions; requires indexes on case/source fields. |
| DISCOVER | entity edges self-match + cases + 3 source records | current SQLite shape needs four joins and several filters | At ZCQL join ceiling; prefer 2–3 bounded queries keyed by edge/entity IDs then app-side dedupe/rank. Sandbox exact semantics. |
| Relationship paths | entity edges + source records | fetch allowlisted bounded edges, service performs max-depth-3 BFS | No recursive client/query traversal. No recursive support assumed. |
| Case 360 | case; fixed entity-type batches; evidence; forensics; trust issues | fixed read per section/batch | Multi-query assembly avoids a 5+ table join and 20-column cap. |
| Source Passport | source record + source system; transformations | one join then one ordered transform query | Feasible; payload not selected unless existing service needs authorised field. |
| Case DNA | cases + source-backed edges/features | fixed seed/candidate/edge reads, service computes scores | No client weights/sorts. Candidate cap before service scoring. |
| Evidence Graph | case + allowlisted source-backed edges | bounded root/edge queries | Service produces nodes/labels; no generic graph ZCQL. |
| Record Assurance | trust issues (and current fixed source/case reads) | ordered bounded reads | Service retains deterministic classification. |
| Reports/versions/reviews | reports, versions, reviews, users, investigations | list/detail via <=4-join split read; lifecycle writes as matrix above | Reads feasible in batches; lifecycle is transaction gate. |
| Audit | audit events + optional user role lookup | bounded safe fields, fixed filters/order | role filtering may be pre-resolved to actor IDs to avoid subquery; investigation/report references currently require safe JSON matching and should be normalized later for reliable Catalyst filtering. |

### Complete current repository-method inventory

The following is the implementation checklist for the existing `Repository` contract. A slash groups methods that use the identical fixed template family; it does not authorize a generic query API. `row` means documented table-row CRUD is preferred; `select` means a fixed ZCQL SELECT; `multi` means a bounded sequence of those operations with application-side assembly.

| Contract methods | Tables | Proposed operation / gate |
|---|---|---|
| `health_check`, `schema_version`, `table_count`, `initialize`, `close` | schema manifest / `schema_versions` | metadata inspect + fixed aggregate SELECT; `initialize` stays no-op/unavailable until operator bootstrap is separately authorized. |
| `seed_predefined_users`, `find_active_user_by_username`, `find_user_by_id` | users | bounded row inserts; fixed exact username/ID select. |
| `create_session`, `find_session_with_user`, `revoke_session` | sessions, users | row insert/update; one fixed join select. Unique token and update targeting sandbox gate. |
| `upsert_source_systems`, `list_source_systems`, `find_source_system`, `source_external_ids` | source systems, source records | row upsert behavior must be proven; fixed ordered/exact reads. |
| `create_import_job`, `find_import_job`, `list_import_failures`, `commit_import_rows` | imports/failures/source records/transforms/cases | fixed row operations; `commit_import_rows` blocked on transaction/reconciliation gate. |
| `create_investigation`, `find_investigation`, `list_investigations_for_user`, `replace_investigation_sources` | investigations | fixed exact/owner select and row writes. |
| `create_investigation_message`, `find_investigation_message`, `list_investigation_messages`, `confirm_investigation_message` | investigation messages | fixed insert/exact/list/conditional update. |
| `search_case_candidates` | cases, source records, entity edges, phones/devices/vehicles as required | multi: fixed candidate and ID-match selects, then existing service ranking. |
| `list_discovery_candidates` | entity edges, cases, source records | multi: source-bounded entity match and candidate reads, then dedupe. |
| `list_relationship_edges` | entity edges, source records | fixed allowlisted edge select; service BFS remains bounded. |
| `find_case_360_case`, `list_case_360_entities`, `list_case_360_evidence`, `list_case_360_forensics`, `list_case_360_trust_issues` | cases, entity tables/edges, evidence, forensics, trust issues | fixed section reads, multi assembly. |
| `find_source_passport_record`, `list_source_transformations` | source records, source systems, transforms | one join + ordered transform select. |
| `find_case_dna_case`, `list_case_dna_edges`, `find_evidence_graph_case`, `list_evidence_graph_edges`, `list_assurance_trust_issues` | cases, entity edges, source records, trust issues | fixed bounded reads only; intelligence remains service-owned. |
| `create_report_with_initial_version`, `find_report`, `list_reports_owned_by`, `list_reports_assigned_to` | reports, report versions, users | read templates feasible; create is blocked on multi-write atomicity gate. |
| `find_eligible_supervisor`, `list_eligible_supervisors`, `assign_report_reviewer` | users, reports | fixed active-Supervisor reads; one conditional report update. |
| `find_report_version`, `find_current_report_version`, `list_report_versions`, `update_report_draft`, `submit_report_version`, `create_next_report_draft` | report versions, reports | fixed reads/draft update; submit/next draft blocked on transition transaction gate. |
| `create_report_review_decision`, `list_report_review_history` | reviews, versions, users, reports | review history fixed reads; decision blocked on multi-write transition gate. |
| `append_audit_event`, `list_audit_events` | audit events, users | single idempotent append and fixed bounded filter read; normalized report/investigation refs are a later compatibility decision. |

### Query template registry rules

1. `backend/anvaya/platform/catalyst/zcql_templates.py` (future) contains named templates and field allowlists only.
2. Values are encoded by a single literal encoder; table, column, join, and order fragments are constants, never parameters.
3. Each select projects no more than 20 explicit columns and asks for <=300 rows; repository caps remain stricter where current APIs do.
4. Stable ordering always ends in canonical application `id`; timestamps use a matching canonical UTC representation after sandbox proof.
5. Relationship/path and analytic assembly run in Python over capped, pre-authorized rows.

## 5. Join, graph, pagination, and content risks

| Area | Decision | Risk / verification gate |
|---|---|---|
| SEARCH | Fetch source-backed candidate cases first, then bounded entity match batches; rank/mask in service. | Current combined optional predicate behavior must be parity-tested. |
| Case 360 / Passport | Section-specific batched reads; no generic entity table lookup. | More round trips; set bounded fan-out and test latency. |
| DISCOVER / Evidence Graph / paths | Fetch only selected-source edge records; bounded Python BFS/assembly. | ZCQL recursive traversal is not assumed. Enforce current edge 200/depth 3 caps before assembly. |
| Case DNA | fixed candidate and edge reads; deterministic scoring stays service-owned. | Candidate batch/feature fan-out must remain capped. |
| Reports | derive/refresh HTML from policy-filtered section data; never trust stored HTML alone. | HTML >10k cannot live safely in Data Store Text. |
| Audit role filter | resolve role scope with fixed user lookup, then query audit by actor ID(s), or add normalized safe `actor_role` if a later migration is approved. | JSON LIKE used by SQLite for report/investigation references is not a robust portable design. |
| Offset pagination | retain current `LIMIT offset,value` API envelope with canonical tie-break (`time DESC,id DESC` or version/id order). | Offset can skip/duplicate amid concurrent writes; later cursor/keyset token is preferable but would be compatibility change. |

## 6. JSON and large-content strategy

| Field family | M7.2B proposal | Decision gate |
|---|---|---|
| `safe_metadata_json`, `query_plan_json`, `selected_sources_json`, `sections_json`, `source_record_ids_json`, `mapped_fields_json` | canonical compact JSON in Text with declared schema/version and <=10k validation | Test actual max serialized sizes and Unicode character counting. |
| `accepted_rows_json` | retain only if measured <=10k for supported import batches; otherwise child staging rows or artifact design later | Do not implement bulk import in Catalyst before resolution. |
| `payload_json` | keep only bounded, policy-filtered source payloads <=10k; otherwise normalized data plus external artifact pointer later | High-risk privacy/size gate. |
| report HTML | treat as derived; store version section data as canonical. Use Text only when <=10k; otherwise defer artifact storage decision (File Store vs Stratus) to an explicitly authorized later block. | Native report lifecycle Catalyst write remains blocked. |
| notes/reviewer notes | Text <=10k, escaped as today | Measure limit; preserve inert rendering. |

## 7. Schema manifest and operator-run bootstrap

**Design decision:** no application start-up creates or mutates Catalyst resources. A future operator-only manifest, such as `backend/anvaya/platform/catalyst/schema_manifest.v1.json`, declares table names, columns, max lengths, PII flags, unique/mandatory rules, and required indexes/search indexes. A separate explicit command inspects the target project, creates only missing manifest objects when authorized, and writes a canonical schema-manifest version record.

Bootstrap order: schema ledger → users/source systems → source records/transforms → entities/cases/edges/evidence → imports/trust → investigations/messages → reports/versions/reviews → audit. It must be idempotent, report partial state, never destructively alter/truncate, and provide no automatic rollback claim. Synthetic sandbox seeding is explicit and deterministic; production seeding is prohibited.

## 8. Security and error boundaries

- Use a least-privilege service identity and a secret reference injected by the deployment environment; never commit OAuth tokens, credential files, project IDs, or raw Catalyst errors.
- Project and environment are selected only by trusted configuration. Catalyst mode remains explicit and never falls back to SQLite.
- The adapter accepts only existing typed repository requests. No browser/client value becomes a table name, ZCQL fragment, order clause, feature weight, graph expression, or raw query.
- Preserve service-owned role, jurisdiction, masking, selected-source, and report-assignment checks before reads and after row normalization.
- Redact request bodies, authorization headers, token hashes, payloads, and raw provider exceptions from logs/audit. Translate Catalyst HTTP/SDK failures to current safe `ApiError` envelopes with request ID.
- Use bounded timeouts, narrow retry only for demonstrably idempotent reads/writes, exponential backoff, and reconciliation for unknown write outcome. Do not retry multi-table workflow writes until transaction behavior is proved.

## 9. Future adapter structure (not implemented)

| Future file | Responsibility |
|---|---|
| `backend/anvaya/platform/catalyst/client.py` | narrow injected HTTP-or-SDK client protocol: table metadata, row CRUD, fixed ZCQL execution; no domain logic. |
| `backend/anvaya/platform/catalyst/zcql_templates.py` | immutable named query templates, projection lists, fixed allowlists, literal encoding. |
| `backend/anvaya/platform/catalyst/normalization.py` | Catalyst row/system-column → plain canonical record, date/boolean/ID conversion, no raw row leakage. |
| `backend/anvaya/platform/catalyst/errors.py` | safe provider error classification/redaction. |
| `backend/anvaya/platform/catalyst/repository.py` | `CatalystRepository` implementation of the existing `Repository` contract; explicit no-fallback behavior. |
| `backend/anvaya/platform/catalyst/idempotency.py` | only after transaction discovery: operation state/reconciliation helpers. |
| `backend/anvaya/platform/catalyst/schema_manifest.v1.json` | operator-reviewed schema specification; not an auto-provisioner. |
| `backend/tests/fakes/catalyst_datastore.py` | deterministic fake client for unit/contract tests, no network. |

**Client choice:** begin with a local protocol plus fake client, then select SDK versus direct REST only after target runtime/support verification. REST is documented and makes HTTP/auth behavior explicit; a Python SDK might reduce boilerplate but must not be imported until license/runtime/version and transaction capabilities are verified. This avoids locking the Flask runtime to an unverified SDK.

## 10. Test strategy

| Test layer | Required coverage |
|---|---|
| Unit (offline) | literal encoding, fixed-template selection, row normalization, timestamp conversion, safe errors, no secret leakage, capability states, retry/idempotency decision logic. |
| Contract (offline) | existing repository contract against SQLite and fake Catalyst: deterministic order, filters, immutability, append-only behavior, no cursor/connection leakage, policy/masking regression. |
| Sandbox (opt-in) | manifest inspection, canonical-ID unique behavior, CRUD, row lookup/update targeting, mandatory/null defaults, FK/cascade behavior, timestamp/timezone handling, 10k limits, JSON/Unicode, joins, five-condition limit, four-join ceiling, SELECT 20-column/300-row caps, OFFSET/LIMIT, concurrent duplicate inserts, retry/timeout partial writes, transaction/conditional-update behavior. |
| Full regression | all existing backend/frontend suites in SQLite mode. Catalyst tests must be opt-in and must never run in default CI without an explicit sandbox credential/configuration. |

## 11. Decision gates and blockers

| Gate | Why it matters | Official evidence / sandbox test | Safe default | Can coding start? |
|---|---|---|---|---|
| Target project/environment | adapter cannot identify tables safely | REST metadata has project/environment parameters; validate target isolation | placeholder unavailable | client/fake code only |
| SDK vs REST | dependency/auth/runtime support | REST documented; SDK parity unknown for this Flask runtime | protocol + fake client | yes, no live client |
| table/column limits | 27+ tables and wide reports/payloads | 100 custom columns/table in dev documented; test manifest | no resource creation | manifest design only |
| unique/composite constraints | session/source/report version integrity | single-column unique documented; composite not found | derived unique keys | reads only; writes blocked pending test |
| FK/cascade | referential behavior | FK + Null/Cascade documented | canonical-ID application checks | yes, do not rely on cascade |
| transactions/CAS | report/import atomicity | primary store called transaction-oriented, API semantics not found | disable complex writes | reads yes; complex writes no |
| ZCQL joins/subqueries | SEARCH/DISCOVER/report aggregation | 4 joins, 5 WHERE, V2 subqueries documented | bounded multi-query assembly | yes, fake/templates |
| OFFSET/LIMIT and ordering | current API envelopes | LIMIT offset,value documented | canonical tie-breaks | yes, sandbox required before production |
| Text/JSON/HTML limits | source payload and reports | Text/Encrypted Text 10k documented; no JSON type listed | measure/reject overflow; no artifact assumption | small reads yes; report/import writes blocked |
| runtime/request limits and rate limits | timeouts/retry behavior | not verified in consulted docs | conservative adapter timeout | need platform confirmation |
| sandbox credentials | live validation | deployment-specific | no connection | offline code only |
| File Store vs Stratus | reports/payload overflow | explicitly deferred | no artifact migration | Data Store small-content adapter only |

## 12. Safe future implementation sequence

1. **M7.2B-1:** offline low-level client protocol, fixed-template registry, literal encoder, normalization, fake client, and no-network unit tests.
2. **M7.2B-2:** fake-client-backed small read-only adapter for user/source/case/source-record/schema contract tests; no app wiring or live transport.
3. **M7.2B-3:** fake-client-backed investigation, selected-source JSON, and query-history read contract tests; no app wiring or live transport.
4. **M7.2B-4:** fake-client-backed bounded SEARCH candidate read contract using one fixed logical template; no app wiring or live transport.
5. **M7.2B-5:** fake-client-backed bounded DISCOVER candidate and relationship-edge read contracts; no app wiring or live transport.
6. **M7.2B-6:** fake-client-backed Case 360 and Source Passport reads using bounded fixed templates; no application wiring or transport. Entity CASE projection, joins, text/JSON limits, and ordering remain sandbox gates.
7. **M7.2B-7:** sandbox manifest inspection and read-only schema/capability validation; no provisioning. Resolve type, ID, pagination, query, and limit gates before any application wiring.
8. **M7.2B-8:** sandbox manifest inspection and read-only schema/capability validation; no provisioning. Resolve type, ID, pagination, query, and limit gates before any application wiring.
9. **M7.2B-9:** sessions and audit single-row write support only after unique/update semantics pass sandbox tests.
10. **M7.2B-10:** report/review lifecycle only after proven multi-row transaction or an explicitly accepted journal/reconciliation design.
11. **M7.2B-11:** import commit only after transaction/unique/partial-write reconciliation tests pass.
12. **M7.2B-12:** opt-in sandbox contract suite, concurrency/race tests, operational runbook, and a go/no-go review before any deployment work.

No block above authorizes AppSail, Catalyst Authentication, File Store/Stratus, schema creation, ZCQL execution against a project, or deployment. Those require separate explicit scope and target-project validation.

## M7.2B-2 implementation note (offline only)

The repository now contains a fake-client-only `CatalystReadOnlyRepository` for contract testing. It maps seven immutable, unverified templates to active user by username, user by canonical ID, source-system list/by ID, case by canonical ID, source record by canonical ID, and schema-version inspection. It is not selected by the Flask application factory and is not a live transport. Exact reads treat duplicate response rows as malformed/conflicting rather than choosing one; canonical ANVAYA IDs remain the API identity while a provider row ID is isolated in `_catalyst_rowid` for adapter-internal parity tests. All write and broader read methods deliberately return `CATALYST_NOT_IMPLEMENTED`.

This changes none of the decision gates above: final ZCQL parameter encoding, Data Store table/column presence, uniqueness, joins, pagination, timezones, text limits, transactions, authentication, and service credentials require opt-in sandbox validation. No credentials were read, no SDK was imported, no request was sent to Catalyst, and no schema resource was created.

### M7.2B-3 implementation note (offline only)

The fake-backed adapter now also proves only the existing repository reads for canonical investigations and scoped query-history messages. The stored selected-source snapshot remains compact JSON text rather than a new table: the adapter rejects malformed/non-list/duplicate/invalid source IDs but does not mutate or reinterpret the stored string. Query plans remain validated JSON text. The future Data Store templates use fixed owner/investigation constraints and fixed caps/order; their literal syntax, JSON/text limits, filtering, and ordering behavior have not been sent to or verified against Catalyst. Investigation creation, source replacement, history creation, confirmation, and all other writes remain unavailable.

### M7.2B-4 implementation note (offline only)

One fixed, unverified logical SEARCH-candidate template now accepts the existing typed `CaseSearchFilter` without accepting raw text, a sort expression, table name, column name, join, or query fragment. It carries bounded optional identifier/offence/status/date/location/entity/source parameters plus limit/offset. The fake-backed adapter applies deterministic `incident_at DESC, id ASC` ordering and validates every returned case/source field visible in the current SQLite candidate projection. A filter with more than one entity identifier is deliberately unsupported rather than silently broadened. Entity joins, optional-predicate syntax, `IN` encoding, date semantics, offsets, joins, index requirements, and provider limits have not been executed or verified against Catalyst. This is neither a live transport nor an application-wired SEARCH implementation.

### M7.2B-5 implementation note (offline only)

Two more fixed, unverified logical templates now cover the existing bounded discovery-candidate join and stored relationship-edge query. Discovery takes only preselected seed cases/source systems plus offset/limit; it preserves multiple relationship rows for the same candidate case because SQLite already returns them. The edge request accepts only the existing relationship-type allowlist, source-system list, and capped edge limit. The fake-backed adapter validates result-visible source scope, endpoints, edge uniqueness, and ordering, but intentionally does not traverse a graph or create reverse edges. Fixed join syntax, repeated source scope across discovery edge/link provenance, `IN` encoding, provider ordering, offsets, and index behavior remain unverified sandbox gates. No live transport or application wiring exists.

### M7.2B-6 implementation note (offline only)

Fixed, unverified templates now cover the existing Case 360 entity/evidence/forensic/trust-issue sections and Source Passport joined source record/transformation history. The adapter accepts only canonical IDs, retains fixed provider projections, validates visible scope and duplicate identifiers, isolates provider row IDs, and returns no raw transport fields. Entity types are a fixed five-value allowlist; source payload JSON is retained as existing text rather than transported into a new response. Case policy, jurisdiction, masking, warnings, and timeline/provenance shaping remain service-owned. The CASE-style entity projection, joins, provider result limits/order, transformation tie-break behavior, JSON/text limits, and live syntax remain explicit sandbox gates. No write operation, live transport, live ZCQL, credential access, schema activity, or Flask wiring was added.

### M7.2B-7 implementation note (offline only)

The fake-backed adapter now includes the existing bounded Case DNA and Evidence Graph stored-edge reads plus all/case-scoped Record Assurance trust-issue reads. Every request remains a typed server-side request; callers cannot supply a feature name, weight, graph expression, ordering expression, table, or column. The repository returns stored edges only, with fixed node/relationship allowlists, source-restriction joins represented only in immutable templates, deterministic ID ordering, duplicate rejection, and the existing Evidence Graph edge cap. Case DNA similarity, rankings, explanations, policy, masking, and all disclaimers remain service-owned. Evidence Graph does not traverse paths or infer relationships. Assurance reads stored issues only and does not calculate a score. Source joins/IN-lists, provider result ordering/limits, graph-edge behavior, and final template syntax are not live-verified. No live transport, ZCQL, schema validation, writes, credentials, SDK, or Flask wiring exists.

### M7.2B-8 implementation note (offline only)

The fake-backed adapter also supports fixed report, version, active-Supervisor, and review-history reads. It preserves owner/reviewer scopes, current-version join semantics, descending version order, chronological review history, and bounded list sizes. HTML, notes, and sections JSON remain stored strings; no File Store/Stratus work is introduced. Writes, lifecycle state changes, review decisions, authentication, and audit remain unavailable. Live joins, pagination, ordering, uniqueness, conditional updates, and text/HTML limits are sandbox decision gates.

### D-3 future Data Store impact (design only)

The local canonical model now plans three future tables: `arrest_surrender_events` (canonical ID, case foreign reference, fixed `ARREST`/`SURRENDER` enum, event time, temporary unit/officer/court reference strings, source-record ID), `arrest_accused_links` (canonical ID, event/person/case-role references, optional positive sequence, source-record ID), and `chargesheets` (canonical ID, case reference, filed time, fixed `A_CHARGESHEET`/`B_FALSE`/`C_UNDETECTED` enum, bounded summary, source-record ID). Required future indexes are case-plus-time for events/chargesheets and event-plus-sequence for links. Unique source-record IDs and event-person/event-role pairs require Data Store constraint validation. The same-case-ACCUSED link rule is currently a SQLite trigger and will require a transactional conditional validation or a reconciliation journal in Catalyst. Multi-row import must atomically write event, links, source records, transformations, and factual edges or detect/reconcile partial writes. Provider enum enforcement, foreign-key behavior, trigger alternatives, joins, pagination, timestamps, uniqueness, and transaction semantics remain sandbox gates. No Catalyst template, schema resource, SDK, credential, request, or live ZCQL was added.
# D-4 future Data Store impact

Future Catalyst schema work must provision organisation reference tables with canonical string IDs, unique scoped codes, active flags, source-record links, and indexes on district/state, unit/district, employee/unit, court/district, and case organisation references. Multi-table hierarchy validation and conditional update behaviour remain sandbox gates. No live Data Store schema, query, transport, SDK, or credentials were added.
