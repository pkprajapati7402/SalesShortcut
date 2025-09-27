"""
Outreach Email Agent - Sequential agent for creating commercial offers and sending emails.
"""

from google.adk.agents.sequential_agent import SequentialAgent
from .sub_agents.specification_creator.specification_creator_agent import specification_creator_agent
from .sub_agents.website_creator.websiter_creator_agent import website_creator_agent
from .sub_agents.email_sender.email_agent import email_agent
from .sub_agents.engagement_saver_agent import engagement_saver_agent
from .sub_agents.offer_file_creator_agent import offer_file_creator_agent


outreach_email_agent = SequentialAgent(
    name="OutreachEmailAgent",
    description="Sequential agent that creates commercial specifications, demo websites, sends emails, and saves engagement data",
    sub_agents=[
        specification_creator_agent,
        website_creator_agent,
        offer_file_creator_agent,
        email_agent,
        engagement_saver_agent
    ],
)