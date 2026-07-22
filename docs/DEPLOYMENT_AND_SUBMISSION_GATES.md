# Deployment and submission gates

## Verified in this package

- Flask API and React production build run locally from one container image.
- Production startup rejects missing/short session secrets and non-HTTPS allowed origins.
- Cookies are server-side, HttpOnly, SameSite and Secure when HTTPS is enabled.
- Rate limits, request/upload size limits, audit events, role/purpose/jurisdiction enforcement and synthetic-data watermarking are implemented.
- SQLite migrations are ordered and repeatable. The demo does not require an external AI key.

## Required before declaring a live Catalyst submission

These are operational gates, not code claims. Mark them only with evidence from the approved non-production Catalyst sandbox.

- [ ] Confirm selected Catalyst project and environment are non-production.
- [ ] Validate current official CLI syntax and add the generated Catalyst service configuration without credentials in Git.
- [ ] Provision and test Catalyst Data Store/ZCQL adapter, including uniqueness, indexes, transactional writes and migration rollback.
- [ ] Replace the prototype auth adapter with Catalyst Authentication and repeat role/jurisdiction-denial tests.
- [ ] Deploy the validated container through AppSail and verify secret/environment injection outside source control.
- [ ] Configure API Gateway and frontend hosting; verify same-site HTTPS routing and CORS behavior.
- [ ] Run persistence, logout/session revocation, audit, backup/restore, rollback and resource-disable tests in the sandbox.
- [ ] Capture the live URL, service list, deployment logs/screenshots, test results, known limitations and a five-minute demo video for submission.

## Local production rehearsal

```bash
npm ci
npm --prefix frontend ci
npm run build
export ANVAYA_ENV=production
export ANVAYA_SESSION_SECRET='unique-32-plus-character-value-outside-git'
export ANVAYA_ALLOWED_ORIGINS='https://your-approved-host.example'
export ANVAYA_HTTPS_ENABLED=true
gunicorn --bind 0.0.0.0:5000 --workers 2 backend.wsgi:app
```

Use only a synthetic database during the datathon. Do not place credentials, access tokens, real FIR data, or deployment exports in Git.
