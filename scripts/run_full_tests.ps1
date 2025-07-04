#!/usr/bin/env powershell
# Полные тесты для глубокой проверки функциональности

Write-Host "=== ЗАПУСК ПОЛНЫХ ТЕСТОВ ===" -ForegroundColor Yellow

# Запуск всех тестов
Write-Host "--- Running all tests ---" -ForegroundColor Cyan
python run_tests.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Full tests failed!" -ForegroundColor Red
    exit 1
}

Write-Host "All tests passed successfully!" -ForegroundColor Green
Write-Host "System is fully functional!" -ForegroundColor Green 