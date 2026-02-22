# Deploy to Google Cloud Run with GOOGLE_API_KEY from .env
# Usage: .\deploy.ps1
# Prerequisites: gcloud CLI, Docker, and an existing Cloud Run service

param(
    [string]$Project = "",
    [string]$Region = "us-central1",
    [string]$ServiceName = "resume-rag",
    [int]$MinInstances = 1  # Keep 1 warm instance to avoid cold-start 503 on first Ask (costs ~\$40/mo)
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Load GOOGLE_API_KEY from .env
$envPath = Join-Path $scriptDir ".env"
if (-not (Test-Path $envPath)) {
    Write-Error ".env not found. Create it from .env.example and add GOOGLE_API_KEY."
    exit 1
}

$apiKey = ""
Get-Content $envPath | ForEach-Object {
    if ($_ -match "^GOOGLE_API_KEY=(.+)$") {
        $apiKey = $matches[1].Trim()
    } elseif ($_ -match "^GEMINI_API_KEY=(.+)$" -and -not $apiKey) {
        $apiKey = $matches[1].Trim()
    }
}

if (-not $apiKey -or $apiKey -eq "your-gemini-key-here") {
    Write-Error "GOOGLE_API_KEY or GEMINI_API_KEY not set in .env"
    exit 1
}

# Use default project from gcloud if not specified
if (-not $Project) {
    $Project = (gcloud config get-value project 2>$null)
    if (-not $Project) {
        Write-Error "No project set. Run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    }
}

Write-Host "Deploying to Cloud Run: $ServiceName (project: $Project, region: $Region)" -ForegroundColor Cyan
Write-Host "GOOGLE_API_KEY will be set from .env" -ForegroundColor Cyan
if ($MinInstances -gt 0) {
    Write-Host "Min instances: $MinInstances (keeps instance warm; avoids cold-start 503)" -ForegroundColor Cyan
}

# Build and deploy; 4Gi memory for TensorFlow; min-instances keeps one warm to avoid cold-start timeouts
& gcloud run deploy $ServiceName `
    --source . `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --memory 4Gi `
    --timeout 300 `
    --min-instances $MinInstances `
    --set-env-vars "GOOGLE_API_KEY=$apiKey"
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n--- Deploy failed (exit code $LASTEXITCODE). See gcloud output above. ---" -ForegroundColor Red
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "  gcloud auth login" -ForegroundColor Yellow
    Write-Host "  gcloud services enable run.googleapis.com cloudbuild.googleapis.com" -ForegroundColor Yellow
    Write-Host "  gcloud config set project YOUR_PROJECT_ID" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nDeploy complete. Your service URL:" -ForegroundColor Green
gcloud run services describe $ServiceName --region $Region --format "value(status.url)"
