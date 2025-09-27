"""
Utility functions for the Lead Finder Agent.
"""

from typing import Dict, Any, List
import json

def deduplicate_businesses(businesses: List[dict[str, Any]]) -> List[dict[str, Any]]:
    """
    Deduplicate business data based on name and address.
    
    Args:
        businesses: List of business data dictionaries
        
    Returns:
        Deduplicated list of businesses
    """
    # Use name and address as unique identifiers
    unique_businesses = {}
    for business in businesses:
        key = (business.get("name", ""), business.get("address", ""))
        if key not in unique_businesses:
            unique_businesses[key] = business
        else:
            # Merge additional fields if the business already exists
            existing = unique_businesses[key]
            for field, value in business.items():
                if field not in existing or not existing[field]:
                    existing[field] = value
    
    return list(unique_businesses.values())

def format_business_for_bigquery(business: dict[str, Any]) -> dict[str, Any]:
    """
    Format business data for BigQuery upload.
    
    Args:
        business: Business data dictionary
        
    Returns:
        Formatted business data
    """
    # Ensure consistent schema for BigQuery
    schema_fields = [
        "name", "address", "phone", "website", "category", 
        "rating", "established", "source", "timestamp"
    ]
    
    formatted = {field: business.get(field, "") for field in schema_fields}
    
    # Add additional metadata
    import datetime
    formatted["timestamp"] = datetime.datetime.now().isoformat()
    
    return formatted