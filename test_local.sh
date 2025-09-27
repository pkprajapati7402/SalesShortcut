#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting local test services (UI Client + Lead Manager)..."

# Ensure we are in the project root directory (where the script is located)
cd "$(dirname "$0")"

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ]; then
  echo "ERROR: Please set GOOGLE_API_KEY environment variable for Gemini LLM inference."
  exit 1
fi

echo "Using GOOGLE_API_KEY for Gemini LLM inference..."

# Start Lead Manager (Port: 8082)
echo "Starting Lead Manager service in the background..."
GOOGLE_API_KEY="$GOOGLE_API_KEY" python -m lead_manager --port 8082 &
LEAD_MANAGER_PID=$!
echo "Lead Manager started with PID: $LEAD_MANAGER_PID"

# Wait a moment for Lead Manager to start
sleep 2

# Start UI Client (Port: 8000)
echo "Starting UI Client service in the background..."
GOOGLE_API_KEY="$GOOGLE_API_KEY" python -m ui_client &
UI_CLIENT_PID=$!
echo "UI Client started with PID: $UI_CLIENT_PID"

echo "--------------------------------------------------"
echo "Test services started:"
echo "  Lead Manager:       http://127.0.0.1:8082 (PID: $LEAD_MANAGER_PID)"
echo "  UI Client:          http://127.0.0.1:8000 (PID: $UI_CLIENT_PID)"
echo "--------------------------------------------------"
echo "Open http://127.0.0.1:8000 in your browser to test the application"
echo "Use 'kill $LEAD_MANAGER_PID $UI_CLIENT_PID' or Ctrl+C to stop services."

# Function to cleanup processes on script exit
cleanup() {
    echo "Stopping services..."
    kill $LEAD_MANAGER_PID $UI_CLIENT_PID 2>/dev/null || true
    exit 0
}

# Trap EXIT signal to cleanup
trap cleanup EXIT INT TERM

# Wait for all background processes
wait