"""
MergerAgent implementation.
"""

from google.adk.agents import LlmAgent 
from ..config import MODEL
from ..prompts import MERGER_AGENT_PROMPT
from ..tools.bigquery_utils import bigquery_upload_tool

merger_agent = LlmAgent(
    model=MODEL,
    name="MergerAgent",
    description="Agent for processing and merging business data",
    instruction=MERGER_AGENT_PROMPT,
    tools=[bigquery_upload_tool],
    output_key="final_merged_leads", 
)
