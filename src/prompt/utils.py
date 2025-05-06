def PROMPT_FOR_API_UTILITY_CONVERSION(
    resource_content: str,
    rest_api_content: str,
) -> str:
    return f"""You are an expert Angular-to-Next.js version 15 migration specialist. Your task is to convert Angular factories using $resource to modern Next.js utilities using Axios.

Original Resource Factory Definition:
```javascript
{resource_content}
```

Original Factory Implementations:
```javascript
{rest_api_content}
```

Please convert these to modern Next.js utilities following these requirements:

1. **Module Structure:**
   - Convert to ES6 module format using export/import
   - Use Axios for HTTP requests
   - Use environment variables for API URL (process.env.NEXT_PUBLIC_API_URL)
   - Create a utility function that handles dynamic URL parameters

2. **Resource Factory Conversion:**
   - Create a createResource utility function that takes:
     * basePath: The base API path (e.g., 'admin/models')
     * paramDefaults: Default parameters for dynamic segments
     * customMethods: Custom HTTP methods and their configurations
   - For each Angular factory, create a constant using createResource
   - Export each resource as a named constant
   - Handle both direct $resource usage and Resource factory usage

3. **URL and Parameter Handling:**
   - Handle any dynamic segments in URLs (e.g., :id, :userId, :modelId, etc.)
   - Support multiple dynamic segments in the same URL (e.g., 'admin/users/:userId/models/:modelId')
   - When a dynamic parameter is not provided:
     * Remove that segment from the URL path
     * DO NOT add the parameter to query parameters
     * Example: For URL 'admin/users/:userId/models/:modelId'
       - With both params: /admin/users/123/models/456
       - With only userId: /admin/users/123/models
       - With only modelId: /admin/users/models/456
       - With no params: /admin/users/models
   - Handle query parameters separately from dynamic segments
   - Support both URL path parameters and query parameters in the same request
   - Examples:
     * URL with multiple dynamic segments: /admin/users/123/models/456
     * URL with query params: /admin/models?status=active&type=premium
     * Combined: /admin/users/123/models?status=active

4. **Method Implementation:**
   - Implement standard methods:
     * query(params): GET request returning array, supports query parameters
     * get(params): GET request for single item, supports both path and query parameters
     * save(data, params): POST request with body and optional parameters
     * update(params, data): PATCH request with both path and query parameters
     * remove(params): DELETE request with parameters
   - Support custom methods from the original factory
   - All methods should return Promises
   - Handle both direct $resource methods and Resource factory methods
   - All methods should support both path and query parameters
   - When calling methods, only include parameters that are actually needed
   - Do not add parameters with falsy values to query params and path parameters

5. **Error Handling:**
   - Implement proper error handling with try/catch
   - Log errors with method name and URL
   - Re-throw errors after logging

6. **Important Notes:**
   - The query() method should be available for all resources to get list of items
   - All dynamic parameters should be optional and removed from URL if not provided
   - Custom methods from original factory should be preserved
   - All HTTP methods should use Axios
   - Use async/await for all API calls
   - Handle both single item and array responses appropriately
   - Support both direct $resource and Resource factory patterns
   - Handle the $save method from Resource factory that switches between create and update
   - Preserve all custom methods and their configurations
   - Support any number of dynamic parameters in both URL paths and query parameters
   - Handle parameter combinations (path + query) in all methods
   - Strictly use typescript for all variables and functions
   - Default values passed as arguments to common API utility should be strictly empty string

OUTPUT FORMAT: Respond ONLY with the converted code without any explanations or comments:
<converted code here>
"""


def PROMPT_FOR_FACTORY_CONVERSION(
    factory_content: str,
) -> str:
    return f"""You are an expert Angular-to-Next.js version 15 migration specialist. Your task is to convert an Angular factory to modern Next.js utility.

Original Factory Code:
```javascript
{factory_content}
```

Please convert this to a modern Next.js utility following these requirements:

1. **Module Structure:**
   - Convert to ES6 module format using export default for the primary utility function.
   - Use modern JavaScript features including async/await, arrow functions, and destructuring.
   - Encapsulate the factory's core functionality into a single export default utility function.

2. **Functionality Preservation:**
   - Maintain all the original factory's business logic, data transformations, and core functionality.
   - Convert Angular dependencies ($http, services, etc.) to modern JavaScript equivalents. Handle HTTP requests using the axios library.
   - Preserve the intended behavior and data flow of the original factory.

3. **Modern Best Practices:**
   - Use TypeScript types for function parameters, return types, and any relevant data structures.
   - Leverage environment variables for base URLs, API keys, or other configuration settings.
   - Adhere to standard Next.js utility practices for maintainability and reusability.

4. **Error Handling:**
   - Implement robust try...catch blocks for all asynchronous operations, especially HTTP requests.
   - Log errors informatively (assume a logging mechanism is available or can be implemented).
   - Return or throw meaningful error messages/objects in case of failure.

Important Notes:
   - Eliminate all Angular-specific code (angular, $scope, $http, Angular services, dependency injection syntax).
   - Convert Angular services to modern JavaScript functions or classes as needed within the utility.
   - Handle any Angular-specific features (like promises from $http) using modern async/await patterns.
   - Ensure the generated code is compatible with Next.js 15.
   - The code should be clean, maintainable, and production-ready.
   - DO NOT INCLUDE ANY COMMENTED CODE IN THE FINAL OUTPUT.
   - AVOID CREATING REACT COMPONENTS. This utility should be purely for logic and data fetching.
   - The output must ONLY contain the converted source code.

OUTPUT FORMAT: Respond ONLY with the converted code without any explanations or comments:
<converted code here>
"""


def PROMPT_FOR_API_VERIFICATION(
    resource_content: str,
    rest_api_content: str,
    converted_content: str,
) -> str:
    return f"""You are an expert code converter specializing in migrating Angular $resource factories to modern Next.js 15 utilities using Axios and TypeScript. You are also skilled at identifying and rectifying errors in such conversions based on specific requirements.
You are given the original Angular $resource factory definition, the original factory implementations, and a attempt at the converted Next.js code.

Original Resource Factory Definition:
```javascript
{resource_content}
```

Original Factory Implementations:
```javascript
{rest_api_content}
```

Attempted Converted Next.js Utility Code:
```typescript
{converted_content}
```

Conversion Requirements (for rectification):
  - Convert to ES6 module format using export/import
  - Use Axios for HTTP requests
  - Use environment variables for API URL (process.env.NEXT_PUBLIC_API_URL)
  - Create a createResource utility function with specified parameters (basePath, paramDefaults, customMethods)
  - Create a constant for each Angular factory using createResource and export them
  - Handle both direct $resource usage and Resource factory usage
  - Handle dynamic segments in URLs (:id, :userId etc.)
  - Support multiple dynamic segments
  - Crucially: Handle missing dynamic parameters by removing the segment from the URL (not adding to query)
  - Handle query parameters separately
  - Support both path and query parameters in all methods
  - Implement standard methods: query, get, save, update, remove
  - Support custom methods with their configurations
  - All methods return Promises
  - Error handling with try/catch and logging
  - Handle the $save method logic (create vs. update)
  - All dynamic parameters should be optional
  - Do not add parameters with falsy values to query params and path parameters
  - Strictly use TypeScript
  - Default values passed as arguments to common API utility should be strictly empty string
  - Strictly remove unused code as well as imports if not required

Task:
  - Review the Attempted Converted Next.js Utility Code against the Original Angular Factory Implementations and the Conversion Requirements.
  - Identify Issues: Check if the Attempted Converted Next.js Utility Code correctly implements all conversion requirements based on the original definitions. Pay close attention to URL construction (especially optional dynamic segments), parameter handling, correct Axios methods, implementation of all required and custom methods, error handling, and TypeScript usage.
  - Rectify Issues: If any issues are found, correct the Attempted Converted Next.js Utility Code to meet the requirements.

Output:
  - If ANY corrections were made, provide the ENTIRE rectified Converted Next.js Utility Code as the response.
  - If NO corrections were necessary (the Attempted Converted Next.js Utility Code already perfectly meets all requirements), respond with the single word: False.

OUTPUT FORMAT: Respond ONLY with the rectified code or the word False. Do not include any explanations, comments outside the code itself, or other text.
<corrected code or False>
"""


def PROMPT_FOR_FACTORY_VERIFICATION(
    original_factory_content: str,
    converted_utility_content: str,
) -> str:
    return f"""You are an expert Angular-to-Next.js version 15 migration verification and correction specialist. Your task is to meticulously compare an original Angular factory's functionality with a converted Next.js utility, identify any discrepancies or violations of the migration requirements, and then correct the converted utility code to accurately match the original functionality and adhere to the specified standards. Finally, provide the corrected code or indicate if no corrections were needed.

Original Angular Factory Code:
```javascript
{original_factory_content}
```

Converted Next.js Utility Code:
```javascript
{converted_utility_content}
```

Analyze both code snippets based on the following criteria:

1. **Functionality Match:**
   - Identify any differences in core business logic, data transformations, calculations, and output between the two snippets.
   - Verify if HTTP requests are made correctly with the same parameters, methods, and endpoints.
   - Check if HTTP responses are processed and utilized identically.

2. **Dependency Handling:**
   - Ensure all Angular dependencies ($http, services, etc.) were correctly replaced with modern JavaScript/Next.js equivalents (e.g., Axios for HTTP).

3. **Modern Best Practices & Structure:**
   - Verify the use of async/await, arrow functions, destructuring, and other modern JavaScript features.
   - Check for correct usage of TypeScript types.
   - Confirm the module structure is export default for the primary utility function.

4. **Error Handling:**
   - Confirm the presence and correctness of try...catch blocks for asynchronous operations.
   - Assess if errors are handled and potentially logged or returned appropriately.

5. **Migration Compliance:**
   - Ensure all Angular-specific constructs (keywords, services, syntax) are completely absent.
   - Verify that the code is free of any commented-out lines or blocks.
   - Ensure absolutely no React components are included.
   - Strictly remove unused code as well as imports if not required

*Based on your analysis:*
   - If you find any issues (functional discrepancies, syntax errors introduced during conversion, violations of migration compliance, etc.) in the Converted Next.js Utility Code when compared to the Original Angular Factory Code and the migration requirements, you MUST carefully edit and correct the Converted Next.js Utility Code. Your correction should make the code functionally equivalent to the original factory while strictly adhering to ALL the migration requirements (modern JS, TypeScript types, Axios, error handling, no Angular, no comments, no components, export default). After making all necessary corrections, output the entire, fully corrected Next.js utility code.
   - If you find NO issues and the Converted Next.js Utility Code is already an accurate and compliant conversion of the Original Angular Factory Code according to the criteria, you MUST output False.

OUTPUT FORMAT: Respond ONLY with either the complete corrected Next.js utility code or the single word False. Do not include any explanations, comments, or other text.
<corrected code or False>
"""
