"""
On-demand.io Agent Platform Configuration
==========================================
Configuration for integrating with On-demand.io's AI agent orchestration platform.
Used across Lead Finder, Lead Manager, and SDR agents for specialized tasks.
"""

import os
from typing import Optional


class OnDemandConfig:
    """Configuration for On-demand.io agent platform integration."""
    
    # API Configuration
    API_KEY: str = os.getenv("ONDEMAND_API_KEY", "")
    API_BASE: str = os.getenv("ONDEMAND_API_BASE", "https://api.ondemand.io/v1")
    WORKSPACE_ID: str = os.getenv("ONDEMAND_WORKSPACE_ID", "")
    
    # Agent IDs for specialized tasks
    LEAD_ENRICHMENT_AGENT: str = os.getenv("ONDEMAND_LEAD_ENRICHMENT_AGENT", "agent_enrich_lead_data_v2")
    LEAD_QUALIFIER_AGENT: str = os.getenv("ONDEMAND_LEAD_QUALIFIER_AGENT", "agent_qualify_b2b_leads_v3")
    EMAIL_COMPOSER_AGENT: str = os.getenv("ONDEMAND_EMAIL_COMPOSER_AGENT", "agent_compose_outreach_email_v2")
    CALL_SCRIPT_AGENT: str = os.getenv("ONDEMAND_CALL_SCRIPT_AGENT", "agent_generate_call_script_v1")
    DATA_VALIDATOR_AGENT: str = os.getenv("ONDEMAND_DATA_VALIDATOR_AGENT", "agent_validate_business_data_v1")
    
    # Integration Settings
    TIMEOUT: int = int(os.getenv("ONDEMAND_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("ONDEMAND_MAX_RETRIES", "3"))
    ENABLE_CACHING: bool = os.getenv("ONDEMAND_ENABLE_CACHING", "true").lower() == "true"
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if On-demand.io integration is enabled."""
        return bool(cls.API_KEY and cls.WORKSPACE_ID)
    
    @classmethod
    def get_agent_endpoint(cls, agent_id: str) -> str:
        """Get the full endpoint URL for an On-demand.io agent."""
        return f"{cls.API_BASE}/workspaces/{cls.WORKSPACE_ID}/agents/{agent_id}/invoke"
    
    @classmethod
    def get_headers(cls) -> dict:
        """Get authentication headers for On-demand.io API."""
        return {
            "Authorization": f"Bearer {cls.API_KEY}",
            "Content-Type": "application/json",
            "X-OnDemand-Workspace": cls.WORKSPACE_ID
        }


# Agent Use Cases Mapping
AGENT_USE_CASES = {
    "lead_enrichment": {
        "agent_id": OnDemandConfig.LEAD_ENRICHMENT_AGENT,
        "description": "Enriches lead data with company size, revenue, tech stack, and decision makers",
        "input_schema": {"company_name": "str", "domain": "str", "location": "str"},
        "used_by": ["lead_finder", "lead_manager"]
    },
    "lead_qualification": {
        "agent_id": OnDemandConfig.LEAD_QUALIFIER_AGENT,
        "description": "Qualifies leads based on ICP fit, buying signals, and engagement potential",
        "input_schema": {"lead_data": "dict", "icp_criteria": "dict"},
        "used_by": ["lead_manager"]
    },
    "email_composition": {
        "agent_id": OnDemandConfig.EMAIL_COMPOSER_AGENT,
        "description": "Generates personalized outreach emails based on lead profile and context",
        "input_schema": {"lead_profile": "dict", "campaign_type": "str", "tone": "str"},
        "used_by": ["sdr"]
    },
    "call_script_generation": {
        "agent_id": OnDemandConfig.CALL_SCRIPT_AGENT,
        "description": "Creates dynamic call scripts with objection handling for phone outreach",
        "input_schema": {"lead_context": "dict", "call_objective": "str"},
        "used_by": ["sdr"]
    },
    "data_validation": {
        "agent_id": OnDemandConfig.DATA_VALIDATOR_AGENT,
        "description": "Validates and cleans business data (emails, phones, addresses)",
        "input_schema": {"data": "dict", "validation_rules": "list"},
        "used_by": ["lead_finder", "lead_manager", "sdr"]
    }
}


def get_agent_info(use_case: str) -> Optional[dict]:
    """Get agent information for a specific use case."""
    return AGENT_USE_CASES.get(use_case)
