import json
import logging
import os
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.auth import default
from google.oauth2 import service_account
from typing import Dict, Any

from ..config import CLOUD_PROJECT_ID, CLOUD_PROJECT_REGION, MODEL, SERVICE_ACCOUNT_FILE
from ..prompts import EMAIL_ANALYZER_PROMPT

logger = logging.getLogger(__name__)

async def is_meeting_request_llm(email_data: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
    """
    Use Vertex AI LLM to analyze email content to determine if it's a meeting request.
    """
    sender_email = email_data.get("sender_email_address", email_data.get("sender_email", "unknown"))
    try:
        # Load service account credentials or fall back to default ADC
        try:
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
        except Exception as cred_err:
            logging.warning(f"[{agent_name}] Could not load service account credentials: {cred_err}, falling back to default credentials.")
            credentials, _ = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        vertexai.init(
            project=CLOUD_PROJECT_ID,
            location=CLOUD_PROJECT_REGION,
            credentials=credentials
        )
        analysis_prompt = EMAIL_ANALYZER_PROMPT.format(email_data=email_data)

        combined_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["meeting_request", "no_meeting_request"]},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "start_datetime": {"type": "string"},
                "end_datetime": {"type": "string"},
                "attendees": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["status"],
            "additionalProperties": False
        }

        model = GenerativeModel(MODEL)
        generation_config = GenerationConfig(
            response_mime_type="application/json",
            response_schema=combined_schema,
            temperature=0.1,
            max_output_tokens=1024
        )
        response = await model.generate_content_async(
            analysis_prompt,
            generation_config=generation_config
        )
        raw_response = response.candidates[0].content.parts[0].text
        return json.loads(raw_response)

    except Exception as e:
        logger.error(f"[{agent_name}] Error in LLM meeting analysis for {sender_email}: {e}")
        simple_keywords = ["meeting", "schedule", "call", "discuss", "available", "appointment"]
        email_text = f"{email_data.get('subject_line', '')} {email_data.get('body_content', '')}".lower()
        if any(keyword in email_text for keyword in simple_keywords):
            return {"status": "meeting_request", "fallback": True, "title": f"Meeting with {sender_email}"}
        return {"status": "no_meeting_request", "fallback": True}

async def test_is_meeting_request_llm():
    """
    Test function to validate the is_meeting_request_llm functionality.
    """
    email_data = {
        "unread_emails": [
            {
                "sender_email": "meinnps@gmail.com",
                "message_id": "197907e95f4bf65f",
                "thread_id": "197907b5558cf5ea",
                "sender_name": "Merdan Durdyev",
                "subject": "Re: Follow-up with out disscussion",
                "body": "Hi Lexi,\r\n\r\nI would like to meet with your team tomorrow at 9:45 AM.\r\n\r\nHow does it sound?\r\n\r\nOn Fri, Jun 20, 2025 at 9:16 PM Sales Sales <sales@zemzen.org> wrote:\r\n\r\n> Hi Merdan\r\n>\r\n> Let's arrange a meeting with you.\r\n>\r\n> What time is more convenient for you?\r\n>\r\n> Lexi\r\n\r\nHi Lexi,I would like to meet with your team tomorrow at 9:45 AM.How does it sound?On Fri, Jun 20, 2025 at 9:16 PM Sales Sales <sales@zemzen.org> wrote:Hi MerdanLet's arrange a meeting with you.What time is more convenient for you?Lexi",
                "date_received": "2025-06-20T21:17:46-06:00",
                "thread_conversation_history": None
            }
        ]
    }
    result = await is_meeting_request_llm(email_data, "TestAgent")
    return result


def simple_test():
    # Test credentials
    credentials = service_account.Credentials.from_service_account_file(
       SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )

    vertexai.init(
        project=CLOUD_PROJECT_ID,
        location=CLOUD_PROJECT_REGION,
        credentials=credentials
    )
    
    print("Project ID:", CLOUD_PROJECT_ID)
    print("Region:", CLOUD_PROJECT_REGION)

    model = GenerativeModel("gemini-2.0-flash")
    response = model.generate_content("Hello, test message!")
    
    return response.text