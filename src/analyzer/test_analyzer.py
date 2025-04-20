#!/usr/bin/env python3
import os
import json
import argparse
from pathlib import Path

from analyzer import AngularCodebaseAnalyzer
from reporting import save_analysis_report

def main():
    """
    Test script for the AngularCodebaseAnalyzer
    """
    parser = argparse.ArgumentParser(description='Test the Angular codebase analyzer')
    parser.add_argument('--angular-root', type=str, default='sample_app', help='Path to Angular project root')
    parser.add_argument('--output', type=str, default='analyzer_test_output.json', help='Path to output report file')
    
    args = parser.parse_args()
    
    try:
        print(f"Analyzing Angular codebase at {args.angular_root}...")
        analyzer = AngularCodebaseAnalyzer(args.angular_root)
        analyzer.analyze_codebase()
        report = analyzer.generate_analysis_report()
        
        # Save report to file
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Analysis complete! Report saved to {args.output}")
        
        # Print summary
        print("\nSummary:")
        print(f"Total routes: {report['summary']['total_routes']}")
        print(f"Total controllers: {report['summary']['total_controllers']}")
        print(f"Total templates: {report['summary']['total_templates']}")
        print(f"Total services: {report['summary']['total_services']}")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 