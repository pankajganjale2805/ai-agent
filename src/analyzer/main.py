import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

from utils import should_ignore, filter_dependencies, extract_require_dependencies
from route_analyzer import analyze_routes, verify_state_definition
from component_analyzer import analyze_controllers, analyze_services, analyze_directives, analyze_filters, analyze_modules
from template_analyzer import analyze_templates, analyze_styles, analyze_assets, analyze_vendor_libraries, analyze_html_dependencies
from dependency_analyzer import analyze_file_dependencies, analyze_dependencies, estimate_migration_complexity
from reporting import generate_analysis_report, save_analysis_report

class AngularCodebaseAnalyzer:
    def __init__(self, angular_root: str):
        """
        Initialize the analyzer with the Angular project root path
        
        Args:
            angular_root: Path to Angular project root
        """
        self.angular_root = Path(angular_root)
        
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
        
        # Directories to ignore
        self.ignore_dirs = ['v1', 'scripts/vendor']
        # Minified file patterns to ignore
        self.ignore_files = ['.min.js', '.min.css']
        
        # Define paths based on provided structure
        self.app_js_path = self.angular_root / 'app' / 'scripts' / 'app.js'
        self.app_path = self.angular_root / 'app'
        self.scripts_path = self.angular_root / 'app' / 'scripts'
        self.views_path = self.angular_root / 'app' / 'views'
        self.styles_path = self.angular_root / 'app' / 'sass'
        self.assets_path = self.angular_root / 'app' / 'assets'
        self.fonts_path = self.angular_root / 'app' / 'fonts'
        self.images_path = self.angular_root / 'app' / 'images'

    def analyze_routes(self) -> None:
        """
        Parse app.js to extract all route definitions
        """
        self.routes = analyze_routes(self.app_js_path, self.ignore_dirs, self.ignore_files)

    def analyze_controllers(self) -> None:
        """
        Find and analyze all controllers
        """
        self.controllers = analyze_controllers(self.scripts_path, self.angular_root, self.ignore_dirs, self.ignore_files)

    def analyze_templates(self) -> None:
        """
        Find and analyze all templates
        """
        self.templates = analyze_templates(self.app_path, self.angular_root, self.ignore_dirs, self.ignore_files)

    def analyze_services(self) -> None:
        """
        Find and analyze all services
        """
        self.services = analyze_services(self.scripts_path, self.angular_root, self.ignore_dirs, self.ignore_files)

    def analyze_directives(self) -> None:
        """
        Find and analyze all directives
        """
        self.directives = analyze_directives(self.scripts_path, self.angular_root, self.ignore_dirs, self.ignore_files)

    def analyze_filters(self) -> None:
        """
        Find and analyze all filters
        """
        self.filters = analyze_filters(self.scripts_path, self.angular_root, self.ignore_dirs, self.ignore_files)

    def analyze_modules(self) -> None:
        """
        Find and analyze all Angular modules
        """
        self.modules = analyze_modules(self.scripts_path, self.angular_root, self.ignore_dirs, self.ignore_files)

    def analyze_styles(self) -> None:
        """
        Find and analyze all style files
        """
        self.styles = analyze_styles(self.app_path, self.styles_path, self.angular_root, self.ignore_dirs, self.ignore_files)

    def analyze_assets(self) -> None:
        """
        Find and catalog all assets (images, fonts, etc.)
        """
        self.assets = analyze_assets(self.assets_path, self.fonts_path, self.images_path, self.angular_root, self.ignore_dirs, self.ignore_files)

    def analyze_vendor_libraries(self) -> None:
        """
        Find and analyze selected vendor libraries (excluding the ones in ignore list)
        """
        self.vendor_libs = analyze_vendor_libraries(self.scripts_path, self.angular_root, self.ignore_dirs, self.ignore_files)

    def analyze_dependencies(self) -> Dict[str, List[str]]:
        """
        Analyze dependencies between components
        """
        self.file_dependencies = analyze_html_dependencies(self.templates, self.directives, self.file_dependencies)
        return analyze_dependencies(self.controllers, self.angular_root)

    def analyze_codebase(self) -> None:
        """
        Run all analysis steps
        """
        self.analyze_routes()
        self.analyze_controllers()
        self.analyze_templates()
        self.analyze_services()
        self.analyze_directives()
        self.analyze_filters()
        self.analyze_modules()
        self.analyze_styles()
        self.analyze_assets()
        self.analyze_vendor_libraries()
        
        print("Completed full codebase analysis")

    def generate_analysis_report(self) -> Dict:
        """
        Generate a JSON report with codebase analysis
        """
        dependencies = self.analyze_dependencies()
        complexity = estimate_migration_complexity(self.routes, self.controllers, self.templates, self.angular_root)
        
        return generate_analysis_report(
            self.routes,
            self.controllers,
            self.templates,
            self.services,
            self.directives,
            self.filters,
            self.modules,
            self.styles,
            self.assets,
            self.vendor_libs,
            self.file_dependencies,
            dependencies,
            complexity
        )


def main():
    parser = argparse.ArgumentParser(description='Analyze AngularJS app for Next.js migration')
    parser.add_argument('--angular-root', type=str, required=True, help='Path to Angular project root')
    parser.add_argument('--output', type=str, default='analysis_report.json', help='Path to output report file')
    
    args = parser.parse_args()
    
    try:
        analyzer = AngularCodebaseAnalyzer(args.angular_root)
        analyzer.analyze_codebase()
        report = analyzer.generate_analysis_report()
        
        # Save report to file
        save_analysis_report(report, args.output)
        
        print(f"Analysis complete! Report saved to {args.output}")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 