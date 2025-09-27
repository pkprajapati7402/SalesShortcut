"""
Email Analyzer Agent for analyzing emails and identifying hot leads with meeting requests.
Fixed version with robust JSON parsing, updated imports, and complete Event objects.
"""
import json
import logging
import re
from typing import AsyncGenerator, Dict, Any, Optional
from typing_extensions import override

# --- FIX 1, PART A: Move imports to the top of the file ---
import google.generativeai as genai
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from ..tools.bigquery_utils import check_hot_lead
from ..config import MODEL # Assuming MODEL is in your config
from ..prompts import EMAIL_ANALYZER_PROMPT
from ..tools.meeting_request_llm import is_meeting_request_llm
from ..callbacks import send_hot_lead_to_ui

logger = logging.getLogger(__name__)

def parse_llm_json_output(raw_data: str) -> dict:
    """
    Extracts and parses a JSON object from a raw string, which might include
    markdown code fences. Includes fallbacks for common syntax errors.
    """
    if not isinstance(raw_data, str):
        if isinstance(raw_data, dict): return raw_data
        raise TypeError(f"Expected a string to parse, but got {type(raw_data)}")

    # Step 1: Extract content from markdown fences if they exist
    match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw_data)
    if match:
        json_str = match.group(1)
    else:
        json_str = raw_data

    # Step 2: First attempt to parse the string
    try:
        return json.loads(json_str.strip())
    except json.JSONDecodeError as e:
        logger.warning(f"Initial JSON parsing failed: {e}. Attempting correction...")

    # Step 3: Fallback 1 - Simple regex to remove trailing commas
    try:
        # Remove trailing commas from objects `... ,}` and arrays `... ,]`
        corrected_str = re.sub(r",\s*([}\]])", r"\1", json_str)
        logger.info("Attempting to parse again after removing trailing commas.")
        return json.loads(corrected_str.strip())
    except json.JSONDecodeError as e2:
        logger.error(f"Fallback parsing also failed: {e2}")
        # As a final resort, you could even ask another LLM to fix the JSON,
        # but for now, we will raise the error.
        raise ValueError(f"Could not parse the JSON string even after correction attempts.") from e2

class EmailAnalyzer(BaseAgent):
    """
    A custom agent that analyzes emails to identify hot leads with meeting requests.
    """
    calendar_organizer_agent: BaseAgent
    output_key: Optional[str] = None  # Add as class field
    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, name: str, calendar_organizer_agent: BaseAgent, output_key: str = None):
        sub_agents_list = [calendar_organizer_agent]
        super().__init__(
            name=name,
            calendar_organizer_agent=calendar_organizer_agent,
            sub_agents=sub_agents_list,
        )
        self.output_key = output_key  # Store the output_key

    def __maybe_save_output_to_state(self, event: Event):
        """Saves the agent output to state if needed."""
        if (
            self.output_key
            and event.is_final_response()
            and event.content
            and event.content.parts
        ):
            result = ''.join(
                [part.text if part.text else '' for part in event.content.parts]
            )
            # Save to state using the event's actions
            event.actions.state_delta[self.output_key] = result

    async def _is_meeting_request_llm(self, email_data: Dict[str, Any], ctx: InvocationContext) -> dict:
        """Delegate meeting request analysis to the shared tool."""
        return await is_meeting_request_llm(email_data, self.name)

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        logger.info(f"[{self.name}] Starting email analysis workflow.")
        unread_emails_data = ctx.session.state.get("unread_emails")

        if not unread_emails_data:
            logger.info(f"[{self.name}] No unread emails data found in session state.")
            event = Event(content=types.Content(parts=[types.Part(text="No unread emails data found.")]), author=self.name)
            self.__maybe_save_output_to_state(event)  # Save to state
            yield event
            return

        try:
            unread_emails_dict = parse_llm_json_output(unread_emails_data)
        except (ValueError, TypeError) as e:
            logger.error(f"[{self.name}] Failed to parse unread emails data: {e}")
            ctx.session.state["meeting_result"] = "parsing_failed"
            event = Event(
                content=types.Content(parts=[types.Part(text=f"Email analysis failed: {e}")]),
                author=self.name,
            )
            self.__maybe_save_output_to_state(event)  # Save to state
            yield event
            return

        emails_list = unread_emails_dict.get("unread_emails", [])
        logger.info(f"[{self.name}]✅ Found {len(emails_list)} unread emails to analyze.")
        if not emails_list:
            ctx.session.state["meeting_result"] = "no_action_needed"
            event = Event(content=types.Content(parts=[types.Part(text="No unread emails found to analyze.")]), author=self.name)
            self.__maybe_save_output_to_state(event)  # Save to state
            yield event
            return

        logger.info(f"[{self.name}] Analyzing {len(emails_list)} emails for hot leads...")
        hot_leads_found = 0
        meeting_requests_found = 0

        ctx.session.state["calendar_request"] = ''
        ctx.session.state["email_message_id"] = ''
        
        for email_data in emails_list:
            sender_email = email_data.get("sender_email_address", "") or email_data.get("sender_email", "")
            if not sender_email:
                logger.warning(f"[{self.name}] No sender email found.")
                continue

            try:
                # The logic inside this try/except is now correct
                if await check_hot_lead(sender_email):
                    hot_leads_found += 1
                    logger.info(f"[{self.name}] Hot lead identified: {sender_email}")
                    
                    # Send hot lead notification to UI
                    try:
                        send_hot_lead_to_ui(email_data)
                        logger.info(f"[{self.name}] Hot lead notification sent to UI for: {sender_email}")
                    except Exception as ui_error:
                        logger.error(f"[{self.name}] Failed to send hot lead notification to UI: {ui_error}")
                    
                    calendar_request_data = await self._is_meeting_request_llm(email_data, ctx)
                    logger.info(f"[{self.name}]✅ LLM analysis result for {sender_email}: {calendar_request_data}")
                    if calendar_request_data.get("status") == "meeting_request":
                        logger.info(f"[{self.name}] Meeting request found from hot lead: {sender_email}")

                        ctx.session.state["calendar_request"] = calendar_request_data
                        ctx.session.state["email_message_id"] = email_data.get("message_id", "")
                        ctx.session.state["email_data"] = email_data
                        
                        # Propagate events from sub-agent and save to state
                        async for event in self.calendar_organizer_agent.run_async(ctx):
                            self.__maybe_save_output_to_state(event)  # Save to state
                            yield event
                        break
                    else:
                        logger.info(f"[{self.name}] No meeting request found in email from {sender_email}.")
                    
            except Exception as e:
                # This will catch errors during check_hot_lead or _is_meeting_request_llm
                logger.error(f"[{self.name}] Error processing email for {sender_email}: {e}", exc_info=True)
                continue

        summary_message = f"Analyzed {len(emails_list)} emails. Found {hot_leads_found} hot leads and {meeting_requests_found} meeting requests. No further action needed at this time."
        ctx.session.state["meeting_result"] = "no_meeting_requests"
        
        # Create final event and save to state
        event = Event(
            content=types.Content(parts=[types.Part(text=summary_message)]),
            author=self.name,
        )
        self.__maybe_save_output_to_state(event)  # Save to state
        yield event
        logger.info(f"[{self.name}] Email analysis workflow finished.")