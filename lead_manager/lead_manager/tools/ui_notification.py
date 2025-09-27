"""
UI Notification tool for Lead Manager.
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

import httpx
import common.config as config
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

async def notify_meeting_arranged(
    meeting_data: Dict[str, Any],
    lead_data: Dict[str, Any],
    email_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Notify the UI about a successfully arranged meeting.
    
    Args:
        meeting_data: Meeting creation results
        lead_data: Hot lead information
        email_data: Original email that triggered the meeting
        
    Returns:
        Dictionary containing notification result
    """
    try:
        logger.info("📤 Sending meeting arrangement notification to UI...")
        
        # Get UI client URL
        ui_client_url = os.environ.get(
            "UI_CLIENT_SERVICE_URL", config.DEFAULT_UI_CLIENT_URL
        ).rstrip("/")
        callback_endpoint = f"{ui_client_url}/agent_callback"
        
        # Prepare notification payload
        payload = {
            "agent_type": "calendar",
            "business_id": lead_data.get("id", f"lead_{lead_data.get('email', 'unknown')}"),
            "status": "meeting_scheduled",
            "message": f"Meeting arranged with {lead_data.get('name', 'Unknown')} ({lead_data.get('email', 'unknown email')})",
            "timestamp": datetime.now().isoformat(),
            "data": {
                # Lead information
                "lead_name": lead_data.get("name", "Unknown"),
                "lead_email": lead_data.get("email", ""),
                "lead_company": lead_data.get("company", ""),
                "lead_phone": lead_data.get("phone", ""),
                
                # Meeting information
                "meeting_id": meeting_data.get("meeting_id", ""),
                "meeting_title": meeting_data.get("title", ""),
                "meeting_start": meeting_data.get("start_time", ""),
                "meeting_end": meeting_data.get("end_time", ""),
                "meeting_duration": meeting_data.get("duration", 60),
                "meeting_link": meeting_data.get("meet_link", ""),
                "calendar_link": meeting_data.get("calendar_link", ""),
                
                # Original email information
                "email_subject": email_data.get("subject", ""),
                "email_date": email_data.get("date", ""),
                "email_sender": email_data.get("sender", ""),
                "email_preview": email_data.get("preview", ""),
                
                # Metadata
                "agent_action": "meeting_arranged",
                "processing_timestamp": datetime.now().isoformat()
            }
        }
        
        logger.info(f"📤 Sending notification to: {callback_endpoint}")
        logger.info(f"📋 Meeting arranged: {meeting_data.get('title', 'Unknown')} with {lead_data.get('name', 'Unknown')}")
        
        # Send notification
        async with httpx.AsyncClient() as client:
            response = await client.post(
                callback_endpoint, 
                json=payload, 
                timeout=10.0
            )
            response.raise_for_status()
            
        logger.info(f"✅ Successfully sent meeting notification to UI. Status: {response.status_code}")
        
        return {
            "success": True,
            "status_code": response.status_code,
            "endpoint": callback_endpoint,
            "meeting_id": meeting_data.get("meeting_id", ""),
            "lead_email": lead_data.get("email", ""),
            "message": "Meeting arrangement notification sent successfully to UI"
        }
        
    except httpx.RequestError as e:
        logger.error(f"❌ Network error sending notification: {e}")
        return {
            "success": False,
            "error": f"Network error: {str(e)}",
            "error_type": "network_error",
            "message": f"Failed to send notification due to network error: {str(e)}"
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ HTTP error sending notification: {e}")
        return {
            "success": False,
            "error": f"HTTP error: {e.response.status_code}",
            "error_type": "http_error",
            "message": f"Failed to send notification. HTTP status: {e.response.status_code}"
        }
    except Exception as e:
        logger.error(f"❌ Unexpected error sending notification: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "unexpected_error",
            "message": f"Unexpected error sending notification: {str(e)}"
        }

# async def notify_processing_status(
#     status: str,
#     message: str,
#     data: Optional[Dict[str, Any]] = None
# ) -> Dict[str, Any]:
#     """
#     Send a general status notification to the UI.
    
#     Args:
#         status: Status type (processing, error, completed, etc.)
#         message: Status message
#         data: Optional additional data
        
#     Returns:
#         Dictionary containing notification result
#     """
#     try:
#         logger.info(f"📤 Sending status notification: {status} - {message}")
        
#         # Get UI client URL
#         ui_client_url = os.environ.get(
#             "UI_CLIENT_SERVICE_URL", config.DEFAULT_UI_CLIENT_URL
#         ).rstrip("/")
#         callback_endpoint = f"{ui_client_url}/agent_callback"
        
#         # Prepare notification payload
#         payload = {
#             "agent_type": "lead_manager",
#             "business_id": None,
#             "status": status,
#             "message": message,
#             "timestamp": datetime.now().isoformat(),
#             "data": data or {}
#         }
        
#         # Send notification
#         async with httpx.AsyncClient() as client:
#             response = await client.post(
#                 callback_endpoint, 
#                 json=payload, 
#                 timeout=10.0
#             )
#             response.raise_for_status()
            
#         logger.info(f"✅ Status notification sent successfully")
        
#         return {
#             "success": True,
#             "status_code": response.status_code,
#             "message": "Status notification sent successfully"
#         }
        
#     except Exception as e:
#         logger.error(f"❌ Error sending status notification: {e}")
#         return {
#             "success": False,
#             "error": str(e),
#             "message": f"Error sending status notification: {str(e)}"
#         }

# # Create the tools
# notify_status_tool = FunctionTool(func=notify_processing_status)

notify_meeting_tool = FunctionTool(func=notify_meeting_arranged)
