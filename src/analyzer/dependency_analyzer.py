import re
from pathlib import Path
from typing import Dict, List, Set

def analyze_file_dependencies(file_path: Path, content: str, angular_root: Path, file_dependencies: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """
    Analyze dependencies in a JavaScript file
    
    Args:
        file_path: Path to the file
        content: File content
        angular_root: Path to Angular project root
        file_dependencies: Dict mapping file paths to sets of dependencies
        
    Returns:
        Updated file_dependencies dict
    """
    relative_path = str(file_path.relative_to(angular_root))
    
    if relative_path not in file_dependencies:
        file_dependencies[relative_path] = set()
        
    # Look for Angular module dependencies
    module_dep_match = re.search(r"angular\.module\(['\"][^'\"]+['\"],\s*\[(.*?)\]", content, re.DOTALL)
    if module_dep_match:
        deps = module_dep_match.group(1)
        module_deps = re.findall(r"['\"]([^'\"]+)['\"]", deps)
        
        for dep in module_deps:
            file_dependencies[relative_path].add(dep)
            
    # Look for service injections
    service_match = re.search(r"function\s*\((.*?)\)", content)
    if service_match:
        params = service_match.group(1)
        param_list = [p.strip() for p in params.split(',')]
        
        # Map to actual services (this is approximate)
        for param in param_list:
            if param and not param.startswith('$'):  # Skip Angular built-in services
                file_dependencies[relative_path].add(param)
    
    return file_dependencies

def analyze_dependencies(controllers: Dict[str, str], angular_root: Path) -> Dict[str, List[str]]:
    """
    Analyze dependencies between components
    
    Args:
        controllers: Dict mapping controller names to file paths
        angular_root: Path to Angular project root
        
    Returns:
        Dict mapping component names to lists of dependencies
    """
    print("Analyzing dependencies...")
    
    dependencies = {}
    
    # Check controller dependencies
    for controller_name, path in controllers.items():
        full_path = angular_root / path
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
            
            if external_services:
                dependencies[controller_name] = external_services
    
    return dependencies

def estimate_migration_complexity(routes: List[Dict], controllers: Dict[str, str], templates: Dict[str, str], angular_root: Path) -> Dict:
    """
    Estimate the complexity of migration for different parts of the codebase
    
    Args:
        routes: List of route objects
        controllers: Dict mapping controller names to file paths
        templates: Dict mapping template URLs to file paths
        angular_root: Path to Angular project root
        
    Returns:
        Dict containing complexity score and details
    """
    # Count complex features in the codebase
    complex_features = {
        "custom_directives": 0,
        "complex_controllers": 0,
        "large_templates": 0
    }
    
    # Check for complex controllers (large files, many dependencies)
    for controller_name, path in controllers.items():
        full_path = angular_root / path
        if not full_path.exists():
            continue
            
        content = full_path.read_text(encoding='utf-8')
        
        # Count lines of code
        lines = content.count('\n')
        
        if lines > 200:
            complex_features["complex_controllers"] += 1
    
    # Check for large templates
    for template_url, path in templates.items():
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
    
    # Calculate complexity scores
    complexity = {
        "overall_score": 0,
        "details": complex_features,
        "migration_time_estimate": ""
    }
    
    # Calculate overall score
    score = (
        complex_features["complex_controllers"] * 5 + 
        complex_features["large_templates"] * 3 + 
        complex_features["custom_directives"] * 2
    )
    
    # Normalize to 0-100 scale
    routes_count = len(routes)
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
    
    return complexity 