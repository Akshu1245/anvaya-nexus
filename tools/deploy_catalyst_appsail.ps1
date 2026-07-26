[CmdletBinding()]
param(
    [string]$AppSailName = "AppSail",
    [string]$ImageTag = "anvaya-nexus:submission",
    [string]$ArchiveName = "anvaya-nexus-submission.tar",
    [int]$Port = 5000,
    [switch]$DryRun,
    [switch]$ArchiveOnly,
    [switch]$Deploy,
    [switch]$AllowProductionTarget
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$containerName = "anvaya-submission-smoke"
$archivePath = Join-Path $root $ArchiveName
$pytestTemp = Join-Path ([IO.Path]::GetTempPath()) ("anvaya-pytest-" + [guid]::NewGuid().ToString("N"))

function Invoke-Checked([string]$Label, [scriptblock]$Command) {
    Write-Host "`n==> $Label" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "'$Name' was not found in PowerShell. Install it before continuing."
    }
}

function Test-ContainerExists([string]$Name) {
    $existing = docker ps -aq --filter "name=^/$Name$" 2>$null
    return -not [string]::IsNullOrWhiteSpace(($existing | Out-String))
}

function Remove-ContainerIfExists([string]$Name) {
    if (Test-ContainerExists $Name) {
        Write-Host "Removing existing container '$Name'..." -ForegroundColor DarkYellow
        docker rm -f $Name | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to remove existing container '$Name'."
        }
    }
}

Set-Location $root
Write-Host "ANVAYA Docker Custom Runtime AppSail preparation" -ForegroundColor Green
Write-Host "Repository: $root"
Write-Host "Archive: $archivePath"
Write-Host "Mode: $(if($DryRun){'Dry run'}elseif($ArchiveOnly){'Archive only'}elseif($Deploy){'Deploy requested'}else{'Archive only unless -Deploy is supplied'})"

Require-Command docker
Require-Command catalyst
Require-Command npm

$pythonCmd = $null
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (Test-Path $venvPython -PathType Leaf) {
    $pythonCmd = $venvPython
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = (Get-Command python).Source
} else {
    throw "Python was not found. Create .venv or install Python before continuing."
}
Write-Host "Using Python: $pythonCmd"

& docker --version
& catalyst --version
& npm --version
& $pythonCmd --version

if (
    -not (Test-Path "Dockerfile" -PathType Leaf) -or
    -not (Test-Path "backend\anvaya\__init__.py" -PathType Leaf) -or
    -not (Test-Path "frontend\package.json" -PathType Leaf)
) {
    throw "Required Docker, backend, or frontend source files are missing."
}

Invoke-Checked "Checking Docker daemon" {
    docker info --format '{{.ServerVersion}}' | Out-Host
}

Invoke-Checked "Checking Catalyst authentication" {
    catalyst whoami | Out-Host
}

Invoke-Checked "Listing selected Catalyst project access" {
    catalyst project:list | Out-Host
}

$appsailHelp = (& catalyst deploy appsail --help 2>&1 | Out-String)
if ($appsailHelp -notmatch "--source" -or $appsailHelp -notmatch "--port") {
    throw "Installed Catalyst CLI does not advertise the required AppSail --source/--port options. Update the CLI or use the Catalyst console; no archive will be deployed."
}

if ($DryRun) {
    Write-Host "Dry run completed. No dependencies, image, container, archive, or Catalyst deployment were created." -ForegroundColor Yellow
    Write-Host "When ready, run: .\tools\deploy_catalyst_appsail.ps1 -ArchiveOnly"
    Write-Host "After confirming the target is Development, run: .\tools\deploy_catalyst_appsail.ps1 -Deploy"
    exit 0
}

try {
    Invoke-Checked "Installing locked frontend dependencies" {
        npm --prefix frontend ci --include=dev
    }

    Invoke-Checked "Running frontend lint" {
        npm --prefix frontend run lint
    }

    Invoke-Checked "Running frontend tests" {
        npm --prefix frontend run test -- --run
    }

    Invoke-Checked "Building production frontend" {
        npm --prefix frontend run build
    }

    Invoke-Checked "Running backend tests" {
        & $pythonCmd -m pytest backend/tests -q -p no:cacheprovider --basetemp=$pytestTemp
    }

    Invoke-Checked "Building Docker image" {
        docker build -t $ImageTag .
    }

    $sessionSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 48 | ForEach-Object { [char]$_ })
    $demoPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ })

    Remove-ContainerIfExists $containerName

    Invoke-Checked "Starting local production smoke container" {
        docker run -d --name $containerName -p 8000:5000 `
            -e ANVAYA_ENV=production `
            -e ANVAYA_SESSION_SECRET=$sessionSecret `
            -e ANVAYA_DEMO_PASSWORD=$demoPassword `
            -e ANVAYA_PUBLIC_DEMO_MODE=true `
            -e ANVAYA_ALLOWED_ORIGINS=https://localhost `
            -e ANVAYA_HTTPS_ENABLED=true `
            -e ANVAYA_TRUST_PROXY=true `
            $ImageTag | Out-Host
    }

    Start-Sleep -Seconds 3

    $health = Invoke-RestMethod "http://localhost:8000/api/health"
    if ($health.data.status -ne "ok") {
        throw "Local health endpoint did not return status=ok."
    }

    $rootResponse = Invoke-WebRequest "http://localhost:8000/" -UseBasicParsing
    if ($rootResponse.Content -notmatch "ANVAYA") {
        throw "Local frontend root did not contain ANVAYA."
    }

    $demo = Invoke-WebRequest `
        "http://localhost:8000/api/auth/public-demo" `
        -Method Post `
        -ContentType "application/json" `
        -UseBasicParsing `
        -SessionVariable session

    if ($demo.Content -notmatch "INVESTIGATOR") {
        throw "Public-demo entry did not create the restricted Investigator session."
    }

    Remove-ContainerIfExists $containerName

    Invoke-Checked "Exporting generated Docker archive" {
        docker save --output $archivePath $ImageTag
    }

    Write-Host "Generated local archive: $archivePath" -ForegroundColor Green

    if ($ArchiveOnly -or -not $Deploy) {
        Write-Host "Archive-only completion. The archive is generated locally and ignored by Git; do not commit it." -ForegroundColor Yellow
        Write-Host "Manual Catalyst CLI command after you confirm the target is Development:"
        Write-Host "catalyst deploy appsail --name $AppSailName --source docker-archive://$ArchiveName --port $Port"
        exit 0
    }

    if (-not $AllowProductionTarget) {
        Write-Host "Confirm in Catalyst console that the selected project is the intended Development environment. Use -AllowProductionTarget only after explicit approval for a Production target." -ForegroundColor Yellow
    }

    Invoke-Checked "Deploying Docker archive to Catalyst AppSail" {
        catalyst deploy appsail `
            --name $AppSailName `
            --source "docker-archive://$ArchiveName" `
            --port $Port
    }

    Write-Host "Deployment command completed. Configure environment variables in AppSail, create the deployment, then verify /api/health and Open public demo." -ForegroundColor Green
}
finally {
    try {
        Remove-ContainerIfExists $containerName
    }
    catch {
        Write-Warning "Cleanup warning: $($_.Exception.Message)"
    }
    try {
        $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
        $resolvedPytestTemp = [IO.Path]::GetFullPath($pytestTemp)
        if (
            $resolvedPytestTemp.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase) -and
            (Test-Path -LiteralPath $resolvedPytestTemp)
        ) {
            Remove-Item -LiteralPath $resolvedPytestTemp -Recurse -Force
        }
    }
    catch {
        Write-Warning "Pytest temp cleanup warning: $($_.Exception.Message)"
    }
}
