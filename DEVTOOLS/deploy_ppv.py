"""
PPV Deployment Tool
===================
This tool helps deploy PPV files from the main development directory
to the DebugFramework PPV location in S2T\\BASELINE\\DebugFramework\\PPV

Features:
- Interactive file selection
- Side-by-side file comparison
- Change detection with similarity metrics
- Safe deployment with backup options
- Dependency tracking

Author: GitHub Copilot
Version: 1.0.0
Date: December 9, 2025
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import difflib
import shutil
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import hashlib


def load_config():
    """Load configuration from JSON file if it exists, otherwise use defaults."""
    config_file = Path(__file__).parent / "deploy_config.json"

    # Default configuration
    default_config = {
        "paths": {
            "source_base": r"c:\Git\Automation\PPV",
            "target_base": r"c:\Git\Automation\S2T\BASELINE\DebugFramework\PPV",
            "backup_base": r"c:\Git\Automation\DEVTOOLS\backups"
        },
        "settings": {
            "similarity_threshold": 0.3,
            "max_diff_lines_display": 200,
            "auto_backup": True,
            "confirm_major_changes": True
        }
    }

    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
                # Merge with defaults
                default_config.update(loaded_config)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")

    return default_config


# Load configuration
CONFIG = load_config()

# Configuration
SOURCE_BASE = Path(CONFIG["paths"]["source_base"])
TARGET_BASE = Path(CONFIG["paths"]["target_base"])
BACKUP_BASE = Path(CONFIG["paths"]["backup_base"])

# Similarity threshold for "too big" changes (0.0 = completely different, 1.0 = identical)
SIMILARITY_THRESHOLD = CONFIG["settings"]["similarity_threshold"]


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
    def compare_files(source: Path, target: Path) -> Dict:
        """
        Compare two files and return detailed comparison info.

        Returns:
            dict with keys: exists, identical, similarity, diff_lines, status
        """
        result = {
            'exists': target.exists(),
            'identical': False,
            'similarity': 0.0,
            'diff_lines': [],
            'status': 'new',
            'source_size': 0,
            'target_size': 0
        }

        if not source.exists():
            result['status'] = 'missing_source'
            return result

        result['source_size'] = source.stat().st_size

        if not target.exists():
            result['status'] = 'new'
            return result

        result['target_size'] = target.stat().st_size

        # Check if files are identical
        source_hash = FileComparer.get_file_hash(source)
        target_hash = FileComparer.get_file_hash(target)

        if source_hash == target_hash:
            result['identical'] = True
            result['similarity'] = 1.0
            result['status'] = 'identical'
            return result

        # Read files for comparison
        try:
            with open(source, 'r', encoding='utf-8', errors='ignore') as f:
                source_lines = f.readlines()
            with open(target, 'r', encoding='utf-8', errors='ignore') as f:
                target_lines = f.readlines()
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            return result

        # Calculate similarity
        matcher = difflib.SequenceMatcher(None, source_lines, target_lines)
        result['similarity'] = matcher.ratio()

        # Generate unified diff
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


class DependencyTracker:
    """Tracks file dependencies by analyzing imports."""

    @staticmethod
    def get_local_imports(file_path: Path, base_path: Path) -> List[str]:
        """Extract local imports from a Python file."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                # Match: from .module import / from ..module import / import module
                if line.startswith('from ') or line.startswith('import '):
                    # Extract module name
                    parts = line.split()
                    if parts[0] == 'from':
                        module = parts[1].split('.')[0]
                        if module in ['api', 'gui', 'parsers', 'utils', 'Decoder']:
                            imports.append(module)
                    elif parts[0] == 'import':
                        module = parts[1].split('.')[0]
                        if module in ['api', 'gui', 'parsers', 'utils', 'Decoder']:
                            imports.append(module)
        except Exception as e:
            pass

        return list(set(imports))


class DeploymentGUI:
    """Main GUI for the deployment tool."""

    def __init__(self, root):
        self.root = root
        self.root.title("PPV Deployment Tool")
        self.root.geometry("1200x800")

        self.source_base = SOURCE_BASE
        self.target_base = TARGET_BASE
        self.backup_base = BACKUP_BASE

        # Store file states
        self.files_data = {}  # relative_path -> comparison_data
        self.selected_files = set()
        self.checkboxes = {}  # item_id -> checkbox state

        self.setup_ui()
        self.scan_files()

    def setup_ui(self):
        """Create the user interface."""
        # Header
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill='x')

        ttk.Label(
            header_frame,
            text="PPV Deployment Tool",
            font=('Arial', 16, 'bold')
        ).pack()

        # Source/Target selection
        paths_frame = ttk.Frame(header_frame)
        paths_frame.pack(fill='x', pady=5)

        ttk.Label(paths_frame, text="Source:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky='w', padx=5)
        ttk.Label(paths_frame, text=str(self.source_base), font=('Arial', 9)).grid(row=0, column=1, sticky='w', padx=5)

        ttk.Label(paths_frame, text="Target:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky='w', padx=5)
        self.target_label = ttk.Label(paths_frame, text=str(self.target_base), font=('Arial', 9))
        self.target_label.grid(row=1, column=1, sticky='w', padx=5)

        ttk.Button(
            paths_frame,
            text="Change Target...",
            command=self.change_target
        ).grid(row=1, column=2, padx=5)

        # Main content with paned window
        paned = ttk.PanedWindow(self.root, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=10, pady=5)

        # Left panel - File list
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        # File list controls
        controls_frame = ttk.Frame(left_frame)
        controls_frame.pack(fill='x', pady=5)

        ttk.Button(
            controls_frame,
            text="Select All",
            command=self.select_all
        ).pack(side='left', padx=2)

        ttk.Button(
            controls_frame,
            text="Deselect All",
            command=self.deselect_all
        ).pack(side='left', padx=2)

        ttk.Button(
            controls_frame,
            text="Refresh",
            command=self.scan_files
        ).pack(side='left', padx=2)

        # Filter
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill='x', pady=5)
        ttk.Label(filter_frame, text="Filter:").pack(side='left')
        self.filter_var = tk.StringVar()
        self.filter_var.trace('w', lambda *args: self.apply_filter())
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var)
        filter_entry.pack(side='left', fill='x', expand=True, padx=5)

        # Filter options
        filter_options = ttk.Frame(left_frame)
        filter_options.pack(fill='x', pady=2)
        self.show_only_changes = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            filter_options,
            text="Show only files with changes",
            variable=self.show_only_changes,
            command=self.apply_filter
        ).pack(side='left', padx=5)

        self.show_only_selected = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            filter_options,
            text="Show only selected",
            variable=self.show_only_selected,
            command=self.apply_filter
        ).pack(side='left', padx=5)

        # File tree
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill='both', expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')

        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=('selected', 'status', 'similarity', 'size'),
            yscrollcommand=scrollbar.set,
            selectmode='extended'
        )
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.tree.yview)

        # Configure columns
        self.tree.heading('#0', text='File')
        self.tree.heading('selected', text='☑', command=self.toggle_all_visible)
        self.tree.heading('status', text='Status')
        self.tree.heading('similarity', text='Similarity')
        self.tree.heading('size', text='Size')

        self.tree.column('#0', width=350)
        self.tree.column('selected', width=40, anchor='center')
        self.tree.column('status', width=120)
        self.tree.column('similarity', width=80)
        self.tree.column('size', width=80)

        # Bind selection
        self.tree.bind('<<TreeviewSelect>>', self.on_file_select)
        self.tree.bind('<space>', self.toggle_selection)
        self.tree.bind('<Button-1>', self.on_tree_click)

        # Right panel - Details and diff
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)

        # Details section
        details_frame = ttk.LabelFrame(right_frame, text="File Details", padding="5")
        details_frame.pack(fill='x', pady=5)

        self.details_text = tk.Text(details_frame, height=8, wrap='word')
        self.details_text.pack(fill='x')

        # Diff section
        diff_frame = ttk.LabelFrame(right_frame, text="Changes Preview", padding="5")
        diff_frame.pack(fill='both', expand=True, pady=5)

        self.diff_text = scrolledtext.ScrolledText(
            diff_frame,
            wrap='none',
            font=('Courier', 9)
        )
        self.diff_text.pack(fill='both', expand=True)

        # Configure diff colors
        self.diff_text.tag_config('add', foreground='green')
        self.diff_text.tag_config('remove', foreground='red')
        self.diff_text.tag_config('header', foreground='blue', font=('Courier', 9, 'bold'))

        # Bottom panel - Actions
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill='x', side='bottom')

        self.status_label = ttk.Label(
            bottom_frame,
            text="Ready. Select files to deploy.",
            relief='sunken'
        )
        self.status_label.pack(side='left', fill='x', expand=True)

        ttk.Button(
            bottom_frame,
            text="Deploy Selected",
            command=self.deploy_selected,
            style='Accent.TButton'
        ).pack(side='right', padx=5)

        ttk.Button(
            bottom_frame,
            text="View Dependencies",
            command=self.show_dependencies
        ).pack(side='right', padx=5)

    def scan_files(self):
        """Scan source directory and compare with target."""
        self.status_label.config(text="Scanning files...")
        self.root.update()

        self.files_data.clear()
        self.tree.delete(*self.tree.get_children())

        # Scan all Python files in source
        for root, dirs, files in os.walk(self.source_base):
            # Skip __pycache__ and .vscode
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.vscode', '.git']]

            for file in files:
                # Only include Python files and JSON configs
                if file.endswith(('.py', '.json')) and not file.startswith('__'):
                    source_path = Path(root) / file
                    rel_path = source_path.relative_to(self.source_base)
                    target_path = self.target_base / rel_path

                    # Compare files
                    comparison = FileComparer.compare_files(source_path, target_path)
                    comparison['rel_path'] = str(rel_path)
                    comparison['source_path'] = source_path
                    comparison['target_path'] = target_path

                    self.files_data[str(rel_path)] = comparison

        self.populate_tree()
        self.status_label.config(text=f"Found {len(self.files_data)} files")

    def populate_tree(self):
        """Populate the tree view with files."""
        # Group by directory
        directories = {}

        for rel_path, data in sorted(self.files_data.items()):
            parts = Path(rel_path).parts
            if len(parts) > 1:
                dir_name = parts[0]
            else:
                dir_name = "root"

            if dir_name not in directories:
                directories[dir_name] = []
            directories[dir_name].append((rel_path, data))

        # Add to tree
        for dir_name in sorted(directories.keys()):
            # Add directory node
            dir_node = self.tree.insert('', 'end', text=dir_name, open=True)

            # Add files
            for rel_path, data in directories[dir_name]:
                status = self.format_status(data['status'])
                similarity = f"{data['similarity']*100:.0f}%" if data['similarity'] > 0 else "-"
                size = self.format_size(data['source_size'])

                # Check if selected
                is_selected = rel_path in self.selected_files
                checkbox = "☑" if is_selected else "☐"

                # Color code based on status
                tags = (data['status'],)

                item_id = self.tree.insert(
                    dir_node,
                    'end',
                    text=Path(rel_path).name,
                    values=(checkbox, status, similarity, size),
                    tags=tags
                )

                # Store mapping
                self.checkboxes[item_id] = rel_path

        # Configure tags for colors
        self.tree.tag_configure('new', foreground='blue')
        self.tree.tag_configure('identical', foreground='gray')
        self.tree.tag_configure('minor_changes', foreground='orange')
        self.tree.tag_configure('major_changes', foreground='red')

    def format_status(self, status: str) -> str:
        """Format status for display."""
        status_map = {
            'new': 'New File',
            'identical': 'Identical',
            'minimal_changes': 'Minimal Changes',
            'minor_changes': 'Minor Changes',
            'major_changes': 'Major Changes',
            'missing_source': 'Missing Source',
            'error': 'Error'
        }
        return status_map.get(status, status)

    def format_size(self, size: int) -> str:
        """Format file size for display."""
        for unit in ['B', 'KB', 'MB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}GB"

    def on_file_select(self, event):
        """Handle file selection in tree."""
        selection = self.tree.selection()
        if not selection:
            return

        # Get selected item
        item = selection[0]

        # Check if it's a file (has parent)
        parent = self.tree.parent(item)
        if not parent:
            return

        # Get file name and directory
        file_name = self.tree.item(item, 'text')
        dir_name = self.tree.item(parent, 'text')

        # Find the file data
        rel_path = None
        for path, data in self.files_data.items():
            if Path(path).name == file_name:
                if dir_name == "root" or Path(path).parts[0] == dir_name:
                    rel_path = path
                    break

        if rel_path:
            self.show_file_details(rel_path)

    def show_file_details(self, rel_path: str):
        """Show details for a selected file."""
        data = self.files_data[rel_path]

        # Clear previous content
        self.details_text.delete('1.0', 'end')
        self.diff_text.delete('1.0', 'end')

        # Show details
        details = f"""File: {rel_path}
Status: {self.format_status(data['status'])}
Similarity: {data['similarity']*100:.1f}%
Source Size: {self.format_size(data['source_size'])}
Target Size: {self.format_size(data['target_size']) if data['exists'] else 'N/A'}

Source: {data['source_path']}
Target: {data['target_path']}
"""

        self.details_text.insert('1.0', details)

        # Show diff
        if data['status'] in ['minor_changes', 'minimal_changes', 'major_changes']:
            if data['status'] == 'major_changes':
                warning = "⚠️  WARNING: Major changes detected (similarity < 30%)\n"
                warning += "=" * 60 + "\n\n"
                self.diff_text.insert('1.0', warning, 'header')

            # Show diff
            for line in data['diff_lines'][:200]:  # Limit to 200 lines
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
            self.diff_text.insert('1.0', "This is a new file that doesn't exist in the target location.\n")
        elif data['status'] == 'identical':
            self.diff_text.insert('1.0', "Files are identical. No changes needed.\n")

    def on_tree_click(self, event):
        """Handle click on tree item."""
        region = self.tree.identify_region(event.x, event.y)
        if region == 'cell':
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)

            # Check if clicked on checkbox column
            if column == '#1' and item in self.checkboxes:
                self.toggle_item_selection(item)

    def toggle_selection(self, event):
        """Toggle selection of current item with spacebar."""
        selection = self.tree.selection()
        if not selection:
            return

        for item in selection:
            if item in self.checkboxes:
                self.toggle_item_selection(item)

    def toggle_item_selection(self, item_id):
        """Toggle selection state of a specific item."""
        if item_id not in self.checkboxes:
            return

        rel_path = self.checkboxes[item_id]

        if rel_path in self.selected_files:
            self.selected_files.remove(rel_path)
            checkbox = "☐"
        else:
            self.selected_files.add(rel_path)
            checkbox = "☑"

        # Update checkbox in tree
        current_values = list(self.tree.item(item_id, 'values'))
        current_values[0] = checkbox
        self.tree.item(item_id, values=current_values)

        self.update_selection_display()

    def toggle_all_visible(self):
        """Toggle selection of all visible files."""
        # Get all visible file items
        visible_items = []
        for item in self.tree.get_children():
            for child in self.tree.get_children(item):
                if child in self.checkboxes:
                    visible_items.append(child)

        if not visible_items:
            return

        # Check if all are selected
        all_selected = all(
            self.checkboxes[item] in self.selected_files
            for item in visible_items
        )

        # Toggle
        if all_selected:
            # Deselect all visible
            for item in visible_items:
                rel_path = self.checkboxes[item]
                if rel_path in self.selected_files:
                    self.selected_files.remove(rel_path)
                current_values = list(self.tree.item(item, 'values'))
                current_values[0] = "☐"
                self.tree.item(item, values=current_values)
        else:
            # Select all visible
            for item in visible_items:
                rel_path = self.checkboxes[item]
                self.selected_files.add(rel_path)
                current_values = list(self.tree.item(item, 'values'))
                current_values[0] = "☑"
                self.tree.item(item, values=current_values)

        self.update_selection_display()

    def update_selection_display(self):
        """Update status label with selection count."""
        count = len(self.selected_files)
        self.status_label.config(text=f"Selected {count} file(s) for deployment")

    def select_all(self):
        """Select all files."""
        self.selected_files = set(self.files_data.keys())
        self.apply_filter()  # Refresh display with checkboxes
        self.update_selection_display()

    def deselect_all(self):
        """Deselect all files."""
        self.selected_files.clear()
        self.apply_filter()  # Refresh display with checkboxes
        self.update_selection_display()

    def change_target(self):
        """Change target deployment directory."""
        from tkinter import filedialog

        new_target = filedialog.askdirectory(
            title="Select Target Directory",
            initialdir=self.target_base.parent
        )

        if new_target:
            self.target_base = Path(new_target)
            self.target_label.config(text=str(self.target_base))

            # Rescan with new target
            self.selected_files.clear()
            self.scan_files()

            messagebox.showinfo(
                "Target Changed",
                f"Target directory changed to:\n{self.target_base}\n\nFiles have been rescanned."
            )

    def apply_filter(self):
        """Apply filter to file list."""
        filter_text = self.filter_var.get().lower()
        show_changes_only = self.show_only_changes.get()
        show_selected_only = self.show_only_selected.get()

        # Clear tree
        self.tree.delete(*self.tree.get_children())
        self.checkboxes.clear()

        # Filter files
        filtered_data = {}
        for path, data in self.files_data.items():
            # Apply text filter
            if filter_text and filter_text not in path.lower():
                continue

            # Apply changes filter
            if show_changes_only and data['status'] == 'identical':
                continue

            # Apply selected filter
            if show_selected_only and path not in self.selected_files:
                continue

            filtered_data[path] = data

        if not filtered_data:
            self.status_label.config(text="No files match the current filters")
            return

        # Temporarily replace files_data
        original_data = self.files_data
        self.files_data = filtered_data
        self.populate_tree()
        self.files_data = original_data

    def show_dependencies(self):
        """Show dependencies for selected files."""
        if not self.selected_files:
            messagebox.showwarning("No Selection", "Please select files first.")
            return

        # Analyze dependencies
        dep_window = tk.Toplevel(self.root)
        dep_window.title("Dependency Analysis")
        dep_window.geometry("600x400")

        text = scrolledtext.ScrolledText(dep_window, wrap='word')
        text.pack(fill='both', expand=True, padx=10, pady=10)

        all_deps = set()
        file_deps = {}

        for rel_path in self.selected_files:
            data = self.files_data[rel_path]
            if data['source_path'].suffix == '.py':
                deps = DependencyTracker.get_local_imports(
                    data['source_path'],
                    self.source_base
                )
                if deps:
                    file_deps[rel_path] = deps
                    all_deps.update(deps)

        # Display results
        text.insert('1.0', "Dependency Analysis\n")
        text.insert('end', "=" * 60 + "\n\n")

        if not file_deps:
            text.insert('end', "No dependencies found.\n")
        else:
            text.insert('end', f"Required modules: {', '.join(sorted(all_deps))}\n\n")
            text.insert('end', "File-by-file dependencies:\n")
            text.insert('end', "-" * 60 + "\n")

            for file, deps in sorted(file_deps.items()):
                text.insert('end', f"\n{file}:\n")
                for dep in sorted(deps):
                    text.insert('end', f"  - {dep}\n")

        text.config(state='disabled')

    def deploy_selected(self):
        """Deploy selected files to target."""
        if not self.selected_files:
            messagebox.showwarning("No Selection", "Please select files to deploy.")
            return

        # Check for major changes
        major_changes = []
        for rel_path in self.selected_files:
            data = self.files_data[rel_path]
            if data['status'] == 'major_changes':
                major_changes.append(rel_path)

        if major_changes:
            msg = "The following files have major changes (< 30% similarity):\n\n"
            msg += "\n".join(f"  • {p}" for p in major_changes[:10])
            if len(major_changes) > 10:
                msg += f"\n  ... and {len(major_changes) - 10} more"
            msg += "\n\nDo you want to continue?"

            if not messagebox.askyesno("Major Changes Detected", msg):
                return

        # Confirm deployment
        msg = f"Deploy {len(self.selected_files)} file(s) to:\n{self.target_base}\n\n"
        msg += "A backup will be created before deployment."

        if not messagebox.askyesno("Confirm Deployment", msg):
            return

        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_base / timestamp

        # Deploy files
        deployed = 0
        errors = []

        for rel_path in self.selected_files:
            data = self.files_data[rel_path]
            source = data['source_path']
            target = data['target_path']

            try:
                # Backup existing file
                if target.exists():
                    backup_file = backup_dir / rel_path
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, backup_file)

                # Copy new file
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                deployed += 1

            except Exception as e:
                errors.append(f"{rel_path}: {str(e)}")

        # Show results
        if errors:
            error_msg = f"Deployed {deployed} files with {len(errors)} errors:\n\n"
            error_msg += "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n... and {len(errors) - 5} more"
            messagebox.showwarning("Deployment Completed with Errors", error_msg)
        else:
            messagebox.showinfo(
                "Deployment Successful",
                f"Successfully deployed {deployed} file(s).\n\nBackup location:\n{backup_dir}"
            )

        # Refresh
        self.selected_files.clear()
        self.scan_files()


def main():
    """Main entry point."""
    # Verify paths exist
    if not SOURCE_BASE.exists():
        print(f"Error: Source directory not found: {SOURCE_BASE}")
        sys.exit(1)

    if not TARGET_BASE.exists():
        print(f"Error: Target directory not found: {TARGET_BASE}")
        response = input("Create target directory? (y/n): ")
        if response.lower() == 'y':
            TARGET_BASE.mkdir(parents=True, exist_ok=True)
        else:
            sys.exit(1)

    # Create backup directory
    BACKUP_BASE.mkdir(parents=True, exist_ok=True)

    # Launch GUI
    root = tk.Tk()
    app = DeploymentGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
