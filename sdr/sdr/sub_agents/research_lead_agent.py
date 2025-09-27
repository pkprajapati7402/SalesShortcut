"""
Research Lead Agent for gathering business insights and information.
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import google_search

from ..config import MODEL
from ..prompts import RESEARCH_LEAD_PROMPT

research_lead_agent = LlmAgent(
    model=MODEL,
    name="ResearchLeadAgent",
    description="Agent that researches business leads to gather insights and understand how a website would help",
    instruction=RESEARCH_LEAD_PROMPT,
    tools=[google_search],
    output_key="research_result"
)