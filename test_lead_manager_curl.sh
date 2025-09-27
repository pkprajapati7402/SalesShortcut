#!/bin/bash

# Lead Manager Agent Test Script
# This script tests the Lead Manager A2A agent using curl commands

echo "🚀 Testing Lead Manager Agent with curl"
echo "========================================="

# Configuration
A2A_SERVER_URL="http://localhost:8080"
UI_CLIENT_URL="http://localhost:8000"

# Function to make curl request
test_curl() {
    local test_name="$1"
    local payload="$2"
    
    echo "📋 Testing: $test_name"
    echo "📤 Sending request..."
    
    response=$(curl -s -X POST "${A2A_SERVER_URL}/api/tasks" \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    if [ $? -eq 0 ]; then
        echo "✅ Request sent successfully"
        echo "📨 Response:"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    else
        echo "❌ Request failed"
    fi
    
    echo ""
}

# Check if servers are running
echo "🔧 Checking if servers are running..."

# Check A2A server
if curl -s "${A2A_SERVER_URL}/health" > /dev/null 2>&1; then
    echo "✅ A2A Server is running at $A2A_SERVER_URL"
else
    echo "❌ A2A Server is not running at $A2A_SERVER_URL"
    echo "💡 Please start the A2A server first"
    exit 1
fi

# Check UI client (optional)
if curl -s "${UI_CLIENT_URL}" > /dev/null 2>&1; then
    echo "✅ UI Client is running at $UI_CLIENT_URL"
else
    echo "⚠️  UI Client is not running at $UI_CLIENT_URL"
    echo "💡 UI notifications will fail, but agent can still run"
fi

echo ""

# Test 1: Basic Lead Manager trigger
test_curl "Basic Lead Manager Trigger" '{
    "agent_type": "lead_manager",
    "data": {
        "operation": "check_lead_emails",
        "ui_client_url": "'$UI_CLIENT_URL'"
    }
}'

# Test 2: Lead Manager with specific configuration
test_curl "Lead Manager with Configuration" '{
    "agent_type": "lead_manager", 
    "data": {
        "operation": "check_lead_emails",
        "ui_client_url": "'$UI_CLIENT_URL'",
        "config": {
            "max_emails_to_process": 10,
            "default_meeting_duration": 60
        }
    }
}'

# Test 3: Test with task ID tracking
task_id=$(uuidgen 2>/dev/null || echo "test-task-$(date +%s)")
test_curl "Lead Manager with Task ID" '{
    "agent_type": "lead_manager",
    "task_id": "'$task_id'",
    "data": {
        "operation": "check_lead_emails",
        "ui_client_url": "'$UI_CLIENT_URL'"
    }
}'

echo "📊 Test Summary:"
echo "=================="
echo "✅ Sent test requests to Lead Manager Agent"
echo "📋 Check the A2A server logs for detailed processing information"
echo "🌐 Check the UI client for any notifications"
echo ""
echo "🔧 Troubleshooting:"
echo "   - If requests fail, check if A2A server is running on port 8080"
echo "   - If agent errors occur, check environment variables and credentials"
echo "   - If emails aren't processed, verify Gmail service account setup"
echo "   - If calendar fails, verify Google Calendar API access"
echo ""
echo "📚 Useful commands:"
echo "   - View A2A logs: docker logs <a2a_container_name>"
echo "   - Check agent status: curl $A2A_SERVER_URL/api/status"
echo "   - View UI logs: docker logs <ui_container_name>"