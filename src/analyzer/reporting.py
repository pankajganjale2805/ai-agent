import json
from typing import Dict, List

def generate_analysis_report(
    routes: List[Dict],
    controllers: Dict[str, str],
    templates: Dict[str, str],
    services: Dict[str, str],
    directives: Dict[str, str],
    filters: Dict[str, str],
    modules: Dict[str, str],
    styles: Dict[str, str],
    assets: Dict[str, str],
    vendor_libs: Dict[str, List[str]],
    file_dependencies: Dict[str, List[str]],
    dependencies: Dict[str, List[str]],
    migration_complexity: Dict
) -> Dict:
    """
    Generate a JSON report with codebase analysis
    
    Args:
        routes: List of route objects
        controllers: Dict mapping controller names to file paths
        templates: Dict mapping template URLs to file paths
        services: Dict mapping service names to file paths
        directives: Dict mapping directive names to file paths
        filters: Dict mapping filter names to file paths
        modules: Dict mapping module names to file paths
        styles: Dict mapping style paths to file paths
        assets: Dict mapping asset paths to file paths
        vendor_libs: Dict mapping library names to lists of file paths
        file_dependencies: Dict mapping file paths to lists of dependencies
        dependencies: Dict mapping component names to lists of dependencies
        migration_complexity: Dict containing complexity score and details
        
    Returns:
        Dict containing the analysis report
    """
    print("Generating analysis report...")
    
    # Map controllers to routes
    controller_routes = {}
    for route in routes:
        controller = route.get('controller')
        if controller:
            if controller not in controller_routes:
                controller_routes[controller] = []
            controller_routes[controller].append(route)
    
    # Ensure all routes have all expected properties
    processed_routes = []
    for route in routes:
        # Create a clean route object with all expected fields
        route_obj = {
            "name": route.get("name", ""),
            "url": route.get("url", ""),
            "controller": route.get("controller", ""),
            "templateUrl": route.get("templateUrl", ""),
            "resolve_dependencies": route.get("resolve_dependencies", []),
            "type": route.get("type", "ui-router"),
            "views": route.get("views", {}),
            "parent": route.get("parent", ""),
            "abstract": route.get("abstract", False),
            "template": route.get("template", "")
        }
        processed_routes.append(route_obj)
    
    # Create analysis report
    report = {
        "summary": {
            "total_routes": len(routes),
            "total_controllers": len(controllers),
            "total_templates": len(templates),
            "total_services": len(services),
            "total_directives": len(directives),
            "total_filters": len(filters),
            "total_modules": len(modules),
            "total_styles": len(styles),
            "total_assets": len(assets),
            "total_vendor_libraries": len(vendor_libs)
        },
        "routes": processed_routes,
        "controllers": {name: path for name, path in controllers.items()},
        "services": {name: path for name, path in services.items()},
        "directives": {name: path for name, path in directives.items()},
        "filters": {name: path for name, path in filters.items()},
        "modules": {name: path for name, path in modules.items()},
        "styles": {path: file_path for path, file_path in styles.items()},
        "assets": {path: file_path for path, file_path in assets.items()},
        "vendor_libraries": vendor_libs,
        "controller_routes": controller_routes,
        "dependencies": {
            source: list(deps) for source, deps in file_dependencies.items()
        },
        "service_dependencies": dependencies,
        "migration_complexity": migration_complexity
    }
    
    return report

def save_analysis_report(report: Dict, output_path: str) -> None:
    """
    Save the analysis report to a JSON file
    
    Args:
        report: Dict containing the analysis report
        output_path: Path to the output file
    """
    print(f"Saving analysis report to {output_path}...")
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Analysis report saved to {output_path}")
    
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