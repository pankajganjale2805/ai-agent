#!/usr/bin/env python3
import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from dotenv import load_dotenv

from helpers.read_write import read_file, write_file
from communication.code_convert import convert_with_llm
from setup.next_project import setup_next_project
from routes.create_routes import generate_next_pages
from re_verify.route_code_conversion import reverify_all_converted_routes
from conversion_rating.main import rate_all_converted_routes
from prompt.code_verification import PROMPT_FOR_HTML_STRUCTURE_VERIFICATION
from re_verify.verify_styles_conversion import verify_converted_styles
from re_verify.verify_html_structure import verify_html_structure
from re_verify.verify_logic import verify_logic
from re_verify.verify_api_calls import verify_api_calls

from assets.copy_assets_styles import copy_assets_and_styles
from assets.convert_styles import convert_styles_to_css

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
    Simply iterate through routes in the JSON report and log them.

    Returns:
        None
    """
    try:
        logger.info("Starting route iteration...")

        # Load the JSON report
        try:
            with open(json_report_path, "r") as file:
                data = json.load(file)
        except Exception as e:
            logger.error(f"Error loading JSON report from {json_report_path}: {str(e)}")
            return

        # Get all routes
        routes = data.get("routes", [])
        controllers = data.get("controllers", {})
        logger.info(f"Found {len(routes)} total routes in the JSON report")

        # Simply iterate through each route
        for index, route in enumerate(routes):
            if not route.get("url") or not route.get("name", "").startswith(
                "app.models"
            ):
                continue

            # Extract necessary information from the route
            route_path = route.get("path", "")

            # Skip routes without a path
            if not route_path:
                logger.warning(f"Route missing path: {route}")
                continue

            # Check if the route has controller and templateUrl
            controller_name = route.get("controller")
            template_url = route.get("templateUrl")

            # For logic verification, we need the component path
            react_component_path = (
                destination_path / "src" / "app" / route_path / "page.jsx"
            )

            # Only attempt to get controller_path if controller_name exists and is in controllers
            controller_path = None
            if controller_name and controller_name in controllers:
                controller_path = source_path / controllers[controller_name]

            # Only attempt to get template_path if template_url exists
            template_path = None
            if template_url:
                template_path = source_path / "app" / template_url

            is_html_structure_updated = False
            if (
                not route.get("html_structure_verified")
                or route.get("html_structure_verified") == False
            ):
                try:
                    is_html_structure_updated = verify_html_structure(
                        route,
                        controller_path,
                        template_path,
                        react_component_path,
                    )

                    route["html_structure_verified"] = True
                    if is_html_structure_updated:
                        route["html_structure_updated"] = True

                    logger.info(
                        f"Route [{index+1}/{len(routes)}]: {route.get('path', '')} (URL: {route.get('url', '')}) - Updated HTML structure"
                    )
                except Exception as e:
                    logger.error(f"Error in verify_html_structure: {str(e)}")

            is_logic_updated = False
            if not route.get("logic_verified") or route.get("logic_verified") == False:
                try:
                    is_logic_updated = verify_logic(
                        route,
                        controller_path,
                        template_path,
                        react_component_path,
                    )

                    route["logic_verified"] = True
                    if is_logic_updated:
                        route["logic_updated"] = True

                    logger.info(
                        f"Route [{index+1}/{len(routes)}]: {route.get('path', '')} (URL: {route.get('url', '')}) - Updated logic"
                    )
                except Exception as e:
                    logger.error(f"Error in verify_logic: {str(e)}")

            is_api_calls_updated = False
            if (
                not route.get("api_calls_verified")
                or route.get("api_calls_verified") == False
            ):
                try:
                    is_api_calls_updated = verify_api_calls(
                        route,
                        controller_path,
                        template_path,
                        react_component_path,
                    )

                    route["api_calls_verified"] = True
                    if is_api_calls_updated:
                        route["api_calls_updated"] = True

                    logger.info(
                        f"Route [{index+1}/{len(routes)}]: {route.get('path', '')} (URL: {route.get('url', '')}) - Updated API calls"
                    )
                except Exception as e:
                    logger.error(f"Error in verify_api_calls: {str(e)}")

        # Save the updated JSON report
        with open(json_report_path, "w") as file:
            json.dump(data, file, indent=2)

    except Exception as e:
        logger.error(f"Error in iterate_through_routes: {str(e)}")


def main():
    setup_next_project()
    generate_next_pages()
    iterate_through_routes()
    copy_assets_and_styles()
    files = convert_styles_to_css()
    print(files)
    # # for i in range(3):
    # # rate_all_converted_routes()
    # # reverify_all_converted_routes()
    results, unconverted_files = verify_converted_styles()
    print("--------------------------------")
    print(results)
    print(unconverted_files)


if __name__ == "__main__":
    main()
