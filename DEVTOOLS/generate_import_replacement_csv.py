"""
Generate Import Replacement CSV Template
=========================================
Creates CSV files for import replacement configuration used by deploy_universal.py

This tool helps you:
1. Generate template CSV from import analysis
2. Create product-specific replacement rules
3. Map base imports to product variants

Usage:
    python generate_import_replacement_csv.py [options]

Author: GitHub Copilot
Version: 1.0.0
Date: December 9, 2025
"""

import csv
import json
import argparse
from pathlib import Path
from typing import Dict, List, Set

DEVTOOLS = Path(__file__).parent
WORKSPACE = DEVTOOLS.parent


def load_import_analysis(analysis_file: Path) -> Dict:
    """Load import analysis from detailed report."""
    imports = {
        'external': set(),
        'intel': set(),
        'project': set()
    }
    
    if not analysis_file.exists():
        print(f"Analysis file not found: {analysis_file}")
        return imports
    
    current_category = None
    
    with open(analysis_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Detect category headers
            if '## External Packages' in line:
                current_category = 'external'
            elif '## Intel-Specific Packages' in line:
                current_category = 'intel'
            elif '## Project-Specific Modules' in line:
                current_category = 'project'
            elif line.startswith('### ') and current_category:
                # Extract package name from header like "### pandas"
                package = line.replace('###', '').strip()
                if package and not package.startswith('Standard'):
                    imports[current_category].add(package)
    
    return imports


def generate_template_csv(output_file: Path, product_prefix: str = "GNR"):
    """Generate CSV template for import replacements."""
    
    # Common replacement patterns
    replacements = [
        # DebugFramework modules
        {
            'old_import': 'from DebugFramework.SystemDebug import',
            'new_import': f'from DebugFramework.{product_prefix}SystemDebug import',
            'description': 'Product-specific SystemDebug'
        },
        {
            'old_import': 'from DebugFramework import SystemDebug',
            'new_import': f'from DebugFramework import {product_prefix}SystemDebug as SystemDebug',
            'description': 'Product-specific SystemDebug alias'
        },
        {
            'old_import': 'import DebugFramework.SystemDebug',
            'new_import': f'import DebugFramework.{product_prefix}SystemDebug as SystemDebug',
            'description': 'Product-specific SystemDebug module'
        },
        # S2T modules
        {
            'old_import': 'from S2T.dpmChecks import',
            'new_import': f'from S2T.{product_prefix}dpmChecks import',
            'description': 'Product-specific dpmChecks'
        },
        {
            'old_import': 'from S2T import CoreManipulation',
            'new_import': f'from S2T import {product_prefix}CoreManipulation as CoreManipulation',
            'description': 'Product-specific CoreManipulation'
        },
        # Config files
        {
            'old_import': 'users.gaespino.dev.DebugFramework.SystemDebug',
            'new_import': f'users.gaespino.DebugFramework.{product_prefix}SystemDebug',
            'description': 'Path replacement for product variant'
        },
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['old_import', 'new_import', 'description', 'enabled'])
        writer.writeheader()
        
        for replacement in replacements:
            writer.writerow({
                'old_import': replacement['old_import'],
                'new_import': replacement['new_import'],
                'description': replacement['description'],
                'enabled': 'yes'
            })
    
    print(f"✅ Template CSV created: {output_file}")
    print(f"   Product prefix: {product_prefix}")
    print(f"   Total rules: {len(replacements)}")


def generate_from_analysis(analysis_file: Path, output_file: Path, source_prefix: str = "", target_prefix: str = "GNR"):
    """Generate CSV from import analysis file."""
    
    imports = load_import_analysis(analysis_file)
    
    replacements = []
    
    # Process project-specific imports
    for module in imports['project']:
        if not source_prefix or module.startswith(source_prefix):
            # Create replacement rule
            replacements.append({
                'old_import': f'from {module} import',
                'new_import': f'from {module.replace(source_prefix, target_prefix)} import',
                'description': f'Project module: {module}',
                'enabled': 'yes'
            })
            
            replacements.append({
                'old_import': f'import {module}',
                'new_import': f'import {module.replace(source_prefix, target_prefix)} as {module.split(".")[-1]}',
                'description': f'Project module import: {module}',
                'enabled': 'yes'
            })
    
    if replacements:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['old_import', 'new_import', 'description', 'enabled'])
            writer.writeheader()
            writer.writerows(replacements)
        
        print(f"✅ Replacement CSV created: {output_file}")
        print(f"   Source prefix: {source_prefix or '(none)'}")
        print(f"   Target prefix: {target_prefix}")
        print(f"   Total rules: {len(replacements)}")
    else:
        print("❌ No project imports found to create replacements")


def create_product_specific_csv(product: str, output_dir: Path):
    """Create product-specific CSV templates."""
    
    product_configs = {
        'GNR': {
            'prefix': 'GNR',
            'paths': [
                'DebugFramework.SystemDebug',
                'S2T.dpmChecks',
                'S2T.CoreManipulation'
            ]
        },
        'CWF': {
            'prefix': 'CWF',
            'paths': [
                'DebugFramework.SystemDebug',
                'S2T.dpmChecks',
                'S2T.CoreManipulation'
            ]
        },
        'DMR': {
            'prefix': 'DMR',
            'paths': [
                'DebugFramework.SystemDebug',
                'S2T.dpmChecks',
                'S2T.CoreManipulation'
            ]
        }
    }
    
    if product not in product_configs:
        print(f"❌ Unknown product: {product}")
        print(f"   Available: {', '.join(product_configs.keys())}")
        return
    
    config = product_configs[product]
    output_file = output_dir / f"import_replacement_{product.lower()}.csv"
    
    replacements = []
    
    for path in config['paths']:
        module_name = path.split('.')[-1]
        
        # from X import Y
        replacements.append({
            'old_import': f'from {path} import',
            'new_import': f'from {path.rsplit(".", 1)[0]}.{config["prefix"]}{module_name} import',
            'description': f'{product} variant: {module_name}',
            'enabled': 'yes'
        })
        
        # import X as Y
        replacements.append({
            'old_import': f'import {path}',
            'new_import': f'import {path.rsplit(".", 1)[0]}.{config["prefix"]}{module_name} as {module_name}',
            'description': f'{product} variant import: {module_name}',
            'enabled': 'yes'
        })
        
        # Path replacements for config files
        replacements.append({
            'old_import': f'users.gaespino.dev.{path}',
            'new_import': f'users.gaespino.{path.rsplit(".", 1)[0]}.{config["prefix"]}{module_name}',
            'description': f'{product} config path: {module_name}',
            'enabled': 'yes'
        })
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['old_import', 'new_import', 'description', 'enabled'])
        writer.writeheader()
        writer.writerows(replacements)
    
    print(f"✅ Product-specific CSV created: {output_file}")
    print(f"   Product: {product}")
    print(f"   Total rules: {len(replacements)}")
    print(f"\nYou can now load this CSV in deploy_universal.py")


def validate_csv(csv_file: Path):
    """Validate a replacement CSV file."""
    
    if not csv_file.exists():
        print(f"❌ File not found: {csv_file}")
        return False
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            required = {'old_import', 'new_import'}
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
                print(f"\n📋 Sample rules:")
                for i, rule in enumerate(rules[:3], 1):
                    print(f"   {i}. {rule['old_import']}")
                    print(f"      → {rule['new_import']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error validating CSV: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate import replacement CSV templates for deployment"
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
        '--analysis',
        type=Path,
        help='Import analysis file (for analysis mode)'
    )
    
    parser.add_argument(
        '--source-prefix',
        default='',
        help='Source module prefix to replace'
    )
    
    parser.add_argument(
        '--target-prefix',
        default='GNR',
        help='Target module prefix'
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
        output_file = args.output or (output_dir / f"import_replacement_template.csv")
        generate_template_csv(output_file, args.target_prefix)
    
    elif args.mode == 'product':
        create_product_specific_csv(args.product.upper(), output_dir)
    
    elif args.mode == 'analysis':
        if not args.analysis:
            print("❌ --analysis file required for analysis mode")
            return
        
        output_file = args.output or (output_dir / f"import_replacement_from_analysis.csv")
        generate_from_analysis(args.analysis, output_file, args.source_prefix, args.target_prefix)
    
    elif args.mode == 'validate':
        if args.validate:
            validate_csv(args.validate)
        else:
            print("❌ --validate file required for validate mode")


if __name__ == "__main__":
    main()
