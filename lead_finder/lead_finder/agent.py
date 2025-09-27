"""
Main agent definition for the Lead Finder Agent.
"""

import logging
from typing import Dict, Any, List, Optional
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.agents.sequential_agent import SequentialAgent
from .config import MODEL
from .prompts import ROOT_AGENT_PROMPT
from .sub_agents.potential_lead_finder_agent import potential_lead_finder_agent
from .sub_agents.merger_agent import merger_agent
from .callbacks import post_results_callback
from .tools.bigquery_utils import (
    bigquery_upload, 
    bigquery_query_leads,
    bigquery_no_website_upload,
    bigquery_query_no_website_leads
)

# Create the root agent (LeadFinderAgent)
lead_finder_agent = SequentialAgent(
    name="LeadFinderAgent",
    description="Sequential agent for finding business leads in a specified city",
    sub_agents=[potential_lead_finder_agent, merger_agent],
    after_agent_callback=post_results_callback,
)

root_agent = lead_finder_agent
