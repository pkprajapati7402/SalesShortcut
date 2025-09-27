"""
Fact Checker Agent for reviewing and improving proposals.
"""

from google.adk.agents.llm_agent import LlmAgent
from ..config import MODEL
from ..prompts import FACT_CHECKER_PROMPT


fact_checker_agent = LlmAgent(
    name="FactCheckerAgent",
    description="Agent that reviews and improves proposal drafts for accuracy and effectiveness",
    model=MODEL,
    instruction=FACT_CHECKER_PROMPT,
    output_key="proposal"
)