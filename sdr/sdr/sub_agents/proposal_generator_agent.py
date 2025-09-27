"""
Proposal Generator Agent - Sequential agent with sub-agents for proposal creation.
"""

from google.adk.agents.sequential_agent import SequentialAgent
from .draft_writer_agent import draft_writer_agent
from .fact_checker_agent import fact_checker_agent

# Review/Critique Pattern (Generator-Critic)
proposal_generator_agent = SequentialAgent(
    name="ProposalGeneratorAgent",
    description="Sequential agent that generates and refines business proposals using Review/Critique pattern",
    sub_agents=[draft_writer_agent, fact_checker_agent],
)