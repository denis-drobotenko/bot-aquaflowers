# Deploy bot to Google Cloud Run
Write-Host "Starting deployment..." -ForegroundColor Green

# Generate unique deploy ID for session management
$deploy_id = Get-Date -Format "yyyyMMdd-HHmmss"
Write-Host "Generated deploy ID: $deploy_id" -ForegroundColor Cyan

# Критические тесты компонентов
Write-Host "Running critical component tests..." -ForegroundColor Yellow
$env:DEPLOY_ID = $deploy_id

# Тест 1: Конфигурация
Write-Host "Testing configuration..." -ForegroundColor Cyan
python tests/test_config.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "CONFIG TEST FAILED! Deploy cancelled." -ForegroundColor Red
    exit 1
}

# Тест 2: AI сервис
Write-Host "Testing AI service..." -ForegroundColor Cyan
python tests/test_ai.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "AI TEST FAILED! Deploy cancelled." -ForegroundColor Red
    exit 1
}

# Тест 3: Каталог
Write-Host "Testing catalog service..." -ForegroundColor Cyan
python tests/test_catalog.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "CATALOG TEST FAILED! Deploy cancelled." -ForegroundColor Red
    exit 1
}

# Тест 4: База данных
Write-Host "Testing database..." -ForegroundColor Cyan
python tests/test_database.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "DATABASE TEST FAILED! Deploy cancelled." -ForegroundColor Red
    exit 1
}

# Тест 5: WhatsApp
Write-Host "Testing WhatsApp client..." -ForegroundColor Cyan
python tests/test_whatsapp.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "WHATSAPP TEST FAILED! Deploy cancelled." -ForegroundColor Red
    exit 1
}

Write-Host "All critical tests passed!" -ForegroundColor Green

# Deploy to Cloud Run with deploy ID
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy auraflora-bot --source . --region asia-southeast1 --platform managed --allow-unauthenticated --memory 1Gi --cpu 1 --set-env-vars DEPLOY_ID=$deploy_id
if ($LASTEXITCODE -eq 0) {
    Write-Host "Deploy completed successfully!" -ForegroundColor Green
    Write-Host "Deploy ID: $deploy_id" -ForegroundColor Cyan
} else {
    Write-Host "Deploy failed!" -ForegroundColor Red
    exit 1
} 