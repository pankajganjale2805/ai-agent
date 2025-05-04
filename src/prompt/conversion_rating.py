def get_verify_conversion_quality_prompt(
    component_name: str,
    controller_code: str,
    template_code: str,
    react_code: str,
) -> str:
    """
    Verify the quality of the conversion of the controller and template to the component.
    """
    return f"""You are an expert Angular-to-React conversion specialist.
Your task is to rate the quality of a React component that was converted from Angular.

Component Name: {component_name}

Original Angular Controller Code:
```javascript
{controller_code}
```

Original Angular Template:
```html
{template_code}
```

Converted React Component:
```tsx
{react_code}
```

Please analyze the conversion quality based on these criteria:
1. Functionality: React component should have all the functionality from the Angular controller.
2. UI Elements: React component should have all the UI elements from the Angular template with same class and id names.
3. HTML Structure: React component should have the same HTML structure as the Angular template.
4. React Best Practices: React component should follow React best practices (hooks, state management, etc.)
5. TypeScript Usage: React component should be properly typed with TypeScript.
6. Code Quality: React component should be clean, maintainable, and efficient.
7. Error Handling: React component should handle errors appropriately.
8. Next.js Compatibility: React component should follow Next.js patterns for page components.
9. React component should not have Vanilla JS, jQuery and Angular dependency as well as code.
10. Console.log statements should be removed.
11. Check for any missing, unused and unnecessary imports
12. Check for undefined variables, functions, types,etc
13. Avoid mocking responses as well as data.

Rate the conversion on a scale of 1-10, where:
- 1-3: Poor conversion with major functionality missing or broken
- 4-6: Acceptable conversion with some issues or missing elements
- 7-8: Good conversion with minor issues
- 9-10: Excellent conversion with all functionality preserved and following best practices

OUTPUT FORMAT: Respond with ONLY a single number from 1 to 10 representing your rating. No other text.
"""
