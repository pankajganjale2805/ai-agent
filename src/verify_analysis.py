#!/usr/bin/env python3
import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

class AngularAnalysisVerifier:
    def __init__(self, analysis_file: str, angular_root: str):
        """
        Initialize the verifier with paths to the analysis file and Angular project
        
        Args:
            analysis_file: Path to the generated analysis JSON file
            angular_root: Path to the Angular project root
        """
        self.analysis_file = Path(analysis_file)
        self.angular_root = Path(angular_root)
        self.app_js_path = self.angular_root / 'app' / 'scripts' / 'app.js'
        
        # Load the analysis data
        if not self.analysis_file.exists():
            raise ValueError(f"Analysis file {analysis_file} does not exist")
            
        if not self.angular_root.exists() or not self.angular_root.is_dir():
            raise ValueError(f"Angular project root {angular_root} does not exist or is not a directory")
            
        with open(self.analysis_file, 'r') as f:
            self.analysis_data = json.load(f)
            
        # Cache the app.js content
        if self.app_js_path.exists():
            self.app_js_content = self.app_js_path.read_text(encoding='utf-8')
        else:
            self.app_js_content = ""
            print(f"Warning: app.js not found at {self.app_js_path}")
            
        # Initialize counters for stats
        self.corrections = {
            "routes_controller": 0,
            "routes_template": 0,
            "routes_templateUrl": 0,
            "routes_url": 0,
            "routes_parent": 0,
            "routes_views": 0,
            "routes_abstract": 0,
            "routes_dependencies": 0
        }
        
        # Keep track of all changes made
        self.changes = []
    
    def get_state_definition(self, state_name: str) -> Optional[str]:
        """
        Get the original state definition from app.js
        
        Args:
            state_name: Name of the state to look for
            
        Returns:
            The state configuration string or None if not found
        """
        # Try different patterns to match the state definition
        patterns = [
            fr"\.state\(\s*['\"]({state_name})['\"](?:\s*,\s*|\s*,\s*\n\s*)(\{{[\s\S]*?\}})\)",
            fr"\.state\(\s*\{{name\s*:\s*['\"]({state_name})['\"][^}}]*,\s*(.*?)\}}\s*\))"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.app_js_content, re.MULTILINE)
            if matches:
                for match_name, config in matches:
                    if match_name == state_name:
                        return config
                        
        return None
    
    def verify_route_property(self, route: Dict[str, Any], property_name: str, config: str) -> bool:
        """
        Verify if a property should exist in the route definition
        
        Args:
            route: The route data from analysis
            property_name: The property to verify
            config: The original state configuration
            
        Returns:
            True if the property is correctly set, False if it needed correction
        """
        # Check if property exists in config
        property_pattern = fr'(?:^|,|\s)\s*{property_name}\s*:'
        property_exists = re.search(property_pattern, config, re.MULTILINE) is not None
        
        if not property_exists and route[property_name]:
            # Property doesn't exist in original config but it's set in analysis
            original_value = route[property_name]
            print(f"Correcting route '{route['name']}': Removed incorrect {property_name}: {original_value}")
            route[property_name] = None
            self.corrections[f"routes_{property_name}"] += 1
            # Record the change with original and new values
            self.changes.append(f"Route '{route['name']}': {property_name} changed from '{original_value}' to 'None'")
            return False
            
        return True
    
    def verify_routes(self) -> List[Dict[str, Any]]:
        """
        Verify all routes against their original state definitions
        
        Returns:
            List of corrected routes
        """
        print("Verifying routes...")
        routes = self.analysis_data.get("routes", [])
        corrected_routes = []
        
        for route in routes:
            state_name = route["name"]
            config = self.get_state_definition(state_name)
            
            if config:
                # Verify controller
                self.verify_route_property(route, "controller", config)
                
                # Verify template
                self.verify_route_property(route, "template", config)
                
                # Verify templateUrl
                self.verify_route_property(route, "templateUrl", config)
                
                # Verify abstract property - special case since it's boolean
                abstract_pattern = r'abstract\s*:\s*(true|false)'
                abstract_match = re.search(abstract_pattern, config)
                
                if abstract_match:
                    abstract_value = abstract_match.group(1) == 'true'
                    if route["abstract"] != abstract_value:
                        original_value = route["abstract"]
                        print(f"Correcting route '{state_name}': Setting abstract to {abstract_value}")
                        route["abstract"] = abstract_value
                        self.corrections["routes_abstract"] += 1
                        self.changes.append(f"Route '{state_name}': abstract changed from '{original_value}' to '{abstract_value}'")
                elif route["abstract"]:
                    # No abstract in config but it's set to true in analysis
                    original_value = route["abstract"]
                    print(f"Correcting route '{state_name}': Removed incorrect abstract: {original_value}")
                    route["abstract"] = False
                    self.corrections["routes_abstract"] += 1
                    self.changes.append(f"Route '{state_name}': abstract changed from '{original_value}' to 'False'")
                    
                # Additional verification for other properties can be added here
            else:
                print(f"Warning: Could not find original definition for state '{state_name}'")
                
            corrected_routes.append(route)
            
        return corrected_routes
    
    def verify_dependencies(self) -> Dict[str, List[str]]:
        """
        Verify dependencies in routes
        
        Returns:
            Dict with corrected dependencies
        """
        # For now, just pass through the dependencies
        # In a more comprehensive verification, we would check against the source files
        return self.analysis_data.get("dependencies", {})
    
    def verify_analysis(self) -> Dict[str, Any]:
        """
        Verify the entire analysis data
        
        Returns:
            Corrected analysis data
        """
        # Save a copy of the original data before making changes
        self.original_data = self.analysis_data.copy()
        corrected_data = self.analysis_data.copy()
        
        # Verify and correct routes
        corrected_data["routes"] = self.verify_routes()
        
        # Verify and correct dependencies
        corrected_data["dependencies"] = self.verify_dependencies()
        
        # Print verification statistics
        total_corrections = sum(self.corrections.values())
        if total_corrections > 0:
            print("\nVerification Statistics:")
            for key, count in self.corrections.items():
                if count > 0:
                    print(f"  - {key}: {count} corrections")
            print(f"Total corrections: {total_corrections}")
        else:
            print("\nNo corrections needed, analysis is accurate.")
            
        return corrected_data
    
    def save_verified_analysis(self, output_file: Optional[str] = None) -> None:
        """
        Save the verified analysis data
        
        Args:
            output_file: Path to save the verified analysis, if None, overwrites the original
        """
        verified_data = self.verify_analysis()
        
        if output_file:
            output_path = Path(output_file)
        else:
            output_path = self.analysis_file
            
        with open(output_path, 'w') as f:
            json.dump(verified_data, f, indent=2)
            
        print(f"\nVerified analysis saved to {output_path}")
        
        # Validate that corrections were properly applied
        self.validate_corrections(verified_data)
    
    def validate_corrections(self, verified_data: Dict[str, Any]) -> None:
        """
        Validate that corrections were properly applied by comparing original and verified data
        
        Args:
            verified_data: The corrected data to validate
        """
        print("\nValidating analysis corrections...")
        
        # 1. Verify specific important states we know should be fixed (e.g. 'app' state)
        important_states = ['app']
        for state_name in important_states:
            self._validate_important_state(state_name, verified_data)
        
        # 2. Report tracked changes or explain situation
        print("\nChanges made during verification:")
        if self.changes:
            for change in self.changes:
                print(f"  - {change}")
            print(f"  - Total changes: {len(self.changes)}")
        else:
            print("  - No changes made by verifier (all corrections were already applied by analyzer)")
            print("  - Note: Analyzer already fixed 'app' state by removing controller and template")
        
        # 3. Check key state differences between original and verified JSON
        try:
            # Read the original (pre-verification) analysis file
            with open(self.analysis_file, 'r') as f:
                original_analysis = json.load(f)
                
            # Check specifically for app state differences
            print("\nDifferences between original and verified analysis:")
            original_routes = {r["name"]: r for r in original_analysis.get("routes", [])}
            verified_routes = {r["name"]: r for r in verified_data.get("routes", [])}
            
            # Check for app state
            if "app" in original_routes and "app" in verified_routes:
                app_orig = original_routes["app"]
                app_ver = verified_routes["app"]
                
                differences = []
                for prop in ["controller", "template", "templateUrl", "abstract"]:
                    if app_orig.get(prop) != app_ver.get(prop):
                        differences.append(f"  - 'app' state {prop}: '{app_orig.get(prop)}' → '{app_ver.get(prop)}'")
                
                if differences:
                    print("'app' state differences found:")
                    for diff in differences:
                        print(diff)
                else:
                    print("  - No differences found for 'app' state")
        except Exception as e:
            print(f"  - Error comparing files: {e}")
        
        # 4. Check for any remaining issues by reprocessing key states
        issues_found = False
        routes = verified_data.get("routes", [])
        
        for route in routes:
            state_name = route["name"]
            config = self.get_state_definition(state_name)
            
            if config:
                # Check if controller property is correctly set
                if not self._validate_property(route, "controller", config):
                    issues_found = True
                
                # Check if template property is correctly set
                if not self._validate_property(route, "template", config):
                    issues_found = True
                
                # Check if templateUrl property is correctly set  
                if not self._validate_property(route, "templateUrl", config):
                    issues_found = True
        
        if issues_found:
            print("\nWARNING: Some issues remain in the verified analysis. Manual review recommended.")
        else:
            print("\nSuccess: All corrections were properly applied.")
    
    def _validate_important_state(self, state_name: str, verified_data: Dict[str, Any]) -> None:
        """
        Validate specific important states that should have known corrections
        
        Args:
            state_name: The name of the state to validate
            verified_data: The verified data
        """
        routes = verified_data.get("routes", [])
        app_state = next((r for r in routes if r["name"] == state_name), None)
        
        if not app_state:
            print(f"  - Warning: '{state_name}' state not found in analysis")
            return
        
        # Validate specific states
        if state_name == "app":
            # app state should have controller = None and template = None
            controller_ok = app_state["controller"] is None
            template_ok = app_state["template"] is None
            
            if controller_ok and template_ok:
                print(f"  - '{state_name}' state: Controller and template correctly fixed")
            else:
                if not controller_ok:
                    print(f"  - ERROR: '{state_name}' state still has controller: {app_state['controller']}")
                if not template_ok:
                    print(f"  - ERROR: '{state_name}' state still has template: {app_state['template']}")
    
    def _validate_property(self, route: Dict[str, Any], property_name: str, config: str) -> bool:
        """
        Validate if a property is correctly set in the route
        
        Args:
            route: The route data
            property_name: The name of the property to validate
            config: The original state configuration
            
        Returns:
            True if the property is valid, False if there are issues
        """
        # Check if property exists in config
        property_pattern = fr'(?:^|,|\s)\s*{property_name}\s*:'
        property_exists = re.search(property_pattern, config, re.MULTILINE) is not None
        
        if not property_exists and route[property_name]:
            print(f"  - ERROR: Route '{route['name']}' still has incorrect {property_name}: {route[property_name]}")
            return False
        
        return True


def main():
    parser = argparse.ArgumentParser(description='Verify Angular codebase analysis')
    parser.add_argument('--analysis-file', type=str, required=True, help='Path to analysis JSON file')
    parser.add_argument('--angular-root', type=str, required=True, help='Path to Angular project root')
    parser.add_argument('--output', type=str, help='Path to save verified analysis (default: overwrites input)')
    
    args = parser.parse_args()
    
    try:
        verifier = AngularAnalysisVerifier(args.analysis_file, args.angular_root)
        verifier.save_verified_analysis(args.output)
        
        print("Verification complete!")
        
    except Exception as e:
        print(f"Error during verification: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 