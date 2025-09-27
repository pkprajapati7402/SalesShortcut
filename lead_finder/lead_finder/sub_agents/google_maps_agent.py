"""
GoogleMapsAgent implementation.
"""

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext

from ..config import MODEL
from ..prompts import GOOGLE_MAPS_AGENT_PROMPT
from ..tools.maps_search import google_maps_search_tool
     

google_maps_agent = LlmAgent(
    model=MODEL,
    name="GoogleMapsAgent",
    description="Agent specialized in finding business information using Google Maps",
    instruction=GOOGLE_MAPS_AGENT_PROMPT,
    tools=[google_maps_search_tool],
)
