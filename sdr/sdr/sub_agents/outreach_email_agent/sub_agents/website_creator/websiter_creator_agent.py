"""
Websiter Creator Agent for creating demo prototype websites.
"""

from google.adk.agents import SequentialAgent
from .request_human_creation import request_URL
from .prompt_prepare_agent import prepare_prompt
from .process_decision_agent import process_decision

website_creator_agent = SequentialAgent(
    name="WebsiteCreatorAgent",
    description="Agent that creates demo prototype websites and returns the link",
    sub_agents=[
        prepare_prompt,
        request_URL,
        process_decision
    ],
)