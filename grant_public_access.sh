#!/bin/bash
# Script to grant unauthenticated (public) access to all Cloud Run services
# for the SalesShortcut project.
set -e

# You can override these via env vars, or let the defaults apply
PROJECT_ID="${PROJECT_ID:-salesshortcut}"
REGION="${REGION:-us-central1}"

SERVICES=(
  "lead-finder-service"
  "lead-manager-service"
  "sdr-service"
  "gmail-listener-service"
  "ui-client-service"
)

echo "Granting public (unauthenticated) access to Cloud Run services"
echo "Project: $PROJECT_ID, Region: $REGION"

for SERVICE in "${SERVICES[@]}"; do
  echo " - $SERVICE"
  gcloud run services add-iam-policy-binding "$SERVICE" \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT_ID"
done

echo "All services are now publicly accessible."