"""
Dragon Content to NSH Generator
Parses DragonContent.txt file and generates .nsh files with user-selected content
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import os
from pathlib import Path


# Modern color scheme
COLORS = {
    'bg': '#f5f5f5',
    'fg': '#2c3e50',
    'primary': '#3498db',
    'success': '#2ecc71',
    'warning': '#f39c12',
    'danger': '#e74c3c',
    'border': '#bdc3c7',
    'header_bg': '#34495e',
    'header_fg': '#ecf0f1',
    'row_alt': '#ecf0f1',
    'selected': '#d5e8f7'
}


class DragonContent:
    """Represents a single DragonContent entry"""
    def __init__(self, name, obj_path, operations='', features='', enabled=''):
        self.name = name
        self.obj_path = obj_path
        self.operations = operations
        self.features = features
        self.enabled = enabled
        self.selected = True  # Default to selected
        
    def get_base_path(self):
        """Extract base path from object file path"""
        # Extract path before the .obj filename and convert double backslashes to single
        match = re.search(r'(.*\\)[^\\]+\.obj', self.obj_path)
        if match:
            path = match.group(1).rstrip('\\')
            # Replace double backslashes with single backslashes
            path = path.replace('\\\\', '\\')
            return path
        return ""
    
    def get_obj_filename(self):
        """Extract just the .obj filename"""
        match = re.search(r'([^\\]+\.obj)', self.obj_path)
        if match:
            return match.group(1).replace('.obj', '')
        return self.name
    
    def get_features_list(self):
        """Parse features into a list"""
        features = []
        if self.features:
            # Extract individual features from expressions like:
            # ProductFeatures.IsDrgBmGnrReleaseEnabled && ProductFeatures.IsPmEnabled
            feature_matches = re.findall(r'ProductFeatures\.(\w+)', self.features)
            features = list(set(feature_matches))  # Remove duplicates
        return features
    
    def get_operations_list(self):
        """Parse operations into a list"""
        operations = []
        if self.operations:
            # Extract individual operations from expressions like:
            # TestOperations.HVCP || TestOperations.HVCPCellCheckout
            op_matches = re.findall(r'TestOperations\.(\w+)', self.operations)
            operations = list(set(op_matches))  # Remove duplicates
        return operations


class DragonContentParser:
    """Parses DragonContent files (.txt/.content), .obj directories, or .nsh files"""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.contents = []
        
    def parse(self):
        """Parse the file based on its type"""
        ext = os.path.splitext(self.filepath)[1].lower()
        
        if os.path.isdir(self.filepath):
            # Directory of .obj files
            return self._parse_obj_directory()
        elif ext == '.nsh':
            # Previously generated NSH file
            return self._parse_nsh_file()
        else:
            # DragonContent file (.txt, .content, etc.)
            return self._parse_dragoncontent_file()
    
    def _parse_dragoncontent_file(self):
        """Parse DragonContent.txt/.content file"""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Pattern to match DragonContent blocks
        pattern = r'DragonContent\s+"([^"]+)"\s*\{([^}]+)\}'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            name = match.group(1)
            content_block = match.group(2)
            
            # Extract properties
            obj_path = self._extract_property(content_block, 'ObjectFilePath')
            operations = self._extract_property(content_block, 'Operations')
            features = self._extract_property(content_block, 'Features')
            enabled = self._extract_property(content_block, 'Enabled')
            
            content = DragonContent(name, obj_path, operations, features, enabled)
            self.contents.append(content)
        
        return self.contents
    
    def _parse_obj_directory(self):
        """Parse directory containing .obj files"""
        obj_files = []
        for file in os.listdir(self.filepath):
            if file.endswith('.obj'):
                obj_files.append(file)
        
        # Sort files alphabetically
        obj_files.sort()
        
        # Create DragonContent entries from .obj files
        for obj_file in obj_files:
            name = os.path.splitext(obj_file)[0]
            full_path = os.path.join(self.filepath, obj_file).replace('\\', '\\\\')
            content = DragonContent(name, full_path)
            self.contents.append(content)
        
        return self.contents
    
    def _parse_nsh_file(self):
        """Parse previously generated NSH file"""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Extract OBJPATH if present
        objpath_match = re.search(r'set OBJPATH\s+"([^"]+)"', text)
        base_objpath = objpath_match.group(1) if objpath_match else ''
        
        # Extract Seed entries
        # Pattern: ## Seed N - filename followed by set OBJFILE "filename.obj"
        pattern = r'##\s*Seed\s+\d+\s+-\s+([^\n]+)\s*\nset OBJFILE\s+"([^"]+)"'
        matches = re.finditer(pattern, text, re.MULTILINE)
        
        for match in matches:
            name = match.group(1).strip()
            obj_filename = match.group(2)
            
            # Construct full path
            if base_objpath:
                full_path = f"{base_objpath}\\{obj_filename}"
            else:
                full_path = obj_filename
            
            content = DragonContent(name, full_path)
            self.contents.append(content)
        
        return self.contents
    
    def _extract_property(self, block, property_name):
        """Extract a property value from a content block"""
        pattern = rf'{property_name}\s*=\s*"([^"]+)"'
        match = re.search(pattern, block)
        if match:
            return match.group(1)
        
        # For non-quoted values
        pattern = rf'{property_name}\s*=\s*([^;]+);'
        match = re.search(pattern, block)
        if match:
            return match.group(1).strip()
        
        return ""


class DragonContentGUI:
    """GUI for selecting content and generating .nsh files"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Dragon Content to NSH Generator")
        self.root.geometry("1600x950")
        
        # Configure root window colors
        self.root.configure(bg=COLORS['bg'])
        
        self.contents = []
        self.all_features = set()
        self.all_operations = set()
        self.column_filters = {}  # Store filter state for each column
        self.filename_keywords = []  # Store filename filter keywords
        
        # NSH generation variables
        self.nsh_vars = {
            'mode': tk.StringVar(value='Normal'),
            'merlin_dir': tk.StringVar(value=r'fs1:\EFI\Version8.15\BinFiles\Release'),
            'merlin': tk.StringVar(value='MerlinX.efi'),
            'objpath': tk.StringVar(value=''),
            'vvar0': tk.StringVar(value='0x04C4B40'),
            'vvar1': tk.StringVar(value='80064000'),
            'vvar2': tk.StringVar(value='0x1000000'),
            'vvar3': tk.StringVar(value='0x800000'),
            'vvar4': tk.StringVar(value=''),
            'vvar5': tk.StringVar(value=''),
            'vvar_extra': tk.StringVar(value=''),
            'stop_on_fail': tk.BooleanVar(value=True)
        }
        
        # Store entry widgets for enabling/disabling
        self.var_entries = []
        
        # Configure ttk styles
        self.setup_styles()
        self.setup_ui()
    
    def setup_styles(self):
        """Setup modern ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('TFrame', background=COLORS['bg'])
        style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['fg'])
        style.configure('TButton', 
                       background=COLORS['primary'], 
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=6)
        style.map('TButton',
                 background=[('active', '#2980b9'), ('pressed', '#2574a9')])
        
        style.configure('Success.TButton', background=COLORS['success'])
        style.map('Success.TButton',
                 background=[('active', '#27ae60'), ('pressed', '#229954')])
        
        style.configure('Danger.TButton', background=COLORS['danger'])
        style.map('Danger.TButton',
                 background=[('active', '#c0392b'), ('pressed', '#a93226')])
        
        style.configure('TLabelframe', background=COLORS['bg'], foreground=COLORS['fg'])
        style.configure('TLabelframe.Label', background=COLORS['bg'], foreground=COLORS['fg'], font=('Segoe UI', 10, 'bold'))
        
        style.configure('TCheckbutton', background=COLORS['bg'], foreground=COLORS['fg'])
        style.configure('TRadiobutton', background=COLORS['bg'], foreground=COLORS['fg'])
        
        # Treeview styling
        style.configure('Treeview',
                       background='white',
                       foreground=COLORS['fg'],
                       fieldbackground='white',
                       borderwidth=0)
        style.configure('Treeview.Heading',
                       background=COLORS['header_bg'],
                       foreground=COLORS['header_fg'],
                       borderwidth=1,
                       relief='flat')
        style.map('Treeview.Heading',
                 background=[('active', '#2c3e50')])
        style.map('Treeview',
                 background=[('selected', COLORS['selected'])])
        
    def setup_ui(self):
        """Setup the user interface"""
        # Top frame - File selection
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="Source:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(0, 10))
        self.file_entry = ttk.Entry(top_frame, width=80, font=('Segoe UI', 9))
        self.file_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_frame, text="📁 Browse", command=self.browse_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="📂 Load", command=self.load_file, style='Success.TButton').pack(side=tk.LEFT, padx=5)
        
        # Info label
        info_frame = ttk.Frame(self.root, padding=(10, 0, 10, 5))
        info_frame.pack(fill=tk.X)
        ttk.Label(info_frame, text="💡 Supports: DragonContent files (.txt/.content), .obj directories, or .nsh files", 
                 font=('Segoe UI', 8, 'italic')).pack(side=tk.LEFT)
        
        # NSH Configuration frame
        nsh_config_frame = ttk.LabelFrame(self.root, text="NSH Generation Configuration", padding="10")
        nsh_config_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        # Create grid layout for NSH variables
        row = 0
        
        # Mode selection
        ttk.Label(nsh_config_frame, text="Mode:", font=('Segoe UI', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        mode_frame = ttk.Frame(nsh_config_frame)
        mode_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        ttk.Radiobutton(mode_frame, text="Normal (Set variables from UI)", 
                       variable=self.nsh_vars['mode'], value='Normal', 
                       command=self.on_mode_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Framework (Variables from external script)", 
                       variable=self.nsh_vars['mode'], value='Framework',
                       command=self.on_mode_change).pack(side=tk.LEFT, padx=5)
        ttk.Button(mode_frame, text="❓ Help", command=self.show_help).pack(side=tk.LEFT, padx=10)
        row += 1
        
        # Separator
        ttk.Separator(nsh_config_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky='ew', pady=5)
        row += 1
        
        # MERLIN_DIR path
        ttk.Label(nsh_config_frame, text="MERLIN_DIR:", font=('Segoe UI', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        merlin_dir_entry = ttk.Entry(nsh_config_frame, textvariable=self.nsh_vars['merlin_dir'], width=50)
        merlin_dir_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        self.var_entries.append(merlin_dir_entry)
        
        # MERLIN
        ttk.Label(nsh_config_frame, text="MERLIN:", font=('Segoe UI', 9, 'bold')).grid(row=row, column=2, sticky=tk.W, padx=5, pady=2)
        merlin_entry = ttk.Entry(nsh_config_frame, textvariable=self.nsh_vars['merlin'], width=20)
        merlin_entry.grid(row=row, column=3, sticky=tk.W, padx=5, pady=2)
        self.var_entries.append(merlin_entry)
        row += 1
        
        # OBJPATH
        ttk.Label(nsh_config_frame, text="OBJPATH:", font=('Segoe UI', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        objpath_entry = ttk.Entry(nsh_config_frame, textvariable=self.nsh_vars['objpath'], width=50)
        objpath_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        self.var_entries.append(objpath_entry)
        ttk.Label(nsh_config_frame, text="(Leave blank to use file path)", font=('Segoe UI', 8, 'italic')).grid(row=row, column=2, columnspan=2, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # VVAR0
        ttk.Label(nsh_config_frame, text="VVAR0 (Test Runtime):", font=('Segoe UI', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        vvar0_entry = ttk.Entry(nsh_config_frame, textvariable=self.nsh_vars['vvar0'], width=20)
        vvar0_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        self.var_entries.append(vvar0_entry)
        
        # VVAR1
        ttk.Label(nsh_config_frame, text="VVAR1 (Exec Time):", font=('Segoe UI', 9, 'bold')).grid(row=row, column=2, sticky=tk.W, padx=5, pady=2)
        vvar1_entry = ttk.Entry(nsh_config_frame, textvariable=self.nsh_vars['vvar1'], width=20)
        vvar1_entry.grid(row=row, column=3, sticky=tk.W, padx=5, pady=2)
        self.var_entries.append(vvar1_entry)
        row += 1
        
        # VVAR2
        ttk.Label(nsh_config_frame, text="VVAR2 (Thread Count):", font=('Segoe UI', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        vvar2_entry = ttk.Entry(nsh_config_frame, textvariable=self.nsh_vars['vvar2'], width=20)
        vvar2_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        self.var_entries.append(vvar2_entry)
        
        # VVAR3
        ttk.Label(nsh_config_frame, text="VVAR3 (Debug Flags):", font=('Segoe UI', 9, 'bold')).grid(row=row, column=2, sticky=tk.W, padx=5, pady=2)
        vvar3_entry = ttk.Entry(nsh_config_frame, textvariable=self.nsh_vars['vvar3'], width=20)
        vvar3_entry.grid(row=row, column=3, sticky=tk.W, padx=5, pady=2)
        self.var_entries.append(vvar3_entry)
        row += 1
        
        # VVAR4
        ttk.Label(nsh_config_frame, text="VVAR4 (Min APIC ID):", font=('Segoe UI', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        vvar4_entry = ttk.Entry(nsh_config_frame, textvariable=self.nsh_vars['vvar4'], width=20)
        vvar4_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        self.var_entries.append(vvar4_entry)
        
        # VVAR5
        ttk.Label(nsh_config_frame, text="VVAR5 (Max APIC ID):", font=('Segoe UI', 9, 'bold')).grid(row=row, column=2, sticky=tk.W, padx=5, pady=2)
        vvar5_entry = ttk.Entry(nsh_config_frame, textvariable=self.nsh_vars['vvar5'], width=20)
        vvar5_entry.grid(row=row, column=3, sticky=tk.W, padx=5, pady=2)
        self.var_entries.append(vvar5_entry)
        row += 1
        
        # VVAR_EXTRA
        ttk.Label(nsh_config_frame, text="VVAR_EXTRA:", font=('Segoe UI', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        vvar_extra_entry = ttk.Entry(nsh_config_frame, textvariable=self.nsh_vars['vvar_extra'], width=70)
        vvar_extra_entry.grid(row=row, column=1, columnspan=3, sticky=tk.W, padx=5, pady=2)
        self.var_entries.append(vvar_extra_entry)
        row += 1
        
        # STOP_ON_FAIL
        ttk.Label(nsh_config_frame, text="STOP_ON_FAIL:", font=('Segoe UI', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        stop_on_fail_cb = ttk.Checkbutton(nsh_config_frame, text="Stop execution on first failure", variable=self.nsh_vars['stop_on_fail'])
        stop_on_fail_cb.grid(row=row, column=1, columnspan=3, sticky=tk.W, padx=5, pady=2)
        self.var_entries.append(stop_on_fail_cb)
        
        # Filter frame - Column-based filters
        filter_frame = ttk.LabelFrame(self.root, text="Filters", padding="10")
        filter_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        # Filename filter
        filename_filter_frame = ttk.Frame(filter_frame)
        filename_filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filename_filter_frame, text="Filter by filename (comma-separated keywords):", 
                 font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        self.filename_filter_var = tk.StringVar()
        self.filename_filter_entry = ttk.Entry(filename_filter_frame, textvariable=self.filename_filter_var, width=50)
        self.filename_filter_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(filename_filter_frame, text="Apply", command=self.apply_filename_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(filename_filter_frame, text="Clear", command=self.clear_filename_filter).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filename_filter_frame, text="(e.g., Ditto, Twiddle)", 
                 font=('Segoe UI', 8, 'italic')).pack(side=tk.LEFT, padx=10)
        
        # Separator
        ttk.Separator(filter_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # Info label
        info_label = ttk.Label(filter_frame, 
                              text="Click on column headers in the table to filter by features/operations",
                              font=('Segoe UI', 9, 'italic'))
        info_label.pack(pady=5)
        
        # Filter action buttons
        filter_btn_frame = ttk.Frame(filter_frame)
        filter_btn_frame.pack(pady=5)
        ttk.Button(filter_btn_frame, text="Clear All Filters", command=self.clear_all_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_btn_frame, text="Select Filtered", command=self.select_filtered, style='Success.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_btn_frame, text="Deselect Filtered", command=self.deselect_filtered, style='Danger.TButton').pack(side=tk.LEFT, padx=5)
        
        # Middle frame - Data grid
        middle_frame = ttk.Frame(self.root, padding="10")
        middle_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Treeview with scrollbars
        tree_frame = ttk.Frame(middle_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Vertical scrollbar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Horizontal scrollbar
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        self.tree = ttk.Treeview(tree_frame, 
                                yscrollcommand=vsb.set,
                                xscrollcommand=hsb.set,
                                selectmode='extended')
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Bind double-click to toggle selection and right-click for column filter
        self.tree.bind('<Double-Button-1>', self.toggle_selection)
        self.tree.bind('<Button-1>', self.on_tree_click)
        
        # Bottom frame - Actions
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X)
        
        ttk.Button(bottom_frame, text="✓ Select All", command=self.select_all, style='Success.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="✗ Deselect All", command=self.deselect_all, style='Danger.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="🚀 Generate NSH", command=self.generate_nsh).pack(side=tk.LEFT, padx=20)
        ttk.Button(bottom_frame, text="Exit", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Please load a DragonContent file")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             bg=COLORS['header_bg'], fg=COLORS['header_fg'],
                             anchor=tk.W, padx=10, pady=5, font=('Segoe UI', 9))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def on_mode_change(self):
        """Handle mode change between Normal and Framework"""
        mode = self.nsh_vars['mode'].get()
        
        # Enable/disable variable entries based on mode
        if mode == 'Framework':
            # Disable all variable entries
            for entry in self.var_entries:
                entry.config(state='disabled')
        else:
            # Enable all variable entries
            for entry in self.var_entries:
                entry.config(state='normal')
    
    def show_help(self):
        """Show help dialog with variable descriptions"""
        help_text = """NSH Generation Modes:

NORMAL MODE:
All variables are set from the UI and written to the NSH file.
Use this mode for standalone NSH file execution.

FRAMEWORK MODE:
All variables are expected to be set by an external script before calling this NSH.
The generated NSH will use %1 parameter for OBJFILE.
Use this mode when integrating with a framework that manages variables.

Variable Descriptions:

MERLIN_DIR: Path to Merlin binaries directory
  Default: fs1:\\EFI\\Version8.15\\BinFiles\\Release

MERLIN: Merlin executable command
  Default: MerlinX.efi

OBJPATH: Path to object files
  Leave blank to use path from DragonContent file

VVAR0: Dragon VVAR 0 - Test Runtime
  Default: 0x04C4B40

VVAR1: Dragon VVAR 1 - Execution Time in CPU Cycles
  Default: 80064000

VVAR2: Dragon VVAR 2 - Thread Count
  Default: 0x1000000

VVAR3: Dragon VVAR 3 - Debug Flags
  Default: 0x800000

VVAR4: Dragon VVAR 4 - Min APIC ID (optional)
  Default: blank (0x0)

VVAR5: Dragon VVAR 5 - Max APIC ID (optional)
  Default: blank (0x7FFFFFFF)

VVAR_EXTRA: Additional VVAR parameters
  Default: blank

DRG_STOP_ON_FAIL: Stop on first failure
  1 = Stop on first failure
  0 = Continue through all tests
"""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("NSH Generation Help")
        help_window.geometry("700x600")
        help_window.configure(bg=COLORS['bg'])
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                             font=('Segoe UI', 9), bg='white', fg=COLORS['fg'])
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        text_widget.insert('1.0', help_text)
        text_widget.config(state='disabled')
        
        # Close button
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)
    
    def browse_file(self):
        """Browse for DragonContent file, NSH file, or directory"""
        # Create a custom dialog to allow both files and directories
        from tkinter import simpledialog
        
        # First, ask what type of source
        choice_window = tk.Toplevel(self.root)
        choice_window.title("Select Source Type")
        choice_window.geometry("400x200")
        choice_window.configure(bg=COLORS['bg'])
        choice_window.transient(self.root)
        choice_window.grab_set()
        
        selected_type = tk.StringVar(value='')
        
        def select_type(type_val):
            selected_type.set(type_val)
            choice_window.destroy()
        
        ttk.Label(choice_window, text="Select source type:", font=('Segoe UI', 11, 'bold')).pack(pady=20)
        
        ttk.Button(choice_window, text="📄 DragonContent File (.txt/.content)", 
                  command=lambda: select_type('file'), 
                  width=40).pack(pady=5)
        ttk.Button(choice_window, text="📁 Directory with .obj files", 
                  command=lambda: select_type('dir'),
                  width=40).pack(pady=5)
        ttk.Button(choice_window, text="📋 Previously Generated .nsh file", 
                  command=lambda: select_type('nsh'),
                  width=40).pack(pady=5)
        
        choice_window.wait_window()
        
        source_type = selected_type.get()
        if not source_type:
            return
        
        if source_type == 'dir':
            # Browse for directory
            directory = filedialog.askdirectory(title="Select Directory with .obj Files")
            if directory:
                self.file_entry.delete(0, tk.END)
                self.file_entry.insert(0, directory)
        elif source_type == 'nsh':
            # Browse for NSH file
            filename = filedialog.askopenfilename(
                title="Select NSH File",
                filetypes=[("NSH files", "*.nsh"), ("All files", "*.*")]
            )
            if filename:
                self.file_entry.delete(0, tk.END)
                self.file_entry.insert(0, filename)
        else:
            # Browse for DragonContent file
            filename = filedialog.askopenfilename(
                title="Select DragonContent File",
                filetypes=[("Content files", "*.txt *.content"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                self.file_entry.delete(0, tk.END)
                self.file_entry.insert(0, filename)
            
    def load_file(self):
        """Load and parse the DragonContent file, directory, or NSH file"""
        filepath = self.file_entry.get()
        
        if not filepath:
            messagebox.showerror("Error", "Please select a file or directory")
            return
        
        if not os.path.exists(filepath):
            messagebox.showerror("Error", "Selected path does not exist")
            return
        
        try:
            parser = DragonContentParser(filepath)
            self.contents = parser.parse()
            
            if not self.contents:
                if os.path.isdir(filepath):
                    messagebox.showwarning("Warning", "No .obj files found in directory")
                else:
                    messagebox.showwarning("Warning", "No content entries found")
                return
            
            # Collect all unique features and operations
            self.all_features = set()
            self.all_operations = set()
            
            for content in self.contents:
                self.all_features.update(content.get_features_list())
                self.all_operations.update(content.get_operations_list())
            
            self.populate_tree()
            
            # Determine source type for status message
            if os.path.isdir(filepath):
                source_type = "directory"
            elif filepath.endswith('.nsh'):
                source_type = "NSH file"
            else:
                source_type = "DragonContent file"
            
            self.status_var.set(f"Loaded {len(self.contents)} entries from {source_type}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse: {str(e)}")
    
    def on_tree_click(self, event):
        """Handle click on tree - check if it's a header click"""
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            column = self.tree.identify_column(event.x)
            col_index = int(column.replace('#', '')) - 1
            col_name = self.tree['columns'][col_index]
            
            # Only allow filtering on feature and operation columns (those with checkmarks)
            if col_name not in ['Selected', 'Name', 'Object File', 'Enabled']:
                self.show_column_filter(col_name, event.x_root, event.y_root)
    
    def populate_tree(self):
        """Populate the treeview with content data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Define columns
        columns = ['Selected', 'Name', 'Object File']
        
        # Add feature columns
        feature_cols = sorted(list(self.all_features))
        columns.extend(feature_cols)
        
        # Add operation columns
        operation_cols = sorted(list(self.all_operations))
        columns.extend(operation_cols)
        
        # Add enabled column
        columns.append('Enabled')
        
        self.tree['columns'] = columns
        self.tree['show'] = 'headings'
        
        # Configure column headings and widths
        self.tree.heading('Selected', text='Selected')
        self.tree.column('Selected', width=60, anchor='center')
        
        self.tree.heading('Name', text='Content Name')
        self.tree.column('Name', width=300)
        
        self.tree.heading('Object File', text='Object File')
        self.tree.column('Object File', width=200)
        
        for feature in feature_cols:
            self.tree.heading(feature, text=feature)
            self.tree.column(feature, width=50, anchor='center')
        
        for operation in operation_cols:
            self.tree.heading(operation, text=operation)
            self.tree.column(operation, width=50, anchor='center')
        
        self.tree.heading('Enabled', text='Enabled')
        self.tree.column('Enabled', width=80, anchor='center')
        
        # Populate rows
        for idx, content in enumerate(self.contents):
            # Check if content matches filters
            if hasattr(self, 'filtered_indices') and idx not in self.filtered_indices:
                continue
            
            values = []
            
            # Selected
            values.append('✓' if content.selected else '')
            
            # Name
            values.append(content.name)
            
            # Object file
            values.append(content.get_obj_filename())
            
            # Features
            content_features = content.get_features_list()
            for feature in feature_cols:
                values.append('✓' if feature in content_features else '')
            
            # Operations
            content_operations = content.get_operations_list()
            for operation in operation_cols:
                values.append('✓' if operation in content_operations else '')
            
            # Enabled
            values.append('✓' if content.enabled else '')
            
            self.tree.insert('', tk.END, iid=str(idx), values=values)
    
    def toggle_selection(self, event):
        """Toggle selection status of clicked item"""
        item = self.tree.identify('item', event.x, event.y)
        if item:
            idx = int(item)
            self.contents[idx].selected = not self.contents[idx].selected
            
            # Update the display
            values = list(self.tree.item(item)['values'])
            values[0] = '✓' if self.contents[idx].selected else ''
            self.tree.item(item, values=values)
    
    def select_all(self):
        """Select all items"""
        for content in self.contents:
            content.selected = True
        self.populate_tree()
        self.status_var.set("All items selected")
    
    def deselect_all(self):
        """Deselect all items"""
        for content in self.contents:
            content.selected = False
        self.populate_tree()
        self.status_var.set("All items deselected")
    
    def show_column_filter(self, col_name, x, y):
        """Show filter menu for a column"""
        menu = tk.Menu(self.root, tearoff=0, bg='white', fg=COLORS['fg'])
        
        # Get current filter state
        current_filter = self.column_filters.get(col_name, 'all')
        
        # Add filter options
        menu.add_radiobutton(label="Show All", 
                            variable=tk.StringVar(value=current_filter),
                            value='all',
                            command=lambda: self.set_column_filter(col_name, 'all'))
        menu.add_radiobutton(label="Show Checked (✓)", 
                            variable=tk.StringVar(value=current_filter),
                            value='checked',
                            command=lambda: self.set_column_filter(col_name, 'checked'))
        menu.add_radiobutton(label="Show Unchecked", 
                            variable=tk.StringVar(value=current_filter),
                            value='unchecked',
                            command=lambda: self.set_column_filter(col_name, 'unchecked'))
        
        # Add visual indicator of current filter
        if current_filter == 'checked':
            menu.entryconfigure(1, background=COLORS['selected'])
        elif current_filter == 'unchecked':
            menu.entryconfigure(2, background=COLORS['selected'])
        else:
            menu.entryconfigure(0, background=COLORS['selected'])
        
        menu.post(x, y)
    
    def set_column_filter(self, col_name, filter_type):
        """Set filter for a specific column"""
        if filter_type == 'all':
            if col_name in self.column_filters:
                del self.column_filters[col_name]
        else:
            self.column_filters[col_name] = filter_type
        
        self.apply_filters()
    
    def apply_column_filters(self):
        """Apply only column-based filters (used internally when combining with filename filter)"""
        if not self.column_filters:
            return set(range(len(self.contents)))
        
        filtered = set()
        feature_cols = sorted(list(self.all_features))
        operation_cols = sorted(list(self.all_operations))
        
        for idx, content in enumerate(self.contents):
            match = True
            
            content_features = content.get_features_list()
            content_operations = content.get_operations_list()
            
            # Check each column filter
            for col_name, filter_type in self.column_filters.items():
                is_checked = False
                
                # Determine if this column is checked for this content
                if col_name in feature_cols:
                    is_checked = col_name in content_features
                elif col_name in operation_cols:
                    is_checked = col_name in content_operations
                
                # Apply filter logic
                if filter_type == 'checked' and not is_checked:
                    match = False
                    break
                elif filter_type == 'unchecked' and is_checked:
                    match = False
                    break
            
            if match:
                filtered.add(idx)
        
        return filtered
    
    def apply_filters(self):
        """Apply all filters (column + filename) and update the tree view"""
        if not self.column_filters and not self.filename_keywords:
            # No filters active
            if hasattr(self, 'filtered_indices'):
                delattr(self, 'filtered_indices')
            self.populate_tree()
            self.status_var.set(f"No filters active - showing all {len(self.contents)} items")
            return
        
        # Start with all indices
        column_filtered = self.apply_column_filters()
        
        # Apply filename filter if present
        if self.filename_keywords:
            filename_filtered = set()
            for idx in column_filtered:
                content = self.contents[idx]
                filename = os.path.basename(content.obj_path).lower()
                
                # Check if any keyword matches the filename
                if any(keyword in filename for keyword in self.filename_keywords):
                    filename_filtered.add(idx)
            
            self.filtered_indices = filename_filtered
        else:
            self.filtered_indices = column_filtered
        
        self.populate_tree()
        
        # Build status message
        filter_parts = []
        if self.column_filters:
            col_desc = ", ".join([f"{k}={v}" for k, v in self.column_filters.items()])
            filter_parts.append(f"Columns: {col_desc}")
        if self.filename_keywords:
            filter_parts.append(f"Filename: {', '.join(self.filename_keywords)}")
        
        filter_desc = " | ".join(filter_parts)
        self.status_var.set(f"Filters active [{filter_desc}]: {len(self.filtered_indices)} of {len(self.contents)} items shown")
    
    def apply_filename_filter(self):
        """Apply filename filter based on comma-separated keywords"""
        filter_text = self.filename_filter_var.get().strip()
        if not filter_text:
            self.clear_filename_filter()
            return
        
        # Parse comma-separated keywords
        self.filename_keywords = [kw.strip().lower() for kw in filter_text.split(',') if kw.strip()]
        
        if not self.filename_keywords:
            self.clear_filename_filter()
            return
        
        # Apply all filters (combined)
        self.apply_filters()
    
    def clear_filename_filter(self):
        """Clear filename filter"""
        self.filename_keywords = []
        self.filename_filter_var.set('')
        
        # Reapply remaining filters
        self.apply_filters()
    
    def clear_filters(self):
        """Clear column-based filters only"""
        self.column_filters.clear()
        
        # Reapply remaining filters
        self.apply_filters()
    
    def clear_all_filters(self):
        """Clear all filters (filename + column)"""
        self.column_filters.clear()
        self.filename_keywords = []
        self.filename_filter_var.set('')
        
        # Remove filtered indices
        if hasattr(self, 'filtered_indices'):
            delattr(self, 'filtered_indices')
        
        self.populate_tree()
        self.status_var.set("All filters cleared")
    
    def select_filtered(self):
        """Select all filtered items"""
        if not hasattr(self, 'filtered_indices'):
            self.status_var.set("No filters applied")
            return
        
        for idx in self.filtered_indices:
            self.contents[idx].selected = True
        
        self.populate_tree()
        self.status_var.set(f"Selected {len(self.filtered_indices)} filtered items")
    
    def deselect_filtered(self):
        """Deselect all filtered items"""
        if not hasattr(self, 'filtered_indices'):
            self.status_var.set("No filters applied")
            return
        
        for idx in self.filtered_indices:
            self.contents[idx].selected = False
        
        self.populate_tree()
        self.status_var.set(f"Deselected {len(self.filtered_indices)} filtered items")
    
    def generate_nsh(self):
        """Generate .nsh file from selected content"""
        selected_contents = [c for c in self.contents if c.selected]
        
        if not selected_contents:
            messagebox.showwarning("Warning", "No content selected")
            return
        
        # Ask for output file
        output_file = filedialog.asksaveasfilename(
            title="Save NSH File",
            defaultextension=".nsh",
            filetypes=[("NSH files", "*.nsh"), ("All files", "*.*")]
        )
        
        if not output_file:
            return
        
        try:
            # Get mode
            mode = self.nsh_vars['mode'].get()
            is_framework = (mode == 'Framework')
            
            # Get variable values
            merlin_dir = self.nsh_vars['merlin_dir'].get()
            merlin = self.nsh_vars['merlin'].get()
            objpath = self.nsh_vars['objpath'].get()
            
            # If OBJPATH is not set, use the path from the first selected item
            if not objpath and selected_contents:
                objpath = selected_contents[0].get_base_path()
            
            # Ensure single backslashes in all paths
            merlin_dir = merlin_dir.replace('\\\\', '\\')
            objpath = objpath.replace('\\\\', '\\')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write initial commands
                f.write('echo -off\n\n')
                
                if is_framework:
                    f.write('############################################################\n')
                    f.write('# FRAMEWORK MODE\n')
                    f.write('# This NSH expects all variables to be set externally\n')
                    f.write('#\n')
                    f.write('# Required Variables:\n')
                    f.write('#   MERLIN_DIR     - Path to Merlin binaries directory\n')
                    f.write('#   MERLIN         - Merlin executable command\n')
                    f.write('#   VVAR0-5        - Dragon VVAR parameters\n')
                    f.write('#   VVAR_EXTRA     - Additional VVAR parameters\n')
                    f.write('#   VVARS          - Combined VVAR string\n')
                    f.write('#   DRG_STOP_ON_FAIL - Stop on fail flag (1/0)\n')
                    f.write('#\n')
                    f.write('# Usage: scriptname.nsh <objpath>\n')
                    f.write('# Parameter %1: Path to object files directory\n')
                    f.write('############################################################\n\n')
                else:
                    f.write('############################################################\n')
                    f.write('# NORMAL MODE\n')
                    f.write('# All variables are defined in this script\n')
                    f.write('############################################################\n\n')
                    
                    # Clean up VVARs at start (Normal mode only)
                    f.write('# Clean up VVAR variables\n')
                    for i in range(6):
                        f.write(f'if "%VVAR{i}%" neq "" then\n')
                        f.write(f'  echo "VVAR{i} removed"\n')
                        f.write(f'  set VVAR{i} ""\n')
                        f.write(f'else\n')
                        f.write(f'  echo "VVAR{i} not set"\n')
                        f.write(f'endif\n')
                    
                    f.write('if "%VVAR_EXTRA%" neq "" then\n')
                    f.write('  echo "VVAR_EXTRA removed"\n')
                    f.write('  set VVAR_EXTRA ""\n')
                    f.write('else\n')
                    f.write('  echo "VVAR_EXTRA not set"\n')
                    f.write('endif\n\n')
                
                if not is_framework:
                    # NORMAL MODE: Write variable definitions
                    f.write(f'set MERLIN_DIR "{merlin_dir}"\n')
                    f.write(f'set MERLIN "{merlin}"\n')
                    f.write(f'set OBJPATH "{objpath}"\n\n')
                    
                    # Get DRG_STOP_ON_FAIL from UI
                    stop_on_fail = self.nsh_vars['stop_on_fail'].get()
                    drg_stop_on_fail = 1 if stop_on_fail else 0
                    
                    f.write(f'set DRG_STOP_ON_FAIL {drg_stop_on_fail}\n')
                    f.write('set TEST_FAILED "false"\n\n')
                    
                    # Remove any existing .var, .miss, and log.txt files at start
                    f.write('# Clean up any existing .var, .miss, and log.txt files\n')
                    f.write('for %a in %OBJPATH%\\*.var\n')
                    f.write('  if exist %a then\n')
                    f.write('    rm %a\n')
                    f.write('  endif\n')
                    f.write('endfor\n')
                    f.write('for %a in %OBJPATH%\\*.miss\n')
                    f.write('  if exist %a then\n')
                    f.write('    rm %a\n')
                    f.write('  endif\n')
                    f.write('endfor\n')
                    f.write('if exist %OBJPATH%\\log.txt then\n')
                    f.write('  rm %OBJPATH%\\log.txt\n')
                    f.write('endif\n\n')
                    
                    # Get VVAR values
                    vvar0 = self.nsh_vars['vvar0'].get()
                    vvar1 = self.nsh_vars['vvar1'].get()
                    vvar2 = self.nsh_vars['vvar2'].get()
                    vvar3 = self.nsh_vars['vvar3'].get()
                    vvar4 = self.nsh_vars['vvar4'].get()
                    vvar5 = self.nsh_vars['vvar5'].get()
                    vvar_extra = self.nsh_vars['vvar_extra'].get()
                    
                    # Write individual VVAR definitions (only if they have values)
                    if vvar0:
                        f.write(f'set VVAR0 "{vvar0}"\n')
                    if vvar1:
                        f.write(f'set VVAR1 "{vvar1}"\n')
                    if vvar2:
                        f.write(f'set VVAR2 "{vvar2}"\n')
                    if vvar3:
                        f.write(f'set VVAR3 "{vvar3}"\n')
                    if vvar4:
                        f.write(f'set VVAR4 "{vvar4}"\n')
                    if vvar5:
                        f.write(f'set VVAR5 "{vvar5}"\n')
                    if vvar_extra:
                        f.write(f'set VVAR_EXTRA "{vvar_extra}"\n')
                    
                    # Build the VVARS string combining all VVARs
                    vvar_parts = []
                    if vvar0:
                        vvar_parts.extend(['0', '%VVAR0%'])
                    if vvar1:
                        vvar_parts.extend(['1', '%VVAR1%'])
                    if vvar2:
                        vvar_parts.extend(['2', '%VVAR2%'])
                    if vvar3:
                        vvar_parts.extend(['3', '%VVAR3%'])
                    if vvar4:
                        vvar_parts.extend(['4', '%VVAR4%'])
                    if vvar5:
                        vvar_parts.extend(['5', '%VVAR5%'])
                    if vvar_extra:
                        vvar_parts.append('%VVAR_EXTRA%')
                    
                    vvars_string = ' '.join(vvar_parts)
                    f.write(f'set VVARS "{vvars_string}"\n\n')
                else:
                    # FRAMEWORK MODE: OBJPATH from parameter %1
                    f.write('# OBJPATH is passed as parameter %1\n')
                    f.write('set OBJPATH "%1"\n')
                    f.write('set TEST_FAILED "false"\n\n')
                    
                    # Set DRG_STOP_ON_FAIL to 0 if not set
                    f.write('# Set DRG_STOP_ON_FAIL to 0 if not already set\n')
                    f.write('if "%DRG_STOP_ON_FAIL%" == "" then\n')
                    f.write('  set DRG_STOP_ON_FAIL 0\n')
                    f.write('endif\n\n')
                    
                    # Remove any existing .var, .miss, and log.txt files at start
                    f.write('# Clean up any existing .var, .miss, and log.txt files\n')
                    f.write('for %a in %OBJPATH%\\*.var\n')
                    f.write('  if exist %a then\n')
                    f.write('    rm %a\n')
                    f.write('  endif\n')
                    f.write('endfor\n')
                    f.write('for %a in %OBJPATH%\\*.miss\n')
                    f.write('  if exist %a then\n')
                    f.write('    rm %a\n')
                    f.write('  endif\n')
                    f.write('endfor\n')
                    f.write('if exist %OBJPATH%\\log.txt then\n')
                    f.write('  rm %OBJPATH%\\log.txt\n')
                    f.write('endif\n\n')
                    
                    # Build VVARS from available VVAR variables
                    f.write('# Build VVARS string from available VVAR variables\n')
                    f.write('set VVARS ""\n')
                    f.write('if "%VVAR0%" neq "" then\n')
                    f.write('  set VVARS "%VVARS% 0 %VVAR0%"\n')
                    f.write('endif\n')
                    f.write('if "%VVAR1%" neq "" then\n')
                    f.write('  set VVARS "%VVARS% 1 %VVAR1%"\n')
                    f.write('endif\n')
                    f.write('if "%VVAR2%" neq "" then\n')
                    f.write('  set VVARS "%VVARS% 2 %VVAR2%"\n')
                    f.write('endif\n')
                    f.write('if "%VVAR3%" neq "" then\n')
                    f.write('  set VVARS "%VVARS% 3 %VVAR3%"\n')
                    f.write('endif\n')
                    f.write('if "%VVAR4%" neq "" then\n')
                    f.write('  set VVARS "%VVARS% 4 %VVAR4%"\n')
                    f.write('endif\n')
                    f.write('if "%VVAR5%" neq "" then\n')
                    f.write('  set VVARS "%VVARS% 5 %VVAR5%"\n')
                    f.write('endif\n')
                    f.write('if "%VVAR_EXTRA%" neq "" then\n')
                    f.write('  set VVARS "%VVARS% %VVAR_EXTRA%"\n')
                    f.write('endif\n\n')
                
                # Write each selected content
                if is_framework:
                    # FRAMEWORK MODE: Process each selected content from UI
                    for idx, content in enumerate(selected_contents, start=1):
                        obj_filename = content.get_obj_filename()
                        f.write(f'## Seed {idx} - {obj_filename}\n')
                        f.write(f'set OBJFILE "{obj_filename}.obj"\n')
                        
                        # Check if .obj file exists before running
                        f.write(f'if exist %OBJPATH%\\%OBJFILE% then\n')
                        f.write(f'  echo " Running %OBJFILE%"\n')
                        f.write(f'  echo "Running %MERLIN_DIR%\\%MERLIN% -a %OBJPATH%\\%OBJFILE% -d %VVARS% "\n')
                        f.write(f'  echo "Running %MERLIN_DIR%\\%MERLIN% -a %OBJPATH%\\%OBJFILE% -d %VVARS%" >> %OBJPATH%\\log.txt\n')
                        f.write(f'  %MERLIN_DIR%\\%MERLIN% -a %OBJPATH%\\%OBJFILE% -d %VVARS%\n')
                        f.write(f'else\n')
                        f.write(f'  echo "%OBJFILE% not found" >> %OBJPATH%\\missing.miss\n')
                        f.write(f'endif\n\n')
                        
                        # Check for specific .var file indicating failure
                        f.write(f'# Check for .var file indicating failure\n')
                        f.write(f'if exist %OBJPATH%\\%OBJFILE%.var then\n')
                        f.write(f'  echo "Failure detected: %OBJFILE%.var"\n')
                        f.write(f'  set TEST_FAILED "true"\n')
                        f.write(f'  if %DRG_STOP_ON_FAIL% eq 1 then\n')
                        f.write(f'    goto END\n')
                        f.write(f'  endif\n')
                        f.write(f'endif\n\n')
                else:
                    # NORMAL MODE: Process each selected content
                    for idx, content in enumerate(selected_contents, start=1):
                        obj_filename = content.get_obj_filename()
                        f.write(f'## Seed {idx} - {obj_filename}\n')
                        f.write(f'set OBJFILE "{obj_filename}.obj"\n')
                        
                        # Check if .obj file exists before running
                        f.write(f'if exist %OBJPATH%\\%OBJFILE% then\n')
                        f.write(f'  echo " Running %OBJFILE%"\n')
                        f.write(f'  echo "Running %MERLIN_DIR%\\%MERLIN% -a %OBJPATH%\\%OBJFILE% -d %VVARS% "\n')
                        f.write(f'  echo "Running %MERLIN_DIR%\\%MERLIN% -a %OBJPATH%\\%OBJFILE% -d %VVARS%" >> %OBJPATH%\\log.txt\n')
                        f.write(f'  %MERLIN_DIR%\\%MERLIN% -a %OBJPATH%\\%OBJFILE% -d %VVARS%\n')
                        f.write(f'else\n')
                        f.write(f'  echo "%OBJFILE% not found" >> %OBJPATH%\\missing.miss\n')
                        f.write(f'endif\n\n')
                    
                        # Check for specific .var file indicating failure
                        f.write(f'# Check for .var file indicating failure\n')
                        f.write(f'if exist %OBJPATH%\\%OBJFILE%.var then\n')
                        f.write(f'  echo "Failure detected: %OBJFILE%.var"\n')
                        f.write(f'  set TEST_FAILED "true"\n')
                        f.write(f'  if %DRG_STOP_ON_FAIL% eq 1 then\n')
                        f.write(f'    goto END\n')
                        f.write(f'  endif\n')
                        f.write(f'endif\n\n')
                
                # Write END label with final status check
                f.write(':END\n')
                f.write('# Display missing files if any\n')
                f.write('if exist %OBJPATH%\\missing.miss then\n')
                f.write('  echo ""\n')
                f.write('  echo "==============================================="\n')
                f.write('  echo "Missing .obj files:"\n')
                f.write('  echo "==============================================="\n')
                f.write('  type %OBJPATH%\\missing.miss\n')
                f.write('  echo "==============================================="\n')
                f.write('  echo ""\n')
                f.write('endif\n\n')
                f.write('if "%TEST_FAILED%" == "true" then\n')
                f.write('  echo "Test Failed"\n')
                f.write('else\n')
                f.write('  echo "Test Complete"\n')
                f.write('endif\n')
            
            messagebox.showinfo("Success", f"NSH file generated successfully:\n{output_file}")
            self.status_var.set(f"Generated NSH file with {len(selected_contents)} entries")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate NSH file: {str(e)}")


def main():
    root = tk.Tk()
    app = DragonContentGUI(root)
    
    # Set default file if it exists
    default_file = Path(__file__).parent / "DragonContent.txt"
    if default_file.exists():
        app.file_entry.insert(0, str(default_file))
    
    root.mainloop()


if __name__ == "__main__":
    main()
