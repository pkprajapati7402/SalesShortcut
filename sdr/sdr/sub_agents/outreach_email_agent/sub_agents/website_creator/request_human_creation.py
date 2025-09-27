from google.adk.agents.llm_agent import LlmAgent
from .tools.human_creation_tool import request_human_input_tool
from sdr.sdr.config import MODEL
from ...outreach_email_prompt import REQUEST_HUMAN_CREATION_PROMPT

def _skip_human_creation_if_exists(tool, args, tool_context):
    # Skip invoking human_creation if a preview link is already present
    existing = tool_context.state.get("website_preview_link", "")
    if existing:
        return existing
    
    # Also skip if there's no website_creation_prompt to act upon
    if not tool_context.state.get("website_creation_prompt"):
        # Return a message indicating no prompt is available
        return "No website creation prompt found in state. Skipping human creation."
    
    return None


request_URL = LlmAgent(
    name="RequestHumanApproval",
    model=MODEL,
    instruction=REQUEST_HUMAN_CREATION_PROMPT,
    tools=[request_human_input_tool],
    before_tool_callback=_skip_human_creation_if_exists,
    output_key="website_preview_link"
)
