"""
BigQuery utility tools for SDR results.
"""
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
import os
import uuid

from typing import Dict, Any, List
from google.adk.tools import FunctionTool
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

logger = logging.getLogger(__name__)

def _write_json_file(filepath: Path, data: Dict[str, Any]) -> None:
    """Helper function to write JSON data to file."""
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "data": data
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


async def sdr_bigquery_upload(
    business_data: Dict[str, Any],
    proposal: str,
    call_category: Dict[str, Any],
) -> dict[str, Any]:
    """
    Uploads complete SDR interaction data to a dedicated BigQuery table.

    This function now performs a real upload to BigQuery, creating the
    dataset and table if they don't exist. It also saves a local JSON backup.
    """
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    # Use SDR-specific dataset and table, not the general env vars
    dataset_id = "sdr_data"
    table_id = "sdr_results"

    if not project:
        logger.error("sdr_bigquery_upload: GOOGLE_CLOUD_PROJECT not configured")
        return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT not configured"}

    # --- Prepare the record ---
    sdr_record = {
        "sdr_run_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "business_name": business_data.get("name"),
        "business_id": business_data.get("place_id"),
        "contact_email": call_category.get("email"),
        "call_category": call_category.get("category"),
        "proposal_summary": proposal,
        "full_transcript": call_category.get("summary"),
    }

    # --- Save local backup ---
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sdr_bigquery_upload_{timestamp_str}.json"
    filepath = Path(filename)
    try:
        await asyncio.to_thread(_write_json_file, filepath, sdr_record)
    except Exception as e:
        logger.error(f"Failed to write local backup file: {e}")


    # --- Upload to BigQuery ---
    try:
        logger.info(f"Attempting to insert record: {json.dumps(sdr_record, indent=2)}")
        client = bigquery.Client(project=project)

        # Ensure dataset exists
        dataset_ref = client.dataset(dataset_id)
        try:
            client.get_dataset(dataset_ref)
            logger.info(f"Dataset {dataset_id} exists")
        except NotFound:
            logger.info(f"Dataset {dataset_id} not found. Creating...")
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"  # You can change this based on your needs
            dataset = client.create_dataset(dataset, timeout=30)
            logger.info(f"Created dataset {dataset_id}")

        table_ref = dataset_ref.table(table_id)

        # Define the complete schema with proper modes
        target_schema = [
            bigquery.SchemaField("sdr_run_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("business_name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("business_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("contact_email", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("call_category", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("proposal_summary", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("full_transcript", "STRING", mode="NULLABLE"),
        ]

        # Check if table exists and validate schema
        table_exists = False
        try:
            table = client.get_table(table_ref)
            table_exists = True
            logger.info(f"Found existing table {table_id}")

            # Log current schema for debugging
            current_field_names = [field.name for field in table.schema]
            logger.info(f"Current table fields: {current_field_names}")

            # Check if schema matches
            target_field_names = [field.name for field in target_schema]
            logger.info(f"Expected fields: {target_field_names}")

            missing_fields = set(target_field_names) - set(current_field_names)
            extra_fields = set(current_field_names) - set(target_field_names)

            if missing_fields:
                logger.warning(f"Missing fields in table: {missing_fields}")
                # Add missing fields
                new_schema = list(table.schema)
                for field in target_schema:
                    if field.name in missing_fields:
                        logger.info(f"Adding field: {field.name}")
                        new_schema.append(field)
                table.schema = new_schema
                table = client.update_table(table, ["schema"])
                logger.info("Schema updated with missing fields")

            if extra_fields:
                logger.warning(f"Extra fields in table (will be ignored): {extra_fields}")

        except NotFound:
            logger.info(f"Table {table_id} not found. Creating with correct schema...")
            table = bigquery.Table(table_ref, schema=target_schema)
            table = client.create_table(table)
            logger.info(f"Created table {table_id} with schema: {[f.name for f in target_schema]}")

        errors = client.insert_rows_json(table, [sdr_record])
        if errors:
            logger.error(f"BigQuery insert errors for SDR data: {errors}")
            return {"status": "error", "message": f"BigQuery upload failed: {errors}", "backup_file": str(filepath)}

        logger.info(f"Successfully uploaded SDR data for {sdr_record['business_name']}")
        return {"status": "success", "message": "SDR data uploaded to BigQuery successfully.", "backup_file": str(filepath)}

    except Exception as e:
        logger.error(f"Error in sdr_bigquery_upload: {e}", exc_info=True)
        return {"status": "error", "message": str(e), "backup_file": str(filepath)}


sdr_bigquery_upload_tool = FunctionTool(func=sdr_bigquery_upload)


# --- NEW: Email Engagement Table ---
ENGAGEMENT_TABLE_ID = "email_engagement"

async def bigquery_email_engagement_upload(
    recipient_email: str,
    subject: str,
    status: str,
    campaign_id: str = "default_campaign",
    notes: str = ""
) -> Dict[str, Any]:
    """
    Upload email engagement data to BigQuery.
    """
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset_id = "sdr_data"

    if not project:
        return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT not configured"}

    try:
        client = bigquery.Client(project=project)
        table_ref = client.dataset(dataset_id).table(ENGAGEMENT_TABLE_ID)

        # Ensure table exists with the correct schema
        try:
            table = client.get_table(table_ref)
        except NotFound:
            logger.info(f"Table {ENGAGEMENT_TABLE_ID} not found. Creating.")
            schema = [
                bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("recipient_email", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("subject", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("campaign_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("notes", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            ]
            table = bigquery.Table(table_ref, schema=schema)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="timestamp"
            )
            table = client.create_table(table) # Re-assign the returned table object
            logger.info(f"Created BigQuery table: {ENGAGEMENT_TABLE_ID}")

        # Prepare data for insertion
        now = datetime.utcnow()
        row_to_insert = {
            "event_id": str(uuid.uuid4()),
            "recipient_email": recipient_email,
            "subject": subject,
            "status": status,
            "campaign_id": campaign_id,
            "notes": notes,
            "timestamp": now.isoformat(),
        }

        errors = client.insert_rows_json(table, [row_to_insert])
        if errors:
            logger.error(f"BigQuery insertion errors for engagement: {errors}")
            return {"status": "error", "message": f"Failed to insert engagement data: {errors}"}

        logger.info(f"Successfully uploaded email engagement data for {recipient_email}")
        return {"status": "success", "message": "Email engagement data uploaded successfully."}

    except Exception as e:
        logger.error(f"Error in bigquery_email_engagement_upload: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

# --- NEW: Function Tool for Email Engagement ---
bigquery_email_engagement_tool = FunctionTool(func=bigquery_email_engagement_upload)


# --- NEW: Accepted Offers Table ---
ACCEPTED_OFFERS_TABLE_ID = "accepted_offers"

async def bigquery_accepted_offer_upload(
    business_name: str,
    business_id: str,
    contact_email: str,
    offer_details: str,
    notes: str = ""
) -> Dict[str, Any]:
    """
    Upload accepted offer data to BigQuery.
    """
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset_id = "sdr_data"

    if not project:
        return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT not configured"}

    try:
        client = bigquery.Client(project=project)
        table_ref = client.dataset(dataset_id).table(ACCEPTED_OFFERS_TABLE_ID)

        try:
            table = client.get_table(table_ref)
        except NotFound:
            logger.info(f"Table {ACCEPTED_OFFERS_TABLE_ID} not found. Creating.")
            schema = [
                bigquery.SchemaField("acceptance_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("business_name", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("business_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("contact_email", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("offer_details", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("notes", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            ]
            table = bigquery.Table(table_ref, schema=schema)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="timestamp"
            )
            table = client.create_table(table) # Re-assign the returned table object
            logger.info(f"Created BigQuery table: {ACCEPTED_OFFERS_TABLE_ID}")

        now = datetime.utcnow()
        row_to_insert = {
            "acceptance_id": str(uuid.uuid4()),
            "business_name": business_name,
            "business_id": business_id,
            "contact_email": contact_email,
            "offer_details": offer_details,
            "notes": notes,
            "timestamp": now.isoformat(),
        }

        errors = client.insert_rows_json(table, [row_to_insert])
        if errors:
            logger.error(f"BigQuery insertion errors for accepted offer: {errors}")
            return {"status": "error", "message": f"Failed to insert accepted offer data: {errors}"}

        logger.info(f"Successfully uploaded accepted offer for {business_name}")
        return {"status": "success", "message": "Accepted offer data uploaded successfully."}

    except Exception as e:
        logger.error(f"Error in bigquery_accepted_offer_upload: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

# --- NEW: Function Tool for Accepted Offers ---
bigquery_accepted_offer_tool = FunctionTool(func=bigquery_accepted_offer_upload)