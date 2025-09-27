#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting local services..."

# Ensure we are in the project root directory (where the script is located)
cd "$(dirname "$0")"

# Source .env file if it exists to load all environment variables
if [ -f .env ]; then
  echo "Loading environment variables from .env file..."
  export $(grep -v '^#' .env | xargs)
fi

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ]; then
  echo "ERROR: Please set GOOGLE_API_KEY environment variable for Gemini LLM inference."
  exit 1
fi

export GOOGLE_MAPS_API_KEY="${GOOGLE_MAPS_API_KEY:-}"


echo "Using GOOGLE_API_KEY for Gemini LLM inference..."

# Start Lead Finder (Default Port: 8081)
echo "Starting Lead Finder service in the background..."
GOOGLE_MAPS_API_KEY="$GOOGLE_MAPS_API_KEY" python -m lead_finder &
LEAD_FINDER_PID=$!
echo "Lead Finder started with PID: $LEAD_FINDER_PID"

# Start Lead Manager (Port: 8082)
echo "Starting Lead Manager service in the background..."
python -m lead_manager --port 8082 &
LEAD_MANAGER_PID=$!
echo "Lead Manager started with PID: $LEAD_MANAGER_PID"

# Start SDR (Default Port: 8084)
echo "Starting SDR service in the background..."
python -m sdr &
SDR_PID=$!
echo "SDR started with PID: $SDR_PID"

# Start Gmail Pub/Sub Listener (Port: 8083)
echo "Starting Gmail Pub/Sub Listener service in the background..."
GOOGLE_API_KEY="$GOOGLE_API_KEY" python -m gmail_pubsub_listener.gmail_listener_service &
GMAIL_LISTENER_PID=$!
echo "Gmail Listener started with PID: $GMAIL_LISTENER_PID"

# Start UI Client (Default Port: 8000)
echo "Starting UI Client service in the background..."
python -m ui_client &
UI_CLIENT_PID=$!
echo "UI Client started with PID: $UI_CLIENT_PID"

echo "--------------------------------------------------"
echo "Local services started:"
echo "  Lead Finder:        http://127.0.0.1:8081 (PID: $LEAD_FINDER_PID)"
echo "  Lead Manager:       http://127.0.0.1:8082 (PID: $LEAD_MANAGER_PID)"
echo "  SDR:                http://127.0.0.1:8084 (PID: $SDR_PID)"
echo "  Gmail Listener:     http://127.0.0.1:8083 (PID: $GMAIL_LISTENER_PID)"
echo "  UI Client:          http://127.0.0.1:8000 (PID: $UI_CLIENT_PID)"
echo "--------------------------------------------------"
echo "Use 'kill $LEAD_FINDER_PID $LEAD_MANAGER_PID $SDR_PID $GMAIL_LISTENER_PID $UI_CLIENT_PID' or Ctrl+C to stop all services."

# Optional: Wait for all background processes to finish (uncomment if needed)
# wait
