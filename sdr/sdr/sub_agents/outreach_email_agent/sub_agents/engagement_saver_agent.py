"""
Engagement Saver Agent for saving email engagement data to BigQuery.
"""

from google.adk.agents.llm_agent import LlmAgent
from sdr.sdr.config import MODEL
from ..outreach_email_prompt import ENGAGEMENT_SAVER_PROMPT
from sdr.sdr.tools.bigquery_utils import bigquery_email_engagement_tool


engagement_saver_agent = LlmAgent(
    name="EngagementSaverAgent",
    description="Agent that saves email engagement and outreach data to BigQuery for analytics",
    model=MODEL,
    instruction=ENGAGEMENT_SAVER_PROMPT,
    tools=[bigquery_email_engagement_tool],
    output_key="engagement_saved_result"
)