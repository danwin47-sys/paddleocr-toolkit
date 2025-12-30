$FrontendDir = "web-frontend"

Write-Host "Starting PaddleOCR Development Environment..." -ForegroundColor Cyan

# 1. Start Backend
Write-Host "Launching Backend API (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { Write-Host '=== Backend API ===' -ForegroundColor Green; python -m paddleocr_toolkit.api.main }"

# 2. Wait a moment
Start-Sleep -Seconds 2

# 3. Start Frontend
Write-Host "Launching Next.js Frontend (Port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { Write-Host '=== Next.js Frontend ===' -ForegroundColor Green; cd $FrontendDir; npm run dev }"

Write-Host "Done! Please check the opened windows." -ForegroundColor Green
Write-Host "Frontend URL: http://localhost:3000" -ForegroundColor Gray
