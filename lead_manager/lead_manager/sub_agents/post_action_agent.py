"""
Post Action Agent for handling post-meeting arrangement tasks.
"""

from google.adk.agents.llm_agent import LlmAgent

from ..config import MODEL_THINK
from ..prompts import POST_ACTION_PROMPT
from ..tools.check_email import mark_email_read_tool
from ..tools.bigquery_utils import save_meeting_tool

post_action_agent = LlmAgent(
    model=MODEL_THINK,
    name="PostActionAgent",
    description="Agent that handles post-meeting arrangement tasks like email marking as read and saving meeting details to BigQuery",
    instruction=POST_ACTION_PROMPT,
    tools=[mark_email_read_tool, save_meeting_tool],
    output_key="notification_result"
)