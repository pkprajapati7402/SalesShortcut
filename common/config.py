# common/config.py
"""
Central configuration file for SalesShortcut application.

Provides port configurations and default parameters for all agents and services.
"""

# --- Agent Port Configurations ---
DEFAULT_LEAD_FINDER_PORT: int = 8081
DEFAULT_LEAD_MANAGER_PORT: int = 8082
DEFAULT_SDR_PORT: int = 8084

# --- UI Client Configuration ---
UI_CLIENT_SERVICE_NAME: int = 8000

# --- Human Input Service Configuration ---
DEFAULT_HUMAN_INPUT_PORT: int = 8000

# --- Agent URL Configurations ---
DEFAULT_LEAD_FINDER_URL: str = f"http://127.0.0.1:{DEFAULT_LEAD_FINDER_PORT}"
DEFAULT_LEAD_MANAGER_URL: str = f"http://127.0.0.1:{DEFAULT_LEAD_MANAGER_PORT}"
DEFAULT_SDR_URL: str = f"http://127.0.0.1:{DEFAULT_SDR_PORT}"

# --- UI Client URL Configuration ---
DEFAULT_UI_CLIENT_URL: str = f"http://127.0.0.1:{UI_CLIENT_SERVICE_NAME}"

# --- Human Input Service URL Configuration ---
DEFAULT_HUMAN_INPUT_URL: str = f"http://127.0.0.1:{DEFAULT_HUMAN_INPUT_PORT}"

# --- Agent Default Parameters ---
# Lead Finder
DEFAULT_LEAD_FINDER_ARTIFACT_NAME: str = "lead_results"

# Lead Manager
DEFAULT_LEAD_MANAGER_ARTIFACT_NAME: str = "lead_management_decision"

# SDR
DEFAULT_SDR_ARTIFACT_NAME: str = "sdr_decision"

