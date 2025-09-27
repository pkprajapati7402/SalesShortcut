"""
Email Agent for crafting and sending outreach emails using service account.
No manual authentication required.
"""
import os

from google.adk.agents.llm_agent import LlmAgent

from sdr.sdr.config import MODEL_THINK
from ...outreach_email_prompt import EMAIL_SENDER_AGENT_PROMPT
from ...tools.gmail_service_account_tool import send_email_with_attachment_tool

email_sender_agent = LlmAgent(
    name="EmailSenderAgent",
    description="Agent that sends personalized business outreach emails with commercial offers using service account (no manual auth)",
    model=MODEL_THINK,
    instruction=EMAIL_SENDER_AGENT_PROMPT,
    tools=[send_email_with_attachment_tool],
    output_key="email_sent_result"
)