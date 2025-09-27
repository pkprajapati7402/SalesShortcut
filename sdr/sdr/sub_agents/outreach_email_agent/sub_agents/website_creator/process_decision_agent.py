from google.adk.agents.llm_agent import LlmAgent
from sdr.sdr.config import MODEL

process_decision = LlmAgent(
    name="ProcessDecision",
    model=MODEL,
    instruction=(
        "Check state key 'website_preview_link'. If it exists and is not empty and does not contain error messages, "
        "confirm the website creation is complete. If the website_preview_link is missing, empty, or contains error messages, "
        "report that website creation failed or is incomplete."
    )
)