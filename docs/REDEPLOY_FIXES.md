# Redeploy fixes — July 2026

This update is for the public synthetic datathon demonstration.

## Fixed before redeployment

- Corrected Flask static-asset routing: `/assets/*` now serves the Vite build assets instead of the JSON API 404 response.
- Added visible, editable guided scenarios in the Investigation Portal:
  - exact FIR / Case 360;
  - shared complainant;
  - repeat accused indicator;
  - duplicate synthetic identifier assurance.
- A scenario fills filters only. It never executes a search automatically.
- Added a protected-path test that proves public demo → investigation → query preview → search → Case 360 → native cited PDF works together.
- Extended the deployment smoke check to verify a built frontend asset is returned as an asset, not JSON.
- Made the SQLite migration loader explicitly skip two historical superseded duplicate-number drafts. The canonical sequence remains `001` through `016`.
- Exposed the existing redacted conversation-PDF export in the mounted Investigation Chat.
- Wired ordinary chat questions to editable query previews and the existing context-aware follow-up endpoint; retrieval still requires an explicit **Search records** confirmation.
- Rotated predefined SQLite demo-user password hashes when deployment configuration changes, preventing an existing demo database from retaining stale credentials.
- Focused and scrolled the authenticated workspace into view after public-demo or private-review login.
- Increased the portal test's asynchronous public-demo wait so the full parallel frontend suite is stable on slower runners.
- Moved deployment-suite pytest files to a unique OS temp directory to avoid repository-local Windows cleanup locks.

## Demonstration values

| Scenario | Fill / click | Expected use |
| --- | --- | --- |
| One FIR | `SYN-CRIME-00001` | Open Case 360 and download the cited case dossier PDF. |
| Shared reporter | `Synthetic Person 0002` + `COMPLAINANT` | Review two records sharing a recorded complainant; do not infer identity, coordination or guilt. |
| Repeat accused | `Synthetic Person 0001` + `ACCUSED` | Review recorded repeat involvement and the cited record history. |
| Duplicate identifier | `SYN-CRIME-DUP-001` | Open Case 360 and review Record Assurance before taking any action. |

All records remain synthetic fixtures. This package is a working hackathon prototype, not an operational police deployment.
