#!/usr/bin/env python3
import os
import re
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict
from dotenv import load_dotenv
import time as import_time  # Import time module for timestamps

from helpers.read_write import read_file, write_file
from communication.code_convert import convert_with_llm
from prompt.conversion_rating import get_verify_conversion_quality_prompt

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


def rate_conversion_quality(
    react_code: str, controller_code: str, template_code: str, component_name: str
) -> Optional[int]:
    """
    Rate the quality of the Angular to React conversion on a scale of 1-10.

    Args:
        react_code: React component code
        controller_code: Angular controller code
        template_code: Angular template code
        component_name: Name of the React component

    Returns:
        Rating from 1-10, with 10 being perfect conversion, or None if rating failed
    """
    try:
        # Create prompt for LLM to rate the conversion
        rating_prompt = get_verify_conversion_quality_prompt(
            component_name, controller_code, template_code, react_code
        )

        # Call LLM to rate the conversion
        rating_response = convert_with_llm(rating_prompt)

        # Parse the rating - handle potential issues
        if not rating_response:
            logger.warning(f"No rating received for {component_name}, setting to null")
            return None

        # Extract just the number from the response
        rating_text = rating_response.strip()
        # Remove any non-numeric characters
        rating_text = "".join(filter(str.isdigit, rating_text))

        if not rating_text:
            logger.warning(
                f"Could not parse rating for {component_name}, setting to null"
            )
            return None

        # Convert to integer
        rating = int(rating_text)

        # Ensure the rating is within bounds
        if rating < 1:
            rating = 1
        elif rating > 10:
            rating = 10

        logger.info(f"Conversion quality for {component_name} rated as {rating}/10")
        return rating

    except Exception as e:
        logger.error(f"Error rating conversion quality: {str(e)}")
        return None  # Return None instead of default rating on error


def rate_converted_route(route: Dict) -> bool:
    """
    Rate the quality of a converted React component by comparing with original Angular code.
    The function adds a conversion_rating attribute to the route object.

    Only attempts to get a new rating when:
    - No existing rating OR rating <= 8
    - AND rating_attempts < 3

    Args:
        route: The complete route object containing path, controller, templateUrl, etc.

    Returns:
        bool: True if rating was successful or skipped appropriately, False otherwise
    """
    try:
        route_path = route.get("path", "")
        component_name = _route_to_component_name(route.get("url", ""))

        # Check existing rating and attempt count
        existing_rating = route.get("conversion_rating")
        rating_attempts = route.get("rating_attempts", 0)

        # Determine if we should get a new rating
        should_rate = False

        # If no rating or rating <= 8, and we've made fewer than 3 attempts
        if (existing_rating is None or existing_rating <= 8) and rating_attempts < 3:
            should_rate = True

        if not should_rate:
            if existing_rating is not None:
                logger.info(
                    f"Skipping rating for route {route_path}: Rating already {existing_rating}/10 with {rating_attempts} attempts"
                )
            else:
                logger.info(
                    f"Skipping rating for route {route_path}: Already attempted {rating_attempts} times"
                )
            return True

        logger.info(
            f"Rating conversion quality for route: {route_path}, component: {component_name} (Attempt {rating_attempts + 1})"
        )

        if not route_path:
            logger.error("Route path is missing in the route object")
            return False

        # Get paths
        react_component_path = (
            destination_path / "src" / "app" / route_path / "page.jsx"
        )

        # Load the JSON report to get controller and template information
        with open(json_report_path, "r") as file:
            data = json.load(file)

        # Get controller and template paths directly from the route object
        controller_name = route.get("controller", "")
        template_url = route.get("templateUrl", "")
        controllers = data.get("controllers", {})

        controller_path = source_path / controllers.get(controller_name, "")
        template_path = source_path / "app" / template_url

        # Read the files
        react_code = read_file(str(react_component_path))
        controller_code = read_file(controller_path) if controller_path else ""
        template_code = read_file(template_path) if template_path else ""

        if not react_code:
            logger.error(f"Could not read React component: {react_component_path}")
            return False

        # Rate the conversion quality
        conversion_rating = rate_conversion_quality(
            react_code, controller_code, template_code, component_name
        )

        # Increment the rating attempts counter
        route["rating_attempts"] = rating_attempts + 1

        # Store the rating in the route object if we got a result
        if conversion_rating is not None:
            route["conversion_rating"] = conversion_rating
            logger.info(
                f"Successfully rated component {component_name}: {conversion_rating}/10 (Attempt {route['rating_attempts']})"
            )
        else:
            logger.warning(
                f"Failed to get rating for component {component_name} (Attempt {route['rating_attempts']})"
            )

        return True

    except Exception as e:
        logger.error(f"Error rating route conversion: {str(e)}")
        return False


def _route_to_component_name(url: str) -> str:
    """
    Convert a route URL to a proper React component name

    Args:
        url: Route URL (e.g., '/users/:id/profile')

    Returns:
        Component name in PascalCase (e.g., 'UserProfile')
    """
    # Remove parameters (anything with colon)
    url = re.sub(r":[^/]+", "", url)

    # Remove special characters, split by delimiters
    parts = re.split(r"[^a-zA-Z0-9]", url)

    # Filter out empty parts and convert to PascalCase
    component_name = "".join(part.capitalize() for part in parts if part)

    # If the component name is empty, use a default name
    if not component_name:
        component_name = "Home"

    # Add 'Page' suffix if it doesn't end with a common component suffix
    if not any(
        component_name.endswith(suffix)
        for suffix in ["Page", "View", "Component", "Screen"]
    ):
        component_name += "Page"

    return component_name


def rate_all_converted_routes() -> None:
    """
    Process all routes in the JSON report and rate each converted React component.
    This function loads the routes from the JSON report, filters relevant ones,
    rates each route, and updates the JSON report with the ratings.

    Returns:
        None
    """
    try:
        logger.info("Starting rating of all converted routes...")

        # Load the JSON report to get routes information
        try:
            with open(json_report_path, "r") as file:
                data = json.load(file)
        except Exception as e:
            logger.error(f"Error loading JSON report from {json_report_path}: {str(e)}")
            return

        # Initialize ratings_summary in the data
        data["ratings_summary"] = {
            "total_rated": 0,
            "rating_1_3": 0,  # Poor conversion
            "rating_4_6": 0,  # Acceptable conversion
            "rating_7_8": 0,  # Good conversion
            "rating_9_10": 0,  # Excellent conversion
            "rating_null": 0,  # Failed to rate
            "average_rating": None,
            "max_attempts_reached": 0,  # Routes with 3+ attempts
            "high_rated_routes": 0,  # Routes with rating > 8
            "total_attempts": 0,  # Total rating attempts made
        }

        # Get all routes
        routes = data.get("routes", [])
        logger.info(f"Found {len(routes)} total routes in the JSON report")

        # Filter routes that have already been converted (have a path property)
        converted_routes = [r for r in routes if r.get("path") and r.get("url")]
        logger.info(f"Found {len(converted_routes)} converted routes to rate")

        # Count routes that don't need rating (rating > 8 or attempts >= 3)
        skipped_high_rating = 0
        skipped_max_attempts = 0

        # Analyze existing attempts and ratings
        for route in converted_routes:
            rating = route.get("conversion_rating")
            attempts = route.get("rating_attempts", 0)

            # Count routes with high ratings
            if rating is not None and rating > 8:
                skipped_high_rating += 1

            # Count routes with max attempts reached
            if attempts >= 3:
                skipped_max_attempts += 1

        logger.info(
            f"Found {skipped_high_rating} routes with rating > 8 (will be skipped)"
        )
        logger.info(
            f"Found {skipped_max_attempts} routes with 3+ rating attempts (will be skipped)"
        )

        # Track success/failure stats
        successful_ratings = 0
        failed_ratings = 0
        skipped_ratings = 0
        sum_ratings = 0
        total_attempts = 0

        # Process each route
        for index, route in enumerate(converted_routes, 1):
            route_path = route.get("path", "")
            rating = route.get("conversion_rating")
            attempts = route.get("rating_attempts", 0)

            should_process = True
            # Skip routes with good ratings or max attempts
            if (rating is not None and rating > 8) or attempts >= 3:
                logger.info(
                    f"Skipping route {index}/{len(converted_routes)}: {route_path} (Rating: {rating}, Attempts: {attempts})"
                )
                skipped_ratings += 1
                should_process = False

            if should_process:
                logger.info(
                    f"Processing route {index}/{len(converted_routes)}: {route_path} (Current rating: {rating}, Attempts: {attempts})"
                )

                # Rate the route
                result = rate_converted_route(route)

                if result:
                    # Check if we actually made a rating attempt or skipped
                    if route.get("rating_attempts", 0) > attempts:
                        successful_ratings += 1
                        total_attempts += 1
                    else:
                        skipped_ratings += 1

                    # Update ratings statistics
                    rating = route.get("conversion_rating")
                    if rating is not None:
                        sum_ratings += rating
                        # Categorize the rating
                        if 1 <= rating <= 3:
                            data["ratings_summary"]["rating_1_3"] += 1
                        elif 4 <= rating <= 6:
                            data["ratings_summary"]["rating_4_6"] += 1
                        elif 7 <= rating <= 8:
                            data["ratings_summary"]["rating_7_8"] += 1
                        elif 9 <= rating <= 10:
                            data["ratings_summary"]["rating_9_10"] += 1
                            data["ratings_summary"]["high_rated_routes"] += 1
                        data["ratings_summary"]["total_rated"] += 1
                else:
                    failed_ratings += 1
                    data["ratings_summary"]["rating_null"] += 1

        # Update total attempts in the summary
        data["ratings_summary"]["total_attempts"] = total_attempts
        data["ratings_summary"]["max_attempts_reached"] = skipped_max_attempts
        data["ratings_summary"]["high_rated_routes"] = skipped_high_rating

        # Calculate average rating
        if data["ratings_summary"]["total_rated"] > 0:
            data["ratings_summary"]["average_rating"] = round(
                sum_ratings / data["ratings_summary"]["total_rated"], 2
            )

        # Write the updated data back to the JSON file with the ratings
        try:
            with open(json_report_path, "w") as json_file:
                json.dump(data, json_file, indent=2)
            logger.info(
                f"Successfully updated JSON report with ratings at {json_report_path}"
            )
        except Exception as e:
            logger.error(f"Error writing updated data to JSON: {str(e)}")

        # Log summary statistics
        logger.info("=== Rating Summary ===")
        logger.info(f"Total routes processed: {len(converted_routes)}")
        logger.info(f"Successful ratings: {successful_ratings}")
        logger.info(f"Skipped ratings: {skipped_ratings}")
        logger.info(f"Failed ratings: {failed_ratings}")
        logger.info(f"Total rating attempts: {total_attempts}")
        if data["ratings_summary"]["total_rated"] > 0:
            logger.info(
                f"Average rating: {data['ratings_summary']['average_rating']}/10"
            )
            logger.info(f"Poor (1-3): {data['ratings_summary']['rating_1_3']}")
            logger.info(f"Acceptable (4-6): {data['ratings_summary']['rating_4_6']}")
            logger.info(f"Good (7-8): {data['ratings_summary']['rating_7_8']}")
            logger.info(f"Excellent (9-10): {data['ratings_summary']['rating_9_10']}")
        logger.info(
            f"Routes with rating > 8: {data['ratings_summary']['high_rated_routes']}"
        )
        logger.info(
            f"Routes with max attempts reached: {data['ratings_summary']['max_attempts_reached']}"
        )
        logger.info("======================")

    except Exception as e:
        logger.error(f"Error in rate_all_converted_routes: {str(e)}")


if __name__ == "__main__":
    # When run directly, rate all routes
    rate_all_converted_routes()
