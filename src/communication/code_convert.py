from dotenv import load_dotenv
import os
import requests

from helpers.extract_code import extract_code_from_response

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL = os.getenv("MODEL", "")
TEMPERATURE = os.getenv("TEMPERATURE", "")


def convert_with_llm(source_code: str) -> str:
    """
    Use LLM to convert code from Angular to Next.js

    Args:
        source_code: The source code or prompt to convert

    Returns:
        Converted code as string
    """
    if not API_KEY:
        print("Warning: No OpenRouter API key provided. Skipping LLM-based conversion.")
        return None

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "HTTP-Referer": "https://localhost",  # Required for OpenRouter API
            "X-Title": "Angular to Next.js Migration Tool",  # Optional for OpenRouter API
        }

        # Create a system prompt that guides the LLM to properly convert the code
        # system_prompt = _get_system_prompt()

        # Generate a user prompt that is specific to the conversion type
        user_prompt = source_code

        # For different source types, we might want to customize the prompt
        # if source_type == "controller" and target_type == "api_route":
        #     user_prompt = _get_user_controller_prompt(source_code)
        # elif source_type == "service" and target_type == "react_hooks":
        #     user_prompt = _get_user_service_prompt(source_code)

        # For controller_template combinations, the source_code is already a complete prompt

        payload = {
            "model": MODEL,
            "messages": [
                # {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": int(TEMPERATURE),
            "max_tokens": 60000,
        }

        print(f"Sending request to {MODEL} for conversion...")

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code == 200:
            result = response.json()
            converted_code = result["choices"][0]["message"]["content"]
            # Clean the response to extract just the code
            cleaned_code = extract_code_from_response(converted_code)
            print(f"Successfully converted code")
            return cleaned_code
        else:
            print(f"Error calling OpenRouter API: {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"Error in LLM conversion: {e}")
        return None
