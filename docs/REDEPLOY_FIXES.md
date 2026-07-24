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

## Demonstration values

| Scenario | Fill / click | Expected use |
| --- | --- | --- |
| One FIR | `SYN-CRIME-00001` | Open Case 360 and download the cited case dossier PDF. |
| Shared reporter | `Synthetic Person 0002` + `COMPLAINANT` | Review two records sharing a recorded complainant; do not infer identity, coordination or guilt. |
| Repeat accused | `Synthetic Person 0001` + `ACCUSED` | Review recorded repeat involvement and the cited record history. |
| Duplicate identifier | `SYN-CRIME-DUP-001` | Open Case 360 and review Record Assurance before taking any action. |

All records remain synthetic fixtures. This package is a working hackathon prototype, not an operational police deployment.
