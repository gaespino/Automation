"""
Generate File Rename CSV Template
==================================
Creates CSV files for file renaming configuration used by deploy_universal.py

This tool helps you:
1. Generate template CSV for file renames
2. Create product-specific rename rules
3. Analyze existing files to suggest renames

Usage:
    python generate_file_rename_csv.py [options]

Author: GitHub Copilot
Version: 1.0.0
Date: December 9, 2025
"""

import csv
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple

DEVTOOLS = Path(__file__).parent
WORKSPACE = DEVTOOLS.parent


def analyze_python_files(directory: Path, product: str) -> List[Dict]:
    """Analyze Python files and suggest renames based on product."""
    suggestions = []
    
    if not directory.exists():
        print(f"Directory not found: {directory}")
        return suggestions
    
    # Common file patterns that might need product prefixes
    base_names = {
        'SystemDebug', 'TestFramework', 'FileHandler', 'S2TMocks',
        'dpmChecks', 'CoreManipulation', 'ConfigsLoader',
        'ControlPanel', 'ExperimentsForm', 'StatusPanel'
    }
    
    for py_file in directory.rglob('*.py'):
        if py_file.name.startswith('__'):
            continue
        
        file_stem = py_file.stem
        
        # Check if file needs product prefix
        needs_prefix = False
        for base_name in base_names:
            if file_stem == base_name or file_stem.endswith(base_name):
                needs_prefix = True
                break
        
        if needs_prefix and not file_stem.startswith(product):
            rel_path = py_file.relative_to(directory)
            new_name = f"{product}{file_stem}.py"
            
            suggestions.append({
                'old_file': str(rel_path),
                'new_file': str(rel_path.parent / new_name),
                'old_name': py_file.name,
                'new_name': new_name,
                'description': f'Add {product} prefix to {file_stem}',
                'update_imports': 'yes'
            })
    
    return suggestions


def generate_template_csv(output_file: Path, product: str = "GNR"):
    """Generate CSV template for file renames."""
    
    # Common file rename patterns
    renames = [
        {
            'old_file': 'DebugFramework/SystemDebug.py',
            'new_file': f'DebugFramework/{product}SystemDebug.py',
            'old_name': 'SystemDebug.py',
            'new_name': f'{product}SystemDebug.py',
            'description': f'Rename SystemDebug to {product}SystemDebug',
            'update_imports': 'yes',
            'enabled': 'yes'
        },
        {
            'old_file': 'DebugFramework/TestFramework.py',
            'new_file': f'DebugFramework/{product}TestFramework.py',
            'old_name': 'TestFramework.py',
            'new_name': f'{product}TestFramework.py',
            'description': f'Rename TestFramework to {product}TestFramework',
            'update_imports': 'yes',
            'enabled': 'yes'
        },
        {
            'old_file': 'S2T/dpmChecks.py',
            'new_file': f'S2T/{product}dpmChecks.py',
            'old_name': 'dpmChecks.py',
            'new_name': f'{product}dpmChecks.py',
            'description': f'Rename dpmChecks to {product}dpmChecks',
            'update_imports': 'yes',
            'enabled': 'yes'
        },
        {
            'old_file': 'S2T/CoreManipulation.py',
            'new_file': f'S2T/{product}CoreManipulation.py',
            'old_name': 'CoreManipulation.py',
            'new_name': f'{product}CoreManipulation.py',
            'description': f'Rename CoreManipulation to {product}CoreManipulation',
            'update_imports': 'yes',
            'enabled': 'yes'
        },
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=['old_file', 'new_file', 'old_name', 'new_name', 'description', 'update_imports', 'enabled']
        )
        writer.writeheader()
        writer.writerows(renames)
    
    print(f"✅ Template CSV created: {output_file}")
    print(f"   Product prefix: {product}")
    print(f"   Total rules: {len(renames)}")


def generate_from_analysis(directory: Path, output_file: Path, product: str = "GNR"):
    """Generate CSV from directory analysis."""
    
    suggestions = analyze_python_files(directory, product)
    
    if suggestions:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=['old_file', 'new_file', 'old_name', 'new_name', 'description', 'update_imports', 'enabled']
            )
            writer.writeheader()
            
            for suggestion in suggestions:
                suggestion['enabled'] = 'yes'
                writer.writerow(suggestion)
        
        print(f"✅ File rename CSV created: {output_file}")
        print(f"   Analyzed: {directory}")
        print(f"   Product: {product}")
        print(f"   Total rename suggestions: {len(suggestions)}")
        
        if len(suggestions) > 0:
            print(f"\n📋 Sample renames:")
            for i, suggestion in enumerate(suggestions[:5], 1):
                print(f"   {i}. {suggestion['old_name']} → {suggestion['new_name']}")
    else:
        print("❌ No files found that need renaming")


def create_product_specific_csv(product: str, output_dir: Path):
    """Create product-specific file rename CSV."""
    
    product = product.upper()
    output_file = output_dir / f"file_rename_{product.lower()}.csv"
    
    generate_template_csv(output_file, product)


def validate_csv(csv_file: Path):
    """Validate a file rename CSV file."""
    
    if not csv_file.exists():
        print(f"❌ File not found: {csv_file}")
        return False
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            required = {'old_file', 'new_file', 'old_name', 'new_name'}
            if not required.issubset(set(reader.fieldnames or [])):
                print(f"❌ Missing required columns: {required}")
                print(f"   Found: {reader.fieldnames}")
                return False
            
            rules = list(reader)
            enabled_count = sum(1 for r in rules if r.get('enabled', 'yes').lower() == 'yes')
            
            print(f"✅ CSV validation passed: {csv_file.name}")
            print(f"   Total rules: {len(rules)}")
            print(f"   Enabled: {enabled_count}")
            print(f"   Disabled: {len(rules) - enabled_count}")
            
            if len(rules) > 0:
                print(f"\n📋 Sample renames:")
                for i, rule in enumerate(rules[:3], 1):
                    print(f"   {i}. {rule['old_name']} → {rule['new_name']}")
                    if rule.get('update_imports') == 'yes':
                        print(f"      (will update imports)")
            
            return True
            
    except Exception as e:
        print(f"❌ Error validating CSV: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate file rename CSV templates for deployment"
    )
    
    parser.add_argument(
        '--mode',
        choices=['template', 'product', 'analysis', 'validate'],
        default='product',
        help='Generation mode'
    )
    
    parser.add_argument(
        '--product',
        default='GNR',
        help='Product name (GNR, CWF, DMR)'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        help='Output CSV file path'
    )
    
    parser.add_argument(
        '--directory',
        type=Path,
        help='Directory to analyze (for analysis mode)'
    )
    
    parser.add_argument(
        '--validate',
        type=Path,
        help='Validate existing CSV file'
    )
    
    args = parser.parse_args()
    
    # Determine output directory
    output_dir = DEVTOOLS
    if args.output:
        if args.output.is_dir():
            output_dir = args.output
        else:
            output_dir = args.output.parent
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Execute based on mode
    if args.mode == 'template':
        output_file = args.output or (output_dir / f"file_rename_template.csv")
        generate_template_csv(output_file, args.product.upper())
    
    elif args.mode == 'product':
        create_product_specific_csv(args.product.upper(), output_dir)
    
    elif args.mode == 'analysis':
        if not args.directory:
            print("❌ --directory required for analysis mode")
            return
        
        output_file = args.output or (output_dir / f"file_rename_{args.product.lower()}_analyzed.csv")
        generate_from_analysis(args.directory, output_file, args.product.upper())
    
    elif args.mode == 'validate':
        if args.validate:
            validate_csv(args.validate)
        else:
            print("❌ --validate file required for validate mode")


if __name__ == "__main__":
    main()
