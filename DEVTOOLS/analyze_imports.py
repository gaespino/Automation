"""
BASELINE Import Analysis - Detailed Report Generator
=====================================================
Analyzes all imports and shows which files use each package.

Usage:
    python analyze_imports.py
"""

import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

BASELINE_PATH = Path(r"c:\Git\Automation\Automation\S2T\BASELINE")

# Known external packages
EXTERNAL_PACKAGES = {
    'pandas', 'numpy', 'openpyxl', 'xlwings', 'pymongo', 
    'colorama', 'tabulate', 'pytz', 'psutil', 'lxml'
}

# Known Intel-specific packages
INTEL_PACKAGES = {
    'ipccli', 'namednodes', 'svtools', 'toolext', 'pm', 
    'registers', 'strategy', 'configs'
}

# Standard library modules to track
STANDARD_LIB = {
    'sys', 'os', 'json', 'time', 'datetime', 'threading',
    'multiprocessing', 'queue', 're', 'pathlib', 'shutil',
    'subprocess', 'socket', 'uuid', 'tempfile', 'logging',
    'unittest', 'argparse', 'collections', 'functools',
    'typing', 'dataclasses', 'enum', 'abc', 'contextlib',
    'weakref', 'signal', 'traceback', 'io', 'csv', 'zipfile',
    'configparser', 'copy', 'math', 'statistics', 'random',
    'string', 'atexit', 'getpass', 'http'
}


def extract_package_name(import_line: str) -> str:
    """Extract the base package name from an import statement."""
    # Remove 'import ' or 'from '
    line = import_line.strip()
    
    if line.startswith('from '):
        # from X import Y -> X
        match = re.match(r'from\s+(\S+)', line)
        if match:
            module = match.group(1)
            # Handle relative imports
            if module.startswith('.'):
                return 'relative'
            # Get first part
            return module.split('.')[0]
    elif line.startswith('import '):
        # import X or import X as Y -> X
        match = re.match(r'import\s+(\S+)', line)
        if match:
            module = match.group(1)
            return module.split('.')[0]
    
    return 'unknown'


def categorize_import(package: str, full_line: str) -> str:
    """Categorize an import into external, intel, standard, or project."""
    if package == 'relative':
        return 'relative'
    
    if package in EXTERNAL_PACKAGES:
        return 'external'
    
    if package in INTEL_PACKAGES:
        return 'intel'
    
    if package in STANDARD_LIB:
        return 'standard'
    
    # Check if it's a project import
    project_modules = {
        'DebugFramework', 'TestMocks', 'TestFramework', 'FileHandler',
        'MaskEditor', 'SerialConnection', 'SystemDebug', 'ExecutionHandler',
        'Automation_Flow', 'PPV', 'S2T', 'Storage_Handler', 'Interfaces',
        'UI', 'Logger', 'Decoder', 'ConfigsLoader', 'EFI', 'HardwareMocks'
    }
    
    if package in project_modules:
        return 'project'
    
    return 'other'


def analyze_imports():
    """Analyze all imports in BASELINE directory."""
    
    imports_map = defaultdict(list)  # import_line -> [files]
    package_map = defaultdict(lambda: defaultdict(list))  # category -> package -> [files]
    
    print("Scanning Python files in BASELINE...")
    
    # Scan all Python files
    py_files = list(BASELINE_PATH.rglob("*.py"))
    print(f"Found {len(py_files)} Python files\n")
    
    for py_file in py_files:
        rel_path = py_file.relative_to(BASELINE_PATH)
        
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    # Store full import line
                    imports_map[line].append((str(rel_path), line_num))
                    
                    # Extract and categorize package
                    package = extract_package_name(line)
                    category = categorize_import(package, line)
                    package_map[category][package].append((str(rel_path), line_num))
    
    return imports_map, package_map


def generate_report(imports_map, package_map):
    """Generate detailed import report."""
    
    output_lines = []
    
    output_lines.append("=" * 80)
    output_lines.append("BASELINE IMPORT ANALYSIS - DETAILED REPORT")
    output_lines.append("=" * 80)
    output_lines.append(f"Generated: 2025-12-09")
    output_lines.append(f"Total unique import statements: {len(imports_map)}")
    output_lines.append("")
    
    # Summary by category
    output_lines.append("=" * 80)
    output_lines.append("SUMMARY BY CATEGORY")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    for category in ['external', 'intel', 'standard', 'project', 'relative', 'other']:
        if category in package_map:
            packages = package_map[category]
            total_files = sum(len(set(f[0] for f in files)) for files in packages.values())
            output_lines.append(f"{category.upper():15} {len(packages):3} packages, {total_files:4} file references")
    
    output_lines.append("")
    
    # External Packages Detail
    output_lines.append("=" * 80)
    output_lines.append("EXTERNAL PACKAGES (pip/conda)")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    if 'external' in package_map:
        for package, files in sorted(package_map['external'].items()):
            unique_files = sorted(set(f[0] for f in files))
            output_lines.append(f"📦 {package}")
            output_lines.append(f"   Used in {len(unique_files)} file(s):")
            for file in unique_files[:10]:  # Limit to 10 for readability
                output_lines.append(f"   - {file}")
            if len(unique_files) > 10:
                output_lines.append(f"   ... and {len(unique_files) - 10} more files")
            output_lines.append("")
    
    # Intel Packages Detail
    output_lines.append("=" * 80)
    output_lines.append("INTEL-SPECIFIC PACKAGES")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    if 'intel' in package_map:
        for package, files in sorted(package_map['intel'].items()):
            unique_files = sorted(set(f[0] for f in files))
            output_lines.append(f"🏢 {package}")
            output_lines.append(f"   Used in {len(unique_files)} file(s):")
            for file in unique_files[:10]:
                output_lines.append(f"   - {file}")
            if len(unique_files) > 10:
                output_lines.append(f"   ... and {len(unique_files) - 10} more files")
            output_lines.append("")
    
    # Most Used Standard Library Modules
    output_lines.append("=" * 80)
    output_lines.append("MOST USED STANDARD LIBRARY MODULES (Top 15)")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    if 'standard' in package_map:
        std_sorted = sorted(
            package_map['standard'].items(), 
            key=lambda x: len(set(f[0] for f in x[1])), 
            reverse=True
        )[:15]
        
        for package, files in std_sorted:
            unique_files = set(f[0] for f in files)
            output_lines.append(f"📚 {package:20} - Used in {len(unique_files):3} files")
        output_lines.append("")
    
    # Project Modules
    output_lines.append("=" * 80)
    output_lines.append("PROJECT MODULES (Top 15 Most Used)")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    if 'project' in package_map:
        proj_sorted = sorted(
            package_map['project'].items(), 
            key=lambda x: len(set(f[0] for f in x[1])), 
            reverse=True
        )[:15]
        
        for package, files in proj_sorted:
            unique_files = set(f[0] for f in files)
            output_lines.append(f"🔧 {package:25} - Used in {len(unique_files):3} files")
        output_lines.append("")
    
    # Detailed Import Statements
    output_lines.append("=" * 80)
    output_lines.append("DETAILED IMPORT STATEMENTS BY PACKAGE")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    # Group imports by package
    by_package = defaultdict(list)
    for import_line, files in imports_map.items():
        package = extract_package_name(import_line)
        category = categorize_import(package, import_line)
        if category in ['external', 'intel']:
            by_package[package].append((import_line, files))
    
    for package in sorted(by_package.keys()):
        output_lines.append(f"\n{'='*80}")
        output_lines.append(f"Package: {package}")
        output_lines.append(f"{'='*80}\n")
        
        for import_line, files in sorted(by_package[package]):
            unique_files = sorted(set(f[0] for f in files))
            output_lines.append(f"Import: {import_line}")
            output_lines.append(f"Used in {len(unique_files)} file(s):")
            
            for file_path in unique_files[:5]:
                # Find line numbers for this file
                line_nums = [f[1] for f in files if f[0] == file_path]
                if len(line_nums) == 1:
                    output_lines.append(f"  - {file_path}:{line_nums[0]}")
                else:
                    output_lines.append(f"  - {file_path} (lines: {', '.join(map(str, line_nums))})")
            
            if len(unique_files) > 5:
                output_lines.append(f"  ... and {len(unique_files) - 5} more files")
            output_lines.append("")
    
    return "\n".join(output_lines)


def main():
    """Main entry point."""
    print("Analyzing BASELINE imports...")
    print(f"Scanning: {BASELINE_PATH}\n")
    
    imports_map, package_map = analyze_imports()
    
    print("Generating report...")
    report = generate_report(imports_map, package_map)
    
    # Save to file
    output_file = Path(r"c:\Git\Automation\Automation\DEVTOOLS\BASELINE_IMPORTS_DETAILED.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Report saved to: {output_file}")
    print(f"   Total imports analyzed: {len(imports_map)}")
    print(f"   External packages: {len(package_map.get('external', {}))}")
    print(f"   Intel packages: {len(package_map.get('intel', {}))}")
    print(f"   Standard library: {len(package_map.get('standard', {}))}")
    print(f"   Project modules: {len(package_map.get('project', {}))}")


if __name__ == "__main__":
    main()
