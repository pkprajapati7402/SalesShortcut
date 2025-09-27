"This module provides a tool for human creation of websites based on a given prompt."

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

import httpx
from google.adk.tools import FunctionTool, ToolContext

from common.config import DEFAULT_UI_CLIENT_URL

logger = logging.getLogger(__name__)

class RequestStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class HumanRequest:
    request_id: str
    prompt: str
    status: RequestStatus = RequestStatus.PENDING
    url_response: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class HumanInteractionManager:
    _instance = None
    _pending_requests: Dict[str, HumanRequest] = {}
    _active_sessions: set = set()  # Track active sessions to prevent duplicates
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HumanInteractionManager, cls).__new__(cls)
        return cls._instance
    
    def create_request(self, prompt: str) -> str:
        request_id = str(uuid.uuid4())[:8]
        request = HumanRequest(request_id=request_id, prompt=prompt)
        self._pending_requests[request_id] = request
        return request_id
    
    def get_request(self, request_id: str) -> Optional[HumanRequest]:
        return self._pending_requests.get(request_id)
    
    def update_request(self, request_id: str, url: str):
        if request_id in self._pending_requests:
            self._pending_requests[request_id].status = RequestStatus.COMPLETED
            self._pending_requests[request_id].url_response = url
    
    def cancel_request(self, request_id: str):
        if request_id in self._pending_requests:
            self._pending_requests[request_id].status = RequestStatus.CANCELLED
    
    def cleanup_request(self, request_id: str):
        if request_id in self._pending_requests:
            del self._pending_requests[request_id]
    
    def is_session_active(self, session_id: str) -> bool:
        return session_id in self._active_sessions
    
    def mark_session_active(self, session_id: str):
        self._active_sessions.add(session_id)
    
    def mark_session_inactive(self, session_id: str):
        self._active_sessions.discard(session_id)

async def send_ui_notification(request_id: str, prompt: str, ui_endpoint: Optional[str] = None, max_retries: int = 3) -> bool:
    """Send notification to UI via REST API with retry logic"""
    if ui_endpoint is None:
        ui_endpoint = DEFAULT_UI_CLIENT_URL
        
    for attempt in range(max_retries):
        try:
            payload = {
                "request_id": request_id,
                "prompt": prompt,
                "type": "website_creation",
                "timestamp": datetime.now().isoformat()
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{ui_endpoint}/api/human-input",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                logger.info(f"Successfully sent UI notification for request {request_id} to {ui_endpoint}")
                return True
                
        except httpx.ConnectError:
            logger.warning(f"UI service connection failed (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        except httpx.TimeoutException:
            logger.warning(f"UI service timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Failed to send UI notification to {ui_endpoint}: {e}")
            break
            
    logger.error(f"Failed to send UI notification after {max_retries} attempts")
    return False

async def wait_for_human_response(request_id: str, timeout: int = 300) -> Optional[str]:
    """Wait for human response with timeout (5 minutes default)"""
    manager = HumanInteractionManager()
    
    start_time = asyncio.get_event_loop().time()
    
    while True:
        request = manager.get_request(request_id)
        
        if request is None:
            logger.error(f"Request {request_id} not found")
            return None
            
        if request.status == RequestStatus.COMPLETED:
            logger.info(f"Request {request_id} completed with URL: {request.url_response}")
            # Don't cleanup here - let the main function handle it to avoid race condition
            return request.url_response
            
        if request.status == RequestStatus.CANCELLED:
            logger.info(f"Request {request_id} was cancelled")
            return None
            
        current_time = asyncio.get_event_loop().time()
        if current_time - start_time > timeout:
            logger.warning(f"Request {request_id} timed out after {timeout} seconds")
            manager.cancel_request(request_id)
            return None
        
        await asyncio.sleep(1)

async def human_creation(website_creation_prompt: str, tool_context: ToolContext = None) -> str:
    """
    Sends a prompt to a human for creating a website.
    
    This function implements the human-in-the-loop pattern:
    1. Pauses execution
    2. Sends prompt to UI via REST API
    3. Waits for human to provide URL
    4. Resumes execution with the URL
    
    Args:
        website_creation_prompt (str): The prompt for creating the website.
        tool_context (ToolContext): Tool execution context.
        
    Returns:
        str: URL for the created website or error message.
    """
    
    logger.info("🔧 [TOOL] Human Creation Tool - Starting website creation process")
    # If we've already received a website preview link in state, skip re-requesting
    try:
        existing_url = tool_context.state.get("website_preview_link", "") if tool_context else ""
    except Exception:
        existing_url = None
    if existing_url:
        logger.info(f"Skipping human creation: existing website_preview_link found: {existing_url}")
        return existing_url
    
    manager = HumanInteractionManager()
    
    # Create a unique session ID based on the tool context or prompt hash
    session_id = f"website_creation_{hash(website_creation_prompt) % 1000000}"
    
    # Check if this session is already active to prevent duplicate requests
    if manager.is_session_active(session_id):
        logger.info(f"Session {session_id} already active, skipping duplicate human creation request")
        # Wait a bit and check for existing results
        await asyncio.sleep(2)
        updated_url = tool_context.state.get("website_preview_link", "") if tool_context else ""
        if updated_url:
            return updated_url
        return "Duplicate request detected. Please wait for the existing request to complete."
    
    # Mark session as active
    manager.mark_session_active(session_id)
    
    logger.info("🤖 AGENT: Requesting human website creation")
    logger.info(f"📋 Prompt: {website_creation_prompt[:100]}...")
    logger.debug(f"Full prompt: {website_creation_prompt}")
    logger.info(f"Session ID: {session_id}")
    
    # Create the request
    request_id = manager.create_request(website_creation_prompt)
    
    logger.info(f"⏸️  WORKFLOW PAUSED - Waiting for human input (Request ID: {request_id})")
    logger.info("=" * 50)
    
    try:
        # Send notification to UI
        ui_sent = await send_ui_notification(request_id, website_creation_prompt)
        
        if not ui_sent:
            logger.warning("UI service unavailable, falling back to console-based interaction")
            logger.info("👤 HUMAN INPUT REQUIRED:")
            logger.info(f"Request ID: {request_id}")
            logger.info(f"Task: Create a website based on the following prompt:")
            logger.info(f"Prompt: {website_creation_prompt}")
            logger.info("Please create the website and provide the URL when ready.")
            logger.info("You can submit the response using the API or wait for timeout.")
        
        # Wait for human response
        logger.info("⏳ Waiting for human to create website and provide URL...")
        url_response = await wait_for_human_response(request_id, timeout=600)
        
        if url_response:
            logger.info(f"✅ WEBSITE CREATED: {url_response}")
            logger.info("▶️  WORKFLOW RESUMED - Human response received")
            logger.info("=" * 50)
            
            # Add a small delay before cleanup to allow UI to complete its callback
            await asyncio.sleep(2)
            manager.cleanup_request(request_id)
            manager.mark_session_inactive(session_id)
            
            # Clear the website_creation_prompt from state to prevent re-execution
            if tool_context and hasattr(tool_context, 'state') and 'website_creation_prompt' in tool_context.state:
                try:
                    # Try to set to None instead of deleting
                    tool_context.state['website_creation_prompt'] = None
                    logger.info("Cleared website_creation_prompt from state to prevent looping")
                except Exception as e:
                    logger.warning(f"Could not clear website_creation_prompt from state: {e}")
            
            return url_response
        else:
            logger.error("❌ NO RESPONSE: Request timed out or was cancelled")
            logger.info("▶️  WORKFLOW RESUMED - No response received")
            logger.info("=" * 50)
            
            # Cleanup
            manager.cleanup_request(request_id)
            manager.mark_session_inactive(session_id)
            
            # Clear the website_creation_prompt from state to prevent re-execution
            if tool_context and hasattr(tool_context, 'state') and 'website_creation_prompt' in tool_context.state:
                try:
                    # Try to set to None instead of deleting
                    tool_context.state['website_creation_prompt'] = None
                    logger.info("Cleared website_creation_prompt from state after timeout to prevent looping")
                except Exception as e:
                    logger.warning(f"Could not clear website_creation_prompt from state: {e}")
            
            return f"Human input timeout. Request ID: {request_id}. You can still submit a response via API."
            
    except Exception as e:
        logger.error(f"Error during human interaction: {e}")
        manager.cleanup_request(request_id)
        manager.mark_session_inactive(session_id)
        
        # Clear the website_creation_prompt from state to prevent re-execution
        if tool_context and hasattr(tool_context, 'state') and 'website_creation_prompt' in tool_context.state:
            try:
                # Try to set to None instead of deleting
                tool_context.state['website_creation_prompt'] = None
                logger.info("Cleared website_creation_prompt from state after error to prevent looping")
            except Exception as e:
                logger.warning(f"Could not clear website_creation_prompt from state: {e}")
        
        return f"Error: {str(e)}"

# API endpoint functions for external access
def get_pending_requests() -> Dict[str, Dict[str, Any]]:
    """Get all pending requests for UI display"""
    manager = HumanInteractionManager()
    return {
        request_id: {
            "prompt": request.prompt,
            "status": request.status.value,
            "created_at": request.created_at.isoformat(),
            "url_response": request.url_response
        }
        for request_id, request in manager._pending_requests.items()
        if request.status == RequestStatus.PENDING
    }

def submit_human_response(request_id: str, url: str) -> bool:
    """Submit human response for a specific request"""
    manager = HumanInteractionManager()
    request = manager.get_request(request_id)
    
    if request and request.status == RequestStatus.PENDING:
        manager.update_request(request_id, url)
        logger.info(f"Human response submitted for request {request_id}: {url}")
        return True
    
    logger.warning(f"Invalid request ID or request not pending: {request_id}")
    return False

def cancel_human_request(request_id: str) -> bool:
    """Cancel a pending human request"""
    manager = HumanInteractionManager()
    request = manager.get_request(request_id)
    
    if request and request.status == RequestStatus.PENDING:
        manager.cancel_request(request_id)
        logger.info(f"Human request cancelled: {request_id}")
        return True
    
    logger.warning(f"Invalid request ID or request not pending: {request_id}")
    return False

request_human_input_tool = FunctionTool(func=human_creation)