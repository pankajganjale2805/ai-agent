#!/usr/bin/env python3
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from communication.code_convert import convert_with_llm
from helpers.read_write import read_file, write_file
from prompt.code_verification import PROMPT_FOR_CSS_VERIFICATION

load_dotenv()

DESTINATION_PATH = os.getenv("DESTINATION_PATH", "")
destination_path = Path(DESTINATION_PATH)

STYLES_DIR = destination_path / "src" / "styles"
# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def find_scss_css_pairs(
    styles_dir_path: str,
) -> Tuple[List[Tuple[Path, Path]], List[Path]]:
    """
    Find pairs of .scss and .css files with matching names in the styles directory.
    Also find SCSS files without matching CSS files.

    Args:
        styles_dir_path: Path to the styles directory

    Returns:
        Tuple containing:
        - List of tuples containing (scss_file_path, css_file_path)
        - List of scss_file_paths that don't have matching CSS files
    """
    file_pairs = []
    unconverted_scss_files = []
    styles_path = Path(styles_dir_path)

    if not styles_path.exists() or not styles_path.is_dir():
        logger.error(
            f"Styles directory does not exist or is not a directory: {styles_dir_path}"
        )
        return file_pairs, unconverted_scss_files

    # Find all .scss files
    scss_files = []
    for root, _, files in os.walk(styles_path):
        for file in files:
            if file.endswith(".scss"):
                scss_path = Path(root) / file
                scss_files.append(scss_path)

    # Check if corresponding .css files exist
    for scss_path in scss_files:
        css_path = scss_path.with_suffix(".css")
        if css_path.exists():
            file_pairs.append((scss_path, css_path))
            logger.info(f"Found matching pair: {scss_path} -> {css_path}")
        else:
            unconverted_scss_files.append(scss_path)
            logger.info(f"Found unconverted SCSS file: {scss_path}")

    logger.info(f"Found {len(file_pairs)} scss/css file pairs")
    logger.info(f"Found {len(unconverted_scss_files)} unconverted SCSS files")
    return file_pairs, unconverted_scss_files


def verify_css_files(
    styles_dir_path: str, mixin_file: str
) -> Tuple[Dict[str, bool], List[str]]:
    """
    Verify converted CSS files against their original SCSS sources.
    Also identify SCSS files that don't have converted CSS versions.

    Args:
        styles_dir_path: Path to the styles directory
        mixin_file: Path to the mixin file

    Returns:
        Tuple containing:
        - Dictionary mapping file paths to verification status
        - List of SCSS file paths that don't have corresponding CSS files
    """
    results = {}
    styles_path = Path(styles_dir_path)

    if not styles_path.exists() or not styles_path.is_dir():
        logger.error(
            f"Styles directory does not exist or is not a directory: {styles_dir_path}"
        )
        return results, []

    logger.info(f"Verifying CSS files in: {styles_dir_path}")

    # Read the mixin file content
    mixin_file_content = read_file(mixin_file)
    if not mixin_file_content:
        logger.warning(f"Could not read mixin file or file is empty: {mixin_file}")
        return results, []

    # Find all scss/css file pairs and unconverted scss files
    file_pairs, unconverted_scss_files = find_scss_css_pairs(styles_dir_path)

    # Process each pair
    for scss_path, css_path in file_pairs:
        results[str(css_path)] = verify_css_file(
            scss_path, css_path, mixin_file_content
        )

    # Log summary
    success_count = sum(1 for status in results.values() if status)
    failure_count = len(results) - success_count

    logger.info(f"CSS Verification Summary:")
    logger.info(f"Total files verified: {len(results)}")
    logger.info(f"Successfully verified: {success_count}")
    logger.info(f"Verification failures: {failure_count}")
    logger.info(f"Unconverted SCSS files: {len(unconverted_scss_files)}")

    # Convert Path objects to strings for better compatibility
    unconverted_scss_paths = [str(path) for path in unconverted_scss_files]

    return results, unconverted_scss_paths


def verify_css_file(scss_path: Path, css_path: Path, mixin_file_content: str) -> bool:
    """
    Verify a single CSS file against its original SCSS source.

    Args:
        scss_path: Path to the original SCSS file
        css_path: Path to the converted CSS file
        mixin_file_content: Content of the mixin file

    Returns:
        True if verification was successful, False otherwise
    """
    try:
        logger.info(f"Verifying CSS file: {css_path}")

        # Read file contents
        scss_content = read_file(str(scss_path))
        css_content = read_file(str(css_path))

        if not scss_content or not css_content:
            logger.warning(
                f"Could not read files or files are empty: {scss_path}, {css_path}"
            )
            return False

        # Generate a prompt for the LLM
        prompt = PROMPT_FOR_CSS_VERIFICATION(
            scss_content, css_content, mixin_file_content
        )

        # Verify with LLM
        verified_css = convert_with_llm(prompt)

        # If no verified_css is returned or it's the same as the original, no changes needed
        if not verified_css or verified_css.strip() == css_content.strip():
            logger.info(f"No issues found in CSS file: {css_path}")
            return True

        p = str(css_path).split(".css")[0]
        # Write the verified CSS back to the file
        if write_file(str(p + "_verified.css"), verified_css):
            logger.info(f"Successfully verified and updated: {css_path}")
            return True
        else:
            logger.error(f"Failed to write verified CSS to: {css_path}")
            return False

    except Exception as e:
        logger.error(f"Error verifying CSS file {css_path}: {str(e)}")
        return False


def verify_converted_styles():
    """
    Main function for verifying converted styles
    """
    styles_dir = STYLES_DIR

    # Find mixin files to use for verification (only .scss files)
    mixin_files = []
    for root, _, files in os.walk(styles_dir):
        for file in files:
            if "mixin" in file.lower() and file.lower().endswith(".scss"):
                mixin_files.append(str(Path(root) / file))

    if not mixin_files:
        logger.error("No SCSS mixin files found, cannot verify CSS")
        return None, []

    # Use the first mixin file found
    mixin_file = mixin_files[0]
    logger.info(f"Using SCSS mixin file for verification: {mixin_file}")

    # Verify CSS files and get unconverted files
    verification_results, unconverted_files = verify_css_files(
        str(styles_dir), mixin_file
    )

    logger.info(f"Verification results: {verification_results}")
    logger.info(f"Unconverted SCSS files: {unconverted_files}")

    return verification_results, unconverted_files


if __name__ == "__main__":
    verify_converted_styles()
