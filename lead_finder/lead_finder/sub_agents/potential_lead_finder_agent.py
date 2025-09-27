"""
PotentialLeadFinderAgent implementation.
"""

from google.adk.agents import ParallelAgent 
from .google_maps_agent import google_maps_agent
# from .cluster_search_agent import cluster_search_agent

potential_lead_finder_agent = ParallelAgent(
    name="PotentialLeadFinderAgent",
    description="Parallel agent for finding potential business leads",
    sub_agents=[google_maps_agent] #, cluster_search_agent]
)
