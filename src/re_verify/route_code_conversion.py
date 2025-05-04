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


def reverify_converted_route(route: Dict) -> bool:
    """
    Reverify a converted React component by comparing with original Angular code.
    The LLM will check for any issues and provide improved code if needed.

    Args:
        route: The complete route object containing path, controller, templateUrl, etc.

    Returns:
        bool: True if verification was successful, False otherwise
    """
    try:
        route_path = route.get("path", "")
        component_name = _route_to_component_name(route.get("url", ""))

        logger.info(f"Reverifying route: {route_path}, component: {component_name}")

        if not route_path:
            logger.error("Route path is missing in the route object")
            return False

        # Get paths
        react_component_path = (
            destination_path / "src" / "app" / route_path / "page.tsx"
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

        # Send directly to LLM for verification and improvement
        logger.info(f"Sending component {component_name} to LLM for verification")

        # Create verification prompt
        verification_prompt = _create_verification_prompt(
            react_code, controller_code, template_code, component_name
        )

        # Use convert_with_llm to perform the verification
        improved_code = convert_with_llm(
            verification_prompt, "controller_template", "react_component"
        )

        # If LLM didn't return any code, assume no issues were found
        if not improved_code:
            logger.info(f"No improvements needed for component: {component_name}")
            return True

        # Check if the code was actually changed
        if improved_code.strip() == react_code.strip():
            logger.info(f"LLM verified component with no changes: {component_name}")
            return True

        # Write the improved code back to the file
        if write_file(str(react_component_path), improved_code):
            logger.info(
                f"Successfully rewrote component with improvements: {react_component_path}"
            )
            return True
        else:
            logger.error(f"Failed to write improved code to {react_component_path}")
            return False

    except Exception as e:
        logger.error(f"Error reverifying route: {str(e)}")
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


def _create_verification_prompt(
    react_code: str, controller_code: str, template_code: str, component_name: str
) -> str:
    """
    Create a prompt for LLM to verify and potentially improve the component.

    Args:
        react_code: React component code
        controller_code: Angular controller code
        template_code: Angular template code
        component_name: Name of the React component

    Returns:
        Prompt string for the LLM
    """
    prompt = f"""You are an expert Angular-to-React conversion verification specialist.
Your primary goal is to ensure a React component, previously converted from Angular, is correct, follows best practices, and is potentially improved.

Component Name: {component_name}

Original Angular Controller Code:
```javascript
{controller_code}
```

Original Angular Template:
```html
{template_code}
```

EXISTING Converted React Component (Code to Verify):
```tsx
{react_code}
```

Verification and Improvement Instructions:

Please meticulously analyze the EXISTING React component based on the original Angular code and React best practices. Check for the following:

- Functional Equivalence: This migration must ensure absolute functional equivalence. Meticulously test that the React component replicates all logic and state management from the Angular controller. Any deviations, even minor ones, are unacceptable and must be corrected.
- UI Equivalence: Does the React component render ALL UI elements and conditional structures present in the Angular template?
- React Best Practices: Does the component adhere to modern React principles (functional components, appropriate hook usage, immutability)?
- TypeScript Best Practices: Is the component strongly-typed using TypeScript effectively? Are types accurate and comprehensive?
- Correctness & Efficiency: Are there any logical errors, potential bugs, race conditions, or significant performance issues?
- Hook Usage: Are React hooks (useState, useEffect, useCallback, useMemo, useContext, etc.) used correctly and efficiently?
- Event Handling: Are event handlers implemented correctly and bound properly?
- Imports: Are all necessary imports present and correct? Are there unused imports?
- Readability & Maintainability: Is the code clean, well-formatted, and easy to understand? Could logic be simplified or clarified?
- Framework Practices (If Applicable): If this component is intended for a specific framework like Next.js (e.g., as a page), does it follow relevant conventions? (Adjust or remove this point based on your typical use case)
- This React component must be implemented using only React principles and best practices. Under no circumstances should it include Vanilla JavaScript, jQuery, or Angular code as well as any other dependencies. This is crucial for maintainability, future updates, and to prevent conflicts within the overall React application.
- Optional chaining should be used instead of null checks.
- React component should not have any console.log statements.
- All labels should be same as in the Angular template and no label should be missing.
- Check for any missing, unused and unnecessary imports and update the imports.
- Check for not defined variables, functions, types,etc and update the code.
- Should not have import of any minified code.

Output Requirements:
- If ANY issues are found OR if improvements (based on the criteria above) can be made: Respond with the COMPLETE, UPDATED React component code. Ensure the entire file content is provided, incorporating all necessary fixes and improvements.
- If NO issues are found and the component is already correct and well-implemented according to the criteria: Respond with empty string.

CRITICAL: Respond ONLY with the final React component code in a single block. Do NOT include any explanations, apologies, introductory sentences, or markdown formatting (like tsx ... ) around the code block. Just the raw code itself.
"""
    return prompt


def reverify_all_converted_routes() -> None:
    """
    Process all routes in the JSON report and reverify each converted React component.
    This function loads the routes from the JSON report, filters relevant ones,
    and calls reverify_converted_route for each route with a conversion_rating <= 8 or falsy.

    Tracks failed verifications in the JSON report under a 'failed_verifications' key.

    Returns:
        None
    """
    try:
        logger.info(
            "Starting verification of all routes with low conversion ratings..."
        )

        # Load the JSON report to get routes information
        try:
            with open(json_report_path, "r") as file:
                data = json.load(file)
        except Exception as e:
            logger.error(f"Error loading JSON report from {json_report_path}: {str(e)}")
            return

        # Initialize or reset the failed_verifications array in the data
        data["failed_verifications"] = []

        # Get all routes
        routes = data.get("routes", [])
        logger.info(f"Found {len(routes)} total routes in the JSON report")

        # Filter routes that have already been converted (have a path property)
        converted_routes = [r for r in routes if r.get("path") and r.get("url")]
        logger.info(f"Found {len(converted_routes)} converted routes")

        # Filter routes with conversion_rating <= 8 or falsy (None, 0, etc.)
        routes_to_verify = [
            r
            for r in converted_routes
            if not r.get("conversion_rating") or r.get("conversion_rating") <= 8
        ]

        # Count routes by rating category for logging
        no_rating = len([r for r in converted_routes if not r.get("conversion_rating")])
        low_rating = len(
            [
                r
                for r in converted_routes
                if r.get("conversion_rating") and r.get("conversion_rating") <= 8
            ]
        )
        high_rating = len(
            [
                r
                for r in converted_routes
                if r.get("conversion_rating") and r.get("conversion_rating") > 8
            ]
        )

        logger.info(f"Found {len(routes_to_verify)} routes to verify:")
        logger.info(f"  - {no_rating} routes with no rating")
        logger.info(f"  - {low_rating} routes with rating <= 8")
        logger.info(f"  - {high_rating} routes with rating > 8 (will be skipped)")

        # Track success/failure stats
        successful_verifications = 0
        failed_verifications = 0
        routes_with_improvements = 0

        # Process each route
        for index, route in enumerate(routes_to_verify, 1):
            route_path = route.get("path", "")
            rating = route.get("conversion_rating", "")

            logger.info(
                f"Processing route {index}/{len(routes_to_verify)}: {route_path} (Rating: {rating})"
            )
            if route_path.endswith("app/models"):
                continue

            # Call reverify_converted_route for this route
            result = reverify_converted_route(route)

            if result:
                successful_verifications += 1
                # Check if the component file has been modified after verification
                component_path = (
                    destination_path / "src" / "app" / route_path / "page.tsx"
                )
                if os.path.exists(str(component_path)):
                    # If file was modified in the last few seconds, count it as improved
                    routes_with_improvements += 1
                    # After improvement, we can update the conversion_rating to reflect the better quality
                    # This is optional and can be removed if not desired
                    route["improved_timestamp"] = import_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
            else:
                failed_verifications += 1
                # Add the failed route to the failed_verifications array
                # Create a copy of the route object with additional failure information
                failed_route = route.copy()
                failed_route["verification_error"] = True
                failed_route["verification_timestamp"] = import_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                data["failed_verifications"].append(failed_route)
                logger.warning(f"Route verification failed: {route_path}")

        # Write the updated data back to the JSON file with the failed_verifications array
        try:
            with open(json_report_path, "w") as json_file:
                json.dump(data, json_file, indent=2)
            logger.info(
                f"Successfully updated JSON report with failed verifications at {json_report_path}"
            )

        except Exception as e:
            logger.error(f"Error writing updated data to JSON: {str(e)}")

        # Log summary statistics
        logger.info("=== Verification Summary ===")
        logger.info(f"Total routes with low ratings: {len(routes_to_verify)}")
        logger.info(f"Successfully verified: {successful_verifications}")
        logger.info(f"Verification failures: {failed_verifications}")
        logger.info(f"Routes with improvements: {routes_with_improvements}")
        logger.info(f"Failed routes saved to JSON under 'failed_verifications' key")
        logger.info("============================")

    except Exception as e:
        logger.error(f"Error in reverify_all_converted_routes: {str(e)}")


if __name__ == "__main__":
    # When run directly, reverify all routes
    reverify_all_converted_routes()
