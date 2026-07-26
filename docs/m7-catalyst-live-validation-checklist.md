# HISTORICAL DESIGN MATERIAL — NOT FINAL DEPLOYMENT INSTRUCTIONS

# Catalyst Live Validation Checklist

All items are pending. Run only after explicit authorization for a non-production sandbox and approved secret handling.

## A. Before access

- [ ] Authorization names the sandbox project/environment and approved operators.
- [ ] No real FIR, citizen, personnel, court, or confidential PDF data is available to the test.
- [ ] Credentials are supplied through approved secret handling, never repository files, command output, or frontend code.
- [ ] SQLite backup and rollback owner are identified.

## B. Resource and hosting validation

- [ ] AppSail supports the chosen Python/runtime/build/port/health configuration.
- [ ] Data Store availability and row/table limits are confirmed from official console/docs.
- [ ] Authentication and API Gateway service availability are confirmed.
- [ ] Frontend hosting SPA fallback, approved origin, and static asset behavior are confirmed.

## C. Schema and fixed-query validation

- [ ] Validate table/column type, nullable, text/JSON length, canonical ID, and provider-row-ID behavior.
- [ ] Validate indexes, uniqueness, active/reference behavior, join support, fixed ordering, and LIMIT/OFFSET.
- [ ] Validate every fixed template in `query-template-manifest.json`; do not test arbitrary ZCQL.
- [ ] Validate multi-row transaction/partial failure/retry behavior before enabling any write category.

## D. Application smoke set

- [ ] Safe public health and authenticated detailed health.
- [ ] Auth mapping/login/logout and denied unmapped user.
- [ ] Source list, FIR Search, Case 360, Related Cases, graph, assurance, reports, review, masking, source filtering, and audit.
- [ ] Unavailable/stale/restricted source, partial case section, empty result, and safe error behavior.

## E. Rollback test

- [ ] Disable the Catalyst route/configuration.
- [ ] Confirm explicit Catalyst mode returns safe unavailable behavior and never selects SQLite.
- [ ] Confirm the local SQLite workflow remains separately usable.
- [ ] Retain safe evidence of the test and no real data.
