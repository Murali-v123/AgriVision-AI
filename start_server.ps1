# AgriVision AI - Unified Server Launcher
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  Starting AgriVision AI Unified Full-Stack Server" -ForegroundColor Green
Write-Host "  (Frontend + Backend REST API + CNN Crop Disease + ML)" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green

$Py = "C:\Users\KANNAN\.local\bin\python3.11.exe"
if (-not (Test-Path $Py)) {
    $Py = "python"
}

$RootDir = $PSScriptRoot

Write-Host "Starting Unified Server on port 8000..." -ForegroundColor Cyan
Write-Host "Opening browser at http://127.0.0.1:8000/login.html..." -ForegroundColor Yellow

# Open browser after 2 seconds
Start-Job -ScriptBlock { Start-Sleep -Seconds 2; Start-Process "http://127.0.0.1:8000/login.html" } | Out-Null

Set-Location "$RootDir\backend"
& $Py manage.py runserver 127.0.0.1:8000
