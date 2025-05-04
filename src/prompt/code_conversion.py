def PROMPT_FOR_CODE_CONVERSION(
    controller_code: str, template_code: str, component_name: str
) -> str:
    """
    Generate user prompt for the AI
    """
    return f"""You are an extremely detail-oriented and precise expert Angular-to-Next.js migration assistant. Your goal is to create perfectly functional Next.js components that precisely replicate the behavior of the original Angular code. You will use React, and the NextJs App Router. You will focus solely on the *content* of the converted code, not its location within the project. Assume the converted code will be integrated into an existing Next.js project, and the necessary dependencies are available or will be installed separately.

Controller code:
```javascript
{controller_code}
```

Template code:
```html
{template_code}
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
```
<component code here>
```"""


def PROMPT_FOR_CSS_CONVERSION(
    file_type: str, css_content: str, common_mixins_content: str
) -> str:
    """
    Generate user prompt for the AI
    """
    return f"""
You are an expert CSS/SASS/LESS modernizer. Your task is to convert the following {file_type} code to modern CSS, considering potential custom mixins from a common file and Bourbon 4 mixins, while:

- Preserving ALL class and ID selectors exactly as they are.
- Ensuring the EXACT SAME visual output and styling compared to the original SASS compiled output.
- Maintaining the same structure and organization where possible, translating SASS nesting to its CSS equivalent.
- Converting any SASS/LESS mixins from the provided common mixins and Bourbon 4 to modern CSS equivalents. This includes translating common Bourbon mixins like clearfix, size, position, transition, transform, border-radius, etc., as well as custom mixins, to their standard CSS properties or modern equivalents using features like custom properties, calc(), flexbox, grid, etc., where appropriate to achieve the original visual output. Assume any mixin or function not found in the provided common mixins is from Bourbon 4.
- Utilizing modern CSS features like custom properties, calc(), flexbox, grid, etc. where appropriate to achieve the original intent and visual output of the SASS/Bourbon code.

Input common mixin {file_type} code:
```
{common_mixins_content}
```

Input {file_type} code:
```
{css_content}
```

OUTPUT FORMAT: Respond ONLY with the converted code without any explanations or comments. It should be only the converted code without css keyword at start.
```
<converted css code or empty string (if no conversion is needed)>
```
"""
