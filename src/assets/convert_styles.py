#!/usr/bin/env python3
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from communication.code_convert import convert_with_llm
from helpers.read_write import read_file, write_file
from prompt.code_conversion import PROMPT_FOR_CSS_CONVERSION

load_dotenv()

DESTINATION_PATH = os.getenv("DESTINATION_PATH", "")
destination_path = Path(DESTINATION_PATH)

STYLES_DIR = destination_path / "src" / "styles"
# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def find_mixin_files(styles_path) -> List[str]:
    """
    Find all files with 'mixin' in their name within a directory structure.

    Args:
        styles_dir_path: Path to the styles directory

    Returns:
        List of file paths containing 'mixin' in their name
    """
    mixin_files = []

    if not styles_path.exists() or not styles_path.is_dir():
        logger.error(
            f"Styles directory does not exist or is not a directory: {STYLES_DIR}"
        )
        return mixin_files

    logger.info(f"Searching for mixin files in: {STYLES_DIR}")

    # Walk through all directories and files
    for root, _, files in os.walk(styles_path):
        for file in files:
            # Check if 'mixin' is in the filename
            if "mixin" in file.lower():
                file_path = Path(root) / file
                mixin_files.append(str(file_path))
                logger.info(f"Found mixin file: {file_path}")

    logger.info(f"Found {len(mixin_files)} mixin files")
    return mixin_files


def modernize_css_files(styles_dir_path: str, mixin_file: str) -> Dict[str, bool]:
    """
    Convert old SASS/CSS files to modern CSS using an LLM.
    Handles mixins and functions while preserving class/id selectors and styles.

    Args:
        styles_dir_path: Path to the styles directory

    Returns:
        Dictionary mapping file paths to success status
    """
    results = {}
    styles_path = Path(styles_dir_path)

    if not styles_path.exists() or not styles_path.is_dir():
        logger.error(
            f"Styles directory does not exist or is not a directory: {styles_dir_path}"
        )
        return results

    logger.info(f"Modernizing CSS files in: {styles_dir_path}")

    # Get list of CSS/SCSS file extensions to process
    css_extensions = [".scss"]

    # Read the mixin file
    mixin_file_content = read_file(mixin_file)

    # Walk through all directories and files
    for root, _, files in os.walk(styles_path):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in css_extensions:
                results[str(file_path)] = modernize_css_file(
                    file_path, mixin_file_content
                )

    # Log summary
    success_count = sum(1 for status in results.values() if status)
    failure_count = len(results) - success_count

    logger.info(f"CSS Modernization Summary:")
    logger.info(f"Total files processed: {len(results)}")
    logger.info(f"Successfully modernized: {success_count}")
    logger.info(f"Failed to modernize: {failure_count}")

    return results


def modernize_css_file(file_path: Path, mixin_file_content: str) -> bool:
    """
    Modernize a single CSS/SCSS file using an LLM.

    Args:
        file_path: Path to the CSS/SCSS file

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Modernizing file: {file_path}")

        # Read the file content
        css_content = read_file(str(file_path))
        if not css_content:
            logger.warning(f"Could not read file or file is empty: {file_path}")
            return False

        # Determine the file type for better LLM guidance
        file_type = file_path.suffix.lower()

        # Generate a prompt for the LLM
        prompt = PROMPT_FOR_CSS_CONVERSION(file_type, css_content, mixin_file_content)

        # Convert with LLM
        modernized_css = convert_with_llm(prompt)

        output_path = file_path.with_suffix(".css")

        # Write the modernized CSS back to the file
        if write_file(str(output_path), modernized_css):
            logger.info(f"Successfully modernized and saved: {output_path}")
            return True
        else:
            logger.error(f"Failed to write modernized CSS to: {output_path}")
            return False

    except Exception as e:
        logger.error(f"Error modernizing CSS file {file_path}: {str(e)}")
        return False


def convert_styles_to_css():
    """
    Main function for testing
    """

    styles_dir = Path(STYLES_DIR)

    # Find mixin files
    mixin_files = find_mixin_files(styles_dir)
    print(f"Found mixin files: {mixin_files}")

    # Modernize CSS files
    results = modernize_css_files(styles_dir, mixin_files[0])
    print(f"Modernization results: {results}")
