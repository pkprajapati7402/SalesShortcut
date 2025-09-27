"""
Quality Checker Agent for validating commercial offer quality.
"""

from google.adk.agents.llm_agent import LlmAgent
from sdr.sdr.config import MODEL_THINK
from .spec_template import SPEC_MARKDOWN_TEMPLATE as template
from .specs_prompts import QUALITY_CHECKER_PROMPT

quality_checker_agent = LlmAgent(
    name="QualityCheckerAgent",
    description="Agent that validates and ensures quality of commercial specifications and offers",
    model=MODEL_THINK,
    instruction=QUALITY_CHECKER_PROMPT.format(
        markdown_template=template
    ),
    output_key="quality_check_status"
)