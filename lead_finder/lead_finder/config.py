"""
Configuration for the Lead Finder Agent.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debug logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Config loading - GOOGLE_MAPS_API_KEY from env: {bool(os.getenv('GOOGLE_MAPS_API_KEY'))}")
logger.info(f"Config loading - GOOGLE_MAPS_API_KEY length: {len(os.getenv('GOOGLE_MAPS_API_KEY', ''))}")

# Model configuration
# Using gemini-2.0-flash-lite for cost-effectiveness (free tier available)
MODEL = os.getenv("MODEL", "gemini-2.0-flash-lite")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
TOP_P = float(os.getenv("TOP_P", "0.95"))
TOP_K = int(os.getenv("TOP_K", "40"))

# BigQuery configuration
PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
DATASET_ID = os.getenv("DATASET_ID", "lead_finder_data")
TABLE_ID = os.getenv("TABLE_ID", "business_leads")

# Google Maps API configuration
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# OpenRouter configuration (for OpenAI/Anthropic via OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
ANTHROPIC_API_BASE = os.getenv("ANTHROPIC_API_BASE", "https://openrouter.ai/api/v1")
