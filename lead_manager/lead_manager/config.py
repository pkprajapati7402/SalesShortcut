"""
Configuration for the Lead Manager Agent.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Model configuration
MODEL = os.getenv("MODEL", "gemini-2.0-flash-lite")
MODEL_THINK = os.getenv("MODEL_THINK", "gemini-2.5-flash-preview-05-20")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
TOP_P = float(os.getenv("TOP_P", "0.95"))
TOP_K = int(os.getenv("TOP_K", "40"))

# BigQuery configuration
PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
DATASET_ID = os.getenv("DATASET_ID", "lead_manager_data")
TABLE_ID = os.getenv("TABLE_ID", "hot_leads")
MEETING_TABLE_ID = os.getenv("MEETING_TABLE_ID", "meetings_arranged")

# Gmail Service Account Configuration
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", ".secrets/sales-automation-service.json")
SALES_EMAIL = os.getenv("SALES_EMAIL", "sales@zemzen.org")
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

# Google Calendar Configuration
CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly'
]

# UI service configuration
UI_SERVICE_ENABLED = os.getenv("UI_SERVICE_ENABLED", "true").lower() == "true"



PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
# CLOUD PUBSUB CONFIGURATION  
TOPIC_NAME = os.getenv("TOPIC_NAME", "gmail-notifications")
SUBSCRIPTION_ID = os.getenv("SUBSCRIPTION_ID", "gmail-notifications-subscription")

# GMAIL MONITORING CONFIGURATION
USERS_TO_MONITOR = os.getenv("USERS_TO_MONITOR", "").split(",")
# Vertex AI configuration for meeting request analysis
CLOUD_PROJECT_ID = os.getenv("CLOUD_PROJECT_ID", "")
CLOUD_PROJECT_REGION = os.getenv("CLOUD_PROJECT_REGION", "")