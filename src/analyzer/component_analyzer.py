import re
from pathlib import Path
from typing import Dict, List

from utils import should_ignore

def analyze_controllers(scripts_path: Path, angular_root: Path, ignore_dirs: List[str], ignore_files: List[str]) -> Dict[str, str]:
    """
    Find and analyze all controllers
    
    Args:
        scripts_path: Path to scripts directory
        angular_root: Path to Angular project root
        ignore_dirs: List of directories to ignore
        ignore_files: List of file patterns to ignore
        
    Returns:
        Dict mapping controller names to file paths
    """
    print("Analyzing controllers...")
    controllers = {}
    
    # Check if scripts path exists
    if not scripts_path.exists():
        print(f"Warning: {scripts_path} does not exist")
        return controllers
    
    # Find all JS files in scripts directory and subdirectories
    controller_files = []
    for file_path in scripts_path.glob('**/*.js'):
        if not should_ignore(file_path, angular_root, ignore_dirs, ignore_files):
            controller_files.append(file_path)
    
    print(f"Found {len(controller_files)} JS files to analyze for controllers (after filtering)")
    
    for file_path in controller_files:
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract controller names using regex - matches both .controller and .directive patterns
            controller_matches = re.findall(r"\.controller\(['\"]([^'\"]+)['\"]", content)
            
            for controller_name in controller_matches:
                relative_path = file_path.relative_to(angular_root)
                controllers[controller_name] = str(relative_path)
            
            # Also check for directives that might contain controller logic
            directive_matches = re.findall(r"\.directive\(['\"]([^'\"]+)['\"]", content)
            for directive_name in directive_matches:
                if "controller:" in content:
                    # Store directives with controllers as a special type of controller
                    relative_path = file_path.relative_to(angular_root)
                    controllers[f"Directive_{directive_name}"] = str(relative_path)
        except Exception as e:
            print(f"Warning: Could not analyze file {file_path}: {e}")
    
    print(f"Found {len(controllers)} controllers and directives with controllers")
    return controllers

def analyze_services(scripts_path: Path, angular_root: Path, ignore_dirs: List[str], ignore_files: List[str]) -> Dict[str, str]:
    """
    Find and analyze all services
    
    Args:
        scripts_path: Path to scripts directory
        angular_root: Path to Angular project root
        ignore_dirs: List of directories to ignore
        ignore_files: List of file patterns to ignore
        
    Returns:
        Dict mapping service names to file paths
    """
    print("Analyzing services...")
    services = {}
    
    # Check if scripts path exists
    if not scripts_path.exists():
        print(f"Warning: {scripts_path} does not exist")
        return services
    
    # Find all JS files in scripts directory and subdirectories
    service_files = []
    for file_path in scripts_path.glob('**/*.js'):
        if not should_ignore(file_path, angular_root, ignore_dirs, ignore_files):
            service_files.append(file_path)
    
    print(f"Found {len(service_files)} JS files to analyze for services (after filtering)")
    
    for file_path in service_files:
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract service names - check for service, factory, provider patterns
            service_matches = re.findall(r"\.(?:service|factory|provider)\(['\"]([^'\"]+)['\"]", content)
            
            for service_name in service_matches:
                relative_path = file_path.relative_to(angular_root)
                services[service_name] = str(relative_path)
                
            # Also look for custom services implemented as values
            value_matches = re.findall(r"\.value\(['\"]([^'\"]+)['\"]", content)
            for value_name in value_matches:
                relative_path = file_path.relative_to(angular_root)
                services[f"Value_{value_name}"] = str(relative_path)
                
            # Check for constants that might be used as services
            constant_matches = re.findall(r"\.constant\(['\"]([^'\"]+)['\"]", content)
            for constant_name in constant_matches:
                relative_path = file_path.relative_to(angular_root)
                services[f"Constant_{constant_name}"] = str(relative_path)
        except Exception as e:
            print(f"Warning: Could not analyze file {file_path}: {e}")
    
    print(f"Found {len(services)} services")
    return services

def analyze_directives(scripts_path: Path, angular_root: Path, ignore_dirs: List[str], ignore_files: List[str]) -> Dict[str, str]:
    """
    Find and analyze all directives
    
    Args:
        scripts_path: Path to scripts directory
        angular_root: Path to Angular project root
        ignore_dirs: List of directories to ignore
        ignore_files: List of file patterns to ignore
        
    Returns:
        Dict mapping directive names to file paths
    """
    print("Analyzing directives...")
    directives = {}
    
    # Search for directives in b-directives folder and other script folders
    all_directive_files = []
    
    # Check b-directives folder
    b_directives_path = scripts_path / 'b-directives'
    if b_directives_path.exists():
        for file_path in b_directives_path.glob('**/*.js'):
            if not should_ignore(file_path, angular_root, ignore_dirs, ignore_files):
                all_directive_files.append(file_path)
    
    # Check directives folder
    directives_path = scripts_path / 'directives'
    if directives_path.exists():
        for file_path in directives_path.glob('**/*.js'):
            if not should_ignore(file_path, angular_root, ignore_dirs, ignore_files):
                all_directive_files.append(file_path)
    
    print(f"Found {len(all_directive_files)} JS files to analyze for directives (after filtering)")
    
    for file_path in all_directive_files:
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract directive names
            directive_matches = re.findall(r"\.directive\(['\"]([^'\"]+)['\"]", content)
            
            for directive_name in directive_matches:
                relative_path = file_path.relative_to(angular_root)
                directives[directive_name] = str(relative_path)
        except Exception as e:
            print(f"Warning: Could not analyze directive file {file_path}: {e}")
    
    print(f"Found {len(directives)} directives")
    return directives

def analyze_filters(scripts_path: Path, angular_root: Path, ignore_dirs: List[str], ignore_files: List[str]) -> Dict[str, str]:
    """
    Find and analyze all filters
    
    Args:
        scripts_path: Path to scripts directory
        angular_root: Path to Angular project root
        ignore_dirs: List of directories to ignore
        ignore_files: List of file patterns to ignore
        
    Returns:
        Dict mapping filter names to file paths
    """
    print("Analyzing filters...")
    filters = {}
    
    # Search for filters in b-filters folder and throughout scripts
    filter_files = []
    
    # Check b-filters folder
    b_filters_path = scripts_path / 'b-filters'
    if b_filters_path.exists():
        for file_path in b_filters_path.glob('**/*.js'):
            if not should_ignore(file_path, angular_root, ignore_dirs, ignore_files):
                filter_files.append(file_path)
    
    # Also check all JS files for filters
    for file_path in scripts_path.glob('**/*.js'):
        if not should_ignore(file_path, angular_root, ignore_dirs, ignore_files) and file_path not in filter_files:
            filter_files.append(file_path)
    
    print(f"Found {len(filter_files)} JS files to analyze for filters (after filtering)")
    
    for file_path in filter_files:
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract filter names
            filter_matches = re.findall(r"\.filter\(['\"]([^'\"]+)['\"]", content)
            
            for filter_name in filter_matches:
                relative_path = file_path.relative_to(angular_root)
                filters[filter_name] = str(relative_path)
        except Exception as e:
            print(f"Warning: Could not analyze filter file {file_path}: {e}")
    
    print(f"Found {len(filters)} filters")
    return filters

def analyze_modules(scripts_path: Path, angular_root: Path, ignore_dirs: List[str], ignore_files: List[str]) -> Dict[str, str]:
    """
    Find and analyze all Angular modules
    
    Args:
        scripts_path: Path to scripts directory
        angular_root: Path to Angular project root
        ignore_dirs: List of directories to ignore
        ignore_files: List of file patterns to ignore
        
    Returns:
        Dict mapping module names to file paths
    """
    print("Analyzing modules...")
    modules = {}
    
    # Search in b-modules and modules directories
    module_files = []
    
    # Check b-modules folder
    b_modules_path = scripts_path / 'b-modules'
    if b_modules_path.exists():
        for file_path in b_modules_path.glob('**/*.js'):
            if not should_ignore(file_path, angular_root, ignore_dirs, ignore_files):
                module_files.append(file_path)
    
    # Check modules folder
    modules_path = scripts_path / 'modules'
    if modules_path.exists():
        for file_path in modules_path.glob('**/*.js'):
            if not should_ignore(file_path, angular_root, ignore_dirs, ignore_files):
                module_files.append(file_path)
    
    print(f"Found {len(module_files)} JS files to analyze for modules (after filtering)")
    
    for file_path in module_files:
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract module names
            module_matches = re.findall(r"angular\.module\(['\"]([^'\"]+)['\"]", content)
            
            for module_name in module_matches:
                relative_path = file_path.relative_to(angular_root)
                modules[module_name] = str(relative_path)
        except Exception as e:
            print(f"Warning: Could not analyze module file {file_path}: {e}")
    
    print(f"Found {len(modules)} modules")
    return modules 