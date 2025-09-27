"""
Draft Writer Agent for creating initial proposals.
"""

from google.adk.agents.llm_agent import LlmAgent
from ..prompts import DRAFT_WRITER_PROMPT
from ..config import MODEL


draft_writer_agent = LlmAgent(
    name="DraftWriterAgent",
    description="Agent that writes initial proposal drafts based on business research",
    model=MODEL,
    instruction=DRAFT_WRITER_PROMPT,
    output_key="draft_proposal"
)