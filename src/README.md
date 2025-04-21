# Angular to Next.js Migration Tool

This tool helps migrate legacy Angular codebases to modern Next.js applications using AI assistance.

## Features

- Analyzes Angular routes, controllers, templates, and services
- Generates equivalent Next.js pages and components
- Uses AI/LLM to intelligently convert Angular code to React/Next.js code
- Creates a complete Next.js project structure with proper routing

## Requirements

- Python 3.6+
- OpenRouter API key (for AI-assisted conversion)
- Source Angular codebase
- Internet connection (for API calls)

## Installation

```bash
# Clone the repository
git clone <repository-url>

# Install dependencies
pip install requests python-dotenv
```

## Usage

```bash
# Basic usage without AI assistance
python new-agent.py --angular-root /path/to/angular/project --nextjs-root /path/to/output/nextjs/project

# With OpenRouter API assistance
python new-agent.py --angular-root /path/to/angular/project --nextjs-root /path/to/output/nextjs/project --api-key your-openrouter-api-key

# Specify a different LLM model (default is google/gemini-2.0-flash-001)
python new-agent.py --angular-root /path/to/angular/project --nextjs-root /path/to/output/nextjs/project --api-key your-openrouter-api-key --model claude-3-opus-20240229
```

You can also set the OpenRouter API key as an environment variable:
```bash
export OPENROUTER_API_KEY=your-openrouter-api-key
```

## How It Works

1. **Analysis Phase**: 
   - Scans and analyzes your Angular codebase
   - Extracts route definitions from app.js
   - Maps controllers to templates
   - Identifies services and their dependencies

2. **Conversion Phase**:
   - Creates Next.js project structure
   - Converts Angular routes to Next.js pages
   - Converts controllers to React functional components
   - Converts services to API routes or React hooks
   - Uses AI to improve conversion quality (if API key provided)

3. **Output**:
   - Complete Next.js project ready for further refinement
   - Modern React components using hooks and functional patterns
   - Proper Next.js routing and API endpoints

## Example

```bash
# Migrate the admin dashboard with OpenRouter and Gemini
python new-agent.py --angular-root /Users/username/projects/admin --nextjs-root /Users/username/projects/admin-nextjs --api-key rt-xxxxxxxxxxxxxxxxxxxxxxx
```

### Example with User's Angular Admin Dashboard

For the specific admin dashboard at `/Users/pankaj.ganjale/Desktop/projects/admin`:

```bash
# Migrate the admin dashboard to Next.js with Google Gemini
python new-agent.py --angular-root /Users/pankaj.ganjale/Desktop/projects/admin --nextjs-root /Users/pankaj.ganjale/Desktop/projects/admin-nextjs --api-key your-openrouter-api-key
```

This will:
1. Analyze the legacy Angular codebase with routes in `app/scripts/app.js`
2. Extract controllers from `app/scripts/b-controllers`
3. Extract templates from `app/views` 
4. Use AI to convert these to modern Next.js components
5. Create a complete Next.js project at `/Users/pankaj.ganjale/Desktop/projects/admin-nextjs`

## Limitations

- Complex Angular features may require manual adjustments
- Custom directives might need additional handling
- Some Angular-specific patterns may not have direct Next.js equivalents
- API key is required for the best conversion results
- Conversion quality depends on the LLM model used (Gemini generally works well for code)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 