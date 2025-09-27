#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
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
export PROJECT_ID="${PROJECT_ID:-${CLOUD_PROJECT_ID:-salesshortcut}}" # Uses env var $PROJECT_ID, or CLOUD_PROJECT_ID, or default
export REGION="${REGION:-${CLOUD_PROJECT_REGION:-us-central1}}"       # Uses env var $REGION, or CLOUD_PROJECT_REGION, or default
export REPOSITORY_NAME="sales-shortcut"

# Derived Artifact Registry path prefix
export AR_PREFIX="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}"

# Service Names
export LEAD_FINDER_SERVICE_NAME="lead-finder-service"
export LEAD_MANAGER_SERVICE_NAME="lead-manager-service"
export SDR_SERVICE_NAME="sdr-service"
export GMAIL_LISTENER_SERVICE_NAME="gmail-listener-service"
export UI_CLIENT_SERVICE_NAME="ui-client-service"

# Cloud Build Config file names
export LEAD_FINDER_BUILDFILE="cloudbuild-lead_finder.yaml"
export LEAD_MANAGER_BUILDFILE="cloudbuild-lead_manager.yaml"
export SDR_BUILDFILE="cloudbuild-sdr.yaml"
export GMAIL_LISTENER_BUILDFILE="cloudbuild-gmail_listener.yaml"
export UI_CLIENT_BUILDFILE="cloudbuild-ui_client.yaml"

# Image tags (used for deployment after build)
export LEAD_FINDER_IMAGE_TAG="${AR_PREFIX}/lead-finder:latest"
export LEAD_MANAGER_IMAGE_TAG="${AR_PREFIX}/lead-manager:latest"
export SDR_IMAGE_TAG="${AR_PREFIX}/sdr:latest"
export GMAIL_LISTENER_IMAGE_TAG="${AR_PREFIX}/gmail-listener:latest"
export UI_CLIENT_IMAGE_TAG="${AR_PREFIX}/ui-client:latest"
 
# Helper: parse .env files and construct comma-separated KEY=VALUE pairs for gcloud run
get_env_vars_string() {
  local service_name="$1"
  local pairs=""
  # Include root .env variables first
  # shellcheck disable=SC2154
  if [ -f .env ]; then
    while IFS='=' read -r key raw_val; do
      [[ "$key" =~ ^\s*# ]] && continue
      key=$(echo "$key" | xargs)
      [[ -z "$key" ]] && continue
      raw_val=$(echo "$raw_val" | xargs)
      # strip surrounding quotes
      if [[ "$raw_val" =~ ^\".*\"$ ]]; then
        val="${raw_val:1:-1}"
      else
        val="$raw_val"
      fi
      pairs+="${key}=${val},"
    done < <(grep -v '^\s*#' .env | grep .)
  fi
  # Service-specific .env
  local env_file=""
  case "$service_name" in
    lead-finder)    env_file="lead_finder/.env";;
    lead-manager)   env_file="lead_manager/.env";;
    sdr)            env_file="sdr/.env";;
    gmail-listener) env_file="gmail_pubsub_listener/.env";;
    ui-client)      env_file=".env";;
  esac
  if [ -n "$env_file" ] && [ -f "$env_file" ]; then
    while IFS='=' read -r key raw_val; do
      [[ "$key" =~ ^\s*# ]] && continue
      key=$(echo "$key" | xargs)
      [[ -z "$key" ]] && continue
      raw_val=$(echo "$raw_val" | xargs)
      if [[ "$raw_val" =~ ^\".*\"$ ]]; then
        val="${raw_val:1:-1}"
      else
        val="$raw_val"
      fi
      # remove duplicate
      pairs=$(echo "$pairs" | sed -E "s/${key}=[^,]*,?//g")
      pairs+="${key}=${val},"
    done < <(grep -v '^\s*#' "$env_file" | grep .)
  fi
  # trim trailing comma
  echo "${pairs%,}"
}

# Check if PROJECT_ID is set
if [ "$PROJECT_ID" == "your-gcp-project-id" ]; then
  echo "ERROR: Please set your PROJECT_ID in the script before running."
  exit 1
fi

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ]; then
  echo "ERROR: Please set GOOGLE_API_KEY environment variable for Gemini LLM inference."
  echo "Example: export GOOGLE_API_KEY='your-api-key' && ./deploy_cloud_run.sh"
  exit 1
fi

# Set Google Maps API key from local env if available
export GOOGLE_MAPS_API_KEY="${GOOGLE_MAPS_API_KEY:-}"

# --- Pre-flight Checks ---
echo "Using Project ID: $PROJECT_ID"
echo "Using Region: $REGION"
echo "Using Repository: $REPOSITORY_NAME"
echo "Artifact Registry Prefix: $AR_PREFIX"
echo "---"

# --- Setup Artifact Registry (if it doesn't exist) ---
echo "Creating Artifact Registry repository (if needed)..."
gcloud artifacts repositories create $REPOSITORY_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for sales shortcut services" \
    --project=$PROJECT_ID || echo "Repository '$REPOSITORY_NAME' likely already exists in region '$REGION'."
# Separator after setup
echo "---"
# Parse services to deploy (optional: supply names as args: lead-finder, lead-manager, sdr, gmail-listener, ui-client)
if [ $# -gt 0 ]; then
  DEPLOY_SERVICES="$@"
else
  DEPLOY_SERVICES="lead-finder lead-manager sdr gmail-listener ui-client"
fi

# --- 1. Deploy Lead Finder ---
if echo "$DEPLOY_SERVICES" | grep -qw "lead-finder"; then
  echo "Deploying Lead Finder..."

# Step 1.1: Build and Push Image using Cloud Build Config
echo "Building Lead Finder image using $LEAD_FINDER_BUILDFILE..."
gcloud builds submit . --config=$LEAD_FINDER_BUILDFILE \
    --substitutions=_REGION=$REGION,_REPO_NAME=$REPOSITORY_NAME \
    --project=$PROJECT_ID --quiet

# Step 1.2: Deploy to Cloud Run
echo "Getting latest image digest for Lead Finder..."
LEAD_FINDER_DIGEST=$(gcloud artifacts docker images list $AR_PREFIX/lead-finder --format="value(DIGEST)" --limit=1 --project=$PROJECT_ID)
echo "Using image digest: $LEAD_FINDER_DIGEST"
echo "Deploying Lead Finder service ($LEAD_FINDER_SERVICE_NAME)..."
# Prepare environment variables for Lead Finder (root and service .env)
ENV_VARS=$(get_env_vars_string "lead-finder")
gcloud run deploy $LEAD_FINDER_SERVICE_NAME \
    --image=$AR_PREFIX/lead-finder@$LEAD_FINDER_DIGEST \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="$ENV_VARS" \
    --project=$PROJECT_ID

# Step 1.3: Get Service URL
export LEAD_FINDER_SERVICE_URL=$(gcloud run services describe $LEAD_FINDER_SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --project=$PROJECT_ID)
  echo "Lead Finder URL: $LEAD_FINDER_SERVICE_URL"
  echo "---"
fi

# --- 2. Deploy Lead Manager ---
if echo "$DEPLOY_SERVICES" | grep -qw "lead-manager"; then
  echo "Deploying Lead Manager..."

# Step 2.1: Build and Push Image using Cloud Build Config
echo "Building Lead Manager image using $LEAD_MANAGER_BUILDFILE..."
gcloud builds submit . --config=$LEAD_MANAGER_BUILDFILE \
    --substitutions=_REGION=$REGION,_REPO_NAME=$REPOSITORY_NAME \
    --project=$PROJECT_ID --quiet

# Step 2.2: Deploy to Cloud Run (passing Lead Finder URL)
echo "Getting latest image digest for Lead Manager..."
LEAD_MANAGER_DIGEST=$(gcloud artifacts docker images list $AR_PREFIX/lead-manager --format="value(DIGEST)" --limit=1 --project=$PROJECT_ID)
echo "Using image digest: $LEAD_MANAGER_DIGEST"
echo "Deploying Lead Manager service ($LEAD_MANAGER_SERVICE_NAME)..."
# Prepare environment variables for Lead Manager (root, service .env, and peer URL)
ENV_VARS=$(get_env_vars_string "lead-manager")
ENV_VARS="${ENV_VARS},LEAD_FINDER_SERVICE_URL=$LEAD_FINDER_SERVICE_URL"
gcloud run deploy $LEAD_MANAGER_SERVICE_NAME \
    --image=$AR_PREFIX/lead-manager@$LEAD_MANAGER_DIGEST \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="$ENV_VARS" \
    --project=$PROJECT_ID

# Step 2.3: Get Service URL
export LEAD_MANAGER_SERVICE_URL=$(gcloud run services describe $LEAD_MANAGER_SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --project=$PROJECT_ID)
  echo "Lead Manager URL: $LEAD_MANAGER_SERVICE_URL"
  echo "---"
fi

# --- 3. Deploy SDR ---
if echo "$DEPLOY_SERVICES" | grep -qw "sdr"; then
  echo "Deploying SDR..."

  # Step 3.1: Build and Push Image using Cloud Build Config
  echo "Building SDR image using $SDR_BUILDFILE..."
  gcloud builds submit . --config=$SDR_BUILDFILE \
      --substitutions=_REGION=$REGION,_REPO_NAME=$REPOSITORY_NAME \
      --project=$PROJECT_ID --quiet

  # Step 3.2: Wait for build to complete and get image digest
  echo "Getting latest image digest for SDR..."
  
  # Wait a moment for the image to be available
  sleep 5
  
  # Try to get the digest with error handling
  SDR_DIGEST=$(gcloud artifacts docker images list $AR_PREFIX/sdr \
    --format="value(DIGEST)" \
    --limit=1 \
    --project=$PROJECT_ID 2>/dev/null)
  
  if [ -z "$SDR_DIGEST" ]; then
    echo "Warning: Could not get image digest. Using latest tag instead."
    SDR_IMAGE="$AR_PREFIX/sdr:latest"
  else
    echo "Using image digest: $SDR_DIGEST"
    SDR_IMAGE="$AR_PREFIX/sdr@$SDR_DIGEST"
  fi

  # Step 3.3: Deploy to Cloud Run
  echo "Deploying SDR service ($SDR_SERVICE_NAME)..."
  
  # Prepare environment variables for SDR (root, service .env, and peer URLs)
  ENV_VARS=$(get_env_vars_string "sdr")
  
  # Add service URLs if available
  if [ -n "$LEAD_MANAGER_SERVICE_URL" ]; then
    ENV_VARS="${ENV_VARS},LEAD_MANAGER_SERVICE_URL=$LEAD_MANAGER_SERVICE_URL"
  fi
  
  # Deploy with proper resource allocation for A2A service
  gcloud run deploy $SDR_SERVICE_NAME \
      --image=$SDR_IMAGE \
      --platform managed \
      --region $REGION \
      --allow-unauthenticated \
      --port 8080 \
      --memory 2Gi \
      --cpu 2 \
      --timeout 300 \
      --max-instances 10 \
      --min-instances 0 \
      --concurrency 80 \
      --set-env-vars="$ENV_VARS" \
      --project=$PROJECT_ID

  # Step 3.4: Get Service URL and verify deployment
  export SDR_SERVICE_URL=$(gcloud run services describe $SDR_SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)' \
    --project=$PROJECT_ID)
  
  echo "SDR URL: $SDR_SERVICE_URL"
  
  # Verify the service is healthy
  echo "Verifying SDR service health..."
  sleep 10  # Give the service time to start
  
  if curl -f "$SDR_SERVICE_URL/health" --max-time 30; then
    echo "✅ SDR service is healthy!"
  else
    echo "⚠️  SDR service health check failed. Check logs:"
    echo "gcloud run logs read $SDR_SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
  fi
  
  echo "---"
fi

# --- 4. Deploy Gmail Listener ---
if echo "$DEPLOY_SERVICES" | grep -qw "gmail-listener"; then
  echo "Deploying Gmail Listener..."

# Step 4.1: Build and Push Image using Cloud Build Config
echo "Building Gmail Listener image using $GMAIL_LISTENER_BUILDFILE..."
gcloud builds submit . --config=$GMAIL_LISTENER_BUILDFILE \
    --substitutions=_REGION=$REGION,_REPO_NAME=$REPOSITORY_NAME \
    --project=$PROJECT_ID --quiet

# Step 4.2: Deploy to Cloud Run (passing Lead Manager URL)
echo "Getting latest image digest for Gmail Listener..."
GMAIL_LISTENER_DIGEST=$(gcloud artifacts docker images list $AR_PREFIX/gmail-listener --format="value(DIGEST)" --limit=1 --project=$PROJECT_ID)
echo "Using image digest: $GMAIL_LISTENER_DIGEST"
echo "Deploying Gmail Listener service ($GMAIL_LISTENER_SERVICE_NAME)..."
# Prepare environment variables for Gmail Listener (root, service .env, and correct peer URL)
ENV_VARS=$(get_env_vars_string "gmail-listener")
ENV_VARS="${ENV_VARS},LEAD_MANAGER_URL=$LEAD_MANAGER_SERVICE_URL"
gcloud run deploy $GMAIL_LISTENER_SERVICE_NAME \
    --image=$AR_PREFIX/gmail-listener@$GMAIL_LISTENER_DIGEST \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="$ENV_VARS" \
    --project=$PROJECT_ID

# Step 4.3: Get Service URL
export GMAIL_LISTENER_SERVICE_URL=$(gcloud run services describe $GMAIL_LISTENER_SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --project=$PROJECT_ID)
  echo "Gmail Listener URL: $GMAIL_LISTENER_SERVICE_URL"
  echo "---"
fi

# --- 5. Deploy UI Client ---
if echo "$DEPLOY_SERVICES" | grep -qw "ui-client"; then
  echo "Deploying UI Client..."

# Step 5.1: Build and Push Image using Cloud Build Config
echo "Building UI Client image using $UI_CLIENT_BUILDFILE..."
gcloud builds submit . --config=$UI_CLIENT_BUILDFILE \
    --substitutions=_REGION=$REGION,_REPO_NAME=$REPOSITORY_NAME \
    --project=$PROJECT_ID --quiet

# Step 5.2: Deploy to Cloud Run (passing all service URLs)
echo "Getting latest image digest for UI Client..."
UI_CLIENT_DIGEST=$(gcloud artifacts docker images list $AR_PREFIX/ui_client --format="value(DIGEST)" --limit=1 --project=$PROJECT_ID)
echo "Using image digest: $UI_CLIENT_DIGEST"
echo "Deploying UI Client service ($UI_CLIENT_SERVICE_NAME)..."
# Prepare environment variables for UI Client (root, service .env, and peer URLs)
ENV_VARS=$(get_env_vars_string "ui-client")
ENV_VARS="${ENV_VARS},LEAD_FINDER_SERVICE_URL=$LEAD_FINDER_SERVICE_URL,LEAD_MANAGER_SERVICE_URL=$LEAD_MANAGER_SERVICE_URL,SDR_SERVICE_URL=$SDR_SERVICE_URL,GMAIL_LISTENER_SERVICE_URL=$GMAIL_LISTENER_SERVICE_URL"
gcloud run deploy $UI_CLIENT_SERVICE_NAME \
    --image=$AR_PREFIX/ui_client@$UI_CLIENT_DIGEST \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="$ENV_VARS" \
    --project=$PROJECT_ID

# Step 5.3: Get Service URL
export UI_CLIENT_SERVICE_URL=$(gcloud run services describe $UI_CLIENT_SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --project=$PROJECT_ID)
  echo "UI Client URL: $UI_CLIENT_SERVICE_URL"
  echo "---"
fi

# --- Update services with UI Client URL ---
echo "Updating Lead Finder service with UI_CLIENT_SERVICE_URL..."
gcloud run services update $LEAD_FINDER_SERVICE_NAME \
    --update-env-vars "UI_CLIENT_SERVICE_URL=$UI_CLIENT_SERVICE_URL" \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID
echo "Updating Lead Manager service with UI_CLIENT_SERVICE_URL..."
gcloud run services update $LEAD_MANAGER_SERVICE_NAME \
    --update-env-vars "UI_CLIENT_SERVICE_URL=$UI_CLIENT_SERVICE_URL" \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID
echo "Updating SDR service with UI_CLIENT_SERVICE_URL..."
gcloud run services update $SDR_SERVICE_NAME \
    --update-env-vars "UI_CLIENT_SERVICE_URL=$UI_CLIENT_SERVICE_URL" \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID
echo "Updating Gmail Listener service with UI_CLIENT_SERVICE_URL..."
gcloud run services update $GMAIL_LISTENER_SERVICE_NAME \
    --update-env-vars "UI_CLIENT_SERVICE_URL=$UI_CLIENT_SERVICE_URL" \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID

# Grant public access to deployed services
echo "Granting public (unauthenticated) access to deployed services..."
for S in $DEPLOY_SERVICES; do
  case "$S" in
    lead-finder) NAME=$LEAD_FINDER_SERVICE_NAME;;
    lead-manager) NAME=$LEAD_MANAGER_SERVICE_NAME;;
    sdr) NAME=$SDR_SERVICE_NAME;;
    gmail-listener) NAME=$GMAIL_LISTENER_SERVICE_NAME;;
    ui-client) NAME=$UI_CLIENT_SERVICE_NAME;;
    *) continue;;
  esac
  echo " - $NAME"
  gcloud run services add-iam-policy-binding "$NAME" \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT_ID" || echo "Warning: failed to bind $NAME"
done

echo "Deployment Complete!"
echo "Access the UI Client at: $UI_CLIENT_SERVICE_URL"
echo "Remember to consider security (--allow-unauthenticated) for production environments."