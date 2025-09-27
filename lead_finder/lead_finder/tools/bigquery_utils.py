"""
BigQuery utility tools for lead data management.
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from google.adk.tools import FunctionTool
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, Conflict
from ..config import PROJECT, DATASET_ID, TABLE_ID

logger = logging.getLogger(__name__)

class BigQueryClient:
    """BigQuery client wrapper for lead data operations."""
    
    def __init__(self):
        self.client = None
        self.dataset_ref = None
        self.table_ref = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the BigQuery client and references."""
        if not PROJECT:
            logger.warning("Google Cloud Project not configured. BigQuery operations will be mocked.")
            return
        
        try:
            # Initialize client - it will use default credentials (GOOGLE_APPLICATION_CREDENTIALS or ADC)
            self.client = bigquery.Client(project=PROJECT)
            self.dataset_ref = self.client.dataset(DATASET_ID)
            self.table_ref = self.dataset_ref.table(TABLE_ID)
            logger.info(f"BigQuery client initialized for project: {PROJECT}")
            
            # Ensure dataset exists first
            self._ensure_dataset_exists()
            
            # Test the connection by trying to get the dataset
            try:
                self.client.get_dataset(self.dataset_ref)
                logger.info(f"Successfully connected to BigQuery dataset: {DATASET_ID}")
            except NotFound:
                logger.info(f"Dataset {DATASET_ID} not found, creating it...")
                self._ensure_dataset_exists()
            except Exception as dataset_error:
                logger.warning(f"Cannot access BigQuery dataset {DATASET_ID}: {dataset_error}")
                logger.info("Attempting to create dataset...")
                try:
                    self._ensure_dataset_exists()
                except Exception as create_error:
                    logger.error(f"Failed to create dataset: {create_error}")
                    logger.info("BigQuery operations will use mock fallback")
                    self.client = None
                    return
            
            # Ensure table exists
            self._ensure_table_exists()
            
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            logger.info("BigQuery operations will use mock fallback")
            self.client = None

    def _ensure_dataset_exists(self):
        """Create the dataset if it doesn't exist."""
        if not self.client:
            return
        
        try:
            self.client.get_dataset(self.dataset_ref)
            logger.info(f"Dataset {DATASET_ID} exists")
        except NotFound:
            logger.info(f"Creating dataset {DATASET_ID}")
            dataset = bigquery.Dataset(self.dataset_ref)
            dataset.description = "Lead Finder data storage"
            dataset.location = "US"
            self.client.create_dataset(dataset)
            logger.info(f"Dataset {DATASET_ID} created successfully")

    def _ensure_table_exists(self):
        """Create the table with proper schema if it doesn't exist."""
        if not self.client:
            return
        
        try:
            self.client.get_table(self.table_ref)
            logger.info(f"Table {TABLE_ID} exists")
        except NotFound:
            logger.info(f"Creating table {TABLE_ID}")
            
            # Define the schema for business leads
            schema = [
                bigquery.SchemaField("place_id", "STRING", mode="REQUIRED", description="Google Places ID"),
                bigquery.SchemaField("name", "STRING", mode="REQUIRED", description="Business name"),
                bigquery.SchemaField("address", "STRING", mode="NULLABLE", description="Formatted address"),
                bigquery.SchemaField("phone", "STRING", mode="NULLABLE", description="Phone number"),
                bigquery.SchemaField("website", "STRING", mode="NULLABLE", description="Website URL"),
                bigquery.SchemaField("category", "STRING", mode="NULLABLE", description="Business category"),
                bigquery.SchemaField("rating", "FLOAT", mode="NULLABLE", description="Rating (1-5)"),
                bigquery.SchemaField("total_ratings", "INTEGER", mode="NULLABLE", description="Number of ratings"),
                bigquery.SchemaField("price_level", "INTEGER", mode="NULLABLE", description="Price level (0-4)"),
                bigquery.SchemaField("is_open", "BOOLEAN", mode="NULLABLE", description="Currently open status"),
                bigquery.SchemaField("city", "STRING", mode="REQUIRED", description="City searched"),
                bigquery.SchemaField("search_type", "STRING", mode="NULLABLE", description="Type of search performed"),
                bigquery.SchemaField("latitude", "FLOAT", mode="NULLABLE", description="Latitude"),
                bigquery.SchemaField("longitude", "FLOAT", mode="NULLABLE", description="Longitude"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", description="Record creation timestamp"),
                bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED", description="Last update timestamp"),
                bigquery.SchemaField("lead_status", "STRING", mode="NULLABLE", description="Lead qualification status"),
                bigquery.SchemaField("contact_attempts", "INTEGER", mode="NULLABLE", description="Number of contact attempts"),
                bigquery.SchemaField("last_contact_date", "TIMESTAMP", mode="NULLABLE", description="Last contact attempt date"),
                bigquery.SchemaField("notes", "STRING", mode="NULLABLE", description="Additional notes")
            ]
            
            table = bigquery.Table(self.table_ref, schema=schema)
            table.description = "Business leads data from Google Maps searches"
            
            # Add partitioning and clustering for better performance
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="created_at"
            )
            table.clustering_fields = ["city", "category", "lead_status"]
            
            self.client.create_table(table)
            logger.info(f"Table {TABLE_ID} created successfully with schema")

    def _validate_business_data(self, business: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean business data before insertion."""
        # Required fields
        if not business.get("place_id") or not business.get("name"):
            raise ValueError("Business must have place_id and name")
        
        # Clean and validate data
        cleaned = {
            "place_id": str(business["place_id"])[:255],  # Ensure string and limit length
            "name": str(business["name"])[:255],
            "address": str(business.get("address", ""))[:500] if business.get("address") else None,
            "phone": str(business.get("phone", ""))[:50] if business.get("phone") else None,
            "website": str(business.get("website", ""))[:500] if business.get("website") else None,
            "category": str(business.get("category", ""))[:100] if business.get("category") else None,
            "rating": float(business["rating"]) if business.get("rating") is not None else None,
            "total_ratings": int(business["total_ratings"]) if business.get("total_ratings") is not None else None,
            "price_level": int(business["price_level"]) if business.get("price_level") is not None else None,
            "is_open": bool(business["is_open"]) if business.get("is_open") is not None else None,
            "city": str(business.get("city", ""))[:100],
            "search_type": str(business.get("search_type", ""))[:50] if business.get("search_type") else None,
        }
        
        # Handle location data
        location = business.get("location", {})
        cleaned["latitude"] = float(location["lat"]) if location and location.get("lat") is not None else None
        cleaned["longitude"] = float(location["lng"]) if location and location.get("lng") is not None else None
        
        # Add timestamps and default values
        now = datetime.utcnow()
        cleaned["created_at"] = now.isoformat() + 'Z'  # BigQuery expects ISO format with Z
        cleaned["updated_at"] = now.isoformat() + 'Z'
        cleaned["lead_status"] = "NEW"
        cleaned["contact_attempts"] = 0
        cleaned["last_contact_date"] = None
        cleaned["notes"] = None
        
        return cleaned

    async def upload_businesses(self, businesses: List[Dict[str, Any]], city: str, search_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload business data to BigQuery with deduplication.
        
        Args:
            businesses: List of business data dictionaries
            city: The city these businesses are from
            search_type: The type of search performed
            
        Returns:
            Dictionary with upload results and statistics
        """
        if not self.client:
            logger.info("BigQuery client not available, using mock upload")
            return await self._mock_upload(businesses, city, search_type)
        
        if not businesses:
            return {"status": "success", "message": "No businesses to upload", "stats": {"total": 0}}
        
        try:
            # Prepare data for insertion
            rows_to_insert = []
            validation_errors = []
            
            for i, business in enumerate(businesses):
                try:
                    # Add city and search_type to business data
                    business_data = business.copy()
                    business_data["city"] = city
                    business_data["search_type"] = search_type
                    
                    cleaned_business = self._validate_business_data(business_data)
                    rows_to_insert.append(cleaned_business)
                    
                except ValueError as e:
                    validation_errors.append(f"Business {i}: {str(e)}")
                    logger.warning(f"Validation error for business {i}: {e}")
            
            if not rows_to_insert:
                return {
                    "status": "error",
                    "message": "No valid businesses to upload",
                    "validation_errors": validation_errors
                }
            
            # Check for existing records to avoid duplicates
            existing_place_ids = await self._get_existing_place_ids([row["place_id"] for row in rows_to_insert])
            
            # Filter out duplicates
            new_rows = [row for row in rows_to_insert if row["place_id"] not in existing_place_ids]
            duplicate_count = len(rows_to_insert) - len(new_rows)
            
            if new_rows:
                # Insert new rows
                def _insert_rows():
                    try:
                        errors = self.client.insert_rows_json(self.table_ref, new_rows)
                        return errors
                    except Exception as e:
                        logger.error(f"Error in insert_rows_json: {e}")
                        raise
                
                errors = await asyncio.to_thread(_insert_rows)
                
                if errors:
                    logger.error(f"BigQuery insertion errors: {errors}")
                    return {
                        "status": "partial_success",
                        "message": f"Some rows failed to insert: {errors}",
                        "stats": {
                            "total_input": len(businesses),
                            "validated": len(rows_to_insert),
                            "duplicates_skipped": duplicate_count,
                            "new_inserted": len(new_rows) - len(errors),
                            "failed": len(errors)
                        },
                        "errors": errors,
                        "validation_errors": validation_errors
                    }
            
            logger.info(f"Successfully uploaded {len(new_rows)} businesses to BigQuery")
            
            return {
                "status": "success",
                "message": f"Successfully uploaded {len(new_rows)} new businesses",
                "stats": {
                    "total_input": len(businesses),
                    "validated": len(rows_to_insert),
                    "duplicates_skipped": duplicate_count,
                    "new_inserted": len(new_rows),
                    "failed": 0
                },
                "validation_errors": validation_errors
            }
            
        except Exception as e:
            logger.error(f"Error uploading businesses to BigQuery: {e}")
            return {
                "status": "error",
                "message": f"BigQuery upload failed: {str(e)}",
                "stats": {"total_input": len(businesses), "failed": len(businesses)}
            }

    async def _get_existing_place_ids(self, place_ids: List[str]) -> set:
        """Check which place_ids already exist in the table."""
        if not self.client or not place_ids:
            return set()
        
        try:
            # Create a query to check for existing place_ids
            place_ids_str = "', '".join(place_ids)
            query = f"""
                SELECT DISTINCT place_id 
                FROM `{PROJECT}.{DATASET_ID}.{TABLE_ID}` 
                WHERE place_id IN ('{place_ids_str}')
            """
            
            def _run_query():
                return list(self.client.query(query))
            
            results = await asyncio.to_thread(_run_query)
            return {row.place_id for row in results}
            
        except Exception as e:
            logger.error(f"Error checking existing place_ids: {e}")
            return set()

    async def query_businesses(
        self, 
        city: Optional[str] = None, 
        category: Optional[str] = None,
        min_rating: Optional[float] = None,
        lead_status: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Query businesses from BigQuery with filters.
        
        Args:
            city: Filter by city
            category: Filter by business category
            min_rating: Minimum rating filter
            lead_status: Filter by lead status
            limit: Maximum number of results
        
        Returns:
            Dictionary with query results
        """
        if not self.client:
            return {"status": "error", "message": "BigQuery client not available"}
        
        try:
            # Build WHERE clause
            where_conditions = []
            if city:
                where_conditions.append(f"city = '{city}'")
            if category:
                where_conditions.append(f"category = '{category}'")
            if min_rating:
                where_conditions.append(f"rating >= {min_rating}")
            if lead_status:
                where_conditions.append(f"lead_status = '{lead_status}'")
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            query = f"""
                SELECT *
                FROM `{PROJECT}.{DATASET_ID}.{TABLE_ID}`
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT {limit}
            """
            
            def _run_query():
                return [dict(row) for row in self.client.query(query)]
            
            results = await asyncio.to_thread(_run_query)
            
            return {
                "status": "success",
                "total_results": len(results),
                "filters": {
                    "city": city,
                    "category": category,
                    "min_rating": min_rating,
                    "lead_status": lead_status
                },
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error querying businesses: {e}")
            return {"status": "error", "message": str(e)}

    async def _mock_upload(self, businesses: List[Dict[str, Any]], city: str, search_type: Optional[str] = None) -> Dict[str, Any]:
        """Mock upload for when BigQuery is not available."""
        logger.info(f"Mock BigQuery upload: {len(businesses)} businesses for {city}")
        
        # Write to JSON file as fallback
        timestamp = datetime.now().isoformat().replace(":", "-")
        filename = f"bigquery_mock_{city}_{timestamp}.json"
        
        # Prepare data for JSON serialization (avoid datetime objects)
        serializable_businesses = []
        for business in businesses:
            # Create a copy and ensure all values are JSON serializable
            clean_business = {}
            for key, value in business.items():
                if isinstance(value, datetime):
                    clean_business[key] = value.isoformat()
                else:
                    clean_business[key] = value
            serializable_businesses.append(clean_business)
        
        mock_data = {
            "timestamp": datetime.now().isoformat(),
            "city": city,
            "search_type": search_type,
            "record_count": len(businesses),
            "data": serializable_businesses
        }
        
        try:
            import json
            from pathlib import Path
            
            def _write_file():
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(mock_data, f, indent=2, ensure_ascii=False, default=str)
            
            await asyncio.to_thread(_write_file)
            
            return {
                "status": "success",
                "message": f"Mock upload complete - written to {filename}",
                "stats": {
                    "total_input": len(businesses),
                    "new_inserted": len(businesses),
                    "duplicates_skipped": 0,
                    "failed": 0
                },
                "mock_file": filename
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Mock upload failed: {str(e)}",
                "stats": {"total_input": len(businesses), "failed": len(businesses)}
            }

# Global client instance
_bigquery_client = BigQueryClient()

async def bigquery_upload(data: List[Dict[str, Any]], city: str = "", search_type: str = "general") -> Dict[str, Any]:
    """
    Upload business data to BigQuery.
    
    Args:
        data: The business data to upload
        city: The city these businesses are from
        search_type: The type of search performed
        
    Returns:
        A dictionary containing upload status and statistics
    """
    try:
        if not data:
            return {"status": "success", "message": "No data to upload", "stats": {"total": 0}}
        
        logger.info(f"Starting BigQuery upload for {len(data)} businesses in {city}")
        
        result = await _bigquery_client.upload_businesses(data, city, search_type)
        
        # Log the results
        if result["status"] == "success":
            logger.info(f"BigQuery upload successful: {result['stats']}")
        else:
            logger.warning(f"BigQuery upload issues: {result.get('message', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in bigquery_upload: {e}")
        return {
            "status": "error",
            "message": f"Upload failed: {str(e)}",
            "stats": {"total_input": len(data) if data else 0, "failed": len(data) if data else 0}
        }

async def bigquery_query_leads(
    city: Optional[str] = None,
    category: Optional[str] = None,
    min_rating: Optional[float] = None,
    lead_status: str = "NEW",
    limit: int = 50
) -> Dict[str, Any]:
    """
    Query leads from BigQuery with filters.
    
    Args:
        city: Filter by city
        category: Filter by business category  
        min_rating: Minimum rating filter
        lead_status: Lead status filter
        limit: Maximum number of results
        
    Returns:
        A dictionary containing query results
    """
    try:
        logger.info(f"Querying leads: city={city}, category={category}, min_rating={min_rating}")
        
        result = await _bigquery_client.query_businesses(
            city=city,
            category=category,
            min_rating=min_rating,
            lead_status=lead_status,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error querying leads: {e}")
        return {"status": "error", "message": str(e)}

# Create function tools
bigquery_upload_tool = FunctionTool(func=bigquery_upload)
bigquery_query_leads_tool = FunctionTool(func=bigquery_query_leads)

# --- NEW: No-Website Table Config ---
NO_WEBSITE_TABLE_ID = "business_leads_no_websites"

# --- NEW: No-Website Table Schema (same as business_leads, minus 'website') ---
NO_WEBSITE_SCHEMA = [
    bigquery.SchemaField("place_id", "STRING", mode="REQUIRED", description="Google Places ID"),
    bigquery.SchemaField("name", "STRING", mode="REQUIRED", description="Business name"),
    bigquery.SchemaField("address", "STRING", mode="NULLABLE", description="Formatted address"),
    bigquery.SchemaField("phone", "STRING", mode="NULLABLE", description="Phone number"),
    bigquery.SchemaField("category", "STRING", mode="NULLABLE", description="Business category"),
    bigquery.SchemaField("rating", "FLOAT", mode="NULLABLE", description="Rating (1-5)"),
    bigquery.SchemaField("total_ratings", "INTEGER", mode="NULLABLE", description="Number of ratings"),
    bigquery.SchemaField("price_level", "INTEGER", mode="NULLABLE", description="Price level (0-4)"),
    bigquery.SchemaField("is_open", "BOOLEAN", mode="NULLABLE", description="Currently open status"),
    bigquery.SchemaField("city", "STRING", mode="REQUIRED", description="City searched"),
    bigquery.SchemaField("search_type", "STRING", mode="NULLABLE", description="Type of search performed"),
    bigquery.SchemaField("latitude", "FLOAT", mode="NULLABLE", description="Latitude"),
    bigquery.SchemaField("longitude", "FLOAT", mode="NULLABLE", description="Longitude"),
    bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", description="Record creation timestamp"),
    bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED", description="Last update timestamp"),
    bigquery.SchemaField("lead_status", "STRING", mode="NULLABLE", description="Lead qualification status"),
    bigquery.SchemaField("contact_attempts", "INTEGER", mode="NULLABLE", description="Number of contact attempts"),
    bigquery.SchemaField("last_contact_date", "TIMESTAMP", mode="NULLABLE", description="Last contact attempt date"),
    bigquery.SchemaField("notes", "STRING", mode="NULLABLE", description="Additional notes"),
]

# --- NEW: Ensure No-Website Table Exists ---
def ensure_no_website_table_exists(client, dataset_ref):
    table_ref = dataset_ref.table(NO_WEBSITE_TABLE_ID)
    try:
        client.get_table(table_ref)
        logger.info(f"Table {NO_WEBSITE_TABLE_ID} exists")
    except NotFound:
        logger.info(f"Creating table {NO_WEBSITE_TABLE_ID}")
        table = bigquery.Table(table_ref, schema=NO_WEBSITE_SCHEMA)
        table.description = "Business leads with no website info"
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="created_at"
        )
        table.clustering_fields = ["city", "category", "lead_status"]
        client.create_table(table)
        logger.info(f"Table {NO_WEBSITE_TABLE_ID} created successfully with schema")
    return table_ref

# --- NEW: Upload Businesses Without Websites ---
async def bigquery_no_website_upload(data: List[Dict[str, Any]], city: str = "", search_type: str = "general") -> Dict[str, Any]:
    """
    Upload businesses with no website to the business_leads_no_websites table.
    """
    # Filter out businesses that have a website
    filtered = [b for b in data if not b.get("website")]
    if not filtered:
        return {"status": "success", "message": "No businesses without websites to upload", "stats": {"total": 0}}

    # Use BigQuery client
    client = BigQueryClient()
    if not client.client:
        # Fallback to mock upload
        return await client._mock_upload(filtered, city, search_type)

    # Ensure the no-website table exists
    table_ref = ensure_no_website_table_exists(client.client, client.dataset_ref)

    # Prepare and clean data (reuse validation, but skip website)
    rows_to_insert = []
    validation_errors = []
    for i, business in enumerate(filtered):
        try:
            # Remove website field if present
            business = dict(business)
            business.pop("website", None)
            # Add city and search_type
            business["city"] = city
            business["search_type"] = search_type
            # Validate using the same logic, but ignore website
            cleaned = client._validate_business_data(business)
            cleaned.pop("website", None)
            rows_to_insert.append(cleaned)
        except Exception as e:
            validation_errors.append(f"Business {i}: {str(e)}")
            logger.warning(f"Validation error for business {i}: {e}")
    if not rows_to_insert:
        return {"status": "error", "message": "No valid businesses to upload", "validation_errors": validation_errors}
    # Insert rows
    def _insert_rows():
        try:
            errors = client.client.insert_rows_json(table_ref, rows_to_insert)
            return errors
        except Exception as e:
            logger.error(f"Error in insert_rows_json (no website): {e}")
            raise
    import asyncio
    errors = await asyncio.to_thread(_insert_rows)
    if errors:
        logger.error(f"BigQuery insertion errors (no website): {errors}")
        return {
            "status": "partial_success",
            "message": f"Some rows failed to insert: {errors}",
            "stats": {"total_input": len(filtered), "new_inserted": len(filtered) - len(errors), "failed": len(errors)},
            "errors": errors,
            "validation_errors": validation_errors
        }
    logger.info(f"Successfully uploaded {len(rows_to_insert)} businesses with no website to BigQuery")
    return {
        "status": "success",
        "message": f"Successfully uploaded {len(rows_to_insert)} new businesses with no website",
        "stats": {"total_input": len(filtered), "new_inserted": len(rows_to_insert), "failed": 0},
        "validation_errors": validation_errors
    }

# --- NEW: Query Businesses Without Websites ---
async def bigquery_query_no_website_leads(
    city: Optional[str] = None,
    category: Optional[str] = None,
    min_rating: Optional[float] = None,
    lead_status: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Query businesses from business_leads_no_websites table with filters.
    """
    client = BigQueryClient()
    if not client.client:
        return {"status": "error", "message": "BigQuery client not available"}
    table_ref = ensure_no_website_table_exists(client.client, client.dataset_ref)
    # Build WHERE clause
    where_conditions = []
    if city:
        where_conditions.append(f"city = '{city}'")
    if category:
        where_conditions.append(f"category = '{category}'")
    if min_rating:
        where_conditions.append(f"rating >= {min_rating}")
    if lead_status:
        where_conditions.append(f"lead_status = '{lead_status}'")
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    query = f"""
        SELECT *
        FROM `{PROJECT}.{DATASET_ID}.{NO_WEBSITE_TABLE_ID}`
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT {limit}
    """
    def _run_query():
        return [dict(row) for row in client.client.query(query)]
    import asyncio
    results = await asyncio.to_thread(_run_query)
    return {
        "status": "success",
        "total_results": len(results),
        "filters": {"city": city, "category": category, "min_rating": min_rating, "lead_status": lead_status},
        "results": results
    }

# --- NEW: Tools for upload/query ---
bigquery_no_website_upload_tool = FunctionTool(func=bigquery_no_website_upload)
bigquery_query_no_website_leads_tool = FunctionTool(func=bigquery_query_no_website_leads)