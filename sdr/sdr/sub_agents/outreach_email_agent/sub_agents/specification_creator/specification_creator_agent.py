"""
Specification Creator Agent for creating detailed commercial specifications.
"""

from google.adk.agents import LoopAgent
from .requirements_refiner_agent import requirements_refiner_agent
from .quality_checker_agent import quality_checker_agent
from .spec_status_checker_agent import SpecStatusCheckerAgent

spec_creator_agent = LoopAgent(
    name="SpecCreatorAgent",
    description="Agent that creates detailed commercial specifications and offer documents",
    max_iterations=3,
    sub_agents=[requirements_refiner_agent, quality_checker_agent, SpecStatusCheckerAgent(name="SpecStatusCheckerAgent")],
)

# Alias for backward compatibility
specification_creator_agent = spec_creator_agent