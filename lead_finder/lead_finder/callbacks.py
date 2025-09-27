# In lead_finder/callbacks.py

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
# --- End new helper function ---

def send_update_to_ui(business_data: dict):
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

    # Ensure 'city' is a top-level field for UI client's AgentUpdate validation
    if 'city' not in data_for_ui and 'address' in data_for_ui:
        extracted_city = extract_city_from_address(data_for_ui['address'])
        if extracted_city:
            data_for_ui['city'] = extracted_city
        else:
            logger.warning(f"Could not extract city from address: {data_for_ui.get('address')}. Business may not be created in UI.")
            # Optionally, you might want to return here or set a default city
            # if 'city' is strictly required for every business.

    payload = {
        "agent_type": "lead_finder",
        "business_id": data_for_ui.get("id"), # Use id from the potentially modified data_for_ui
        "status": "found",
        "message": f"Successfully discovered business: {data_for_ui.get('name')}",
        "timestamp": datetime.now().isoformat(),
        "data": data_for_ui # Send the modified data with the top-level 'city'
    }

    logger.info(f"Sending POST to UI endpoint: {callback_endpoint} for business: {data_for_ui.get('name')}")
    try:
        with httpx.Client() as client:
            response = client.post(callback_endpoint, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info(f"Successfully posted update for {data_for_ui.get('name')} to UI. Status: {response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Error sending POST request to UI client at {e.request.url}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while posting to the UI client: {e}")


async def post_results_callback(callback_context: CallbackContext) -> Optional[genai_types.Content]:
    agent_name = callback_context.agent_name
    logger.info(f"[Callback] Exiting agent: {agent_name}. Processing final result.")

    final_businesses: List[Dict[str, Any]] = []

    # Access the state directly
    context_state = callback_context.state.to_dict()
    print(f"[Callback] Current callback_context.state: {context_state}")

    # Check if 'final_merged_leads' key exists in the state
    if 'final_merged_leads' in context_state:
        merged_leads_text = context_state['final_merged_leads']
        
        # Use regex to find the JSON block in the text
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", merged_leads_text)
        if json_match:
            try:
                json_str = json_match.group(1)
                parsed_data = json.loads(json_str)
                if isinstance(parsed_data, list):
                    final_businesses = parsed_data
                    logger.info(f"[Callback] Successfully extracted {len(final_businesses)} businesses from callback_context.state.")
                else:
                    logger.warning(f"[Callback] Extracted JSON from state is not a list: {parsed_data}")
            except json.JSONDecodeError as e:
                logger.error(f"[Callback] Failed to parse JSON from callback_context.state: {e}")
        else:
            logger.warning(f"[Callback] No JSON block found in 'final_merged_leads' state data.")
    else:
        logger.warning("[Callback] 'final_merged_leads' not found in callback_context.state.")
        return None


    if not final_businesses:
        logger.warning("[Callback] No businesses found for UI update. Check MergerAgent's output_key and state propagation.")
        # For deeper debugging if needed, log the full state
        logger.warning(f"Full callback_context.state.to_dict(): {context_state}")
        return None


    for biz in final_businesses:
        if "id" not in biz:
            # Generate a stable ID based on unique business attributes
            biz_id_components = [str(biz.get("name", "")), str(biz.get("address", "")), str(biz.get("phone", ""))]
            # Filter out empty strings/None values before joining for hashing
            clean_components = [c for c in biz_id_components if c and c != 'None']
            biz["id"] = "generated_" + str(hash(tuple(clean_components))) if clean_components else str(datetime.now().timestamp())
        send_update_to_ui(biz)

    try:
        # Saving artifacts
        # This part is still subject to the "Artifact service is not initialized" error
        # but it should not block UI updates now.
        await callback_context.save_artifact("final_lead_results", {
            "businesses": final_businesses,
            "count": len(final_businesses)
        })
        logger.info(f"[Callback] Saved artifact with {len(final_businesses)} businesses for task completion.")
    except Exception as e:
        logger.error(f"[Callback] Error saving final artifact: {e}")

    logger.info("[Callback] UI updates sent. Callback finished.")
    return None
