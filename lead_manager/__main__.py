#!/usr/bin/env python3
"""Lead Manager service - tries ADK first, falls back to simple version"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Try to run ADK version, fall back to simple version if dependencies missing"""
    try:
        # Try to import ADK dependencies
        from a2a.server.apps import A2AStarletteApplication
        from google.adk.agents import BaseAgent
        
        # If imports succeed, run the full ADK version
        logger.info("ADK dependencies found, starting full A2A server...")
        from .adk_main import main as adk_main
        adk_main()
        
    except ImportError as e:
        logger.warning(f"ADK dependencies not found ({e}), falling back to simple version...")
        from .simple_main import main as simple_main
        simple_main()

if __name__ == "__main__":
    main()