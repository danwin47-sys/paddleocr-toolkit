#!/bin/bash

# PaddleOCR Toolkit - Backend & Ngrok Starter
# This script starts the FastAPI backend and creates an ngrok tunnel

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting PaddleOCR Toolkit Backend Service...${NC}"

# 1. Check/Install Ngrok
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}❌ ngrok not found!${NC}"
    echo "Please install ngrok first: brew install ngrok/ngrok/ngrok"
    exit 1
fi

# 2. Check Python Environment
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

source .venv/bin/activate

# 3. Check Dependencies
echo -e "${BLUE}🔍 Checking dependencies...${NC}"
if ! pip show uvicorn &> /dev/null; then
    echo "Installing required packages..."
    pip install -r requirements.txt
fi

# 4. Start Backend (in background)
echo -e "${GREEN}✅ Starting Uvicorn Server on port 8000...${NC}"
uvicorn paddleocr_toolkit.api.main:app --reload --port 8000 > uvicorn.log 2>&1 &
BACKEND_PID=$!

sleep 3 # Wait for backend to start

# 5. Start Ngrok
echo -e "${GREEN}✅ Starting ngrok tunnel...${NC}"
# Run ngrok in background and log to file
ngrok http 8000 --log=stdout > ngrok.log 2>&1 &
NGROK_PID=$!

echo -e "${BLUE}⏳ Waiting for ngrok to initialize...${NC}"
sleep 5

# Extract URL from log
NGROK_URL=$(grep -o "https://[a-zA-Z0-9-]*\.ngrok-free\.app" ngrok.log | head -n 1)

if [ -z "$NGROK_URL" ]; then
    echo -e "${RED}❌ Could not find ngrok URL. Check ngrok.log for details.${NC}"
    echo -e "${RED}Note: You may need to configure your authtoken: ngrok config add-authtoken <token>${NC}"
    cat ngrok.log
else
    echo -e "${GREEN}✅ Ngrok Tunnel Started!${NC}"
    echo -e "${BLUE}Public URL: ${NGROK_URL}${NC}"
    echo ""
    echo "Please update your Vercel Environment Variable NEXT_PUBLIC_API_URL with this URL."
fi

# Keep script running to keep processes alive
wait $BACKEND_PID $NGROK_PID
