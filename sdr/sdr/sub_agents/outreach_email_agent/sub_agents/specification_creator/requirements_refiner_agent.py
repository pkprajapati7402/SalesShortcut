"""
Requirements Refiner Agent for analyzing and refining commercial requirements.
"""

from google.adk.agents.llm_agent import LlmAgent
from sdr.sdr.config import MODEL_THINK
from .specs_prompts import REQUIREMENTS_REFINER_PROMPT
from .spec_template import SPEC_MARKDOWN_TEMPLATE as template

requirements_refiner_agent = LlmAgent(
    name="RequirementsRefinerAgent",
    description="Agent that analyzes customer needs and refines business requirements for commercial offers",
    model=MODEL_THINK,
    instruction=REQUIREMENTS_REFINER_PROMPT.format(
        markdown_template=template
    ),
    output_key="refined_requirements"
)