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
import ast
import subprocess
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from pathlib import Path
import difflib
import shutil
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
import hashlib
import re
import fnmatch

# ── CustomTkinter Dark Theme (VS Code palette) ────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C_BG       = "#1e1e1e"   # editor background
C_PANEL    = "#252526"   # sidebar / panel background
C_PANEL2   = "#2d2d2d"   # slightly lighter panel
C_INPUT    = "#3c3c3c"   # input field fill
C_BORDER   = "#454545"   # border / separator
C_TEXT     = "#d4d4d4"   # primary text
C_TEXT_DIM = "#858585"   # secondary / hint text
C_ACCENT   = "#0078d4"   # VS Code blue accent
C_HOVER    = "#1a8ad4"   # hover accent
C_SUCCESS  = "#4ec9b0"   # teal green
C_WARNING  = "#ce9178"   # orange
C_ERROR    = "#f44747"   # red
C_NEW      = "#569cd6"   # new file (blue)
C_IDENT    = "#608b4e"   # identical (muted green)
C_MINOR    = "#dcdcaa"   # minor changes (yellow)
C_MAJOR    = "#f44747"   # major changes (red)

FONT_MAIN  = ("Segoe UI", 12)
FONT_BOLD  = ("Segoe UI", 12, "bold")
FONT_SMALL = ("Segoe UI", 11)
FONT_MONO  = ("Cascadia Code", 10)
FONT_MONO_B= ("Cascadia Code", 10, "bold")

# Default Paths
WORKSPACE_ROOT = Path(r"C:\Git\Automation")
BASELINE_PATH = WORKSPACE_ROOT / "S2T" / "BASELINE"
BASELINE_DMR_PATH = WORKSPACE_ROOT / "S2T" / "BASELINE_DMR"
PPV_PATH = WORKSPACE_ROOT / "PPV"
DEVTOOLS_PATH = WORKSPACE_ROOT / "DEVTOOLS"
BACKUP_BASE = DEVTOOLS_PATH / "backups"

# Changelog / agent paths
CHANGELOG_PATH = DEVTOOLS_PATH / "CHANGELOG.md"
DEPLOYMENT_CHANGELOG_PATH = DEVTOOLS_PATH / "deployment_changelog.json"
DEPLOY_AGENT_PATH = DEVTOOLS_PATH / "deploy_agent.py"

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


# \u2500\u2500 UI Helper utilities \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _lf(parent, title: str, **grid_kw):
    """Create a ctk 'labeled frame'.  Returns (outer_frame, inner_frame)."""
    outer = ctk.CTkFrame(parent, fg_color=C_PANEL, corner_radius=6,
                         border_width=1, border_color=C_BORDER)
    ctk.CTkLabel(outer, text=f"  {title}", font=FONT_SMALL,
                 text_color=C_TEXT_DIM, anchor="w").pack(
                     side="top", anchor="w", padx=6, pady=(4, 0))
    inner = ctk.CTkFrame(outer, fg_color="transparent")
    inner.pack(fill="both", expand=True, padx=4, pady=(0, 4))
    return outer, inner


def _sep_v(parent) -> ctk.CTkFrame:
    """Thin vertical divider compatible with .pack(side='left', fill='y')."""
    return ctk.CTkFrame(parent, width=1, height=18, fg_color=C_BORDER)


def _apply_dark_tree_style():
    """Style ttk.Treeview + scrollbars to match the CTK dark palette."""
    s = ttk.Style()
    try:
        s.theme_use("clam")
    except Exception:
        pass
    s.configure("Dark.Treeview",
        background=C_PANEL2, foreground=C_TEXT, rowheight=24,
        fieldbackground=C_PANEL2, bordercolor=C_BORDER,
        font=("Segoe UI", 9)
    )
    s.configure("Dark.Treeview.Heading",
        background="#333333", foreground="#cccccc",
        borderwidth=1, font=("Segoe UI", 9, "bold"), relief="flat"
    )
    s.map("Dark.Treeview",
        background=[("selected", "#094771")],
        foreground=[("selected", "#ffffff")]
    )
    s.configure("Dark.Vertical.TScrollbar",
        background=C_PANEL2, troughcolor=C_BG, arrowcolor=C_TEXT_DIM,
        bordercolor=C_BG, lightcolor=C_PANEL2, darkcolor=C_PANEL2
    )
    s.map("Dark.Vertical.TScrollbar", background=[("active", C_INPUT)])
    s.configure("Dark.Horizontal.TScrollbar",
        background=C_PANEL2, troughcolor=C_BG, arrowcolor=C_TEXT_DIM,
        bordercolor=C_BG
    )
    s.map("Dark.Horizontal.TScrollbar", background=[("active", C_INPUT)])


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
    def compare_files(source: Path, target: Path, replacer: Optional[ImportReplacer] = None) -> Dict:
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


class DeploymentManifest:
    """Handles deployment manifest loading and file filtering."""

    def __init__(self):
        self.manifest = None
        self.manifest_path = None
        self.exclude_files = set()
        self.exclude_patterns = []
        self.include_files = set()
        self.include_directories = {}

    def load_from_json(self, manifest_path: Path) -> bool:
        """Load deployment manifest from JSON file."""
        if not manifest_path.exists():
            return False

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                self.manifest = json.load(f)

            self.manifest_path = manifest_path

            # Extract exclusion rules
            self.exclude_files = set(self.manifest.get('exclude_files', []))
            self.exclude_patterns = self.manifest.get('exclude_patterns', [])

            # Extract inclusion rules
            self.include_files = set(self.manifest.get('include_files', []))

            # Process include_directories
            for dir_info in self.manifest.get('include_directories', []):
                path = dir_info.get('path', '')
                self.include_directories[path] = dir_info

            return True

        except Exception as e:
            print(f"Error loading manifest: {e}")
            return False

    def should_include_file(self, rel_path: str) -> Tuple[bool, str]:
        """Check if file should be included based on manifest rules.

        Returns:
            Tuple[bool, str]: (should_include, reason)
        """
        if not self.manifest:
            return True, "No manifest loaded"

        rel_path_str = str(rel_path).replace('\\', '/')
        file_name = Path(rel_path).name

        # Check explicit exclusions
        if file_name in self.exclude_files or rel_path_str in self.exclude_files:
            return False, f"Excluded by manifest: {file_name}"

        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(file_name, pattern):
                return False, f"Matches exclude pattern: {pattern}"

        # Check if it's in an excluded directory pattern
        path_parts = Path(rel_path).parts
        for part in path_parts:
            # Check for common exclusions
            if part in ['__pycache__', '.pytest_cache', '.vscode', '.git']:
                return False, f"System directory: {part}"

        # If we have include rules, check if file matches
        if self.include_files or self.include_directories:
            # Check explicit includes
            if file_name in self.include_files:
                return True, "Explicitly included"

            # Check directory includes
            for dir_path, dir_info in self.include_directories.items():
                if rel_path_str.startswith(dir_path.replace('\\', '/')):
                    # Check directory-specific exclusions
                    dir_excludes = dir_info.get('exclude_patterns', [])
                    for pattern in dir_excludes:
                        if fnmatch.fnmatch(file_name, pattern) or fnmatch.fnmatch(rel_path_str, pattern):
                            return False, f"Excluded by directory rule: {pattern}"

                    if dir_info.get('include_all', False):
                        return True, f"Included by directory: {dir_path}"

            # If we have strict include rules and file doesn't match, exclude it
            if self.include_files and not self.include_directories:
                return False, "Not in include list"

        # Default to include if no rules matched
        return True, "No exclusion rules matched"

    def get_excluded_count(self, file_list: List[str]) -> int:
        """Get count of files that would be excluded."""
        if not self.manifest:
            return 0

        excluded = 0
        for file_path in file_list:
            should_include, _ = self.should_include_file(file_path)
            if not should_include:
                excluded += 1

        return excluded

    def get_manifest_info(self) -> str:
        """Get formatted information about loaded manifest."""
        if not self.manifest:
            return "No manifest loaded"

        info = f"Module: {self.manifest.get('module_name', 'Unknown')}\n"
        info += f"Description: {self.manifest.get('description', 'N/A')}\n"
        info += f"Exclude Files: {len(self.exclude_files)}\n"
        info += f"Exclude Patterns: {len(self.exclude_patterns)}\n"
        info += f"Include Directories: {len(self.include_directories)}\n"

        return info


class CSVGeneratorDialog:
    """Dialog for generating CSV templates (ctk version)."""

    def __init__(self, parent, title: str, product: str, csv_type: str, callback=None):
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("660x520")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(fg_color=C_BG)

        self.product = product
        self.csv_type = csv_type
        self.callback = callback
        self.result_file = None

        self.setup_ui()

    def setup_ui(self):
        """Create the dialog UI."""
        # Header
        ctk.CTkLabel(
            self.dialog,
            text=f"Generate {self.csv_type.title()} CSV for {self.product}",
            font=("Segoe UI", 14, "bold"), text_color=C_TEXT, anchor="w"
        ).pack(fill="x", padx=16, pady=(14, 4))

        # Options frame
        opts_outer, opts = _lf(self.dialog, "Options")
        opts_outer.pack(fill="both", expand=True, padx=12, pady=6)

        # Product prefix
        pf = ctk.CTkFrame(opts, fg_color="transparent")
        pf.pack(fill="x", pady=4)
        ctk.CTkLabel(pf, text="Product Prefix:", width=140, anchor="w",
                     font=FONT_SMALL, text_color=C_TEXT).pack(side="left", padx=4)
        self.prefix_var = tk.StringVar(value=self.product)
        ctk.CTkEntry(pf, textvariable=self.prefix_var, width=100).pack(side="left", padx=4)

        # File name
        ff = ctk.CTkFrame(opts, fg_color="transparent")
        ff.pack(fill="x", pady=4)
        ctk.CTkLabel(ff, text="Output File:", width=140, anchor="w",
                     font=FONT_SMALL, text_color=C_TEXT).pack(side="left", padx=4)
        default_name = (f"{self.csv_type}_replacement_{self.product.lower()}.csv"
                        if self.csv_type == "import"
                        else f"file_rename_{self.product.lower()}.csv")
        self.filename_var = tk.StringVar(value=default_name)
        ctk.CTkEntry(ff, textvariable=self.filename_var, width=300).pack(side="left", padx=4)

        # Output directory
        df = ctk.CTkFrame(opts, fg_color="transparent")
        df.pack(fill="x", pady=4)
        ctk.CTkLabel(df, text="Output Directory:", width=140, anchor="w",
                     font=FONT_SMALL, text_color=C_TEXT).pack(side="left", padx=4)
        self.dir_var = tk.StringVar(value=str(DEVTOOLS_PATH))
        ctk.CTkEntry(df, textvariable=self.dir_var, width=240).pack(side="left", padx=4)
        ctk.CTkButton(df, text="Browse\u2026", width=80,
                      command=self.browse_directory).pack(side="left", padx=4)

        # Info / preview
        info_outer, info_inner = _lf(opts, "Template Contents")
        info_outer.pack(fill="both", expand=True, pady=(8, 4))

        self.info_text = ctk.CTkTextbox(info_inner, font=FONT_SMALL, wrap="word",
                                         fg_color=C_PANEL2)
        self.info_text.pack(fill="both", expand=True, padx=4, pady=4)

        if self.csv_type == "import":
            info_content = (
                f"This will generate a template CSV with common import replacement "
                f"patterns for {self.product}:\n\n"
                f"\u2022 SystemDebug \u2192 {self.product}SystemDebug\n"
                f"\u2022 TestFramework \u2192 {self.product}TestFramework\n"
                f"\u2022 dpmChecks \u2192 {self.product}dpmChecks\n"
                f"\u2022 CoreManipulation \u2192 {self.product}CoreManipulation\n\n"
                "You can edit the generated CSV to add or modify replacement rules."
            )
        else:
            info_content = (
                f"This will generate a template CSV with common file rename "
                f"patterns for {self.product}:\n\n"
                f"\u2022 SystemDebug.py \u2192 {self.product}SystemDebug.py\n"
                f"\u2022 TestFramework.py \u2192 {self.product}TestFramework.py\n"
                f"\u2022 dpmChecks.py \u2192 {self.product}dpmChecks.py\n"
                f"\u2022 CoreManipulation.py \u2192 {self.product}CoreManipulation.py\n\n"
                "Files will be automatically renamed during deployment, and imports will be updated."
            )
        self.info_text.insert("1.0", info_content)
        self.info_text.configure(state="disabled")

        # Buttons
        btn_bar = ctk.CTkFrame(self.dialog, fg_color="transparent")
        btn_bar.pack(fill="x", side="bottom", padx=12, pady=10)
        ctk.CTkButton(btn_bar, text="Cancel", width=90,
                      fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self.dialog.destroy).pack(side="right", padx=4)
        ctk.CTkButton(btn_bar, text="Generate", width=90,
                      command=self.generate_csv).pack(side="right", padx=4)

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
                'new_import': f'from DebugFramework import {prefix}SystemDebug',
                'description': f'Product-specific SystemDebug alias',
                'enabled': 'yes'
            },
            {
                'old_import': 'import DebugFramework.SystemDebug',
                'new_import': f'import DebugFramework.{prefix}SystemDebug',
                'description': f'Product-specific SystemDebug module',
                'enabled': 'yes'
            },
            {
                'old_import': 'from S2T.dpmChecks import',
                'new_import': f'from S2T.dpmChecks{prefix} import',
                'description': f'Product-specific dpmChecks',
                'enabled': 'yes'
            },
            {
                'old_import': 'from S2T import CoreManipulation',
                'new_import': f'from S2T import {prefix}CoreManipulation',
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
                'old_import': 'users.gaespino.dev.DebugFramework.',
                'new_import': f'users.gaespino.DebugFramework.',
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
                'old_file': 'DebugFramework/MaskEditor.py',
                'new_file': f'DebugFramework/{prefix}MaskEditor.py',
                'old_name': 'MaskEditor.py',
                'new_name': f'{prefix}MaskEditor.py',
                'description': f'Rename MaskEditor to {prefix}MaskEditor',
                'update_imports': 'yes',
                'enabled': 'yes'
            },
            {
                'old_file': 'S2T/dpmChecks.py',
                'new_file': f'S2T/dpmChecks{prefix}.py',
                'old_name': 'dpmChecks.py',
                'new_name': f'dpmChecks{prefix}.py',
                'description': f'Rename dpmChecks to dpmChecks{prefix}',
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
            {
                'old_file': 'S2T/DffDataCollector.py',
                'new_file': f'S2T/{prefix}DffDataCollector.py',
                'old_name': 'DffDataCollector.py',
                'new_name': f'{prefix}DffDataCollector.py',
                'description': f'Rename DffDataCollector to {prefix}DffDataCollector',
                'update_imports': 'yes',
                'enabled': 'yes'
            },
            {
                'old_file': 'S2T/GetTesterCurves.py',
                'new_file': f'S2T/{prefix}GetTesterCurves.py',
                'old_name': 'GetTesterCurves.py',
                'new_name': f'{prefix}GetTesterCurves.py',
                'description': f'Rename GetTesterCurves to {prefix}GetTesterCurves',
                'update_imports': 'yes',
                'enabled': 'yes'
            },
            {
                'old_file': 'S2T/SetTesterRegs.py',
                'new_file': f'S2T/{prefix}SetTesterRegs.py',
                'old_name': 'SetTesterRegs.py',
                'new_name': f'{prefix}SetTesterRegs.py',
                'description': f'Rename SetTesterRegs to {prefix}SetTesterRegs',
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


class ValidationAgentDialog:
    """Modal dialog for running deploy_agent.py validation (ctk version)."""

    def __init__(self, parent, product: str, target_base):
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(f"Validate & Review \u2014 {product}")
        self.dialog.geometry("960x700")
        self.dialog.transient(parent)
        self.dialog.resizable(True, True)
        self.dialog.configure(fg_color=C_BG)

        self.product = product
        self.target_base = target_base
        self._process = None
        self._setup_ui()

    def _setup_ui(self):
        # Options panel
        opts_outer, opts = _lf(self.dialog, "Validation Options")
        opts_outer.pack(fill="x", padx=10, pady=(10, 4))

        r1 = ctk.CTkFrame(opts, fg_color="transparent")
        r1.pack(fill="x", pady=3)
        self.do_validate = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(r1, text="Syntax check (ast)", font=FONT_MAIN,
                        variable=self.do_validate).pack(side="left", padx=8)
        self.do_lint = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(r1, text="Linting (flake8/pyflakes)", font=FONT_MAIN,
                        variable=self.do_lint).pack(side="left", padx=8)
        self.do_test = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(r1, text="Quick tests (pytest)", font=FONT_MAIN,
                        variable=self.do_test).pack(side="left", padx=8)
        self.do_pr = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(r1, text="Create Draft PR (gh CLI)", font=FONT_MAIN,
                        variable=self.do_pr).pack(side="left", padx=8)

        r2 = ctk.CTkFrame(opts, fg_color="transparent")
        r2.pack(fill="x", pady=3)
        ctk.CTkLabel(r2, text="PR Title:", width=90, anchor="w",
                     font=FONT_SMALL, text_color=C_TEXT).pack(side="left", padx=4)
        self.pr_title_var = tk.StringVar(
            value=f"Deploy {self.product} \u2014 {datetime.now().strftime('%Y-%m-%d')}"
        )
        ctk.CTkEntry(r2, textvariable=self.pr_title_var, width=500).pack(side="left", padx=4)

        r3 = ctk.CTkFrame(opts, fg_color="transparent")
        r3.pack(fill="x", pady=3)
        ctk.CTkLabel(r3, text="Target dir:", width=90, anchor="w",
                     font=FONT_SMALL, text_color=C_TEXT).pack(side="left", padx=4)
        self.target_var = tk.StringVar(
            value=str(self.target_base) if self.target_base else ""
        )
        ctk.CTkEntry(r3, textvariable=self.target_var, width=440).pack(side="left", padx=4)
        ctk.CTkButton(r3, text="Browse\u2026", width=80,
                      command=self._browse_target).pack(side="left", padx=4)

        # Output textbox
        out_outer, out_inner = _lf(self.dialog, "Output")
        out_outer.pack(fill="both", expand=True, padx=10, pady=4)

        self.out_text = ctk.CTkTextbox(out_inner, font=FONT_MONO,
                                        fg_color=C_PANEL2, state="disabled", wrap="word")
        self.out_text.pack(fill="both", expand=True, padx=4, pady=4)

        # Color tags via underlying tk.Text (Step 15: verified via ._textbox)
        self.out_text._textbox.tag_config("ok",      foreground="#4ec9b0")
        self.out_text._textbox.tag_config("error",   foreground="#f44747")
        self.out_text._textbox.tag_config("heading", foreground="#569cd6",
                                           font=("Cascadia Code", 9, "bold"))
        self.out_text._textbox.tag_config("warn",    foreground="#ce9178")

        # Buttons
        btn_bar = ctk.CTkFrame(self.dialog, fg_color="transparent")
        btn_bar.pack(fill="x", side="bottom", padx=10, pady=8)
        ctk.CTkButton(btn_bar, text="Run Validation",
                      command=self._run).pack(side="left", padx=4)
        ctk.CTkButton(btn_bar, text="Stop",
                      fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self._stop).pack(side="left", padx=4)
        ctk.CTkButton(btn_bar, text="Save Report\u2026",
                      fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self._save_output).pack(side="left", padx=4)
        ctk.CTkButton(btn_bar, text="Close",
                      fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self.dialog.destroy).pack(side="right", padx=4)

    def _browse_target(self):
        d = filedialog.askdirectory(
            title="Select Target Directory",
            initialdir=self.target_var.get() or str(WORKSPACE_ROOT)
        )
        if d:
            self.target_var.set(d)

    def _append(self, text, tag=None):
        tb = self.out_text._textbox
        tb.config(state="normal")
        if tag:
            tb.insert("end", text, tag)
        else:
            tb.insert("end", text)
        tb.see("end")
        tb.config(state="disabled")
        try:
            self.dialog.update_idletasks()
        except Exception:
            pass

    def _run(self):
        if not DEPLOY_AGENT_PATH.exists():
            self._append(
                f"ERROR: deploy_agent.py not found at:\n  {DEPLOY_AGENT_PATH}\n"
                "Please ensure it exists in DEVTOOLS/.\n", "error"
            )
            return

        tb = self.out_text._textbox
        tb.config(state="normal")
        tb.delete("1.0", "end")
        tb.config(state="disabled")

        cmd = [sys.executable, str(DEPLOY_AGENT_PATH)]
        if self.do_validate.get(): cmd.append("--validate")
        if self.do_lint.get():     cmd.append("--lint")
        if self.do_test.get():     cmd += ["--test", "--quick"]
        if self.do_pr.get():       cmd += ["--pr", "--pr-title", self.pr_title_var.get()]
        cmd += ["--product", self.product]
        if self.target_var.get():  cmd += ["--target", self.target_var.get()]

        self._append(f"$ {' '.join(cmd)}\n", "heading")
        self._append("\u2500" * 72 + "\n")

        def _worker():
            try:
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(DEVTOOLS_PATH)
                )
                for line in self._process.stdout:
                    if any(x in line for x in ['ERROR', 'Error:', 'FAILED', '\u2717', 'Syntax error']):
                        tag = 'error'
                    elif any(x in line for x in ['WARNING', 'W ', 'flake8', 'warning']):
                        tag = 'warn'
                    elif any(x in line for x in ['\u2713', 'OK', 'passed', 'success', 'PASSED']):
                        tag = 'ok'
                    elif line.startswith('==') or line.startswith('--'):
                        tag = 'heading'
                    else:
                        tag = None
                    self.dialog.after(0, self._append, line, tag)
                self._process.wait()
                rc = self._process.returncode
                final = f"\n{'\u2500'*72}\nFinished \u2014 exit code {rc}\n"
                self.dialog.after(0, self._append, final, 'ok' if rc == 0 else 'error')
            except Exception as e:
                self.dialog.after(0, self._append, f"\nFailed to launch agent:\n{e}\n", 'error')

        threading.Thread(target=_worker, daemon=True).start()

    def _stop(self):
        if self._process:
            try:
                self._process.terminate()
                self._append("\n[Process terminated by user]\n", 'warn')
            except Exception:
                pass

    def _save_output(self):
        path = filedialog.asksaveasfilename(
            title="Save Validation Report",
            initialdir=DEVTOOLS_PATH,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            content = self.out_text._textbox.get("1.0", "end")
            Path(path).write_text(content, encoding="utf-8")
            messagebox.showinfo("Saved", f"Report saved:\n{Path(path).name}",
                                parent=self.dialog)


class UniversalDeploymentGUI:
    """Main GUI for universal deployment tool (ctk dark-theme version)."""

    def __init__(self, root):
        self.root = root
        self.root.title("Universal Central Deployment Tool")
        self.root.geometry("1400x900")
        self.root.minsize(1100, 700)
        self.root.resizable(True, True)
        self.root.configure(fg_color=C_BG)

        # State
        self.product = tk.StringVar(value="GNR")
        self.source_type = tk.StringVar(value="BASELINE")
        self.deployment_type = tk.StringVar(value="DebugFramework")
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

        # Deployment manifest
        self.deployment_manifest = DeploymentManifest()
        self.manifest_file = None

        # Config management
        self.config = CONFIG
        self.config_auto_save = tk.BooleanVar(value=True)
        self.auto_csv_on_product = tk.BooleanVar(value=True)
        self.auto_manifest_on_deploy = tk.BooleanVar(value=True)

        # Deployment tracking
        self.last_deployment_report = None
        self.last_report_file_path = None

        # Release notes tracking
        self.current_release_file = None
        self._history_entries = []

        # Collapsible config state
        self._config_collapsed = False

        self.setup_ui()
        self.load_product_config()

    def setup_ui(self):
        """Create the user interface with a tabbed ctk layout."""
        _apply_dark_tree_style()
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.notebook = ctk.CTkTabview(
            self.root,
            fg_color=C_PANEL,
            segmented_button_fg_color=C_PANEL2,
            segmented_button_selected_color=C_ACCENT,
            segmented_button_unselected_color=C_PANEL2,
            segmented_button_selected_hover_color=C_HOVER,
            segmented_button_unselected_hover_color=C_INPUT,
            command=self._on_tab_changed_ctk
        )
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        self.notebook.add("  Deploy  ")
        self.notebook.add("  Reports & Changelog  ")
        self.notebook.add("  Release Notes  ")

        self._setup_deploy_tab(self.notebook.tab("  Deploy  "))
        self._setup_reports_tab(self.notebook.tab("  Reports & Changelog  "))
        self._setup_release_tab(self.notebook.tab("  Release Notes  "))

    def _setup_deploy_tab(self, tab):
        """Build the main Deploy tab (ctk, dark theme)."""
        tab.rowconfigure(2, weight=1)
        tab.columnconfigure(0, weight=1)
        tab.configure(fg_color=C_BG)

        # \u2500\u2500 Collapsible config header bar \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        cfg_hdr = ctk.CTkFrame(tab, fg_color=C_PANEL2, height=30, corner_radius=4)
        cfg_hdr.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 0))
        cfg_hdr.columnconfigure(0, weight=1)
        cfg_hdr.grid_propagate(False)
        ctk.CTkLabel(cfg_hdr, text="  Source Configuration",
                     font=FONT_BOLD, text_color=C_TEXT, anchor="w"
                     ).grid(row=0, column=0, sticky="w", padx=6)
        self._cfg_toggle_btn = ctk.CTkButton(
            cfg_hdr, text="\u25bc  collapse", width=100, height=22,
            fg_color="transparent", hover_color=C_INPUT, text_color=C_TEXT_DIM,
            font=FONT_SMALL, command=self._toggle_config
        )
        self._cfg_toggle_btn.grid(row=0, column=1, padx=6, pady=3)

        # \u2500\u2500 Config body (collapsible) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        self._cfg_body = ctk.CTkFrame(tab, fg_color=C_PANEL, corner_radius=4)
        self._cfg_body.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 4))
        self._cfg_body.columnconfigure(0, weight=1)

        # Row 0: Product + save controls
        r0 = ctk.CTkFrame(self._cfg_body, fg_color="transparent")
        r0.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 2))
        ctk.CTkLabel(r0, text="Product:", font=FONT_BOLD,
                     text_color=C_TEXT, width=72).pack(side="left", padx=2)
        ctk.CTkRadioButton(r0, text="GNR", variable=self.product, value="GNR",
                           font=FONT_MAIN, command=self.on_product_change).pack(side="left", padx=4)
        ctk.CTkRadioButton(r0, text="CWF", variable=self.product, value="CWF",
                           font=FONT_MAIN, command=self.on_product_change).pack(side="left", padx=4)
        ctk.CTkRadioButton(r0, text="DMR", variable=self.product, value="DMR",
                           font=FONT_MAIN, command=self.on_product_change).pack(side="left", padx=4)
        _sep_v(r0).pack(side="left", fill="y", padx=10)
        ctk.CTkCheckBox(r0, text="Auto-save config", font=FONT_MAIN,
                        variable=self.config_auto_save).pack(side="left", padx=4)
        ctk.CTkCheckBox(r0, text="Auto-load CSV", font=FONT_MAIN,
                        variable=self.auto_csv_on_product).pack(side="left", padx=4)
        ctk.CTkButton(r0, text="Save Config", width=90,
                      command=self.save_current_config).pack(side="left", padx=4)

        # Row 1: Source + Deploy type
        r1 = ctk.CTkFrame(self._cfg_body, fg_color="transparent")
        r1.grid(row=1, column=0, sticky="ew", padx=8, pady=2)
        ctk.CTkLabel(r1, text="Source:", font=FONT_BOLD,
                     text_color=C_TEXT, width=72).pack(side="left", padx=2)
        ctk.CTkRadioButton(r1, text="BASELINE", variable=self.source_type,
                           font=FONT_MAIN, value="BASELINE", command=self.on_source_change).pack(side="left", padx=4)
        ctk.CTkRadioButton(r1, text="BASELINE_DMR", variable=self.source_type,
                           font=FONT_MAIN, value="BASELINE_DMR", command=self.on_source_change).pack(side="left", padx=4)
        ctk.CTkRadioButton(r1, text="PPV", variable=self.source_type,
                           font=FONT_MAIN, value="PPV", command=self.on_source_change).pack(side="left", padx=4)
        _sep_v(r1).pack(side="left", fill="y", padx=10)
        ctk.CTkLabel(r1, text="Deploy:", font=FONT_BOLD,
                     text_color=C_TEXT).pack(side="left", padx=2)
        ctk.CTkRadioButton(r1, text="DebugFramework", variable=self.deployment_type,
                           font=FONT_MAIN, value="DebugFramework",
                           command=self.on_deployment_type_change).pack(side="left", padx=4)
        ctk.CTkRadioButton(r1, text="S2T", variable=self.deployment_type,
                           font=FONT_MAIN, value="S2T",
                           command=self.on_deployment_type_change).pack(side="left", padx=4)
        self.ppv_radio = ctk.CTkRadioButton(
            r1, text="PPV", variable=self.deployment_type, value="PPV",
            font=FONT_MAIN, command=self.on_deployment_type_change, state="disabled"
        )
        self.ppv_radio.pack(side="left", padx=4)

        # Row 2: Target
        r2 = ctk.CTkFrame(self._cfg_body, fg_color="transparent")
        r2.grid(row=2, column=0, sticky="ew", padx=8, pady=2)
        ctk.CTkLabel(r2, text="Target:", font=FONT_BOLD,
                     text_color=C_TEXT, width=72).pack(side="left", padx=2)
        self.target_label = ctk.CTkLabel(r2, text="Not selected", font=FONT_MAIN,
                                          text_color=C_TEXT, anchor="w")
        self.target_label.pack(side="left", padx=4, fill="x", expand=True)
        ctk.CTkButton(r2, text="Select Target\u2026", width=110,
                      command=self.select_target).pack(side="left", padx=4)

        # Row 3: Import CSV + Rename CSV
        r3 = ctk.CTkFrame(self._cfg_body, fg_color="transparent")
        r3.grid(row=3, column=0, sticky="ew", padx=8, pady=2)
        ctk.CTkLabel(r3, text="Import CSV:", font=FONT_BOLD,
                     text_color=C_TEXT, width=88).pack(side="left", padx=2)
        self.csv_label = ctk.CTkLabel(r3, text="None", font=FONT_MAIN,
                                       text_color=C_TEXT_DIM, width=200, anchor="w")
        self.csv_label.pack(side="left", padx=2)
        ctk.CTkButton(r3, text="Load\u2026", width=54,
                      command=self.load_replacement_csv).pack(side="left", padx=1)
        ctk.CTkButton(r3, text="Clear", width=48, fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self.clear_replacement_csv).pack(side="left", padx=1)
        ctk.CTkButton(r3, text="Gen\u2026", width=48, fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self.generate_import_csv).pack(side="left", padx=1)
        _sep_v(r3).pack(side="left", fill="y", padx=10)
        ctk.CTkLabel(r3, text="Rename CSV:", font=FONT_BOLD,
                     text_color=C_TEXT, width=92).pack(side="left", padx=2)
        self.rename_csv_label = ctk.CTkLabel(r3, text="None", font=FONT_MAIN,
                                              text_color=C_TEXT_DIM, width=200, anchor="w")
        self.rename_csv_label.pack(side="left", padx=2)
        ctk.CTkButton(r3, text="Load\u2026", width=54,
                      command=self.load_rename_csv).pack(side="left", padx=1)
        ctk.CTkButton(r3, text="Clear", width=48, fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self.clear_rename_csv).pack(side="left", padx=1)
        ctk.CTkButton(r3, text="Gen\u2026", width=48, fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self.generate_rename_csv).pack(side="left", padx=1)

        # Row 4: Manifest
        r4 = ctk.CTkFrame(self._cfg_body, fg_color="transparent")
        r4.grid(row=4, column=0, sticky="ew", padx=8, pady=(2, 8))
        ctk.CTkLabel(r4, text="Manifest:", font=FONT_BOLD,
                     text_color=C_TEXT, width=72).pack(side="left", padx=2)
        self.manifest_label = ctk.CTkLabel(r4, text="None (all files included)",
                                            font=FONT_MAIN, text_color=C_TEXT_DIM, anchor="w")
        self.manifest_label.pack(side="left", padx=4, fill="x", expand=True)
        ctk.CTkButton(r4, text="Load Manifest\u2026", width=112,
                      command=self.load_manifest).pack(side="left", padx=2)
        ctk.CTkButton(r4, text="Clear", width=48, fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self.clear_manifest).pack(side="left", padx=1)
        ctk.CTkButton(r4, text="Auto-Load", width=80,
                      command=self.auto_load_manifest).pack(side="left", padx=2)
        ctk.CTkCheckBox(r4, text="Auto on deploy change", font=FONT_MAIN,
                        variable=self.auto_manifest_on_deploy).pack(side="left", padx=8)

        # \u2500\u2500 Horizontal split (file list | divider | details) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        content = ctk.CTkFrame(tab, fg_color=C_BG)
        content.grid(row=2, column=0, sticky="nsew", padx=4, pady=2)
        content.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=6)
        content.columnconfigure(1, weight=0)
        content.columnconfigure(2, weight=4)

        # \u2500\u2500 Left panel \u2013 file list \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        left_frame = ctk.CTkFrame(content, fg_color=C_BG)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        left_frame.rowconfigure(4, weight=1)
        left_frame.columnconfigure(0, weight=1)

        ctrl = ctk.CTkFrame(left_frame, fg_color="transparent")
        ctrl.grid(row=0, column=0, sticky="ew", pady=3)
        ctk.CTkButton(ctrl, text="Scan Files", width=90,
                      command=self.scan_files).pack(side="left", padx=2)
        ctk.CTkButton(ctrl, text="Select All", width=80,
                      fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self.select_all).pack(side="left", padx=2)
        ctk.CTkButton(ctrl, text="Deselect All", width=88,
                      fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self.deselect_all).pack(side="left", padx=2)

        filt = ctk.CTkFrame(left_frame, fg_color="transparent")
        filt.grid(row=1, column=0, sticky="ew", pady=2)
        ctk.CTkLabel(filt, text="Filter:", font=FONT_SMALL,
                     text_color=C_TEXT).pack(side="left", padx=2)
        self.filter_var = tk.StringVar()
        self.filter_var.trace("w", lambda *args: self.apply_filter())
        ctk.CTkEntry(filt, textvariable=self.filter_var,
                     placeholder_text="Search files\u2026").pack(
                     side="left", fill="x", expand=True, padx=4)

        fopts = ctk.CTkFrame(left_frame, fg_color="transparent")
        fopts.grid(row=2, column=0, sticky="ew", pady=1)
        self.show_only_changes = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(fopts, text="Changes only", variable=self.show_only_changes,
                        command=self.apply_filter, font=FONT_SMALL).pack(side="left", padx=3)
        self.show_only_selected = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(fopts, text="Selected only", variable=self.show_only_selected,
                        command=self.apply_filter, font=FONT_SMALL).pack(side="left", padx=3)
        self.show_replacements = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(fopts, text="Has replacements", variable=self.show_replacements,
                        command=self.apply_filter, font=FONT_SMALL).pack(side="left", padx=3)

        # Scan progress bar (hidden by default)
        self._scan_progress = ctk.CTkProgressBar(left_frame, mode="indeterminate",
                                                   height=4, progress_color=C_ACCENT,
                                                   fg_color=C_PANEL2)
        self._scan_progress.grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        self._scan_progress.grid_remove()

        # Dark-styled Treeview
        tree_frame = ctk.CTkFrame(left_frame, fg_color=C_PANEL2, corner_radius=4)
        tree_frame.grid(row=4, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        vsb = ttk.Scrollbar(tree_frame, style="Dark.Vertical.TScrollbar")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal",
                             style="Dark.Horizontal.TScrollbar")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("selected", "status", "similarity", "replacements", "rename"),
            yscrollcommand=vsb.set, xscrollcommand=hsb.set,
            style="Dark.Treeview"
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        self.tree.heading("#0", text="File")
        self.tree.heading("selected", text="\u2611", command=self.toggle_all_visible)
        self.tree.heading("status", text="Status")
        self.tree.heading("similarity", text="Similar")
        self.tree.heading("replacements", text="Replacements")
        self.tree.heading("rename", text="Rename")

        self.tree.column("#0", width=280, minwidth=150)
        self.tree.column("selected", width=35, minwidth=35, anchor="center")
        self.tree.column("status", width=90, minwidth=70)
        self.tree.column("similarity", width=65, minwidth=55)
        self.tree.column("replacements", width=80, minwidth=70)
        self.tree.column("rename", width=55, minwidth=45, anchor="center")

        self.tree.bind("<<TreeviewSelect>>", self.on_file_select)
        self.tree.bind("<space>", self.toggle_selection)
        self.tree.bind("<Button-1>", self.on_tree_click)

        self.tree.tag_configure("new",           foreground=C_NEW)
        self.tree.tag_configure("identical",     foreground=C_IDENT)
        self.tree.tag_configure("minor_changes", foreground=C_MINOR)
        self.tree.tag_configure("major_changes", foreground=C_MAJOR)
        self.tree.tag_configure("renamed",       font=("Segoe UI", 9, "italic"))

        # Vertical divider
        ctk.CTkFrame(content, width=1, fg_color=C_BORDER
                     ).grid(row=0, column=1, sticky="ns", padx=2)

        # \u2500\u2500 Right panel \u2013 details + diff \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        right_frame = ctk.CTkFrame(content, fg_color=C_BG)
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(2, 0))
        right_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)

        # File details (top section)
        det_outer, det_inner = _lf(right_frame, "File Details")
        det_outer.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        det_inner.columnconfigure(0, weight=1)
        self.details_text = ctk.CTkTextbox(det_inner, height=140, font=FONT_SMALL,
                                            wrap="word", fg_color=C_PANEL2)
        self.details_text.grid(row=0, column=0, sticky="ew", padx=4, pady=4)

        # Changes preview (bottom section) + search bar
        diff_outer, diff_inner = _lf(right_frame, "Changes Preview")
        diff_outer.grid(row=1, column=0, sticky="nsew")
        diff_inner.rowconfigure(1, weight=1)
        diff_inner.columnconfigure(0, weight=1)

        # Diff search bar
        srch = ctk.CTkFrame(diff_inner, fg_color="transparent")
        srch.grid(row=0, column=0, sticky="ew", padx=4, pady=(2, 0))
        ctk.CTkLabel(srch, text="Search:", font=FONT_SMALL,
                     text_color=C_TEXT).pack(side="left", padx=2)
        self._diff_search_var = tk.StringVar()
        self._diff_search_entry = ctk.CTkEntry(
            srch, textvariable=self._diff_search_var,
            placeholder_text="Find in diff\u2026", width=180
        )
        self._diff_search_entry.pack(side="left", padx=4)
        ctk.CTkButton(srch, text="\u25c4", width=28, height=24,
                      fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self._diff_search_prev).pack(side="left", padx=1)
        ctk.CTkButton(srch, text="\u25ba", width=28, height=24,
                      fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self._diff_search_next).pack(side="left", padx=1)
        ctk.CTkButton(srch, text="\u2715", width=24, height=24,
                      fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self._diff_search_clear).pack(side="left", padx=1)
        self._diff_match_label = ctk.CTkLabel(srch, text="", font=FONT_SMALL,
                                               text_color=C_TEXT_DIM)
        self._diff_match_label.pack(side="left", padx=6)
        self._diff_search_var.trace("w", lambda *a: self._diff_search_run())
        self._diff_search_positions: List[str] = []
        self._diff_search_idx: int = -1

        self.diff_text = ctk.CTkTextbox(diff_inner, font=FONT_MONO,
                                         fg_color=C_PANEL2, wrap="none")
        self.diff_text.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        # Color tags on underlying tk.Text widget
        self.diff_text._textbox.tag_config("add",         foreground="#4ec9b0")
        self.diff_text._textbox.tag_config("remove",      foreground="#f44747")
        self.diff_text._textbox.tag_config("header",      foreground="#569cd6",
                                            font=("Cascadia Code", 9, "bold"))
        self.diff_text._textbox.tag_config("replacement", foreground="#c586c0",
                                            font=("Cascadia Code", 9, "bold"))
        self.diff_text._textbox.tag_config("search_hi",   background="#3a3a00",
                                            foreground="#ffff00")

        # \u2500\u2500 Bottom action bar \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        bot = ctk.CTkFrame(tab, fg_color=C_PANEL2, height=48, corner_radius=4)
        bot.grid(row=3, column=0, sticky="ew", padx=4, pady=(2, 4))
        bot.columnconfigure(0, weight=1)
        bot.grid_propagate(False)

        # Deploy progress bar (hidden by default)
        self._deploy_progress = ctk.CTkProgressBar(
            bot, mode="determinate", height=3, width=180,
            progress_color=C_ACCENT, fg_color=C_PANEL2
        )
        self._deploy_progress.set(0)

        self.status_label = ctk.CTkLabel(
            bot,
            text="Select source, deployment type, and target to begin",
            font=FONT_SMALL, text_color=C_TEXT_DIM, anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        btn_f = ctk.CTkFrame(bot, fg_color="transparent")
        btn_f.grid(row=0, column=1, sticky="e", padx=6, pady=6)
        ctk.CTkButton(btn_f, text="Export Selection", width=112,
                      fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self.export_selection).pack(side="left", padx=2)
        ctk.CTkButton(btn_f, text="Validate & Review\u2026", width=134,
                      fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self.run_validation_agent).pack(side="left", padx=2)
        self.report_button = ctk.CTkButton(
            btn_f, text="View Last Report", width=120,
            fg_color=C_INPUT, hover_color=C_BORDER, state="disabled",
            command=self.view_last_report
        )
        self.report_button.pack(side="left", padx=2)
        ctk.CTkButton(btn_f, text="Deploy Selected \u25ba", width=136,
                      command=self.deploy_selected).pack(side="left", padx=2)

    def _setup_reports_tab(self, tab):
        """Build the Reports & Changelog tab (ctk)."""
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        tab.configure(fg_color=C_BG)

        # Left: Deployment history
        hist_outer, hist = _lf(tab, "Deployment History")
        hist_outer.grid(row=0, column=0, sticky="nsew", padx=(5, 3), pady=5)
        hist_outer.rowconfigure(1, weight=1)
        hist_outer.columnconfigure(0, weight=1)
        hist.rowconfigure(1, weight=1)
        hist.columnconfigure(0, weight=1)

        hc = ctk.CTkFrame(hist, fg_color="transparent")
        hc.grid(row=0, column=0, sticky="ew", pady=3)
        ctk.CTkButton(hc, text="Refresh", width=80,
                      command=self.refresh_reports_tab).pack(side="left", padx=3)
        ctk.CTkButton(hc, text="Open CSV Report\u2026", width=130, fg_color=C_INPUT,
                      hover_color=C_BORDER,
                      command=self.open_csv_report).pack(side="left", padx=3)

        # History list (scrollable frame acting as listbox)
        hl_frame = ctk.CTkScrollableFrame(hist, fg_color=C_PANEL2, label_text="")
        hl_frame.grid(row=1, column=0, sticky="nsew")
        hl_frame.columnconfigure(0, weight=1)
        self._history_list_frame = hl_frame
        self._history_btn_refs: list = []

        # Entry detail
        det_outer2, det_inner2 = _lf(hist, "Entry Detail")
        det_outer2.grid(row=2, column=0, sticky="ew", pady=3)
        det_inner2.columnconfigure(0, weight=1)
        self.history_detail_text = ctk.CTkTextbox(
            det_inner2, height=120, font=FONT_MONO,
            fg_color=C_PANEL2, state="disabled", wrap="word"
        )
        self.history_detail_text.grid(row=0, column=0, sticky="ew", padx=4, pady=4)

        # Right: CHANGELOG viewer
        cl_outer, cl_inner = _lf(tab, "CHANGELOG.md")
        cl_outer.grid(row=0, column=1, sticky="nsew", padx=(3, 5), pady=5)
        cl_outer.rowconfigure(1, weight=1)
        cl_outer.columnconfigure(0, weight=1)
        cl_inner.rowconfigure(1, weight=1)
        cl_inner.columnconfigure(0, weight=1)

        cc = ctk.CTkFrame(cl_inner, fg_color="transparent")
        cc.grid(row=0, column=0, sticky="ew", pady=3)
        ctk.CTkButton(cc, text="Refresh", width=80,
                      command=self.view_changelog).pack(side="left", padx=3)
        ctk.CTkButton(cc, text="Open in Editor", width=110, fg_color=C_INPUT,
                      hover_color=C_BORDER,
                      command=self._open_changelog_in_editor).pack(side="left", padx=3)

        self.changelog_text = ctk.CTkTextbox(
            cl_inner, font=FONT_MONO, fg_color=C_PANEL2, state="disabled", wrap="word"
        )
        self.changelog_text.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

    def _setup_release_tab(self, tab):
        """Build the Release Notes tab (ctk)."""
        tab.rowconfigure(1, weight=1)
        tab.columnconfigure(0, weight=1)
        tab.configure(fg_color=C_BG)

        # Controls
        ctrl_outer, ctrl = _lf(tab, "Release Configuration")
        ctrl_outer.grid(row=0, column=0, sticky="ew", padx=5, pady=3)

        r1 = ctk.CTkFrame(ctrl, fg_color="transparent")
        r1.pack(fill="x", pady=2)
        ctk.CTkLabel(r1, text="Version:", font=FONT_BOLD,
                     text_color=C_TEXT, width=90).pack(side="left", padx=3)
        self.release_version_var = tk.StringVar(value="")
        ctk.CTkEntry(r1, textvariable=self.release_version_var, width=90).pack(side="left", padx=3)
        ctk.CTkLabel(r1, text="Start Date (YYYY-MM-DD):", font=FONT_BOLD,
                     text_color=C_TEXT).pack(side="left", padx=(14, 3))
        self.release_start_var = tk.StringVar(value="")
        ctk.CTkEntry(r1, textvariable=self.release_start_var, width=110).pack(side="left", padx=3)
        ctk.CTkLabel(r1, text="End Date:", font=FONT_BOLD,
                     text_color=C_TEXT).pack(side="left", padx=(10, 3))
        self.release_end_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ctk.CTkEntry(r1, textvariable=self.release_end_var, width=110).pack(side="left", padx=3)

        r2 = ctk.CTkFrame(ctrl, fg_color="transparent")
        r2.pack(fill="x", pady=2)
        ctk.CTkButton(r2, text="Generate Draft Release", width=150,
                      command=self.generate_draft_release).pack(side="left", padx=3)
        ctk.CTkButton(r2, text="Load Existing Release\u2026", width=154,
                      fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self.load_existing_release).pack(side="left", padx=3)
        ctk.CTkButton(r2, text="Export HTML", width=100,
                      fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self.export_release_html).pack(side="left", padx=3)
        ctk.CTkButton(r2, text="Create Draft PR", width=110,
                      fg_color=C_INPUT, hover_color=C_BORDER,
                      command=self.create_release_pr).pack(side="left", padx=3)

        r3 = ctk.CTkFrame(ctrl, fg_color="transparent")
        r3.pack(fill="x", pady=2)
        ctk.CTkLabel(r3, text="File:", font=FONT_BOLD,
                     text_color=C_TEXT, width=90).pack(side="left", padx=3)
        self.release_file_label = ctk.CTkLabel(r3, text="No file",
                                                font=FONT_SMALL, text_color=C_TEXT_DIM)
        self.release_file_label.pack(side="left", padx=3)

        # Editor
        ed_outer, ed_inner = _lf(tab, "Release Document Editor")
        ed_outer.grid(row=1, column=0, sticky="nsew", padx=5, pady=3)
        ed_inner.rowconfigure(0, weight=1)
        ed_inner.columnconfigure(0, weight=1)
        self.release_editor = ctk.CTkTextbox(ed_inner, font=FONT_MONO,
                                              fg_color=C_PANEL2, wrap="word")
        self.release_editor.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # Save bar
        save_bar = ctk.CTkFrame(tab, fg_color=C_PANEL2, height=40, corner_radius=4)
        save_bar.grid(row=2, column=0, sticky="ew", padx=5, pady=(2, 4))
        save_bar.columnconfigure(0, weight=1)
        save_bar.grid_propagate(False)
        self.release_status_label = ctk.CTkLabel(save_bar, text="", font=FONT_SMALL,
                                                   text_color=C_TEXT_DIM, anchor="w")
        self.release_status_label.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        ctk.CTkButton(save_bar, text="Save Release Document", width=160,
                      command=self.save_release_document
                      ).grid(row=0, column=1, sticky="e", padx=6, pady=6)

    def on_product_change(self):
        """Handle product change."""
        if self.config_auto_save.get():
            self.save_current_config()
        self.load_product_config()
        if self.auto_csv_on_product.get():
            self._auto_load_csvs_for_product()
        self.clear_scan()

    def on_source_change(self):
        """Handle source type change."""
        source = self.source_type.get()

        if source == "BASELINE":
            self.source_base = BASELINE_PATH
            self.ppv_radio.configure(state="disabled")
            if self.deployment_type.get() == "PPV":
                self.deployment_type.set("DebugFramework")
        elif source == "BASELINE_DMR":
            self.source_base = BASELINE_DMR_PATH
            self.ppv_radio.configure(state="disabled")
            if self.deployment_type.get() == "PPV":
                self.deployment_type.set("DebugFramework")
        else:  # PPV
            self.source_base = PPV_PATH
            self.ppv_radio.configure(state="normal")
            self.deployment_type.set("PPV")

        self.clear_scan()
        if self.config_auto_save.get():
            self.save_current_config()

    def on_deployment_type_change(self):
        """Handle deployment type change."""
        self.clear_scan()
        if self.auto_manifest_on_deploy.get():
            self._auto_load_manifest_silent()
        if self.config_auto_save.get():
            self.save_current_config()

    def _auto_load_csvs_for_product(self):
        """Silently auto-load import/rename CSVs for the current product from DEVTOOLS/."""
        product = self.product.get()
        prod_lower = product.lower()

        import_csv_path = DEVTOOLS_PATH / f"import_replacement_{prod_lower}.csv"
        if import_csv_path.exists():
            if self.import_replacer.load_from_csv(import_csv_path):
                self.replacement_csv = import_csv_path
                self.csv_label.configure(text=import_csv_path.name,
                                         text_color=C_SUCCESS)

        rename_csv_path = DEVTOOLS_PATH / f"file_rename_{prod_lower}.csv"
        if rename_csv_path.exists():
            if self.file_renamer.load_from_csv(rename_csv_path):
                self.rename_csv = rename_csv_path
                self.rename_csv_label.configure(text=rename_csv_path.name,
                                                text_color=C_SUCCESS)

    def _auto_load_manifest_silent(self):
        """Silently auto-load the manifest for the current deployment type."""
        manifest_map = {
            'DebugFramework': 'deployment_manifest_debugframework.json',
            'S2T': 'deployment_manifest_s2t.json',
            'PPV': 'deployment_manifest_ppv.json',
        }
        deployment = self.deployment_type.get()
        filename = manifest_map.get(deployment)
        if not filename:
            return
        manifest_path = DEVTOOLS_PATH / filename
        if not manifest_path.exists():
            return
        if self.deployment_manifest.load_from_json(manifest_path):
            self.manifest_file = manifest_path
            manifest_name = manifest_path.stem.replace('deployment_manifest_', '')
            self.manifest_label.configure(text=manifest_name, text_color=C_SUCCESS)
            if self.files_data:
                self.scan_files()
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
            self.target_label.configure(text=str(self.target_base))
            self.status_label.configure(text="Target selected. Click 'Scan Files' to compare.")
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
                self.csv_label.configure(text=csv_path.name, text_color=C_TEXT)
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
        self.csv_label.configure(text="None", text_color=C_TEXT_DIM)
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
                self.rename_csv_label.configure(text=csv_path.name, text_color=C_TEXT)
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
        self.rename_csv_label.configure(text="None", text_color=C_TEXT_DIM)
        # Rescan if files already loaded
        if self.files_data:
            self.scan_files()

    def load_manifest(self):
        """Load deployment manifest JSON file."""
        initial_dir = DEVTOOLS_PATH
        if self.manifest_file and self.manifest_file.exists():
            initial_dir = self.manifest_file.parent

        manifest_path = filedialog.askopenfilename(
            title="Select Deployment Manifest",
            initialdir=initial_dir,
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )

        if manifest_path:
            manifest_path = Path(manifest_path)
            if self.deployment_manifest.load_from_json(manifest_path):
                self.manifest_file = manifest_path
                manifest_name = manifest_path.stem.replace('deployment_manifest_', '')
                self.manifest_label.configure(text=manifest_name, text_color=C_TEXT)
                info = self.deployment_manifest.get_manifest_info()
                messagebox.showinfo(
                    "Manifest Loaded",
                    f"Loaded deployment manifest:\n{manifest_path.name}\n\n{info}"
                )
                # Rescan if files already loaded
                if self.files_data:
                    self.scan_files()
                if self.config_auto_save.get():
                    self.save_current_config()
            else:
                messagebox.showerror("Error", "Failed to load manifest file")

    def clear_manifest(self):
        """Clear deployment manifest configuration."""
        self.deployment_manifest = DeploymentManifest()
        self.manifest_file = None
        self.manifest_label.configure(text="None (all files included)", text_color=C_TEXT_DIM)
        # Rescan if files already loaded
        if self.files_data:
            self.scan_files()
        if self.config_auto_save.get():
            self.save_current_config()

    def auto_load_manifest(self):
        """Automatically load manifest based on deployment type."""
        deployment = self.deployment_type.get()

        # Determine manifest file based on deployment type
        manifest_map = {
            'DebugFramework': 'deployment_manifest_debugframework.json',
            'S2T': 'deployment_manifest_s2t.json',
            'PPV': 'deployment_manifest_ppv.json'
        }

        manifest_filename = manifest_map.get(deployment)
        if not manifest_filename:
            messagebox.showwarning(
                "No Manifest",
                f"No manifest available for deployment type: {deployment}"
            )
            return

        manifest_path = DEVTOOLS_PATH / manifest_filename

        if not manifest_path.exists():
            messagebox.showwarning(
                "Manifest Not Found",
                f"Manifest file not found:\n{manifest_filename}\n\nPlease create the manifest or use 'Load Manifest...' to select a different file."
            )
            return

        if self.deployment_manifest.load_from_json(manifest_path):
            self.manifest_file = manifest_path
            manifest_name = manifest_path.stem.replace('deployment_manifest_', '')
            self.manifest_label.configure(text=manifest_name)

            info = self.deployment_manifest.get_manifest_info()
            messagebox.showinfo(
                "Auto-Loaded Manifest",
                f"Automatically loaded manifest for {deployment}:\n\n{info}\n\nTest/mock/development files will be automatically excluded."
            )
            # Rescan if files already loaded
            if self.files_data:
                self.scan_files()
            if self.config_auto_save.get():
                self.save_current_config()
        else:
            messagebox.showerror("Error", "Failed to load manifest file")

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
            if self.import_replacer.load_from_csv(csv_file):
                self.replacement_csv = csv_file
                self.csv_label.configure(text=csv_file.name)
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
            if self.file_renamer.load_from_csv(csv_file):
                self.rename_csv = csv_file
                self.rename_csv_label.configure(text=csv_file.name)
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
        self.status_label.configure(text="Configuration changed. Click 'Scan Files' to compare.")

    def should_include_file(self, rel_path: Path) -> bool:
        """Check if file should be included based on product selection."""
        product = self.product.get()
        path_parts = [p.upper() for p in rel_path.parts]

        # Get just the directory parts (excluding the filename)
        dir_parts = [p.lower() for p in rel_path.parts[:-1]]

        # Check if any directory part (not filename) contains product-specific folders
        has_product_folder = any(
            folder.lower() in dir_parts
            for folder in PRODUCT_SPECIFIC_FOLDERS
        )

        if has_product_folder:
            # If it's in a product-specific folder, only include if it matches current product
            # or if it's in the generic product_specific folder with product name in path
            if 'product_specific' in dir_parts:
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

        self.status_label.configure(text="Scanning files…")
        self._scan_progress.grid()
        self._scan_progress.start()
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

        # Scan source files - Python, config files, and data files
        skipped_count = 0
        manifest_excluded = 0
        total_files_seen = 0

        # Define scannable extensions
        scannable_extensions = (
            '.py', '.json', '.ttl', '.ini',  # Original extensions
            '.xlsx', '.csv', '.md', '.txt',   # Data and documentation
            '.xml', '.yaml', '.yml', '.cfg'   # Additional config formats
        )

        for root_dir, dirs, files in os.walk(scan_base):
            # Filter out system directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.vscode', '.git', '.pytest_cache']]

            for file in files:
                total_files_seen += 1
                if file.endswith(scannable_extensions) and not file.startswith('__'):
                    source_path = Path(root_dir) / file
                    rel_path = source_path.relative_to(scan_base)

                    # Check manifest filtering first
                    if self.deployment_manifest.manifest:
                        should_include_manifest, reason = self.deployment_manifest.should_include_file(str(rel_path))
                        if not should_include_manifest:
                            manifest_excluded += 1
                            # Uncomment for debugging:
                            # print(f"Manifest excluded: {rel_path} - {reason}")
                            continue

                    # Check if file should be included based on product
                    if not self.should_include_file(rel_path):
                        skipped_count += 1
                        # Uncomment for debugging:
                        # print(f"Product filtered: {rel_path}")
                        continue

                    # Check if file should be renamed
                    new_rel_path, will_update_imports = self.file_renamer.get_new_path(str(rel_path))
                    target_path = self.target_base / new_rel_path

                    # Compare with import replacement (only for Python files)
                    # For non-Python files, still do comparison but without import replacement
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
        self._scan_progress.stop()
        self._scan_progress.grid_remove()
        status_msg = f"Found {len(self.files_data)} files for {product}"
        if manifest_excluded > 0:
            status_msg += f" (manifest excluded {manifest_excluded})"
        if skipped_count > 0:
            status_msg += f" (product filtered {skipped_count})"
        if total_files_seen > 0:
            status_msg += f" (scanned {total_files_seen} total)"
        self.status_label.configure(text=status_msg)

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
            self.status_label.configure(text="No files match filters")
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

        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", "end")
        dt = self.diff_text._textbox
        dt.config(state="normal")
        dt.delete("1.0", "end")

        # Details (no tags needed)
        details = f"""File: {rel_path}
Status: {self.format_status(data['status'])}
Similarity: {data['similarity']*100:.1f}%
Source: {data['source_path']}
Target: {data['target_path']}

"""
        if data.get('renamed'):
            details += "File Rename:\n"
            details += f"  Old: {Path(rel_path).name}\n"
            details += f"  New: {Path(data['new_rel_path']).name}\n"
            if data.get('will_update_imports'):
                details += "  Will update imports in this file\n"
            details += "\n"

        if data.get('replacements'):
            details += "Import Replacements:\n"
            for old_imp, new_imp in data['replacements']:
                details += f"  {old_imp}\n    \u2192 {new_imp}\n"
            details += "\n"

        self.details_text.insert("1.0", details)
        self.details_text.configure(state="disabled")

        # Diff (tag operations through ._textbox)
        if data['status'] in ['minor_changes', 'minimal_changes', 'major_changes']:
            if data['status'] == 'major_changes':
                warning = "\u26a0\ufe0f  WARNING: Major changes (< 30% similarity)\n" + "=" * 60 + "\n\n"
                dt.insert("1.0", warning, "header")

            if data.get('replacements'):
                repl_info = "\U0001f504 Import replacements will be applied:\n"
                for old_imp, new_imp in data['replacements'][:3]:
                    repl_info += f"  \u2022 {old_imp} \u2192 {new_imp}\n"
                if len(data['replacements']) > 3:
                    repl_info += f"  ... and {len(data['replacements']) - 3} more\n"
                repl_info += "\n"
                dt.insert("end", repl_info, "replacement")

            for line in data['diff_lines'][:200]:
                if line.startswith('+++') or line.startswith('---'):
                    dt.insert("end", line + "\n", "header")
                elif line.startswith('+'):
                    dt.insert("end", line + "\n", "add")
                elif line.startswith('-'):
                    dt.insert("end", line + "\n", "remove")
                else:
                    dt.insert("end", line + "\n")

            if len(data['diff_lines']) > 200:
                dt.insert("end",
                           f"\n... ({len(data['diff_lines']) - 200} more lines)\n", "header")

        elif data['status'] == 'new':
            msg = "This is a new file.\n"
            if data.get('replacements'):
                msg += "\nImport replacements will be applied during deployment.\n"
            dt.insert("1.0", msg)
        elif data['status'] == 'identical':
            dt.insert("1.0", "Files are identical.\n")

        dt.config(state="disabled")

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
        self.status_label.configure(text=msg)

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
        self.last_report_file_path = report_file

        # Save changelog entry (JSON + CHANGELOG.md)
        self.save_changelog_entry(deployment_report, report_file)

        # Enable report button
        try:
            self.report_button.configure(state='normal')
        except Exception:
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
            'rename_csv': str(self.rename_csv) if self.rename_csv else "",
            'manifest_file': str(self.manifest_file) if self.manifest_file else "",
            'selected_files': list(self.selected_files)
        }

        # Save to file
        if save_config(self.config):
            self.status_label.configure(text=f"Configuration saved for {product}")
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
                self.target_label.configure(text=str(self.target_base))

        # Load CSV
        if prod_config.get('replacement_csv'):
            csv_path = Path(prod_config['replacement_csv'])
            if csv_path.exists():
                if self.import_replacer.load_from_csv(csv_path):
                    self.replacement_csv = csv_path
                    self.csv_label.configure(text=csv_path.name)

        # Load rename CSV
        if prod_config.get('rename_csv'):
            csv_path = Path(prod_config['rename_csv'])
            if csv_path.exists():
                if self.file_renamer.load_from_csv(csv_path):
                    self.rename_csv = csv_path
                    self.rename_csv_label.configure(text=csv_path.name)

        # Load manifest
        if prod_config.get('manifest_file'):
            manifest_path = Path(prod_config['manifest_file'])
            if manifest_path.exists():
                if self.deployment_manifest.load_from_json(manifest_path):
                    self.manifest_file = manifest_path
                    manifest_name = manifest_path.stem.replace('deployment_manifest_', '')
                    self.manifest_label.configure(text=manifest_name)

        # Load selected files (will be applied after scan)
        if prod_config.get('selected_files'):
            self.selected_files = set(prod_config['selected_files'])

        self.status_label.configure(text=f"Loaded configuration for {product}")

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

        report_window = ctk.CTkToplevel(self.root)
        report_window.title(f"Deployment Report - {report['timestamp']}")
        report_window.geometry("960x720")
        report_window.configure(fg_color=C_BG)

        text_widget = ctk.CTkTextbox(
            report_window, font=FONT_MONO, fg_color=C_PANEL2, wrap="word"
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=(10, 4))

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

        text_widget.insert("1.0", report_text)
        text_widget.configure(state="disabled")

        ctk.CTkButton(
            report_window, text="Close", width=90, fg_color=C_INPUT, hover_color=C_BORDER,
            command=report_window.destroy
        ).pack(pady=6)

    # ──────────────────────────────────────────────────────────────────────
    # Tab switching
    # ──────────────────────────────────────────────────────────────────────

    def _on_tab_changed_ctk(self, tab_name: str):
        """Handle tab change for CTkTabview."""
        if tab_name == "  Reports & Changelog  ":
            self.refresh_reports_tab()
        elif tab_name == "  Release Notes  " and hasattr(self, 'release_end_var'):
            self.release_end_var.set(datetime.now().strftime('%Y-%m-%d'))

    # ── Collapsible config sidebar ─────────────────────────────────────────

    def _toggle_config(self):
        """Toggle the source configuration panel collapsed/expanded."""
        if self._config_collapsed:
            self._cfg_body.grid()
            self._cfg_toggle_btn.configure(text="▼  collapse")
            self._config_collapsed = False
        else:
            self._cfg_body.grid_remove()
            self._cfg_toggle_btn.configure(text="▶  expand")
            self._config_collapsed = True

    # ── Diff search helpers ────────────────────────────────────────────────

    def _diff_search_run(self):
        """Highlight all matches of search term in the diff textbox."""
        dt = self.diff_text._textbox
        dt.tag_remove("search_hi", "1.0", "end")
        self._diff_search_positions = []
        self._diff_search_idx = -1
        term = self._diff_search_var.get()
        if not term:
            self._diff_match_label.configure(text="")
            return
        start = "1.0"
        while True:
            pos = dt.search(term, start, stopindex="end", nocase=True)
            if not pos:
                break
            end_pos = f"{pos}+{len(term)}c"
            dt.tag_add("search_hi", pos, end_pos)
            self._diff_search_positions.append(pos)
            start = end_pos
        count = len(self._diff_search_positions)
        if count:
            self._diff_match_label.configure(
                text=f"{count} match{'es' if count != 1 else ''}"
            )
            self._diff_search_idx = 0
            dt.see(self._diff_search_positions[0])
        else:
            self._diff_match_label.configure(text="no matches")

    def _diff_search_next(self):
        """Jump to next search match in the diff textbox."""
        if not self._diff_search_positions:
            return
        self._diff_search_idx = (self._diff_search_idx + 1) % len(self._diff_search_positions)
        self.diff_text._textbox.see(self._diff_search_positions[self._diff_search_idx])

    def _diff_search_prev(self):
        """Jump to previous search match in the diff textbox."""
        if not self._diff_search_positions:
            return
        self._diff_search_idx = (self._diff_search_idx - 1) % len(self._diff_search_positions)
        self.diff_text._textbox.see(self._diff_search_positions[self._diff_search_idx])

    def _diff_search_clear(self):
        """Clear the diff search highlight."""
        self._diff_search_var.set("")
        self.diff_text._textbox.tag_remove("search_hi", "1.0", "end")
        self._diff_search_positions = []
        self._diff_match_label.configure(text="")

    # ──────────────────────────────────────────────────────────────────────
    # Changelog & History
    # ──────────────────────────────────────────────────────────────────────

    def save_changelog_entry(self, report: dict, report_file: Path):
        """Append a deployment entry to deployment_changelog.json and CHANGELOG.md."""
        deployed = report.get('deployed', [])
        errors = report.get('errors', [])
        skipped = report.get('skipped_files', [])
        product = report.get('product', '?')
        source = report.get('source_type', '?')
        dep_type = report.get('deployment_type', '?')
        target = report.get('target_base', '?')
        timestamp_str = report.get('timestamp', datetime.now().strftime('%Y%m%d_%H%M%S'))

        entry = {
            'timestamp': timestamp_str,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'product': product,
            'source_type': source,
            'deployment_type': dep_type,
            'target': target,
            'files_deployed': [d.get('target_file', '') for d in deployed],
            'files_deployed_count': len(deployed),
            'files_skipped_count': len(skipped),
            'errors_count': len(errors),
            'replacements_count': sum(len(d.get('import_replacements', [])) for d in deployed),
            'renames_count': sum(1 for d in deployed if d.get('renamed')),
            'report_file': str(report_file),
        }

        # JSON changelog
        existing: list = []
        if DEPLOYMENT_CHANGELOG_PATH.exists():
            try:
                with open(DEPLOYMENT_CHANGELOG_PATH, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        existing.append(entry)
        try:
            with open(DEPLOYMENT_CHANGELOG_PATH, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=2)
        except Exception as e:
            print(f"Warning: could not write deployment_changelog.json: {e}")

        # CHANGELOG.md
        try:
            date_human = datetime.now().strftime('%B %d, %Y')
            block = (
                f"\n## [{timestamp_str}] — {product} Deploy — {date_human}\n\n"
                f"### Summary\n"
                f"- **Product:** {product}  \n"
                f"- **Source:** {source} / {dep_type}  \n"
                f"- **Target:** `{target}`  \n"
                f"- **Files Deployed:** {len(deployed)}  \n"
                f"- **Errors:** {len(errors)}  \n"
                f"- **Import Replacements:** {entry['replacements_count']}  \n"
                f"- **File Renames:** {entry['renames_count']}  \n\n"
                f"### Deployed Files\n"
            )
            for d in deployed[:25]:
                tag = (f" ← *renamed from `{d.get('old_name','')}`*"
                       if d.get('renamed') else "")
                block += f"- `{d.get('target_file', '')}`{tag}\n"
            if len(deployed) > 25:
                block += f"- *(…and {len(deployed) - 25} more)*\n"
            if errors:
                block += "\n### Errors\n"
                for err in errors:
                    block += f"- `{err.get('source_file','')}`: {err.get('error','')}\n"
            block += "\n---\n"
            with open(CHANGELOG_PATH, 'a', encoding='utf-8') as f:
                f.write(block)
        except Exception as e:
            print(f"Warning: could not append to CHANGELOG.md: {e}")

        # Refresh live widgets if visible
        try:
            if hasattr(self, 'changelog_text'):
                self.view_changelog()
            if hasattr(self, '_history_list_frame'):
                self.refresh_reports_tab()
        except Exception:
            pass

    def view_changelog(self):
        """Load CHANGELOG.md into the Reports tab changelog widget."""
        if not hasattr(self, 'changelog_text'):
            # Fallback: open a standalone ctk window
            if CHANGELOG_PATH.exists():
                win = ctk.CTkToplevel(self.root)
                win.title("CHANGELOG.md")
                win.geometry("960x720")
                win.configure(fg_color=C_BG)
                txt = ctk.CTkTextbox(win, font=FONT_MONO, fg_color=C_PANEL2, wrap="word")
                txt.pack(fill="both", expand=True, padx=10, pady=(10, 4))
                txt.insert("1.0", CHANGELOG_PATH.read_text(encoding="utf-8"))
                txt.configure(state="disabled")
                ctk.CTkButton(win, text="Close", width=90, fg_color=C_INPUT,
                              hover_color=C_BORDER,
                              command=win.destroy).pack(pady=6)
            else:
                messagebox.showinfo("Not Found", "CHANGELOG.md not found.")
            return

        content = ""
        if CHANGELOG_PATH.exists():
            try:
                content = CHANGELOG_PATH.read_text(encoding="utf-8")
            except Exception as e:
                content = f"Error reading CHANGELOG.md:\n{e}"
        else:
            content = "CHANGELOG.md not found in DEVTOOLS/."

        self.changelog_text.configure(state="normal")
        self.changelog_text.delete("1.0", "end")
        self.changelog_text.insert("1.0", content)
        self.changelog_text.configure(state="disabled")

    def _open_changelog_in_editor(self):
        """Open CHANGELOG.md in the OS default text editor."""
        if CHANGELOG_PATH.exists():
            os.startfile(str(CHANGELOG_PATH))
        else:
            messagebox.showinfo("Not Found", "CHANGELOG.md not found.")

    def refresh_reports_tab(self):
        """Populate the deployment history list from deployment_changelog.json."""
        # Clear existing buttons
        for btn in getattr(self, '_history_btn_refs', []):
            btn.destroy()
        self._history_btn_refs = []
        self._history_entries = []

        if not DEPLOYMENT_CHANGELOG_PATH.exists():
            placeholder = ctk.CTkLabel(
                self._history_list_frame,
                text="(No deployment history yet — deploy something first)",
                font=FONT_SMALL,
                text_color=C_TEXT_DIM,
                wraplength=320,
            )
            placeholder.pack(pady=12, padx=8)
            self._history_btn_refs.append(placeholder)
            self.view_changelog()
            return

        try:
            with open(DEPLOYMENT_CHANGELOG_PATH, 'r', encoding='utf-8') as f:
                entries: list = json.load(f)
        except Exception as e:
            err_lbl = ctk.CTkLabel(
                self._history_list_frame,
                text=f"Error loading history: {e}",
                font=FONT_SMALL,
                text_color=C_ERROR,
            )
            err_lbl.pack(pady=8, padx=8)
            self._history_btn_refs.append(err_lbl)
            return

        # Newest first
        self._history_entries = list(reversed(entries))
        for idx, entry in enumerate(self._history_entries):
            ts = entry.get('timestamp', '?')
            prod = entry.get('product', '?')
            dep = entry.get('deployment_type', '?')
            n = entry.get('files_deployed_count', 0)
            err = entry.get('errors_count', 0)
            label = f"{ts}  [{prod}/{dep}]  {n} files"
            if err:
                label += f"  ⚠ {err} errors"
            btn = ctk.CTkButton(
                self._history_list_frame,
                text=label,
                font=FONT_SMALL,
                anchor="w",
                fg_color="transparent",
                hover_color=C_PANEL2,
                text_color=C_TEXT if not err else C_WARNING,
                command=lambda i=idx: self._on_history_select(i),
            )
            btn.pack(fill="x", padx=2, pady=1)
            self._history_btn_refs.append(btn)

        self.view_changelog()

    def _on_history_select(self, idx: int):
        """Show detail text for the history entry at *idx*."""
        if not hasattr(self, '_history_entries') or not self._history_entries:
            return
        if idx >= len(self._history_entries):
            return
        entry = self._history_entries[idx]

        detail = (
            f"Timestamp    : {entry.get('timestamp', '?')}\n"
            f"Date         : {entry.get('date', '?')}\n"
            f"Product      : {entry.get('product', '?')}\n"
            f"Source       : {entry.get('source_type', '?')}\n"
            f"Deploy Type  : {entry.get('deployment_type', '?')}\n"
            f"Target       : {entry.get('target', '?')}\n"
            f"Deployed     : {entry.get('files_deployed_count', 0)} files\n"
            f"Skipped      : {entry.get('files_skipped_count', 0)} files\n"
            f"Errors       : {entry.get('errors_count', 0)}\n"
            f"Replacements : {entry.get('replacements_count', 0)}\n"
            f"Renames      : {entry.get('renames_count', 0)}\n"
            f"Report CSV   : {entry.get('report_file', 'N/A')}\n\n"
            "Files deployed:\n"
        )
        for fp in entry.get('files_deployed', [])[:15]:
            detail += f"  • {fp}\n"
        total = entry.get('files_deployed_count', 0)
        if total > 15:
            detail += f"  … and {total - 15} more\n"

        self.history_detail_text.configure(state='normal')
        self.history_detail_text.delete('1.0', 'end')
        self.history_detail_text.insert('1.0', detail)
        self.history_detail_text.configure(state='disabled')

    def open_csv_report(self):
        """Open a deployment CSV report in a scrollable viewer window."""
        csv_path = filedialog.askopenfilename(
            title="Open Deployment Report CSV",
            initialdir=DEVTOOLS_PATH,
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not csv_path:
            return
        try:
            content = Path(csv_path).read_text(encoding="utf-8", errors="replace")
            win = ctk.CTkToplevel(self.root)
            win.title(f"Report — {Path(csv_path).name}")
            win.geometry("1040x720")
            win.configure(fg_color=C_BG)
            txt = ctk.CTkTextbox(win, font=FONT_MONO, fg_color=C_PANEL2, wrap="none")
            txt.pack(fill="both", expand=True, padx=6, pady=(6, 4))
            txt.insert("1.0", content)
            txt.configure(state="disabled")
            ctk.CTkButton(win, text="Close", width=90, fg_color=C_INPUT, hover_color=C_BORDER,
                          command=win.destroy).pack(pady=6)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open report:\n{e}")

    # ──────────────────────────────────────────────────────────────────────
    # Validation Agent
    # ──────────────────────────────────────────────────────────────────────

    def run_validation_agent(self):
        """Open the Validate & Review dialog (runs deploy_agent.py)."""
        ValidationAgentDialog(self.root, self.product.get(), self.target_base)

    def _run_agent_command(self, cmd: list, title: str):
        """Run a deploy_agent.py command and stream output into a CTkToplevel window."""
        win = ctk.CTkToplevel(self.root)
        win.title(title)
        win.geometry("840x520")
        win.configure(fg_color=C_BG)
        txt = ctk.CTkTextbox(win, font=FONT_MONO, fg_color=C_PANEL2,
                              state="disabled", wrap="word")
        txt.pack(fill="both", expand=True, padx=6, pady=(6, 4))

        def _insert(line):
            txt.configure(state="normal")
            txt.insert("end", line)
            txt.see("end")
            txt.configure(state="disabled")

        def _worker():
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, cwd=str(DEVTOOLS_PATH)
                )
                for line in proc.stdout:
                    win.after(0, _insert, line)
                proc.wait()
                win.after(0, _insert, f"\n[Finished — exit {proc.returncode}]\n")
            except Exception as e:
                win.after(0, _insert, f"\nError: {e}\n")

        threading.Thread(target=_worker, daemon=True).start()
        ctk.CTkButton(win, text="Close", width=90, fg_color=C_INPUT, hover_color=C_BORDER,
                      command=win.destroy).pack(pady=6)

    # ──────────────────────────────────────────────────────────────────────
    # Release Notes Tab
    # ──────────────────────────────────────────────────────────────────────

    def generate_draft_release(self):
        """Run generate_release_notes.py as a subprocess and load the output."""
        start_date = self.release_start_var.get().strip()
        if not start_date:
            messagebox.showwarning("Missing Date", "Please enter a Start Date (YYYY-MM-DD).")
            return

        script = DEVTOOLS_PATH / "generate_release_notes.py"
        if not script.exists():
            messagebox.showerror("Error", "generate_release_notes.py not found in DEVTOOLS/.")
            return

        end_date = self.release_end_var.get().strip() or datetime.now().strftime("%Y-%m-%d")
        version = self.release_version_var.get().strip()
        cmd = [sys.executable, str(script), "--start-date", start_date, "--end-date", end_date]
        if version:
            cmd += ["--version", version]

        self.release_status_label.configure(text="Generating draft release notes…")
        self.root.update()

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=90, cwd=str(DEVTOOLS_PATH)
            )
            # Find the newest DRAFT file
            deploys_dir = DEVTOOLS_PATH / "deploys"
            candidates = (
                sorted(deploys_dir.glob("DRAFT_RELEASE_*.md"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
                if deploys_dir.exists() else []
            )
            if candidates:
                self.current_release_file = candidates[0]
                self.release_file_label.configure(text=str(self.current_release_file))
                content = self.current_release_file.read_text(encoding='utf-8')
                self.release_editor.delete('1.0', 'end')
                self.release_editor.insert('1.0', content)
                self.release_status_label.configure(
                    text=f"Draft generated: {self.current_release_file.name}"
                )
            else:
                output = result.stdout + ("\nSTDERR:\n" + result.stderr if result.stderr.strip() else "")
                self.release_editor.delete('1.0', 'end')
                self.release_editor.insert(
                    '1.0',
                    f"Script output:\n{output}\n\n(No DRAFT_RELEASE_*.md found in deploys/)"
                )
                self.release_status_label.configure(text="Script ran — no draft file found in deploys/")
        except subprocess.TimeoutExpired:
            self.release_status_label.configure(text="Timeout (>90s)")
            messagebox.showerror("Timeout", "generate_release_notes.py timed out after 90 seconds.")
        except Exception as e:
            self.release_status_label.configure(text=f"Error: {e}")
            messagebox.showerror("Error", f"Failed to generate release notes:\n{e}")

    def load_existing_release(self):
        """Load an existing release Markdown file into the editor."""
        deploys_dir = DEVTOOLS_PATH / "deploys"
        initial = deploys_dir if deploys_dir.exists() else DEVTOOLS_PATH
        path = filedialog.askopenfilename(
            title="Load Release Document",
            initialdir=initial,
            filetypes=[("Markdown Files", "*.md"), ("All Files", "*.*")]
        )
        if path:
            self.current_release_file = Path(path)
            self.release_file_label.configure(text=str(self.current_release_file))
            self.release_editor.delete('1.0', 'end')
            self.release_editor.insert(
                '1.0', self.current_release_file.read_text(encoding='utf-8')
            )
            self.release_status_label.configure(text=f"Loaded: {self.current_release_file.name}")

    def save_release_document(self):
        """Save the release editor content to a .md file."""
        content = self.release_editor.get('1.0', 'end-1c')
        if not content.strip():
            messagebox.showwarning("Empty", "Nothing to save.")
            return

        if self.current_release_file:
            save_path = self.current_release_file
        else:
            version = self.release_version_var.get().strip() or "X.X.X"
            date_tag = datetime.now().strftime("%b%Y")
            deploys_dir = DEVTOOLS_PATH / "deploys"
            deploys_dir.mkdir(exist_ok=True)
            path = filedialog.asksaveasfilename(
                title="Save Release Document",
                initialdir=deploys_dir,
                initialfile=f"RELEASE_v{version}_{date_tag}.md",
                defaultextension=".md",
                filetypes=[("Markdown Files", "*.md"), ("All Files", "*.*")]
            )
            if not path:
                return
            save_path = Path(path)

        try:
            save_path.write_text(content, encoding='utf-8')
            self.current_release_file = save_path
            self.release_file_label.configure(text=str(save_path))
            self.release_status_label.configure(text=f"Saved: {save_path.name}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save:\n{e}")

    def export_release_html(self):
        """Convert release editor content to a self-contained HTML file."""
        content = self.release_editor.get('1.0', 'end-1c')
        if not content.strip():
            messagebox.showwarning("Empty", "Nothing to export.")
            return

        version = self.release_version_var.get().strip() or "X.X.X"
        date_tag = datetime.now().strftime("%b%Y")
        deploys_dir = DEVTOOLS_PATH / "deploys" / "release_files"
        deploys_dir.mkdir(parents=True, exist_ok=True)

        path = filedialog.asksaveasfilename(
            title="Export HTML",
            initialdir=deploys_dir,
            initialfile=f"RELEASE_EMAIL_v{version}_{date_tag}.html",
            defaultextension=".html",
            filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")]
        )
        if not path:
            return

        import html as _html
        css = (
            "body{font-family:Arial,sans-serif;max-width:900px;margin:40px auto;line-height:1.6}"
            "h1{color:#1a1a2e}h2{color:#16213e;border-bottom:1px solid #ccc;padding-bottom:4px}"
            "h3{color:#0f3460}code{background:#f4f4f4;padding:2px 5px;border-radius:3px}"
            "pre{background:#f4f4f4;padding:12px;border-radius:5px;overflow-x:auto}"
            "li{margin:3px 0}hr{border:none;border-top:1px solid #ddd}"
        )
        out = [
            '<!DOCTYPE html><html><head><meta charset="utf-8">',
            f'<style>{css}</style></head><body>'
        ]
        in_pre = False
        in_ul = False
        for raw in content.split('\n'):
            esc = _html.escape(raw)
            if esc.startswith('```'):
                if in_ul:
                    out.append('</ul>'); in_ul = False
                if in_pre:
                    out.append('</code></pre>'); in_pre = False
                else:
                    out.append('<pre><code>'); in_pre = True
                continue
            if in_pre:
                out.append(esc); continue
            if esc.startswith('### '):
                if in_ul: out.append('</ul>'); in_ul = False
                out.append(f'<h3>{esc[4:]}</h3>')
            elif esc.startswith('## '):
                if in_ul: out.append('</ul>'); in_ul = False
                out.append(f'<h2>{esc[3:]}</h2>')
            elif esc.startswith('# '):
                if in_ul: out.append('</ul>'); in_ul = False
                out.append(f'<h1>{esc[2:]}</h1>')
            elif esc.startswith('- ') or esc.startswith('* '):
                if not in_ul: out.append('<ul>'); in_ul = True
                item = re.sub(r'`(.+?)`', r'<code>\1</code>', esc[2:])
                out.append(f'<li>{item}</li>')
            elif esc.startswith('---'):
                if in_ul: out.append('</ul>'); in_ul = False
                out.append('<hr>')
            elif esc.strip() == '':
                if in_ul: out.append('</ul>'); in_ul = False
                out.append('')
            else:
                if in_ul: out.append('</ul>'); in_ul = False
                line_h = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', esc)
                line_h = re.sub(r'`(.+?)`', r'<code>\1</code>', line_h)
                out.append(f'<p>{line_h}</p>')
        if in_ul:
            out.append('</ul>')
        if in_pre:
            out.append('</code></pre>')
        out.append('</body></html>')

        try:
            Path(path).write_text('\n'.join(out), encoding='utf-8')
            self.release_status_label.configure(text=f"HTML exported: {Path(path).name}")
            if messagebox.askyesno("Open HTML?", f"HTML saved:\n{Path(path).name}\n\nOpen in browser?"):
                webbrowser.open(path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not export HTML:\n{e}")

    def create_release_pr(self):
        """Create a draft GitHub PR for the release using the gh CLI."""
        version = self.release_version_var.get().strip()
        if not version:
            messagebox.showwarning("No Version", "Please enter a version number first.")
            return

        self.save_release_document()
        if not self.current_release_file:
            return

        if not DEPLOY_AGENT_PATH.exists():
            messagebox.showerror(
                "Error",
                "deploy_agent.py not found in DEVTOOLS/.\nEnsure the agent script is present."
            )
            return

        title = f"Release v{version} — {datetime.now().strftime('%B %Y')}"
        body = (
            f"Release notes for v{version}.\n\n"
            f"Generated by Universal Central Deployment Tool on "
            f"{datetime.now().strftime('%Y-%m-%d')}.\n\n"
            f"See: `{self.current_release_file.name}`"
        )
        cmd = [
            sys.executable, str(DEPLOY_AGENT_PATH),
            "--pr",
            "--pr-title", title,
            "--pr-body", body,
            "--draft"
        ]
        self._run_agent_command(cmd, f"Creating Draft PR: {title}")


def main():
    """Main entry point."""
    root = ctk.CTk()
    app = UniversalDeploymentGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
