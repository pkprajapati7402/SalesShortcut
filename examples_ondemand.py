"""
Example: Using On-demand.io Agents in SalesShortcut
====================================================
This example demonstrates how to integrate On-demand.io agents
into the SalesShortcut workflow.
"""

from common.ondemand_client import ondemand_client
from common.ondemand_config import OnDemandConfig
import json


def example_lead_discovery_with_enrichment():
    """
    Example: Lead Finder discovers a lead and enriches it with On-demand.io
    """
    print("=" * 60)
    print("EXAMPLE 1: Lead Discovery + Enrichment")
    print("=" * 60)
    
    # Step 1: Lead Finder discovers a lead (mocked here)
    discovered_lead = {
        "company_name": "Acme HVAC Services",
        "domain": "acmehvac.com",
        "location": "Austin, TX",
        "phone": "+1-512-555-0123"
    }
    
    print("\n1. Lead Discovered:")
    print(json.dumps(discovered_lead, indent=2))
    
    # Step 2: Enrich with On-demand.io
    print("\n2. Enriching lead with On-demand.io...")
    enriched = ondemand_client.enrich_lead(
        company_name=discovered_lead["company_name"],
        domain=discovered_lead["domain"],
        location=discovered_lead["location"]
    )
    
    print("\n3. Enriched Data:")
    print(json.dumps(enriched, indent=2))
    
    # In real implementation, this enriched data would be:
    # - Stored in BigQuery
    # - Passed to Lead Manager for qualification
    # - Used by SDR for personalized outreach
    
    return enriched


def example_lead_qualification():
    """
    Example: Lead Manager qualifies a lead using On-demand.io
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Lead Qualification")
    print("=" * 60)
    
    # Step 1: Lead data from Lead Finder (enriched)
    lead_data = {
        "company_name": "Acme HVAC Services",
        "employee_count": 45,
        "estimated_revenue": 3500000,
        "industry": "HVAC Services",
        "location": "Austin, TX",
        "tech_stack": ["QuickBooks", "WordPress"],
        "decision_maker": "John Smith (Owner)"
    }
    
    # Step 2: Define ICP criteria
    icp_criteria = {
        "min_employees": 20,
        "max_employees": 100,
        "min_revenue": 1000000,
        "target_industries": ["HVAC", "Home Services", "Construction"],
        "target_locations": ["TX", "CA", "FL"]
    }
    
    print("\n1. Lead Data:")
    print(json.dumps(lead_data, indent=2))
    
    print("\n2. ICP Criteria:")
    print(json.dumps(icp_criteria, indent=2))
    
    # Step 3: Qualify with On-demand.io
    print("\n3. Qualifying with On-demand.io...")
    qualification = ondemand_client.qualify_lead(
        lead_data=lead_data,
        icp_criteria=icp_criteria
    )
    
    print("\n4. Qualification Result:")
    print(json.dumps(qualification, indent=2))
    
    return qualification


def example_personalized_outreach():
    """
    Example: SDR Agent generates personalized outreach using On-demand.io
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Personalized Outreach Generation")
    print("=" * 60)
    
    # Step 1: Qualified lead profile
    lead_profile = {
        "name": "John Smith",
        "title": "Owner",
        "company": "Acme HVAC Services",
        "employee_count": 45,
        "location": "Austin, TX",
        "pain_points": [
            "Seasonal lead generation fluctuations",
            "Lack of digital marketing presence",
            "Manual customer follow-up process"
        ],
        "interests": ["business growth", "automation", "customer retention"]
    }
    
    print("\n1. Lead Profile:")
    print(json.dumps(lead_profile, indent=2))
    
    # Step 2: Generate personalized email
    print("\n2. Generating personalized email with On-demand.io...")
    email = ondemand_client.compose_email(
        lead_profile=lead_profile,
        campaign_type="cold_outreach",
        tone="professional"
    )
    
    print("\n3. Generated Email:")
    print(json.dumps(email, indent=2))
    
    # Step 3: Generate call script
    print("\n4. Generating call script with On-demand.io...")
    call_script = ondemand_client.generate_call_script(
        lead_context=lead_profile,
        call_objective="discovery_call"
    )
    
    print("\n5. Generated Call Script:")
    print(json.dumps(call_script, indent=2))
    
    return email, call_script


def example_complete_workflow():
    """
    Example: Complete end-to-end workflow with On-demand.io
    """
    print("\n" + "=" * 60)
    print("COMPLETE WORKFLOW: Lead Discovery → Qualification → Outreach")
    print("=" * 60)
    
    # Phase 1: Discovery & Enrichment
    print("\n[PHASE 1] Lead Finder: Discovery & Enrichment")
    print("-" * 60)
    enriched_lead = example_lead_discovery_with_enrichment()
    
    # Phase 2: Qualification
    print("\n[PHASE 2] Lead Manager: Qualification")
    print("-" * 60)
    qualification = example_lead_qualification()
    
    # Phase 3: Outreach (only if qualified)
    if qualification.get("status") == "success":
        print("\n[PHASE 3] SDR Agent: Personalized Outreach")
        print("-" * 60)
        email, call_script = example_personalized_outreach()
        
        print("\n" + "=" * 60)
        print("✅ Workflow Complete!")
        print("=" * 60)
        print(f"Lead enriched with On-demand.io ✓")
        print(f"Lead qualified with On-demand.io ✓")
        print(f"Outreach content generated with On-demand.io ✓")
    else:
        print("\n❌ Lead did not meet ICP criteria - skipping outreach")


def show_configuration():
    """
    Show current On-demand.io configuration
    """
    print("\n" + "=" * 60)
    print("ON-DEMAND.IO CONFIGURATION")
    print("=" * 60)
    
    config_info = {
        "API Base": OnDemandConfig.API_BASE,
        "Workspace ID": OnDemandConfig.WORKSPACE_ID[:20] + "..." if OnDemandConfig.WORKSPACE_ID else "Not configured",
        "API Key": "***" + OnDemandConfig.API_KEY[-8:] if OnDemandConfig.API_KEY else "Not configured",
        "Enabled": OnDemandConfig.is_enabled(),
        "Timeout": f"{OnDemandConfig.TIMEOUT}s",
        "Max Retries": OnDemandConfig.MAX_RETRIES,
        "Caching": "Enabled" if OnDemandConfig.ENABLE_CACHING else "Disabled"
    }
    
    for key, value in config_info.items():
        print(f"{key:20}: {value}")
    
    print("\nAvailable Agents:")
    print("-" * 60)
    agents = {
        "Lead Enrichment": OnDemandConfig.LEAD_ENRICHMENT_AGENT,
        "Lead Qualification": OnDemandConfig.LEAD_QUALIFIER_AGENT,
        "Email Composer": OnDemandConfig.EMAIL_COMPOSER_AGENT,
        "Call Script": OnDemandConfig.CALL_SCRIPT_AGENT,
        "Data Validator": OnDemandConfig.DATA_VALIDATOR_AGENT
    }
    
    for name, agent_id in agents.items():
        print(f"  • {name:20}: {agent_id}")


if __name__ == "__main__":
    print("\n" + "🚀" * 30)
    print("SalesShortcut + On-demand.io Integration Examples")
    print("🚀" * 30)
    
    # Show configuration
    show_configuration()
    
    # Run examples
    print("\n\nRunning Examples...")
    print("=" * 60)
    
    try:
        # Example 1: Discovery + Enrichment
        example_lead_discovery_with_enrichment()
        
        # Example 2: Qualification
        example_lead_qualification()
        
        # Example 3: Outreach
        example_personalized_outreach()
        
        # Complete Workflow
        print("\n\n" + "🔄" * 30)
        example_complete_workflow()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: These examples work with mock data when On-demand.io is not configured.")
        print("Add your ONDEMAND_API_KEY to .env to use real agents.")
    
    print("\n" + "=" * 60)
    print("Examples complete! Check ONDEMAND_INTEGRATION.md for more details.")
    print("=" * 60)
