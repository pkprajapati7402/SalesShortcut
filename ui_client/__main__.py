"""
Entry point for the UI Client module.

This module can be run directly using:
    python -m ui_client

Or with custom port:
    python -m ui_client --port 8000
"""

import argparse
import logging
import os
import sys
import uvicorn

# Import the main app and configuration
from ui_client.main import app
import common.config as config

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )

def main():
    """Main entry point for the UI Client service."""
    parser = argparse.ArgumentParser(
        description="SalesShortcut UI Client - Lead Generation Dashboard"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=config.UI_CLIENT_SERVICE_NAME,
        help=f"Port to run the UI Client on (default: {config.UI_CLIENT_SERVICE_NAME})"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the UI Client to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: INFO)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development (default: False)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger("UIClient")

    # Validate environment
    google_api_key = os.environ.get("GOOGLE_API_KEY")

    # Print startup information
    logger.info("=" * 60)
    logger.info("SalesShortcut UI Client - Lead Generation Dashboard")
    logger.info("=" * 60)
    logger.info(f"Starting UI Client on {args.host}:{args.port}")
    logger.info(f"Log level: {args.log_level}")
    logger.info(f"Reload mode: {args.reload}")
    logger.info(f"Workers: {args.workers}")
    logger.info("")
    logger.info("Required Services (ensure they are running):")
    logger.info(f"  Lead Finder:        {os.environ.get('LEAD_FINDER_SERVICE_URL', config.DEFAULT_LEAD_FINDER_URL)}")
    logger.info(f"  SDR Agent:          {os.environ.get('SDR_SERVICE_URL', config.DEFAULT_SDR_URL)}")
    logger.info(f"  Lead Manager:       {os.environ.get('LEAD_MANAGER_SERVICE_URL', config.DEFAULT_LEAD_MANAGER_URL)}")
    logger.info("")
    logger.info("Environment Variables:")
    logger.info(f"  GOOGLE_API_KEY: {'✓ Set' if google_api_key else '✗ Not set'}")
    logger.info("")
    logger.info(f"Dashboard will be available at: http://{args.host}:{args.port}")
    logger.info("=" * 60)

    # Configure uvicorn
    uvicorn_config = {
        "app": "ui_client.main:app",
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level.lower(),
        "reload": args.reload,
        "workers": args.workers if not args.reload else 1,  # Workers > 1 incompatible with reload
        "access_log": True,
        "use_colors": True,
    }

    # Remove workers if reload is enabled (they're incompatible)
    if args.reload and args.workers > 1:
        logger.warning("Reload mode is incompatible with multiple workers. Setting workers=1")
        uvicorn_config["workers"] = 1

    try:
        # Start the server
        uvicorn.run(**uvicorn_config)
    except KeyboardInterrupt:
        logger.info("Shutting down UI Client...")
    except Exception as e:
        logger.error(f"Failed to start UI Client: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()