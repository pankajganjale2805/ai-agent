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
   - Default values passed as arguments to common API utility should be empty string

OUTPUT FORMAT: Respond ONLY with the converted code without any explanations or comments:
<converted code here>
"""


# def PROMPT_FOR_HANDLING
