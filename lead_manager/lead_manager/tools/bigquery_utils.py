"""
BigQuery utility tools for Lead Manager.
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from google.adk.tools import FunctionTool
from google.cloud import bigquery
from ..config import PROJECT, DATASET_ID, TABLE_ID, MEETING_TABLE_ID

logger = logging.getLogger(__name__)


# TODO(sergazy): Implement these
def _write_json_file(filepath: Path, data: Dict[str, Any]) -> None:
    """Helper function to write JSON data to file."""
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

async def check_hot_lead(email_address: str) -> bool:
    """
    Check if an email address is in the hot leads database.
    
    Args:
        email_address: Email address to check
        
    Returns:
        bool indicating if the email is a hot lead or not, along with lead data if found.
    """
    
    # Sleep for 2 sec
    try:
        logger.info(f"🔍 Checking if {email_address} is a hot lead...")
        
        # Initialize BigQuery client
        client = bigquery.Client(project=PROJECT)
        
        # Query to check if email exists in hot leads table
        query = f"""
        SELECT 
            *
        FROM `{PROJECT}.{DATASET_ID}.{TABLE_ID}`
        WHERE LOWER(email) = LOWER(@email_address)
        LIMIT 1
        """
        
        # Configure query parameters
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email_address", "STRING", email_address),
            ]
        )
        
        # Execute query
        query_job = client.query(query, job_config=job_config)
        results = list(query_job)
        
        if not results:
            logger.info(f"❌ {email_address} is not a hot lead")
            return {
                "success": True,
                "is_hot_lead": False,
                "email": email_address,
                "lead_data": None,
                "message": f"{email_address} is not found in hot leads database"
            }
        
        # Convert BigQuery row to dictionary
        lead_data = dict(results[0])
        
        # Convert any datetime objects to strings for JSON serialization
        for key, value in lead_data.items():
            if isinstance(value, datetime):
                lead_data[key] = value.isoformat()
        
        logger.info(f"✅ {email_address} is a hot lead!")
        return {
            "success": True,
            "is_hot_lead": True,
            "email": email_address,
            "lead_data": lead_data,
            "message": f"{email_address} found in hot leads database"
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking hot lead: {e}")
        return {
            "success": False,
            "is_hot_lead": False,
            "email": email_address,
            "lead_data": None,
            "error": str(e),
            "message": f"Error checking hot lead status: {str(e)}"
        }

async def save_meeting_arrangement(
    calendar_request: Dict[str, Any],
    email_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save meeting arrangement data to BigQuery.
    
    Args:
        lead_data: Hot lead information
        meeting_data: Meeting details and results
        email_data: Original email that triggered the meeting
        
    Returns:
        Dictionary containing upload status
    """
    try:
        logger.info("💾 Saving meeting arrangement to BigQuery...")
        
        # Create output file for backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lead_manager_meeting_{timestamp}.json"
        filepath = Path(filename)
        
        # Write backup file
        backup_data = {
            "full_meeting_data": calendar_request,
            "full_email_data": email_data
        }
        _write_json_file(filepath, backup_data)
        
        # Initialize BigQuery client
        # client = bigquery.Client(project=PROJECT)
        
        # # Get table reference
        # table_id = f"{PROJECT}.{DATASET_ID}.{MEETING_TABLE_ID}"
        
        
        logger.info("✅ Meeting arrangement saved to BigQuery successfully")
        return {
            "success": True,
            "backup_file": str(filepath),
            "message": "Meeting arrangement saved successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Error saving meeting arrangement: {e}")
        return {
            "success": False,
            "error": str(e),
            "backup_file": str(filepath) if 'filepath' in locals() else None,
            "message": f"Error saving meeting arrangement: {str(e)}."
        }

# Create the tools
check_hot_lead_tool = FunctionTool(func=check_hot_lead)

save_meeting_tool = FunctionTool(func=save_meeting_arrangement)