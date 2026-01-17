#!/bin/bash

# SalesShortcut - Start All Services
# ===================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  SalesShortcut - Starting All Services${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables from .env
if [ -f .env ]; then
    echo -e "${GREEN}✓${NC} Loading environment from .env file..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
else
    echo -e "${RED}✗${NC} .env file not found!"
    exit 1
fi

# Check critical environment variables
echo ""
echo "Checking configuration..."
if [ -z "$GOOGLE_API_KEY" ]; then
    echo -e "${RED}✗${NC} GOOGLE_API_KEY is not set in .env"
    exit 1
else
    echo -e "${GREEN}✓${NC} GOOGLE_API_KEY: Set (${#GOOGLE_API_KEY} chars)"
fi

if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo -e "${YELLOW}⚠${NC} GOOGLE_CLOUD_PROJECT not set - BigQuery disabled"
else
    echo -e "${GREEN}✓${NC} GOOGLE_CLOUD_PROJECT: $GOOGLE_CLOUD_PROJECT"
fi

if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
    echo -e "${YELLOW}⚠${NC} GOOGLE_MAPS_API_KEY not set - Using mock Indian business data"
else
    echo -e "${GREEN}✓${NC} GOOGLE_MAPS_API_KEY: Set"
fi

if [ -z "$EMAIL_USERNAME" ]; then
    echo -e "${YELLOW}⚠${NC} EMAIL_USERNAME not set - Email outreach disabled"
else
    echo -e "${GREEN}✓${NC} EMAIL_USERNAME: $EMAIL_USERNAME"
fi

if [ -z "$ELEVENLABS_API_KEY" ]; then
    echo -e "${YELLOW}⚠${NC} ELEVENLABS_API_KEY not set - Phone calls disabled"
else
    echo -e "${GREEN}✓${NC} ELEVENLABS_API_KEY: Set"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo "Starting services..."
echo ""

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1 || curl -s "$url/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $name is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    echo -e "${YELLOW}⚠${NC} $name may not be ready (timeout)"
    return 1
}

# Start Lead Finder (Port 8081)
echo "Starting Lead Finder service..."
python -m lead_finder > logs/lead_finder.log 2>&1 &
LEAD_FINDER_PID=$!
echo "  PID: $LEAD_FINDER_PID"

# Start Lead Manager (Port 8082)
echo "Starting Lead Manager service..."
python -m lead_manager > logs/lead_manager.log 2>&1 &
LEAD_MANAGER_PID=$!
echo "  PID: $LEAD_MANAGER_PID"

# Start SDR Agent (Port 8084)
echo "Starting SDR Agent service..."
python -m sdr > logs/sdr.log 2>&1 &
SDR_PID=$!
echo "  PID: $SDR_PID"

# Start Gmail Listener (Port 8083)
echo "Starting Gmail Listener service..."
python -m gmail_pubsub_listener.gmail_listener_service > logs/gmail_listener.log 2>&1 &
GMAIL_PID=$!
echo "  PID: $GMAIL_PID"

# Start UI Client (Port 8000)
echo "Starting UI Dashboard..."
python -m ui_client > logs/ui_client.log 2>&1 &
UI_PID=$!
echo "  PID: $UI_PID"

echo ""
echo "Waiting for services to start..."
sleep 3

# Check service health
echo ""
wait_for_service "http://localhost:8081" "Lead Finder (8081)"
wait_for_service "http://localhost:8082" "Lead Manager (8082)"
wait_for_service "http://localhost:8084" "SDR Agent (8084)"
wait_for_service "http://localhost:8083" "Gmail Listener (8083)"
wait_for_service "http://localhost:8000" "UI Dashboard (8000)"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All Services Started Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📊 Dashboard:      http://localhost:8000"
echo "🔍 Lead Finder:    http://localhost:8081"
echo "📋 Lead Manager:   http://localhost:8082"
echo "📧 SDR Agent:      http://localhost:8084"
echo "📬 Gmail Listener: http://localhost:8083"
echo ""
echo "📝 Logs are in: $SCRIPT_DIR/logs/"
echo ""
echo -e "${YELLOW}Features Status:${NC}"
if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
    echo "  🏪 Lead Search: Mock Indian business data"
else
    echo "  🏪 Lead Search: Real Google Maps data"
fi
if [ -z "$EMAIL_USERNAME" ]; then
    echo "  📧 Email: Disabled (configure EMAIL_USERNAME)"
else
    echo "  📧 Email: Enabled"
fi
if [ -z "$ELEVENLABS_API_KEY" ]; then
    echo "  📞 Phone: Disabled (configure ELEVENLABS_API_KEY)"
else
    echo "  📞 Phone: Enabled"
fi
echo ""
echo "To stop all services, run: ./stop_all.sh"
echo ""

# Save PIDs for later cleanup
echo "$LEAD_FINDER_PID $LEAD_MANAGER_PID $SDR_PID $GMAIL_PID $UI_PID" > .pids

echo -e "${GREEN}✓ Ready to use!${NC} Open http://localhost:8000 in your browser"
