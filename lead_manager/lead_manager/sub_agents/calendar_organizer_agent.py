"""
Calendar Organizer Agent for scheduling meetings with hot leads.
"""

from google.adk.agents.llm_agent import LlmAgent

from ..config import MODEL
from ..prompts import CALENDAR_ORGANIZER_PROMPT
from ..tools.calendar_utils import check_availability_tool, create_meeting_tool

calendar_organizer_agent = LlmAgent(
    model=MODEL,
    name="CalendarOrganizerAgent",
    description="Agent that schedules meetings with hot leads using Google Calendar and Meet",
    instruction=CALENDAR_ORGANIZER_PROMPT,
    tools=[check_availability_tool, create_meeting_tool],
    output_key="meeting_result"
)