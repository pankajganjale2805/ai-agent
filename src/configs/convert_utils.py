#!/usr/bin/env python3
import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv
import sys

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from helpers.read_write import read_file, write_file
from communication.code_convert import convert_with_llm
from prompt.utils import PROMPT_FOR_API_UTILITY_CONVERSION
from constants import UTILS_PATH

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

SOURCE_PATH = os.getenv("SOURCE_PATH", "")
DESTINATION_PATH = os.getenv("DESTINATION_PATH", "")
source_path = Path(SOURCE_PATH)
destination_path = Path(DESTINATION_PATH)


def convert_angular_api_utils() -> Optional[str]:
    """
    Convert an Angular service/factory to modern JavaScript using LLM.
    Returns the converted code or None if conversion fails.
    """
    try:
        # Read both resource.js and rest-api.js
        resource_path = source_path / "app" / "scripts" / "b-modules" / "resource.js"
        rest_api_path = source_path / "app" / "scripts" / "b-services" / "rest-api.js"

        resource_content = read_file(str(resource_path))
        rest_api_content = read_file(str(rest_api_path))

        # Create prompt for LLM to convert Angular service/factory to modern JS
        prompt = PROMPT_FOR_API_UTILITY_CONVERSION(resource_content, rest_api_content)

        # Convert with LLM
        converted_code = convert_with_llm(prompt)

        if not converted_code:
            logger.error(f"Failed to convert")
            return None

        return converted_code

    except Exception as e:
        logger.error(f"Error converting: {str(e)}")
        return None


def verify_converted_utility(
    file_path: Path, original_content: str, converted_content: str
) -> Tuple[bool, str, Optional[str]]:
    """
    Verify the converted utility code using LLM.
    Returns a tuple of (is_valid, message, updated_code).
    """
    try:
        prompt = f"""You are an expert Next.js version 14 code reviewer. Your task is to verify the conversion of an Angular service/factory to a modern Next.js utility.

Original Angular Service/Factory:
```javascript
{original_content}
```

Converted Next.js Utility:
```javascript
{converted_content}
```

Please verify the following aspects:

1. **Module Structure:**
   - Proper ES6 module format with export/import
   - No Angular-specific dependencies or patterns
   - Modern JavaScript features (async/await, arrow functions) are used correctly

2. **Service/Factory Conversion:**
   - Proper conversion to ES6 classes or functions
   - Same functionality and API surface as original
   - Dependency injection through function parameters instead of Angular's DI

3. **Dependencies:**
   - Angular's $http replaced with axios
   - Angular's $q replaced with native Promises
   - Angular's $timeout replaced with setTimeout
   - Angular's $interval replaced with setInterval

4. **Error Handling:**
   - Proper try/catch implementation
   - Correct async/await usage
   - Error propagation patterns maintained

5. **Code Quality:**
   - Modern JavaScript best practices followed
   - Clean and maintainable code
   - No Angular-specific patterns remain
   - Proper use of ES6+ features

If you find any issues, provide the corrected code. If everything is correct, respond with "VALID".

OUTPUT FORMAT: If you find issues then make changes, respond with the complete updated code. 
If no issues are found, respond with "VALID".

DO NOT include any explanations, markdown formatting, or additional text in your response. 
Just provide the raw JavaScript code or "VALID".
"""

        # Get verification from LLM
        verification_result = convert_with_llm(prompt)

        if verification_result.strip() == "VALID":
            return True, "Utility verification passed", None
        else:
            return False, "Utility code needs updates", verification_result

    except Exception as e:
        return False, f"Error during utility verification: {str(e)}", None


# def convert_angular_services() -> None:
#     """
#     Convert all Angular services and factories in the b-services directory to modern JavaScript utilities.
#     """
#     # Create utils directory if it doesn't exist
#     utils_dir = destination_path / "src" / "utils"
#     utils_dir.mkdir(parents=True, exist_ok=True)

#     # Get all files from b-services directory
#     services_dir = source_path / "app" / "scripts" / "b-services"
#     if not services_dir.exists():
#         logger.error(f"Services directory not found: {services_dir}")
#         return

#     # Process each file in the services directory
#     for file_path in services_dir.glob("*.js"):
#         try:
#             # Convert the service/factory
#             # converted_code = convert_angular_service_to_js(file_path)
#             # if not converted_code:
#             #     continue

#             # Create the output file path
#             output_path = utils_dir / file_path.name

#             # Verify the converted code
#             # original_content = read_file(str(file_path))
#             # is_valid, message, updated_code = verify_converted_utility(
#             #     file_path, original_content, converted_code
#             # )

#             # if not is_valid:
#             #     logger.warning(f"Verification failed for {file_path.name}: {message}")
#             #     if updated_code:
#             #         converted_code = updated_code

#             # Write the converted code
#             if write_file(str(output_path), converted_code):
#                 logger.info(f"Successfully converted {file_path.name} to {output_path}")
#             else:
#                 logger.error(f"Failed to write converted code to {output_path}")

#         except Exception as e:
#             logger.error(f"Error processing {file_path}: {str(e)}")


if __name__ == "__main__":
    converted_code = convert_angular_api_utils()

    if not converted_code:
        logger.error("Failed to convert")
        exit(1)

    output_path = destination_path / UTILS_PATH / "resource.js"

    if write_file(str(output_path), converted_code):
        logger.info(f"Successfully converted")
    else:
        logger.error(f"Failed to write converted code to {output_path}")
