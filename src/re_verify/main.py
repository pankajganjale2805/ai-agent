#!/usr/bin/env python3
import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

from re_verify.verify_html_structure import verify_html_structure

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

SOURCE_PATH = os.getenv("SOURCE_PATH", "")
DESTINATION_PATH = os.getenv("DESTINATION_PATH", "")
JSON_REPORT_PATH = os.getenv("JSON_REPORT_PATH", "")
source_path = Path(SOURCE_PATH)
destination_path = Path(DESTINATION_PATH)
json_report_path = Path(JSON_REPORT_PATH)


def iterate_through_routes() -> None:
    """
    Process all routes in the JSON report and verify the HTML structure for each converted component.

    Returns:
        None
    """
    try:
        logger.info("Starting HTML structure verification for all routes...")

        # Load the JSON report
        try:
            with open(json_report_path, "r") as file:
                data = json.load(file)
        except Exception as e:
            logger.error(f"Error loading JSON report from {json_report_path}: {str(e)}")
            return

        # Get all routes
        routes = data.get("routes", [])
        logger.info(f"Found {len(routes)} total routes in the JSON report")

        # Filter routes that have already been converted
        converted_routes = [r for r in routes if r.get("path") and r.get("url")]
        logger.info(f"Found {len(converted_routes)} converted routes to verify")

        # Track statistics
        successful_verifications = 0
        failed_verifications = 0
        updated_components = 0

        # Process each route
        for index, route in enumerate(converted_routes, 1):
            if not route["url"] or not route["name"].startswith("app.models"):
                continue
            route_path = route.get("path", "")

            logger.info(
                f"Processing route {index}/{len(converted_routes)}: {route_path}"
            )

            # Skip routes that were already verified if desired
            if route.get("html_structure_verified", False):
                logger.info(f"Skipping already verified route: {route_path}")
                successful_verifications += 1
                continue

            # Verify the HTML structure
            result = verify_html_structure(route)

            if result:
                successful_verifications += 1
                if route.get("html_structure_updated", False):
                    updated_components += 1
            else:
                failed_verifications += 1

        # Update the JSON report
        try:
            with open(json_report_path, "w") as json_file:
                json.dump(data, json_file, indent=2)
            logger.info(
                f"Successfully updated JSON report with HTML verification results at {json_report_path}"
            )
        except Exception as e:
            logger.error(f"Error writing updated data to JSON: {str(e)}")

        # Log summary statistics
        logger.info("=== HTML Structure Verification Summary ===")
        logger.info(f"Total routes processed: {len(converted_routes)}")
        logger.info(f"Successfully verified: {successful_verifications}")
        logger.info(f"Verification failures: {failed_verifications}")
        logger.info(f"Components updated: {updated_components}")
        logger.info("===========================================")

    except Exception as e:
        logger.error(f"Error in verify_html_for_all_routes: {str(e)}")
