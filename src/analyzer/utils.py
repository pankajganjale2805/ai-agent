import re
from pathlib import Path
from typing import List

def is_vendor_or_minified(path: str) -> bool:
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
        'slider', 'touchspin', 'qrcode', 'barcode'
    ]
    
    if any(indicator in path.lower() for indicator in vendor_indicators):
        return True
        
    # Check for minified files or bundles
    minified_indicators = [
        '.min.js', '.min.css', '-min.js', '-min.css',
        '.bundle.js', '.bundle.css', '.pack.js',
        '.compiled.js', '.prod.js'
    ]
    
    if any(indicator in path.lower() for indicator in minified_indicators):
        return True
        
    return False
    
def filter_dependencies(dependencies: List[str]) -> List[str]:
    """
    Filter a list of dependencies to:
    1. Remove vendor and minified files
    2. Only include actual files with extensions
    
    Args:
        dependencies: List of dependencies to filter
        
    Returns:
        List[str]: Filtered list of dependencies
    """
    if not dependencies:
        return []
    
    # File extensions to include
    file_extensions = ['.js', '.css', '.html', '.json', '.svg', '.png', '.jpg', '.jpeg', '.gif']
    
    filtered_deps = []
    for dep in dependencies:
        # Skip vendor or minified files
        if is_vendor_or_minified(dep):
            continue
            
        # Only include dependencies that are actual files (with extensions)
        if any(dep.lower().endswith(ext) for ext in file_extensions):
            filtered_deps.append(dep)
            
    return filtered_deps

def should_ignore(path: Path, angular_root: Path, ignore_dirs, ignore_files) -> bool:
    """
    Check if a path should be ignored based on the ignore rules
    
    Args:
        path: Path to check
        angular_root: Root path of the Angular project
        ignore_dirs: List of directories to ignore
        ignore_files: List of file patterns to ignore
        
    Returns:
        True if path should be ignored, False otherwise
    """
    rel_path = str(path.relative_to(angular_root))
    
    # Check if path is in ignored directories
    for ignore_dir in ignore_dirs:
        if ignore_dir in rel_path:
            return True
    
    # Check if file is minified
    for ignore_pattern in ignore_files:
        if ignore_pattern in path.name:
            return True
    
    return False

def extract_require_dependencies(content: str) -> List[str]:
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