"""
Callbacks for the Lead Manager Agent.
"""
import json
import logging
import os
import re
from typing import Optional, Dict, Any
from datetime import datetime

import httpx
import common.config as config

from google.adk.agents.callback_context import CallbackContext
from google.genai import types as genai_types

logger = logging.getLogger(__name__)


def send_calendar_notification_to_ui(calendar_request: Dict[str, Any]) -> None:
    """
    Sends a calendar notification to the UI client's /agent_callback endpoint.
    Shows unread calendar requests in the lead-manager-content section.
    """
    ui_client_url = os.environ.get(
        "UI_CLIENT_SERVICE_URL", config.DEFAULT_UI_CLIENT_URL
    ).rstrip("/")
    callback_endpoint = f"{ui_client_url}/agent_callback"
    
    payload = {
        "agent_type": "calendar",
        "business_id": calendar_request.get("business_id", "unknown_business"),
        "status": "meeting_scheduled",
        "message": f"Incoming meeting with {calendar_request.get('sender_email', 'unknown')}",
        "timestamp": datetime.now().isoformat(),
        "data": calendar_request
    }
    
    logger.info(f"Sending calendar notification to UI endpoint: {callback_endpoint}")
    try:
        with httpx.Client() as client:
            response = client.post(callback_endpoint, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info(f"Successfully posted calendar notification to UI. Status: {response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Error sending POST request to UI client at {e.request.url if hasattr(e, 'request') else 'unknown'}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while posting calendar notification to UI client: {e}")

def send_hot_lead_to_ui(email_data: Dict[str, Any]):
    """
    Sends a hot lead email notification to the UI client's /agent_callback endpoint.
    Shows unread hot lead emails in the lead-manager-content section.
    """
    ui_client_url = os.environ.get(
        "UI_CLIENT_SERVICE_URL", config.DEFAULT_UI_CLIENT_URL
    ).rstrip("/")
    callback_endpoint = f"{ui_client_url}/agent_callback"
    
    # Extract email info
    sender_email = email_data.get("sender_email_address", "") or email_data.get("sender_email", "")
    subject = email_data.get("subject", "No Subject")
    body = email_data.get("body", "")
    
    # Get first few words from body for preview
    body_preview = " ".join(body.split()[:15]) + "..." if len(body.split()) > 15 else body
    
    payload = {
        "agent_type": "lead_manager",
        "business_id": f"hot_lead_{hash(sender_email)}",
        "status": "converting",
        "message": f"Hot lead email from {sender_email}",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "sender_email": sender_email,
            "sender_name": email_data.get("sender_name", sender_email.split('@')[0]),
            "subject": subject,
            "body_preview": body_preview,
            "received_date": email_data.get("date", datetime.now().isoformat()),
            "message_id": email_data.get("message_id", ""),
            "type": "hot_lead_email"
        }
    }

    logger.info(f"Sending hot lead notification to UI endpoint: {callback_endpoint} for email: {sender_email}")
    try:
        with httpx.Client() as client:
            response = client.post(callback_endpoint, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info(f"Successfully posted hot lead notification to UI. Status: {response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Error sending POST request to UI client at {e.request.url if hasattr(e, 'request') else 'unknown'}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while posting hot lead to UI client: {e}")

async def post_lead_manager_callback(callback_context: CallbackContext) -> Optional[genai_types.Content]:
    """
    Callback function for Lead Manager Agent completion.
    This version includes robust parsing for all potential JSON strings from the context.
    """
    agent_name = callback_context.agent_name
    logger.info(f"[Callback] Exiting agent: {agent_name}. Processing final result.")

    context_state = callback_context.state.to_dict()
    logger.info(f"[Callback] Current callback_context.state: {context_state}")
    
    # Helper function to safely parse a string that might be markdown-wrapped JSON
    def safe_json_parse(value: any, key_name: str) -> any:
        if not isinstance(value, str):
            return value # It's already an object, return as-is

        cleaned_str = value.strip()
        match = re.search(r"```json\s*([\s\S]*?)\s*```", cleaned_str)
        if match:
            cleaned_str = match.group(1)
        
        try:
            return json.loads(cleaned_str)
        except json.JSONDecodeError:
            logger.warning(f"[Callback] Could not parse '{key_name}' as JSON. Using raw string value.")
            return value # Return the original string if parsing fails

    notification_data = safe_json_parse(context_state.get('calendar_request'), 'notification_result')
    
    if notification_data is None and 'notification_result' in context_state:
        logger.warning(f"[Callback] No notification data found in state for agent: {agent_name}")
        return None

    send_calendar_notification_to_ui(notification_data)
    
    try:
        # Saving artifacts
        # This part is still subject to the "Artifact service is not initialized" error
        # but it should not block UI updates now.
        await callback_context.save_artifact("final_notification_results", {
            "notification_data": notification_data,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"[Callback] Saved artifact with notification data for task completion.")
    except Exception as e:
        logger.error(f"[Callback] Error saving final artifact: {e}")

    logger.info("[Callback] UI updates sent. Callback finished.")
    return None
