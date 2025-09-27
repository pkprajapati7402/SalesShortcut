"""
Phone call tool for outreach activities using ElevenLabs Conversational AI.
"""
import os
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from elevenlabs import ElevenLabs

from google.adk.tools import FunctionTool, ToolContext
from ..config import ELEVENLABS_API_KEY, ELEVENLABS_AGENT_ID, ELEVENLABS_PHONE_NUMBER_ID
from ..prompts import CALLER_PROMPT

logger = logging.getLogger(__name__)


def validate_us_phone_number(phone_number: str) -> Dict[str, Any]:
    """Validate that the phone number is a valid US number for ElevenLabs."""
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



def _init_elevenlabs_client():
    """Initialize and return the ElevenLabs client and conversational AI subclient."""
    try:
        from elevenlabs import ElevenLabs
        
        api_key = ELEVENLABS_API_KEY
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables.")
            
        client = ElevenLabs(api_key=api_key)
        convai = client.conversational_ai
    
        return client, convai
    except ImportError:
        logger.error("ElevenLabs library not available. Please install: pip install elevenlabs")
        return None, None
    except Exception as e:
        logger.error(f"Failed to initialize ElevenLabs client: {e}")
        return None, None


async def _make_call(
    to_number: str,
    system_prompt: str,
    first_message: str,
    poll_interval: float = 1.0
) -> dict[str, Any]:
    """
    Place a test outbound call via ElevenLabs Conversational-AI → Twilio
    and return its transcript & metadata.
    """
    result = {
        "status": "initializing",
        "transcript": [],
        "debug_info": [],
        "error": None,
        "conversation_id": None,
    }
    def add(msg: str):
        result["debug_info"].append(msg)
        logger.info(msg)

    # --- sanity checks -----------------------------------------------------
    for var, val in [
        ("ELEVENLABS_API_KEY", ELEVENLABS_API_KEY),
        ("ELEVENLABS_AGENT_ID", ELEVENLABS_AGENT_ID),
        ("ELEVENLABS_PHONE_NUMBER_ID", ELEVENLABS_PHONE_NUMBER_ID),
    ]:
        if not val:
            err = f"{var} environment variable is not set"
            add(f"ERROR: {err}")
            result.update(status="error", error=err)
            return result

    client, convai = _init_elevenlabs_client()
    if not client or not convai:
        err = "Failed to initialise ElevenLabs client"
        add(f"ERROR: {err}")
        result.update(status="error", error=err)
        return result

    # --- 1️⃣  start the call ----------------------------------------------
    add(f"Initiating call → {to_number}")
    try:
        response = convai.twilio.outbound_call(      # ← new namespace!
            agent_id=ELEVENLABS_AGENT_ID,
            agent_phone_number_id=ELEVENLABS_PHONE_NUMBER_ID,
            to_number=to_number,
            conversation_initiation_client_data={
                "conversation_config_override": {
                    "agent": {
                        "prompt": {"prompt": system_prompt},
                        "first_message": first_message,
                    }
                }
            },
        )
    except Exception as exc:
        add(f"Error initiating call: {exc}")
        result.update(status="error", error=str(exc))
        return result

    conv_id = getattr(response, "conversation_id", None) or getattr(response, "callSid", None)
    if not conv_id:
        err = "Conversation ID missing in outbound_call response"
        add(f"ERROR: {err}")
        result.update(status="error", error=err)
        return result

    result.update(status="initiated", conversation_id=conv_id)
    add(f"Call started (conversation_id = {conv_id})")

    # --- 2️⃣  poll until finished -----------------------------------------
    terminal = {"done", "failed"}
    while True:
        time.sleep(poll_interval)
        try:
            details = convai.conversations.get(conv_id)   # ← new helper!
            status  = getattr(details, "status", "unknown")
            result["status"] = status
            add(f"Polling status: {status}")
            if status in terminal:
                break
        except Exception as exc:
            add(f"Error polling: {exc}")
            result.update(status="error_polling", error=str(exc))
            return result

    # --- 3️⃣  extract transcript ------------------------------------------
    turns = (
        getattr(details, "transcript", None)
        or getattr(details, "turns", None)
        or []
    )
    formatted = []
    for t in turns:
        role = getattr(t, "role", "unknown")
        msg  = (
            t.message if hasattr(t, "message") else
            getattr(t, "text", "unknown")
        )
        if hasattr(msg, "text"):  # ElevenLabs sometimes nests TextObject
            msg = msg.text
        formatted.append({"role": role, "message": msg})
    result["transcript"] = formatted
    return result



async def phone_call(business_data: dict[str, Any], proposal: str) -> dict[str, Any]:
    """
    Function for calling a Business to discuss website development.

    Args:
        business_data (dict[str, Any]): The business data containing phone number and other details.
        proposal (str): The proposal to present during the call.
        tool_context (ToolContext): The context containing all necessary information for the call.

    Returns:
        A dictionary containing test call results
    """
    
    logger.info("⚒️ [TOOL] 📞 Starting phone call tool...")
    

    # await asyncio.sleep(3)
    # mock_result = {
    #   "status": "done",
    #   "transcript": [
    #     {
    #       "role": "agent",
    #       "message": "Hello!.. This is Lexi from Web Solutions Inc. I hope I'm not catching you at a bad time. I'm calling to let you know about our website development services for you. Do you have just a quick moment to chat?"
    #     },
    #     {
    #       "role": "user",
    #       "message": "Yes, I would like to receive the email with proposal right away."
    #     },
    #     {
    #       "role": "agent",
    #       "message": "Great! I understand that The Sportsman has been a cornerstone of the Logan community for over seventy years, and I'd like..."
    #     },
    #     {
    #       "role": "user",
    #       "message": "Yes, just send it to MEINNPS at gmail.com."
    #     },
    #     {
    #       "role": "agent",
    #       "message": "Thank you for confirming your email address. Just to be clear, is that M. E. I. N. N. P. S. at gmail dot com? Also, do I..."
    #     },
    #     {
    #       "role": "user",
    #       "message": "Yes, sure."
    #     },
    #     {
    #       "role": "agent",
    #       "message": "Perfect! I'll send over the proposal right away. If you express interest by replying to the email, we'll create and send you a demo website MVP tailored to your business. After you review it, a..."
    #     },
    #     {
    #       "role": "user",
    #       "message": "Okay."
    #     },
    #     {
    #       "role": "agent",
    #       "message": "Great, I'm glad we could connect! I'm sending the email now, and a human from our team will contact you later. Have a great rest of your day!"
    #     }
    #   ],
    #   "debug_info": [
    #     "Initiating call → +14353173849",
    #     "Call started (conversation_id = conv_01jxv205n2f2s96ycrcx00s1cx)",
    #     "Polling status: initiated",
    #     "Polling status: initiated",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: in-progress",
    #     "Polling status: processing",
    #     "Polling status: done"
    #   ],
    #   "error": None,
    #   "conversation_id": "conv_01jxv205n2f2s96ycrcx00s1cx"
    # }
    
    # return mock_result 


    # Initialize logging to file
    root_path = Path.cwd()
    log_file = root_path / "phone_call_tool_usage.log"

    def log_to_file(message: str):
        """Write log message to file with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    # Clear previous logs and start fresh for this call
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"=== PHONE CALL TOOL USAGE LOG - {datetime.now().isoformat()} ===\n\n")
    
    log_to_file("=" * 80)
    log_to_file("🔍 PHONE CALL FUNCTION DEBUG START")
    log_to_file("=" * 80)
        
    debug_info = {}
        
    # Check environment variables
    log_to_file(f"\n🔧 Checking environment variables...")
    env_vars = {
        "ELEVENLABS_API_KEY": "✅ Set" if ELEVENLABS_API_KEY else "❌ Missing",
        "ELEVENLABS_AGENT_ID": "✅ Set" if ELEVENLABS_AGENT_ID else "❌ Missing", 
        "ELEVENLABS_PHONE_NUMBER_ID": "✅ Set" if ELEVENLABS_PHONE_NUMBER_ID else "❌ Missing"
    }
    
    for var, status in env_vars.items():
        log_to_file(f"   {var}: {status}")
    
    missing_vars = [var for var, status in env_vars.items() if "❌" in status]
    if missing_vars:
        log_to_file(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        log_to_file("Please set these environment variables before running the test.")
        return "No valid environment variables found for ElevenLabs API. Please set ELEVENLABS_API_KEY, ELEVENLABS_AGENT_ID, and ELEVENLABS_PHONE_NUMBER_ID."
    
    # Make the call
    log_to_file("⏳ This may take a few minutes depending on call duration...")
    
    
    # Extract key information with flexible key handling
    if business_data and proposal:
        debug_info["business_data"] = business_data
        debug_info["proposal"] = proposal
        
        # Handle both 'phone' and 'phone_number' keys
        business_phone = (
            business_data.get('phone') or 
            business_data.get('phone_number') or 
            'No phone available'
        )
    
        debug_info["extracted_phone"] = business_phone
        
        log_to_file(f"\n🔍 Validating phone number: {business_phone}")
        validation = validate_us_phone_number(business_phone)

        if not validation["valid"]:
            log_to_file(f"❌ Phone number validation failed: {validation['error']}")
            log_to_file("\n💡 Please edit business_phone in this script with a valid US phone number")
            return "Try another phone number or format"

        normalized_number = validation["normalized"]
        log_to_file(f"\n🚀 Initiating call to {normalized_number}...")
        log_to_file(f"✅ Phone number valid. Normalized: {normalized_number}")

        FIRST_MESSAGE = "Hi, this is Lexi from ZemZen Web Solutions—just spotted some quick wins to boost your business online. Got a minute to chat?"
        SYSTEM_PROMPT = CALLER_PROMPT.format(
            business_data= json.dumps(business_data, indent=2),
            proposal=proposal
        )


        start_time = time.time()
        result = await _make_call(
               to_number=normalized_number,
               system_prompt=SYSTEM_PROMPT,
               first_message=FIRST_MESSAGE,
               poll_interval=2.0
        )
        end_time = time.time()
        
        log_to_file(" - - - - - ")
        log_to_file(f"📞 Call completed in {end_time - start_time:.2f} seconds")
        log_to_file(f"📜 Transcript: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
    
    # Write comprehensive debug file
    debug_file = root_path / "phone_call_debug_detailed.json"
    
    try:
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(debug_info, f, indent=2, ensure_ascii=False)
        log_to_file("")
        log_to_file(f"💾 Debug info written to: {debug_file}")
    except Exception as e:
        log_to_file(f"❌ Failed to write debug file: {e}")
    
    # Create mock conversation result
    log_to_file("")
    log_to_file("🎭 CREATING MOCK CONVERSATION RESULT")
    log_to_file("-" * 50)

    
    return result

# High level tool definition for phone call
phone_call_tool = FunctionTool(func=phone_call)