"""
Test suite for the SalesShortcut UI Client.

This module contains comprehensive tests for the UI Client including:
- API endpoints
- WebSocket functionality
- Business state management
- A2A integration
- Error handling

Run tests with:
    pytest tests/test_ui_client.py -v
    pytest tests/test_ui_client.py::test_health_check -v
"""

import json
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

# Import the application
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui_client.main import app, app_state, manager, Business, BusinessStatus, AgentType, AgentUpdate

class TestUIClient:
    """Test class for UI Client functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture
    def reset_app_state(self):
        """Reset application state before each test."""
        app_state["is_running"] = False
        app_state["current_city"] = None
        app_state["businesses"] = {}
        app_state["agent_updates"] = []
        app_state["session_id"] = None
        manager.active_connections.clear()
        yield
        # Cleanup after test
        app_state["is_running"] = False
        app_state["current_city"] = None
        app_state["businesses"] = {}
        app_state["agent_updates"] = []
        app_state["session_id"] = None
        manager.active_connections.clear()
    
    def test_health_check(self, client, reset_app_state):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ui_client"
        assert "timestamp" in data
        assert "active_connections" in data
        assert data["is_running"] is False
        assert data["business_count"] == 0
    
    def test_root_endpoint_initial_state(self, client, reset_app_state):
        """Test root endpoint returns input form when no data."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Start Lead Generation" in response.content
        assert b"Target City" in response.content
    
    def test_root_endpoint_with_data(self, client, reset_app_state):
        """Test root endpoint returns dashboard when data exists."""
        # Add some test business data
        test_business = Business(
            name="Test Company",
            city="San Francisco",
            status=BusinessStatus.FOUND
        )
        app_state["businesses"][test_business.id] = test_business
        app_state["current_city"] = "San Francisco"
        
        response = client.get("/")
        assert response.status_code == 200
        assert b"dashboard" in response.content.lower()
        assert b"Test Company" in response.content
    
    def test_start_lead_finding_valid_input(self, client, reset_app_state):
        """Test starting lead finding with valid city input."""
        with patch("ui_client.main.run_lead_finding_process") as mock_process:
            response = client.post("/start_lead_finding", data={"city": "New York"})
            assert response.status_code == 303  # Redirect
            assert app_state["current_city"] == "New York"
            assert app_state["is_running"] is True
            assert app_state["session_id"] is not None
            mock_process.assert_called_once()
    
    def test_start_lead_finding_empty_city(self, client, reset_app_state):
        """Test starting lead finding with empty city input."""
        response = client.post("/start_lead_finding", data={"city": ""})
        assert response.status_code == 400
        assert app_state["is_running"] is False
    
    def test_start_lead_finding_already_running(self, client, reset_app_state):
        """Test starting lead finding when already running."""
        app_state["is_running"] = True
        response = client.post("/start_lead_finding", data={"city": "Boston"})
        assert response.status_code == 400
        data = response.json()
        assert "already running" in data["error"]
    
    def test_agent_callback_valid_update(self, client, reset_app_state):
        """Test agent callback with valid business update."""
        # Create a test business
        test_business = Business(
            name="Test Business",
            city="Chicago",
            status=BusinessStatus.FOUND
        )
        app_state["businesses"][test_business.id] = test_business
        
        # Send agent update
        update_data = {
            "agent_type": "sdr",
            "business_id": test_business.id,
            "status": "engaged",
            "message": "Business showed interest",
            "timestamp": datetime.now().isoformat()
        }
        
        with patch.object(manager, "send_update") as mock_send:
            response = client.post("/agent_callback", json=update_data)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            
            # Check business was updated
            updated_business = app_state["businesses"][test_business.id]
            assert updated_business.status == BusinessStatus.ENGAGED
            assert len(updated_business.notes) == 1
            
            # Check WebSocket update was sent
            mock_send.assert_called_once()
    
    def test_agent_callback_business_not_found(self, client, reset_app_state):
        """Test agent callback with non-existent business ID."""
        update_data = {
            "agent_type": "sdr",
            "business_id": "non-existent-id",
            "status": "engaged",
            "message": "Business showed interest",
            "timestamp": datetime.now().isoformat()
        }
        
        response = client.post("/agent_callback", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "not found" in data["message"]
    
    def test_api_businesses_empty(self, client, reset_app_state):
        """Test businesses API endpoint with no businesses."""
        response = client.get("/api/businesses")
        assert response.status_code == 200
        data = response.json()
        assert data["businesses"] == []
        assert data["total"] == 0
    
    def test_api_businesses_with_data(self, client, reset_app_state):
        """Test businesses API endpoint with business data."""
        test_business = Business(
            name="API Test Business",
            city="Seattle",
            status=BusinessStatus.ENGAGED
        )
        app_state["businesses"][test_business.id] = test_business
        
        response = client.get("/api/businesses")
        assert response.status_code == 200
        data = response.json()
        assert len(data["businesses"]) == 1
        assert data["total"] == 1
        assert data["businesses"][0]["name"] == "API Test Business"
    
    def test_api_status(self, client, reset_app_state):
        """Test status API endpoint."""
        app_state["current_city"] = "Portland"
        app_state["is_running"] = True
        app_state["session_id"] = "test-session-123"
        
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["current_city"] == "Portland"
        assert data["is_running"] is True
        assert data["session_id"] == "test-session-123"
        assert data["business_count"] == 0
    
    def test_reset_state(self, client, reset_app_state):
        """Test resetting application state."""
        # Set up some state
        app_state["current_city"] = "Denver"
        app_state["is_running"] = True
        test_business = Business(name="Test", city="Denver")
        app_state["businesses"][test_business.id] = test_business
        
        with patch.object(manager, "send_update") as mock_send:
            response = client.post("/reset")
            assert response.status_code == 303  # Redirect
            
            # Check state was reset
            assert app_state["current_city"] is None
            assert app_state["is_running"] is False
            assert len(app_state["businesses"]) == 0
            
            # Check WebSocket update was sent
            mock_send.assert_called_once()

class TestWebSocketManager:
    """Test WebSocket functionality."""
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        mock_ws = Mock(spec=WebSocket)
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()
        return mock_ws
    
    @pytest.mark.asyncio
    async def test_websocket_connect(self, mock_websocket):
        """Test WebSocket connection."""
        await manager.connect(mock_websocket)
        
        mock_websocket.accept.assert_called_once()
        assert mock_websocket in manager.active_connections
    
    def test_websocket_disconnect(self, mock_websocket):
        """Test WebSocket disconnection."""
        manager.active_connections.add(mock_websocket)
        manager.disconnect(mock_websocket)
        
        assert mock_websocket not in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_send_update_no_connections(self):
        """Test sending update with no active connections."""
        manager.active_connections.clear()
        
        # Should not raise an exception
        await manager.send_update({"type": "test", "data": "test"})
    
    @pytest.mark.asyncio
    async def test_send_update_with_connections(self, mock_websocket):
        """Test sending update to active connections."""
        manager.active_connections.add(mock_websocket)
        
        test_data = {"type": "test", "message": "hello"}
        await manager.send_update(test_data)
        
        mock_websocket.send_text.assert_called_once_with(json.dumps(test_data))
    
    @pytest.mark.asyncio
    async def test_send_update_connection_error(self, mock_websocket):
        """Test handling connection errors during update."""
        mock_websocket.send_text.side_effect = Exception("Connection error")
        manager.active_connections.add(mock_websocket)
        
        # Should handle the error gracefully and remove the connection
        await manager.send_update({"type": "test"})
        
        assert mock_websocket not in manager.active_connections

class TestBusinessModels:
    """Test business data models."""
    
    def test_business_creation(self):
        """Test creating a Business instance."""
        business = Business(
            name="Test Company",
            phone="123-456-7890",
            email="test@company.com",
            description="A test company",
            city="Austin"
        )
        
        assert business.name == "Test Company"
        assert business.phone == "123-456-7890"
        assert business.email == "test@company.com"
        assert business.description == "A test company"
        assert business.city == "Austin"
        assert business.status == BusinessStatus.FOUND
        assert isinstance(business.created_at, datetime)
        assert len(business.notes) == 0
    
    def test_agent_update_creation(self):
        """Test creating an AgentUpdate instance."""
        update = AgentUpdate(
            agent_type=AgentType.SDR,
            business_id="test-id",
            status=BusinessStatus.ENGAGED,
            message="Business engaged successfully"
        )
        
        assert update.agent_type == AgentType.SDR
        assert update.business_id == "test-id"
        assert update.status == BusinessStatus.ENGAGED
        assert update.message == "Business engaged successfully"
        assert isinstance(update.timestamp, datetime)

class TestA2AIntegration:
    """Test A2A integration functionality."""
    
    @pytest.mark.asyncio
    async def test_call_lead_finder_agent_success(self):
        """Test successful A2A call to Lead Finder agent."""
        with patch("ui_client.main.httpx.AsyncClient") as mock_client_class:
            # Mock the HTTP client and A2A client
            mock_http_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_http_client
            
            with patch("ui_client.main.A2AClient") as mock_a2a_client_class:
                mock_a2a_client = AsyncMock()
                mock_a2a_client_class.return_value = mock_a2a_client
                
                # Mock successful response
                mock_response = Mock()
                mock_response.root = Mock()
                mock_response.root.result = Mock()
                mock_response.root.result.id = "test-task-id"
                mock_response.root.result.status.state = "completed"
                mock_response.root.result.artifacts = []
                
                mock_a2a_client.send_message.return_value = mock_response
                
                from ui_client.main import call_lead_finder_agent
                
                result = await call_lead_finder_agent("San Francisco", "test-session")
                
                # Verify the call was made
                mock_a2a_client.send_message.assert_called_once()
                
                # Since we mocked no artifacts, it should indicate no results
                assert result["success"] is False or "error" in result

if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])