# 🚀 SalesShortcut Installation Guide

This comprehensive guide will walk you through setting up the SalesShortcut AI-powered SDR system, from initial setup to full deployment.

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Service Configuration](#service-configuration)
- [Deployment Options](#deployment-options)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## 💻 System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows 10+
- **Python**: 3.9 or higher
- **Memory**: 4GB RAM
- **Storage**: 2GB available space
- **Network**: Internet connection for API access

### Recommended Requirements
- **OS**: Linux (Ubuntu 20.04+) or macOS
- **Python**: 3.11
- **Memory**: 8GB RAM
- **Storage**: 5GB available space
- **CPU**: 4+ cores for optimal performance

## 🔑 Prerequisites

### 1. Google Cloud Account Setup

#### Create Google Cloud Project
```bash
# Install gcloud CLI if not already installed
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Create new project
gcloud projects create salesshortcut-$(date +%s) --name="SalesShortcut"
export PROJECT_ID=$(gcloud projects list --format="value(projectId)" --filter="name:SalesShortcut" --limit=1)
gcloud config set project $PROJECT_ID
```

#### Enable Required APIs
```bash
# Enable all required Google Cloud APIs
gcloud services enable \
  gmail.googleapis.com \
  calendar-json.googleapis.com \
  bigquery.googleapis.com \
  places-backend.googleapis.com \
  pubsub.googleapis.com \
  aiplatform.googleapis.com
```

#### Create Service Account
```bash
# Create service account for SalesShortcut
gcloud iam service-accounts create salesshortcut-sa \
  --description="SalesShortcut Service Account" \
  --display-name="SalesShortcut"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:salesshortcut-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:salesshortcut-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/pubsub.editor"

# Create and download service account key
gcloud iam service-accounts keys create salesshortcut-key.json \
  --iam-account=salesshortcut-sa@$PROJECT_ID.iam.gserviceaccount.com
```

### 2. API Keys Setup

#### Google API Key
```bash
# Create API key for Gemini and Maps
gcloud alpha services api-keys create \
  --display-name="SalesShortcut API Key" \
  --api-target=service=generativelanguage.googleapis.com \
  --api-target=service=places-backend.googleapis.com

# Get the API key (save this for environment variables)
gcloud alpha services api-keys list --format="value(name,displayName)"
```

#### ElevenLabs API Key
1. Sign up at [ElevenLabs](https://elevenlabs.io)
2. Navigate to your profile settings
3. Copy your API key
4. Create a conversational AI agent and note the agent ID
5. Set up a phone number and note the phone number ID

### 3. Domain Setup (for Gmail/Calendar)

#### Google Workspace Admin Setup
```bash
# In Google Admin Console (admin.google.com):
# 1. Go to Security > API Controls > Domain-wide Delegation
# 2. Add client ID from service account with scopes:
#    - https://www.googleapis.com/auth/gmail.readonly
#    - https://www.googleapis.com/auth/gmail.modify
#    - https://www.googleapis.com/auth/calendar
#    - https://www.googleapis.com/auth/bigquery
```

## ⚡ Quick Start

### 1. Clone and Setup
```bash
# Clone repository
git clone <repository-url>
cd SalesShortcut

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
# Copy configuration template
cp config.template .env

# Edit .env with your API keys and settings
nano .env
```

### 3. Start All Services
```bash
# Option A: Start all services with one command
./deploy_local.sh

# Option B: Start services individually
python -m ui_client --port 8000 &
python -m lead_finder --port 8081 &
python -m lead_manager --port 8082 &
python -m gmail_pubsub_listener --port 8083 &
python -m sdr --port 8084 &
```

### 4. Access Dashboard
Open your browser to `http://localhost:8000`

## 🔧 Detailed Setup

### 1. Project Setup

#### Clone Repository
```bash
git clone <repository-url>
cd SalesShortcut
```

#### Virtual Environment
```bash
# Create isolated Python environment
python -m venv venv

# Activate environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows
```

#### Dependencies Installation
```bash
# Install all service dependencies
pip install -r requirements.txt

# Or install individual service dependencies
pip install -r ui_client/requirements.txt
pip install -r lead_finder/requirements.txt
pip install -r lead_manager/requirements.txt
pip install -r sdr/requirements.txt
pip install -r gmail_pubsub_listener/requirements.txt
```

### 2. Environment Configuration

#### Main Configuration File
```bash
# Copy template
cp config.template .env

# Edit with your values
nano .env
```

Required environment variables:
```env
# Core APIs (REQUIRED)
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
GOOGLE_CLOUD_PROJECT=your_gcp_project_id

# ElevenLabs (for phone calls)
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_AGENT_ID=your_agent_id
ELEVENLABS_PHONE_NUMBER_ID=your_phone_number_id

# Email Configuration
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com
SALES_EMAIL=sales@zemzen.org

# BigQuery Configuration
DATASET_ID=lead_finder_data
TABLE_ID=business_leads

# Service Account
GOOGLE_APPLICATION_CREDENTIALS=./salesshortcut-key.json
```

#### Service-Specific Configuration

Each service can have its own `.env` file for additional configuration:

**Lead Finder** (`lead_finder/.env`):
```env
GOOGLE_MAPS_API_KEY=your_maps_api_key
DATASET_ID=lead_finder_data
TABLE_ID=business_leads
MAX_RESULTS_PER_SEARCH=100
SEARCH_RADIUS=25000
```

**Lead Manager** (`lead_manager/.env`):
```env
SALES_EMAIL=sales@zemzen.org
CALENDAR_ID=primary
BUSINESS_HOURS_START=9
BUSINESS_HOURS_END=18
MEETING_DURATION=60
```

**SDR Agent** (`sdr/.env`):
```env
ELEVENLABS_API_KEY=your_elevenlabs_api_key
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

**Gmail PubSub** (`gmail_pubsub_listener/.env`):
```env
PROJECT_ID=your_gcp_project_id
SUBSCRIPTION_NAME=gmail-notifications-pull
SALES_EMAIL=sales@zemzen.org
```

### 3. Google Cloud Setup

#### BigQuery Setup
```bash
# Create dataset for lead storage
bq mk --dataset \
  --description="SalesShortcut lead data" \
  $PROJECT_ID:lead_finder_data

# Verify dataset creation
bq ls $PROJECT_ID:lead_finder_data
```

#### Pub/Sub Setup
```bash
# Create topic for Gmail notifications
gcloud pubsub topics create gmail-notifications

# Create subscription
gcloud pubsub subscriptions create gmail-notifications-pull \
  --topic=gmail-notifications

# Configure Gmail push notifications
curl -X POST \
  'https://gmail.googleapis.com/gmail/v1/users/me/watch' \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H 'Content-Type: application/json' \
  -d "{
    \"topicName\": \"projects/$PROJECT_ID/topics/gmail-notifications\",
    \"labelIds\": [\"INBOX\"]
  }"
```

### 4. Service Account Configuration

#### Download and Place Service Account Key
```bash
# Move service account key to project directory
mv salesshortcut-key.json .
chmod 600 salesshortcut-key.json

# Or place in secrets directory
mkdir -p .secrets
mv salesshortcut-key.json .secrets/
```

#### Test Service Account Access
```bash
# Test BigQuery access
python -c "
from google.cloud import bigquery
client = bigquery.Client()
print('BigQuery access successful')
print(f'Available datasets: {[d.dataset_id for d in client.list_datasets()][:5]}')
"

# Test Gmail access
python -c "
from google.oauth2 import service_account
from googleapiclient.discovery import build
creds = service_account.Credentials.from_service_account_file('salesshortcut-key.json')
delegated_creds = creds.with_subject('sales@zemzen.org')
service = build('gmail', 'v1', credentials=delegated_creds)
profile = service.users().getProfile(userId='me').execute()
print(f'Gmail access successful for: {profile[\"emailAddress\"]}')
"
```

## 🎛️ Service Configuration

### UI Client (Port 8000)
```bash
# Start UI Client
python -m ui_client --port 8000 --host 0.0.0.0

# With custom configuration
python -m ui_client \
  --port 8000 \
  --log-level DEBUG \
  --reload
```

### Lead Finder (Port 8081)
```bash
# Start Lead Finder
python -m lead_finder --port 8081

# Test functionality
curl -X POST http://localhost:8081/find_leads \
  -H 'Content-Type: application/json' \
  -d '{"city": "San Francisco"}'
```

### Lead Manager (Port 8082)
```bash
# Start Lead Manager
python -m lead_manager --port 8082

# Test email processing
curl -X POST http://localhost:8082/process_emails
```

### Gmail PubSub Listener (Port 8083)
```bash
# Start Gmail listener
python gmail_pubsub_listener/gmail_listener_service.py

# Check connection
curl http://localhost:8083/health
```

### SDR Agent (Port 8084)
```bash
# Start SDR agent
python -m sdr --port 8084

# Test agent capabilities
curl http://localhost:8084/capabilities
```

## 🐳 Deployment Options

### Option 1: Local Development
```bash
# Start all services locally
./deploy_local.sh

# Check all services are running
curl http://localhost:8000/health
curl http://localhost:8081/health
curl http://localhost:8082/health
curl http://localhost:8084/health
```

### Option 2: Docker Deployment
```bash
# Build all Docker images
docker build -f Dockerfile.ui_client -t salesshortcut-ui-client .
docker build -f Dockerfile.lead_finder -t salesshortcut-lead-finder .
docker build -f Dockerfile.lead_manager -t salesshortcut-lead-manager .
docker build -f Dockerfile.sdr -t salesshortcut-sdr .
docker build -f gmail_pubsub_listener/Dockerfile -t salesshortcut-gmail-listener .

# Run with Docker Compose (if available)
docker-compose up -d

# Or run individual containers
docker run -d -p 8000:8000 --env-file .env salesshortcut-ui-client
docker run -d -p 8081:8081 --env-file .env salesshortcut-lead-finder
docker run -d -p 8082:8082 --env-file .env salesshortcut-lead-manager
docker run -d -p 8084:8084 --env-file .env salesshortcut-sdr
docker run -d --env-file .env salesshortcut-gmail-listener
```

### Option 3: Google Cloud Run Deployment
```bash
# Deploy all services to Cloud Run
./deploy_cloud_run.sh

# Or deploy individual services
gcloud run deploy ui-client-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

gcloud run deploy lead-finder-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Continue for other services...
```

## 🧪 Testing

### 1. Service Health Checks
```bash
# Check all services are running
for port in 8000 8081 8082 8084; do
  echo "Testing port $port:"
  curl -f http://localhost:$port/health || echo "Service on port $port not responding"
done
```

### 2. Integration Testing
```bash
# Test lead finding workflow
echo "Testing lead finding..."
curl -X POST http://localhost:8000/start_lead_finding \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'city=San Francisco'

# Test email notification
echo "Testing email processing..."
curl -X POST http://localhost:8000/agent_callback \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_type": "lead_manager",
    "business_id": "test_lead",
    "status": "converting",
    "message": "Hot lead email received",
    "timestamp": "'$(date -Iseconds)'",
    "data": {
      "sender_email": "test@example.com",
      "subject": "Meeting Request",
      "type": "hot_lead_email"
    }
  }'
```

### 3. End-to-End Testing
```bash
# Run comprehensive test script
./test_local.sh

# Manual testing checklist:
# 1. Access dashboard at http://localhost:8000
# 2. Enter a city name and start lead finding
# 3. Monitor real-time updates in the dashboard
# 4. Send test email to sales account
# 5. Verify email processing and notifications
```

## 🔧 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check Python version
python --version  # Should be 3.9+

# Check dependencies
pip list | grep -E "(fastapi|uvicorn|google|elevenlabs)"

# Check port availability
lsof -i :8000  # Replace with specific port
```

#### API Authentication Errors
```bash
# Verify API keys
echo $GOOGLE_API_KEY | cut -c1-10  # Should show first 10 chars
echo $GOOGLE_MAPS_API_KEY | cut -c1-10

# Test API access
curl "https://generativelanguage.googleapis.com/v1beta/models?key=$GOOGLE_API_KEY"
```

#### Database Connection Issues
```bash
# Test BigQuery connection
python -c "
from google.cloud import bigquery
client = bigquery.Client()
datasets = list(client.list_datasets())
print(f'Connected to BigQuery. Found {len(datasets)} datasets.')
"

# Check service account file
ls -la salesshortcut-key.json
cat salesshortcut-key.json | jq .type  # Should show "service_account"
```

#### Gmail/Calendar Access Issues
```bash
# Check domain-wide delegation
# Verify in Google Admin Console that client ID is authorized

# Test Gmail API access
python -c "
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    'salesshortcut-key.json',
    scopes=['https://www.googleapis.com/auth/gmail.readonly']
)
delegated_creds = creds.with_subject('sales@zemzen.org')
service = build('gmail', 'v1', credentials=delegated_creds)
profile = service.users().getProfile(userId='me').execute()
print(f'Gmail access working for: {profile[\"emailAddress\"]}')
"
```

### Performance Issues
```bash
# Check system resources
top -p $(pgrep -f "python -m")

# Monitor API usage
gcloud logging read "resource.type=consumed_api" --limit=10

# Check BigQuery usage
bq ls -j --max_results=10
```

### Network Issues
```bash
# Test external API connectivity
curl -I https://api.elevenlabs.io/v1/user
curl -I https://maps.googleapis.com/maps/api/place/findplacefromtext/json

# Check internal service communication
curl http://localhost:8081/health
curl http://localhost:8082/health
```

## 📚 Next Steps

After successful installation:

1. **Configure Lead Generation**:
   - Access the dashboard at `http://localhost:8000`
   - Enter target cities for lead discovery
   - Monitor the lead finding process

2. **Set Up Email Monitoring**:
   - Configure Gmail push notifications
   - Test email response processing
   - Verify meeting scheduling functionality

3. **Customize SDR Workflows**:
   - Adjust LLM prompts for your business
   - Configure outreach templates
   - Set up phone call scripts

4. **Monitor Performance**:
   - Check BigQuery for collected data
   - Review agent logs for optimization
   - Monitor API usage and costs

5. **Scale for Production**:
   - Deploy to Google Cloud Run
   - Set up monitoring and alerting
   - Configure backup and recovery

## 🆘 Getting Help

If you encounter issues during installation:

1. Check the [main README](README.md) for overview
2. Review individual service READMEs for specific configuration
3. Check the troubleshooting sections in each service documentation
4. Verify all prerequisites are properly configured
5. Open an issue on GitHub with detailed error information

---

**Ready to automate your sales development process! 🚀**