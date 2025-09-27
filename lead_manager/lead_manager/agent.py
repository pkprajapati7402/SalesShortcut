"""
Main agent definition for the Lead Manager Agent.
"""

from google.adk.agents.sequential_agent import SequentialAgent
from .config import MODEL
from .sub_agents.email_checker_agent import email_checker_agent
from .sub_agents.email_analyzer_instance import email_analyzer
from .sub_agents.post_action_agent import post_action_agent
from .callbacks import post_lead_manager_callback

# Create the root agent (LeadManagerAgent)
lead_manager_agent = SequentialAgent(
    name="LeadManagerAgent",
    description="Sequential agent for managing hot leads through email monitoring, meeting scheduling, and UI notifications",
    sub_agents=[
        email_checker_agent,
        email_analyzer,
        post_action_agent
    ],
    after_agent_callback=post_lead_manager_callback,
)

root_agent = lead_manager_agent