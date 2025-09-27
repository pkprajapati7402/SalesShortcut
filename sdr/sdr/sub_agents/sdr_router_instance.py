"""
SDR Router Instance - Creates the SDRRouter agent with proper sub-agents.
"""

from .sdr_router import SDRRouter
from .outreach_email_agent import outreach_email_agent
from .lead_clerk_agent import lead_clerk_agent

# Create the SDRRouter instance
sdr_router = SDRRouter(
    name="SDRRouter",
    email_agent=outreach_email_agent,
    save_to_database_agent=lead_clerk_agent
)