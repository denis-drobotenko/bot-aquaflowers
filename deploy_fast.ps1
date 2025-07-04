# Быстрый деплой без тестов
Write-Host "Starting fast deployment..." -ForegroundColor Green

# Generate unique deploy ID for session management
$deploy_id = Get-Date -Format "yyyyMMdd-HHmmss"
Write-Host "Generated deploy ID: $deploy_id" -ForegroundColor Cyan

# Deploy to Cloud Run with deploy ID (без тестов)
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy auraflora-bot --source . --region asia-southeast1 --platform managed --allow-unauthenticated --memory 1Gi --cpu 1 --set-env-vars DEPLOY_ID=$deploy_id
if ($LASTEXITCODE -eq 0) {
    Write-Host "Deploy completed successfully!" -ForegroundColor Green
    Write-Host "Deploy ID: $deploy_id" -ForegroundColor Cyan
} else {
    Write-Host "Deploy failed!" -ForegroundColor Red
    exit 1
} 