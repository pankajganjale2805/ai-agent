def PROMPT_FOR_HTML_STRUCTURE_VERIFICATION(
    controller_code: str, template_code: str, react_code: str
) -> str:
    """
    Generate user prompt for the AI
    """
    return f"""You are an expert Angular-to-Next.js migration specialist with deep knowledge of HTML and CSS structures.

Your task is to verify the HTML and CSS structure of a React component that was converted from an Angular template, 
and fix any issues you find.

Original Angular Template:
```html
{template_code}
```

Original Angular Controller:
```javascript
{controller_code}
```

Converted React Component:
```jsx
{react_code}
```

Please carefully analyze the HTML and CSS structure in the React component and compare it with the original Angular template.  Verify following instructions:
*   **HTML:** Converted React component have the same HTML structure as in the original Angular code. If the original Angular code has a JQuery, Vanilla JavaScript, or Angular specific code, there should be the equivalent React code or library instead.
*   **CSS:** Converted React component uses the same Classes and IDs as in the original Angular code.
*   **Inline CSS:** Converted React component have the same inline CSS as in the original Angular code (if any).
*   **Anchor Tags:** Converted React component must use next/link for anchor tags.
*   **HTML Injection from JavaScript:** If the original Angular code has HTML Injection from JavaScript or JQuery, converted React component should have the equivalent React code or library instead.

If you find any issues, update the React component code to fix them. Preserve the JavaScript logic and only 
modify the HTML structure and JSX elements. If there is any missing HTML or CSS, add it to the React component.

OUTPUT FORMAT: If you find issues then make changes, respond with the complete updated React component code. 
If no issues are found, respond with empty string.

DO NOT include any explanations, markdown formatting, or additional text in your response. 
Just provide the raw React component code or empty string.
"""


def PROMPT_FOR_LOGIC_VERIFICATION(
    controller_code: str, template_code: str, react_code: str
) -> str:
    """
    Generate user prompt for the AI
    """
    return f"""You are an expert Angular-to-Next.js migration specialist with deep knowledge of Javascript and React structures.

Your task is to verify the logic of a React component that was converted from an Angular template, 
and fix any issues you find.

Original Angular Template:
```html
{template_code}
```

Original Angular Controller:
```javascript
{controller_code}
```

Converted React Component:
```jsx
{react_code}
```

Please carefully analyze the logic in the React component and compare it with the original Angular template.  Verify following instructions:
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
If no issues are found, respond with empty string.

DO NOT include any explanations, markdown formatting, or additional text in your response. 
Just provide the raw React component code or empty string.
"""


def PROMPT_FOR_API_CALLS_VERIFICATION(
    controller_code: str, template_code: str, react_code: str
) -> str:
    """
    Generate user prompt for the AI
    """
    return f"""You are an expert Angular-to-Next.js migration specialist with deep knowledge of Javascript and React structures.

Your task is to verify the API calls of a React component that was converted from an Angular code, and fix any issues you find.

Original Angular Controller:
```javascript
{controller_code}
```

Converted React Component:
```jsx
{react_code}
```

Please carefully analyze the API calls in the React component and compare it with the original Angular controller.  Verify following instructions:
*   **API Calls:** The same API calls as in the original Angular code.
*   **Error Handling:** The same error handling as in the original Angular code. (if any)
*   **No Data Mocking:** Under any circumstances, do not mock API response or any other data related to API calls.
*   Assume services are declared in services folder. Each service have functions for each API call. Use the functions in the component to make API calls and pass valid payloads (if any). Strictly import it as @/services/service-name.js in the component.
*   Use axios for API calls. Assume axios is available.
*   Use try...catch blocks for API calls.
*   Instead of commenting out any code related to API calls logic, implement it properly (if needed) or remove it completely if not needed.
*   Follow best practices for API calls and error handling.
*   Strictly avoid adding any commented out code related to API calls.

If you find any issues, update the React component code to fix them. Preserve the HTML structure and JSX elements and only 
modify the API calls and logic related to API calls if needed.

OUTPUT FORMAT: If you find issues then make changes, respond with the complete updated React component code. 
If no issues are found, strictly respond with empty string.

DO NOT include any explanations, markdown formatting, or additional text in your response. 
Just provide the raw React component code or empty string.
"""


def PROMPT_FOR_CSS_VERIFICATION(
    sass_content: str,
    converted_css_content: str,
    common_mixins_content: str,
) -> str:
    return f"""
You are an expert CSS/SASS/LESS modernizer with deep knowledge of Bourbon 4 mixins. Your task is to thoroughly verify and rectify the following converted code from SASS to CSS, ensuring it accurately reflects the original SASS compiled output while utilizing modern CSS practices.

Verify and rectify based on the following instructions:
- Preserving ALL class and ID selectors exactly as they are used in the original SASS.
- Ensuring the EXACT SAME visual output and styling compared to the original SASS compiled output across all elements and states.
- Maintaining the same structure and organization where possible, accurately translating SASS nesting and hierarchy to its equivalent CSS selectors.
- Converting any SASS/LESS mixins from the provided `common_mixins_content`, which represents a collection of custom mixins used in the original SASS project, and Bourbon 4 mixins to modern CSS equivalents. This includes translating common Bourbon mixins like `clearfix`, `size`, `position`, `transition`, `transform`, `border-radius`, etc., as well as custom mixins, to their standard CSS properties or modern equivalents using features like custom properties, calc(), flexbox, grid, etc., where appropriate to achieve the original visual output. Assume any mixin or function not found in the common mixins is from Bourbon 4 and translate it accordingly.
- Utilizing modern CSS features like custom properties, calc(), flexbox, grid, etc., where appropriate and semantically correct, to achieve the original intent and visual output of the SASS/Bourbon code, prioritizing maintainability and performance.

Original common mixin code:
```
{common_mixins_content}
```

Original SASS code:
```
{sass_content}
```

Converted CSS code:
```
{converted_css_content}
```

OUTPUT FORMAT: Respond ONLY with the converted code without any explanations or comments. It should be only the converted code or empty string (if no conversion is needed) without css keyword at start.
```
<converted css code or empty string (if no conversion is needed)>
```
"""
