"""
Main entry point for the Lead Manager Agent.
Imports the properly structured Sequential Agent.
"""

from .lead_manager.agent import root_agent

# Export the root agent for use by the agent executor
__all__ = ['root_agent']