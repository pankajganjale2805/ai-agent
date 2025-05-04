#!/usr/bin/env python3
import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

from helpers.read_write import read_file, write_file
from prompt.code_verification import PROMPT_FOR_HTML_STRUCTURE_VERIFICATION

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


def verify_html_structure(
    route: Dict, controller_path: Path, template_path: Path, react_component_path: Path
) -> bool:
    """
    Verify the HTML structure of a converted React component against the original Angular template.
    The function will check for missing elements, unnecessary elements, and other structural issues.

    Args:
        route: The complete route object containing path, controller, templateUrl, etc.

    Returns:
        bool: True if verification was successful and component was updated if needed, False otherwise
    """
    try:
        route_path = route.get("path", "")
        # Load the files
        react_code = read_file(str(react_component_path))
        controller_code = read_file(str(controller_path))
        template_code = read_file(str(template_path))

        if not all([react_code, template_code]):
            logger.warning(f"Could not read necessary files for route: {route_path}")
            return False

        # Call LLM to verify the HTML structure
        updated_code = verify_html_with_llm(
            controller_code=controller_code,
            template_code=template_code,
            react_code=react_code,
        )

        # If no updated code is returned or it's the same as the original, no changes needed
        if not updated_code or len(updated_code.strip()) == 0:
            logger.info(f"No HTML structure issues found in component: {route_path}")
            return False

        # Write the updated code back to the file
        if write_file(str(react_component_path), updated_code):
            logger.info(f"Updated HTML structure in component: {route_path}")
            return True
        else:
            logger.error(f"Failed to write updated component: {route_path}")
            return False

    except Exception as e:
        logger.error(
            f"Error verifying HTML structure for route {route.get('path', '')}: {str(e)}"
        )
        return False


def verify_html_with_llm(
    controller_code: str,
    template_code: str,
    react_code: str,
) -> Optional[str]:
    """
    Use LLM to verify and potentially update the HTML structure of a React component.

    Args:
        react_code: The React component code
        controller_code: The Angular controller code
        template_code: The Angular template code
        component_name: The name of the component

    Returns:
        Optional[str]: Updated React component code if changes were needed, None otherwise
    """
    try:
        # Create a prompt for the LLM
        prompt = PROMPT_FOR_HTML_STRUCTURE_VERIFICATION(
            controller_code, template_code, react_code
        )

        # Call the LLM to verify and potentially update the HTML structure
        updated_code = convert_with_llm(prompt)

        return updated_code

    except Exception as e:
        logger.error(f"Error in LLM HTML structure verification: {str(e)}")
        return None
