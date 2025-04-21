#!/usr/bin/env python3
import os
import re
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

class AngularCodebaseAnalyzer:
    def __init__(self, angular_root: str, template_prefix: str = 'app/', 
                 verify_states: bool = True, skip_vendor: bool = True):
        """
        Initialize the analyzer with the Angular project root path
        
        Args:
            angular_root: Path to Angular project root
            template_prefix: Prefix to remove from template paths (default: 'app/')
            verify_states: Whether to verify state definitions
            skip_vendor: Whether to skip vendor libraries
        """
        self.angular_root = Path(angular_root)
        self.template_prefix = template_prefix
        self._verify_state_definitions_enabled = verify_states
        self._skip_vendor = skip_vendor
        
        # Ensure path exists and is directory
        if not self.angular_root.exists() or not self.angular_root.is_dir():
            raise ValueError(f"Angular project root {angular_root} does not exist or is not a directory")
        
        # Initialize data structures
        self.routes: List[Dict] = []
        self.controllers: Dict[str, str] = {}
        self.templates: Dict[str, str] = {}
        self.services: Dict[str, str] = {}
        self.directives: Dict[str, str] = {}
        self.filters: Dict[str, str] = {}
        self.modules: Dict[str, str] = {}
        self.styles: Dict[str, str] = {}
        self.assets: Dict[str, str] = {}
        self.vendor_libs: Dict[str, List[str]] = {}
        self.file_dependencies: Dict[str, Set[str]] = {}
        
        # Update ignore_dirs to include specific patterns from the analyzed app
        self.ignore_dirs = ['v1', 'scripts/vendor', 'vendor', 'node_modules', 'dist', 'build', 'tmp']
        # Minified file patterns to ignore
        self.ignore_files = [
            '.min.js', '.min.css', '-min.js', '-min.css',
            '.bundle.js', '.bundle.css', '.pack.js',
            '.compiled.js', '.prod.js', '.compressed.js',
            'dist.js', 'compressed.css', 'minimized.js',
            'bootstrap-filestyle.min.js', 'datatables.bootstrap.min.css',
            'alasql.min.js', 'xlsx.core.min.js', 'jquery.dataTables.columnFilter.js'
        ]
        
        # Define paths based on provided structure - try to infer if not standard
        self.app_path = self.angular_root / 'app'
        if not self.app_path.exists():
            # Try to find the app directory
            possible_app_dirs = ['app', 'src', 'client', 'www']
            for dir_name in possible_app_dirs:
                test_path = self.angular_root / dir_name
                if test_path.exists() and test_path.is_dir():
                    self.app_path = test_path
                    break
        
        self.app_js_path = self.find_app_js()
        self.scripts_path = self.find_scripts_dir()
        self.views_path = self.find_views_dir()
        self.styles_path = self.find_styles_dir()
        self.assets_path = self.find_assets_dir()
        self.fonts_path = self.find_dir_with_glob('**/fonts')
        self.images_path = self.find_dir_with_glob('**/images')
        
        # Add new properties for b-controllers and b-services directories
        self.b_controllers_path = self.find_b_controllers_dir()
        self.b_services_path = self.find_b_services_dir()
        self.b_tmpl_path = self.find_b_tmpl_dir()
        
    def find_app_js(self) -> Path:
        """
        Find the main app.js file, trying various common locations
        """
        possible_locations = [
            self.angular_root / 'app' / 'scripts' / 'app.js',
            self.angular_root / 'app' / 'app.js',
            self.angular_root / 'src' / 'app.js',
            self.angular_root / 'src' / 'app' / 'app.js',
            self.angular_root / 'www' / 'js' / 'app.js',
            self.angular_root / 'scripts' / 'app.js',
            self.angular_root / 'js' / 'app.js'
        ]
        
        # Also search for any file with "app" in the name and .js extension
        app_js_files = list(self.angular_root.glob('**/app*.js'))
        possible_locations.extend(app_js_files)
        
        for location in possible_locations:
            if location.exists():
                print(f"Found app.js at {location}")
                return location
        
        print("Warning: Could not find app.js. Using default path.")
        return self.angular_root / 'app' / 'scripts' / 'app.js'
    
    def find_scripts_dir(self) -> Path:
        """
        Find the scripts directory, trying various common locations
        """
        possible_locations = [
            self.angular_root / 'app' / 'scripts',
            self.angular_root / 'app' / 'js',
            self.angular_root / 'src' / 'scripts',
            self.angular_root / 'src' / 'js',
            self.angular_root / 'www' / 'js',
            self.angular_root / 'scripts',
            self.angular_root / 'js'
        ]
        
        for location in possible_locations:
            if location.exists() and location.is_dir():
                print(f"Found scripts directory at {location}")
                return location
        
        print("Warning: Could not find scripts directory. Using default path.")
        return self.angular_root / 'app' / 'scripts'
    
    def find_styles_dir(self) -> Path:
        """
        Find the styles directory, trying various common locations
        """
        possible_locations = [
            self.angular_root / 'app' / 'sass',
            self.angular_root / 'app' / 'scss',
            self.angular_root / 'app' / 'css',
            self.angular_root / 'app' / 'styles',
            self.angular_root / 'src' / 'sass',
            self.angular_root / 'src' / 'scss',
            self.angular_root / 'src' / 'css',
            self.angular_root / 'src' / 'styles',
            self.angular_root / 'sass',
            self.angular_root / 'scss',
            self.angular_root / 'css',
            self.angular_root / 'styles'
        ]
        
        for location in possible_locations:
            if location.exists() and location.is_dir():
                print(f"Found styles directory at {location}")
                return location
        
        print("Warning: Could not find styles directory. Using default path.")
        return self.angular_root / 'app' / 'sass'
    
    def find_assets_dir(self) -> Path:
        """
        Find the assets directory, trying various common locations
        """
        possible_locations = [
            self.angular_root / 'app' / 'assets',
            self.angular_root / 'src' / 'assets',
            self.angular_root / 'assets',
            self.angular_root / 'public' / 'assets',
            self.angular_root / 'static' / 'assets',
            self.angular_root / 'www' / 'assets'
        ]
        
        for location in possible_locations:
            if location.exists() and location.is_dir():
                print(f"Found assets directory at {location}")
                return location
        
        print("Warning: Could not find assets directory. Using default path.")
        return self.angular_root / 'app' / 'assets'
    
    def find_dir_with_glob(self, glob_pattern: str) -> Optional[Path]:
        """
        Find a directory using glob pattern
        """
        dirs = list(self.angular_root.glob(glob_pattern))
        if dirs:
            print(f"Found directory matching {glob_pattern} at {dirs[0]}")
            return dirs[0]
        
        print(f"Warning: Could not find directory matching {glob_pattern}")
        return None
        
    def _should_ignore(self, path: Path) -> bool:
        """
        Check if a path should be ignored based on the ignore rules
        
        Args:
            path: Path to check
            
        Returns:
            True if path should be ignored, False otherwise
        """
        rel_path = str(path.relative_to(self.angular_root))
        
        # Check if path is in ignored directories
        for ignore_dir in self.ignore_dirs:
            if ignore_dir in rel_path:
                return True
        
        # Check if file is minified - more aggressive check
        if self._is_vendor_or_minified(rel_path):
            return True
        
        # Also check the original patterns
        for ignore_pattern in self.ignore_files:
            if ignore_pattern in path.name:
                return True
        
        return False
        
    def _extract_require_dependencies(self, content: str) -> List[str]:
        """
        Extract dependencies from require.js style Angular apps
        
        Args:
            content: JS file content to analyze
            
        Returns:
            List of extracted dependencies
        """
        deps = []
        
        # Look for require patterns
        require_pattern = r"require\(\[(.*?)\]"
        require_matches = re.findall(require_pattern, content, re.DOTALL)
        
        for deps_list in require_matches:
            # Extract quoted strings from the dependencies list
            dep_matches = re.findall(r"['\"]([^'\"]+)['\"]", deps_list)
            deps.extend(dep_matches)
        
        # Also look for define patterns
        define_pattern = r"define\(\[(.*?)\]"
        define_matches = re.findall(define_pattern, content, re.DOTALL)
        
        for deps_list in define_matches:
            # Extract quoted strings from the dependencies list
            dep_matches = re.findall(r"['\"]([^'\"]+)['\"]", deps_list)
            deps.extend(dep_matches)
        
        return deps
        
    def analyze_routes(self) -> None:
        """
        Parse app.js to extract all route definitions
        """
        print("Analyzing routes from app.js...")
        
        if not self.app_js_path.exists():
            print(f"Warning: {self.app_js_path} does not exist")
            # Try to find main module configuration file
            js_files = list(self.angular_root.glob('**/app.module.js')) + \
                       list(self.angular_root.glob('**/routes.js')) + \
                       list(self.angular_root.glob('**/config.js'))
            
            if js_files:
                self.app_js_path = js_files[0]
                print(f"Found alternative route definition file: {self.app_js_path}")
            else:
                print("Could not find any route definition files. No routes will be analyzed.")
                return
            
        try:
            content = self.app_js_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try with different encodings
            try:
                content = self.app_js_path.read_text(encoding='latin-1')
                print("Warning: File was not UTF-8 encoded, used latin-1 instead")
            except:
                print(f"Error: Could not read {self.app_js_path} with any encoding")
                return
                
        # DEBUG: Print file size
        print(f"Route file size: {len(content)} bytes")
        
        # Check for different router types
        if '.state(' in content:
            print("Detected UI-Router style routes")
            self._analyze_ui_router(content)
        elif '$routeProvider' in content:
            print("Detected ngRoute style routes")
            self._analyze_ng_route(content)
        else:
            print("Warning: Could not detect router type. Trying all known patterns.")
            self._analyze_ui_router(content)
            self._analyze_ng_route(content)
            
        # Also check for require.js style dependencies
        require_deps = self._extract_require_dependencies(content)
        if require_deps:
            # Filter vendor and minified dependencies
            filtered_require_deps = self._filter_dependencies(require_deps)
            print(f"Found {len(filtered_require_deps)} require.js dependencies (after filtering)")
        
        # Look for additional router config files
        additional_config_files = []
        
        # Check modules directory for potential route configs
        if self.scripts_path and self.scripts_path.exists():
            for js_file in self.scripts_path.glob('**/routes.js'):
                if not self._should_ignore(js_file):
                    additional_config_files.append(js_file)
            
            for js_file in self.scripts_path.glob('**/config.js'):
                if not self._should_ignore(js_file) and js_file != self.app_js_path:
                    additional_config_files.append(js_file)
        
        # Analyze additional route files
        for config_file in additional_config_files:
            try:
                print(f"Analyzing additional route file: {config_file}")
                content = config_file.read_text(encoding='utf-8')
                
                if '.state(' in content:
                    self._analyze_ui_router(content)
                elif '$routeProvider' in content:
                    self._analyze_ng_route(content)
            except Exception as e:
                print(f"Warning: Could not analyze additional route file {config_file}: {e}")
        
        print(f"Total routes found: {len(self.routes)}")
        
        # Add summary information 
        routes_with_deps = [r for r in self.routes if r['resolve_dependencies']]
        print(f"Routes with dependencies: {len(routes_with_deps)}/{len(self.routes)}")
        
    def _analyze_ui_router(self, content: str) -> None:
        """
        Analyze UI-Router style route definitions
        
        Args:
            content: File content to analyze
        """
        print("Analyzing UI-Router style routes...")
        
        # Use more comprehensive regex to find actual state definitions
        # This pattern looks for proper state method calls in the JavaScript code
        state_pattern = r'(?<!\w)(?:\.|\$stateProvider\.)state\s*\(\s*[\'"]([^\'"]+)[\'"]'
        
        # Find all potential state definitions
        state_matches = re.findall(state_pattern, content)
        total_potential_states = len(state_matches)
        print(f"Found {total_potential_states} potential state definitions")
        
        # Variables to track state processing
        commented_count = 0
        invalid_state_count = 0
        duplicate_state_count = 0
        processed_state_count = 0
        extracted_states = []
        state_names_seen = set()
        
        # Find state definitions with more precise context
        # This looks for the complete state definition including the configuration object
        complete_state_patterns = [
            # Standard format: .state('name', {...})
            r'(?<!\w)(?:\.|\$stateProvider\.)state\s*\(\s*[\'"]([^\'"]+)[\'"](?:\s*,\s*|\s*,\s*\n\s*)(\{[^{]*(?:\{[^}]*\}[^{]*)*\})',
            # Alternate format with object config: .state({name: 'name', ...})
            r'(?<!\w)(?:\.|\$stateProvider\.)state\s*\(\s*\{[^{]*name\s*:\s*[\'"]([^\'"]+)[\'"][^}]*,\s*(.*?)\}\s*\)',
            # More permissive pattern for nested structures
            r'(?<!\w)(?:\.|\$stateProvider\.)state\s*\(\s*[\'"]([^\'"]+)[\'"](?:\s*,\s*|\s*,\s*\n\s*)(\{[\s\S]*?(?:\}\s*\)(?!\s*\.state)))',
            # Catch state definitions with function parameters
            r'(?<!\w)(?:\.|\$stateProvider\.)state\s*\(\s*[\'"]([^\'"]+)[\'"](?:\s*,\s*|\s*,\s*\n\s*)(?:function\s*\([^\)]*\)\s*\{[\s\S]*?\}|\{[\s\S]*?\})(?=\s*\))',
        ]
        
        # Track matched lines for debugging
        state_definition_lines = []
        lines = content.split('\n')
        
        # First pass: identify lines containing state definitions and if they're in comments
        for i, line in enumerate(lines):
            # Check if the line has a state definition
            if re.search(state_pattern, line):
                line_num = i + 1
                
                # Check if this line is in a comment
                is_commented = False
                if '//' in line:
                    # Check if state is after comment
                    comment_pos = line.find('//')
                    if comment_pos < line.find('.state('):
                        is_commented = True
                
                if '/*' in line and '*/' in line:
                    # Check if state is between /* and */
                    comment_start = line.find('/*')
                    comment_end = line.find('*/')
                    if comment_start < line.find('.state(') < comment_end:
                        is_commented = True
                
                # Record the line info
                state_definition_lines.append({
                    'line_num': line_num,
                    'content': line.strip(),
                    'is_commented': is_commented
                })
                
                if is_commented:
                    commented_count += 1
        
        # Find multi-line comments
        multi_line_comments = []
        in_comment = False
        comment_start = 0
        
        for i, line in enumerate(lines):
            if '/*' in line and '*/' not in line:
                in_comment = True
                comment_start = i
            elif '*/' in line and in_comment:
                multi_line_comments.append((comment_start, i))
                in_comment = False
        
        # Check for state definitions in multi-line comments
        for start, end in multi_line_comments:
            for line_info in state_definition_lines:
                if start <= line_info['line_num'] - 1 <= end and not line_info['is_commented']:
                    line_info['is_commented'] = True
                    commented_count += 1
        
        # Second pass: extract complete state definitions using regex
        for pattern in complete_state_patterns:
            state_configs = re.findall(pattern, content, re.DOTALL)
            for match in state_configs:
                if len(match) >= 2:
                    name = match[0]
                    config = match[1]
                    
                    # Check if state is in a commented section
                    is_commented = False
                    for start, end in multi_line_comments:
                        # Find the position of this match in the content
                        match_pos = content.find(f'.state("{name}"')
                        if match_pos == -1:
                            match_pos = content.find(f".state('{name}'")
                        
                        if match_pos >= 0:
                            # Find the line number
                            line_count = content[:match_pos].count('\n')
                            if start <= line_count <= end:
                                is_commented = True
                                break
                    
                    # Also check if it's in a line comment
                    for line_info in state_definition_lines:
                        if name in line_info['content'] and line_info['is_commented']:
                            is_commented = True
                            break
                    
                    if is_commented:
                        continue
                    
                    # Skip duplicates
                    if name in state_names_seen:
                        duplicate_state_count += 1
                        continue
                    
                    # Add to extracted states
                    state_names_seen.add(name)
                    extracted_states.append((name, config))
        
        # Fall back to line-by-line extraction for any states not captured by regex
        missing_states = set(state_matches) - state_names_seen
        if missing_states:
            print(f"Attempting to extract {len(missing_states)} missing states line by line")
            
            # Line-by-line extraction logic
            for i, line in enumerate(lines):
                for name in missing_states:
                    if f'.state("{name}"' in line or f".state('{name}'" in line:
                        # Skip commented lines
                        if '//' in line and line.find('//') < line.find('.state'):
                            continue
                        
                        # Check if line is in a multiline comment
                        is_in_comment = False
                        for start, end in multi_line_comments:
                            if start <= i <= end:
                                is_in_comment = True
                                break
                        
                        if is_in_comment:
                            continue
                        
                        # Locate the full state block
                        block_start = i
                        block_end = i
                        brace_count = line.count('{') - line.count('}')
                        
                        # If the state definition is on a single line
                        if '{' in line and '}' in line and line.rfind('{') < line.rfind('}') and brace_count == 0:
                            config_match = re.search(r',\s*(\{.*\})\s*\)', line)
                            if config_match:
                                config = config_match.group(1)
                                if name not in state_names_seen:
                                    state_names_seen.add(name)
                                    extracted_states.append((name, config))
                            continue
                        
                        # Otherwise, track braces to find the end of the block
                        if brace_count > 0:
                            block_text = [line]
                            
                            # Scan forward to find end of block
                            for j in range(i+1, len(lines)):
                                next_line = lines[j]
                                block_text.append(next_line)
                                brace_count += next_line.count('{') - next_line.count('}')
                                
                                if brace_count <= 0 and (')' in next_line or '})' in next_line):
                                    block_end = j
                                    break
                            
                            if block_end > block_start:
                                # We found a complete block
                                block_content = '\n'.join(block_text)
                                # Try to extract the config part
                                config_match = re.search(r',\s*(\{[\s\S]*\})\s*\)', block_content, re.DOTALL)
                                if config_match:
                                    config = config_match.group(1)
                                    if name not in state_names_seen:
                                        state_names_seen.add(name)
                                        extracted_states.append((name, config))
        
        # Verify extracted configs are valid
        final_states = []
        for name, config in extracted_states:
            # Check if config is valid (not too short)
            if not config or len(config.strip()) < 5:  # Config too short
                invalid_state_count += 1
                continue
                
            final_states.append((name, config))
        
        processed_state_count = len(final_states)
        
        # Write diagnostic information
        try:
            with open('state_analysis.txt', 'w') as f:
                f.write(f"Total potential states: {total_potential_states}\n")
                f.write(f"Commented states: {commented_count}\n")
                f.write(f"Duplicate states: {duplicate_state_count}\n")
                f.write(f"Invalid states: {invalid_state_count}\n")
                f.write(f"Processed states: {processed_state_count}\n\n")
                
                f.write("State definitions found:\n")
                for name in sorted(state_names_seen):
                    f.write(f"- {name}\n")
                    
                f.write("\nPotential states not processed:\n")
                for name in sorted(set(state_matches) - state_names_seen):
                    f.write(f"- {name}\n")
            print("Wrote diagnostic information to state_analysis.txt")
        except Exception as e:
            print(f"Failed to write diagnostic file: {e}")
        
        # Summary of state statistics
        print("\nState Statistics:")
        print(f"Total potential states:         {total_potential_states}")
        print(f"Commented states:               {commented_count}")
        print(f"Duplicate states:               {duplicate_state_count}")
        print(f"Invalid/problematic states:     {invalid_state_count}")
        print(f"Unique valid states processed:  {processed_state_count}")
        
        # Process states into routes
        self._process_states(final_states, content)
    
    def _analyze_ng_route(self, content: str) -> None:
        """
        Analyze ngRoute style route definitions
        
        Args:
            content: File content to analyze
        """
        # Look for $routeProvider configurations
        config_pattern = r"(?:\.config\(|config\s*\(\s*function\s*\([^\)]*\)\s*\{)(.*?)(?:\}\s*\)|[,;]$)"
        config_blocks = re.findall(config_pattern, content, re.DOTALL)
        
        route_count = 0
        
        for config_block in config_blocks:
            if "$routeProvider" in config_block:
                route_pattern = r"\.when\(['\"]([^'\"]+)['\"],\s*\{([^{}]+(?:\{[^{}]*\}[^{}]*)*)\}\)"
                route_matches = re.findall(route_pattern, config_block, re.DOTALL)
                
                for route_url, route_config in route_matches:
                    route_data = {
                        'name': f"route_{len(self.routes)}",  # Generate a name
                        'url': route_url,
                        'controller': None,
                        'templateUrl': None,
                        'template': None,
                        'resolve': [],
                        'resolve_dependencies': [],  # Add this for report compatibility
                        'type': 'ngRoute'  # Mark as ngRoute type
                    }
                    
                    # Extract controller
                    controller_match = re.search(r"controller\s*:\s*['\"]([^'\"]+)['\"]", route_config)
                    if controller_match:
                        route_data['controller'] = controller_match.group(1)
                    
                    # Extract templateUrl
                    template_match = re.search(r"templateUrl\s*:\s*['\"]([^'\"]+)['\"]", route_config)
                    if template_match:
                        route_data['templateUrl'] = template_match.group(1)
                    
                    # Extract inline template
                    inline_template_match = re.search(r"template\s*:\s*['\"]([^'\"]+)['\"]", route_config)
                    if inline_template_match:
                        route_data['template'] = inline_template_match.group(1)
                    
                    # Use the same approach as for states to find dependencies
                    route_specific_deps = []
                    
                    # Check for resolve block
                    resolve_match = re.search(r"resolve\s*:\s*\{([^{}]+(?:\{[^{}]*\}[^{}]*)*)\}", route_config, re.DOTALL)
                    if resolve_match:
                        resolve_content = resolve_match.group(1)
                        
                        # Same extraction logic as for states
                        all_strings = re.findall(r"['\"]([^'\"]+)['\"]", resolve_content)
                        potential_deps = []
                        
                        common_words = ['function', 'return', 'var', 'let', 'const', 'true', 'false', 'null', 'this']
                        for string in all_strings:
                            if (not string.startswith('$') and 
                                not any(word in string.lower() for word in common_words) and
                                len(string) > 2):
                                potential_deps.append(string)
                        
                        js_identifiers = re.findall(r'(?<![\'"])([A-Za-z$_][A-Za-z0-9$_]*)', resolve_content)
                        for ident in js_identifiers:
                            if (not ident.startswith('$') and 
                                ident not in common_words and
                                len(ident) > 2):
                                potential_deps.append(ident)
                        
                        script_deps = re.findall(r'scripts/([^\'"\s]+\.js)', resolve_content)
                        for script in script_deps:
                            potential_deps.append(script)
                        
                        route_specific_deps.extend(self._filter_dependencies(potential_deps))
                    
                    # Look for JS files in the entire route config
                    js_files_in_route = re.findall(r'[\'"]([^\'"\s]+\.js)[\'"]', route_config)
                    if js_files_in_route:
                        route_specific_deps.extend(self._filter_dependencies(js_files_in_route))
                    
                    # Deduplicate and store dependencies
                    unique_deps = list(set(route_specific_deps))
                    route_data['resolve'] = unique_deps
                    route_data['resolve_dependencies'] = unique_deps
                    
                    self.routes.append(route_data)
                    route_count += 1
                
                # Also check for otherwise route
                otherwise_pattern = r"\.otherwise\(\s*\{([^{}]+(?:\{[^{}]*\}[^{}]*)*)\}\s*\)"
                otherwise_matches = re.findall(otherwise_pattern, config_block, re.DOTALL)
                
                if otherwise_matches:
                    for otherwise_config in otherwise_matches:
                        route_data = {
                            'name': f"route_otherwise_{len(self.routes)}",
                            'url': '*',  # Default wildcard route
                            'controller': None,
                            'templateUrl': None,
                            'template': None,
                            'resolve': [],
                            'resolve_dependencies': [],
                            'type': 'ngRoute'
                        }
                        
                        # Extract redirectTo
                        redirect_match = re.search(r"redirectTo\s*:\s*['\"]([^'\"]+)['\"]", otherwise_config)
                        if redirect_match:
                            route_data['redirectTo'] = redirect_match.group(1)
                        
                        # Extract controller if present
                        controller_match = re.search(r"controller\s*:\s*['\"]([^'\"]+)['\"]", otherwise_config)
                        if controller_match:
                            route_data['controller'] = controller_match.group(1)
                        
                        # Extract templateUrl if present
                        template_match = re.search(r"templateUrl\s*:\s*['\"]([^'\"]+)['\"]", otherwise_config)
                        if template_match:
                            route_data['templateUrl'] = template_match.group(1)
                        
                        self.routes.append(route_data)
                        route_count += 1
        
        print(f"Found {route_count} ngRoute routes")
        
    def _process_states(self, all_states: List[Tuple[str, str]], content: str) -> None:
        """
        Process the extracted state definitions to create route objects
        
        Args:
            all_states: List of (state_name, config_object) tuples
            content: File content for additional analysis
        """
        print(f"Processing {len(all_states)} state definitions")
        
        # States to exclude - these are technical states or not true routes
        # Adjust this list based on your specific app, make it more specific
        exclude_patterns = [
            'root.access-denied', 'root.not-found', 'root.error', 
            'root.login', 'root.logout', 'root.locked',
            'root.debug', 'root.internal', '404', 'error',
            # Add more patterns here if needed
        ]
        
        # Track parent-child relationships for nested states
        parent_map = {}
        for state_name, _ in all_states:
            if '.' in state_name:
                parent_name = state_name.rsplit('.', 1)[0]
                parent_map[state_name] = parent_name

        # Track processed states and reasons for exclusion
        processed_states = []
        excluded_states = []
        abstract_states = []
        duplicate_states = []
        added_state_names = set()
        
        # Process each state definition
        for state_name, config in all_states:
            # Skip explicitly excluded states - use more specific matching
            if any(pattern == state_name or (pattern.endswith('.') and state_name.startswith(pattern)) 
                  for pattern in exclude_patterns):
                excluded_states.append((state_name, "Excluded by pattern"))
                continue
            
            # Create route object with default values
            route = {
                'name': state_name,
                'url': None,
                'controller': None,
                'templateUrl': None,
                'parent': parent_map.get(state_name, ''),
                'abstract': False,
                'type': 'ui-router',
                'views': {},
                'resolve_dependencies': [],
                'plugins': [],
                'template': None
            }
            
            try:
                # Quick check if this is a commented state - more thorough check
                if config.strip().startswith('//') or config.strip().startswith('/*') or '/*' in config and '*/' in config:
                    excluded_states.append((state_name, "Commented"))
                    continue
                
                # Extract URL - using more flexible pattern
                url_match = re.search(r'url\s*:\s*[\'"]([^\'"]+)[\'"]', config)
                if url_match:
                    route['url'] = url_match.group(1)
                else:
                    # Try alternative patterns for URL
                    alt_url_match = re.search(r'url\s*:\s*([^,\s\}\n]+)', config)
                    if alt_url_match:
                        url_val = alt_url_match.group(1)
                        # Handle variable references
                        if not url_val.startswith('$') and not url_val.startswith('function'):
                            route['url'] = url_val
                
                # Extract controller - check multiple patterns
                controller_patterns = [
                    r'controller\s*:\s*[\'"]([^\'"]+)[\'"]',  # String format
                    r'controller\s*:\s*([A-Za-z0-9_$]+)\s+as\s+',  # controllerAs
                    r'controller\s*:\s*([A-Za-z0-9_$]+(?:\.[A-Za-z0-9_$]+)*)',  # Simple reference
                ]
                
                for pattern in controller_patterns:
                    controller_match = re.search(pattern, config)
                    if controller_match:
                        route['controller'] = controller_match.group(1)
                        break
                
                # Extract templateUrl - check multiple patterns
                template_url_match = re.search(r'templateUrl\s*:\s*[\'"]([^\'"]+)[\'"]', config)
                if template_url_match:
                    route['templateUrl'] = template_url_match.group(1)
                else:
                    # Try function-based templateUrl
                    func_template_url = re.search(r'templateUrl\s*:\s*function\s*\([^\)]*\)\s*\{\s*return\s*[\'"]([^\'"]+)[\'"]', config)
                    if func_template_url:
                        route['templateUrl'] = func_template_url.group(1)
                
                # Check for template (inline) - with more patterns
                template_patterns = [
                    r'template\s*:\s*[\'"]([^\'"]+)[\'"]',  # Simple quoted template
                    r'template\s*:\s*[\'"]([^\'"](?:\\[\s\S]|[^\\\'"]*)*)[\'"]',  # Template with escapes
                ]
                
                for pattern in template_patterns:
                    template_match = re.search(pattern, config)
                    if template_match:
                        route['template'] = template_match.group(1)
                        break
                
                # Check if state is abstract - more thorough check
                abstract_patterns = [
                    r'abstract\s*:\s*(true|false)',  # Standard syntax
                    r'abstract\s*:\s*([A-Za-z0-9_$]+)',  # Variable reference
                    r'abstract\s*=\s*(true|false)',  # Alternative syntax
                ]
                
                for pattern in abstract_patterns:
                    abstract_match = re.search(pattern, config)
                    if abstract_match:
                        abstract_value = abstract_match.group(1).lower()
                        is_abstract = abstract_value == 'true' or abstract_value == '!0' or abstract_value == '1'
                        route['abstract'] = is_abstract
                        if is_abstract:
                            abstract_states.append(state_name)
                            # Don't exclude abstract states anymore - include them in routes
                            # excluded_states.append((state_name, "Abstract state"))
                            # continue
                        break
                
                # Extract views if available - with more flexible pattern
                views_pattern = r'views\s*:\s*(\{[^{]*(?:\{[^}]*\}[^{]*)*\})'
                views_match = re.search(views_pattern, config, re.DOTALL)
                if views_match:
                    views_str = views_match.group(1)
                    # Extract view names and properties - more flexible
                    view_entries = re.findall(r'[\'"]([^\'"]+)[\'"]\s*:\s*(\{[^{]*(?:\{[^}]*\}[^{]*)*\})', views_str)
                    for view_name, view_config in view_entries:
                        view_obj = {}
                        
                        # Extract controller and templateUrl for this view - check more patterns
                        for ctrl_pattern in controller_patterns:
                            view_controller_match = re.search(ctrl_pattern, view_config)
                            if view_controller_match:
                                view_obj['controller'] = view_controller_match.group(1)
                                break
                        
                        view_template_url_match = re.search(r'templateUrl\s*:\s*[\'"]([^\'"]+)[\'"]', view_config)
                        if view_template_url_match:
                            view_obj['templateUrl'] = view_template_url_match.group(1)
                        else:
                            # Try function-based templateUrl for view
                            func_view_template_url = re.search(r'templateUrl\s*:\s*function\s*\([^\)]*\)\s*\{\s*return\s*[\'"]([^\'"]+)[\'"]', view_config)
                            if func_view_template_url:
                                view_obj['templateUrl'] = func_view_template_url.group(1)
                        
                        # Only add views that have useful data
                        if view_obj:
                            route['views'][view_name] = view_obj
                
                # Extract resolve dependencies with improved patterns
                all_dependencies = []  # Collect all dependencies here
                
                # More comprehensive resolve extraction
                resolve_pattern = r'resolve\s*:\s*(\{[^{]*(?:\{[^}]*\}[^{]*)*\})'
                resolve_match = re.search(resolve_pattern, config, re.DOTALL)
                if resolve_match:
                    resolve_str = resolve_match.group(1)
                    
                    # Extract string dependencies
                    string_deps = re.findall(r'[\'"]([^\'":]+)[\'"](?=\s*:|\s*,)', resolve_str)
                    all_dependencies.extend(string_deps)
                    
                    # Look for array syntax with dependencies like ['$http', '$stateParams', function($http, $stateParams) {...}]
                    dependency_arrays = re.findall(r'\[\s*([^\[\]]*)\s*\]', resolve_str)
                    for dep_array in dependency_arrays:
                        # Extract quoted strings from the dependency array
                        deps = re.findall(r'[\'"]([^\'"]+)[\'"]', dep_array)
                        all_dependencies.extend(deps)
                    
                    # Look for $ocLazyLoad dependencies which are common in UI-Router apps
                    oc_lazy_load_pattern = r'\$ocLazyLoad\.load\(\s*(?:\{\s*name\s*:\s*[\'"][^\'"]*[\'"],\s*files\s*:\s*)?\[(.*?)\]\s*\)?'
                    oc_lazy_load_matches = re.findall(oc_lazy_load_pattern, resolve_str, re.DOTALL)
                    
                    for lazy_deps_str in oc_lazy_load_matches:
                        # Extract quoted file paths
                        lazy_deps = re.findall(r'[\'"]([^\'"]+)[\'"]', lazy_deps_str)
                        # These are lazy-loaded plugin paths
                        if lazy_deps:
                            # Filter out non-JS files
                            js_deps = [dep for dep in lazy_deps if '.js' in dep or '/js/' in dep or 'scripts/' in dep]
                            route['plugins'].extend(js_deps)
                
                # Check for duplicate routes (same name) - with more careful handling
                if state_name in added_state_names:
                    duplicate_states.append(state_name)
                    excluded_states.append((state_name, "Duplicate"))
                    continue
                
                # Filter redirect states - these often don't have templates
                if re.search(r'redirectTo\s*:', config):
                    # Don't exclude redirects anymore, just mark them
                    route['redirectTo'] = True
                    # excluded_states.append((state_name, "Redirect state"))
                    # continue
                
                # Deduplicate and filter dependencies
                # Remove Angular built-in services (starting with $)
                filtered_deps = [dep for dep in all_dependencies if not dep.startswith('$')]
                # Remove duplicates while preserving order
                seen = set()
                route['resolve_dependencies'] = [dep for dep in filtered_deps if not (dep in seen or seen.add(dep))]
                
                # Deduplicate plugins
                if route['plugins']:
                    seen = set()
                    route['plugins'] = [plugin for plugin in route['plugins'] if not (plugin in seen or seen.add(plugin))]
                
                # More flexible validation - do not require templates for every state 
                # Abstract states, parent states, and states with views shouldn't require templates
                skip_template_validation = (
                    route['abstract'] or 
                    state_name == 'root' or 
                    route['views'] or 
                    route.get('redirectTo') or
                    state_name in parent_map.values()  # This is a parent state
                )
                
                if (not route['template'] and not route['templateUrl'] and not route['views'] and 
                    not skip_template_validation):
                    
                    # More specific validation for states that should have templates
                    if not route['url'] and not route['abstract']:
                        # This state has no URL, template, or views - likely incomplete
                        excluded_states.append((state_name, "No template, URL or views"))
                        continue
                
                # If we get here, this is a valid route to include
                added_state_names.add(state_name)
                processed_states.append(state_name)
                # Add to routes
                self.routes.append(route)
                
            except Exception as e:
                excluded_states.append((state_name, f"Error: {str(e)}"))
                print(f"Warning: Error processing state {state_name}: {e}")
        
        # Report on state processing
        total_states = len(all_states)
        excluded_count = len(excluded_states)
        abstract_count = len(abstract_states)
        duplicate_count = len(duplicate_states)
        
        print(f"\nState Processing Summary:")
        print(f"Total states extracted: {total_states}")
        print(f"States processed and added to routes: {len(processed_states)}")
        print(f"Abstract states: {abstract_count}")
        print(f"Duplicate states: {duplicate_count}")
        print(f"Excluded states: {excluded_count}")
        
        # Detailed exclusion reasons
        exclusion_reasons = {}
        for _, reason in excluded_states:
            exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
        
        if exclusion_reasons:
            print("\nExclusion reasons:")
            for reason, count in exclusion_reasons.items():
                print(f"  - {reason}: {count}")
                
        # Suggest action if many states were excluded
        if excluded_count > 10:
            print("\nWarning: A large number of states were excluded. Check exclusion reasons above.")
            print("Consider reviewing exclude_patterns and validation logic if legitimate states are being excluded.")
    
    def analyze_controllers(self) -> None:
        """
        Find and analyze all controllers
        """
        print("Analyzing controllers...")
        
        # Find all JS files in scripts directory and subdirectories
        controller_files = []
        
        # First check specific b-controllers directory
        if self.b_controllers_path and self.b_controllers_path.exists():
            for file_path in self.b_controllers_path.glob('**/*.js'):
                if not self._should_ignore(file_path):
                    controller_files.append(file_path)
            print(f"Found {len(controller_files)} controller files in b-controllers directory")
        
        # Also check the standard controllers directory
        controllers_path = self.scripts_path / 'controllers'
        if controllers_path.exists():
            for file_path in controllers_path.glob('**/*.js'):
                if not self._should_ignore(file_path):
                    controller_files.append(file_path)
        
        # Also look through all JS files in the scripts directory for controller definitions
        for file_path in self.scripts_path.glob('**/*.js'):
            if not self._should_ignore(file_path) and file_path not in controller_files:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    if '.controller(' in content:
                        controller_files.append(file_path)
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
        
        print(f"Found {len(controller_files)} controller files in total (after filtering)")
        
        for file_path in controller_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Extract controller name patterns like ".controller('MyCtrl'" and ".controller('MyCtrl as vm'"
                controller_matches = re.findall(r"\.controller\s*\(\s*['\"]([^'\"]+)['\"]", content)
                
                for controller_name in controller_matches:
                    # Handle "controller as" syntax
                    if ' as ' in controller_name:
                        controller_name = controller_name.split(' as ')[0].strip()
                    
                    # Store the controller path (relative to angular_root)
                    relative_path = file_path.relative_to(self.angular_root)
                    self.controllers[controller_name] = str(relative_path)
                    
                    # Analyze controller dependencies
                    self._analyze_file_dependencies(file_path, content)
            except Exception as e:
                print(f"Warning: Could not analyze controller file {file_path}: {e}")
        
        print(f"Found {len(self.controllers)} controllers")
    
    def analyze_templates(self) -> None:
        """
        Find and analyze all templates
        """
        print("Analyzing templates...")
        
        # Find all HTML files in views directory and subdirectories
        template_files = []
        
        # Check if b-tmpl directory exists and has templates
        if self.b_tmpl_path and self.b_tmpl_path.exists():
            for file_path in self.b_tmpl_path.glob('**/*.html'):
                if not self._should_ignore(file_path):
                    template_files.append(file_path)
            print(f"Found {len(template_files)} templates in b-tmpl directory")
        
        # Also check views directory
        if self.views_path and self.views_path.exists():
            for file_path in self.views_path.glob('**/*.html'):
                if not self._should_ignore(file_path) and file_path not in template_files:
                    template_files.append(file_path)
        
        # Also check root app directory for any other HTML templates
        for file_path in self.app_path.glob('**/*.html'):
            if not self._should_ignore(file_path) and file_path not in template_files:
                template_files.append(file_path)
        
        print(f"Found {len(template_files)} template files in total (after filtering)")
        
        # Process templates - map them by their URL
        for file_path in template_files:
            try:
                # Get path relative to root (for templateUrl lookups)
                rel_path = file_path.relative_to(self.angular_root)
                rel_path_str = str(rel_path)
                
                # Create a template URL version to match against route definitions
                # Handle various common template path formats
                if rel_path_str.startswith(self.template_prefix):
                    template_url = rel_path_str[len(self.template_prefix):]
                else:
                    template_url = rel_path_str
                
                # Also create a version with 'views/' prefix which is common
                if not template_url.startswith('views/') and not template_url.startswith('/views/'):
                    views_template_url = f"views/{template_url}"
                else:
                    views_template_url = template_url
                
                # Store both paths to increase chance of matching with route templateUrls
                self.templates[template_url] = str(file_path)
                self.templates[views_template_url] = str(file_path)
                
                # Also clean paths for better matching with route templateUrls
                clean_url = template_url.lstrip('/')
                if clean_url != template_url:
                    self.templates[clean_url] = str(file_path)
                
                # For templates in b-tmpl, also index them with a special prefix used in routes
                if 'b-tmpl' in rel_path_str:
                    tmpl_name = file_path.name
                    self.templates[f'b-tmpl/{tmpl_name}'] = str(file_path)
                    self.templates[f'views/b-tmpl/{tmpl_name}'] = str(file_path)
            except Exception as e:
                print(f"Warning: Could not process template {file_path}: {e}")
        
        print(f"Found {len(self.templates)} template paths for {len(template_files)} template files")
        
        # Additional pass to match templates mentioned in routes
        print("Matching templates from routes...")
        templates_from_routes_count = 0
        
        for route in self.routes:
            template_url = route.get('templateUrl')
            if template_url and template_url not in self.templates:
                # Try to find the template file
                # First check with template prefix
                potential_path = self.angular_root / self.template_prefix / template_url.lstrip('/')
                if potential_path.exists():
                    self.templates[template_url] = str(potential_path)
                    templates_from_routes_count += 1
                    continue
                
                # Then try plain path
                potential_path = self.angular_root / template_url.lstrip('/')
                if potential_path.exists():
                    self.templates[template_url] = str(potential_path)
                    templates_from_routes_count += 1
                    continue
                
                # Then try with views prefix
                if not template_url.startswith('views/'):
                    potential_path = self.angular_root / 'views' / template_url.lstrip('/')
                    if potential_path.exists():
                        self.templates[template_url] = str(potential_path)
                        templates_from_routes_count += 1
                        continue
                
                # Finally, for b-tmpl files, try direct path to b-tmpl
                if 'b-tmpl' in template_url:
                    tmpl_name = template_url.split('/')[-1]
                    potential_path = self.b_tmpl_path / tmpl_name
                    if potential_path.exists():
                        self.templates[template_url] = str(potential_path)
                        templates_from_routes_count += 1
                        continue
        
        print(f"Added {templates_from_routes_count} additional templates from route definitions")
    
    def analyze_services(self) -> None:
        """
        Find and analyze all services
        """
        print("Analyzing services...")
        
        # Find all JS files for service analysis
        service_files = []
        
        # First check b-services directory
        if self.b_services_path and self.b_services_path.exists():
            for file_path in self.b_services_path.glob('**/*.js'):
                if not self._should_ignore(file_path):
                    service_files.append(file_path)
            print(f"Found {len(service_files)} service files in b-services directory")
        
        # Also check standard services directory
        services_path = self.scripts_path / 'services'
        if services_path.exists():
            for file_path in services_path.glob('**/*.js'):
                if not self._should_ignore(file_path):
                    service_files.append(file_path)
        
        # Also look for service definitions in all JS files
        for file_path in self.scripts_path.glob('**/*.js'):
            if not self._should_ignore(file_path) and file_path not in service_files:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    if any(pattern in content for pattern in ['.service(', '.factory(', '.provider(', '.constant(', '.value(']):
                        service_files.append(file_path)
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
        
        print(f"Found {len(service_files)} service files in total (after filtering)")
        
        # Patterns for different Angular service types
        patterns = {
            'factory': r"\.factory\s*\(\s*['\"]([^'\"]+)['\"]",
            'service': r"\.service\s*\(\s*['\"]([^'\"]+)['\"]", 
            'provider': r"\.provider\s*\(\s*['\"]([^'\"]+)['\"]",
            'value': r"\.value\s*\(\s*['\"]([^'\"]+)['\"]",
            'constant': r"\.constant\s*\(\s*['\"]([^'\"]+)['\"]"
        }
        
        # Also look for $resource factory definitions which are common in RESTful APIs
        resource_pattern = r"\$resource\s*\(\s*['\"]([^'\"]+)['\"]"
        
        for file_path in service_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                relative_path = file_path.relative_to(self.angular_root)
                
                # Find all types of service definitions
                for service_type, pattern in patterns.items():
                    matches = re.findall(pattern, content)
                    for service_name in matches:
                        self.services[service_name] = str(relative_path)
                        # Tag service with its type
                        self.services[f"{service_type}:{service_name}"] = str(relative_path)
                
                # Look for Resource definitions for RESTful services (used with $resource)
                if '$resource' in content:
                    resource_matches = re.findall(resource_pattern, content)
                    for endpoint in resource_matches:
                        # For resource endpoints, we store them with a special prefix
                        endpoint_name = f"Resource:{endpoint}"
                        self.services[endpoint_name] = str(relative_path)
                
                # Also analyze file dependencies for services
                self._analyze_file_dependencies(file_path, content)
            except Exception as e:
                print(f"Warning: Could not analyze file {file_path}: {e}")
        
        print(f"Found {len(self.services)} services and API endpoints")
    
    def analyze_directives(self) -> None:
        """
        Find and analyze all directives
        """
        print("Analyzing directives...")
        
        # Search for directives in b-directives folder and other script folders
        all_directive_files = []
        
        # Check b-directives folder
        b_directives_path = self.scripts_path / 'b-directives'
        if b_directives_path.exists():
            for file_path in b_directives_path.glob('**/*.js'):
                if not self._should_ignore(file_path):
                    all_directive_files.append(file_path)
        
        # Check directives folder
        directives_path = self.scripts_path / 'directives'
        if directives_path.exists():
            for file_path in directives_path.glob('**/*.js'):
                if not self._should_ignore(file_path):
                    all_directive_files.append(file_path)
        
        print(f"Found {len(all_directive_files)} JS files to analyze for directives (after filtering)")
        
        for file_path in all_directive_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Extract directive names
                directive_matches = re.findall(r"\.directive\(['\"]([^'\"]+)['\"]", content)
                
                for directive_name in directive_matches:
                    relative_path = file_path.relative_to(self.angular_root)
                    self.directives[directive_name] = str(relative_path)
                    
                    # Analyze directive dependencies
                    self._analyze_file_dependencies(file_path, content)
            except Exception as e:
                print(f"Warning: Could not analyze directive file {file_path}: {e}")
        
        print(f"Found {len(self.directives)} directives")
    
    def analyze_filters(self) -> None:
        """
        Find and analyze all filters
        """
        print("Analyzing filters...")
        
        # Search for filters in b-filters folder and throughout scripts
        filter_files = []
        
        # Check b-filters folder
        b_filters_path = self.scripts_path / 'b-filters'
        if b_filters_path.exists():
            for file_path in b_filters_path.glob('**/*.js'):
                if not self._should_ignore(file_path):
                    filter_files.append(file_path)
        
        # Also check all JS files for filters
        for file_path in self.scripts_path.glob('**/*.js'):
            if not self._should_ignore(file_path) and file_path not in filter_files:
                filter_files.append(file_path)
        
        print(f"Found {len(filter_files)} JS files to analyze for filters (after filtering)")
        
        for file_path in filter_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Extract filter names
                filter_matches = re.findall(r"\.filter\(['\"]([^'\"]+)['\"]", content)
                
                for filter_name in filter_matches:
                    relative_path = file_path.relative_to(self.angular_root)
                    self.filters[filter_name] = str(relative_path)
            except Exception as e:
                print(f"Warning: Could not analyze filter file {file_path}: {e}")
        
        print(f"Found {len(self.filters)} filters")
    
    def analyze_modules(self) -> None:
        """
        Find and analyze all Angular modules
        """
        print("Analyzing modules...")
        
        # Search in b-modules and modules directories
        module_files = []
        
        # Check b-modules folder
        b_modules_path = self.scripts_path / 'b-modules'
        if b_modules_path.exists():
            for file_path in b_modules_path.glob('**/*.js'):
                if not self._should_ignore(file_path):
                    module_files.append(file_path)
        
        # Check modules folder
        modules_path = self.scripts_path / 'modules'
        if modules_path.exists():
            for file_path in modules_path.glob('**/*.js'):
                if not self._should_ignore(file_path):
                    module_files.append(file_path)
        
        print(f"Found {len(module_files)} JS files to analyze for modules (after filtering)")
        
        for file_path in module_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Extract module names
                module_matches = re.findall(r"angular\.module\(['\"]([^'\"]+)['\"]", content)
                
                for module_name in module_matches:
                    relative_path = file_path.relative_to(self.angular_root)
                    self.modules[module_name] = str(relative_path)
                    
                    # Analyze module dependencies
                    self._analyze_file_dependencies(file_path, content)
            except Exception as e:
                print(f"Warning: Could not analyze module file {file_path}: {e}")
        
        print(f"Found {len(self.modules)} modules")
    
    def analyze_styles(self) -> None:
        """
        Find and analyze all style files
        """
        print("Analyzing styles...")
        
        # Check if styles directory exists
        if not self.styles_path.exists():
            print(f"Warning: Styles path {self.styles_path} does not exist")
            
        # Look for all style files in the app directory
        style_extensions = ['.css', '.scss', '.sass', '.less']
        style_files = []
        
        for ext in style_extensions:
            for file_path in self.app_path.glob(f'**/*{ext}'):
                if not self._should_ignore(file_path):
                    style_files.append(file_path)
        
        print(f"Found {len(style_files)} style files (after filtering)")
        
        for file_path in style_files:
            try:
                relative_path = file_path.relative_to(self.angular_root)
                self.styles[str(relative_path)] = str(file_path)
                
                # For SASS/SCSS files, check for imports
                if file_path.suffix in ['.scss', '.sass']:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    # Extract imports
                    import_matches = re.findall(r'@import\s+[\'"]([^\'"]+)[\'"]', content)
                    
                    if import_matches:
                        file_key = str(relative_path)
                        if file_key not in self.file_dependencies:
                            self.file_dependencies[file_key] = set()
                            
                        for import_path in import_matches:
                            self.file_dependencies[file_key].add(import_path)
            except Exception as e:
                print(f"Warning: Could not analyze style file {file_path}: {e}")
        
        print(f"Found {len(self.styles)} style files")
    
    def analyze_assets(self) -> None:
        """
        Find and catalog all assets (images, fonts, etc.)
        """
        print("Analyzing assets...")
        
        # Check assets directories
        asset_paths = [
            self.assets_path,
            self.fonts_path,
            self.images_path
        ]
        
        asset_extensions = [
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',  # Images
            '.woff', '.woff2', '.ttf', '.eot', '.otf',        # Fonts
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',         # Documents
            '.mp3', '.mp4', '.webm', '.ogg'                   # Media
        ]
        
        for base_path in asset_paths:
            if not base_path.exists():
                print(f"Warning: Asset path {base_path} does not exist")
                continue
                
            for ext in asset_extensions:
                for file_path in base_path.glob(f'**/*{ext}'):
                    if not self._should_ignore(file_path):
                        try:
                            relative_path = file_path.relative_to(self.angular_root)
                            self.assets[str(relative_path)] = str(file_path)
                        except Exception as e:
                            print(f"Warning: Could not process asset {file_path}: {e}")
        
        print(f"Found {len(self.assets)} assets")
    
    def analyze_vendor_libraries(self) -> None:
        """
        Find and analyze selected vendor libraries (excluding the ones in ignore list)
        """
        print("Analyzing vendor libraries...")
        
        vendor_path = self.scripts_path / 'vendor'
        if not vendor_path.exists():
            print(f"Warning: Vendor directory {vendor_path} does not exist")
            return
            
        # Collect specific vendor libraries that are not in ignore list
        vendor_libs_to_include = []
        for lib_dir in vendor_path.iterdir():
            if lib_dir.is_dir():
                # Skip if the entire vendor directory is in ignore list
                if any(ignore_dir in str(lib_dir.relative_to(self.angular_root)) for ignore_dir in self.ignore_dirs):
                    continue
                
                # Only include explicitly allowed vendor libraries
                lib_name = lib_dir.name
                if lib_name in ['angular-qrcode', 'barcode-generator', 'qrcode-generator', 'slider', 'table-to-excel', 'ui-router', 'ui-bootstrap']:
                    vendor_libs_to_include.append(lib_dir)
                    
        # Process selected vendor libraries
        for lib_dir in vendor_libs_to_include:
            lib_name = lib_dir.name
            lib_files = []
            
            for file_path in lib_dir.glob('**/*.js'):
                # Apply stricter minified file filtering
                if not self._should_ignore(file_path) and not self._is_vendor_or_minified(str(file_path)):
                    lib_files.append(file_path)
            
            if lib_files:
                self.vendor_libs[lib_name] = [str(f.relative_to(self.angular_root)) for f in lib_files]
                print(f"  - Found vendor library: {lib_name} with {len(lib_files)} files")
        
        print(f"Found {len(self.vendor_libs)} vendor libraries (after filtering)")
    
    def _analyze_file_dependencies(self, file_path: Path, content: str) -> None:
        """
        Analyze dependencies in a JavaScript file
        
        Args:
            file_path: Path to the file
            content: File content
        """
        relative_path = str(file_path.relative_to(self.angular_root))
        
        if relative_path not in self.file_dependencies:
            self.file_dependencies[relative_path] = set()
            
        # Look for Angular module dependencies
        module_dep_match = re.search(r"angular\.module\(['\"][^'\"]+['\"],\s*\[(.*?)\]", content, re.DOTALL)
        if module_dep_match:
            deps = module_dep_match.group(1)
            module_deps = re.findall(r"['\"]([^'\"]+)['\"]", deps)
            
            for dep in module_deps:
                self.file_dependencies[relative_path].add(dep)
                
        # Look for service injections
        service_match = re.search(r"function\s*\((.*?)\)", content)
        if service_match:
            params = service_match.group(1)
            param_list = [p.strip() for p in params.split(',')]
            
            # Map to actual services (this is approximate)
            for param in param_list:
                if param and not param.startswith('$'):  # Skip Angular built-in services
                    self.file_dependencies[relative_path].add(param)
    
    def analyze_html_dependencies(self) -> None:
        """
        Analyze dependencies in HTML templates
        """
        print("Analyzing HTML dependencies...")
        
        # Process all HTML files
        for template_url, file_path in self.templates.items():
            try:
                path = Path(file_path)
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Look for directive usages
                directive_usages = set()
                
                # Convert directive names to kebab-case (how they appear in HTML)
                for directive_name in self.directives.keys():
                    # Convert camelCase to kebab-case
                    kebab = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', directive_name).lower()
                    
                    # Check if directive is used in template
                    if kebab in content or directive_name in content:
                        directive_usages.add(directive_name)
                
                if directive_usages:
                    if template_url not in self.file_dependencies:
                        self.file_dependencies[template_url] = set()
                    
                    self.file_dependencies[template_url].update(directive_usages)
            except Exception as e:
                print(f"Warning: Could not analyze HTML dependencies in {file_path}: {e}")
        
        print("Completed HTML dependency analysis")
    
    def analyze_dependencies(self) -> Dict[str, List[str]]:
        """
        Analyze dependencies between components
        """
        print("Analyzing dependencies...")
        
        dependencies = {}
        
        # Check controller dependencies
        for controller_name, path in self.controllers.items():
            full_path = self.angular_root / path
            if not full_path.exists():
                continue
                
            content = full_path.read_text(encoding='utf-8')
            
            # Look for injected services
            injection_match = re.search(r"controller\(['\"].*?['\"],\s*\[(.*?)\]", content, re.DOTALL)
            if injection_match:
                injections = injection_match.group(1)
                # Extract service names
                services = re.findall(r"['\"]([^'\"]+)['\"]", injections)
                
                # Filter out built-in Angular services
                external_services = [s for s in services if not s.startswith('$')]
                
                # Deduplicate services
                if external_services:
                    # Remove duplicates while preserving order
                    seen = set()
                    dependencies[controller_name] = [s for s in external_services if not (s in seen or seen.add(s))]
        
        return dependencies
    
    def analyze_codebase(self) -> None:
        """
        Run all analysis steps
        """
        self.analyze_routes()
        # return
        self.analyze_controllers()
        self.analyze_templates()
        self.analyze_services()
        self.analyze_directives()
        self.analyze_filters()
        self.analyze_modules()
        self.analyze_styles()
        self.analyze_assets()
        self.analyze_vendor_libraries()
        self.analyze_html_dependencies()
        
        print("Completed full codebase analysis")
    
    def generate_analysis_report(self) -> Dict:
        """
        Generate a comprehensive analysis report of the Angular codebase
        
        Returns:
            Dict containing the analysis results
        """
        print("Generating analysis report...")
        
        # Map controllers to routes for reference
        controller_to_routes = {}
        for route in self.routes:
            controller = route.get('controller')
            if controller:
                if controller not in controller_to_routes:
                    controller_to_routes[controller] = []
                controller_to_routes[controller].append(route['name'])
                
            # Check for controllers in views
            for view_name, view_data in route.get('views', {}).items():
                view_controller = view_data.get('controller')
                if view_controller:
                    if view_controller not in controller_to_routes:
                        controller_to_routes[view_controller] = []
                    controller_to_routes[view_controller].append(f"{route['name']} (view: {view_name})")
        
        # Prepare routes for the report
        routes_for_report = []
        
        # Count routes before filtering
        total_routes_before_filtering = len(self.routes)
        
        # Get all lazy-loaded plugins from routes
        all_plugins = []
        for route in self.routes:
            plugins = route.get('plugins', [])
            if plugins:
                all_plugins.extend(plugins)
        
        # Deduplicate plugins
        unique_plugins = []
        seen_plugins = set()
        for plugin in all_plugins:
            # Skip minified files that don't add value in the migration
            if not self._is_vendor_or_minified(plugin):
                if plugin not in seen_plugins:
                    seen_plugins.add(plugin)
                    unique_plugins.append(plugin)
        
        # Process each route
        for route in self.routes:
            # Create a clean route object for the report
            route_for_report = {
                'name': route['name'],
                'url': route['url'],
                'controller': route['controller'],
                'templateUrl': route['templateUrl'],
                'parent': route['parent'],
                'abstract': route['abstract'],
                'type': route['type'],
                'views': route['views'],
                'template': route['template'],
                'resolve_dependencies': route['resolve_dependencies'].copy() if route['resolve_dependencies'] else [],
                'plugins': route['plugins'].copy() if route['plugins'] else []
            }
            
            # Include special properties
            if 'redirectTo' in route:
                route_for_report['redirectTo'] = route['redirectTo']
            
            # Ensure all routes have expected properties
            expected_props = ['name', 'url', 'controller', 'templateUrl', 'parent', 'abstract', 'views', 'template', 'resolve_dependencies', 'plugins']
            for prop in expected_props:
                if prop not in route_for_report:
                    route_for_report[prop] = None
            
            # Include the route in the report
            routes_for_report.append(route_for_report)
        
        # Don't filter out routes with missing properties, as they might be valid
        # Instead, log them for diagnostic purposes
        routes_missing_props = [r['name'] for r in routes_for_report 
                               if not r['url'] and 
                                  not r['controller'] and 
                                  not r['templateUrl'] and 
                                  not r['views'] and 
                                  not r['template']]
        
        if routes_missing_props:
            print(f"Warning: Found {len(routes_missing_props)} routes with missing properties.")
            print("These routes will still be included in the report for completeness.")
        
        # Filter out minified or vendor files from collections (but keep in original data)
        filtered_controllers = {}
        for name, path in self.controllers.items():
            if not self._is_vendor_or_minified(path):
                filtered_controllers[name] = path
                
        filtered_services = {}
        for name, path in self.services.items():
            if not self._is_vendor_or_minified(path):
                filtered_services[name] = path
                
        filtered_directives = {}
        for name, path in self.directives.items():
            if not self._is_vendor_or_minified(path):
                filtered_directives[name] = path
                
        filtered_filters = {}
        for name, path in self.filters.items():
            if not self._is_vendor_or_minified(path):
                filtered_filters[name] = path
                
        filtered_modules = {}
        for name, path in self.modules.items():
            if not self._is_vendor_or_minified(path):
                filtered_modules[name] = path
                
        filtered_styles = {}
        for name, path in self.styles.items():
            if not self._is_vendor_or_minified(path):
                filtered_styles[name] = path
                
        filtered_assets = {}
        for name, path in self.assets.items():
            if not self._is_vendor_or_minified(path):
                filtered_assets[name] = path
        
        # Filter dependencies
        filtered_dependencies = {}
        for module, deps in self.analyze_dependencies().items():
            filtered_deps = self._filter_dependencies(deps)
            if filtered_deps:  # Only include if there are deps after filtering
                filtered_dependencies[module] = filtered_deps
        
        # Print count comparison for debugging
        print("\nCount comparison (original -> filtered):")
        print(f"Routes: {total_routes_before_filtering} -> {len(routes_for_report)}")
        print(f"Controllers: {len(self.controllers)} -> {len(filtered_controllers)}")
        print(f"Services: {len(self.services)} -> {len(filtered_services)}")
        print(f"Directives: {len(self.directives)} -> {len(filtered_directives)}")
        print(f"Filters: {len(self.filters)} -> {len(filtered_filters)}")
        print(f"Modules: {len(self.modules)} -> {len(filtered_modules)}")
        
        # Calculate the total count of lazy-loaded plugins
        total_plugins = len(unique_plugins)
        
        # Create the comprehensive analysis report
        report = {
            'angular_root': str(self.angular_root),
            'routes': routes_for_report,
            'controllers': filtered_controllers,
            'services': filtered_services,
            'directives': filtered_directives,
            'filters': filtered_filters,
            'modules': filtered_modules,
            'styles': filtered_styles,
            'assets': filtered_assets,
            'dependencies': filtered_dependencies,
            'vendor_libraries': self.vendor_libs,
            'plugins': unique_plugins,
            'templates': self.templates,
            'summary': {
                'routes_count': len(routes_for_report),
                'controllers_count': len(filtered_controllers),
                'services_count': len(filtered_services),
                'directives_count': len(filtered_directives),
                'filters_count': len(filtered_filters),
                'modules_count': len(filtered_modules),
                'styles_count': len(filtered_styles),
                'assets_count': len(filtered_assets),
                'templates_count': len(self.templates),
                'plugins_count': total_plugins,
                'total_files': (
                    len(filtered_controllers) + 
                    len(filtered_services) + 
                    len(filtered_directives) + 
                    len(filtered_filters) + 
                    len(filtered_modules) + 
                    len(filtered_styles) + 
                    len(filtered_assets) + 
                    len(self.templates) +
                    total_plugins
                )
            }
        }
        
        # Add complexity estimate
        report['complexity'] = self.estimate_migration_complexity()
        
        print("Analysis report generated successfully")
        return report
    
    def estimate_migration_complexity(self) -> Dict:
        """
        Estimate the complexity of migration for different parts of the codebase
        """
        # Count complex features in the codebase
        complex_features = {
            "custom_directives": 0,
            "complex_controllers": 0,
            "large_templates": 0,
            "resolves_with_lazy_loading": 0,
            "nested_views": 0,
            "resource_services": 0,
            "data_tables": 0,
            "custom_filters": 0
        }
        
        # Check for complex controllers (large files, many dependencies)
        for controller_name, path in self.controllers.items():
            try:
                full_path = self.angular_root / path
                if not full_path.exists():
                    continue
                    
                content = full_path.read_text(encoding='utf-8')
                
                # Count lines of code
                lines = content.count('\n')
                
                if lines > 200:
                    complex_features["complex_controllers"] += 1
                
                # Look for data table usage
                if 'DataTable' in content or 'datatable' in content.lower() or 'ngTable' in content:
                    complex_features["data_tables"] += 1
            except Exception as e:
                print(f"Warning: Could not analyze controller complexity for {path}: {e}")
        
        # Check for complex services
        for service_name, path in self.services.items():
            try:
                if service_name.startswith("Resource:") or "Resource" in service_name:
                    complex_features["resource_services"] += 1
            except Exception as e:
                print(f"Warning: Could not analyze service complexity for {service_name}: {e}")
        
        # Check for routes with lazy loading
        for route in self.routes:
            if route.get('plugins'):
                complex_features["resolves_with_lazy_loading"] += 1
                
            # Check for nested views
            if route.get('views') and len(route.get('views', {})) > 0:
                complex_features["nested_views"] += 1
        
        # Check for large templates
        for template_url, path in self.templates.items():
            try:
                template_path = Path(path)
                if not template_path.exists():
                    continue
                    
                content = template_path.read_text(encoding='utf-8')
                
                # Count lines of code
                lines = content.count('\n')
                
                if lines > 300:
                    complex_features["large_templates"] += 1
                    
                # Look for custom directives
                custom_directive_matches = re.findall(r"ng-[a-z\-]+=", content)
                complex_features["custom_directives"] += len(set(custom_directive_matches))
                
                # Look for data tables
                if 'datatable' in content.lower() or 'data-table' in content.lower() or 'dt-' in content:
                    complex_features["data_tables"] += 1
            except Exception as e:
                print(f"Warning: Could not analyze template complexity for {path}: {e}")
        
        # Custom filters add complexity
        complex_features["custom_filters"] = len(self.filters)
        
        # Calculate complexity scores
        complexity = {
            "overall_score": 0,
            "details": complex_features,
            "migration_time_estimate": ""
        }
        
        # Calculate overall score with weighted factors
        score = (
            complex_features["complex_controllers"] * 5 + 
            complex_features["large_templates"] * 3 + 
            complex_features["custom_directives"] * 2 +
            complex_features["resolves_with_lazy_loading"] * 4 +
            complex_features["nested_views"] * 3 +
            complex_features["resource_services"] * 2 +
            complex_features["data_tables"] * 4 +
            complex_features["custom_filters"] * 1
        )
        
        # Normalize to 0-100 scale
        routes_count = len(self.routes)
        if routes_count > 0:
            normalized_score = min(100, score / routes_count * 20)
        else:
            normalized_score = 0
            
        complexity["overall_score"] = round(normalized_score)
        
        # Provide time estimate
        if normalized_score < 30:
            complexity["migration_time_estimate"] = "1-2 weeks"
        elif normalized_score < 60:
            complexity["migration_time_estimate"] = "2-4 weeks"
        else:
            complexity["migration_time_estimate"] = "4+ weeks"
        
        # Add specific recommendations
        complexity["recommendations"] = []
        
        if complex_features["resolves_with_lazy_loading"] > 0:
            complexity["recommendations"].append("Replace $ocLazyLoad with Next.js dynamic imports")
            
        if complex_features["data_tables"] > 0:
            complexity["recommendations"].append("Migrate DataTables to a React-compatible library like react-table or MUI X DataGrid")
            
        if complex_features["resource_services"] > 0:
            complexity["recommendations"].append("Convert $resource services to API Routes and React Query or SWR for data fetching")
            
        if complex_features["nested_views"] > 0:
            complexity["recommendations"].append("Convert nested UI-Router views to nested React components or layouts")
        
        return complexity

    def _is_vendor_or_minified(self, path: str) -> bool:
        """
        Check if a file path is from vendor directory or is a minified file
        
        Args:
            path: File path to check
            
        Returns:
            bool: True if path is vendor or minified, False otherwise
        """
        # Check for vendor paths (more comprehensive)
        vendor_indicators = [
            'vendor/', '/vendor/', 'scripts/vendor',
            'angular-', 'jquery', 'bootstrap', 
            'datatables', 'footable', 'flot', 
            'jqvmap', 'magnific', 'mixitup',
            'slider', 'touchspin', 'qrcode', 'barcode',
            # Add common vendor library paths
            'Scripts/vendor', '/vendor/js/', '/vendor/css/',
            'libs/', '/lib/', 'node_modules/'
        ]
        
        # Custom vendor libraries that should not be filtered out
        allowed_vendor_libs = [
            'angular-qrcode', 'qrcode-generator', 'barcode-generator', 
            'slider', 'table-to-excel', 'ui-router', 'ui-bootstrap'
        ]
        
        # If path contains an allowed vendor library, don't consider it a vendor path
        if any(lib in path.lower() for lib in allowed_vendor_libs):
            return False
            
        if any(indicator in path.lower() for indicator in vendor_indicators):
            return True
            
        # Check for minified files or bundles - more comprehensive patterns
        minified_indicators = [
            '.min.js', '.min.css', '-min.js', '-min.css',
            '.bundle.js', '.bundle.css', '.pack.js',
            '.compiled.js', '.prod.js', '.compressed.js',
            'dist.js', 'compressed.css', 'minimized.js',
            # Common vendor minified files
            'jquery.min.js', 'angular.min.js', 'bootstrap.min.js',
            'bootstrap.min.css', 'all.min.css', 'app.min.js',
            # DataTables and other library minified files
            'datatables.min.js', 'dataTables.bootstrap.min.js',
            'jquery.dataTables', 'alasql.min.js', 'xlsx.core.min.js',
            'input.js', 'columnFilter.js', 'filestyle.min.js',
            'barcode.css', '.googleapis.com', 'cloudflare.com'
        ]
        
        # More aggressive check for minified files
        # Look for patterns in the file path
        if any(indicator in path.lower() for indicator in minified_indicators):
            return True
            
        # Check filename length (many minified files have very long names with numbers)
        filename = os.path.basename(path)
        if len(filename) > 50 and any(c.isdigit() for c in filename):
            return True
            
        return False

    def _filter_dependencies(self, dependencies: List[str]) -> List[str]:
        """
        Filter a list of dependencies to:
        1. Remove vendor and minified files (except for allowed ones)
        2. Only include actual files with recognizable extensions
        3. Include Angular module names without extensions
        
        Args:
            dependencies: List of dependencies to filter
            
        Returns:
            List[str]: Filtered list of dependencies
        """
        if not dependencies:
            return []
        
        # File extensions to include - expanded list for better coverage
        file_extensions = [
            '.js', '.css', '.html', '.json', '.svg', '.png', '.jpg', '.jpeg', '.gif',
            '.tpl.html', '.template.html', '.component.js', '.service.js', '.factory.js',
            '.directive.js', '.filter.js', '.provider.js', '.controller.js', '.module.js'
        ]
        
        filtered_deps = []
        for dep in dependencies:
            # Skip vendor or minified files unless specifically allowed
            if self._is_vendor_or_minified(dep):
                continue
                
            # Include dependencies with recognizable extensions
            if any(dep.lower().endswith(ext) for ext in file_extensions):
                filtered_deps.append(dep)
            # Include Angular module names (no extension)
            elif '.' not in os.path.basename(dep) and len(dep) > 3:
                # Skip common non-dependency strings
                if dep.lower() not in ['true', 'false', 'null', 'undefined', 'function', 'return', 
                                     'const', 'let', 'var', 'this']:
                    filtered_deps.append(dep)
                
        return filtered_deps
        
    def _verify_state_definitions(self, content: str) -> None:
        """
        Verify state definitions against the original content
        
        Args:
            content: Content of the app.js file
        """
        print(f"Verifying state definitions...")
        
        # Count raw occurrences of .state( for diagnostic purposes
        raw_state_count = content.count('.state(')
        
        # Counters for verification statistics
        total_verified = 0
        controller_fixes = 0
        template_fixes = 0
        verified_with_issues = 0
        not_found_in_content = 0
        
        # Set to track verified routes
        verified_routes = set()
        
        for route in self.routes:
            state_name = route['name']
            verification = self._verify_state_definition(state_name, content)
            verified_routes.add(state_name)
            total_verified += 1
            
            # Check and fix controller
            if not verification['controller'] and route['controller']:
                original_controller = route['controller']
                route['controller'] = None
                print(f"Verification fix: Removed incorrect controller '{original_controller}' from '{state_name}' state")
                controller_fixes += 1
                verified_with_issues += 1
            
            # Check and fix template
            if not verification['template'] and route['template']:
                original_template = route['template']
                route['template'] = None
                print(f"Verification fix: Removed incorrect template '{original_template}' from '{state_name}' state")
                template_fixes += 1
                verified_with_issues += 1
                
            # Track states not found in the original content
            if not verification['controller'] and not verification['template']:
                # This means the verification couldn't find the state definition
                if state_name not in ['root', 'app']:  # Skip common parent states often not explicitly defined
                    not_found_in_content += 1
        
        # Print verification statistics
        print("\nState Verification Statistics:")
        print(f"  - Raw '.state(' occurrences in file: {raw_state_count}")
        print(f"  - Routes in analysis: {len(self.routes)}")
        print(f"  - Routes verified: {total_verified}")
        if controller_fixes > 0:
            print(f"  - Controller fixes: {controller_fixes}")
        if template_fixes > 0:
            print(f"  - Template fixes: {template_fixes}")
        if verified_with_issues > 0:
            print(f"  - Routes with verification fixes: {verified_with_issues}")
        if not_found_in_content > 0:
            print(f"  - Routes not found in original content: {not_found_in_content}")
            
        # Explain verification outcome
        if controller_fixes > 0 or template_fixes > 0:
            print("\nVerification found and fixed issues with route definitions.")
            print("This typically happens when the state extraction process infers properties that are not in the original state definition.")
        else:
            print("\nVerification completed with no issues found.")
            
        # Explain discrepancy between raw state count and processed routes
        if raw_state_count > len(self.routes):
            print(f"\nNote: The raw count of '.state(' occurrences ({raw_state_count}) is higher than the number of processed routes ({len(self.routes)}).")
            print("This is normal and can be due to:")
            print("  - Commented-out state definitions")
            print("  - Duplicate state definitions")
            print("  - States excluded by patterns (technical/utility states)")
            print("  - Abstract states (excluded from final routes)")
            print("  - States with parsing errors")
            
        print(f"\nState verification complete")

    def _verify_state_definition(self, state_name: str, app_js_content: str) -> Dict[str, bool]:
        """
        Verify a state definition against the original app.js file
        
        Args:
            state_name: The name of the state to verify
            app_js_content: The content of app.js
            
        Returns:
            Dict containing verification results for each property
        """
        verification = {
            'controller': False,
            'template': False
        }
        
        # Find the state definition in app.js - more flexible pattern
        state_patterns = [
            fr"\.state\(\s*['\"]({state_name})['\"](?:\s*,\s*|\s*,\s*\n\s*)(\{{[\s\S]*?\}})",
            fr"\.state\(\s*\{{[\s\S]*?name\s*:\s*['\"]({state_name})['\"][\s\S]*?\}}",
            fr"\.state\(['\"]({state_name})['\"][\s\S]*?\{{([\s\S]*?)\}}\s*\)"
        ]
        
        for pattern in state_patterns:
            state_matches = re.findall(pattern, app_js_content, re.MULTILINE)
            
            if state_matches:
                for match in state_matches:
                    name = match[0]
                    config = match[1] if len(match) > 1 else ""
                    
                    if name == state_name:
                        # Verify controller presence
                        if 'controller:' in config or 'controller :' in config:
                            verification['controller'] = True
                        
                        # Verify template presence
                        if 'template:' in config or 'template :' in config:
                            verification['template'] = True
                        
                        # If we found it, we can break
                        if verification['controller'] and verification['template']:
                            break
        
        return verification

    def find_views_dir(self) -> Path:
        """
        Find the views directory, trying various common locations
        """
        possible_locations = [
            self.angular_root / 'app' / 'views',
            self.angular_root / 'views',
            self.angular_root / 'src' / 'views',
            self.angular_root / 'src' / 'app' / 'views',
            self.angular_root / 'templates',
            self.angular_root / 'src' / 'templates'
        ]
        
        for location in possible_locations:
            if location.exists() and location.is_dir():
                print(f"Found views directory at {location}")
                return location
        
        print("Warning: Could not find views directory. Using default path.")
        return self.angular_root / 'app' / 'views'

    def find_b_controllers_dir(self) -> Path:
        """
        Find the b-controllers directory, which is common in some Angular apps
        """
        possible_locations = [
            self.angular_root / 'app' / 'scripts' / 'b-controllers',
            self.scripts_path / 'b-controllers',
            self.angular_root / 'app' / 'b-controllers',
            self.angular_root / 'scripts' / 'b-controllers',
            self.angular_root / 'js' / 'b-controllers'
        ]
        
        for location in possible_locations:
            if location.exists() and location.is_dir():
                print(f"Found b-controllers directory at {location}")
                return location
        
        print("Warning: Could not find b-controllers directory.")
        return self.scripts_path / 'b-controllers'

    def find_b_services_dir(self) -> Path:
        """
        Find the b-services directory, which is common in some Angular apps
        """
        possible_locations = [
            self.angular_root / 'app' / 'scripts' / 'b-services',
            self.scripts_path / 'b-services',
            self.angular_root / 'app' / 'b-services',
            self.angular_root / 'scripts' / 'b-services',
            self.angular_root / 'js' / 'b-services'
        ]
        
        for location in possible_locations:
            if location.exists() and location.is_dir():
                print(f"Found b-services directory at {location}")
                return location
        
        print("Warning: Could not find b-services directory.")
        return self.scripts_path / 'b-services'

    def find_b_tmpl_dir(self) -> Path:
        """
        Find the b-tmpl directory, which contains Angular templates in some apps
        """
        possible_locations = [
            self.angular_root / 'app' / 'views' / 'b-tmpl',
            self.views_path / 'b-tmpl',
            self.angular_root / 'app' / 'b-tmpl',
            self.angular_root / 'views' / 'b-tmpl'
        ]
        
        for location in possible_locations:
            if location.exists() and location.is_dir():
                print(f"Found b-tmpl directory at {location}")
                return location
        
        print("Warning: Could not find b-tmpl directory.")
        return self.views_path / 'b-tmpl'


def main():
    parser = argparse.ArgumentParser(description='Analyze AngularJS app for Next.js migration')
    parser.add_argument('--angular-root', type=str, required=True, help='Path to Angular project root')
    parser.add_argument('--output', type=str, default='analysis_report.json', help='Path to output report file')
    parser.add_argument('--template-prefix', type=str, default='app/', help='Prefix to remove from template paths')
    parser.add_argument('--ignore-dirs', type=str, default='v1,scripts/vendor,node_modules,dist,build,tmp', 
                      help='Comma-separated list of directories to ignore')
    parser.add_argument('--ignore-files', type=str, default='.min.js,.min.css,.spec.js,.test.js',
                      help='Comma-separated list of file patterns to ignore')
    parser.add_argument('--validate', action='store_true', help='Validate the output report')
    parser.add_argument('--skip-vendor', action='store_true', help='Skip vendor libraries analysis')
    parser.add_argument('--skip-verify', action='store_false', dest='verify_states', 
                      help='Skip state definition verification')
    
    args = parser.parse_args()
    
    try:
        # Update ignore lists from arguments
        ignore_dirs = args.ignore_dirs.split(',')
        ignore_files = args.ignore_files.split(',')
        
        start_time = time.time()
        
        print(f"Starting Angular codebase analysis of {args.angular_root}")
        print(f"Template prefix: {args.template_prefix}")
        print(f"Ignoring directories: {ignore_dirs}")
        print(f"Ignoring file patterns: {ignore_files}")
        
        analyzer = AngularCodebaseAnalyzer(
            args.angular_root, 
            template_prefix=args.template_prefix,
            verify_states=args.verify_states,
            skip_vendor=args.skip_vendor
        )
        
        # Update ignore lists
        analyzer.ignore_dirs = ignore_dirs
        analyzer.ignore_files = ignore_files
        
        analyzer.analyze_codebase()
        report = analyzer.generate_analysis_report()
        
        # Write report to file
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        
        analysis_time = time.time() - start_time
        
        print(f"Analysis complete! Report saved to {args.output}")
        print(f"Analysis completed in {analysis_time:.2f} seconds")
        
        # Validate the report if requested
        if args.validate:
            print("\nValidating analysis report...")
            validation_issues = validate_report(report)
            if validation_issues:
                print("\nValidation Issues:")
                for issue in validation_issues:
                    print(f"- {issue}")
            else:
                print("\nReport validation successful!")
        
        # Print summary to console
        print("\nSummary:")
        print(f"Total routes: {report['summary']['total_routes']}")
        print(f"Total controllers: {report['summary']['total_controllers']}")
        print(f"Total templates: {report['summary']['total_templates']}")
        print(f"Total services: {report['summary']['total_services']}")
        print(f"Total directives: {report['summary']['total_directives']}")
        print(f"Total filters: {report['summary']['total_filters']}")
        print(f"Total modules: {report['summary']['total_modules']}")
        print(f"Total styles: {report['summary']['total_styles']}")
        print(f"Total assets: {report['summary']['total_assets']}")
        print(f"Total vendor libraries: {report['summary']['total_vendor_libraries']}")
        print(f"Migration complexity score: {report['migration_complexity']['overall_score']}/100")
        print(f"Estimated migration time: {report['migration_complexity']['migration_time_estimate']}")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

def validate_report(report: Dict) -> List[str]:
    """
    Validate the analysis report to ensure critical information is present
    
    Args:
        report: Analysis report dictionary
        
    Returns:
        List of validation issues, empty if no issues found
    """
    issues = []
    
    # Check if summary information is complete
    if 'summary' not in report:
        issues.append("Missing summary section in report")
    
    # Check if routes are present
    if 'routes' not in report or not report['routes']:
        issues.append("No routes found in the analysis")
    
    # Check for missing templates
    route_templates = [r.get('templateUrl') for r in report.get('routes', []) if r.get('templateUrl')]
    if route_templates:
        found_templates = list(report.get('templates', {}).keys())
        missing_templates = []
        
        for template_url in route_templates:
            if template_url:
                # Try different template path formats
                template_found = False
                
                # Try exact match
                if template_url in found_templates:
                    template_found = True
                
                # Try with/without app/ prefix
                alt_url = f"app/{template_url}" if not template_url.startswith('app/') else template_url[4:]
                if alt_url in found_templates:
                    template_found = True
                
                # Try as suffix
                if not template_found and not any(t.endswith(template_url) for t in found_templates):
                    missing_templates.append(template_url)
        
        if missing_templates:
            issues.append(f"Found {len(missing_templates)} route templates that are missing: {missing_templates[:5]}")
    
    # Check for missing controllers
    route_controllers = [r.get('controller') for r in report.get('routes', []) if r.get('controller')]
    if route_controllers:
        found_controllers = list(report.get('controllers', {}).keys())
        missing_controllers = [c for c in route_controllers if c and c not in found_controllers]
        
        if missing_controllers:
            issues.append(f"Found {len(missing_controllers)} route controllers that are missing: {missing_controllers[:5]}")
    
    # Check for components with no dependencies
    components_with_deps = len([d for d in report.get('dependencies', {}).values() if d])
    total_components = len(report.get('controllers', {})) + len(report.get('services', {}))
    
    if total_components > 0 and components_with_deps < total_components * 0.5:
        issues.append(f"Only {components_with_deps}/{total_components} components have dependencies. Dependency detection might be incomplete.")
    
    return issues

if __name__ == "__main__":
    exit(main()) 