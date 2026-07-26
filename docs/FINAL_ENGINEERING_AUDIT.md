# Final engineering audit

| Issue | File(s) | Severity | Root cause | Correction | Verification |
| --- | --- | --- | --- | --- | --- |
| Two AppSail routes appeared active | Catalyst templates, historical docs | High | Generated managed-runtime package was retained beside Docker approach | Removed active managed-runtime templates; Docker Custom Runtime is the sole active route; historical documents are marked | Documentation scan and deployment script review |
| Deployment script only built/exported | `tools/deploy_catalyst_appsail.ps1` | High | No local quality or container proof before export | Added dry-run, archive-only, explicit deploy, tool/auth checks, frontend/backend checks and local smoke container | Script reviewed; Docker execution remains owner/local evidence |
| Production public demo inherited local default password | `config.py` | High | Base config fallback applied to production | Production password is empty by default; public-demo production mode requires private 24+ character value | `test_config.py`, `test_public_demo.py` |
| Public demo needed normal rate limiting | `api/m3.py` | Medium | Login throttle applied only to password endpoint | Shared rate-limit guard for password and public-demo sessions | `test_public_demo.py` |
| Role selection was visually ambiguous | `InvestigationExperience.tsx` | Medium | Buttons had no active state | Private review controls use `aria-pressed` and active styling; Enter submits login | frontend InvestigationExperience tests |
| Generated PDF and print preview were conflated | README and demo/report docs | Medium | Legacy report wording remained after native Case 360 PDF | Documentation now distinguishes native cited brief from printable HTML report | README/doc review and PDF tests |
| Catalyst Data Store claim conflicted with runnable demo | env/template/docs | High | Read-only experimental design was presented beside final prototype | Final Docker route explicitly uses ephemeral synthetic SQLite; no Data Store/Auth integration claim | configuration tests and final status |
| Submission status was ambiguous | final/checklist docs | Medium | Source readiness and external evidence were mixed | Added owner actions, evidence template and evidence-based sections | documentation review |
