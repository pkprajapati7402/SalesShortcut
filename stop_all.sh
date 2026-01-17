#!/bin/bash

# SalesShortcut - Stop All Services
# ==================================

echo "Stopping all SalesShortcut services..."

# Kill by PID file if exists
if [ -f .pids ]; then
    echo "Stopping services by saved PIDs..."
    kill $(cat .pids) 2>/dev/null || true
    rm -f .pids
fi

# Kill by process name (fallback)
echo "Stopping services by process name..."
pkill -f "python -m lead_finder" 2>/dev/null || true
pkill -f "python -m lead_manager" 2>/dev/null || true
pkill -f "python -m sdr" 2>/dev/null || true
pkill -f "python -m gmail_pubsub_listener" 2>/dev/null || true
pkill -f "python -m ui_client" 2>/dev/null || true

echo "✓ All services stopped"
