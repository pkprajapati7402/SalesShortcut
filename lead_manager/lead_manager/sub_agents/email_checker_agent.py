"""
Email Checker Agent for checking unread emails.
"""

from google.adk.agents.llm_agent import LlmAgent

from ..config import MODEL
from ..prompts import EMAIL_CHECKER_PROMPT
from ..tools.check_email import check_email_tool

email_checker_agent = LlmAgent(
    model=MODEL,
    name="EmailCheckerAgent",
    description="Agent that checks and retrieves unread emails from the sales email account",
    instruction=EMAIL_CHECKER_PROMPT,
    tools=[check_email_tool],
    output_key="unread_emails"
)