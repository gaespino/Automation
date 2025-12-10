"""
Universal Deployment Tool for BASELINE Projects
================================================
Deploys code from BASELINE/BASELINE_DMR to product-specific locations
with intelligent import replacement and selective deployment.

Features:
- Deploy S2T or DebugFramework independently
- Multiple source support (BASELINE, BASELINE_DMR, PPV)
- Import replacement from CSV configuration
- Visual selection with checkboxes
- Smart file comparison
- Automatic backups

Author: GitHub Copilot
Version: 2.0.0
Date: December 9, 2025
"""

import os
import sys
import json
import csv
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from pathlib import Path
import difflib
import shutil
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
import hashlib
import re

# Default Paths
WORKSPACE_ROOT = Path(r"c:\Git\Automation\Automation")
BASELINE_PATH = WORKSPACE_ROOT / "S2T" / "BASELINE"
BASELINE_DMR_PATH = WORKSPACE_ROOT / "S2T" / "BASELINE_DMR"
PPV_PATH = WORKSPACE_ROOT / "PPV"
DEVTOOLS_PATH = WORKSPACE_ROOT / "DEVTOOLS"
BACKUP_BASE = DEVTOOLS_PATH / "backups"

# Similarity threshold
SIMILARITY_THRESHOLD = 0.3

# Product-specific folders to filter
PRODUCT_SPECIFIC_FOLDERS = ['product_specific', 'GNR', 'CWF', 'DMR']


def load_config():
    """Load configuration from JSON file if exists."""
    config_file = DEVTOOLS_PATH / "deploy_config.json"
    
    default_config = {
        "paths": {
            "baseline": str(BASELINE_PATH),
            "baseline_dmr": str(BASELINE_DMR_PATH),
            "ppv": str(PPV_PATH),
            "backup_base": str(BACKUP_BASE)
        },
        "settings": {
            "similarity_threshold": 0.3
        },
        "product_configs": {
            "GNR": {
                "source_type": "BASELINE",
                "deployment_type": "DebugFramework",
                "target_base": "",
                "replacement_csv": "",
                "selected_files": []
            },
            "CWF": {
                "source_type": "BASELINE",
                "deployment_type": "DebugFramework",
                "target_base": "",
                "replacement_csv": "",
                "selected_files": []
            },
            "DMR": {
                "source_type": "BASELINE_DMR",
                "deployment_type": "DebugFramework",
                "target_base": "",
                "replacement_csv": "",
                "selected_files": []
            }
        }
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                loaded = json.load(f)
                # Merge configs
                if 'paths' in loaded:
                    default_config['paths'].update(loaded['paths'])
                if 'settings' in loaded:
                    default_config['settings'].update(loaded['settings'])
                if 'product_configs' in loaded:
                    for product, prod_config in loaded['product_configs'].items():
                        if product in default_config['product_configs']:
                            default_config['product_configs'][product].update(prod_config)
                        else:
                            default_config['product_configs'][product] = prod_config
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
    
    return default_config


def save_config(config):
    """Save configuration to JSON file."""
    config_file = DEVTOOLS_PATH / "deploy_config.json"
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Warning: Could not save config: {e}")
        return False


CONFIG = load_config()


class FileRenamer:
    """Handles file renaming based on CSV configuration."""
    
    def __init__(self):
        self.renames = {}  # old_file_path -> (new_file_path, update_imports)
        self.name_mappings = {}  # old_name -> new_name (for import updates)
    
    def load_from_csv(self, csv_path: Path) -> bool:
        """Load file rename rules from CSV file."""
        if not csv_path.exists():
            return False
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('enabled', 'yes').lower() != 'yes':
                        continue
                    
                    old_file = row.get('old_file', '').strip()
                    new_file = row.get('new_file', '').strip()
                    old_name = row.get('old_name', '').strip()
                    new_name = row.get('new_name', '').strip()
                    update_imports = row.get('update_imports', 'no').lower() == 'yes'
                    
                    if old_file and new_file:
                        self.renames[old_file] = (new_file, update_imports)
                    
                    if old_name and new_name and update_imports:
                        # Store module name mappings for import updates
                        old_module = old_name.replace('.py', '')
                        new_module = new_name.replace('.py', '')
                        self.name_mappings[old_module] = new_module
            
            return True
        except Exception as e:
            print(f"Error loading file rename CSV: {e}")
            return False
    
    def get_new_path(self, rel_path: str) -> Tuple[str, bool]:
        """Get new path for file if rename rule exists."""
        rel_path_normalized = str(Path(rel_path)).replace('\\', '/')
        
        for old_file, (new_file, update_imports) in self.renames.items():
            old_file_normalized = old_file.replace('\\', '/')
            if rel_path_normalized == old_file_normalized or rel_path_normalized.endswith(old_file_normalized):
                return (new_file, update_imports)
        
        return (rel_path, False)
    
    def update_imports_in_content(self, content: str) -> Tuple[str, List[Tuple[str, str]]]:
        """Update imports in file content based on name mappings."""
        if not self.name_mappings:
            return content, []
        
        modified_content = content
        changes = []
        
        for old_name, new_name in self.name_mappings.items():
            # Pattern 1: from X.Y import (where Y is old_name)
            pattern1 = f'.{old_name} import'
            replacement1 = f'.{new_name} import'
            if pattern1 in modified_content:
                modified_content = modified_content.replace(pattern1, replacement1)
                changes.append((pattern1, replacement1))
            
            # Pattern 2: import X.Y (where Y is old_name)
            pattern2 = f'import {old_name}'
            replacement2 = f'import {new_name}'
            if pattern2 in modified_content and pattern2 != replacement2:
                modified_content = modified_content.replace(pattern2, replacement2)
                changes.append((pattern2, replacement2))
            
            # Pattern 3: from X import Y (where Y is old_name)
            pattern3 = f'from {old_name} import'
            replacement3 = f'from {new_name} import'
            if pattern3 in modified_content:
                modified_content = modified_content.replace(pattern3, replacement3)
                changes.append((pattern3, replacement3))
        
        return modified_content, changes


class ImportReplacer:
    """Handles import statement replacement based on CSV configuration."""
    
    def __init__(self):
        self.replacements = {}  # old_import -> new_import
    
    def load_from_csv(self, csv_path: Path) -> bool:
        """Load import replacements from CSV file."""
        if not csv_path.exists():
            return False
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'old_import' in row and 'new_import' in row:
                        old = row['old_import'].strip()
                        new = row['new_import'].strip()
                        if old and new:
                            self.replacements[old] = new
            return True
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return False
    
    def add_replacement(self, old_import: str, new_import: str):
        """Add a single replacement rule."""
        self.replacements[old_import] = new_import
    
    def replace_in_file(self, file_path: Path) -> Tuple[str, int]:
        """
        Replace imports in a file and return modified content.
        Returns: (modified_content, replacement_count)
        """
        if not file_path.exists():
            return "", 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return "", 0
        
        modified_content = content
        replacement_count = 0
        
        # Apply each replacement
        for old_import, new_import in self.replacements.items():
            if old_import in modified_content:
                modified_content = modified_content.replace(old_import, new_import)
                replacement_count += modified_content.count(new_import) - content.count(new_import)
        
        return modified_content, replacement_count
    
    def get_replacements_for_file(self, file_path: Path) -> List[Tuple[str, str]]:
        """Get list of replacements that would apply to a file."""
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return []
        
        applicable = []
        for old_import, new_import in self.replacements.items():
            if old_import in content:
                applicable.append((old_import, new_import))
        
        return applicable


class FileComparer:
    """Handles file comparison and similarity calculation."""
    
    @staticmethod
    def get_file_hash(file_path: Path) -> str:
        """Calculate MD5 hash of a file."""
        if not file_path.exists():
            return ""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    @staticmethod
    def compare_files(source: Path, target: Path, replacer: ImportReplacer = None) -> Dict:
        """Compare two files with optional import replacement."""
        result = {
            'exists': target.exists(),
            'identical': False,
            'similarity': 0.0,
            'diff_lines': [],
            'status': 'new',
            'source_size': 0,
            'target_size': 0,
            'replacements': []
        }
        
        if not source.exists():
            result['status'] = 'missing_source'
            return result
        
        result['source_size'] = source.stat().st_size
        
        # Get replacements if applicable
        if replacer and source.suffix == '.py':
            result['replacements'] = replacer.get_replacements_for_file(source)
        
        if not target.exists():
            result['status'] = 'new'
            return result
        
        result['target_size'] = target.stat().st_size
        
        # Read source (with replacements if applicable)
        try:
            if replacer and source.suffix == '.py':
                source_content, _ = replacer.replace_in_file(source)
                source_lines = source_content.splitlines(keepends=True)
            else:
                with open(source, 'r', encoding='utf-8', errors='ignore') as f:
                    source_lines = f.readlines()
            
            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                target_lines = f.readlines()
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            return result
        
        # Check if identical after replacements
        source_hash = hashlib.md5(''.join(source_lines).encode()).hexdigest()
        target_hash = hashlib.md5(''.join(target_lines).encode()).hexdigest()
        
        if source_hash == target_hash:
            result['identical'] = True
            result['similarity'] = 1.0
            result['status'] = 'identical'
            return result
        
        # Calculate similarity
        matcher = difflib.SequenceMatcher(None, source_lines, target_lines)
        result['similarity'] = matcher.ratio()
        
        # Generate diff
        diff = difflib.unified_diff(
            target_lines,
            source_lines,
            fromfile=f"current: {target.name}",
            tofile=f"new: {source.name}",
            lineterm=''
        )
        result['diff_lines'] = list(diff)
        
        # Determine status
        if result['similarity'] < SIMILARITY_THRESHOLD:
            result['status'] = 'major_changes'
        elif result['similarity'] < 0.9:
            result['status'] = 'minor_changes'
        else:
            result['status'] = 'minimal_changes'
        
        return result


class CSVGeneratorDialog:
    """Dialog for generating CSV templates."""
    
    def __init__(self, parent, title: str, product: str, csv_type: str, callback=None):
        """
        Initialize CSV generator dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            product: Product name (GNR, CWF, DMR)
            csv_type: Type of CSV ('import' or 'rename')
            callback: Function to call with generated file path
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.product = product
        self.csv_type = csv_type
        self.callback = callback
        self.result_file = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the dialog UI."""
        # Header
        header = ttk.Frame(self.dialog, padding="10")
        header.pack(fill='x')
        
        ttk.Label(
            header,
            text=f"Generate {self.csv_type.title()} CSV for {self.product}",
            font=('Arial', 12, 'bold')
        ).pack()
        
        # Options frame
        options_frame = ttk.LabelFrame(self.dialog, text="Options", padding="10")
        options_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Product prefix
        prefix_frame = ttk.Frame(options_frame)
        prefix_frame.pack(fill='x', pady=5)
        
        ttk.Label(prefix_frame, text="Product Prefix:", width=20).pack(side='left')
        self.prefix_var = tk.StringVar(value=self.product)
        ttk.Entry(prefix_frame, textvariable=self.prefix_var, width=15).pack(side='left', padx=5)
        
        # File name
        filename_frame = ttk.Frame(options_frame)
        filename_frame.pack(fill='x', pady=5)
        
        ttk.Label(filename_frame, text="Output File:", width=20).pack(side='left')
        default_name = f"{self.csv_type}_replacement_{self.product.lower()}.csv" if self.csv_type == "import" else f"file_rename_{self.product.lower()}.csv"
        self.filename_var = tk.StringVar(value=default_name)
        ttk.Entry(filename_frame, textvariable=self.filename_var, width=40).pack(side='left', padx=5)
        
        # Output directory
        dir_frame = ttk.Frame(options_frame)
        dir_frame.pack(fill='x', pady=5)
        
        ttk.Label(dir_frame, text="Output Directory:", width=20).pack(side='left')
        self.dir_var = tk.StringVar(value=str(DEVTOOLS_PATH))
        ttk.Entry(dir_frame, textvariable=self.dir_var, width=40).pack(side='left', padx=5)
        ttk.Button(dir_frame, text="Browse...", command=self.browse_directory).pack(side='left')
        
        # Info text
        info_frame = ttk.LabelFrame(options_frame, text="Template Contents", padding="10")
        info_frame.pack(fill='both', expand=True, pady=10)
        
        info_text = scrolledtext.ScrolledText(info_frame, height=8, wrap='word')
        info_text.pack(fill='both', expand=True)
        
        if self.csv_type == "import":
            info_content = f"""This will generate a template CSV with common import replacement patterns for {self.product}:

• SystemDebug → {self.product}SystemDebug
• TestFramework → {self.product}TestFramework  
• dpmChecks → {self.product}dpmChecks
• CoreManipulation → {self.product}CoreManipulation

You can edit the generated CSV to add or modify replacement rules."""
        else:
            info_content = f"""This will generate a template CSV with common file rename patterns for {self.product}:

• SystemDebug.py → {self.product}SystemDebug.py
• TestFramework.py → {self.product}TestFramework.py
• dpmChecks.py → {self.product}dpmChecks.py
• CoreManipulation.py → {self.product}CoreManipulation.py

Files will be automatically renamed during deployment, and imports will be updated."""
        
        info_text.insert('1.0', info_content)
        info_text.config(state='disabled')
        
        # Buttons
        button_frame = ttk.Frame(self.dialog, padding="10")
        button_frame.pack(fill='x', side='bottom')
        
        ttk.Button(
            button_frame,
            text="Generate",
            command=self.generate_csv
        ).pack(side='right', padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side='right', padx=5)
    
    def browse_directory(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.dir_var.get()
        )
        if directory:
            self.dir_var.set(directory)
    
    def generate_csv(self):
        """Generate the CSV file."""
        try:
            output_dir = Path(self.dir_var.get())
            output_file = output_dir / self.filename_var.get()
            prefix = self.prefix_var.get()
            
            if self.csv_type == "import":
                self._generate_import_csv(output_file, prefix)
            else:
                self._generate_rename_csv(output_file, prefix)
            
            self.result_file = output_file
            
            messagebox.showinfo(
                "Success",
                f"CSV template generated:\n{output_file.name}\n\nThe file has been created and will be loaded automatically."
            )
            
            # Call callback with result
            if self.callback:
                self.callback(self.result_file)
            
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate CSV:\n{str(e)}")
    
    def _generate_import_csv(self, output_file: Path, prefix: str):
        """Generate import replacement CSV."""
        replacements = [
            {
                'old_import': 'from DebugFramework.SystemDebug import',
                'new_import': f'from DebugFramework.{prefix}SystemDebug import',
                'description': f'Product-specific SystemDebug',
                'enabled': 'yes'
            },
            {
                'old_import': 'from DebugFramework import SystemDebug',
                'new_import': f'from DebugFramework import {prefix}SystemDebug as SystemDebug',
                'description': f'Product-specific SystemDebug alias',
                'enabled': 'yes'
            },
            {
                'old_import': 'import DebugFramework.SystemDebug',
                'new_import': f'import DebugFramework.{prefix}SystemDebug as SystemDebug',
                'description': f'Product-specific SystemDebug module',
                'enabled': 'yes'
            },
            {
                'old_import': 'from S2T.dpmChecks import',
                'new_import': f'from S2T.{prefix}dpmChecks import',
                'description': f'Product-specific dpmChecks',
                'enabled': 'yes'
            },
            {
                'old_import': 'from S2T import CoreManipulation',
                'new_import': f'from S2T import {prefix}CoreManipulation as CoreManipulation',
                'description': f'Product-specific CoreManipulation',
                'enabled': 'yes'
            },
            {
                'old_import': 'from S2T.CoreManipulation import',
                'new_import': f'from S2T.{prefix}CoreManipulation import',
                'description': f'Product-specific CoreManipulation imports',
                'enabled': 'yes'
            },
            {
                'old_import': 'users.gaespino.dev.DebugFramework.SystemDebug',
                'new_import': f'users.gaespino.DebugFramework.{prefix}SystemDebug',
                'description': f'Path replacement for product variant',
                'enabled': 'yes'
            },
            {
                'old_import': 'from DebugFramework.TestFramework import',
                'new_import': f'from DebugFramework.{prefix}TestFramework import',
                'description': f'Product-specific TestFramework',
                'enabled': 'yes'
            },
            {
                'old_import': 'from DebugFramework import TestFramework',
                'new_import': f'from DebugFramework import {prefix}TestFramework as TestFramework',
                'description': f'Product-specific TestFramework alias',
                'enabled': 'yes'
            },
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['old_import', 'new_import', 'description', 'enabled'])
            writer.writeheader()
            writer.writerows(replacements)
    
    def _generate_rename_csv(self, output_file: Path, prefix: str):
        """Generate file rename CSV."""
        renames = [
            {
                'old_file': 'DebugFramework/SystemDebug.py',
                'new_file': f'DebugFramework/{prefix}SystemDebug.py',
                'old_name': 'SystemDebug.py',
                'new_name': f'{prefix}SystemDebug.py',
                'description': f'Rename SystemDebug to {prefix}SystemDebug',
                'update_imports': 'yes',
                'enabled': 'yes'
            },
            {
                'old_file': 'DebugFramework/TestFramework.py',
                'new_file': f'DebugFramework/{prefix}TestFramework.py',
                'old_name': 'TestFramework.py',
                'new_name': f'{prefix}TestFramework.py',
                'description': f'Rename TestFramework to {prefix}TestFramework',
                'update_imports': 'yes',
                'enabled': 'yes'
            },
            {
                'old_file': 'S2T/dpmChecks.py',
                'new_file': f'S2T/{prefix}dpmChecks.py',
                'old_name': 'dpmChecks.py',
                'new_name': f'{prefix}dpmChecks.py',
                'description': f'Rename dpmChecks to {prefix}dpmChecks',
                'update_imports': 'yes',
                'enabled': 'yes'
            },
            {
                'old_file': 'S2T/CoreManipulation.py',
                'new_file': f'S2T/{prefix}CoreManipulation.py',
                'old_name': 'CoreManipulation.py',
                'new_name': f'{prefix}CoreManipulation.py',
                'description': f'Rename CoreManipulation to {prefix}CoreManipulation',
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


class UniversalDeploymentGUI:
    """Main GUI for universal deployment tool."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Deployment Tool - BASELINE/PPV")
        self.root.geometry("1400x900")
        
        # State
        self.product = tk.StringVar(value="GNR")  # GNR, CWF, DMR
        self.source_type = tk.StringVar(value="BASELINE")  # BASELINE, BASELINE_DMR, PPV
        self.deployment_type = tk.StringVar(value="DebugFramework")  # DebugFramework, S2T, PPV
        self.source_base = BASELINE_PATH
        self.target_base = None
        self.backup_base = BACKUP_BASE
        
        self.files_data = {}
        self.selected_files = set()
        self.checkboxes = {}
        
        self.import_replacer = ImportReplacer()
        self.replacement_csv = None
        
        self.file_renamer = FileRenamer()
        self.rename_csv = None
        
        # Config management
        self.config = CONFIG
        self.config_auto_save = tk.BooleanVar(value=True)
        
        # Deployment tracking
        self.last_deployment_report = None
        
        self.setup_ui()
        self.load_product_config()
    
    def setup_ui(self):
        """Create the user interface."""
        # Header with source selection
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill='x')
        
        ttk.Label(
            header_frame,
            text="Universal Deployment Tool",
            font=('Arial', 16, 'bold')
        ).pack()
        
        # Source selection
        source_frame = ttk.LabelFrame(header_frame, text="Source Configuration", padding="10")
        source_frame.pack(fill='x', pady=5)
        
        # Product selection
        product_frame = ttk.Frame(source_frame)
        product_frame.pack(fill='x', pady=2)
        
        ttk.Label(product_frame, text="Product:", font=('Arial', 9, 'bold')).pack(side='left', padx=5)
        ttk.Radiobutton(
            product_frame,
            text="GNR",
            variable=self.product,
            value="GNR",
            command=self.on_product_change
        ).pack(side='left', padx=5)
        ttk.Radiobutton(
            product_frame,
            text="CWF",
            variable=self.product,
            value="CWF",
            command=self.on_product_change
        ).pack(side='left', padx=5)
        ttk.Radiobutton(
            product_frame,
            text="DMR",
            variable=self.product,
            value="DMR",
            command=self.on_product_change
        ).pack(side='left', padx=5)
        
        ttk.Separator(product_frame, orient='vertical').pack(side='left', fill='y', padx=10)
        
        ttk.Checkbutton(
            product_frame,
            text="Auto-save configuration",
            variable=self.config_auto_save
        ).pack(side='left', padx=5)
        
        ttk.Button(
            product_frame,
            text="Save Config",
            command=self.save_current_config
        ).pack(side='left', padx=5)
        
        # Source type
        src_type_frame = ttk.Frame(source_frame)
        src_type_frame.pack(fill='x')
        
        ttk.Label(src_type_frame, text="Source:", font=('Arial', 9, 'bold')).pack(side='left', padx=5)
        ttk.Radiobutton(
            src_type_frame,
            text="BASELINE",
            variable=self.source_type,
            value="BASELINE",
            command=self.on_source_change
        ).pack(side='left', padx=5)
        ttk.Radiobutton(
            src_type_frame,
            text="BASELINE_DMR",
            variable=self.source_type,
            value="BASELINE_DMR",
            command=self.on_source_change
        ).pack(side='left', padx=5)
        ttk.Radiobutton(
            src_type_frame,
            text="PPV",
            variable=self.source_type,
            value="PPV",
            command=self.on_source_change
        ).pack(side='left', padx=5)
        
        # Deployment type
        dep_type_frame = ttk.Frame(source_frame)
        dep_type_frame.pack(fill='x', pady=5)
        
        ttk.Label(dep_type_frame, text="Deploy:", font=('Arial', 9, 'bold')).pack(side='left', padx=5)
        ttk.Radiobutton(
            dep_type_frame,
            text="DebugFramework",
            variable=self.deployment_type,
            value="DebugFramework",
            command=self.on_deployment_type_change
        ).pack(side='left', padx=5)
        ttk.Radiobutton(
            dep_type_frame,
            text="S2T",
            variable=self.deployment_type,
            value="S2T",
            command=self.on_deployment_type_change
        ).pack(side='left', padx=5)
        
        # Show PPV option only when PPV source is selected
        self.ppv_radio = ttk.Radiobutton(
            dep_type_frame,
            text="PPV",
            variable=self.deployment_type,
            value="PPV",
            command=self.on_deployment_type_change,
            state='disabled'
        )
        self.ppv_radio.pack(side='left', padx=5)
        
        # Target selection
        target_frame = ttk.Frame(source_frame)
        target_frame.pack(fill='x', pady=5)
        
        ttk.Label(target_frame, text="Target:", font=('Arial', 9, 'bold')).pack(side='left', padx=5)
        self.target_label = ttk.Label(target_frame, text="Not selected", font=('Arial', 9))
        self.target_label.pack(side='left', padx=5)
        ttk.Button(
            target_frame,
            text="Select Target...",
            command=self.select_target
        ).pack(side='left', padx=5)
        
        # Import replacement
        import_frame = ttk.Frame(source_frame)
        import_frame.pack(fill='x', pady=5)
        
        ttk.Label(import_frame, text="Import Replacement CSV:", font=('Arial', 9, 'bold')).pack(side='left', padx=5)
        self.csv_label = ttk.Label(import_frame, text="None", font=('Arial', 9))
        self.csv_label.pack(side='left', padx=5)
        ttk.Button(
            import_frame,
            text="Load CSV...",
            command=self.load_replacement_csv
        ).pack(side='left', padx=5)
        ttk.Button(
            import_frame,
            text="Clear",
            command=self.clear_replacement_csv
        ).pack(side='left', padx=5)
        ttk.Button(
            import_frame,
            text="Generate...",
            command=self.generate_import_csv
        ).pack(side='left', padx=5)
        
        # File renaming
        rename_frame = ttk.Frame(source_frame)
        rename_frame.pack(fill='x', pady=5)
        
        ttk.Label(rename_frame, text="File Rename CSV:", font=('Arial', 9, 'bold')).pack(side='left', padx=5)
        self.rename_csv_label = ttk.Label(rename_frame, text="None", font=('Arial', 9))
        self.rename_csv_label.pack(side='left', padx=5)
        ttk.Button(
            rename_frame,
            text="Load CSV...",
            command=self.load_rename_csv
        ).pack(side='left', padx=5)
        ttk.Button(
            rename_frame,
            text="Clear",
            command=self.clear_rename_csv
        ).pack(side='left', padx=5)
        ttk.Button(
            rename_frame,
            text="Generate...",
            command=self.generate_rename_csv
        ).pack(side='left', padx=5)
        
        # Main content
        paned = ttk.PanedWindow(self.root, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left panel - File list
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        # Controls
        controls_frame = ttk.Frame(left_frame)
        controls_frame.pack(fill='x', pady=5)
        
        ttk.Button(controls_frame, text="Scan Files", command=self.scan_files).pack(side='left', padx=2)
        ttk.Button(controls_frame, text="Select All", command=self.select_all).pack(side='left', padx=2)
        ttk.Button(controls_frame, text="Deselect All", command=self.deselect_all).pack(side='left', padx=2)
        
        # Filter
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill='x', pady=5)
        ttk.Label(filter_frame, text="Filter:").pack(side='left')
        self.filter_var = tk.StringVar()
        self.filter_var.trace('w', lambda *args: self.apply_filter())
        ttk.Entry(filter_frame, textvariable=self.filter_var).pack(side='left', fill='x', expand=True, padx=5)
        
        # Filter options
        filter_opts = ttk.Frame(left_frame)
        filter_opts.pack(fill='x', pady=2)
        self.show_only_changes = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            filter_opts,
            text="Show only changes",
            variable=self.show_only_changes,
            command=self.apply_filter
        ).pack(side='left', padx=5)
        
        self.show_only_selected = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            filter_opts,
            text="Show only selected",
            variable=self.show_only_selected,
            command=self.apply_filter
        ).pack(side='left', padx=5)
        
        self.show_replacements = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            filter_opts,
            text="Show files with replacements",
            variable=self.show_replacements,
            command=self.apply_filter
        ).pack(side='left', padx=5)
        
        # Tree
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=('selected', 'status', 'similarity', 'replacements', 'rename'),
            yscrollcommand=scrollbar.set
        )
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Configure columns
        self.tree.heading('#0', text='File')
        self.tree.heading('selected', text='☑', command=self.toggle_all_visible)
        self.tree.heading('status', text='Status')
        self.tree.heading('similarity', text='Similar')
        self.tree.heading('replacements', text='Replacements')
        self.tree.heading('rename', text='Rename')
        
        self.tree.column('#0', width=300)
        self.tree.column('selected', width=40, anchor='center')
        self.tree.column('status', width=100)
        self.tree.column('similarity', width=70)
        self.tree.column('replacements', width=90)
        self.tree.column('rename', width=60, anchor='center')
        
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self.on_file_select)
        self.tree.bind('<space>', self.toggle_selection)
        self.tree.bind('<Button-1>', self.on_tree_click)
        
        # Configure tags
        self.tree.tag_configure('new', foreground='blue')
        self.tree.tag_configure('identical', foreground='gray')
        self.tree.tag_configure('minor_changes', foreground='orange')
        self.tree.tag_configure('major_changes', foreground='red')
        self.tree.tag_configure('renamed', font=('TkDefaultFont', 9, 'italic'))
        
        # Right panel - Details
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        # Details
        details_frame = ttk.LabelFrame(right_frame, text="File Details", padding="5")
        details_frame.pack(fill='x', pady=5)
        
        self.details_text = tk.Text(details_frame, height=10, wrap='word')
        self.details_text.pack(fill='x')
        
        # Diff
        diff_frame = ttk.LabelFrame(right_frame, text="Changes Preview", padding="5")
        diff_frame.pack(fill='both', expand=True, pady=5)
        
        self.diff_text = scrolledtext.ScrolledText(diff_frame, wrap='none', font=('Courier', 9))
        self.diff_text.pack(fill='both', expand=True)
        
        # Configure diff colors
        self.diff_text.tag_config('add', foreground='green')
        self.diff_text.tag_config('remove', foreground='red')
        self.diff_text.tag_config('header', foreground='blue', font=('Courier', 9, 'bold'))
        self.diff_text.tag_config('replacement', foreground='purple', font=('Courier', 9, 'bold'))
        
        # Bottom panel
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill='x', side='bottom')
        
        self.status_label = ttk.Label(
            bottom_frame,
            text="Select source, deployment type, and target to begin",
            relief='sunken'
        )
        self.status_label.pack(side='left', fill='x', expand=True)
        
        ttk.Button(
            bottom_frame,
            text="Deploy Selected",
            command=self.deploy_selected
        ).pack(side='right', padx=5)
        
        ttk.Button(
            bottom_frame,
            text="View Last Report",
            command=self.view_last_report,
            state='disabled'
        ).pack(side='right', padx=5)
        self.report_button = bottom_frame.children[list(bottom_frame.children.keys())[-1]]
        
        ttk.Button(
            bottom_frame,
            text="Export Selection",
            command=self.export_selection
        ).pack(side='right', padx=5)
    
    def on_product_change(self):
        """Handle product change."""
        if self.config_auto_save.get():
            self.save_current_config()
        self.load_product_config()
        self.clear_scan()
    
    def on_source_change(self):
        """Handle source type change."""
        source = self.source_type.get()
        
        if source == "BASELINE":
            self.source_base = BASELINE_PATH
            self.ppv_radio.config(state='disabled')
            if self.deployment_type.get() == "PPV":
                self.deployment_type.set("DebugFramework")
        elif source == "BASELINE_DMR":
            self.source_base = BASELINE_DMR_PATH
            self.ppv_radio.config(state='disabled')
            if self.deployment_type.get() == "PPV":
                self.deployment_type.set("DebugFramework")
        else:  # PPV
            self.source_base = PPV_PATH
            self.ppv_radio.config(state='normal')
            self.deployment_type.set("PPV")
        
        self.clear_scan()
        if self.config_auto_save.get():
            self.save_current_config()
    
    def on_deployment_type_change(self):
        """Handle deployment type change."""
        self.clear_scan()
        if self.config_auto_save.get():
            self.save_current_config()
    
    def select_target(self):
        """Select target directory."""
        initial_dir = WORKSPACE_ROOT
        if self.target_base:
            initial_dir = self.target_base.parent if self.target_base.exists() else WORKSPACE_ROOT
        
        target = filedialog.askdirectory(
            title="Select Target Directory",
            initialdir=initial_dir
        )
        
        if target:
            self.target_base = Path(target)
            self.target_label.config(text=str(self.target_base))
            self.status_label.config(text="Target selected. Click 'Scan Files' to compare.")
            if self.config_auto_save.get():
                self.save_current_config()
    
    def load_replacement_csv(self):
        """Load import replacement CSV file."""
        initial_dir = DEVTOOLS_PATH
        if self.replacement_csv and self.replacement_csv.exists():
            initial_dir = self.replacement_csv.parent
        
        csv_path = filedialog.askopenfilename(
            title="Select Import Replacement CSV",
            initialdir=initial_dir,
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if csv_path:
            csv_path = Path(csv_path)
            if self.import_replacer.load_from_csv(csv_path):
                self.replacement_csv = csv_path
                self.csv_label.config(text=csv_path.name)
                messagebox.showinfo(
                    "CSV Loaded",
                    f"Loaded {len(self.import_replacer.replacements)} replacement rules from:\n{csv_path.name}"
                )
                # Rescan if files already loaded
                if self.files_data:
                    self.scan_files()
                if self.config_auto_save.get():
                    self.save_current_config()
            else:
                messagebox.showerror("Error", "Failed to load CSV file")
    
    def clear_replacement_csv(self):
        """Clear import replacement configuration."""
        self.import_replacer = ImportReplacer()
        self.replacement_csv = None
        self.csv_label.config(text="None")
        # Rescan if files already loaded
        if self.files_data:
            self.scan_files()
    
    def load_rename_csv(self):
        """Load file rename CSV file."""
        initial_dir = DEVTOOLS_PATH
        if self.rename_csv and self.rename_csv.exists():
            initial_dir = self.rename_csv.parent
        
        csv_path = filedialog.askopenfilename(
            title="Select File Rename CSV",
            initialdir=initial_dir,
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if csv_path:
            csv_path = Path(csv_path)
            if self.file_renamer.load_from_csv(csv_path):
                self.rename_csv = csv_path
                self.rename_csv_label.config(text=csv_path.name)
                messagebox.showinfo(
                    "CSV Loaded",
                    f"Loaded {len(self.file_renamer.renames)} rename rules from:\n{csv_path.name}"
                )
                # Rescan if files already loaded
                if self.files_data:
                    self.scan_files()
                if self.config_auto_save.get():
                    self.save_current_config()
            else:
                messagebox.showerror("Error", "Failed to load rename CSV file")
    
    def clear_rename_csv(self):
        """Clear file rename configuration."""
        self.file_renamer = FileRenamer()
        self.rename_csv = None
        self.rename_csv_label.config(text="None")
        # Rescan if files already loaded
        if self.files_data:
            self.scan_files()
    
    def generate_import_csv(self):
        """Generate import replacement CSV template."""
        dialog = CSVGeneratorDialog(
            self.root,
            "Import Replacement CSV Generator",
            self.product.get(),
            "import",
            callback=self.on_import_csv_generated
        )
    
    def generate_rename_csv(self):
        """Generate file rename CSV template."""
        dialog = CSVGeneratorDialog(
            self.root,
            "File Rename CSV Generator",
            self.product.get(),
            "rename",
            callback=self.on_rename_csv_generated
        )
    
    def on_import_csv_generated(self, csv_file: Path):
        """Handle generated import CSV."""
        if csv_file and csv_file.exists():
            # Load the generated CSV
            if self.import_replacer.load_replacements(csv_file):
                self.replacement_csv = csv_file
                self.csv_label.config(text=csv_file.name)
                if self.config_auto_save.get():
                    self.save_current_config()
                messagebox.showinfo(
                    "CSV Generated",
                    f"Import replacement CSV created and loaded:\n{csv_file.name}"
                )
    
    def on_rename_csv_generated(self, csv_file: Path):
        """Handle generated rename CSV."""
        if csv_file and csv_file.exists():
            # Load the generated CSV
            if self.file_renamer.load_renames(csv_file):
                self.rename_csv = csv_file
                self.rename_csv_label.config(text=csv_file.name)
                # Rescan if files already loaded
                if self.files_data:
                    self.scan_files()
                if self.config_auto_save.get():
                    self.save_current_config()
                messagebox.showinfo(
                    "CSV Generated",
                    f"File rename CSV created and loaded:\n{csv_file.name}"
                )
    
    def clear_scan(self):
        """Clear current scan data."""
        self.files_data.clear()
        self.selected_files.clear()
        self.checkboxes.clear()
        self.tree.delete(*self.tree.get_children())
        self.status_label.config(text="Configuration changed. Click 'Scan Files' to compare.")
    
    def should_include_file(self, rel_path: Path) -> bool:
        """Check if file should be included based on product selection."""
        product = self.product.get()
        path_str = str(rel_path).lower()
        path_parts = [p.upper() for p in rel_path.parts]
        
        # Check if path contains product-specific folders
        has_product_folder = any(folder.lower() in path_str for folder in PRODUCT_SPECIFIC_FOLDERS)
        
        if has_product_folder:
            # If it's in a product-specific folder, only include if it matches current product
            # or if it's in the generic product_specific folder with product name in path
            if 'product_specific' in path_str:
                # Check if any part of the path matches the product
                return product in path_parts
            else:
                # Check if the path contains the product name as a folder
                return product in path_parts
        
        # If not in any product-specific folder, include it
        return True
    
    def scan_files(self):
        """Scan source directory and compare with target."""
        if not self.target_base:
            messagebox.showwarning("No Target", "Please select a target directory first.")
            return
        
        self.status_label.config(text="Scanning files...")
        self.root.update()
        
        self.files_data.clear()
        self.selected_files.clear()
        
        # Determine source path based on deployment type
        deployment = self.deployment_type.get()
        source = self.source_type.get()
        product = self.product.get()
        
        if source == "PPV":
            scan_base = self.source_base
        else:
            if deployment == "DebugFramework":
                scan_base = self.source_base / "DebugFramework"
            elif deployment == "S2T":
                scan_base = self.source_base / "S2T"
            else:
                scan_base = self.source_base
        
        if not scan_base.exists():
            messagebox.showerror("Error", f"Source path does not exist:\n{scan_base}")
            return
        
        # Scan Python and JSON files
        skipped_count = 0
        for root_dir, dirs, files in os.walk(scan_base):
            # Filter out system directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.vscode', '.git', '.pytest_cache']]
            
            for file in files:
                if file.endswith(('.py', '.json', '.ttl', '.ini')) and not file.startswith('__'):
                    source_path = Path(root_dir) / file
                    rel_path = source_path.relative_to(scan_base)
                    
                    # Check if file should be included based on product
                    if not self.should_include_file(rel_path):
                        skipped_count += 1
                        continue
                    
                    # Check if file should be renamed
                    new_rel_path, will_update_imports = self.file_renamer.get_new_path(str(rel_path))
                    target_path = self.target_base / new_rel_path
                    
                    # Compare with import replacement
                    comparison = FileComparer.compare_files(
                        source_path,
                        target_path,
                        self.import_replacer if source_path.suffix == '.py' else None
                    )
                    comparison['rel_path'] = str(rel_path)
                    comparison['new_rel_path'] = new_rel_path
                    comparison['renamed'] = str(rel_path) != new_rel_path
                    comparison['will_update_imports'] = will_update_imports
                    comparison['source_path'] = source_path
                    comparison['target_path'] = target_path
                    
                    self.files_data[str(rel_path)] = comparison
        
        self.populate_tree()
        status_msg = f"Found {len(self.files_data)} files for {product}"
        if skipped_count > 0:
            status_msg += f" (skipped {skipped_count} other product files)"
        self.status_label.config(text=status_msg)
    
    def populate_tree(self):
        """Populate tree view with files."""
        self.tree.delete(*self.tree.get_children())
        self.checkboxes.clear()
        
        # Group by directory
        directories = {}
        for rel_path, data in sorted(self.files_data.items()):
            parts = Path(rel_path).parts
            dir_name = parts[0] if len(parts) > 1 else "root"
            
            if dir_name not in directories:
                directories[dir_name] = []
            directories[dir_name].append((rel_path, data))
        
        # Add to tree
        for dir_name in sorted(directories.keys()):
            dir_node = self.tree.insert('', 'end', text=dir_name, open=True)
            
            for rel_path, data in directories[dir_name]:
                status = self.format_status(data['status'])
                similarity = f"{data['similarity']*100:.0f}%" if data['similarity'] > 0 else "-"
                replacement_count = len(data.get('replacements', []))
                replacements = f"{replacement_count} rules" if replacement_count > 0 else "-"
                rename_status = "✓" if data.get('renamed', False) else "-"
                
                is_selected = rel_path in self.selected_files
                checkbox = "☑" if is_selected else "☐"
                
                tags = (data['status'],)
                if data.get('renamed'):
                    tags = tags + ('renamed',)
                
                # Show new name if renamed
                display_name = Path(data.get('new_rel_path', rel_path)).name if data.get('renamed') else Path(rel_path).name
                
                item_id = self.tree.insert(
                    dir_node,
                    'end',
                    text=display_name,
                    values=(checkbox, status, similarity, replacements, rename_status),
                    tags=tags
                )
                
                self.checkboxes[item_id] = rel_path
    
    def format_status(self, status: str) -> str:
        """Format status for display."""
        status_map = {
            'new': 'New File',
            'identical': 'Identical',
            'minimal_changes': 'Minimal',
            'minor_changes': 'Minor',
            'major_changes': 'Major',
            'missing_source': 'Missing',
            'error': 'Error'
        }
        return status_map.get(status, status)
    
    def apply_filter(self):
        """Apply filters to file list."""
        filter_text = self.filter_var.get().lower()
        show_changes = self.show_only_changes.get()
        show_selected = self.show_only_selected.get()
        show_replacements = self.show_replacements.get()
        
        self.tree.delete(*self.tree.get_children())
        self.checkboxes.clear()
        
        filtered_data = {}
        for path, data in self.files_data.items():
            if filter_text and filter_text not in path.lower():
                continue
            
            if show_changes and data['status'] == 'identical':
                continue
            
            if show_selected and path not in self.selected_files:
                continue
            
            if show_replacements and not data.get('replacements'):
                continue
            
            filtered_data[path] = data
        
        if not filtered_data:
            self.status_label.config(text="No files match filters")
            return
        
        original_data = self.files_data
        self.files_data = filtered_data
        self.populate_tree()
        self.files_data = original_data
    
    def on_file_select(self, event):
        """Handle file selection."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        parent = self.tree.parent(item)
        if not parent or item not in self.checkboxes:
            return
        
        rel_path = self.checkboxes[item]
        self.show_file_details(rel_path)
    
    def show_file_details(self, rel_path: str):
        """Show details for selected file."""
        data = self.files_data[rel_path]
        
        self.details_text.delete('1.0', 'end')
        self.diff_text.delete('1.0', 'end')
        
        # Details
        details = f"""File: {rel_path}
Status: {self.format_status(data['status'])}
Similarity: {data['similarity']*100:.1f}%
Source: {data['source_path']}
Target: {data['target_path']}

"""
        
        # Show file rename info
        if data.get('renamed'):
            details += f"File Rename:\n"
            details += f"  Old: {Path(rel_path).name}\n"
            details += f"  New: {Path(data['new_rel_path']).name}\n"
            if data.get('will_update_imports'):
                details += f"  Will update imports in this file\n"
            details += "\n"
        
        # Show import replacements
        if data.get('replacements'):
            details += "Import Replacements:\n"
            for old_imp, new_imp in data['replacements']:
                details += f"  {old_imp}\n    → {new_imp}\n"
            details += "\n"
        
        self.details_text.insert('1.0', details)
        
        # Show diff
        if data['status'] in ['minor_changes', 'minimal_changes', 'major_changes']:
            if data['status'] == 'major_changes':
                warning = "⚠️  WARNING: Major changes (< 30% similarity)\n" + "=" * 60 + "\n\n"
                self.diff_text.insert('1.0', warning, 'header')
            
            # Show replacement info
            if data.get('replacements'):
                repl_info = "🔄 Import replacements will be applied:\n"
                for old_imp, new_imp in data['replacements'][:3]:
                    repl_info += f"  • {old_imp} → {new_imp}\n"
                if len(data['replacements']) > 3:
                    repl_info += f"  ... and {len(data['replacements']) - 3} more\n"
                repl_info += "\n"
                self.diff_text.insert('end', repl_info, 'replacement')
            
            for line in data['diff_lines'][:200]:
                if line.startswith('+++') or line.startswith('---'):
                    self.diff_text.insert('end', line + '\n', 'header')
                elif line.startswith('+'):
                    self.diff_text.insert('end', line + '\n', 'add')
                elif line.startswith('-'):
                    self.diff_text.insert('end', line + '\n', 'remove')
                else:
                    self.diff_text.insert('end', line + '\n')
            
            if len(data['diff_lines']) > 200:
                self.diff_text.insert('end', f"\n... ({len(data['diff_lines']) - 200} more lines)\n", 'header')
        
        elif data['status'] == 'new':
            msg = "This is a new file.\n"
            if data.get('replacements'):
                msg += "\nImport replacements will be applied during deployment.\n"
            self.diff_text.insert('1.0', msg)
        elif data['status'] == 'identical':
            self.diff_text.insert('1.0', "Files are identical.\n")
    
    def on_tree_click(self, event):
        """Handle tree click."""
        region = self.tree.identify_region(event.x, event.y)
        if region == 'cell':
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            
            if column == '#1' and item in self.checkboxes:
                self.toggle_item_selection(item)
    
    def toggle_selection(self, event):
        """Toggle selection with spacebar."""
        for item in self.tree.selection():
            if item in self.checkboxes:
                self.toggle_item_selection(item)
    
    def toggle_item_selection(self, item_id):
        """Toggle item selection state."""
        if item_id not in self.checkboxes:
            return
        
        rel_path = self.checkboxes[item_id]
        
        if rel_path in self.selected_files:
            self.selected_files.remove(rel_path)
            checkbox = "☐"
        else:
            self.selected_files.add(rel_path)
            checkbox = "☑"
        
        current_values = list(self.tree.item(item_id, 'values'))
        current_values[0] = checkbox
        self.tree.item(item_id, values=current_values)
        
        self.update_selection_display()
    
    def toggle_all_visible(self):
        """Toggle all visible files."""
        visible_items = []
        for item in self.tree.get_children():
            for child in self.tree.get_children(item):
                if child in self.checkboxes:
                    visible_items.append(child)
        
        if not visible_items:
            return
        
        all_selected = all(self.checkboxes[item] in self.selected_files for item in visible_items)
        
        for item in visible_items:
            rel_path = self.checkboxes[item]
            if all_selected:
                if rel_path in self.selected_files:
                    self.selected_files.remove(rel_path)
                checkbox = "☐"
            else:
                self.selected_files.add(rel_path)
                checkbox = "☑"
            
            current_values = list(self.tree.item(item, 'values'))
            current_values[0] = checkbox
            self.tree.item(item, values=current_values)
        
        self.update_selection_display()
    
    def select_all(self):
        """Select all files."""
        self.selected_files = set(self.files_data.keys())
        self.apply_filter()
        self.update_selection_display()
    
    def deselect_all(self):
        """Deselect all files."""
        self.selected_files.clear()
        self.apply_filter()
        self.update_selection_display()
    
    def update_selection_display(self):
        """Update status label."""
        count = len(self.selected_files)
        replacement_files = sum(1 for f in self.selected_files if self.files_data[f].get('replacements'))
        msg = f"Selected {count} file(s)"
        if replacement_files > 0:
            msg += f" ({replacement_files} with import replacements)"
        self.status_label.config(text=msg)
    
    def export_selection(self):
        """Export selected files list."""
        if not self.selected_files:
            messagebox.showwarning("No Selection", "Please select files first.")
            return
        
        export_path = filedialog.asksaveasfilename(
            title="Export Selection",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt")]
        )
        
        if export_path:
            with open(export_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['File', 'Status', 'Similarity', 'Replacements'])
                
                for rel_path in sorted(self.selected_files):
                    data = self.files_data[rel_path]
                    writer.writerow([
                        rel_path,
                        data['status'],
                        f"{data['similarity']*100:.1f}%",
                        len(data.get('replacements', []))
                    ])
            
            messagebox.showinfo("Exported", f"Selection exported to:\n{export_path}")
    
    def deploy_selected(self):
        """Deploy selected files with comprehensive tracking."""
        if not self.selected_files:
            messagebox.showwarning("No Selection", "Please select files to deploy.")
            return
        
        # Check for major changes
        major_changes = [f for f in self.selected_files if self.files_data[f]['status'] == 'major_changes']
        
        if major_changes:
            msg = f"WARNING: {len(major_changes)} file(s) have major changes (< 30% similarity)\n\n"
            msg += "Do you want to continue?"
            if not messagebox.askyesno("Major Changes", msg):
                return
        
        # Show deployment summary
        replacement_count = sum(len(self.files_data[f].get('replacements', [])) for f in self.selected_files)
        renamed_count = sum(1 for f in self.selected_files if self.files_data[f].get('renamed'))
        
        msg = f"Deploy {len(self.selected_files)} file(s) to:\n{self.target_base}\n\n"
        if replacement_count > 0:
            msg += f"Import replacements: {sum(1 for f in self.selected_files if self.files_data[f].get('replacements'))} file(s)\n"
        if renamed_count > 0:
            msg += f"File renames: {renamed_count} file(s)\n"
        msg += "\nA backup will be created before deployment."
        
        if not messagebox.askyesno("Confirm Deployment", msg):
            return
        
        # Create backup and report tracking
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_base / timestamp
        
        deployment_report = {
            'timestamp': timestamp,
            'product': self.product.get(),
            'source_type': self.source_type.get(),
            'deployment_type': self.deployment_type.get(),
            'target_base': str(self.target_base),
            'total_files_scanned': len(self.files_data),
            'product_filtered': len([f for f, d in self.files_data.items() if f not in self.selected_files]),
            'deployed': [],
            'errors': [],
            'skipped_files': []
        }
        
        # Track skipped files (product-filtered)
        all_possible_files = set(self.files_data.keys())
        for file_path in all_possible_files:
            if file_path not in self.selected_files:
                data = self.files_data[file_path]
                deployment_report['skipped_files'].append({
                    'file': file_path,
                    'reason': 'Not selected',
                    'status': data['status'],
                    'renamed': data.get('renamed', False),
                    'new_name': Path(data.get('new_rel_path', file_path)).name if data.get('renamed') else ''
                })
        
        deployed = 0
        
        for rel_path in self.selected_files:
            data = self.files_data[rel_path]
            source = data['source_path']
            target = data['target_path']
            
            file_report = {
                'source_file': str(rel_path),
                'target_file': str(data.get('new_rel_path', rel_path)),
                'renamed': data.get('renamed', False),
                'old_name': Path(rel_path).name,
                'new_name': Path(data.get('new_rel_path', rel_path)).name,
                'status': data['status'],
                'similarity': f"{data['similarity']*100:.1f}%",
                'import_replacements': [],
                'filename_import_updates': [],
                'lines_with_import_changes': [],
                'lines_with_rename_changes': [],
                'success': False,
                'error': None
            }
            
            try:
                # Backup existing
                if target.exists():
                    backup_file = backup_dir / rel_path
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, backup_file)
                
                # Prepare content
                target.parent.mkdir(parents=True, exist_ok=True)
                
                if source.suffix == '.py':
                    # Read source
                    with open(source, 'r', encoding='utf-8', errors='ignore') as f:
                        original_content = f.read()
                    
                    modified_content = original_content
                    original_lines = original_content.splitlines()
                    
                    # Apply import replacements
                    if self.import_replacer.replacements:
                        modified_content, repl_count = self.import_replacer.replace_in_file(source)
                        if repl_count > 0:
                            file_report['import_replacements'] = data.get('replacements', [])
                            # Find lines that changed
                            modified_lines = modified_content.splitlines()
                            for i, (orig, mod) in enumerate(zip(original_lines, modified_lines), 1):
                                if orig != mod:
                                    file_report['lines_with_import_changes'].append({
                                        'line': i,
                                        'old': orig.strip(),
                                        'new': mod.strip()
                                    })
                    
                    # Apply file rename import updates
                    if data.get('will_update_imports') and self.file_renamer.name_mappings:
                        before_rename = modified_content
                        modified_content, rename_changes = self.file_renamer.update_imports_in_content(modified_content)
                        if rename_changes:
                            file_report['filename_import_updates'] = rename_changes
                            # Find lines that changed
                            before_lines = before_rename.splitlines()
                            after_lines = modified_content.splitlines()
                            for i, (before, after) in enumerate(zip(before_lines, after_lines), 1):
                                if before != after:
                                    file_report['lines_with_rename_changes'].append({
                                        'line': i,
                                        'old': before.strip(),
                                        'new': after.strip()
                                    })
                    
                    # Write modified content
                    with open(target, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                else:
                    # Direct copy for non-Python files
                    shutil.copy2(source, target)
                
                file_report['success'] = True
                deployed += 1
                
            except Exception as e:
                file_report['error'] = str(e)
                deployment_report['errors'].append(file_report)
                continue
            
            deployment_report['deployed'].append(file_report)
        
        # Save report
        self.last_deployment_report = deployment_report
        report_file = DEVTOOLS_PATH / f"deployment_report_{timestamp}.csv"
        self.save_deployment_report(report_file)
        
        # Enable report button
        try:
            self.report_button.config(state='normal')
        except:
            pass
        
        # Results
        if deployment_report['errors']:
            msg = f"Deployed {deployed} files with {len(deployment_report['errors'])} errors\n\n"
            msg += f"Report saved: {report_file.name}"
            messagebox.showwarning("Completed with Errors", msg)
        else:
            msg = f"Successfully deployed {deployed} file(s)!\n\n"
            if replacement_count > 0:
                msg += f"Import replacements: {replacement_count} rule(s)\n"
            if renamed_count > 0:
                msg += f"File renames: {renamed_count}\n"
            msg += f"\nReport: {report_file.name}\n"
            msg += f"Backup: {backup_dir}"
            messagebox.showinfo("Success", msg)
        
        # Refresh
        self.selected_files.clear()
        self.scan_files()
    
    def save_current_config(self):
        """Save current configuration for the selected product."""
        product = self.product.get()
        
        # Update config for current product
        self.config['product_configs'][product] = {
            'source_type': self.source_type.get(),
            'deployment_type': self.deployment_type.get(),
            'target_base': str(self.target_base) if self.target_base else "",
            'replacement_csv': str(self.replacement_csv) if self.replacement_csv else "",
            'selected_files': list(self.selected_files)
        }
        
        # Save to file
        if save_config(self.config):
            self.status_label.config(text=f"Configuration saved for {product}")
        else:
            messagebox.showwarning("Save Failed", "Could not save configuration")
    
    def load_product_config(self):
        """Load configuration for the selected product."""
        product = self.product.get()
        
        if product not in self.config['product_configs']:
            return
        
        prod_config = self.config['product_configs'][product]
        
        # Load source type
        if prod_config.get('source_type'):
            self.source_type.set(prod_config['source_type'])
            self.on_source_change()
        
        # Load deployment type
        if prod_config.get('deployment_type'):
            self.deployment_type.set(prod_config['deployment_type'])
        
        # Load target
        if prod_config.get('target_base'):
            target_path = Path(prod_config['target_base'])
            if target_path.exists():
                self.target_base = target_path
                self.target_label.config(text=str(self.target_base))
        
        # Load CSV
        if prod_config.get('replacement_csv'):
            csv_path = Path(prod_config['replacement_csv'])
            if csv_path.exists():
                if self.import_replacer.load_from_csv(csv_path):
                    self.replacement_csv = csv_path
                    self.csv_label.config(text=csv_path.name)
        
        # Load selected files (will be applied after scan)
        if prod_config.get('selected_files'):
            self.selected_files = set(prod_config['selected_files'])
        
        self.status_label.config(text=f"Loaded configuration for {product}")
    
    def save_deployment_report(self, report_file: Path):
        """Save deployment report to CSV file."""
        if not self.last_deployment_report:
            return
        
        report = self.last_deployment_report
        
        try:
            with open(report_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header information
                writer.writerow(['Deployment Report'])
                writer.writerow(['Timestamp', report['timestamp']])
                writer.writerow(['Product', report['product']])
                writer.writerow(['Source Type', report['source_type']])
                writer.writerow(['Deployment Type', report['deployment_type']])
                writer.writerow(['Target', report['target_base']])
                writer.writerow(['Total Files Scanned', report['total_files_scanned']])
                writer.writerow(['Product Filtered', report['product_filtered']])
                writer.writerow(['Deployed Successfully', len(report['deployed'])])
                writer.writerow(['Errors', len(report['errors'])])
                writer.writerow([])
                
                # Deployed files
                writer.writerow(['DEPLOYED FILES'])
                writer.writerow([
                    'Source File', 'Target File', 'Renamed', 'Old Name', 'New Name',
                    'Status', 'Similarity', 'Import Replacements', 'Filename Import Updates',
                    'Import Change Lines', 'Rename Change Lines'
                ])
                
                for file_data in report['deployed']:
                    import_repls = '; '.join([f"{old} → {new}" for old, new in file_data['import_replacements'][:3]])
                    if len(file_data['import_replacements']) > 3:
                        import_repls += f" (+{len(file_data['import_replacements'])-3} more)"
                    
                    filename_updates = '; '.join([f"{old} → {new}" for old, new in file_data['filename_import_updates'][:3]])
                    if len(file_data['filename_import_updates']) > 3:
                        filename_updates += f" (+{len(file_data['filename_import_updates'])-3} more)"
                    
                    import_lines = ', '.join([str(line['line']) for line in file_data['lines_with_import_changes'][:10]])
                    if len(file_data['lines_with_import_changes']) > 10:
                        import_lines += f" (+{len(file_data['lines_with_import_changes'])-10} more)"
                    
                    rename_lines = ', '.join([str(line['line']) for line in file_data['lines_with_rename_changes'][:10]])
                    if len(file_data['lines_with_rename_changes']) > 10:
                        rename_lines += f" (+{len(file_data['lines_with_rename_changes'])-10} more)"
                    
                    writer.writerow([
                        file_data['source_file'],
                        file_data['target_file'],
                        'Yes' if file_data['renamed'] else 'No',
                        file_data['old_name'],
                        file_data['new_name'],
                        file_data['status'],
                        file_data['similarity'],
                        import_repls or '-',
                        filename_updates or '-',
                        import_lines or '-',
                        rename_lines or '-'
                    ])
                
                # Detailed line changes
                writer.writerow([])
                writer.writerow(['DETAILED LINE CHANGES'])
                writer.writerow(['File', 'Line', 'Change Type', 'Old Content', 'New Content'])
                
                for file_data in report['deployed']:
                    for line_change in file_data['lines_with_import_changes']:
                        writer.writerow([
                            file_data['source_file'],
                            line_change['line'],
                            'Import Replacement',
                            line_change['old'],
                            line_change['new']
                        ])
                    
                    for line_change in file_data['lines_with_rename_changes']:
                        writer.writerow([
                            file_data['source_file'],
                            line_change['line'],
                            'Filename Import Update',
                            line_change['old'],
                            line_change['new']
                        ])
                
                # Skipped files
                writer.writerow([])
                writer.writerow(['SKIPPED FILES'])
                writer.writerow(['File', 'Reason', 'Status', 'Renamed', 'New Name'])
                
                for skipped in report['skipped_files']:
                    writer.writerow([
                        skipped['file'],
                        skipped['reason'],
                        skipped['status'],
                        'Yes' if skipped['renamed'] else 'No',
                        skipped['new_name'] or '-'
                    ])
                
                # Errors
                if report['errors']:
                    writer.writerow([])
                    writer.writerow(['ERRORS'])
                    writer.writerow(['File', 'Error'])
                    
                    for error_data in report['errors']:
                        writer.writerow([
                            error_data['source_file'],
                            error_data['error']
                        ])
            
            return True
        
        except Exception as e:
            print(f"Error saving deployment report: {e}")
            return False
    
    def view_last_report(self):
        """View the last deployment report."""
        if not self.last_deployment_report:
            messagebox.showinfo("No Report", "No deployment report available.")
            return
        
        report = self.last_deployment_report
        
        # Create a new window to show report
        report_window = tk.Toplevel(self.root)
        report_window.title(f"Deployment Report - {report['timestamp']}")
        report_window.geometry("900x700")
        
        # Add text widget with scrollbar
        text_frame = ttk.Frame(report_window)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        text_widget = tk.Text(text_frame, wrap='word', yscrollcommand=scrollbar.set, font=('Courier', 9))
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Build report text
        report_text = f"""DEPLOYMENT REPORT
{'='*80}
Timestamp: {report['timestamp']}
Product: {report['product']}
Source: {report['source_type']}
Deployment Type: {report['deployment_type']}
Target: {report['target_base']}

SUMMARY
{'='*80}
Total Files Scanned: {report['total_files_scanned']}
Product Filtered: {report['product_filtered']}
Deployed Successfully: {len(report['deployed'])}
Errors: {len(report['errors'])}

DEPLOYED FILES ({len(report['deployed'])})
{'='*80}
"""
        
        for i, file_data in enumerate(report['deployed'], 1):
            report_text += f"\n{i}. {file_data['source_file']}\n"
            if file_data['renamed']:
                report_text += f"   Renamed: {file_data['old_name']} → {file_data['new_name']}\n"
            report_text += f"   Status: {file_data['status']} (Similarity: {file_data['similarity']})\n"
            
            if file_data['import_replacements']:
                report_text += f"   Import Replacements: {len(file_data['import_replacements'])}\n"
                for old, new in file_data['import_replacements'][:2]:
                    report_text += f"     • {old} → {new}\n"
            
            if file_data['filename_import_updates']:
                report_text += f"   Filename Import Updates: {len(file_data['filename_import_updates'])}\n"
                for old, new in file_data['filename_import_updates'][:2]:
                    report_text += f"     • {old} → {new}\n"
            
            if file_data['lines_with_import_changes']:
                report_text += f"   Import Changes: Lines {', '.join([str(l['line']) for l in file_data['lines_with_import_changes'][:5]])}\n"
            
            if file_data['lines_with_rename_changes']:
                report_text += f"   Rename Changes: Lines {', '.join([str(l['line']) for l in file_data['lines_with_rename_changes'][:5]])}\n"
        
        if report['errors']:
            report_text += f"\n\nERRORS ({len(report['errors'])})\n{'='*80}\n"
            for error_data in report['errors']:
                report_text += f"\n• {error_data['source_file']}\n"
                report_text += f"  Error: {error_data['error']}\n"
        
        report_text += f"\n\nSKIPPED FILES ({len(report['skipped_files'])})\n{'='*80}\n"
        for skipped in report['skipped_files'][:20]:
            report_text += f"• {skipped['file']} - {skipped['reason']}\n"
        
        if len(report['skipped_files']) > 20:
            report_text += f"... and {len(report['skipped_files'])-20} more\n"
        
        text_widget.insert('1.0', report_text)
        text_widget.config(state='disabled')
        
        # Add close button
        ttk.Button(
            report_window,
            text="Close",
            command=report_window.destroy
        ).pack(pady=5)


def main():
    """Main entry point."""
    root = tk.Tk()
    app = UniversalDeploymentGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
