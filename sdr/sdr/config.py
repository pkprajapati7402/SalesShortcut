"""
Configuration for the SDR Agent.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Model configuration
# Using cost-effective models - gemini-2.0-flash-lite is free tier
MODEL = os.getenv("MODEL", "gemini-2.0-flash-lite")
MODEL_THINK = os.getenv("MODEL_THINK", "gemini-2.0-flash-thinking-exp")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
TOP_P = float(os.getenv("TOP_P", "0.95"))
TOP_K = int(os.getenv("TOP_K", "40"))

# BigQuery configuration
PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
DATASET_ID = os.getenv("DATASET_ID", "sdr_data")
TABLE_ID = os.getenv("TABLE_ID", "sdr_results")

# Google Search API configuration
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")

# ElevenLabs configuration for phone calls
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "")
ELEVENLABS_PHONE_NUMBER_ID = os.getenv("ELEVENLABS_PHONE_NUMBER_ID", "")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")


# Google Cloud Client ID for OAuth (Legacy - for backward compatibility)
GOOGLE_CLOUD_CLIENT_ID = os.getenv("GOOGLE_CLOUD_CLIENT_ID", "")
GOOGLE_CLOUD_CLIENT_SECRET = os.getenv("GOOGLE_CLOUD_CLIENT_SECRET", "")

# Gmail Service Account Configuration (New - No manual auth required)
# For local development
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", ".secrets/sales-automation-service.json")
# For cloud deployment, set GOOGLE_APPLICATION_CREDENTIALS environment variable
# or use Cloud Run service account (no file needed)
SALES_EMAIL = os.getenv("SALES_EMAIL", "sales@zemzen.org")  # Email to send from
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

# Test mode configuration
TEST_MODE = os.getenv("TEST", "false").lower() == "true"

# UI service configuration
UI_SERVICE_ENABLED = os.getenv("UI_SERVICE_ENABLED", "true").lower() == "true"

# OpenRouter configuration (for OpenAI/Anthropic via OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
ANTHROPIC_API_BASE = os.getenv("ANTHROPIC_API_BASE", "https://openrouter.ai/api/v1")