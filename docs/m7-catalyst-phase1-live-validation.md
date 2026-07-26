# HISTORICAL DESIGN MATERIAL — NOT FINAL DEPLOYMENT INSTRUCTIONS

# Catalyst Phase 1 Live Validation Record

Status: completed for the authorised non-production Development environment only.

This record captures inspection and schema-validation work completed under the explicit restriction that no Production access, AppSail deployment, API Gateway enablement, Authentication configuration, data seeding, merge, or `main` modification was authorised.

## Verified environment and tooling

- Official Catalyst CLI login completed using the provider-approved flow.
- Active project/environment inspected in the Catalyst console and used only in Development.
- AppSail, Data Store, Authentication, API Gateway, and frontend-hosting capabilities were available for inspection.
- AppSail was not deployed.
- API Gateway remained disabled.
- Catalyst Authentication remained unconfigured.
- No frontend application was created.
- No Production action was performed.

## Data Store behavior verified

Catalyst automatically created these provider-managed columns for each table:

- `ROWID` (`bigint`)
- `CREATORID` (`bigint`)
- `CREATEDTIME` (`datetime`)
- `MODIFIEDTIME` (`datetime`)

A temporary Development table was created and deleted successfully before the authorised schema work, confirming reversible table creation/deletion behavior.

The following seven authorised Development tables were created:

1. `source_systems`
2. `source_records`
3. `states`
4. `districts`
5. `police_unit_types`
6. `police_units`
7. `cases`

No rows were inserted or seeded.

## Provider-specific schema findings

- Catalyst rejected `priority` as a reserved column name.
- The live Development schema therefore uses `source_priority` in `source_systems`.
- Application/provider mapping must translate ANVAYA's canonical `priority` field to `source_priority` for Catalyst operations.
- `payload_json` in `source_records` was created as `text`, mandatory, not search-indexed, and marked PII/ePHI.
- Application-owned string identifiers use `varchar`; Catalyst `ROWID` remains provider-internal.
- Reference and lookup fields were created with the authorised mandatory/search-index settings captured during the console walkthrough.
- The `cases` table contains the four required manifest fields and the authorised optional compatibility fields created during validation.

## ZCQL read-only validation

The following read-only query shapes executed successfully in Development:

```sql
SELECT id FROM source_systems;
```

```sql
SELECT id, name, status
FROM source_systems
WHERE status = 'Fresh';
```

Both returned zero rows, as expected because no data was seeded.

This validates basic table resolution, projection, and equality filtering only. It does not validate joins, pagination, ordering, transactions, mutation behavior, partial failure, retry behavior, or the complete fixed-query manifest.

## Repository state at completion

Before this documentation update:

- Branch: `feat/m7-zoho-catalyst-deployment`
- Verified base commit: `2f4edb216b7ca34e0d64dd9ed4f42fa4a1d81a43`
- Local working tree was clean.
- Local and remote branch heads were aligned.

No credentials, tokens, project IDs, organisation IDs, provider row IDs, or `.catalystrc` contents are recorded here.

## Still deferred and not authorised

- AppSail creation or deployment
- API Gateway enablement
- Catalyst Authentication configuration
- Frontend hosting creation
- Data seeding or import execution
- Write-query or transaction testing
- Full fixed-query manifest validation
- Production access or deployment
- Merge, pull request merge, or `main` modification
