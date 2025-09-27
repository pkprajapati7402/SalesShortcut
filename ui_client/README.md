# 🖥️ UI Client - SalesShortcut Dashboard

A modern, real-time web dashboard for managing AI-powered sales lead generation and qualification workflows. This application provides a centralized interface to monitor and control multiple sales agents working together to find, qualify, and schedule meetings with potential customers.

## 🚀 Features

- **Real-time Dashboard**: Live updates via WebSocket for instant visibility into sales agent activities
- **Multi-Agent Workflow**: Orchestrates Lead Finder, SDR, Lead Manager, and Calendar Assistant agents
- **City-based Lead Generation**: Target specific cities for focused lead discovery
- **Status Tracking**: Track leads through the entire sales funnel from discovery to meeting scheduling
- **Activity Logging**: Comprehensive logging of all agent activities and lead interactions
- **Responsive Design**: Modern, mobile-friendly interface with intuitive navigation
- **A2A Integration**: Seamless communication with sales agents using A2A (Agent-to-Agent) protocol

## 📋 Table of Contents

- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture

The UI Client serves as the central orchestration point for the SalesShortcut platform:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Input    │───▶│   UI Client      │───▶│  Lead Finder    │
│   (City Name)   │    │   (Dashboard)    │    │     Agent       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                         │
                         ▼
┌──────────────────┐    ┌─────────────────┐
│   WebSocket      │    │      SDR        │
│   Updates        │    │     Agent       │
└──────────────────┘    └─────────────────┘
                         │
                         ▼
┌──────────────────┐    ┌─────────────────┐
│   Real-time      │    │  Lead Manager   │
│   Dashboard      │    │     Agent       │
└──────────────────┘    └─────────────────┘
                         │
                         ▼
                       ┌─────────────────┐
                       │ Calendar Agent  │
                       │   (Meetings)    │
                       └─────────────────┘
```

### Agent Flow

1. **Lead Finder Agent**: Discovers potential businesses in target cities
2. **SDR Agent**: Engages with prospects and qualifies their interest
3. **Lead Manager Agent**: Converts qualified leads into sales opportunities
4. **Calendar Assistant**: Schedules meetings with hot prospects

### Data Models

- **Business**: Core entity representing a potential customer
- **Agent Update**: Status updates from agents about business interactions
- **WebSocket Events**: Real-time communication for dashboard updates

## 🛠️ Installation

### Prerequisites

- Python 3.9+
- Node.js 16+ (for frontend assets, if needed)
- Google API Key (for Gemini LLM inference)
- Running sales agent services

### Local Development Setup

1. **Clone the repository**:
```bash
git clone <repository-url>
cd salesshortcut
```

2. **Install Python dependencies**:
```bash
pip install -r ui_client/requirements.txt
```

3. **Set environment variables**:
```bash
export GOOGLE_API_KEY="your-google-api-key"

# Optional: Override default service URLs
export LEAD_FINDER_SERVICE_URL="http://localhost:8081"
export SDR_SERVICE_URL="http://localhost:8084"
export LEAD_MANAGER_SERVICE_URL="http://localhost:8082"
export GMAIL_LISTENER_SERVICE_URL="http://localhost:8083"
```

4. **Start the application**:
```bash
# Using the module
python -m ui_client

# Or with custom configuration
python -m ui_client --port 8000 --reload --log-level DEBUG
```

### Docker Installation

1. **Build the Docker image**:
```bash
docker build -f Dockerfile.ui_client -t salesshortcut-ui-client .
```

2. **Run the container**:
```bash
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY="your-google-api-key" \
  -e LEAD_FINDER_SERVICE_URL="http://lead-finder:8081" \
  -e SDR_SERVICE_URL="http://sdr:8084" \
  -e LEAD_MANAGER_SERVICE_URL="http://lead-manager:8082" \
  salesshortcut-ui-client
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_API_KEY` | Google API key for Gemini LLM | None | Yes |
| `LEAD_FINDER_SERVICE_URL` | Lead Finder service URL | http://localhost:8081 | No |
| `SDR_SERVICE_URL` | SDR service URL | http://localhost:8084 | No |
| `LEAD_MANAGER_SERVICE_URL` | Lead Manager service URL | http://localhost:8082 | No |
| `GMAIL_LISTENER_SERVICE_URL` | Gmail service URL | http://localhost:8083 | No |
| `UI_CLIENT_PORT` | UI Client port | 8000 | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `WEBSOCKET_TIMEOUT` | WebSocket timeout (seconds) | 300 | No |

### Service Configuration

Create a `.env` file in the `ui_client/` directory:

```env
# Core configuration
GOOGLE_API_KEY=your_google_api_key_here
LOG_LEVEL=INFO

# Service URLs (optional overrides)
LEAD_FINDER_SERVICE_URL=http://localhost:8081
SDR_SERVICE_URL=http://localhost:8084
LEAD_MANAGER_SERVICE_URL=http://localhost:8082
GMAIL_LISTENER_SERVICE_URL=http://localhost:8083

# WebSocket configuration
WEBSOCKET_TIMEOUT=300
```

## 📖 Usage

### Starting the Dashboard

1. **Start dependent services**:
```bash
# Start all agent services first
python -m lead_finder --port 8081
python -m sdr --port 8084
python -m lead_manager --port 8082
python -m gmail_pubsub_listener --port 8083
```

2. **Start the UI Client**:
```bash
python -m ui_client --port 8000
```

3. **Access the dashboard**:
   - Open your browser to `http://localhost:8000`
   - The dashboard will show real-time updates from all agents

### Dashboard Features

#### Lead Generation
- Enter a target city name to start lead discovery
- Monitor Lead Finder agent progress in real-time
- View discovered businesses with contact information

#### SDR Management
- Track SDR agent activities and outreach campaigns
- Monitor phone call outcomes and email responses
- View proposal generation and fact-checking results

#### Lead Qualification
- Monitor Lead Manager agent activities
- Track hot leads and meeting requests
- View email response analysis and engagement scoring

#### Calendar Management
- View scheduled meetings and appointments
- Monitor calendar assistant activities
- Track meeting outcomes and follow-up actions

### WebSocket Events

The dashboard receives real-time updates via WebSocket connections:

```javascript
// Example WebSocket message structure
{
  "agent_type": "lead_finder",
  "business_id": "biz-123",
  "status": "found",
  "message": "Found business: Acme Corp",
  "timestamp": "2025-06-23T12:00:00Z",
  "data": {
    "name": "Acme Corp",
    "city": "New York",
    "phone": "+1-555-1234",
    "email": "contact@acme.com"
  }
}
```

## 🔌 API Documentation

### REST Endpoints

#### Start Lead Finding
```http
POST /start_lead_finding
Content-Type: application/x-www-form-urlencoded

city=New%20York
```

#### Agent Callback
```http
POST /agent_callback
Content-Type: application/json

{
  "agent_type": "sdr",
  "business_id": "biz-123",
  "status": "contacted",
  "message": "Sent outreach email",
  "timestamp": "2025-06-23T12:00:00Z",
  "data": {...}
}
```

#### Get Business Data
```http
GET /api/businesses
```

#### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  // Handle real-time updates
};
```

### Testing with curl

#### Human Feedback Popup Testing

```bash
# 1. Send human input request (triggers popup)
curl -X POST http://localhost:8000/api/human-input \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test-123",
    "prompt": "Please review this outreach email draft",
    "type": "email_review",
    "timestamp": "2025-06-23T10:00:00Z"
  }'

# 2. Get pending human input requests
curl -X GET http://localhost:8000/api/human-input

# 3. Submit human response
curl -X POST http://localhost:8000/api/human-input/test-123 \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test-123",
    "response": "Approved with minor changes"
  }'
```

#### SDR Agent Contacted Callback Testing

```bash
# SDR agent completion callback
curl -X POST http://localhost:8000/agent_callback \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "sdr",
    "business_id": "test-business-456",
    "status": "contacted",
    "message": "Successfully sent outreach email to contact@example.com",
    "timestamp": "2025-06-23T10:30:00Z",
    "data": {
      "email_sent": true,
      "contact_email": "contact@example.com",
      "outreach_type": "cold_email"
    }
  }'
```

#### Lead Manager Callbacks Testing

```bash
# 1. Hot lead notification (requires business name for new business)
curl -X POST http://localhost:8000/agent_callback \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "lead_manager",
    "business_id": "hot-lead-789",
    "status": "converting",
    "message": "Hot lead detected - customer showing high interest",
    "timestamp": "2025-06-23T11:00:00Z",
    "data": {
      "name": "Hot Lead Corp",
      "lead_score": 95,
      "interest_level": "high",
      "contact_email": "interested@client.com"
    }
  }'

# 2. Meeting scheduled callback (requires business name for new business)
curl -X POST http://localhost:8000/agent_callback \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "lead_manager",
    "business_id": "meeting-lead-101",
    "status": "meeting_scheduled",
    "message": "Demo meeting scheduled for tomorrow at 2 PM",
    "timestamp": "2025-06-23T11:15:00Z",
    "data": {
      "name": "Meeting Demo Corp",
      "meeting_time": "2025-06-24T14:00:00Z",
      "meeting_type": "demo",
      "calendar_link": "https://calendar.example.com/meeting/123"
    }
  }'

# 3. Lead manager search callback (Note: endpoint may not be available in simple_main.py)
curl -X POST http://localhost:8082/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test lead search",
    "ui_client_url": "http://localhost:8000"
  }'
```

#### Calendar Agent Testing

```bash
# Calendar notification callback
curl -X POST http://localhost:8000/agent_callback \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "calendar",
    "business_id": "calendar-test-202",
    "status": "meeting_scheduled",
    "message": "Calendar meeting created successfully",
    "timestamp": "2025-06-23T11:30:00Z",
    "data": {
      "calendar_event_id": "cal-123",
      "attendees": ["client@example.com", "sales@yourcompany.com"]
    }
  }'
```

#### WebSocket Connection Testing

```bash
# Test WebSocket connection (use wscat if available)
wscat -c ws://localhost:8000/ws

# Or use curl to test the endpoint exists
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:8000/ws
```

#### Health Check Testing

```bash
# UI health check
curl -X GET http://localhost:8000/health

# SDR agent health check  
curl -X GET http://localhost:8084/health

# Lead manager health check
curl -X GET http://localhost:8082/health
```

#### Legacy Test Examples

```bash
# Test Lead Finder notification
curl -X POST http://localhost:8000/agent_callback \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_type": "lead_finder",
    "business_id": "biz-123",
    "status": "found",
    "message": "Found business: Test Corp",
    "timestamp": "2025-06-23T12:00:00Z",
    "data": {
      "name": "Test Corp",
      "city": "Test City",
      "phone": "+1-555-1234",
      "email": "test@testcorp.com"
    }
  }'

# Test SDR notification
curl -X POST http://localhost:8000/agent_callback \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_type": "sdr",
    "business_id": "biz-123",
    "status": "contacted",
    "message": "Sent outreach email",
    "timestamp": "2025-06-23T12:00:00Z",
    "data": {
      "email_subject": "Website Development Proposal",
      "body_preview": "We noticed your business could benefit from..."
    }
  }'
```

## 🛠️ Development

### Running in Development Mode

```bash
# Install development dependencies
pip install -r ui_client/requirements.txt

# Start with hot reload
python -m ui_client --reload --log-level DEBUG

# Or using uvicorn directly
uvicorn ui_client.main:app --reload --port 8000 --log-level debug
```

### Project Structure

```
ui_client/
├── __init__.py
├── __main__.py           # Entry point
├── main.py              # FastAPI application
├── requirements.txt     # Dependencies
├── static/             # Static assets
│   ├── css/
│   │   ├── style.css
│   │   └── dashboard.css
│   └── js/
│       └── dashboard.js
├── templates/          # Jinja2 templates
│   ├── index.html
│   ├── dashboard.html
│   ├── architecture_diagram.html
│   └── error.html
└── test/              # Tests
    └── test_ui_client.py
```

### Adding New Features

1. **Add new routes** in `main.py`:
```python
@app.get("/new-feature")
async def new_feature():
    return {"message": "New feature"}
```

2. **Add new templates** in `templates/`:
```html
<!-- templates/new_feature.html -->
<div class="feature">
  <h2>New Feature</h2>
</div>
```

3. **Add new static assets** in `static/`:
```css
/* static/css/new_feature.css */
.feature {
  background: #f0f0f0;
  padding: 20px;
}
```

### Testing

```bash
# Run tests
pytest ui_client/test/

# Run specific test
pytest ui_client/test/test_ui_client.py::test_websocket_connection

# Run with coverage
pytest --cov=ui_client ui_client/test/
```

## 🐳 Deployment

### Docker Deployment

```bash
# Build image
docker build -f Dockerfile.ui_client -t salesshortcut-ui-client .

# Run container
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY="your-api-key" \
  salesshortcut-ui-client
```

### Cloud Run Deployment

```bash
# Deploy to Google Cloud Run
gcloud run deploy ui-client-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY="your-api-key"
```

### Production Configuration

1. **Set production environment variables**:
```bash
export GOOGLE_API_KEY="your-production-api-key"
export LOG_LEVEL="WARNING"
export WEBSOCKET_TIMEOUT="600"
```

2. **Use production server**:
```bash
# Use gunicorn for production
pip install gunicorn
gunicorn ui_client.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🔍 Troubleshooting

### Common Issues

#### WebSocket Connection Failed
```bash
# Check if the service is running
curl http://localhost:8000/health

# Verify WebSocket endpoint
wscat -c ws://localhost:8000/ws
```

#### Agent Communication Errors
```bash
# Check agent service URLs
export LEAD_FINDER_SERVICE_URL="http://localhost:8081"
curl $LEAD_FINDER_SERVICE_URL/health

# Verify A2A configuration
python -c "from a2a.client import A2AClient; print('A2A available')"
```

#### Template Rendering Issues
```bash
# Check template directory
ls -la ui_client/templates/

# Verify static files
ls -la ui_client/static/
```

### Debugging

1. **Enable debug logging**:
```bash
python -m ui_client --log-level DEBUG
```

2. **Check service health**:
```bash
curl http://localhost:8000/health
```

3. **Monitor WebSocket connections**:
```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Message:', event.data);
ws.onerror = (error) => console.error('Error:', error);
```

### Performance Optimization

1. **Optimize WebSocket connections**:
```python
# Increase timeout for long-running operations
WEBSOCKET_TIMEOUT = 600
```

2. **Use connection pooling**:
```python
# Configure httpx client
client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_connections=100)
)
```

## 📊 Monitoring

### Health Checks

```bash
# Check service health
curl http://localhost:8000/health

# Monitor WebSocket connections
curl http://localhost:8000/ws/stats
```

### Logging

```python
# Configure structured logging
import structlog
logger = structlog.get_logger("ui_client")
logger.info("Dashboard started", port=8000)
```

### Metrics

```python
# Track key metrics
from prometheus_client import Counter, Histogram

request_count = Counter('ui_client_requests_total', 'Total requests')
response_time = Histogram('ui_client_response_time_seconds', 'Response time')
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🆘 Support

For issues, questions, or feature requests:

1. Check the [main README](../README.md) for general setup instructions
2. Review the troubleshooting section above
3. Check service logs for detailed error information
4. Open an issue on GitHub with detailed information about your problem

---

**Built with ❤️ for real-time sales agent orchestration**