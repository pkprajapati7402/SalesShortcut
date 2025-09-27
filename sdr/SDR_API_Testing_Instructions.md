# SDR Agent API Testing Instructions

This document provides curl commands to test the SDR agent APIs.

## Prerequisites

- SDR service running on `localhost:8084` (or set `SDR_SERVICE_URL` environment variable)
- Service should be started with `python -m sdr` or via Docker

## Available Test Endpoints

### 1. Health Check
Check if the service is running and view available endpoints:

```bash
curl -X GET http://localhost:8084/health
```

### 2. Test UI Callback (`test_ui_callback`)
Tests the SDR UI update functionality with mock business data:

```bash
curl -X GET http://localhost:8084/test/ui-callback
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "UI callback test completed",
  "ui_callback_success": true
}
```

### 3. Test Human Creation (`test_human_creation`)
Tests the human creation tool notification system:

```bash
# Basic test
curl -X GET http://localhost:8084/test/human-creation

# With custom prompt
curl -X GET "http://localhost:8084/test/human-creation?prompt=Create%20a%20landing%20page%20for%20testing"
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Human creation test completed",
  "test_data": {
    "request_id": "test-12345",
    "prompt": "Create a test website for communication testing"
  },
  "ui_notification_success": true
}
```

### 4. Human Input Callback (`human_input_callback`)
Submit human response for a pending request:

```bash
curl -X POST http://localhost:8084/api/human-input/test-12345 \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/completed-task",
    "response": "Task completed successfully"
  }'
```

**Expected Response (Success):**
```json
{
  "status": "success",
  "request_id": "test-12345"
}
```

**Expected Response (Error):**
```json
{
  "status": "failed",
  "message": "Invalid request ID or request not pending"
}
```

## Authentication Endpoint

For Google Calendar integration testing:

```bash
# This will redirect to Google OAuth flow
curl -X GET "http://localhost:8084/authenticate?state=test-state"
```

## Testing Workflow

1. **Start the service:**
   ```bash
   python -m sdr --host 0.0.0.0 --port 8084
   ```

2. **Verify service health:**
   ```bash
   curl -X GET http://localhost:8084/health
   ```

3. **Test UI callback:**
   ```bash
   curl -X GET http://localhost:8084/test/ui-callback
   ```

4. **Test human creation (note the request_id from response):**
   ```bash
   curl -X GET http://localhost:8084/test/human-creation
   ```

5. **Submit human response using the request_id from step 4:**
   ```bash
   curl -X POST http://localhost:8084/api/human-input/test-12345 \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/completed"}'
   ```

## Error Handling

### Common Error Responses:

- **400 Bad Request:** Invalid JSON or missing required fields
- **404 Not Found:** Invalid request ID or request not pending
- **500 Internal Server Error:** Service error or missing configuration

### Troubleshooting:

1. Check service logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure the service has proper permissions for external integrations
4. Test endpoints individually to isolate issues

## Environment Variables

Make sure these are set if using external integrations:
- `SDR_SERVICE_URL`: Public URL for the SDR service
- `GOOGLE_CLIENT_ID`: For calendar integration
- `GOOGLE_CLIENT_SECRET`: For calendar integration