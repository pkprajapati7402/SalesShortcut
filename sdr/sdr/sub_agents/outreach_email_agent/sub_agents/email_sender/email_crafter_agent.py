# an LlmAgent
from google.adk.agents.llm_agent import LlmAgent
from sdr.sdr.config import MODEL
from ...outreach_email_prompt import EMAIL_CRAFTER_PROMPT


email_crafter_agent = LlmAgent(
    name="EmailCrafterAgent",
    description="Agent that crafts personalized outreach emails based on provided data.",
    model=MODEL,
    instruction=EMAIL_CRAFTER_PROMPT,
    output_key="crafted_email"
)
