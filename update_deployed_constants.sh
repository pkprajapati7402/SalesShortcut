#!/bin/bash

# Update already deployed Cloud Run services with environment variables
# This script is for manual updates to existing deployed services

# Exit immediately if a command exits with a non-zero status.
set -e

# Load root .env (global environment variables) if present
if [ -f .env ]; then
  echo "Sourcing root .env for environment variables..."
  # shellcheck source=/dev/null
  set -o allexport
  source .env
  set +o allexport
fi

# --- Configuration ---
export PROJECT_ID="${PROJECT_ID:-${CLOUD_PROJECT_ID:-salesshortcut}}"
export REGION="${REGION:-${CLOUD_PROJECT_REGION:-us-central1}}"

# Service Names
export LEAD_FINDER_SERVICE_NAME="lead-finder-service"
export LEAD_MANAGER_SERVICE_NAME="lead-manager-service"
export SDR_SERVICE_NAME="sdr-service"
export GMAIL_LISTENER_SERVICE_NAME="gmail-listener-service"
export UI_CLIENT_SERVICE_NAME="ui-client-service"

# Get deployed service URLs
echo "Getting deployed service URLs..."
export UI_CLIENT_SERVICE_URL=$(gcloud run services describe $UI_CLIENT_SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --project=$PROJECT_ID 2>/dev/null || echo "")
export LEAD_FINDER_SERVICE_URL=$(gcloud run services describe $LEAD_FINDER_SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --project=$PROJECT_ID 2>/dev/null || echo "")

if [ -z "$UI_CLIENT_SERVICE_URL" ]; then
  echo "ERROR: UI Client service not found or not deployed."
  exit 1
fi

if [ -z "$LEAD_FINDER_SERVICE_URL" ]; then
  echo "ERROR: Lead Finder service not found or not deployed."
  exit 1
fi

echo "UI Client URL: $UI_CLIENT_SERVICE_URL"
echo "Lead Finder URL: $LEAD_FINDER_SERVICE_URL"
echo "---"

# Update services with UI Client URL
echo "Updating deployed services with UI_CLIENT_SERVICE_URL..."

echo "Updating Lead Finder service..."
gcloud run services update $LEAD_FINDER_SERVICE_NAME \
    --update-env-vars "UI_CLIENT_SERVICE_URL=$UI_CLIENT_SERVICE_URL" \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID

echo "Updating Lead Manager service..."
gcloud run services update $LEAD_MANAGER_SERVICE_NAME \
    --update-env-vars "UI_CLIENT_SERVICE_URL=$UI_CLIENT_SERVICE_URL" \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID

echo "Updating SDR service..."
gcloud run services update $SDR_SERVICE_NAME \
    --update-env-vars "UI_CLIENT_SERVICE_URL=$UI_CLIENT_SERVICE_URL" \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID

echo "Updating Gmail Listener service..."
if gcloud run services describe $GMAIL_LISTENER_SERVICE_NAME --platform managed --region $REGION --project $PROJECT_ID >/dev/null 2>&1; then
    gcloud run services update $GMAIL_LISTENER_SERVICE_NAME \
        --update-env-vars "UI_CLIENT_SERVICE_URL=$UI_CLIENT_SERVICE_URL" \
        --platform managed \
        --region $REGION \
        --project $PROJECT_ID
else
    echo "  -> Gmail Listener service not found, skipping..."
fi

# Update UI Client with Lead Finder URL
echo "Updating UI Client service with LEAD_FINDER_SERVICE_URL..."
gcloud run services update $UI_CLIENT_SERVICE_NAME \
    --update-env-vars "LEAD_FINDER_SERVICE_URL=$LEAD_FINDER_SERVICE_URL" \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID

echo "---"
echo "Environment variable updates complete!"
echo "Services have been updated with the following URLs:"
echo "- UI_CLIENT_SERVICE_URL: $UI_CLIENT_SERVICE_URL"
echo "- LEAD_FINDER_SERVICE_URL: $LEAD_FINDER_SERVICE_URL"