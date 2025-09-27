"""
ClusterSearchAgent implementation.
"""

from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext

from ..config import MODEL
from ..prompts import CLUSTER_SEARCH_AGENT_PROMPT
from ..tools.cluster_search import cluster_search_tool

cluster_search_agent = LlmAgent(
    model=MODEL,
    name="ClusterSearchAgent",
    description="Agent specialized in finding business information using custom cluster search",
    instruction=CLUSTER_SEARCH_AGENT_PROMPT,
    tools=[cluster_search_tool],
)

