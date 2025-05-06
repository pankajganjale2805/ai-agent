#!/usr/bin/env python3
import os
import re
import logging
from pathlib import Path
from typing import Dict, Optional, List, Union, Any
from dotenv import load_dotenv
import sys
import json

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from helpers.read_write import read_file, write_file
from communication.code_convert import convert_with_llm
from prompt.utils import (
    PROMPT_FOR_API_UTILITY_CONVERSION,
    PROMPT_FOR_FACTORY_CONVERSION,
    PROMPT_FOR_API_VERIFICATION,
    PROMPT_FOR_FACTORY_VERIFICATION,
)
from constants import API_UTILS, IGNORE_JS_DIRS, IGNORE_FACTORY_FILES, MAX_TRIALS

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


class FactoryConversion:
    def __init__(self):
        self.source_path = Path(os.getenv("SOURCE_PATH", ""))
        self.destination_path = Path(os.getenv("DESTINATION_PATH", ""))
        self.report = {
            "api_utils": {
                "conversion_trial": 0,
                "is_converted": False,
                "max_trials": MAX_TRIALS,
                "last_error": None,
                "verification_trial": 0,
                "verification_success": 0,
                "verification_failed": 0,
                "file_updated": 0,
                "verified": False,
            },
            "other_utils": {},
        }

    def update_factory_report(
        self, util_type: str, is_converted: bool, error: Optional[str] = None
    ):
        """Update the factory conversion report."""
        try:
            if util_type == "api_utils":
                self.report[util_type]["conversion_trial"] += 1
                self.report[util_type]["is_converted"] = is_converted
                self.report[util_type]["last_error"] = error
            else:
                if util_type not in self.report["other_utils"]:
                    self.report["other_utils"][util_type] = {
                        "conversion_trial": 0,
                        "is_converted": False,
                        "max_trials": MAX_TRIALS,
                        "last_error": None,
                    }
                self.report["other_utils"][util_type]["conversion_trial"] += 1
                self.report["other_utils"][util_type]["is_converted"] = is_converted
                self.report["other_utils"][util_type]["last_error"] = error

        except Exception as e:
            logger.error(f"Error updating factory report: {str(e)}")

    def update_verification_report(
        self, util_type: str, is_success: bool, is_updated: bool = False
    ):
        """Update the verification report."""
        try:
            if util_type == "api_utils":
                self.report[util_type]["verification_trial"] += 1
                if is_success:
                    self.report[util_type]["verification_success"] += 1
                    if is_updated:
                        self.report[util_type]["file_updated"] += 1
                else:
                    self.report[util_type]["verification_failed"] += 1
            else:
                self.report["other_utils"][util_type]["verification_trial"] += 1
                if is_success:
                    self.report["other_utils"][util_type]["verification_success"] += 1
                    if is_updated:
                        self.report["other_utils"][util_type]["file_updated"] += 1
                else:
                    self.report["other_utils"][util_type]["verification_failed"] += 1
        except Exception as e:
            logger.error(f"Error updating verification report: {str(e)}")

    def _is_false_result(self, result: Any) -> bool:
        """
        Check if the result indicates no changes needed.
        Handles various string representations of false.
        """
        if result is False:
            return True
        if isinstance(result, str):
            return result.lower() in ["false", "FALSE", "False"]
        return False

    def verify_api_utils(self) -> Union[str, bool, None]:
        """
        Verify the converted API utils by comparing with original files.
        Returns:
            - str: Updated code if changes are needed
            - False: If verification successful and no changes needed
            - None: If verification failed
        """
        try:
            # Read original files
            resource_path = self.source_path / API_UTILS["SOURCE"]["RESOURCE_PATH"]
            rest_api_path = self.source_path / API_UTILS["SOURCE"]["REST_API_PATH"]
            converted_path = self.destination_path / API_UTILS["DESTINATION"]

            resource_content = read_file(str(resource_path))
            rest_api_content = read_file(str(rest_api_path))
            converted_content = read_file(str(converted_path))

            # Create prompt for verification
            prompt = PROMPT_FOR_API_VERIFICATION(
                resource_content, rest_api_content, converted_content
            )

            # Verify with LLM
            result = convert_with_llm(prompt)

            if self._is_false_result(result):
                # Successfully verified, no changes needed
                self.update_verification_report("api_utils", True, False)
                return False
            elif result:
                # Got updated code
                self.update_verification_report("api_utils", True, True)
                return result
            else:
                # Verification failed
                self.update_verification_report("api_utils", False, False)
                return None

        except Exception as e:
            logger.error(f"Error verifying API utils: {str(e)}")
            self.update_verification_report("api_utils", False, False)
            return None

    def verify_factory_to_nextjs(self, file_path: str) -> Union[str, bool, None]:
        """
        Verify a converted factory file.
        Returns:
            - str: Updated code if changes are needed
            - False: If verification successful and no changes needed
            - None: If verification failed
        """
        try:
            # Read original and converted files
            original_path = self.source_path / file_path
            file_name = Path(file_path).name
            stem = Path(file_name).stem

            # Check both .ts and .tsx files
            ts_path = self.destination_path / "src" / "utils" / f"{stem}.ts"
            tsx_path = self.destination_path / "src" / "utils" / f"{stem}.tsx"

            # Determine which file exists and read its content
            if ts_path.exists():
                converted_path = ts_path
                converted_content = read_file(str(converted_path))
            elif tsx_path.exists():
                converted_path = tsx_path
                converted_content = read_file(str(tsx_path))
            else:
                logger.error(f"No converted file found for {file_path}")
                return None

            original_content = read_file(str(original_path))

            # Create prompt for verification
            prompt = PROMPT_FOR_FACTORY_VERIFICATION(
                original_content, converted_content
            )

            # Verify with LLM
            result = convert_with_llm(prompt)

            if self._is_false_result(result):
                # Successfully verified, no changes needed
                self.update_verification_report(file_path, True, False)
                return False
            elif result:
                # Got updated code
                self.update_verification_report(file_path, True, True)
                return result
            else:
                # Verification failed
                self.update_verification_report(file_path, False, False)
                return None

        except Exception as e:
            logger.error(f"Error verifying {file_path}: {str(e)}")
            self.update_verification_report(file_path, False, False)
            return None

    def verify_all_factories(self):
        """Verify all factory conversions."""
        # Verify API utils
        if (
            self.report["api_utils"]["is_converted"]
            and not self.report["api_utils"]["verified"]
            and self.report["api_utils"]["verification_trial"] < MAX_TRIALS
        ):
            logger.info("Starting API utils verification...")

            # Verify up to MAX_TRIALS times or until verification is successful
            for attempt in range(MAX_TRIALS):
                logger.info(f"Verification attempt {attempt + 1}/{MAX_TRIALS}")

                result = self.verify_api_utils()
                if result is None:
                    # Verification failed, continue to next attempt
                    logger.error("Verification failed, trying again...")
                    continue
                elif result is False:
                    # Successfully verified, no changes needed
                    logger.info("Successfully verified API utils, no changes needed")
                    self.report["api_utils"]["verified"] = True
                    break
                else:
                    # Got updated code, write it
                    output_path = self.destination_path / API_UTILS["DESTINATION"]
                    if write_file(str(output_path), result):
                        logger.info("Successfully updated API utils with verified code")
                    else:
                        logger.error("Failed to write verified code")

            # If we've done all trials, mark as verified
            if self.report["api_utils"]["verification_trial"] >= MAX_TRIALS:
                self.report["api_utils"]["verified"] = True
        else:
            logger.info(
                "Skipping API utils verification - already verified or max trials reached"
            )

        # Verify other factories
        for file_path, file_info in self.report["other_utils"].items():
            if (
                file_info["is_converted"]
                and not file_info["verified"]
                and file_info["verification_trial"] < MAX_TRIALS
            ):
                logger.info(f"Starting verification for {file_path}...")

                # Verify up to MAX_TRIALS times or until verification is successful
                for attempt in range(MAX_TRIALS):
                    logger.info(f"Verification attempt {attempt + 1}/{MAX_TRIALS}")

                    result = self.verify_factory_to_nextjs(file_path)
                    if result is None:
                        # Verification failed, continue to next attempt
                        logger.error(
                            f"Verification failed for {file_path}, trying again..."
                        )
                        continue
                    elif result is False:
                        # Successfully verified, no changes needed
                        logger.info(
                            f"Successfully verified {file_path}, no changes needed"
                        )
                        self.report["other_utils"][file_path]["verified"] = True
                        break
                    else:
                        # Got updated code, write it
                        file_name = Path(file_path).name
                        stem = Path(file_name).stem
                        ext = (
                            ".tsx"
                            if "'react'" in result or '"react"' in result
                            else ".ts"
                        )
                        output_path = (
                            self.destination_path / "src" / "utils" / f"{stem}{ext}"
                        )
                        output_path.parent.mkdir(parents=True, exist_ok=True)

                        # Delete the other extension file if it exists
                        other_ext = ".ts" if ext == ".tsx" else ".tsx"
                        other_path = (
                            self.destination_path
                            / "src"
                            / "utils"
                            / f"{stem}{other_ext}"
                        )
                        if other_path.exists():
                            other_path.unlink()
                            logger.info(f"Deleted {other_ext} file for {file_path}")

                        if write_file(str(output_path), result):
                            logger.info(
                                f"Successfully updated {file_path} with verified code"
                            )
                        else:
                            logger.error(
                                f"Failed to write verified code for {file_path}"
                            )

                # If we've done all trials, mark as verified
                if (
                    self.report["other_utils"][file_path]["verification_trial"]
                    >= MAX_TRIALS
                ):
                    self.report["other_utils"][file_path]["verified"] = True
            else:
                logger.info(
                    f"Skipping verification for {file_path} - already verified or max trials reached"
                )

        # Print final report as JSON
        print(json.dumps(self.report, indent=2))

    def should_attempt_conversion(self, util_type: str) -> bool:
        """Check if we should attempt conversion based on the report."""
        try:
            if util_type == "api_utils":
                util_info = self.report[util_type]
                return (
                    not util_info["is_converted"]
                    and util_info["conversion_trial"] < util_info["max_trials"]
                )
            else:
                util_info = self.report["other_utils"].get(
                    util_type,
                    {
                        "conversion_trial": 0,
                        "is_converted": False,
                        "max_trials": MAX_TRIALS,
                    },
                )
                return (
                    not util_info["is_converted"]
                    and util_info["conversion_trial"] < util_info["max_trials"]
                )

        except Exception as e:
            logger.error(f"Error reading factory report: {str(e)}")
            return False

    def find_js_files_with_factories(self) -> List[str]:
        """Find all files with factory functions excluding the ones in the ignore list."""
        factory_regex = re.compile(r"\.factory\(\s*['\"]\w+['\"]\s*,")
        factory_files = []

        scripts_path = os.path.join(self.source_path, "app", "scripts")

        for root, dirs, files in os.walk(scripts_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_JS_DIRS]

            for file in files:
                if not file.endswith(".js"):
                    continue

                if any(ignore_str in file for ignore_str in IGNORE_FACTORY_FILES):
                    continue

                full_path = os.path.join(root, file)
                try:
                    content = read_file(full_path)
                    if factory_regex.search(content):
                        relative_path = os.path.relpath(full_path, self.source_path)
                        factory_files.append(relative_path)
                except Exception as e:
                    logger.error(f"Error reading file {full_path}: {e}")

        # Update report with discovered files
        for file_path in factory_files:
            self.report["other_utils"][file_path] = {
                "conversion_trial": 0,
                "is_converted": False,
                "max_trials": MAX_TRIALS,
                "last_error": None,
                "verification_trial": 0,
                "verification_success": 0,
                "verification_failed": 0,
                "file_updated": 0,
                "verified": False,
            }

        return factory_files

    def convert_angular_api_utils(self) -> Optional[str]:
        """Convert Angular API utilities to modern JavaScript."""
        try:
            if not self.should_attempt_conversion("api_utils"):
                logger.info(
                    "Skipping API utils conversion - already converted or max trials reached"
                )
                return None

            resource_path = self.source_path / API_UTILS["SOURCE"]["RESOURCE_PATH"]
            rest_api_path = self.source_path / API_UTILS["SOURCE"]["REST_API_PATH"]

            resource_content = read_file(str(resource_path))
            rest_api_content = read_file(str(rest_api_path))

            prompt = PROMPT_FOR_API_UTILITY_CONVERSION(
                resource_content, rest_api_content
            )
            converted_code = convert_with_llm(prompt)

            if not converted_code:
                error_msg = "Failed to convert API utils"
                self.update_factory_report("api_utils", False, error_msg)
                logger.error(error_msg)
                if self.should_attempt_conversion("api_utils"):
                    logger.info("Retrying API utils conversion...")
                    return self.convert_angular_api_utils()
                return None

            return converted_code

        except Exception as e:
            error_msg = f"Error converting API utils: {str(e)}"
            self.update_factory_report("api_utils", False, error_msg)
            logger.error(error_msg)
            if self.should_attempt_conversion("api_utils"):
                logger.info("Retrying API utils conversion after error...")
                return self.convert_angular_api_utils()
            return None

    def convert_factory_to_nextjs(self, file_path: str) -> Optional[str]:
        """Convert an Angular factory to modern Next.js utility."""
        try:
            if not self.should_attempt_conversion(file_path):
                logger.info(
                    f"Skipping {file_path} - already converted or max trials reached"
                )
                return None

            content = read_file(file_path)
            prompt = PROMPT_FOR_FACTORY_CONVERSION(content)
            converted_code = convert_with_llm(prompt)

            if not converted_code:
                error_msg = f"Failed to convert {file_path}"
                self.update_factory_report(file_path, False, error_msg)
                logger.error(error_msg)
                if self.should_attempt_conversion(file_path):
                    logger.info(f"Retrying conversion for {file_path}...")
                    return self.convert_factory_to_nextjs(file_path)
                return None

            return converted_code

        except Exception as e:
            error_msg = f"Error converting {file_path}: {str(e)}"
            self.update_factory_report(file_path, False, error_msg)
            logger.error(error_msg)
            if self.should_attempt_conversion(file_path):
                logger.info(f"Retrying conversion for {file_path} after error...")
                return self.convert_factory_to_nextjs(file_path)
            return None

    def convert_all_factories(self):
        """Convert all factory files to Next.js utilities."""
        # First convert API utils
        converted_code = self.convert_angular_api_utils()
        if converted_code:
            output_path = self.destination_path / API_UTILS["DESTINATION"]
            if write_file(str(output_path), converted_code):
                self.update_factory_report("api_utils", True)
                logger.info("Successfully converted API utils")
            else:
                error_msg = f"Failed to write converted code to {output_path}"
                self.update_factory_report("api_utils", False, error_msg)
                logger.error(error_msg)

        # Find all factory files first
        logger.info("Discovering factory files...")
        factory_files = self.find_js_files_with_factories()
        logger.info(f"Found {len(factory_files)} factory files to convert")

        # Then convert other factories
        for file_path in factory_files:
            logger.info(f"Converting {file_path}")

            if self.report["other_utils"][file_path]["is_converted"]:
                continue

            converted_code = self.convert_factory_to_nextjs(file_path)

            if converted_code:
                file_name = Path(file_path).name
                stem = Path(file_name).stem
                ext = (
                    ".tsx"
                    if "'react'" in converted_code or '"react"' in converted_code
                    else ".ts"
                )
                output_path = self.destination_path / "src" / "utils" / f"{stem}{ext}"
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if write_file(str(output_path), converted_code):
                    logger.info(f"Successfully converted {file_path} to {output_path}")
                    self.update_factory_report(file_path, True)
                else:
                    error_msg = f"Failed to write converted code for {file_path}"
                    self.update_factory_report(file_path, False, error_msg)
                    logger.error(error_msg)
            else:
                logger.error(f"Failed to convert {file_path}")
                self.update_factory_report(file_path, False, "Failed to convert")

        # Print final report as JSON
        print(json.dumps(self.report, indent=2))


def main():
    converter = FactoryConversion()
    converter.convert_all_factories()
    converter.verify_all_factories()


if __name__ == "__main__":
    main()
