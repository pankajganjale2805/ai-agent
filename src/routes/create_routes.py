#!/usr/bin/env python3
import os
import re
import json
from typing import Dict, List
from dotenv import load_dotenv
from pathlib import Path

from prompts import _get_generate_page_for_route_prompt
from helpers.read_write import read_file
from communication.code_convert import convert_with_llm

load_dotenv()

SOURCE_PATH = os.getenv("SOURCE_PATH", "")
DESTINATION_PATH = os.getenv("DESTINATION_PATH", "")
JSON_REPORT_PATH = os.getenv("JSON_REPORT_PATH", "")
source_path = Path(SOURCE_PATH)
destination_path = Path(DESTINATION_PATH)
json_report_path = Path(JSON_REPORT_PATH)


def update_path_for_dynamic_routes(directory: str) -> str:
    # Remove query parameters if present
    if "?" in directory:
        directory = directory.split("?")[0]

    directory = directory.split("/")
    updated_directory = []
    for d in directory:
        if d.startswith(":"):
            updated_directory.append(f"[{d[1:]}]")
        else:
            updated_directory.append(d)
    return "/".join(updated_directory)


def _get_parent_directory(route: Dict, routes: List[Dict]) -> str:
    """
    Get the parent directory for a given route
    """
    route_name = route["name"]
    if route_name is not None and "." in route_name:
        # Split the name by dots
        name_parts = route_name.split(".")
        # Remove the last part to get the parent name
        parent_name = ".".join(name_parts[:-1])

        # If parent name is empty, return empty string
        if not parent_name:
            return ""

        # Find the parent route
        for r in routes:
            if r["name"] == parent_name:
                return r["url"] if r["url"] else ""
        return ""
    else:
        return ""


def generate_next_pages() -> None:
    """
    Generate Next.js pages based on Angular routes
    """
    print("Generating Next.js pages...", json_report_path)
    with open(json_report_path, "r") as file:
        data = json.load(file)

    # Access the specific key
    routes = data.get("routes", [])
    controllers = data.get("controllers", {})
    templates = data.get("templates", {})

    for route in routes:
        if not route["url"] or not route["name"].startswith("app.models"):
            continue
        directory = route["url"]
        if route["url"].startswith("^"):
            directory = directory[1:]
        else:
            parent_directory = _get_parent_directory(route, routes)
            directory = parent_directory + directory
            if directory.startswith("/"):
                directory = directory[1:]

        directory = update_path_for_dynamic_routes(directory)

        if directory.startswith("^"):
            directory = directory[1:]
        print("directory", directory)

        # Create directory if it doesn't exist
        try:
            # Ensure directory doesn't start with a slash to avoid absolute path issues
            clean_directory = directory.lstrip("/")

            # Add path to the route object
            route["path"] = clean_directory

            output_dir = destination_path / "src" / "app" / clean_directory
            os.makedirs(output_dir, exist_ok=True)

            controller_name = data.get("controller", "")
            template_url = data.get("templateUrl", "")

            controller_name = route.get("controller", "")
            template_url = route.get("templateUrl", "")
            controller_path = controllers.get(controller_name, "")
            # Find the template file path from our templates dictionary
            template_path = templates.get(template_url, "")

            _generate_page_for_route(route, controller_path, template_path)
            # Create an empty page.tsx file
            # output_file = output_dir / 'page.tsx'
            # if not os.path.exists(output_file):
            #   open(output_file, 'w').close()
        except Exception as e:
            print(f"Error creating directory for route {directory}: {str(e)}")

    # Write the updated data back to the JSON file
    try:
        with open(json_report_path, "w") as json_file:
            json.dump(data, json_file, indent=2)
        print(
            f"Successfully updated routes with path property in admin-analysis-report.json"
        )
    except Exception as e:
        print(f"Error writing updated data to JSON: {str(e)}")

    return


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


def _generate_page_for_route(
    route: Dict, controller_path: str, template_path: str
) -> None:
    """
    Generate a React page component for a specific route.
    """
    url = route.get("url", "")
    component_name = _route_to_component_name(url)

    # print('---------------------------------')
    # print('controller_path', controller_path)
    # print('template_path', template_path)
    controller_code = read_file(controller_path) if controller_path else ""
    template_code = read_file(template_path) if template_path else ""

    if not controller_code and not template_code:
        print(f"Warning: No controller or template code found for route {url}")
        return

    print(f"Generating component for route: {url}")

    # Prepare the prompt for LLM conversion
    prompt = _get_generate_page_for_route_prompt(
        controller_code, template_code, component_name
    )

    # Use convert_with_llm to perform the conversion
    react_component = convert_with_llm(prompt, "controller_template", "react_component")

    if not react_component:
        print(
            f"Warning: Failed to convert code for {url}. Creating a default component instead."
        )
        return

    output_dir = destination_path / "src" / "app" / route["path"]
    output_file = output_dir / "page.tsx"
    print("---------------------------------")
    print("react_component", react_component)
    # Write the component to the file
    output_file.write_text(react_component)
    print(f"Generated React component: {output_file}")


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
