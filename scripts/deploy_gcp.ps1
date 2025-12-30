# paddleocr_toolkit Deployment Script (Windows/PowerShell)

$PROJECT_ID = "YOUR_GCP_PROJECT_ID"  # Replace with your actual Project ID
$REGION = "asia-east1"               # Choose your region (e.g., taiwan)
$SERVICE_NAME = "paddleocr-backend"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "========= PaddleOCR Cloud Run Deployment =========" -ForegroundColor Cyan

# 1. Check for gcloud CLI
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Error "Google Cloud SDK (gcloud) is not installed or not in PATH."
    Exit 1
}

# 2. Build Image using Cloud Build (No local Docker needed)
Write-Host "`n[1/3] Building container image using Cloud Build..." -ForegroundColor Yellow
gcloud builds submit --tag $IMAGE_NAME .
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed."
    Exit 1
}

# 3. Deploy to Cloud Run
Write-Host "`n[2/3] Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 4Gi `
    --cpu 2 `
    --port 8080 `
    --timeout 300
    
if ($LASTEXITCODE -ne 0) {
    Write-Error "Deployment failed."
    Exit 1
}

# 4. Get Service URL
$SERVICE_URL = (gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
Write-Host "`n[3/3] Deployment Request Complete!" -ForegroundColor Green
Write-Host "Backend URL: $SERVICE_URL" -ForegroundColor Cyan
Write-Host "`nPlease update your frontend configuration with this URL."
