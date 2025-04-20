import re
from pathlib import Path
from typing import Dict, List, Set

from utils import should_ignore

def analyze_templates(app_path: Path, angular_root: Path, ignore_dirs: List[str], ignore_files: List[str]) -> Dict[str, str]:
    """
    Find and analyze all templates
    
    Args:
        app_path: Path to app directory
        angular_root: Path to Angular project root
        ignore_dirs: List of directories to ignore
        ignore_files: List of file patterns to ignore
        
    Returns:
        Dict mapping template URLs to file paths
    """
    print("Analyzing templates...")
    templates = {}
    
    # Check if app path exists
    if not app_path.exists():
        print(f"Warning: {app_path} does not exist")
        return templates
    
    # Find all HTML files in app directory and subdirectories
    template_files = []
    for file_path in app_path.glob('**/*.html'):
        if not should_ignore(file_path, angular_root, ignore_dirs, ignore_files):
            template_files.append(file_path)
    
    print(f"Found {len(template_files)} HTML files to analyze (after filtering)")
    
    for file_path in template_files:
        try:
            relative_path = file_path.relative_to(angular_root)
            template_url = str(relative_path).replace('app/', '')
            templates[template_url] = str(file_path)
        except Exception as e:
            print(f"Warning: Could not process template {file_path}: {e}")
    
    print(f"Found {len(templates)} templates")
    return templates

def analyze_styles(app_path: Path, styles_path: Path, angular_root: Path, ignore_dirs: List[str], ignore_files: List[str]) -> Dict[str, str]:
    """
    Find and analyze all style files
    
    Args:
        app_path: Path to app directory
        styles_path: Path to styles directory
        angular_root: Path to Angular project root
        ignore_dirs: List of directories to ignore
        ignore_files: List of file patterns to ignore
        
    Returns:
        Dict mapping style paths to file paths
    """
    print("Analyzing styles...")
    styles = {}
    
    # Check if styles directory exists
    if not styles_path.exists():
        print(f"Warning: Styles path {styles_path} does not exist")
    
    # Look for all style files in the app directory
    style_extensions = ['.css', '.scss', '.sass', '.less']
    style_files = []
    
    for ext in style_extensions:
        for file_path in app_path.glob(f'**/*{ext}'):
            if not should_ignore(file_path, angular_root, ignore_dirs, ignore_files):
                style_files.append(file_path)
    
    print(f"Found {len(style_files)} style files (after filtering)")
    
    for file_path in style_files:
        try:
            relative_path = file_path.relative_to(angular_root)
            styles[str(relative_path)] = str(file_path)
        except Exception as e:
            print(f"Warning: Could not analyze style file {file_path}: {e}")
    
    print(f"Found {len(styles)} style files")
    return styles

def analyze_assets(assets_path: Path, fonts_path: Path, images_path: Path, angular_root: Path, ignore_dirs: List[str], ignore_files: List[str]) -> Dict[str, str]:
    """
    Find and catalog all assets (images, fonts, etc.)
    
    Args:
        assets_path: Path to assets directory
        fonts_path: Path to fonts directory
        images_path: Path to images directory
        angular_root: Path to Angular project root
        ignore_dirs: List of directories to ignore
        ignore_files: List of file patterns to ignore
        
    Returns:
        Dict mapping asset paths to file paths
    """
    print("Analyzing assets...")
    assets = {}
    
    # Check assets directories
    asset_paths = [assets_path, fonts_path, images_path]
    
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
                if not should_ignore(file_path, angular_root, ignore_dirs, ignore_files):
                    try:
                        relative_path = file_path.relative_to(angular_root)
                        assets[str(relative_path)] = str(file_path)
                    except Exception as e:
                        print(f"Warning: Could not process asset {file_path}: {e}")
    
    print(f"Found {len(assets)} assets")
    return assets

def analyze_vendor_libraries(scripts_path: Path, angular_root: Path, ignore_dirs: List[str], ignore_files: List[str]) -> Dict[str, List[str]]:
    """
    Find and analyze selected vendor libraries (excluding the ones in ignore list)
    
    Args:
        scripts_path: Path to scripts directory
        angular_root: Path to Angular project root
        ignore_dirs: List of directories to ignore
        ignore_files: List of file patterns to ignore
        
    Returns:
        Dict mapping library names to lists of file paths
    """
    print("Analyzing vendor libraries...")
    vendor_libs = {}
    
    vendor_path = scripts_path / 'vendor'
    if not vendor_path.exists():
        print(f"Warning: Vendor directory {vendor_path} does not exist")
        return vendor_libs
        
    # Collect specific vendor libraries that are not in ignore list
    vendor_libs_to_include = []
    for lib_dir in vendor_path.iterdir():
        if lib_dir.is_dir():
            # Skip if the entire vendor directory is in ignore list
            if any(ignore_dir in str(lib_dir.relative_to(angular_root)) for ignore_dir in ignore_dirs):
                continue
            
            # Check specific libraries to include
            lib_name = lib_dir.name
            if lib_name in ['angular-qrcode', 'barcode-generator', 'qrcode-generator', 'slider', 'table-to-excel']:
                vendor_libs_to_include.append(lib_dir)
                
    # Process selected vendor libraries
    for lib_dir in vendor_libs_to_include:
        lib_name = lib_dir.name
        lib_files = []
        
        for file_path in lib_dir.glob('**/*.js'):
            if not should_ignore(file_path, angular_root, ignore_dirs, ignore_files):
                lib_files.append(file_path)
        
        if lib_files:
            vendor_libs[lib_name] = [str(f.relative_to(angular_root)) for f in lib_files]
            print(f"  - Found vendor library: {lib_name} with {len(lib_files)} files")
    
    print(f"Found {len(vendor_libs)} vendor libraries (after filtering)")
    return vendor_libs

def analyze_html_dependencies(templates: Dict[str, str], directives: Dict[str, str], file_dependencies: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """
    Analyze dependencies in HTML templates
    
    Args:
        templates: Dict mapping template URLs to file paths
        directives: Dict mapping directive names to file paths
        file_dependencies: Dict mapping file paths to sets of dependencies
        
    Returns:
        Updated file_dependencies dict
    """
    print("Analyzing HTML dependencies...")
    
    # Process all HTML files
    for template_url, file_path in templates.items():
        try:
            path = Path(file_path)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for directive usages
            directive_usages = set()
            
            # Convert directive names to kebab-case (how they appear in HTML)
            for directive_name in directives.keys():
                # Convert camelCase to kebab-case
                kebab = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', directive_name).lower()
                
                # Check if directive is used in template
                if kebab in content or directive_name in content:
                    directive_usages.add(directive_name)
            
            if directive_usages:
                if template_url not in file_dependencies:
                    file_dependencies[template_url] = set()
                
                file_dependencies[template_url].update(directive_usages)
        except Exception as e:
            print(f"Warning: Could not analyze HTML dependencies in {file_path}: {e}")
    
    print("Completed HTML dependency analysis")
    return file_dependencies 