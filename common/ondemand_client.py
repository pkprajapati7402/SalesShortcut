"""
On-demand.io Client
===================
Client for invoking On-demand.io AI agents for specialized tasks.
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from .ondemand_config import OnDemandConfig, get_agent_info


class OnDemandClient:
    """Client for interacting with On-demand.io agent platform."""
    
    def __init__(self):
        self.config = OnDemandConfig()
        self.session = requests.Session()
        self.session.headers.update(self.config.get_headers())
    
    def invoke_agent(
        self, 
        agent_id: str, 
        input_data: Dict[str, Any],
        timeout: Optional[int] = None,
        async_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Invoke an On-demand.io agent with input data.
        
        Args:
            agent_id: The agent identifier
            input_data: Input data for the agent
            timeout: Request timeout in seconds (defaults to config timeout)
            async_mode: Whether to run agent asynchronously
            
        Returns:
            Agent response data
        """
        if not self.config.is_enabled():
            return self._mock_response(agent_id, input_data)
        
        endpoint = self.config.get_agent_endpoint(agent_id)
        timeout = timeout or self.config.TIMEOUT
        
        payload = {
            "input": input_data,
            "async": async_mode,
            "cache_enabled": self.config.ENABLE_CACHING
        }
        
        try:
            response = self.session.post(
                endpoint,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[OnDemand] Error invoking agent {agent_id}: {e}")
            return self._mock_response(agent_id, input_data)
    
    def enrich_lead(self, company_name: str, domain: str, location: str) -> Dict[str, Any]:
        """Enrich lead data using On-demand.io enrichment agent."""
        return self.invoke_agent(
            self.config.LEAD_ENRICHMENT_AGENT,
            {
                "company_name": company_name,
                "domain": domain,
                "location": location
            }
        )
    
    def qualify_lead(self, lead_data: Dict[str, Any], icp_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Qualify lead using On-demand.io qualification agent."""
        return self.invoke_agent(
            self.config.LEAD_QUALIFIER_AGENT,
            {
                "lead_data": lead_data,
                "icp_criteria": icp_criteria
            }
        )
    
    def compose_email(self, lead_profile: Dict[str, Any], campaign_type: str, tone: str = "professional") -> Dict[str, Any]:
        """Compose personalized email using On-demand.io email composer agent."""
        return self.invoke_agent(
            self.config.EMAIL_COMPOSER_AGENT,
            {
                "lead_profile": lead_profile,
                "campaign_type": campaign_type,
                "tone": tone
            }
        )
    
    def generate_call_script(self, lead_context: Dict[str, Any], call_objective: str) -> Dict[str, Any]:
        """Generate call script using On-demand.io call script agent."""
        return self.invoke_agent(
            self.config.CALL_SCRIPT_AGENT,
            {
                "lead_context": lead_context,
                "call_objective": call_objective
            }
        )
    
    def validate_data(self, data: Dict[str, Any], validation_rules: list) -> Dict[str, Any]:
        """Validate business data using On-demand.io validation agent."""
        return self.invoke_agent(
            self.config.DATA_VALIDATOR_AGENT,
            {
                "data": data,
                "validation_rules": validation_rules
            }
        )
    
    def _mock_response(self, agent_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock response when On-demand.io is not configured."""
        return {
            "status": "success",
            "agent_id": agent_id,
            "mock": True,
            "message": "On-demand.io not configured - using mock data",
            "result": {
                "processed": True,
                "input_received": list(input_data.keys()),
                "note": "Configure ONDEMAND_API_KEY to use real On-demand.io agents"
            }
        }


# Convenience singleton instance
ondemand_client = OnDemandClient()


# Example Usage Functions
def example_enrich_lead():
    """Example: Enrich a lead with company data."""
    client = OnDemandClient()
    result = client.enrich_lead(
        company_name="Acme Corp",
        domain="acme.com",
        location="San Francisco, CA"
    )
    print(json.dumps(result, indent=2))


def example_qualify_lead():
    """Example: Qualify a lead based on ICP criteria."""
    client = OnDemandClient()
    result = client.qualify_lead(
        lead_data={
            "company_name": "Tech Startup Inc",
            "employee_count": 50,
            "revenue": 5000000,
            "industry": "SaaS"
        },
        icp_criteria={
            "min_employees": 20,
            "min_revenue": 1000000,
            "target_industries": ["SaaS", "Technology"]
        }
    )
    print(json.dumps(result, indent=2))


def example_compose_email():
    """Example: Compose a personalized outreach email."""
    client = OnDemandClient()
    result = client.compose_email(
        lead_profile={
            "name": "John Doe",
            "company": "Acme Corp",
            "title": "VP of Sales",
            "pain_points": ["lead generation", "sales automation"]
        },
        campaign_type="cold_outreach",
        tone="professional"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    print("On-demand.io Client Examples")
    print("=" * 50)
    print("\n1. Lead Enrichment:")
    example_enrich_lead()
    print("\n2. Lead Qualification:")
    example_qualify_lead()
    print("\n3. Email Composition:")
    example_compose_email()
