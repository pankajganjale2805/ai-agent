import re
from pathlib import Path
from typing import Dict, List, Set

from utils import filter_dependencies, extract_require_dependencies

def analyze_routes(app_js_path: Path, ignore_dirs: List[str], ignore_files: List[str]) -> List[Dict]:
    """
    Parse app.js to extract all route definitions
    
    Args:
        app_js_path: Path to app.js file
        ignore_dirs: List of directories to ignore
        ignore_files: List of file patterns to ignore
        
    Returns:
        List of route objects
    """
    print("Analyzing routes from app.js...")
    
    if not app_js_path.exists():
        print(f"Warning: {app_js_path} does not exist")
        return []
    
    routes = []
    content = app_js_path.read_text(encoding='utf-8')
    
    # DEBUG: Print file size
    print(f"app.js file size: {len(content)} bytes")
    
    # Count all .state occurrences to understand total potential states
    state_count = content.count('.state(')
    commented_count = 0
    
    # Count commented states using a simple heuristic
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if '//' in line and '.state(' in line[line.find('//'):]:
            commented_count += 1
        if '/*' in line and '*/' in line and '.state(' in line[line.find('/*'):line.find('*/')]:
            commented_count += 1
            
    print(f"Total .state occurrences: {state_count}, estimated commented: {commented_count}")
    
    # Also check for require.js style dependencies
    require_deps = extract_require_dependencies(content)
    if require_deps:
        # Filter vendor and minified dependencies
        filtered_require_deps = filter_dependencies(require_deps)
        print(f"Found {len(filtered_require_deps)} require.js dependencies (after filtering)")
        
    # Extract all state definitions with different regex patterns to catch all variants
    # This is a more comprehensive set of patterns to catch all state formats
    state_patterns = [
        # Standard pattern with any kind of spacing/quotes
        r"\.state\s*\(\s*(['\"])([^'\"]+)\1\s*,\s*(\{[^{]*(?:\{[^}]*\}[^{]*)*\})",
        # Another standard pattern with possible newlines
        r"\.state\s*\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*|\s*,\s*\n\s*)(\{[^{]*(?:\{[^}]*\}[^{]*)*\})",
        # Pattern with name property
        r"\.state\s*\(\s*\{[^{]*name\s*:\s*['\"]([^'\"]+)['\"][^}]*,\s*(.*?)\}\s*\)",
        # Simple patterns to catch common formats
        r"\.state\('([^']+)',\s*\{([^{}]+(?:\{[^{}]*\}[^{}]*)*)\}\)",
        r'\.state\("([^"]+)",\s*\{([^{}]+(?:\{[^{}]*\}[^{}]*)*)\}\)',
        # Abbreviated pattern
        r"\.state\([\'\"]([^\'\"]+)[\'\"],[\s\n]*(\{(?:.|\n)*?\})\)",
    ]
    
    all_states = []
    
    # First try using normal regex for each pattern
    for pattern in state_patterns:
        try:
            matches = re.findall(pattern, content, re.DOTALL)
            # Handle different match group formats
            normalized_matches = []
            for match in matches:
                if len(match) == 3:  # For patterns with 3 groups (quote, name, config)
                    normalized_matches.append((match[1], match[2]))
                else:  # For patterns with 2 groups (name, config)
                    normalized_matches.append(match)
            
            all_states.extend(normalized_matches)
            print(f"Pattern {pattern[:30]}... found {len(normalized_matches)} states")
        except re.error as e:
            print(f"Regex error with pattern {pattern[:30]}...: {e}")
            continue
            
    # If still not finding enough states, try line-by-line parsing approach
    if len(all_states) < state_count - commented_count - 10:  # Allow for some margin of error
        print(f"Only found {len(all_states)} states with regex, attempting line-by-line parse")
        
        # Line-by-line approach to handle very complex files
        state_blocks = []
        in_state_block = False
        current_block = ""
        state_name = ""
        brace_count = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip commented lines
            if stripped.startswith('//') or (stripped.startswith('/*') and '*/' in stripped):
                continue
            
            # Check for state definition start
            if '.state(' in line and not in_state_block:
                # Extract state name
                match = re.search(r"\.state\s*\(\s*['\"]([^'\"]+)['\"]", line)
                if match:
                    state_name = match.group(1)
                    in_state_block = True
                    current_block = line
                    brace_count = line.count('{') - line.count('}')
                    
                    # If state defined on a single line
                    if brace_count == 0 and line.rstrip().endswith(')'):
                        state_blocks.append((state_name, current_block))
                        in_state_block = False
                        current_block = ""
            
            # Continue collecting current state block
            elif in_state_block:
                current_block += line + "\n"
                brace_count += line.count('{') - line.count('}')
                
                # Check if block is complete
                if brace_count <= 0 and (')' in line or '})' in line):
                    # Extract config part
                    config_match = re.search(r",\s*(\{.*\})\s*\)", current_block, re.DOTALL)
                    if config_match:
                        config = config_match.group(1)
                        state_blocks.append((state_name, config))
                    else:
                        print(f"Warning: Could not extract config for state {state_name}")
                    
                    in_state_block = False
                    current_block = ""
        
        print(f"Found {len(state_blocks)} states with line-by-line parsing")
        
        # Only use line-by-line results if they found more states
        if len(state_blocks) > len(all_states):
            all_states = state_blocks
    
    # Remove duplicates by state name
    unique_states = {}
    for state_name, state_config in all_states:
        if state_name not in unique_states:
            unique_states[state_name] = state_config
            
    # Check for any states with only a name (parsing error)
    problematic_states = []
    for name, config in unique_states.items():
        if not config or len(config.strip()) < 5:  # Config too short, likely parsing error
            problematic_states.append(name)
            
    if problematic_states:
        print(f"Warning: {len(problematic_states)} states have parsing issues: {problematic_states[:5]}...")
        
    all_states = [(name, config) for name, config in unique_states.items() if name not in problematic_states]
    print(f"Found {len(all_states)} unique and valid state definitions in app.js")
    
    # Generate a list of missing states
    if len(all_states) < state_count - commented_count - 10:
        print("Warning: Many states may be missing. Consider manual inspection of app.js")
        
    # The rest of the method continues as before with dependency extraction, etc.
    full_file_deps = []
    
    # Look for dependencies defined with 'scripts/...'
    script_deps = re.findall(r'[\'"]scripts/([^\'"\s]+\.js)[\'"]', content)
    if script_deps:
        # Filter vendor and minified dependencies
        filtered_script_deps = filter_dependencies(script_deps)
        print(f"Found {len(filtered_script_deps)} script dependencies (after filtering)")
        full_file_deps.extend(filtered_script_deps)
        
    # Look for $ocLazyLoad dependencies which are common in UI-Router
    oc_lazy_match = re.search(r"\$ocLazyLoad.load\(\s*\[(.*?)\]", content, re.DOTALL)
    if oc_lazy_match:
        oc_deps = re.findall(r"['\"]([^'\"]+)['\"]", oc_lazy_match.group(1))
        if oc_deps:
            # Filter vendor and minified dependencies
            filtered_oc_deps = filter_dependencies(oc_deps)
            print(f"Found {len(filtered_oc_deps)} $ocLazyLoad dependencies (after filtering)")
            full_file_deps.extend(filtered_oc_deps)
        
    # Look for direct service injections in the main module
    module_deps = re.findall(r"angular\.module\(['\"][^'\"]+['\"],\s*\[(.*?)\]", content, re.DOTALL)
    for deps_str in module_deps:
        dep_matches = re.findall(r"['\"]([^'\"]+)['\"]", deps_str)
        if dep_matches:
            print(f"Found {len(dep_matches)} module dependencies")
            # Filter out Angular built-in modules
            filtered_deps = [d for d in dep_matches if not d.startswith('ng')]
            # Filter vendor and minified dependencies
            filtered_deps = filter_dependencies(filtered_deps)
            full_file_deps.extend(filtered_deps)
    
    # Look for any JS files that might be loaded with .js extension
    js_file_deps = re.findall(r'[\'"]([^\'"\s]+\.js)[\'"]', content)
    if js_file_deps:
        # Filter vendor and minified dependencies
        filtered_js_deps = filter_dependencies(js_file_deps)
        print(f"Found {len(filtered_js_deps)} JS file dependencies (after filtering)")
        full_file_deps.extend(filtered_js_deps)
    
    # Add CSS files too
    css_file_deps = re.findall(r'[\'"]([^\'"\s]+\.css)[\'"]', content)
    if css_file_deps:
        # Filter vendor and minified dependencies
        filtered_css_deps = filter_dependencies(css_file_deps)
        print(f"Found {len(filtered_css_deps)} CSS dependencies (after filtering)")
        full_file_deps.extend(filtered_css_deps)
    
    # Deduplicate global dependencies
    global_deps = list(set(full_file_deps + filter_dependencies(require_deps)))
    print(f"Total global dependencies found: {len(global_deps)} (after filtering)")
    
    # Process each state definition
    progress_interval = max(1, len(all_states) // 10)  # Show progress for every 10%
    for i, (state_name, state_config) in enumerate(all_states):
        # Show progress
        if i % progress_interval == 0:
            print(f"Processing state {i+1}/{len(all_states)} ({(i+1)/len(all_states)*100:.1f}%)")
            
        route_data = {
            'name': state_name,
            'url': None,
            'controller': None,
            'templateUrl': None,
            'template': None,
            'views': {},
            'resolve': [],
            'resolve_dependencies': [],
            'parent': None,
            'abstract': False,
            'type': 'ui-router'  # Default type
        }
        
        # Extract URL - handle both quote styles and the ^ character for absolute URLs
        url_match = re.search(r"url\s*:\s*['\"](\^?[^'\"]+)['\"]", state_config)
        if url_match:
            route_data['url'] = url_match.group(1)
        
        # Extract controller - completely revised approach
        route_data['controller'] = None  # Default to None
        
        # Split the state config into lines for more precise analysis
        config_lines = state_config.split('\n')
        for line in config_lines:
            line = line.strip()
            
            # Look for controller definition as a standalone property (not in a nested object)
            if re.match(r'^\s*controller\s*:', line) or re.match(r',\s*controller\s*:', line):
                # Found a controller definition at the correct level (not in a nested object)
                if "as" in line:
                    # Handle "controller as" syntax
                    match = re.search(r"controller\s*:\s*['\"]([^'\"]+)\s+as\s+([^'\"]+)['\"]", line)
                    if match:
                        route_data['controller'] = match.group(1)
                        break
                else:
                    # Handle regular controller syntax
                    match = re.search(r"controller\s*:\s*['\"]([^'\"]+)['\"]", line)
                    if match:
                        route_data['controller'] = match.group(1)
                        break
                    
                    # Try function reference (no quotes)
                    match = re.search(r"controller\s*:\s*([A-Za-z0-9_$]+)", line)
                    if match and match.group(1) not in ['true', 'false', 'null', 'undefined']:
                        route_data['controller'] = match.group(1)
                        break
        
        # Extract templateUrl - revised approach
        route_data['templateUrl'] = None  # Default to None
        
        # Look for templateUrl in each line
        for line in config_lines:
            line = line.strip()
            
            # Look for templateUrl definition as a standalone property
            if re.match(r'^\s*templateUrl\s*:', line) or re.match(r',\s*templateUrl\s*:', line):
                match = re.search(r"templateUrl\s*:\s*['\"]([^'\"]+)['\"]", line)
                if match:
                    route_data['templateUrl'] = match.group(1)
                    break
        
        # Extract template - revised approach
        route_data['template'] = None  # Default to None
        
        # Look for template in each line
        for line in config_lines:
            line = line.strip()
            
            # Look for template definition as a standalone property
            if re.match(r'^\s*template\s*:', line) or re.match(r',\s*template\s*:', line):
                # Try with quotes
                match = re.search(r"template\s*:\s*['\"]([^'\"]+)['\"]", line)
                if match:
                    route_data['template'] = match.group(1)
                    break
                
                # Try without quotes (like '<div ui-view></div>')
                match = re.search(r"template\s*:\s*([^',}\n]+)", line)
                if match:
                    route_data['template'] = match.group(1).strip()
                    break
        
        # Extract parent state
        parent_match = re.search(r"parent\s*:\s*['\"]([^'\"]+)['\"]", state_config)
        if parent_match:
            route_data['parent'] = parent_match.group(1)
        
        # Check if state is abstract
        abstract_match = re.search(r"abstract\s*:\s*(true|false)", state_config)
        if abstract_match:
            route_data['abstract'] = abstract_match.group(1) == 'true'
        
        # Extract views if defined
        views_match = re.search(r"views\s*:\s*\{([^{}]+(?:\{[^{}]*\}[^{}]*)*)\}", state_config, re.DOTALL)
        if views_match:
            views_content = views_match.group(1)
            view_pattern = r"['\"]([^'\"]+)['\"][\s\n]*:[\s\n]*\{([^{}]+)\}"
            view_matches = re.findall(view_pattern, views_content, re.DOTALL)
            
            for view_name, view_config in view_matches:
                view_data = {}
                
                # Extract view's templateUrl
                view_template_match = re.search(r"templateUrl\s*:\s*['\"]([^'\"]+)['\"]", view_config)
                if view_template_match:
                    view_data['templateUrl'] = view_template_match.group(1)
                
                # Extract view's controller
                view_controller_match = re.search(r"controller\s*:\s*['\"]([^'\"]+)['\"]", view_config)
                if view_controller_match:
                    view_data['controller'] = view_controller_match.group(1)
                
                route_data['views'][view_name] = view_data
        
        route_specific_deps = []
        
        # Check for resolve block with multiple patterns
        resolve_match = re.search(r"resolve\s*:\s*\{([^{}]+(?:\{[^{}]*\}[^{}]*)*)\}", state_config, re.DOTALL)
        if resolve_match:
            resolve_content = resolve_match.group(1)
            
            # First check for $ocLazyLoad patterns which are common in UI-Router
            oc_lazy_match = re.search(r"plugins\s*:\s*\[[^\]]*\$ocLazyLoad.load\(\s*\[(.*?)\]\s*\)", resolve_content, re.DOTALL)
            if oc_lazy_match:
                # UI-Router with $ocLazyLoad pattern
                lazy_deps = re.findall(r"['\"]([^'\"]+)['\"]", oc_lazy_match.group(1))
                if lazy_deps:
                    # Filter vendor and minified dependencies
                    filtered_lazy_deps = filter_dependencies(lazy_deps)
                    route_specific_deps.extend(filtered_lazy_deps)
            
            # Extract any strings that might be dependencies
            all_strings = re.findall(r"['\"]([^'\"]+)['\"]", resolve_content)
            potential_deps = []
            
            # Skip common keywords and look for potential service/dependency names
            common_words = ['function', 'return', 'var', 'let', 'const', 'true', 'false', 'null', 'this', 'plugins']
            for string in all_strings:
                if (not string.startswith('$') and  # Skip built-in Angular services
                    not any(word in string.lower() for word in common_words) and
                    len(string) > 2):  # Skip very short strings
                    potential_deps.append(string)
            
            # Also extract any JavaScript identifiers that might be service/dependency names
            js_identifiers = re.findall(r'(?<![\'"])([A-Za-z$_][A-Za-z0-9$_]*)', resolve_content)
            for ident in js_identifiers:
                if (not ident.startswith('$') and  # Skip built-in Angular services
                    ident not in common_words and
                    len(ident) > 2):  # Skip very short identifiers
                    potential_deps.append(ident)
            
            # Also capture script dependencies (direct .js files)
            script_deps = re.findall(r'scripts/([^\'"\s]+\.js)', resolve_content)
            for script in script_deps:
                potential_deps.append(script)
            
            # Add any identified dependencies to route-specific deps (after filtering)
            route_specific_deps.extend(filter_dependencies(potential_deps))
        
        # Look for dependencies in the entire state config
        js_files_in_state = re.findall(r'[\'"]([^\'"\s]+\.js)[\'"]', state_config) + re.findall(r'[\'"]([^\'"\s]+\.css)[\'"]', state_config)
        if js_files_in_state:
            # Filter vendor and minified dependencies
            filtered_js_files = filter_dependencies(js_files_in_state)
            route_specific_deps.extend(filtered_js_files)
        
        # Combine route-specific deps with global deps
        all_deps = route_specific_deps
        
        # If no route-specific deps were found, use global deps as fallback
        if not all_deps and global_deps:
            all_deps = global_deps
        
        # Deduplicate and store dependencies
        unique_deps = list(set(all_deps))
        route_data['resolve'] = unique_deps
        route_data['resolve_dependencies'] = unique_deps
        
        # Add state to routes list
        routes.append(route_data)
    
    print(f"Processed {len(routes)} routes from UI-Router states")
    
    # Post-processing: Verify state definitions against the original app.js file
    if app_js_path.exists():
        try:
            app_js_content = app_js_path.read_text(encoding='utf-8')
            print(f"Verifying state definitions against app.js...")
            
            for route in routes:
                state_name = route['name']
                verification = verify_state_definition(state_name, app_js_content)
                
                # Check and fix controller
                if not verification['controller'] and route['controller']:
                    original_controller = route['controller']
                    route['controller'] = None
                    print(f"Verification fix: Removed incorrect controller '{original_controller}' from '{state_name}' state")
                
                # Check and fix template
                if not verification['template'] and route['template']:
                    original_template = route['template']
                    route['template'] = None
                    print(f"Verification fix: Removed incorrect template '{original_template}' from '{state_name}' state")
            
            print(f"State verification complete")
        except Exception as e:
            print(f"Warning: Error during state verification: {e}")
            
    # After regular parsing, look for any module.config blocks that might contain routes for ngRoute
    config_pattern = r"(?:\.config\(|config\s*\(\s*function\s*\([^\)]*\)\s*\{)(.*?)(?:\}\s*\)|[,;]$)"
    config_blocks = re.findall(config_pattern, content, re.DOTALL)
    
    for config_block in config_blocks:
        # Look for $routeProvider configurations (older Angular apps)
        if "$routeProvider" in config_block:
            route_pattern = r"\.when\(['\"]([^'\"]+)['\"],\s*\{([^{}]+(?:\{[^{}]*\}[^{}]*)*)\}\)"
            route_matches = re.findall(route_pattern, config_block, re.DOTALL)
            
            for route_url, route_config in route_matches:
                route_data = {
                    'name': f"route_{len(routes)}",  # Generate a name
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
                    
                    route_specific_deps.extend(filter_dependencies(potential_deps))
                
                # Look for JS files in the entire route config
                js_files_in_route = re.findall(r'[\'"]([^\'"\s]+\.js)[\'"]', route_config)
                if js_files_in_route:
                    route_specific_deps.extend(filter_dependencies(js_files_in_route))
                
                # Combine route-specific deps with global deps
                all_deps = route_specific_deps
                
                # If no route-specific deps were found, use global deps as fallback
                if not all_deps and global_deps:
                    all_deps = global_deps
                
                # Deduplicate and store dependencies
                unique_deps = list(set(all_deps))
                route_data['resolve'] = unique_deps
                route_data['resolve_dependencies'] = unique_deps
                
                routes.append(route_data)
    
    print(f"Total routes found (including ngRoute): {len(routes)}")
    
    # Add summary information 
    routes_with_deps = [r for r in routes if r['resolve_dependencies']]
    print(f"Routes with dependencies: {len(routes_with_deps)}/{len(routes)}")
    
    return routes

def verify_state_definition(state_name: str, app_js_content: str) -> Dict[str, bool]:
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
    
    # Find the state definition in app.js
    state_pattern = fr"\.state\(\s*['\"]({state_name})['\"](?:\s*,\s*|\s*,\s*\n\s*)(\{{[\s\S]*?\}})"
    state_matches = re.findall(state_pattern, app_js_content, re.MULTILINE)
    
    if state_matches:
        for name, config in state_matches:
            if name == state_name:
                # Verify controller presence
                if 'controller:' in config or 'controller :' in config:
                    verification['controller'] = True
                
                # Verify template presence
                if 'template:' in config or 'template :' in config:
                    verification['template'] = True
    
    return verification 