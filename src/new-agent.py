#!/usr/bin/env python3
import os
import re
import json
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
from dotenv import load_dotenv
import shutil
import traceback

from src.analyzer import AngularCodebaseAnalyzer
import src.prompts as prompts


# Load environment variables
load_dotenv()

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEFAULT_MODEL = "anthropic/claude-3-sonnet"
DEFAULT_TEMPERATURE = 0.2


class AngularToNextMigrator:
    def __init__(self, angular_root: str, nextjs_root: str, api_key: str = None, model: str = None, analysis_file: str = None):
        """
        Initialize the migrator with Angular and Next.js project paths
        
        Args:
            angular_root: Path to Angular project root
            nextjs_root: Path to Next.js project root
            api_key: OpenRouter API key for LLM conversion
            model: Model to use for LLM conversion
            analysis_file: Path to pre-generated analysis file
        """
        self.angular_root = Path(angular_root)
        self.nextjs_root = Path(nextjs_root)
        self.api_key = api_key
        self.model = model or "anthropic/claude-3-sonnet"
        self.analysis_file = analysis_file
        
        # Initialize analysis data structures
        self.routes = []
        self.controllers = {}
        self.templates = {}
        self.services = {}
        self.directives = {}
        
        # Define paths
        self.app_js_path = self.angular_root / 'app.js'
        self.app_path = self.angular_root / 'app'
        
        # Create Next.js output directory if it doesn't exist
        self.nextjs_output_dir = self.nextjs_root
        os.makedirs(self.nextjs_output_dir, exist_ok=True)
        
        # Ensure path exists and is directory
        if not self.angular_root.exists() or not self.angular_root.is_dir():
            raise ValueError(f"Angular project root {angular_root} does not exist or is not a directory")
        
        # Create Next.js project directory if it doesn't exist
        self.nextjs_root.mkdir(parents=True, exist_ok=True)
        
        # Initialize data structures
        self.routes: List[Dict] = []
        self.controllers: Dict[str, str] = {}
        self.templates: Dict[str, str] = {}
        self.services: Dict[str, str] = {}
        self.directives: Dict[str, str] = {}
        
        # Try to find analysis file if not provided
        if not self.analysis_file:
            # Look for either verified or regular analysis file
            verified_file = Path("scripts/verified-admin-analysis-report.json")
            regular_file = Path("scripts/admin-analysis-report.json")
            
            if verified_file.exists():
                self.analysis_file = verified_file
            elif regular_file.exists():
                self.analysis_file = regular_file
        
        # Define paths
        self.app_js_path = self.angular_root / 'app' / 'scripts' / 'app.js'
        self.app_path = self.angular_root / 'app'
        self.scripts_path = self.angular_root / 'app' / 'scripts'
        self.views_path = self.angular_root / 'app' / 'views'
        self.styles_path = self.angular_root / 'app' / 'scss'
    
    def load_analysis_data(self) -> bool:
        """
        Load pre-computed analysis data from JSON file
        
        Returns:
            True if data loaded successfully, False otherwise
        """
        if not self.analysis_file or not Path(self.analysis_file).exists():
            print(f"Warning: Analysis file {self.analysis_file} does not exist")
            return False
            
        try:
            with open(self.analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
                
            print(f"Loading analysis data from {self.analysis_file}")
            
            # Extract routes
            if 'routes' in analysis_data:
                for route in analysis_data['routes']:
                    # Convert to our route format
                    route_data = {
                        'name': route.get('name', ''),
                        'url': route.get('url', ''),
                        'controller': route.get('controller', None),
                        'templateUrl': route.get('templateUrl', None),
                        'abstract': route.get('abstract', False),
                        'resolve': route.get('resolve_dependencies', [])
                    }
                    # Add template if available
                    if 'template' in route:
                        route_data['template'] = route['template']
                        
                    self.routes.append(route_data)
                    
                print(f"Loaded {len(self.routes)} routes from analysis file")
                
            # Extract controllers
            if 'controllers' in analysis_data:
                self.controllers = analysis_data['controllers']
                print(f"Loaded {len(self.controllers)} controllers from analysis file")
                
            # Extract services
            if 'services' in analysis_data:
                self.services = analysis_data['services']
                print(f"Loaded {len(self.services)} services from analysis file")
                
            # Extract directives
            if 'directives' in analysis_data:
                self.directives = analysis_data['directives']
                print(f"Loaded {len(self.directives)} directives from analysis file")
                
            # Extract templates from routes
            templates_seen = set()
            for route in self.routes:
                if route['templateUrl'] and route['templateUrl'] not in templates_seen:
                    # Store template path relative to views directory
                    template_path = route['templateUrl']
                    full_path = self.angular_root / 'app' / template_path
                    if full_path.exists():
                        self.templates[template_path] = str(full_path)
                        templates_seen.add(template_path)
                        
            print(f"Extracted {len(self.templates)} templates from analysis file")
            
            return True
            
        except Exception as e:
            print(f"Error loading analysis data: {e}")
            traceback.print_exc()
            return False
            
    def analyze_controllers(self) -> None:
        """
        Find and analyze all controllers
        """
        print("Analyzing controllers...")
        
        # Search all JS files in scripts directory for controllers
        if not self.scripts_path.exists():
            print(f"Warning: {self.scripts_path} does not exist")
            return
        
        # Find all JS files in scripts directory and subdirectories
        controller_files = list(self.scripts_path.glob('**/*.js'))
        
        for file_path in controller_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Extract controller names using regex
                controller_matches = re.findall(r"\.controller\(['\"]([^'\"]+)['\"]", content)
                
                for controller_name in controller_matches:
                    relative_path = file_path.relative_to(self.angular_root)
                    self.controllers[controller_name] = str(relative_path)
                
                # Also check for directives that might contain controller logic
                directive_matches = re.findall(r"\.directive\(['\"]([^'\"]+)['\"]", content)
                for directive_name in directive_matches:
                    if "controller:" in content:
                        # Store directives with controllers as a special type of controller
                        relative_path = file_path.relative_to(self.angular_root)
                        self.controllers[f"Directive_{directive_name}"] = str(relative_path)
            except Exception as e:
                print(f"Warning: Could not analyze file {file_path}: {e}")
        
        print(f"Found {len(self.controllers)} controllers and directives with controllers")
    
    def analyze_templates(self) -> None:
        """
        Find and analyze all templates
        """
        print("Analyzing templates...")
        
        # Check all HTML files in app directory, not just views
        if not self.app_path.exists():
            print(f"Warning: {self.app_path} does not exist")
            return
        
        # Find all HTML files in app directory and subdirectories
        template_files = list(self.app_path.glob('**/*.html'))
        print('template_files', template_files)
        for file_path in template_files:
            try:
                relative_path = file_path.relative_to(self.angular_root)
                template_url = str(relative_path).replace('app/', '')
                self.templates[template_url] = str(file_path)
            except Exception as e:
                print(f"Warning: Could not process template {file_path}: {e}")
        
        print(f"Found {len(self.templates)} templates")
        return
    
    def analyze_services(self) -> None:
        """
        Find and analyze all services
        """
        print("Analyzing services...")
        
        # Search all JS files in scripts directory for services
        if not self.scripts_path.exists():
            print(f"Warning: {self.scripts_path} does not exist")
            return
        
        # Find all JS files in scripts directory and subdirectories
        service_files = list(self.scripts_path.glob('**/*.js'))
        
        for file_path in service_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Extract service names - check for service, factory, provider patterns
                service_matches = re.findall(r"\.(?:service|factory|provider)\(['\"]([^'\"]+)['\"]", content)
                
                for service_name in service_matches:
                    relative_path = file_path.relative_to(self.angular_root)
                    self.services[service_name] = str(relative_path)
                    
                # Also look for custom services implemented as values
                value_matches = re.findall(r"\.value\(['\"]([^'\"]+)['\"]", content)
                for value_name in value_matches:
                    relative_path = file_path.relative_to(self.angular_root)
                    self.services[f"Value_{value_name}"] = str(relative_path)
                    
                # Check for constants that might be used as services
                constant_matches = re.findall(r"\.constant\(['\"]([^'\"]+)['\"]", content)
                for constant_name in constant_matches:
                    relative_path = file_path.relative_to(self.angular_root)
                    self.services[f"Constant_{constant_name}"] = str(relative_path)
            except Exception as e:
                print(f"Warning: Could not analyze file {file_path}: {e}")
        
        print(f"Found {len(self.services)} services")
    
    def analyze_directives(self) -> None:
        """
        Find and analyze all directives
        """
        print("Analyzing directives...")
        
        # Search all JS files in scripts directory for directives
        if not self.scripts_path.exists():
            print(f"Warning: {self.scripts_path} does not exist")
            return
        
        # Find all JS files in scripts directory and subdirectories
        directive_files = list(self.scripts_path.glob('**/*.js'))
        
        # Store directives in a dictionary: name -> path
        self.directives = {}
        
        for file_path in directive_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Extract directive names using regex
                directive_matches = re.findall(r"\.directive\(['\"]([^'\"]+)['\"]", content)
                
                for directive_name in directive_matches:
                    relative_path = file_path.relative_to(self.angular_root)
                    self.directives[directive_name] = str(relative_path)
            except Exception as e:
                print(f"Warning: Could not analyze file {file_path}: {e}")
        
        print(f"Found {len(self.directives)} directives")
    
    def analyze_dependencies(self) -> None:
        """
        Analyze package.json and bower.json to identify dependencies
        and map them to React/Next.js equivalents
        """
        print("Analyzing dependencies...")
        
        dependencies = {}
        
        # Check for package.json
        package_json_path = self.angular_root / 'package.json'
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    
                if 'dependencies' in package_data:
                    dependencies.update(package_data['dependencies'])
                if 'devDependencies' in package_data:
                    dependencies.update(package_data['devDependencies'])
            except Exception as e:
                print(f"Warning: Could not parse package.json: {e}")
        
        # Check for bower.json
        bower_json_path = self.angular_root / 'bower.json'
        if bower_json_path.exists():
            try:
                with open(bower_json_path, 'r', encoding='utf-8') as f:
                    bower_data = json.load(f)
                    
                if 'dependencies' in bower_data:
                    dependencies.update(bower_data['dependencies'])
                if 'devDependencies' in bower_data:
                    dependencies.update(bower_data['devDependencies'])
            except Exception as e:
                print(f"Warning: Could not parse bower.json: {e}")
        
        # Map of known Angular libraries to React/Next.js equivalents
        self.dependency_mapping = {
            # UI libraries
            'angular-bootstrap': 'react-bootstrap',
            'bootstrap': 'bootstrap',
            'angular-material': '@mui/material',
            'material-design-icons': '@mui/icons-material',
            'font-awesome': '@fortawesome/react-fontawesome',
            'ng-table': 'react-table',
            'angular-ui-grid': 'react-data-grid',
            'ui-select': 'react-select',
            'angular-ui-select': 'react-select',
            'select2': 'react-select',
            'angular-moment': 'moment',
            'momentjs': 'moment',
            'angular-toastr': 'react-toastify',
            'toastr': 'react-toastify',
            'angular-ui-sortable': 'react-beautiful-dnd',
            'angular-ui-router': 'next/navigation',
            'angular-ui-calendar': '@fullcalendar/react',
            'fullcalendar': '@fullcalendar/react',
            'angular-ui-tree': 'react-sortable-tree',
            'angular-file-upload': 'react-dropzone',
            'ng-file-upload': 'react-dropzone',
            'textAngular': 'react-quill',
            'angular-ui-utils': '',  # No direct equivalent
            'ocLazyLoad': '',  # Handled by Next.js
            
            # State management
            'ngstorage': 'zustand',
            'angular-local-storage': 'zustand',
            
            # HTTP libraries
            'angular-resource': 'axios',
            'ngResource': 'axios',
            
            # Animation
            'ngAnimate': 'framer-motion',
            'angular-animate': 'framer-motion',
            
            # Data visualization
            'angular-flot': 'recharts',
            'angular-chart.js': 'recharts',
            'chartjs': 'recharts',
            'd3': 'd3',
            'angular-rickshaw': 'recharts',
            'ng-chartjs': 'recharts',
            'angularjs-charts': 'recharts',
            
            # Form handling
            'angular-formly': 'react-hook-form',
            'ng-form': 'react-hook-form',
            'angular-form': 'react-hook-form',
            
            # Utilities
            'lodash': 'lodash',
            'underscore': 'lodash',
            'jquery': '',  # Not needed in React
            'jquery-ui': 'react-dnd',
        }
        
        # Identify required React libraries based on Angular dependencies
        self.react_dependencies = {
            'next': '^14.0.0',
            'react': '^18.2.0',
            'react-dom': '^18.2.0',
            'axios': '^1.6.0',
        }
        
        for dep_name in dependencies.keys():
            # Normalize dependency name (remove @ versions and organizations)
            clean_name = dep_name.split('@')[0]
            
            # Check if we have a mapping for this dependency
            if clean_name in self.dependency_mapping and self.dependency_mapping[clean_name]:
                react_dep = self.dependency_mapping[clean_name]
                # Add to React dependencies with a recent version
                self.react_dependencies[react_dep] = '^1.0.0'  # Default version
                print(f"Mapped {clean_name} to {react_dep}")
        
        # Check for specific UI frameworks
        if any(lib in dependencies for lib in ['bootstrap', 'angular-bootstrap']):
            self.react_dependencies['react-bootstrap'] = '^2.9.0'
            self.react_dependencies['bootstrap'] = '^5.3.2'
            print("Added Bootstrap and React-Bootstrap")
        
        if any(lib in dependencies for lib in ['angular-material', 'material-design-lite']):
            self.react_dependencies['@mui/material'] = '^5.14.18'
            self.react_dependencies['@mui/icons-material'] = '^5.14.18'
            self.react_dependencies['@emotion/react'] = '^11.11.1'
            self.react_dependencies['@emotion/styled'] = '^11.11.0'
            print("Added Material UI")
        
        # Add state management if needed
        if any(lib in dependencies for lib in ['ngstorage', 'angular-local-storage']):
            self.react_dependencies['zustand'] = '^4.4.6'
            print("Added Zustand for state management")
        
        print(f"Identified {len(self.react_dependencies)} React dependencies based on Angular libraries")
        
    def update_package_json(self) -> None:
        """
        Update package.json with dependencies based on Angular libraries
        """
        print("Updating package.json...")
        
        package_json_path = self.nextjs_root / 'package.json'
        
        try:
            # Read existing package.json
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # Update dependencies
            package_data['dependencies'].update(self.react_dependencies)
            
            # Add development dependencies
            if 'sass' in self.react_dependencies:
                package_data['devDependencies']['sass'] = self.react_dependencies['sass']
                del self.react_dependencies['sass']
            
            # Write updated package.json
            with open(package_json_path, 'w', encoding='utf-8') as f:
                json.dump(package_data, f, indent=2)
            
            print(f"Updated package.json with {len(self.react_dependencies)} dependencies")
        except Exception as e:
            print(f"Warning: Could not update package.json: {e}")
            
    def analyze_codebase(self) -> None:
        """
        Analyze Angular codebase or load from analysis file
        """
        print("Analyzing Angular codebase...")
        
        # Try to load pre-generated analysis data
        if self.analysis_file and self.load_analysis_data():
            print(f"Successfully loaded analysis data from {self.analysis_file}")
            
            # Still need to analyze dependencies
            self.analyze_dependencies()
            return
            
        print("No valid analysis file found. Performing direct analysis.")
        with open('scripts/admin-analysis-report.json', 'r') as file:
          data = json.load(file)
        # Fallback to direct analysis if loading fails
        self.routes = data.get('routes', [])
        self.controllers = data.get('controllers', {})
        # self.analyze_templates()
        # print('routes', self.routes)
        # print('controllers', self.controllers)
        return
        
        # Use our new modular analyzer
        try:
            analyzer = AngularCodebaseAnalyzer(str(self.angular_root))
            analyzer.analyze_codebase()
            report = analyzer.generate_analysis_report()
            
            # Copy data from the report to our data structures
            self.routes = report["routes"]
            self.controllers = report["controllers"]
            self.templates = report["templates"]
            self.services = report["services"]
            self.directives = report["directives"]
            
            # Save the analysis report
            output_file = 'scripts/admin-analysis-report.json'
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Analysis saved to {output_file}")
            
        except Exception as e:
            print(f"Error analyzing codebase: {e}")
            traceback.print_exc()
    
    def _get_parent_directory(self, route: Dict, routes: List[Dict]) -> str:
        """
        Get the parent directory for a given route
        """
        route_name = route['name']
        if route_name is not None and "." in route_name:
            # Split the name by dots
            name_parts = route_name.split('.')
            # Remove the last part to get the parent name
            parent_name = '.'.join(name_parts[:-1])
            
            # If parent name is empty, return empty string
            if not parent_name:
                return ""
            
            # Find the parent route
            for r in routes:
                if r['name'] == parent_name:
                    return r['url'] if r['url'] else ""
            return ""
        else:
            return ""
    
    def update_path_for_dynamic_routes(self, directory: str) -> str:
      # Remove query parameters if present
      if '?' in directory:
        directory = directory.split('?')[0]
      
      directory = directory.split('/')
      updated_directory = []
      for d in directory:
        if d.startswith(':'):
          updated_directory.append(f'[{d[1:]}]')
        else:
          updated_directory.append(d)
      return "/".join(updated_directory)
    
    def generate_next_pages(self) -> None:
        """
        Generate Next.js pages based on Angular routes
        """
        print("Generating Next.js pages...")
        
        with open('scripts/admin-analysis-report.json', 'r') as file:
          data = json.load(file)

        # Access the specific key
        routes = data.get('routes', [])
        
        for route in routes:
            if not route['url'] or not route['name'].startswith('app.models'):
                continue
            directory = route['url']
            if route['url'].startswith('^'):
                directory = directory[1:]
            else:
              parent_directory = self._get_parent_directory(route, routes)
              directory = parent_directory + directory
              if directory.startswith('/'):
                directory = directory[1:]
            
            directory = self.update_path_for_dynamic_routes(directory)
            
            if directory.startswith('^'):
              directory = directory[1:]
            print('directory', directory)
            
            # Create directory if it doesn't exist
            try:
              # Ensure directory doesn't start with a slash to avoid absolute path issues
              clean_directory = directory.lstrip('/')
              
              # Add path to the route object
              route['path'] = clean_directory
              
              output_dir = self.nextjs_root / 'src' / 'app' / clean_directory
              os.makedirs(output_dir, exist_ok=True)
              
              self._generate_page_for_route(route)
              # Create an empty page.tsx file
              # output_file = output_dir / 'page.tsx'
              # if not os.path.exists(output_file):
              #   open(output_file, 'w').close()
            except Exception as e:
              print(f"Error creating directory for route {directory}: {str(e)}")
        
        # Write the updated data back to the JSON file
        try:
            with open('scripts/admin-analysis-report.json', 'w') as json_file:
                json.dump(data, json_file, indent=2)
            print(f"Successfully updated routes with path property in scripts/admin-analysis-report.json")
        except Exception as e:
            print(f"Error writing updated data to JSON: {str(e)}")
        
        return
    
    def _generate_page_for_route(self, route: Dict) -> None:
        """
        Generate a React page component for a specific route.
        """

        controller_name = route.get('controller', '')
        template_url = route.get('templateUrl', '')
        url = route.get('url', '')
        component_name = self._route_to_component_name(url)
        
        # Find the controller file path from our controllers dictionary
        controller_path = self.controllers.get(controller_name, "")
        # Find the template file path from our templates dictionary
        template_path = self.templates.get(template_url, "")
        # print('---------------------------------')
        # print('controller_path', controller_path)
        # print('template_path', template_path)
        controller_code = self._read_file(controller_path) if controller_path else ""
        template_code = self._read_file(template_path) if template_path else ""
        
        if not controller_code and not template_code:
            print(f"Warning: No controller or template code found for route {url}")
            return
        
        print(f"Generating component for route: {url}")
        
        # Prepare the prompt for LLM conversion
        prompt = prompts._get_generate_page_for_route_prompt(controller_code, template_code, component_name)
        
        # Use convert_with_llm to perform the conversion
        react_component = self.convert_with_llm(prompt, "controller_template", "react_component")
        
        if not react_component:
            print(f"Warning: Failed to convert code for {url}. Creating a default component instead.")
            return
        
        output_dir = self.nextjs_root / 'src' / 'app' / route['path']
        output_file = output_dir / 'page.tsx'
        print('---------------------------------')
        print('react_component', react_component)
        # Write the component to the file
        output_file.write_text(react_component)
        print(f"Generated React component: {output_file}")
    
    def _generate_default_component(self, component_name: str, url: str) -> str:
        """
        Generate a default React component when conversion fails
        
        Args:
            component_name: The name for the component
            url: The route URL for API calls
            
        Returns:
            Default component code as string
        """
        # Use regular string concatenation to avoid f-string issues with JSX template literals
        clean_url = url.lstrip('/')
        
        template = "'use client';\n\n"
        template += 'import { useState, useEffect } from "react";\n'
        template += 'import { useRouter } from "next/navigation";\n\n'
        
        template += f'interface {component_name}Props {{\n'
        template += '  // Define props here\n'
        template += '}\n\n'
        
        template += f'export default function {component_name}(props: {component_name}Props) {{\n'
        template += '  const router = useRouter();\n'
        template += '  const [loading, setLoading] = useState(true);\n'
        template += '  const [data, setData] = useState<any>(null);\n'
        template += '  const [error, setError] = useState<string | null>(null);\n\n'
        
        template += '  useEffect(() => {\n'
        template += '    async function fetchData() {\n'
        template += '      try {\n'
        template += '        setLoading(true);\n'
        template += f'        // Replace with actual API call\n'
        template += f'        const response = await fetch("/api/{clean_url}");\n'
        template += '        \n'
        template += '        if (!response.ok) {\n'
        template += '          throw new Error("API request failed with status " + response.status);\n'
        template += '        }\n'
        template += '        \n'
        template += '        const result = await response.json();\n'
        template += '        setData(result);\n'
        template += '        setError(null);\n'
        template += '      } catch (err) {\n'
        template += '        console.error("Error fetching data:", err);\n'
        template += '        setError("Failed to load data. Please try again later.");\n'
        template += '      } finally {\n'
        template += '        setLoading(false);\n'
        template += '      }\n'
        template += '    }\n\n'
        
        template += '    fetchData();\n'
        template += '  }, []);\n\n'
        
        template += '  if (loading) {\n'
        template += '    return (\n'
        template += '      <div className="flex justify-center items-center min-h-screen">\n'
        template += '        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>\n'
        template += '      </div>\n'
        template += '    );\n'
        template += '  }\n\n'
        
        template += '  if (error) {\n'
        template += '    return (\n'
        template += '      <div className="min-h-screen flex flex-col items-center justify-center p-4">\n'
        template += '        <div className="bg-red-50 border-l-4 border-red-500 p-4 w-full max-w-md">\n'
        template += '          <div className="flex">\n'
        template += '            <div className="flex-shrink-0">\n'
        template += '              <svg className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">\n'
        template += '                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />\n'
        template += '              </svg>\n'
        template += '            </div>\n'
        template += '            <div className="ml-3">\n'
        template += '              <p className="text-sm text-red-700">\n'
        template += '                {error}\n'
        template += '              </p>\n'
        template += '            </div>\n'
        template += '          </div>\n'
        template += '        </div>\n'
        template += '        <button \n'
        template += '          onClick={() => window.location.reload()} \n'
        template += '          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"\n'
        template += '        >\n'
        template += '          Try Again\n'
        template += '        </button>\n'
        template += '      </div>\n'
        template += '    );\n'
        template += '  }\n\n'
        
        template += '  return (\n'
        template += '    <div className="p-8">\n'
        template += f'      <h1 className="text-3xl font-bold mb-6">{component_name}</h1>\n'
        template += '      \n'
        template += '      <div className="bg-white shadow rounded-lg p-6">\n'
        template += '        <pre className="bg-gray-100 p-4 rounded overflow-x-auto">\n'
        template += '          {JSON.stringify(data, null, 2)}\n'
        template += '        </pre>\n'
        template += '      </div>\n'
        template += '    </div>\n'
        template += '  );\n'
        template += '}'
        
        return template
    
    def convert_with_llm(self, source_code: str, source_type: str, target_type: str) -> str:
        """
        Use LLM to convert code from Angular to Next.js
        
        Args:
            source_code: The source code or prompt to convert
            source_type: Type of source code (controller, template, service, controller_template)
            target_type: Target format (React component, API route, etc.)
            
        Returns:
            Converted code as string
        """
        if not self.api_key:
            print("Warning: No OpenRouter API key provided. Skipping LLM-based conversion.")
            return None
            
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://localhost",  # Required for OpenRouter API
                "X-Title": "Angular to Next.js Migration Tool"  # Optional for OpenRouter API
            }
            
            # Create a system prompt that guides the LLM to properly convert the code
            system_prompt = prompts._get_system_prompt()
            
            # Generate a user prompt that is specific to the conversion type
            user_prompt = source_code
            
            # For different source types, we might want to customize the prompt
            if source_type == "controller" and target_type == "api_route":
                user_prompt = prompts._get_user_controller_prompt(source_code)
            elif source_type == "service" and target_type == "react_hooks":
                user_prompt = prompts._get_user_service_prompt(source_code)
            
            # For controller_template combinations, the source_code is already a complete prompt
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": DEFAULT_TEMPERATURE,
                "max_tokens": 8000
            }
            
            print(f"Sending request to {self.model} for {source_type} to {target_type} conversion...")
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                converted_code = result["choices"][0]["message"]["content"]
                
                # Clean the response to extract just the code
                cleaned_code = self._extract_code_from_response(converted_code)
                print(f"Successfully converted {source_type} to {target_type}")
                return cleaned_code
            else:
                print(f"Error calling OpenRouter API: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"Error in LLM conversion: {e}")
            return None

    def _extract_code_from_response(self, response: str) -> str:
        """
        Extract code from LLM response, removing any markdown formatting or explanatory text
        """
        # First, try to extract code from markdown code blocks with various language identifiers
        code_block_pattern = r'```(?:jsx|tsx|javascript|typescript|js|ts|react|nextjs|next\.js)?(.+?)```'
        code_blocks = re.findall(code_block_pattern, response, re.DOTALL)
        
        if code_blocks:
            # Join all code blocks if multiple are found
            clean_code = '\n\n'.join(block.strip() for block in code_blocks)
            # Remove any language identifiers that might have been included
            clean_code = re.sub(r'^(jsx|tsx|javascript|typescript|js|ts|react|nextjs|next\.js)\s*\n', '', clean_code, flags=re.MULTILINE)
            return clean_code
        
        # If no code blocks, try to identify pure code sections
        # Remove common prefixes that might indicate explanatory text
        lines = response.split('\n')
        cleaned_lines = []
        in_explanation = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip explanatory text markers
            if any(marker in stripped.lower() for marker in [
                "here's the", "here is the", "converting", "i've converted", 
                "this is the", "code implementation", "explanation:", "note:",
                "implementation of", "let me", "the react", "the next.js",
                "as requested", "here you go", "this code", "following is",
                "this component", "this implementation", "i've created",
                "now let's", "let me explain", "i'll create"
            ]):
                in_explanation = True
                continue
                
            # Skip empty lines at the beginning
            if not cleaned_lines and not stripped:
                continue
                
            # If we hit imports or actual code, we're no longer in explanation
            if (stripped.startswith('import ') or 
                stripped.startswith('export ') or 
                stripped.startswith('function ') or
                stripped.startswith('const ') or 
                stripped.startswith('class ') or
                stripped.startswith('interface ') or
                stripped.startswith('type ') or
                stripped.startswith('let ') or
                stripped.startswith('var ') or
                stripped.startswith('async ') or
                stripped.startswith('return ') or
                stripped.startswith('<') or  # JSX/HTML opening tag
                stripped.startswith('use ')):  # React 'use client' directive
                in_explanation = False
                
            if not in_explanation:
                cleaned_lines.append(line)
        
        # If we have extracted any code this way
        if cleaned_lines:
            code = '\n'.join(cleaned_lines)
            # Remove any trailing explanation text
            if '//' in code or '/*' in code:
                # Keep essential TODOs but remove explanatory comments
                comment_lines = []
                code_lines = code.split('\n')
                for i, line in enumerate(code_lines):
                    line_stripped = line.strip()
                    # Check if this is an explanatory comment, not a TODO
                    if (('//' in line and not 'TODO' in line) or 
                        ('/*' in line and not 'TODO' in line) or 
                        ('*' == line_stripped.lstrip()) or
                        ('*/' in line)):
                        if not any(code_keyword in line_stripped for code_keyword in ['const', 'let', 'var', 'function', 'class', 'import', 'export', 'return', '<', '>']):
                            comment_lines.append(i)
                
                # Remove comment lines
                code_lines = [line for i, line in enumerate(code_lines) if i not in comment_lines]
                code = '\n'.join(code_lines)
            
            return code
            
        # Last resort: just return the response as is, assuming it's just code
        return response.strip()
        
    def _clean_jsx_component(self, component_code: str, component_name: str) -> str:
        """
        Clean and process a JSX/TSX component to ensure it's properly formatted for Next.js App Router
        
        Args:
            component_code: The React component code
            component_name: The name of the component
            
        Returns:
            Cleaned component code
        """
        # First strip markdown blocks completely if they exist
        component_code = self._extract_code_from_response(component_code)
        
        # Add 'use client' directive if not already present and component has client-side hooks
        if ('useState' in component_code or 'useEffect' in component_code or 'useRouter' in component_code) and not "'use client'" in component_code and not '"use client"' in component_code:
            component_code = "'use client';\n\n" + component_code
        
        # Check if we need to add TypeScript typing
        has_typescript = (
            'interface ' in component_code or 
            'type ' in component_code or 
            ': React.' in component_code or 
            '<any>' in component_code or 
            ': string' in component_code
        )
        
        if not has_typescript:
            # Add basic TypeScript types if missing
            # Find function component declaration
            func_pattern = r'(export\s+(?:default\s+)?function\s+' + component_name + r'\s*\()'
            func_match = re.search(func_pattern, component_code)
            
            if func_match:
                # Add type to props parameter
                if 'props' in component_code and not 'props: ' in component_code:
                    type_replacement = f"{func_match.group(1)}props: {component_name}Props"
                    component_code = re.sub(func_pattern, type_replacement, component_code)
                    
                    # Add interface definition if not present
                    if not f"interface {component_name}Props" in component_code:
                        interface_def = f"interface {component_name}Props {{\n  // Define props here\n}}\n\n"
                        # Insert after imports
                        import_pattern = r'(import .+;\n)\s*'
                        last_import = re.search(import_pattern, component_code, re.DOTALL)
                        if last_import:
                            component_code = re.sub(import_pattern, f"\\1\n{interface_def}", component_code, count=1)
                        else:
                            component_code = interface_def + component_code
        
        # Fix imports
        # Check for React import
        if 'useState' in component_code or 'useEffect' in component_code or 'useRef' in component_code:
            if not 'import React' in component_code and not "import { " in component_code:
                hooks = []
                if 'useState' in component_code: hooks.append('useState')
                if 'useEffect' in component_code: hooks.append('useEffect')
                if 'useRef' in component_code: hooks.append('useRef')
                react_import = f"import {{ {', '.join(hooks)} }} from 'react';\n"
                component_code = react_import + component_code
        
        # Check for Next.js imports
        if 'useRouter' in component_code and not 'import { useRouter }' in component_code:
            router_import = "import { useRouter } from 'next/navigation';\n"
            component_code = router_import + component_code
            
        if '<Link' in component_code and not 'import Link' in component_code:
            link_import = "import Link from 'next/link';\n"
            component_code = link_import + component_code
            
        if '<Image' in component_code and not 'import Image' in component_code:
            image_import = "import Image from 'next/image';\n"
            component_code = image_import + component_code
            
        # Make sure component has default export
        if not 'export default' in component_code:
            if f"function {component_name}" in component_code:
                # Find the function declaration without export
                func_pattern = r'function\s+' + component_name
                func_match = re.search(func_pattern, component_code)
                if func_match:
                    component_code = component_code.replace(
                        func_match.group(0), 
                        f"export default {func_match.group(0)}"
                    )
            else:
                # Add export at the end
                component_code += f"\n\nexport default {component_name};"
        
        return component_code
    
    def _route_to_component_name(self, url: str) -> str:
        """
        Convert a route URL to a proper React component name
        
        Args:
            url: Route URL (e.g., '/users/:id/profile')
            
        Returns:
            Component name in PascalCase (e.g., 'UserProfile')
        """
        # Remove parameters (anything with colon)
        url = re.sub(r':[^/]+', '', url)
        
        # Remove special characters, split by delimiters
        parts = re.split(r'[^a-zA-Z0-9]', url)
        
        # Filter out empty parts and convert to PascalCase
        component_name = ''.join(part.capitalize() for part in parts if part)
        
        # If the component name is empty, use a default name
        if not component_name:
            component_name = 'Home'
            
        # Add 'Page' suffix if it doesn't end with a common component suffix
        if not any(component_name.endswith(suffix) for suffix in ['Page', 'View', 'Component', 'Screen']):
            component_name += 'Page'
            
        return component_name
    
    def _read_file(self, file_path: str) -> str:
        """
        Read the contents of a file
        
        Args:
            file_path: Path to the file (relative to angular_root or absolute)
            
        Returns:
            File contents as string or empty string if file not found
        """
        if not file_path:
            return ""
            
        try:
            # Handle both absolute and relative paths
            if os.path.isabs(file_path):
                path = Path(file_path)
            else:
                path = self.angular_root / file_path
                
            # Check if file exists
            if not path.exists():
                print(f"Warning: File not found: {path}")
                return ""
                
            # Read and return file contents
            return path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return ""
    
    def generate_api_routes(self) -> None:
        """
        Generate API routes based on services found in the Angular project
        """
        print("Generating API routes...")
        
        # Create the API directory
        api_dir = self.nextjs_root / 'app' / 'api'
        api_dir.mkdir(exist_ok=True, parents=True)
        
        # Create a sample API route
        route_dir = api_dir / 'sample'
        route_dir.mkdir(exist_ok=True)
        
        route_content = """
export async function GET() {
  return Response.json({ message: 'Hello from API' });
}
"""
        route_file = route_dir / 'route.ts'
        route_file.write_text(route_content)
        
        # Add a generated notice
        self._add_generated_notice(route_file)
        
        # Create helper for API utils
        api_utils_dir = self.nextjs_root / 'lib' / 'api'
        api_utils_dir.mkdir(exist_ok=True, parents=True)
        
        api_utils_content = """/**
 * API utility functions for handling requests and responses
 */

/**
 * Custom error for API responses
 */
export class ApiError extends Error {
  status: number;
  
  constructor(message: string, status: number = 500) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/**
 * Helper to handle API errors
 */
export async function handleApiError(error: unknown) {
  console.error('[API Error]', error);
  
  if (error instanceof ApiError) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: error.status,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
  
  return new Response(
    JSON.stringify({ error: 'Internal Server Error' }),
    { 
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    }
  );
}

/**
 * Parse request body as JSON with error handling
 */
export async function parseRequestBody(request: Request) {
  try {
    return await request.json();
  } catch (error) {
    throw new ApiError('Invalid JSON in request body', 400);
  }
}

/**
 * Validate required fields in a request
 */
export function validateRequiredFields(data: Record<string, any>, requiredFields: string[]) {
  const missingFields = requiredFields.filter(field => !data[field]);
  
  if (missingFields.length > 0) {
    throw new ApiError(
      `Missing required fields: ${missingFields.join(', ')}`, 
      400
    );
  }
  
  return true;
}
"""
        
        api_utils_file = api_utils_dir / 'utils.ts'
        api_utils_file.write_text(api_utils_content)
        
        # Add a service authentication helper for protected routes
        auth_middleware_content = """/**
 * Middleware for API authentication
 */
import { NextRequest } from 'next/server';
import { ApiError } from '@/lib/api/utils';

/**
 * Verify authentication for protected API routes
 */
export async function verifyAuth(request: NextRequest) {
  const token = request.headers.get('Authorization')?.split('Bearer ')[1];
  
  if (!token) {
    throw new ApiError('Unauthorized - Missing token', 401);
  }
  
  // TODO: Implement actual token validation here
  // This is a placeholder for JWT validation or other auth mechanisms
  
  return { userId: 'user_id_placeholder' };
}
"""
        auth_middleware_file = api_utils_dir / 'auth.ts'
        auth_middleware_file.write_text(auth_middleware_content)
        
        # Process each Angular service to generate an API route
        created_routes = 0
        
        for service_name, service_path in self.services.items():
            try:
                # Skip common or utility services
                if any(name in service_name.lower() for name in [
                    'http', 'util', 'common', 'auth', 'helper', 'service'
                ]):
                    continue
                
                # Convert service name to kebab-case for API path
                api_name = re.sub(r'Service$', '', service_name)  # Remove Service suffix
                api_name = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', api_name).lower()  # Convert to kebab-case
                
                # Read service file
                with open(service_path, 'r', encoding='utf-8') as f:
                    service_content = f.read()
                
                # Create route directory
                service_route_dir = api_dir / api_name
                service_route_dir.mkdir(exist_ok=True, parents=True)
                
                # Convert service to API routes
                route_content = self._convert_service_to_api_route(service_name, service_content, api_name)
                
                # Write route file
                route_file = service_route_dir / 'route.ts'
                route_file.write_text(route_content)
                
                # Add a generated notice
                self._add_generated_notice(route_file)
                
                created_routes += 1
                print(f"Created API route for {service_name}: {route_file}")
            except Exception as e:
                print(f"Warning: Could not convert service {service_name}: {e}")
                traceback.print_exc()
                
                # Generate a default API handler
                self._generate_default_api_handler(service_name, api_name, api_dir)
        
        print(f"Generated {created_routes} API routes in {api_dir}")

    def _convert_service_to_api_route(self, service_name: str, service_content: str, api_name: str) -> str:
        """
        Convert an Angular service to a Next.js API route
        
        Args:
            service_name: Name of the Angular service
            service_content: Service file content
            api_name: Kebab-case name for the API route
            
        Returns:
            API route code as string
        """
        # Prepare the prompt for conversion
        prompt = prompts._get_api_service_prompt(service_content, service_name, api_name)
        
        # Use convert_with_llm to perform the conversion
        api_route = self.convert_with_llm(prompt, "service", "api_route")
        
        # If conversion failed, generate a default route
        if not api_route:
            api_route = """
/**
 * Default API route
 */

export async function GET(request: Request) {
  return Response.json({ message: 'API endpoint not yet implemented' });
}

export async function POST(request: Request) {
  return new Response('Method not implemented', { status: 501 });
}
"""
        
        return api_route
    
    def _generate_default_api_handler(self, service_name: str, api_name: str, api_dir: Path) -> None:
        """
        Generate a default API handler when conversion fails
        
        Args:
            service_name: The name of the original Angular service
            api_name: The kebab-case name for the API route
            api_dir: The directory where API routes are stored
        """
        try:
            # Create route directory if it doesn't exist
            route_dir = api_dir / api_name
            route_dir.mkdir(exist_ok=True, parents=True)
            
            # Generate default route content with a notice about the original service
            route_content = f"""/**
 * Default API handler for {service_name}
 * 
 * This file was auto-generated as a placeholder when the original
 * Angular service could not be automatically converted.
 * 
 * Original service: {service_name}
 */

import {{ handleApiError }} from '@/lib/api/utils';

export async function GET(request: Request) {{
  try {{
    // TODO: Implement proper data retrieval based on the original service
    return Response.json({{ 
      message: 'This is a placeholder API endpoint',
      endpoint: '{api_name}',
      original_service: '{service_name}'
    }});
  }} catch (error) {{
    return handleApiError(error);
  }}
}}

export async function POST(request: Request) {{
  try {{
    // TODO: Implement proper data handling based on the original service
    return Response.json({{ 
      success: true, 
      message: 'Data received but not processed'
    }});
  }} catch (error) {{
    return handleApiError(error);
  }}
}}
"""
            
            # Write route file
            route_file = route_dir / 'route.ts'
            route_file.write_text(route_content)
            
            # Add a generated notice
            self._add_generated_notice(route_file)
            
            print(f"Generated default API handler for {service_name} at {route_file}")
        except Exception as e:
            print(f"Error generating default API handler for {service_name}: {e}")
            # No further fallback here as this is already the fallback mechanism
    
    def _add_generated_notice(self, file_path: Path) -> None:
        """
        Add a generated notice to the top of the file
        
        Args:
            file_path: Path to the file
        """
        # Read the file contents
        file_contents = file_path.read_text(encoding='utf-8')
        
        # Add generated notice
        generated_notice = """/**
 * This file was auto-generated by the Angular to Next.js Migration Tool
 * 
 * Please do not modify this file directly.
 * Any changes made will be overwritten the next time the tool runs.
 */
"""
        new_file_contents = generated_notice + file_contents
        
        # Write the new file contents back to the file
        file_path.write_text(new_file_contents)

    def copy_assets_and_styles(self) -> None:
        """
        Copy assets (images, fonts) and styles from Angular to Next.js project
        preserving the directory structure where appropriate
        """
        print("Copying assets and styles...")
        
        # Create public directory for static assets
        public_dir = self.nextjs_root / 'public'
        public_dir.mkdir(exist_ok=True, parents=True)
        
        # Create images directory in public
        images_dir = public_dir / 'images'
        images_dir.mkdir(exist_ok=True, parents=True)
        
        # Copy images
        if (self.angular_root / 'app' / 'images').exists():
            print("Copying images...")
            self._copy_directory(self.angular_root / 'app' / 'images', images_dir)
        
        # Copy from assets directory if it exists
        if (self.angular_root / 'app' / 'assets').exists():
            print("Copying assets...")
            assets_dir = public_dir / 'assets'
            assets_dir.mkdir(exist_ok=True, parents=True)
            self._copy_directory(self.angular_root / 'app' / 'assets', assets_dir)
        
        # Copy fonts to public directory
        if (self.angular_root / 'app' / 'fonts').exists():
            print("Copying fonts...")
            fonts_dir = public_dir / 'fonts'
            fonts_dir.mkdir(exist_ok=True, parents=True)
            self._copy_directory(self.angular_root / 'app' / 'fonts', fonts_dir)
            
        # Create styles directory for SCSS/CSS files
        styles_src_dir = self.nextjs_root / 'src' / 'styles'
        styles_src_dir.mkdir(exist_ok=True, parents=True)
        
        # Copy SCSS files if they exist
        if (self.angular_root / 'app' / 'sass').exists():
            print("Copying SCSS files...")
            self._copy_directory(self.angular_root / 'app' / 'sass', styles_src_dir)
        
        # Copy CSS files if they exist
        if (self.angular_root / 'app' / 'styles').exists():
            print("Copying CSS files...")
            self._copy_directory(self.angular_root / 'app' / 'styles', styles_src_dir)
            
        # Create a main style import file
        self._create_style_imports(styles_src_dir)
        
        print("Assets and styles copying complete.")
        
    def _copy_directory(self, source_dir: Path, target_dir: Path) -> None:
        """
        Recursively copy a directory and its contents from source to target
        
        Args:
            source_dir: Source directory path
            target_dir: Target directory path
        """
        # Ensure the target directory exists
        target_dir.mkdir(exist_ok=True, parents=True)
        
        # Copy all files from source to target
        for item in source_dir.iterdir():
            if item.is_file():
                # Copy file
                shutil.copy2(item, target_dir / item.name)
            elif item.is_dir():
                # Recursively copy subdirectory
                self._copy_directory(item, target_dir / item.name)
                
    def _create_style_imports(self, styles_dir: Path) -> None:
        """
        Create a main SCSS file that imports all other SCSS files
        
        Args:
            styles_dir: Directory containing style files
        """
        # Check if there are any SCSS files
        scss_files = list(styles_dir.glob('**/*.scss'))
        css_files = list(styles_dir.glob('**/*.css'))
        
        if scss_files:
            # Create a main.scss file
            main_scss = styles_dir / 'main.scss'
            
            # Generate import statements for each SCSS file
            imports = []
            for file in scss_files:
                # Get relative path from styles_dir
                rel_path = file.relative_to(styles_dir)
                # Create import statement with path
                # Convert to posix path for consistent forward slashes
                path_str = str(rel_path.with_suffix('')).replace('\\', '/')
                imports.append(f'@import "{path_str}";')
            
            # Join import statements and write to file
            main_scss.write_text('\n'.join(imports))
            print(f"Created {main_scss} with imports for {len(scss_files)} SCSS files")
            
        if css_files:
            # For CSS files, create a global.css
            global_css = styles_dir / 'globals.css'
            
            # Open each CSS file and concatenate
            css_content = []
            for file in css_files:
                if file != global_css:  # Avoid including the file we're creating
                    file_content = file.read_text(encoding='utf-8')
                    css_content.append(f"/* From {file.name} */")
                    css_content.append(file_content)
            
            # Write combined content to globals.css
            if css_content:
                global_css.write_text('\n\n'.join(css_content))
                print(f"Created {global_css} with content from {len(css_files)} CSS files")
    
    def setup_next_project(self) -> None:
        """
        Set up the basic Next.js project structure and configuration files
        """
        print("Setting up Next.js project structure...")
        
        # Create src directory
        src_dir = self.nextjs_root / 'src'
        src_dir.mkdir(exist_ok=True, parents=True)
        
        # Create app directory
        app_dir = src_dir / 'app'
        app_dir.mkdir(exist_ok=True, parents=True)
        
        # Create components directory
        components_dir = src_dir / 'components'
        components_dir.mkdir(exist_ok=True, parents=True)
        
        # Create lib directory for utilities
        lib_dir = src_dir / 'lib'
        lib_dir.mkdir(exist_ok=True, parents=True)
        
        # Create package.json
        package_json_content = """{
  "name": "next-app-migration",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "sass": "^1.69.0"
  },
  "devDependencies": {
    "@types/node": "^20.8.9",
    "@types/react": "^18.2.33",
    "@types/react-dom": "^18.2.14",
    "eslint": "^8.52.0",
    "eslint-config-next": "^14.0.0",
    "typescript": "^5.2.2"
  }
}"""
        (self.nextjs_root / 'package.json').write_text(package_json_content)
        
        # Create tsconfig.json
        tsconfig_json_content = """{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}"""
        (self.nextjs_root / 'tsconfig.json').write_text(tsconfig_json_content)
        
        # Create next.config.js
        next_config_content = """/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  sassOptions: {
    includePaths: ['./src/styles'],
  },
  images: {
    domains: [],
  },
};

module.exports = nextConfig;"""
        (self.nextjs_root / 'next.config.js').write_text(next_config_content)
        
        # Create base app files
        layout_content = """'use client';

import './globals.css';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Migrated App</title>
      </head>
      <body>{children}</body>
    </html>
  );
}"""
        (app_dir / 'layout.tsx').write_text(layout_content)
        
        # Create globals.css
        globals_css_content = """html,
body {
  padding: 0;
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen,
    Ubuntu, Cantarell, Fira Sans, Droid Sans, Helvetica Neue, sans-serif;
}

a {
  color: inherit;
  text-decoration: none;
}

* {
  box-sizing: border-box;
}

@media (prefers-color-scheme: dark) {
  html {
    color-scheme: dark;
  }
  body {
    color: white;
    background: black;
  }
}"""
        (app_dir / 'globals.css').write_text(globals_css_content)
        
        # Create root page.tsx
        page_content = """'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  
  useEffect(() => {
    // Redirect to main app route (typically dashboard)
    router.push('/dashboard');
  }, [router]);
  
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      <p className="mt-4">Loading application...</p>
    </div>
  );
}"""
        (app_dir / 'page.tsx').write_text(page_content)
        
        print("Next.js project structure set up successfully.")
    
    def migrate(self) -> None:
        """
        Run the full migration process
        """
        print(f"Starting migration from {self.angular_root} to {self.nextjs_root}...")
        
        # Set up Next.js project structure
        # self.setup_next_project()
        
        # # Analyze or load Angular codebase data
        self.analyze_codebase()
        # # Update package.json with dependencies
        # self.update_package_json()
        
        # # Copy assets and styles
        # self.copy_assets_and_styles()
        
        # Generate Next.js pages
        self.generate_next_pages()
        
        return
        
        # Generate API routes
        self.generate_api_routes()
        
        # Convert directives to components
        self.convert_directives_to_components()
        
        # Generate React hooks from services
        self.generate_react_hooks()
        
        print(f"Migration completed successfully! Next.js project is available at {self.nextjs_root}")
        
        # Print a success message with next steps
        print("\nNext steps:")
        print("1. Navigate to the Next.js project directory: cd", self.nextjs_root)
        print("2. Install dependencies: npm install")
        print("3. Start the development server: npm run dev")
        print("4. Open http://localhost:3000 in your browser")
        print("\nNote: The migration is automated but may require manual adjustments for complex features.")

    def convert_directives_to_components(self) -> None:
        """
        Convert Angular directives to React components
        """
        print("Converting directives to React components...")
        
        # Create components directory
        components_dir = self.nextjs_root / 'src' / 'components'
        components_dir.mkdir(exist_ok=True, parents=True)
        
        # Process each directive
        converted_count = 0
        
        for directive_name, directive_path in self.directives.items():
            try:
                # Convert directive name from camelCase to PascalCase
                component_name = ''.join(part.capitalize() for part in re.findall(r'[A-Za-z][a-z]*', directive_name))
                
                # Read directive content
                directive_content = self._read_file(directive_path)
                
                if not directive_content:
                    print(f"Warning: Could not read directive file {directive_path}")
                    continue
                
                print(f"Converting directive: {directive_name} to component: {component_name}")
                
                # Use convert_with_llm to generate React component
                prompt = f"""
Convert the following Angular directive to a React functional component using TypeScript and hooks.

Directive code:
```javascript
{directive_content}
```

Please convert this to a React component named {component_name}.
The component should use TypeScript, React hooks, and follow modern React patterns.
If the directive has a template, convert the template to JSX.
If the directive uses scope or isolate scope, convert these to props and state.
If the directive manipulates the DOM directly, use React refs instead.
"""
                
                # Convert directive to React component
                react_component = self.convert_with_llm(prompt, "directive", "react_component")
                
                if not react_component:
                    print(f"Warning: Failed to convert directive {directive_name}. Creating a default component instead.")
                    # Generate a simple component scaffold
                    react_component = self._generate_default_component_scaffold(component_name)
                
                # Write the component file
                output_file = components_dir / f"{component_name}.tsx"
                output_file.write_text(react_component)
                
                # Add a generated notice
                self._add_generated_notice(output_file)
                
                converted_count += 1
                print(f"Created React component for directive {directive_name}: {output_file}")
                
            except Exception as e:
                print(f"Warning: Could not convert directive {directive_name}: {e}")
                traceback.print_exc()
        
        print(f"Converted {converted_count} directives to React components")
    
    def _generate_default_component_scaffold(self, component_name: str) -> str:
        """
        Generate a default React component scaffold
        
        Args:
            component_name: Name for the component
            
        Returns:
            Default component code as string
        """
        return f"""'use client';

import React, {{ useState, useEffect, useRef }} from 'react';

interface {component_name}Props {{
  // Define component props here
}}

/**
 * {component_name} Component
 * 
 * This component was auto-generated from an Angular directive.
 * You may need to implement the specific functionality manually.
 */
export default function {component_name}(props: {component_name}Props) {{
  const ref = useRef<HTMLDivElement>(null);
  
  useEffect(() => {{
    // Implement directive functionality here
    // This is where you would add the equivalent of the link function
    
    return () => {{
      // Cleanup (equivalent to $destroy)
    }};
  }}, []);
  
  return (
    <div ref={{{{ref}}}} className="{component_name.toLowerCase()}-container">
      {{/* Component content goes here */}}
      <p>This is the {component_name} component</p>
    </div>
  );
}}
"""

    def generate_react_hooks(self) -> None:
        """
        Generate React hooks from Angular services
        """
        print("Generating React hooks from Angular services...")
        
        # Create hooks directory
        hooks_dir = self.nextjs_root / 'src' / 'hooks'
        hooks_dir.mkdir(exist_ok=True, parents=True)
        
        # Count of converted services
        converted_count = 0
        
        # Process each service that is not converted to an API route
        for service_name, service_path in self.services.items():
            # Skip services that are already converted to API routes
            if any(name in service_name.lower() for name in [
                'data', 'api', 'http', 'resource', 'store', 'storage', 'state', 'provider'
            ]):
                try:
                    # Convert service name to hook name (camelCase)
                    hook_name = f"use{service_name.replace('Service', '')}"
                    
                    # Read service content
                    service_content = self._read_file(service_path)
                    
                    if not service_content:
                        print(f"Warning: Could not read service file {service_path}")
                        continue
                    
                    print(f"Converting service: {service_name} to hook: {hook_name}")
                    
                    # Use convert_with_llm to generate React hook
                    prompt = f"""
Convert the following Angular service to a React hook using TypeScript.

Service code:
```javascript
{service_content}
```

Please convert this to a React hook named {hook_name}.
The hook should use TypeScript and follow modern React patterns.
If the service has dependencies, handle them correctly using React's dependency injection approach.
If the service uses $http, convert it to use fetch or axios.
If the service manages state, use React's useState and provide appropriate setters.
"""
                    
                    # Convert service to React hook
                    react_hook = self.convert_with_llm(prompt, "service", "react_hooks")
                    
                    if not react_hook:
                        print(f"Warning: Failed to convert service {service_name}. Creating a default hook instead.")
                        # Generate a simple hook scaffold
                        react_hook = self._generate_default_hook_scaffold(hook_name, service_name)
                    
                    # Write the hook file
                    output_file = hooks_dir / f"{hook_name}.ts"
                    output_file.write_text(react_hook)
                    
                    # Add a generated notice
                    self._add_generated_notice(output_file)
                    
                    converted_count += 1
                    print(f"Created React hook for service {service_name}: {output_file}")
                    
                except Exception as e:
                    print(f"Warning: Could not convert service {service_name} to hook: {e}")
                    traceback.print_exc()
        
        # Create context providers for global state management
        self._create_context_providers()
        
        print(f"Converted {converted_count} services to React hooks")
    
    def _generate_default_hook_scaffold(self, hook_name: str, service_name: str) -> str:
        """
        Generate a default React hook scaffold
        
        Args:
            hook_name: Name for the hook
            service_name: Original Angular service name
            
        Returns:
            Default hook code as string
        """
        return f"""import {{ useState, useEffect, useCallback }} from 'react';

/**
 * {hook_name} - React hook version of {service_name}
 * 
 * This hook was auto-generated from an Angular service.
 * You may need to implement the specific service functionality manually.
 */
export function {hook_name}() {{
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  /**
   * Example method - replace with actual implementation
   */
  const fetchData = useCallback(async () => {{
    setLoading(true);
    setError(null);
    
    try {{
      // Replace with actual implementation
      const response = await fetch('/api/example');
      const result = await response.json();
      setData(result);
    }} catch (err) {{
      setError(err instanceof Error ? err : new Error('Unknown error'));
      console.error('Error in {hook_name}:', err);
    }} finally {{
      setLoading(false);
    }}
  }}, []);

  return {{
    data,
    loading,
    error,
    fetchData
  }};
}}

export default {hook_name};
"""
    
    def _create_context_providers(self) -> None:
        """
        Create React context providers for global state management
        """
        print("Creating React context providers...")
        
        # Create context directory
        context_dir = self.nextjs_root / 'src' / 'context'
        context_dir.mkdir(exist_ok=True, parents=True)
        
        # Create app state context
        app_state_context = """import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface AppState {
  // Add your global state properties here
  isAuthenticated: boolean;
  user: any | null;
  theme: 'light' | 'dark';
}

interface AppStateContextType {
  state: AppState;
  login: (user: any) => void;
  logout: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

const initialState: AppState = {
  isAuthenticated: false,
  user: null,
  theme: 'light',
};

const AppStateContext = createContext<AppStateContextType | undefined>(undefined);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>(initialState);

  const login = useCallback((user: any) => {
    setState(prev => ({ ...prev, isAuthenticated: true, user }));
  }, []);

  const logout = useCallback(() => {
    setState(prev => ({ ...prev, isAuthenticated: false, user: null }));
  }, []);

  const setTheme = useCallback((theme: 'light' | 'dark') => {
    setState(prev => ({ ...prev, theme }));
  }, []);

  return (
    <AppStateContext.Provider value={{ state, login, logout, setTheme }}>
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  const context = useContext(AppStateContext);
  if (context === undefined) {
    throw new Error('useAppState must be used within an AppStateProvider');
  }
  return context;
}
"""
        
        # Write app state context
        (context_dir / 'AppStateContext.tsx').write_text(app_state_context)
        
        # Create auth context
        auth_context = """import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface AuthContextType {
  isAuthenticated: boolean;
  user: any | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Check if user is already authenticated on mount
    const checkAuth = async () => {
      try {
        // Replace with your authentication check logic
        const token = localStorage.getItem('token');
        
        if (token) {
          const response = await fetch('/api/auth/verify', {
            headers: {
              Authorization: `Bearer ${token}`
            }
          });
          
          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
            setIsAuthenticated(true);
          } else {
            // Clear invalid token
            localStorage.removeItem('token');
          }
        }
      } catch (err) {
        console.error('Authentication check error:', err);
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    
    try {
      // Replace with your login API call
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Login failed');
      }
      
      const data = await response.json();
      
      // Store token in localStorage or secure cookie
      localStorage.setItem('token', data.token);
      
      setUser(data.user);
      setIsAuthenticated(true);
      
      // Redirect to dashboard
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error during login');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  }, [router]);

  const logout = useCallback(() => {
    // Clear token
    localStorage.removeItem('token');
    
    // Reset state
    setUser(null);
    setIsAuthenticated(false);
    
    // Redirect to login
    router.push('/login');
  }, [router]);

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout, loading, error }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
"""
        
        # Write auth context
        (context_dir / 'AuthContext.tsx').write_text(auth_context)
        
        # Create API context
        api_context = """import React, { createContext, useContext, useCallback, ReactNode } from 'react';
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

interface ApiContextType {
  get: <T>(url: string, config?: AxiosRequestConfig) => Promise<T>;
  post: <T>(url: string, data?: any, config?: AxiosRequestConfig) => Promise<T>;
  put: <T>(url: string, data?: any, config?: AxiosRequestConfig) => Promise<T>;
  delete: <T>(url: string, config?: AxiosRequestConfig) => Promise<T>;
}

const ApiContext = createContext<ApiContextType | undefined>(undefined);

export function ApiProvider({ children }: { children: ReactNode }) {
  // Create axios instance
  const api: AxiosInstance = axios.create({
    baseURL: '/api',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Add request interceptor for authentication
  api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  });

  // Add response interceptor for error handling
  api.interceptors.response.use(
    (response) => response.data,
    (error) => {
      // Handle session expiration
      if (error.response && error.response.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
      
      return Promise.reject(error);
    }
  );

  const get = useCallback(<T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return api.get(url, config);
  }, []);

  const post = useCallback(<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return api.post(url, data, config);
  }, []);

  const put = useCallback(<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return api.put(url, data, config);
  }, []);

  const del = useCallback(<T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return api.delete(url, config);
  }, []);

  return (
    <ApiContext.Provider value={{ get, post, put, delete: del }}>
      {children}
    </ApiContext.Provider>
  );
}

export function useApi() {
  const context = useContext(ApiContext);
  if (context === undefined) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
}
"""
        
        # Write API context
        (context_dir / 'ApiContext.tsx').write_text(api_context)
        
        # Update RootLayout to include providers
        layout_path = self.nextjs_root / 'src' / 'app' / 'layout.tsx'
        if layout_path.exists():
            layout_content = layout_path.read_text()
            
            # Add providers to layout
            updated_layout = layout_content.replace(
                '<body>{children}</body>',
                """<body>
          <ApiProvider>
            <AuthProvider>
              <AppStateProvider>
                {children}
              </AppStateProvider>
            </AuthProvider>
          </ApiProvider>
        </body>"""
            )
            
            # Add imports
            imports = """'use client';

import './globals.css';
import { AppStateProvider } from '@/context/AppStateContext';
import { AuthProvider } from '@/context/AuthContext';
import { ApiProvider } from '@/context/ApiContext';
"""
            
            updated_layout = updated_layout.replace("'use client';\n\nimport './globals.css';", imports)
            
            # Write updated layout
            layout_path.write_text(updated_layout)
            
        print("Created React context providers for global state management")
        

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Migrate Angular project to Next.js")
    parser.add_argument("--angular-root", required=True, help="Path to Angular project root")
    parser.add_argument("--nextjs-root", required=True, help="Path to output Next.js project")
    parser.add_argument("--api-key", help="OpenRouter API key (optional, will use env var if not provided)")
    parser.add_argument("--model", help="LLM model to use (default: google/gemini-2.0-flash-001)")
    parser.add_argument("--analysis-file", help="Path to pre-computed analysis JSON file (optional, will look in scripts/ if not provided)")
    
    args = parser.parse_args()
    
    # Create migrator and run migration
    migrator = AngularToNextMigrator(
        angular_root=args.angular_root,
        nextjs_root=args.nextjs_root,
        api_key=args.api_key,
        model=args.model,
        analysis_file=args.analysis_file
    )
    
    migrator.migrate()
