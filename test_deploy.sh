#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
  source .env
fi

# Configuration
PROJECT_ID="${PROJECT_ID:-salesshortcut}"
REGION="${REGION:-us-central1}"
REPOSITORY_NAME="sales-shortcut"
SERVICE_NAME="test-service"

echo "Deploying test service..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Build the image
echo "Building test service image..."
gcloud builds submit . --config=cloudbuild-test.yaml \
  --substitutions=_REGION=${REGION},_REPO_NAME=${REPOSITORY_NAME} \
  --project=${PROJECT_ID} --quiet

# Get the image digest
echo "Getting latest image digest..."
sleep 5
IMAGE_DIGEST=$(gcloud artifacts docker images list ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/test-service \
  --format="value(DIGEST)" \
  --limit=1 \
  --project=${PROJECT_ID} 2>/dev/null)

if [ -z "$IMAGE_DIGEST" ]; then
  echo "Using latest tag"
  IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/test-service:latest"
else
  echo "Using digest: $IMAGE_DIGEST"
  IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/test-service@$IMAGE_DIGEST"
fi

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --project=$PROJECT_ID

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)' \
  --project=$PROJECT_ID)

echo "Test service deployed!"
echo "URL: $SERVICE_URL"

# Test the service
echo "Testing the service..."
sleep 5
if curl -f "$SERVICE_URL/health" --max-time 30; then
  echo "✅ Test service is working!"
else
  echo "❌ Test service failed"
fi