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
from prompt.code_verification import PROMPT_FOR_LOGIC_VERIFICATION

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

PATHS = [
    # {
    #     "name": "header",
    #     "view": "app/views/header.html",
    #     "controller": "app/scripts/controllers/header.js",
    #     "dependencies": [
    #         "app/scripts/controllers/search.js",
    #         "app/scripts/controllers/main.js",
    #     ],
    # },
    {
        "name": "nav",
        "view": "app/views/nav.html",
        "controller": "app/scripts/controllers/nav.js",
        "dependencies": [
            "app/scripts/directives/navcollapse.js",
            "app/scripts/directives/slimscroll.js",
            "app/scripts/directives/collapsesidebar.js",
            "app/scripts/controllers/main.js",
            "app/scripts/app.js",
        ],
    },
    # {
    #     "name": "app",
    #     "view": "app/views/tmpl/app.html",
    #     "controller": "app/scripts/app.js",
    #     "dependencies": [
    #         "app/scripts/controllers/main.js",
    #     ],
    # },
]


def create_next_layout_file() -> None:
    """
    Create Next.js layout components by mapping through PATHS JSON and using LLM to convert Angular components to React.
    Creates Header, Nav, and App (Layout) components in the correct structure.
    """
    # Create components directory if it doesn't exist
    components_dir = destination_path / "src" / "components"
    components_dir.mkdir(parents=True, exist_ok=True)

    # Process each component in PATHS
    for path in PATHS:
        component_name = path["name"]
        view_path = source_path / path["view"]
        controller_path = source_path / path["controller"]
        dependencies = path["dependencies"]

        # Read the view and controller content
        view_content = read_file(str(view_path))
        controller_content = read_file(str(controller_path))

        # Read all dependency files
        dependency_contents = {}
        for dep in dependencies:
            dep_path = source_path / dep
            if dep_path.exists():
                dependency_contents[dep] = read_file(str(dep_path))

        # Create prompt for LLM to convert Angular to React
        prompt = (
            prompt
        ) = f"""You are an extremely detail-oriented and precise expert Angular-to-Next.js migration assistant. Your goal is to create perfectly functional Next.js components that precisely replicate the behavior of the original Angular code. You will use React, and the NextJs App Router. You will focus solely on the *content* of the converted code, not its location within the project. Assume the converted code will be integrated into an existing Next.js project, and the necessary dependencies are available or will be installed separately.

Controller code:
```javascript
{controller_content}
```

Template code:
```html
{view_content}
```

Dependencies:
```javascript
{json.dumps(dependency_contents, indent=2)}
```

The component should be named {component_name} and should be a fully functional React component.

**Empty File Handling:**
*   If the **Legacy Angular File Content** is empty (contains no code or only whitespace), you **MUST** return an empty string. Do not generate any code or comments.

**Conversion Requirements:**
1.  **Angular to Next.js/React Conversion:**
    *   Angular Components => React Components (Server or Client, as appropriate. Base your decision on the file content; for example, if the file imports `useState` or other React Hooks, it will be a client component.
    *   Angular Services => Utility functions, React Hooks, or API routes (depending on purpose). Explain your choice in a comment if the purpose isn't clear.
    *   Angular Modules => Replaced by React's component composition.
    *   Angular Templates/Data Binding => React JSX and state management (useState, useRef, etc.).
    *   Angular Routing => Translate into component logic or data fetching (since routing is handled externally).
    *   Angular Directives => Translate functionality into React components or helper functions.
2.  **Functional Equivalence:** The component's UI and functionality in Next.js must match the original Angular component exactly.
3.  **Dependencies:** Assume standard Next.js/React libraries are available (e.g., react, react-dom, next).
    *   **3rd Party Libraries:** If a 3rd party library is necessary that isn't part of a standard Next.js setup, use the equivalent React code or library instead.
    *   **Import All Dependencies:** Carefully analyze the Angular component for all dependencies (components, utility functions, etc.) and ensure they are correctly represented. Assume that any dependencies are available.
4.  **Error Handling:** Add try...catch blocks where appropriate to handle potential errors, especially with API calls.
5.  **Optimization:** When feasible, apply memoization to React Components.
6.  **Prop Mapping (CRITICAL):** This is the most important section. Pay extremely close attention to prop mapping.
    *   Analyze Prop Expectations: Thoroughly examine the original Angular component to determine the exact props expected by child components, including their names, and whether they are functions.
    *   **Function Props:** If a prop represents a function, ensure that the Next.js component passes a function with the correct name, argument
7.  **Under no circumstances should it include Vanilla JavaScript, jQuery, or Angular code as well as any other dependencies. This is crucial for maintainability, future updates, and to prevent conflicts within the overall React application. Use equivalent React code or library instead.
8.  **HTML and CSS:** Use the same HTML and CSS as in the original Angular code.
    *   **HTML:** Use the same HTML as in the original Angular code. If the original Angular code has a JQuery, Vanilla JavaScript, or Angular code, use the equivalent React code or library instead.
    *   **CSS:** Use the same Classes and IDs as in the original Angular code.
    *   **Inline CSS:** Use the same inline CSS as in the original Angular code (if any).
    *   **Anchor Tags:** Use next/link for anchor tags.
    *   **HTML Injection from JavaScript:** If the original Angular code has HTML Injection from JavaScript, use the equivalent React code or library instead. Write equivalent React code for the HTML Injection.

Convert the provided Angular code now.

OUTPUT FORMAT: Respond ONLY with the converted code without any explanations or comments:
<component code here>
        """

        # Convert with LLM
        react_component = convert_with_llm(prompt)

        print("react_component", react_component)
        return

        if not react_component:
            logger.error(f"Failed to convert {component_name} component")
            continue

        # Determine the output path based on component name
        if component_name == "app":
            # App component becomes the layout.tsx
            output_path = destination_path / "src" / "app" / "layout.tsx"
        else:
            # Other components go in the components directory
            output_path = components_dir / f"{component_name}.tsx"

        # Write the converted component
        if write_file(str(output_path), react_component):
            logger.info(
                f"Successfully created {component_name} component at {output_path}"
            )
        else:
            logger.error(f"Failed to write {component_name} component to {output_path}")


def verify_html_layout(
    component_path: Path,
    template_path: Path,
    controller_path: Path,
    dependencies: Dict[str, str],
) -> Tuple[bool, str, Optional[str]]:
    """
    Verify the HTML structure and attributes of a React component using LLM.
    Returns a tuple of (is_valid, message, updated_component).
    """
    try:
        content = read_file(str(component_path))
        template_content = read_file(str(template_path))
        controller_content = read_file(str(controller_path))

        # Create prompt for LLM to verify HTML structure
        prompt = f"""You are an expert Angular-to-Next.js migration specialist with deep knowledge of HTML and CSS structures.

Your task is to verify the HTML and CSS structure of a React component that was converted from an Angular template, 
and fix any issues you find.

Original Angular Template:
```html
{template_content}
```

Original Angular Controller:
```javascript
{controller_content}
```

Dependencies:
```javascript
{json.dumps(dependencies, indent=2)}
```

Converted React Component:
```jsx
{content}
```

Please carefully analyze the HTML and CSS structure in the React component and compare it with the original Angular template. Verify following instructions:
*   **HTML:** Converted React component have the same HTML structure as in the original Angular code. If the original Angular code has a JQuery, Vanilla JavaScript, or Angular specific code, there should be the equivalent React code or library instead.
*   **CSS:** Converted React component uses the same Classes and IDs as in the original Angular code.
*   **Inline CSS:** Converted React component have the same inline CSS as in the original Angular code (if any).
*   **Anchor Tags:** Converted React component must use next/link for anchor tags.
*   **HTML Injection from JavaScript:** If the original Angular code has HTML Injection from JavaScript or JQuery, converted React component should have the equivalent React code or library instead.

If you find any issues, update the React component code to fix them. Preserve the JavaScript logic and only 
modify the HTML structure and JSX elements. If there is any missing HTML or CSS, add it to the React component.

OUTPUT FORMAT: If you find issues then make changes, respond with the complete updated React component code. 
If no issues are found, respond with "VALID".

DO NOT include any explanations, markdown formatting, or additional text in your response. 
Just provide the raw React component code or "VALID".
"""

        # Get verification from LLM
        verification_result = convert_with_llm(prompt)

        if verification_result.strip() == "VALID":
            return True, "HTML layout verification passed", None
        else:
            return False, "HTML structure needs updates", verification_result

    except Exception as e:
        return False, f"Error during HTML verification: {str(e)}", None


def verify_component_logic(
    component_path: Path,
    template_path: Path,
    controller_path: Path,
    dependencies: Dict[str, str],
) -> Tuple[bool, str, Optional[str]]:
    """
    Verify the logic and functionality of a React component using LLM.
    Returns a tuple of (is_valid, message, updated_component).
    """
    try:
        content = read_file(str(component_path))
        template_content = read_file(str(template_path))
        controller_content = read_file(str(controller_path))

        # Create prompt for LLM to verify logic
        prompt = f"""You are an expert Angular-to-Next.js migration specialist with deep knowledge of Javascript and React structures.

Your task is to verify the logic of a React component that was converted from an Angular template, 
and fix any issues you find.

Original Angular Template:
```html
{template_content}
```

Original Angular Controller:
```javascript
{controller_content}
```

Dependencies:
```javascript
{json.dumps(dependencies, indent=2)}
```

Converted React Component:
```jsx
{content}
```

Please carefully analyze the logic in the React component and compare it with the original Angular template. Verify following instructions:
*   **Logic:** The same logic as in the original Angular code. If the original Angular code has a JQuery, Vanilla JavaScript, or Angular specific code, there should be the equivalent React code or library instead.
*   **State Management:** The same state management as in the original Angular code.
*   **Event Handling:** The same event handling as in the original Angular code.
*   **API Calls:** The same API calls as in the original Angular code.
*   **Error Handling:** The same error handling as in the original Angular code. (if any)
*   **Functional Equivalence:** The same functionality as in the original Angular component exactly.
*   **Dependencies:** Assume standard Next.js/React libraries are available (e.g., react, react-dom, next).
    *   **3rd Party Libraries:** If a 3rd party library is necessary that isn't part of a standard Next.js setup, use the equivalent React code or library instead.
    *   **Import All Dependencies:** Carefully analyze the Angular component for all dependencies (components, utility functions, etc.) and ensure they are correctly represented. Assume that any dependencies are available.
*   **Error Handling:** Add try...catch blocks where appropriate to handle potential errors, especially with API calls.
*   **Optimization:** When feasible, apply memoization to React Components.
*   **Prop Mapping (CRITICAL):** This is the most important section. Pay extremely close attention to prop mapping.
    *   Analyze Prop Expectations: Thoroughly examine the original Angular component to determine the exact props expected by child components, including their names.
    *   **Function Props:** If a prop represents a function, ensure that the Next.js component passes a function with the correct name, argument
*   **Unused Code:** Use unused code in from React component if needed else remove it.
*   **Add Missing functionality:** Add missing functionality if needed.
*   **Remove Commented Code:** Remove unwanted commented code.
*   **Validation:** Add same validation as in the original Angular code. (if any)
*   **No Data Mocking:** Under any circumstances, do not mock API response or any other data.

If you find any issues, update the React component code to fix them. Preserve the HTML structure and JSX elements and only 
modify the logic. Add missing logic if needed.

OUTPUT FORMAT: If you find issues then make changes, respond with the complete updated React component code. 
If no issues are found, respond with "VALID".

DO NOT include any explanations, markdown formatting, or additional text in your response. 
Just provide the raw React component code or "VALID".
"""

        # Get verification from LLM
        verification_result = convert_with_llm(prompt)

        if verification_result.strip() == "VALID":
            return True, "Logic verification passed", None
        else:
            return False, "Component logic needs updates", verification_result

    except Exception as e:
        return False, f"Error during logic verification: {str(e)}", None


def verify_and_update_layout() -> None:
    """
    Verify the layout components and update them if issues are found.
    """
    # Process each component in PATHS
    for path in PATHS:
        component_name = path["name"]
        component_path = (
            destination_path / "src" / "components" / f"{component_name}.tsx"
        )

        if not component_path.exists():
            logger.error(f"Component file not found: {component_path}")
            continue

        template_path = source_path / path["view"]
        controller_path = source_path / path["controller"]

        # Read all dependency files
        dependencies = {}
        if "dependencies" in path:
            for dep in path["dependencies"]:
                dep_path = source_path / dep
                if dep_path.exists():
                    dependencies[dep] = read_file(str(dep_path))

        # Verify HTML structure
        html_valid, html_message, html_update = verify_html_layout(
            component_path, template_path, controller_path, dependencies
        )
        if not html_valid:
            logger.warning(
                f"HTML verification failed for {component_name}: {html_message}"
            )
            if html_update:
                if write_file(str(component_path), html_update):
                    logger.info(f"Updated {component_name} with HTML fixes")
                else:
                    logger.error(f"Failed to update {component_name} with HTML fixes")
            continue

        # Verify component logic
        logic_valid, logic_message, logic_update = verify_component_logic(
            component_path, template_path, controller_path, dependencies
        )
        if not logic_valid:
            logger.warning(
                f"Logic verification failed for {component_name}: {logic_message}"
            )
            if logic_update:
                if write_file(str(component_path), logic_update):
                    logger.info(f"Updated {component_name} with logic fixes")
                else:
                    logger.error(f"Failed to update {component_name} with logic fixes")
            continue

        logger.info(f"Component {component_name} verification completed successfully")


if __name__ == "__main__":
    create_next_layout_file()
    verify_and_update_layout()
