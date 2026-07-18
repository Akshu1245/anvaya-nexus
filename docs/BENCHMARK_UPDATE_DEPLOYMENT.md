# Deploying the research-led benchmark update

This update remains synthetic-only. It adds 24 deliberately selected FIR benchmark cases and expands the FIR search experience.

## Update and validate locally

From the existing `anvaya-nexus-final` directory on Windows, copy the update files into the project, then run:

```powershell
git status --short
docker build -t anvaya-nexus:1.0.2 .
docker run -d --rm --name anvaya-nexus-smoke -p 5000:5000 `
  -e ANVAYA_ENV=production `
  -e ANVAYA_SESSION_SECRET=$TestSecret `
  -e ANVAYA_ALLOWED_ORIGINS=https://smoke.local `
  -e ANVAYA_HTTPS_ENABLED=true `
  anvaya-nexus:1.0.2
Start-Sleep -Seconds 3
Invoke-RestMethod http://localhost:5000/api/health
docker stop anvaya-nexus-smoke
```

## Deploy to the existing AppSail

```powershell
docker save --output .\anvaya-nexus-1.0.0.tar anvaya-nexus:1.0.2
catalyst deploy appsail --name AppSail --source docker-archive://anvaya-nexus-1.0.0.tar --port 5000
Invoke-RestMethod "https://appsail-50044124045.development.catalystappsail.in/api/health"
```

Then open the AppSail URL and use **Ctrl+F5**. The banner should show **24 case fixtures**.

## Demonstration searches

- `Kavya` in **Find across record fields** returns three cyber benchmark records.
- `IT_ACT` in **Act** plus `UNDER_INVESTIGATION` in **Status** returns active cyber records.
- `UDR` in **Case category** plus `UNNATURAL_DEATH` in **Minor crime head** returns two UDR review records.
- `Synthetic Accused Alpha` in **Person name** plus `ACCUSED` returns the evidence-led related-case example.

Finally commit only the source and documentation changes. Do not commit the Docker archive, `.catalystrc`, passwords, or any environment-variable values.
