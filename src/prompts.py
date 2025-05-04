def _get_system_prompt() -> str:
    """
    Generate system prompt for the AI
    """
    return """You are an expert code migration specialist focused on converting Angular to modern Next.js.
Your primary responsibility is to produce clean, production-ready TypeScript/React code that precisely 
replicates the behavior and functionality of the original Angular code.

OUTPUT RULES:
1. Return ONLY the converted code without explanations, markdown, or comments
2. Do not include backticks (```) or language identifiers
3. Convert all functionality from Angular to Next.js
4. Start with the first line of code (imports) and end with the last line
5. Ensure complete, functional code that can be directly used in a Next.js project"""


def _get_user_controller_prompt(source_code: str) -> str:
    """
    Generate user prompt for the AI
    """
    return f"""Convert this Angular controller code to a Next.js API route handler:

```typescript
{source_code}
```

Detailed Conversion Requirements:
1. Convert the Angular controller to a modern Next.js API route handler using App Router conventions
2. Create proper TypeScript interfaces for request/response types
3. Implement RESTful API patterns (GET, POST, PUT, DELETE) as appropriate handlers using axios
4. Add comprehensive error handling with try/catch blocks and appropriate status codes (400, 401, 403, 404, 500)
5. Use TypeScript for type safety throughout the handler
6. For data validation, use Zod or similar validation approach
7. Implement proper response formatting using Response.json() with appropriate status codes
8. Include logging for errors and important events
9. Ensure the API logic matches the original Angular controller exactly, preserving all business rules
10. Handle authentication and authorization patterns similar to the original code

CSS/SCSS Handling:
- If the controller uses any styling logic, convert it appropriately to server-side styles or include relevant middleware

File Organization:
- The code will be placed in app/api/[route]/route.ts following Next.js App Router conventions

OUTPUT FORMAT: Respond ONLY with the converted code without any explanations or comments.
"""


def _get_user_service_prompt(source_code: str) -> str:
    """
    Generate user prompt for the AI
    """
    return f"""Convert this Angular service to React hooks:

```typescript
{source_code}
```

Detailed Conversion Requirements:
1. Convert Angular service methods to React custom hooks
2. Use TypeScript for proper typing of parameters, return values, and state
3. Create separate hooks for different service functionalities if appropriate
4. Properly handle side effects with useEffect and cleanup functions
5. Add proper error handling with try/catch blocks
6. Implement caching and memoization using useMemo and useCallback
7. Replace Angular dependency injection with React Context if needed
8. Use SWR or React Query for data fetching operations if appropriate
9. Handle authentication state persistence similar to the original Angular code
10. Maintain all business logic exactly as in the original code

CSS/SCSS Handling:
- If the service affects styling, convert using Tailwind classes or CSS modules as appropriate

File Organization:
- Code should be organized as custom hooks in lib/hooks/ directory with proper exports

OUTPUT FORMAT: Respond ONLY with the converted code without any explanations or comments.
"""


def _get_api_service_prompt(service_name: str, service_code: str) -> str:
    """
    Generate user prompt for the AI
    """
    return f"""Convert the following Angular service to a Next.js App Router API route handler using TypeScript.
Use the newer Route Handlers style (not pages API routes).

Service name: {service_name}

```typescript
{service_code}
```

Detailed Conversion Requirements:
1. Convert the Angular service to a modern Next.js API route handler using App Router conventions
2. Create proper TypeScript interfaces for request/response types
3. Implement RESTful API patterns (GET, POST, PUT, DELETE) as separate exported functions
4. Add comprehensive error handling with try/catch blocks and appropriate status codes
5. Use TypeScript for type safety throughout the handler
6. For data validation, use Zod or similar validation approach
7. Implement proper response formatting using Response.json() with appropriate status codes
8. Ensure the service logic matches the original Angular service exactly
9. Convert service state to appropriate server-side state management
10. Preserve all business rules and logic flow from the original service

File Organization:
- The code will be placed in app/api/[endpoint]/route.ts following Next.js App Router conventions

OUTPUT FORMAT: Respond ONLY with the converted code without any explanations or comments.
"""


def _get_generate_page_for_route_prompt(
    controller_code: str, template_code: str, component_name: str
) -> str:
    """
    Generate user prompt for the AI
    """
    return f"""You are an extremely detail-oriented and precise expert Angular-to-Next.js migration assistant. Your goal is to create perfectly functional and type-safe Next.js components that precisely replicate the behavior of the original Angular code. You will use React, TypeScript, Tailwind CSS, and the App Router. You will focus solely on the *content* of the converted code, not its location within the project. Assume the converted code will be integrated into an existing Next.js project, and the necessary dependencies are available or will be installed separately.

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

**File Type Handling:**
*   You will determine the file type of the **Legacy Angular File Content** before attempting any conversion (unless the file is empty).
*   If the file analyzed contains CSS or SCSS, proceed to the CSS Conversion instructions outlined below.

**CSS Conversion Instructions:**
1.  **Same Class and Id Names:** Use the same class and id names as in the original Angular code.
2.  **Inline CSS:** Use same inline CSS as in the original Angular code (if any).

**Other File Types** follow the original instructions:

**Conversion Requirements:**
1.  **Angular to Next.js/React Conversion:**
    *   Angular Components => React Components (Server or Client, as appropriate. Base your decision on the file content; for example, if the file imports `useState` or other React Hooks, it will be a client component.
    *   Angular Services => Utility functions, React Hooks, or API routes (depending on purpose). Explain your choice in a comment if the purpose isn't clear.
    *   Angular Modules => Replaced by React's component composition.
    *   Angular Templates/Data Binding => React JSX and state management (useState, useRef, etc.).
    *   Angular Routing => Translate into component logic or data fetching (since routing is handled externally).
    *   Angular Directives => Translate functionality into React components or helper functions. Libraries like clsx or tailwind-merge are preferred for conditional styling.
4.  **Functional Equivalence:** The component's UI and functionality in Next.js must match the original Angular component exactly.
5.  **TypeScript:** Use TypeScript (.tsx for React components, .ts for other code). All components should be strongly typed using interfaces.
6.  **Tailwind CSS:** (Handled in CSS Conversion Instructions).
7.  **Dependencies:** Assume standard Next.js/React libraries are available (e.g., react, react-dom, next).
    *   **3rd Party Libraries:** If a 3rd party library is necessary that isn't part of a standard Next.js setup, add a comment indicating that the library needs to be installed (e.g., "// Install: npm install some-library").
    *   **Import All Dependencies:** Carefully analyze the Angular component for all dependencies (components, utility functions, etc.) and ensure they are correctly represented. Assume that any dependencies are available.
8.  **Error Handling:** Add try...catch blocks where appropriate to handle potential errors, especially with API calls.
9.  **Optimization:** When feasible, apply memoization to React Components.
10. **Prop Mapping (CRITICAL):** This is the most important section. Pay extremely close attention to prop mapping.
    *   Analyze Prop Expectations: Thoroughly examine the original Angular component to determine the exact props expected by child components, including their names, types, and whether they are functions. Examine how the prop is used within the child component to determine the type.
    *   TypeScript Interfaces (MANDATORY): You must create TypeScript interfaces to define prop types for every component.
    *   **Function Props:** If a prop represents a function, ensure that the Next.js component passes a function with the correct name, argument
12. **Output Format:** Respond ONLY with the converted code without any assumptions and commented code: \
    ```
    <Full content of the converted Next.js file without any comments or other text>
    ```
13. Under no circumstances should it include Vanilla JavaScript, jQuery, or Angular code as well as any other dependencies. This is crucial for maintainability, future updates, and to prevent conflicts within the overall React application. Use equivalent React code or library instead.

Convert the provided Angular code now.

OUTPUT FORMAT: Respond ONLY with the converted code without any explanations or comments:
```
<component code here>
```"""
