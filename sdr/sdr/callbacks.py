"""
Callbacks for the SDR Agent.
"""
import json
import asyncio
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

import httpx

import common.config as config

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.genai import types as genai_types


logger = logging.getLogger(__name__)


# --- New helper function to extract city from address ---
def extract_city_from_address(address: Optional[str]) -> Optional[str]:
    """
    Extracts the city from a standard address string.
    Assumes address format like: "Street, City, State, Zip"
    """
    if not address:
        return None
    parts = [p.strip() for p in address.split(',')]
    if len(parts) >= 2:
        return parts[1] # City is usually the second part
    return None

def send_sdr_update_to_ui(business_data: dict, email_sent_result: Optional[dict] = None) -> None:
    """
    Sends a single business update to the UI client's /agent_callback endpoint.
    This function will now ensure a 'city' field is present in the 'data' payload.
    """
    ui_client_url = os.environ.get(
        "UI_CLIENT_SERVICE_URL", config.DEFAULT_UI_CLIENT_URL
    ).rstrip("/")
    callback_endpoint = f"{ui_client_url}/agent_callback"

    # Create a copy of the business_data to modify it for UI client's validation
    data_for_ui = business_data.copy()
    
    # log data structures 
    logger.debug(f"SDR [Callback] Data for UI: {data_for_ui}")
    logger.debug(f"SDR [Callback] Email sent result: {email_sent_result}")

    # Ensure 'city' is a top-level field for UI client's AgentUpdate validation
    if 'city' not in data_for_ui and 'address' in data_for_ui:
        extracted_city = extract_city_from_address(data_for_ui['address'])
        if extracted_city:
            data_for_ui['city'] = extracted_city
        else:
            logger.warning(f"Could not extract city from address: {data_for_ui.get('address')}. Business may not be created in UI.")

    email_sent_result_for_ui = email_sent_result if email_sent_result else {}
    
    # FIX: Parse the crafted_email if it's a JSON string
    crafted_email_raw = email_sent_result_for_ui.get("crafted_email", {})
    
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
            logger.warning(f"SDR [Callback] Could not parse '{key_name}' as JSON. Using raw string value.")
            return value # Return the original string if parsing fails
    
    # Parse the crafted_email if it's a string
    crafted = safe_json_parse(crafted_email_raw, 'crafted_email')
    
    # Now safely extract email information
    email = None
    email_subject = None
    body_preview = ""
    
    if isinstance(crafted, dict):
        email = crafted.get("to")
        email_subject = crafted.get("subject")
        body_preview = crafted.get("body", "").strip()[:50]
    else:
        logger.warning(f"SDR [Callback] crafted_email could not be parsed as dict: {type(crafted)}")
    
    if email:
        data_for_ui['email'] = email

    # Build the UI update payload
    # Include the recipient email in the message so the CONTACTED card shows it
    if email:
        message_str = f"Sent outreach email to {data_for_ui.get('name')} at {email}"
    else:
        message_str = f"Sent outreach email: {data_for_ui.get('name')}"
    payload = {
        "agent_type": "sdr",
        "business_id": data_for_ui.get("id"),  # Use id from the potentially modified data_for_ui
        "status": "contacted",
        "message": message_str,
        "timestamp": datetime.now().isoformat(),
        "data": {
            "name": data_for_ui.get("name"),
            "city": data_for_ui.get("city"),
            "phone": data_for_ui.get("phone"),
            "email": data_for_ui.get("email"),
            "email_subject": email_subject,
            "body_preview": body_preview
        }
    }

    logger.info(f"Sending POST to UI endpoint: {callback_endpoint} for business: {data_for_ui.get('name')}")
    try:
        with httpx.Client() as client:
            response = client.post(callback_endpoint, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info(f"Successfully posted update for {data_for_ui.get('name')} to UI. Status: {response.status_code}")
            return True
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code} posting to UI client: {e.response.text}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Network error sending POST request to UI client at {e.request.url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error posting to UI client: {e}")
        return False



async def post_results_callback(callback_context: CallbackContext) -> Optional[genai_types.Content]:
    agent_name = callback_context.agent_name
    logger.info(f"SDR [Callback] Exiting agent: {agent_name}. Processing final result.")

    final_businesses: List[Dict[str, Any]] = []

    context_state = callback_context.state.to_dict()
    logger.info(f"SDR [Callback] Current callback_context.state: {context_state}")
    
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
            logger.warning(f"SDR [Callback] Could not parse '{key_name}' as JSON. Using raw string value.")
            return value # Return the original string if parsing fails

    
    business_data = safe_json_parse(context_state.get('business_data'), 'business_data')
    if business_data is None:
        logger.warning(f"SDR [Callback] No business data found in state for agent: {agent_name}")
        return None

    email_sent_result = safe_json_parse(context_state.get('email_sent_result'), 'email_sent_result')

    # If email_sent_result doesn't exist, try to construct it from crafted_email
    if email_sent_result is None:
        crafted_email = safe_json_parse(context_state.get('crafted_email'), 'crafted_email')
        if crafted_email:
            # Create the expected structure for UI callback
            email_sent_result = {
                'email_sent_result': {
                    'status': 'success',
                    'message': 'Email sent successfully',
                    'crafted_email': crafted_email
                }
            }
            logger.info("SDR [Callback] Constructed email_sent_result from crafted_email")
        else:
            logger.info(f"SDR [Callback] No email data found in state for agent: {agent_name}, proceeding with business data only")

    logger.info(f"SDR [Callback] Business data and email sent result parsed successfully.")

    # Send UI update with the parsed data
    ui_update_success = False
    if email_sent_result and 'email_sent_result' in email_sent_result:
        # Pass the inner dictionary, which contains 'crafted_email'
        ui_update_success = send_sdr_update_to_ui(business_data, email_sent_result['email_sent_result'])
        if ui_update_success:
            logger.info(f"SDR [Callback] UI update sent successfully for business: {business_data.get('name')}")
        else:
            logger.error(f"SDR [Callback] Failed to send UI update for business: {business_data.get('name')}")
    else:
        logger.warning("SDR [Callback] 'email_sent_result' key not found in the parsed object.")
        # Still try to send UI update with business data only
        ui_update_success = send_sdr_update_to_ui(business_data, None)
        if ui_update_success:
            logger.info(f"SDR [Callback] UI update sent successfully without email data for business: {business_data.get('name')}")
        else:
            logger.error(f"SDR [Callback] Failed to send UI update without email data for business: {business_data.get('name')}")

    try:
        # Saving artifacts
        # This part is still subject to the "Artifact service is not initialized" error
        # but it should not block UI updates now.
        await callback_context.save_artifact("final_lead_results", {
            "businesses": final_businesses,
            "send_email_result": email_sent_result
        })
        logger.info(f"SDR [Callback] Saved artifact with {len(final_businesses)} businesses for task completion.")
    except Exception as e:
        logger.error(f"SDR [Callback] Error saving final artifact: {e}")

    logger.info("SDR [Callback] UI updates sent. Callback finished.")
    return None

def validate_us_phone_number(phone_number: str) -> Dict[str, Any]:
    """
    Validate that the phone number is a valid US number for ElevenLabs.
    
    Args:
        phone_number: Phone number to validate
        
    Returns:
        Dict with validation result and normalized number
    """
    import re
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone_number)
    
    # Check for valid US number patterns
    if len(digits_only) == 10:
        # Add +1 prefix for 10-digit numbers
        normalized = f"+1{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        # Already has country code
        normalized = f"+{digits_only}"
    else:
        return {
            "valid": False,
            "error": f"Invalid US phone number format: {phone_number}. Expected 10 or 11 digits.",
            "normalized": None
        }
    
    # Basic US number validation (not toll-free, not premium)
    area_code = digits_only[-10:-7]
    if area_code.startswith('0') or area_code.startswith('1'):
        return {
            "valid": False,
            "error": f"Invalid area code: {area_code}. Area codes cannot start with 0 or 1.",
            "normalized": None
        }
    
    return {
        "valid": True,
        "error": None,
        "normalized": normalized
    }


# CORRECTED: Removed the extra 'def' keyword
async def phone_number_validation_callback(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """
    Before-tool callback to validate phone number format and modify args if needed.
    """
    
    tool_name = tool.name # Get the name of the tool being called
    
    # Only apply this callback to the phone call tool (or its test version)
    if tool_name not in ["phone_call_tool", "phone_call_tool_test"]:
        return None # Do nothing if it's not the relevant tool

    # The phone number is expected in the 'destination' argument for the phone_call_tool
    # or 'phone_number' if using an older signature or a different tool.
    destination = args.get("destination") or args.get("phone_number", "")
    
    if not destination:
        # If no destination is provided, let the tool handle the error or raise one here.
        # For a callback, returning None means proceed with original args.
        # If you want to block the tool from running, return a dict with "result".
        logger.warning("No destination phone number found in tool arguments.")
        return None # Or raise ValueError("Missing destination phone number") if you want to explicitly block

    validation_result = validate_us_phone_number(destination)
    
    if not validation_result["valid"]:
        logger.error(f"Phone number validation failed: {validation_result['error']}")
        # When returning a dictionary, the tool call is skipped and this result is used.
        return {"result": f"Phone number validation failed: {validation_result['error']}"}
    
    # If valid, update the args with the normalized version
    normalized_number = validation_result["normalized"]
    if normalized_number != destination: # Only modify if a change occurred
        logger.info(f"Phone number normalized: {destination} -> {normalized_number}")
        args["destination"] = normalized_number
        # If your tool also uses 'phone_number', you might want to update or remove it too
        if "phone_number" in args:
            args["phone_number"] = normalized_number
            
    # Return None to indicate that the tool execution should proceed with the (potentially modified) args.
    return None


async def prevent_duplicate_call_callback(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
) -> Optional[dict]:
    """
    Before-tool callback to prevent duplicate phone calls by checking if call_result already exists.
    """
    
    tool_name = tool.name
    
    # Only apply this callback to the phone call tool
    if tool_name not in ["phone_call_tool", "phone_call_tool_test"]:
        return None
    
    # Check if call_result already exists in the state
    if hasattr(tool_context, 'state') and tool_context.state:
        state_dict = tool_context.state.to_dict() if hasattr(tool_context.state, 'to_dict') else tool_context.state
        
        # Check for existing call_result
        if 'call_result' in state_dict:
            call_result = state_dict['call_result']
            
            # Check if the call was already completed successfully
            if isinstance(call_result, dict):
                call_status = call_result.get('status')
                
                # If status is 'done' or 'completed', return the existing result
                if call_status in ['done', 'completed']:
                    logger.info(f"Call already completed with status '{call_status}'. Returning cached result.")
                    return {"result": call_result}
                
                # Also check if we have a valid transcript indicating completion
                transcript = call_result.get('transcript', [])
                if transcript and len(transcript) > 0:
                    logger.info("Call already completed with transcript. Returning cached result.")
                    return {"result": call_result}
    
    # If we have session state, also check there
    if hasattr(tool_context, 'session') and tool_context.session:
        session_state = tool_context.session.state if hasattr(tool_context.session, 'state') else {}
        
        if 'call_result' in session_state:
            call_result = session_state['call_result']
            
            if isinstance(call_result, dict):
                call_status = call_result.get('status')
                
                if call_status in ['done', 'completed']:
                    logger.info(f"Call already completed in session with status '{call_status}'. Returning cached result.")
                    return {"result": call_result}
                
                transcript = call_result.get('transcript', [])
                if transcript and len(transcript) > 0:
                    logger.info("Call already completed in session with transcript. Returning cached result.")
                    return {"result": call_result}
    
    # No previous successful call found, proceed with the tool execution
    logger.info("No previous successful call found. Proceeding with phone call.")
    return None

