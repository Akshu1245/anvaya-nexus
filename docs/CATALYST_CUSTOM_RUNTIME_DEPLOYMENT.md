# Final Catalyst deployment route

**Docker archive → Zoho Catalyst AppSail Custom Runtime is the only supported final deployment route.**

The Dockerfile compiles the React frontend and packages it with the Flask application. The final prototype uses its synthetic SQLite workflow store inside the AppSail container. Catalyst Data Store, Catalyst Authentication, API Gateway, and separate frontend hosting are not part of this final deployment and must not be claimed as integrated.

## Owner commands

From the repository root in Windows PowerShell:

```powershell
.\tools\deploy_catalyst_appsail.ps1 -DryRun
.\tools\deploy_catalyst_appsail.ps1 -ArchiveOnly
```

After confirming the selected Catalyst target and AppSail name, use:

```powershell
.\tools\deploy_catalyst_appsail.ps1 -Deploy
```

The script runs the local checks and produces a generated `*.tar` Docker archive. The archive is local-only and ignored by Git.

## Required AppSail variables

Use the exact AppSail HTTPS URL as `ANVAYA_ALLOWED_ORIGINS`, then set a unique 32+ character `ANVAYA_SESSION_SECRET`, a private 24+ character `ANVAYA_DEMO_PASSWORD`, `ANVAYA_PUBLIC_DEMO_MODE=true`, `ANVAYA_ENV=production`, `ANVAYA_STORAGE_BACKEND=sqlite`, `ANVAYA_AUTH_BACKEND=prototype`, `ANVAYA_HTTPS_ENABLED=true`, and `ANVAYA_TRUST_PROXY=true`.

Never place any of these values in Git, the video, the public UI, health output, a report, or submission evidence.
