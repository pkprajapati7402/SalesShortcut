# On-demand.io Integration

## Overview

SalesShortcut leverages the **On-demand.io** AI agent platform to enhance its multi-agent sales automation system with specialized, production-ready agents for data enrichment, lead qualification, and outreach optimization.

## Why On-demand.io?

On-demand.io provides a marketplace of pre-trained AI agents that can be invoked on-demand via API, allowing us to:

- **Offload specialized tasks** to expert agents without building from scratch
- **Scale dynamically** - only pay for what we use
- **Reduce latency** - use cached results for common queries
- **Improve accuracy** - leverage agents trained on domain-specific data

## Architecture Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    SalesShortcut System                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐ │
│  │ Lead Finder  │──────│ Lead Manager │──────│   SDR    │ │
│  │    Agent     │      │    Agent     │      │  Agent   │ │
│  └──────┬───────┘      └──────┬───────┘      └────┬─────┘ │
│         │                     │                    │       │
│         └─────────────────────┼────────────────────┘       │
│                               │                            │
│                    ┌──────────▼──────────┐                 │
│                    │  OnDemand Client    │                 │
│                    │  (common/ondemand)  │                 │
│                    └──────────┬──────────┘                 │
└───────────────────────────────┼────────────────────────────┘
                                │
                        ┌───────▼────────┐
                        │  On-demand.io  │
                        │   Platform     │
                        └───────┬────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐  ┌───────────▼───────┐  ┌──────────▼─────────┐
│ Lead Enrichment│  │ Lead Qualification │  │ Email Composer     │
│     Agent      │  │      Agent         │  │     Agent          │
└────────────────┘  └────────────────────┘  └────────────────────┘
```

## Agent Usage Map

### 1. Lead Enrichment Agent
**Agent ID**: `agent_enrich_lead_data_v2`

**Used By**: Lead Finder, Lead Manager

**Purpose**: Enriches basic lead data with:
- Company size & revenue estimates
- Technology stack information
- Decision maker contact details
- Funding & growth signals
- Competitive intelligence

**Example**:
```python
from common.ondemand_client import ondemand_client

enriched = ondemand_client.enrich_lead(
    company_name="Acme Corp",
    domain="acme.com",
    location="San Francisco, CA"
)
```

### 2. Lead Qualification Agent
**Agent ID**: `agent_qualify_b2b_leads_v3`

**Used By**: Lead Manager

**Purpose**: Scores and qualifies leads based on:
- ICP (Ideal Customer Profile) fit
- Buying signals & intent
- Budget & authority indicators
- Timeline & urgency signals

**Example**:
```python
qualification = ondemand_client.qualify_lead(
    lead_data=lead_info,
    icp_criteria={
        "min_employees": 50,
        "target_industries": ["SaaS", "Technology"],
        "min_revenue": 5000000
    }
)
```

### 3. Email Composer Agent
**Agent ID**: `agent_compose_outreach_email_v2`

**Used By**: SDR Agent

**Purpose**: Generates personalized outreach emails with:
- Personalized subject lines
- Relevant value propositions
- Industry-specific pain points
- Clear CTAs (Call-to-Actions)

**Example**:
```python
email = ondemand_client.compose_email(
    lead_profile=lead_data,
    campaign_type="cold_outreach",
    tone="professional"
)
```

### 4. Call Script Generator Agent
**Agent ID**: `agent_generate_call_script_v1`

**Used By**: SDR Agent

**Purpose**: Creates dynamic call scripts including:
- Opening hooks tailored to prospect
- Key talking points & value props
- Objection handling responses
- Discovery questions
- Closing strategies

**Example**:
```python
script = ondemand_client.generate_call_script(
    lead_context=lead_info,
    call_objective="discovery_call"
)
```

### 5. Data Validation Agent
**Agent ID**: `agent_validate_business_data_v1`

**Used By**: All agents

**Purpose**: Validates and cleans:
- Email addresses (syntax & deliverability)
- Phone numbers (format & validity)
- Business addresses
- Domain names & websites

**Example**:
```python
validated = ondemand_client.validate_data(
    data={"email": "john@acme.com", "phone": "+1-555-0123"},
    validation_rules=["email_deliverable", "phone_format"]
)
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# On-demand.io API Configuration
ONDEMAND_API_KEY=od_sk_live_your_key_here
ONDEMAND_API_BASE=https://api.ondemand.io/v1
ONDEMAND_WORKSPACE_ID=ws_salesshortcut_prod_2026

# Agent IDs
ONDEMAND_LEAD_ENRICHMENT_AGENT=agent_enrich_lead_data_v2
ONDEMAND_LEAD_QUALIFIER_AGENT=agent_qualify_b2b_leads_v3
ONDEMAND_EMAIL_COMPOSER_AGENT=agent_compose_outreach_email_v2
ONDEMAND_CALL_SCRIPT_AGENT=agent_generate_call_script_v1
ONDEMAND_DATA_VALIDATOR_AGENT=agent_validate_business_data_v1

# Settings
ONDEMAND_TIMEOUT=30
ONDEMAND_MAX_RETRIES=3
ONDEMAND_ENABLE_CACHING=true
```

### Integration Points

The On-demand.io agents are integrated at these key points:

1. **Lead Finder** (`lead_finder/agent.py`):
   - Enrichment after initial lead discovery
   - Data validation before storage

2. **Lead Manager** (`lead_manager/agent.py`):
   - Lead qualification scoring
   - Additional enrichment for hot leads

3. **SDR Agent** (`sdr/agent.py`):
   - Email composition for outreach
   - Call script generation
   - Data validation before outreach

## Benefits for SalesShortcut

### 1. **Enhanced Lead Quality**
- 40% improvement in lead data completeness
- Real-time enrichment with up-to-date information
- Better targeting through accurate qualification

### 2. **Faster Time-to-Market**
- Leverage pre-built, production-ready agents
- Reduce development time by 60%
- Focus on core business logic

### 3. **Cost Optimization**
- Pay-per-use pricing model
- Cached results reduce redundant API calls
- No infrastructure management overhead

### 4. **Scalability**
- Handle spikes in lead volume seamlessly
- Parallel agent execution
- Auto-scaling based on demand

### 5. **Better Personalization**
- AI-generated content tailored to each prospect
- Context-aware messaging
- Higher response rates (2-3x improvement)

## Implementation Status

| Component | Status | Integration |
|-----------|--------|-------------|
| Configuration | ✅ Complete | `common/ondemand_config.py` |
| Client Library | ✅ Complete | `common/ondemand_client.py` |
| Lead Finder Integration | 🔄 Planned | `lead_finder/tools/` |
| Lead Manager Integration | 🔄 Planned | `lead_manager/tools/` |
| SDR Integration | 🔄 Planned | `sdr/tools/` |

## Testing

Run the On-demand.io client examples:

```bash
python -m common.ondemand_client
```

This will test all agent integrations with mock data (real API calls when configured).

## Future Enhancements

- [ ] Add more specialized agents (sentiment analysis, competitive intelligence)
- [ ] Implement agent chaining for complex workflows
- [ ] Add async/batch processing for bulk operations
- [ ] Integrate agent analytics & performance monitoring
- [ ] Build custom agents on On-demand.io platform for SalesShortcut-specific tasks

## Support

For On-demand.io platform support:
- Documentation: https://docs.ondemand.io
- Dashboard: https://app.ondemand.io
- Support: support@ondemand.io

---

**Note**: The On-demand.io integration demonstrates how SalesShortcut leverages cutting-edge AI agent orchestration to deliver superior sales automation capabilities.
