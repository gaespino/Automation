import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
import uuid
from datetime import datetime


current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

print(' Framework Automation Designer -- rev 1.8 (Standalone)')

sys.path.append(parent_dir)

# Standalone Excel/JSON loading functionality
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    print("Warning: openpyxl not available. Excel file loading will not work.")

def extract_data_from_named_table(sheet):
    """
    Extracts data from a named table within an Excel sheet.
    
    :param sheet: An openpyxl worksheet object from which data is to be extracted.
    :return: A dictionary containing 'Field' and 'Value' pairs if the table is found, otherwise None.
    """    
    # Iterate over all tables in the sheet
    for table in sheet.tables.values():
        # Get the table range
        table_range = sheet[table.ref]
        
        # Check if the first row contains 'Field' and 'Value'
        headers = [cell.value for cell in table_range[0]]
        if 'Field' in headers and 'Value' in headers:
            # Initialize a dictionary to store the values
            data = {}
            
            # Iterate over the rows starting from the second row
            for row in table_range[1:]:
                field = row[headers.index('Field')].value
                value = row[headers.index('Value')].value
                data[field] = value
            
            return data
    return None

def process_excel_file(file_path):
    """
    Processes an Excel file to extract data from named tables in each sheet.
    
    :param file_path: Path to the Excel file to be processed.
    :return: A dictionary containing data from all sheets, with sheet names as keys.
    """
    if not OPENPYXL_AVAILABLE:
        raise ImportError("openpyxl is required to load Excel files. Please install it with: pip install openpyxl")
    
    # Load the Excel file
    workbook = openpyxl.load_workbook(file_path, data_only=True)
    
    # Dictionary to store data from all sheets
    all_data = {}
    
    # Iterate over each sheet
    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
        data = extract_data_from_named_table(sheet)
        
        if data:
            all_data[sheet_name] = data
    
    return all_data

def load_json_file(file_path):
    """
    Load experiments from a JSON file.
    
    :param file_path: Path to the JSON file.
    :return: Dictionary of experiments.
    """
    with open(file_path, 'r') as json_file:
        experiments = json.load(json_file)
    return experiments

def load_experiments_from_file(file_path):
    """
    Load experiments from either Excel or JSON file.
    
    :param file_path: Path to the file (Excel or JSON).
    :return: Dictionary of experiments.
    """
    if file_path.endswith('.json'):
        return load_json_file(file_path)
    elif file_path.endswith('.xlsx'):
        return process_excel_file(file_path)
    else:
        raise ValueError("Unsupported file format. Please use .json or .xlsx files.")

class AutomationFlowDesigner:
    """
    Interface for creating automation flows by arranging experiments into decision trees.
    Allows engineers to visually design automation flows and export to JSON.
    """
    
    def __init__(self, parent=None):
        # Flow data
        self.experiments = {}  # Loaded from Excel/JSON
        self.flow_nodes = {}   # Node definitions
        self.flow_structure = {}  # Structure definitions
        self.flow_config = {}  # INI-style configuration
        self.parent = parent

        # Unit configuration overrides
        self.unit_config = {
            'Visual ID': '',
            'Bucket': '',
            'COM Port': '',
            'IP Address': '',
            '600W Unit': False,
            'Check Core': None
        }

        # UI State
        self.selected_node = None
        self.connection_mode = False
        self.connection_start = None
        self.node_counter = 1
        self._updating_properties = False
        
        # Canvas settings
        self.canvas_width = 1200
        self.canvas_height = 800
        self.node_width = 150
        self.node_height = 100
        self.grid_size = 20
   
        # Create main window
        self.setup_main_window()
        self.create_widgets()
        
        # Initialize with welcome message
        self.log_message("Automation Flow Designer initialized")
        self.log_message("Load experiments to begin designing flows")
        
    def setup_main_window(self):
        """Setup the main designer window."""
        if self.parent:
            self.root = tk.Toplevel(self.parent)
        else:
            self.root = tk.Tk()
        self.root.title("Automation Flow Designer")
        self.root.geometry("1800x1000")
        self.root.minsize(1400, 800)
        
        # Configure grid for header
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # Header frame with teal color accent
        header_frame = tk.Frame(self.root, bg='#1abc9c', height=12)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)
        
        # Configure styles
        self.setup_styles()

    def setup_styles(self):
        """Configure ttk styles."""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Node colors - Modern flat design matching PPV theme
        self.node_colors = {
            'SingleFailFlowInstance': '#ecf0f1',      # Light gray (modern flat)
            'AllFailFlowInstance': '#ecf0f1',         # Light gray (modern flat)
            'MajorityFailFlowInstance': '#ecf0f1',    # Light gray (modern flat)
            'AdaptiveFlowInstance': '#ecf0f1',        # Light gray (modern flat)
            'CharacterizationFlowInstance': '#ecf0f1', # Light gray (modern flat)
            'DataCollectionFlowInstance': '#ecf0f1',   # Light gray (modern flat)
            'AnalysisFlowInstance': '#ecf0f1',        # Light gray (modern flat)
            'StartNode': '#1abc9c',                   # Turquoise for start (PPV theme)
            'EndNode': '#e74c3c'                      # Red for end (PPV theme)
        }
        
        # Text colors for better contrast
        self.node_text_colors = {
            'SingleFailFlowInstance': '#2c3e50',
            'AllFailFlowInstance': '#2c3e50',
            'MajorityFailFlowInstance': '#2c3e50',
            'AdaptiveFlowInstance': '#2c3e50',
            'CharacterizationFlowInstance': '#2c3e50',
            'DataCollectionFlowInstance': '#2c3e50',
            'AnalysisFlowInstance': '#2c3e50',
            'StartNode': 'white',
            'EndNode': 'white'
        }
        
        # Connection colors for different ports - PPV theme colors
        self.connection_colors = {
            0: '#1abc9c',  # Turquoise for success path
            1: '#e74c3c',  # Red for failure path
            2: '#f39c12',  # Orange for alternative path
            3: '#9b59b6'   # Purple for error path
        }

    def create_widgets(self):
        """Create the main UI layout."""
        # Main horizontal container (placed below header at row=1)
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Left side - Unit Configuration
        self.unit_config_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.unit_config_frame, weight=1)
        
        # Middle - Design canvas
        self.canvas_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.canvas_frame, weight=4)
        
        # Right side - Properties and tools
        self.right_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_frame, weight=1)
        
        self.create_unit_config_panel()
        self.create_canvas_panel()
        self.create_right_panel()

    def create_unit_config_panel(self):
        """Create the unit configuration panel."""
        # Menu bar at top of left panel
        menu_frame = ttk.Frame(self.unit_config_frame)
        menu_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # File menu button
        file_menu_btn = ttk.Menubutton(menu_frame, text="File", direction='below', width=15)
        file_menu_btn.pack(fill=tk.X, pady=2)
        file_menu = tk.Menu(file_menu_btn, tearoff=0)
        file_menu_btn.config(menu=file_menu)
        file_menu.add_command(label="New Flow", command=self.new_flow)
        file_menu.add_command(label="Load Flow", command=self.load_flow_design)
        file_menu.add_command(label="Save Flow", command=self.save_flow)
        file_menu.add_command(label="Export Flow", command=self.export_flow)
        file_menu.add_separator()
        file_menu.add_command(label="Import Config", command=self.import_flow_config)
        
        # Experiments menu button
        exp_menu_btn = ttk.Menubutton(menu_frame, text="Experiments", direction='below', width=15)
        exp_menu_btn.pack(fill=tk.X, pady=2)
        exp_menu = tk.Menu(exp_menu_btn, tearoff=0)
        exp_menu_btn.config(menu=exp_menu)
        exp_menu.add_command(label="Load Experiments", command=self.load_experiments)
        
        # Unit Configuration Frame
        unit_frame = ttk.LabelFrame(self.unit_config_frame, text="Unit Configuration", padding=10)
        unit_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Visual ID
        ttk.Label(unit_frame, text="Visual ID").pack(anchor="w")
        self.visual_id_var = tk.StringVar()
        self.visual_id_entry = ttk.Entry(unit_frame, textvariable=self.visual_id_var, width=20)
        self.visual_id_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Bucket
        ttk.Label(unit_frame, text="Bucket").pack(anchor="w")
        self.bucket_var = tk.StringVar()
        self.bucket_entry = ttk.Entry(unit_frame, textvariable=self.bucket_var, width=20)
        self.bucket_entry.pack(fill=tk.X, pady=(0, 10))
        
        # COM Port
        ttk.Label(unit_frame, text="COM Port").pack(anchor="w")
        self.com_port_var = tk.StringVar()
        self.com_port_entry = ttk.Entry(unit_frame, textvariable=self.com_port_var, width=20)
        self.com_port_entry.pack(fill=tk.X, pady=(0, 10))
        
        # IP Address
        ttk.Label(unit_frame, text="IP Address").pack(anchor="w")
        self.ip_address_var = tk.StringVar()
        self.ip_address_entry = ttk.Entry(unit_frame, textvariable=self.ip_address_var, width=20)
        self.ip_address_entry.pack(fill=tk.X, pady=(0, 10))
        
        # 600W Unit
        self.unit_600w_var = tk.BooleanVar()
        self.unit_600w_check = ttk.Checkbutton(unit_frame, text="600W Unit", 
                                              variable=self.unit_600w_var)
        self.unit_600w_check.pack(anchor="w", pady=(0, 10))
        
        # Check Core
        ttk.Label(unit_frame, text="Check Core").pack(anchor="w")
        self.check_core_var = tk.StringVar()
        self.check_core_entry = ttk.Entry(unit_frame, textvariable=self.check_core_var, width=20)
        self.check_core_entry.pack(fill=tk.X, pady=(0, 20))
        
        # Bind events to update unit config
        for var in [self.visual_id_var, self.bucket_var, self.com_port_var, 
                   self.ip_address_var, self.unit_600w_var, self.check_core_var]:
            if isinstance(var, tk.BooleanVar):
                var.trace('w', self.update_unit_config)
            else:
                var.trace('w', self.update_unit_config)

    def create_canvas_panel(self):
        """Create the design canvas panel."""
        # Title
        title_frame = ttk.Frame(self.canvas_frame)
        title_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        ttk.Label(title_frame, text="Automation Flow Designer", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        # Canvas toolbar - Design tools (compact, always visible)
        canvas_toolbar = ttk.Frame(self.canvas_frame)
        canvas_toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        # Canvas tools - no label frame for more compact design
        self.connection_button = ttk.Button(canvas_toolbar, text="Connect Nodes", 
                                          command=self.toggle_connection_mode, width=13)
        self.connection_button.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(canvas_toolbar, text="Auto Layout", command=self.auto_layout_nodes, width=13).pack(side=tk.LEFT, padx=2)
        ttk.Button(canvas_toolbar, text="Validate Flow", command=self.validate_flow, width=13).pack(side=tk.LEFT, padx=2)
        ttk.Button(canvas_toolbar, text="Preview Flow", command=self.preview_flow, width=13).pack(side=tk.LEFT, padx=2)
        
        # Status bar
        status_frame = ttk.Frame(self.canvas_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=2)
        
        self.status_label = ttk.Label(status_frame, text="Ready - Load experiments to begin")
        self.status_label.pack(side=tk.LEFT)
        
        self.mode_label = ttk.Label(status_frame, text="Mode: Design")
        self.mode_label.pack(side=tk.RIGHT)
        
        # Canvas frame with scrollbars
        canvas_container = ttk.Frame(self.canvas_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create canvas with scrollbars
        self.canvas = tk.Canvas(canvas_container, bg='#f0f0f0', highlightthickness=0,
                               scrollregion=(0, 0, self.canvas_width, self.canvas_height))
        
        v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_container, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack canvas and scrollbars
        self.canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Bind canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        
        # Draw grid
        self.draw_grid()

    def create_default_experiment(self):
        """Create a default experiment configuration."""
        return {
            "Experiment": "Enabled",
            "Test Name": "NewTest",
            "Test Mode": "Mesh",
            "Test Type": "Loops",
            "Visual ID": "TestUnitData",
            "Bucket": "IDIPAR",
            "COM Port": 11,
            "IP Address": "192.168.0.2",
            "TTL Folder": "R:\\Templates\\GNR\\version_2_0\\TTL_DragonMesh",
            "Scripts File": None,
            "Post Process": None,
            "Pass String": "Test Complete",
            "Fail String": "Test Failed",
            "Content": "Dragon",
            "Test Number": 11,
            "Test Time": 30,
            "Reset": True,
            "Reset on PASS": True,
            "FastBoot": True,
            "Core License": None,
            "600W Unit": False,
            "Pseudo Config": False,
            "Configuration (Mask)": None,
            "Boot Breakpoint": None,
            "Disable 2 Cores": None,
            "Check Core": 7,
            "Voltage Type": "vbump",
            "Voltage IA": None,
            "Voltage CFC": None,
            "Frequency IA": None,
            "Frequency CFC": None,
            "Loops": 2,
            "Type": "Voltage",
            "Domain": "IA",
            "Start": -0.03,
            "End": 0.06,
            "Steps": 0.03,
            "ShmooFile": "C:\\SystemDebug\\Shmoos\\RVPShmooConfig.json",
            "ShmooLabel": "COREFIX",
            "Linux Pre Command": None,
            "Linux Post Command": None,
            "Linux Pass String": None,
            "Linux Fail String": None,
            "Startup Linux": None,
            "Linux Path": None,
            "Linux Content Wait Time": None,
            "Linux Content Line 0": None,
            "Linux Content Line 1": None,
            "Linux Content Line 2": None,
            "Linux Content Line 3": None,
            "Linux Content Line 4": None,
            "Linux Content Line 5": None,
            "Dragon Pre Command": "dosome.nsh",
            "Dragon Post Command": "more.nsh",
            "Startup Dragon": "startup_efi.nsh",
            "ULX Path": "FS1:\\EFI\\ulx",
            "ULX CPU": "GNR_B0",
            "Product Chop": "GNR",
            "VVAR0": "0x4C4B40",
            "VVAR1": 80064000,
            "VVAR2": "0x1000000",
            "VVAR3": "0x4000000",
            "VVAR_EXTRA": None,
            "Dragon Content Path": "FS1:\\content\\Dragon\\7410_0x0E_PPV_MM\\GNR128C_H_1UP\\",
            "Dragon Content Line": "Demo, Yakko, Sanity",
            "Stop on Fail": True,
            "Merlin Name": "MerlinX.efi",
            "Merlin Drive": "FS1:",
            "Merlin Path": "FS1:\\EFI\\Version8.15\\BinFiles\\Release"
        }

    def create_right_panel(self):
        """Create the properties and tools panel."""
        # Node palette with 3-column layout
        palette_frame = ttk.LabelFrame(self.right_frame, text="Node Palette", padding=10)
        palette_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Configure grid columns to expand equally
        palette_frame.columnconfigure(0, weight=1)
        palette_frame.columnconfigure(1, weight=1)
        palette_frame.columnconfigure(2, weight=1)
        
        # Node type buttons with better descriptions
        node_types = [
            ("Start Node", "StartNode", "Flow entry point - no experiment"),
            ("Single Fail", "SingleFailFlowInstance", "Stops on first failure"),
            ("All Fail", "AllFailFlowInstance", "Requires all tests to fail"),
            ("Majority Fail", "MajorityFailFlowInstance", "Routes based on majority"),
            ("Adaptive", "AdaptiveFlowInstance", "Intelligent decision making"),
            ("Characterization", "CharacterizationFlowInstance", "Uses previous data for experiments"),
            ("Data Collection", "DataCollectionFlowInstance", "Runs complete experiment data collection"),
            ("Analysis", "AnalysisFlowInstance", "Generates summary and experiment proposals"),
            ("End Node", "EndNode", "Flow exit point - no experiment")
        ]
        
        # Arrange buttons in 3 columns
        for idx, (display_name, class_name, tooltip) in enumerate(node_types):
            row = idx // 3
            col = idx % 3
            btn = ttk.Button(palette_frame, text=display_name,
                           command=lambda cn=class_name: self.add_node(cn))
            btn.grid(row=row, column=col, sticky="ew", padx=2, pady=2)
            # Add tooltip (simplified)
            btn.bind("<Enter>", lambda e, tip=tooltip: self.show_tooltip(tip))
        
        # Experiments list
        experiments_frame = ttk.LabelFrame(self.right_frame, text="Available Experiments", padding=10)
        experiments_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Experiments listbox with scrollbar
        list_frame = ttk.Frame(experiments_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.experiments_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        exp_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.experiments_listbox.yview)
        self.experiments_listbox.configure(yscrollcommand=exp_scrollbar.set)
        
        self.experiments_listbox.pack(side="left", fill="both", expand=True)
        exp_scrollbar.pack(side="right", fill="y")
        
        self.experiments_listbox.bind("<Double-Button-1>", self.on_experiment_double_click)
        
        # Properties panel
        properties_frame = ttk.LabelFrame(self.right_frame, text="Node Properties", padding=10)
        properties_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Node ID
        ttk.Label(properties_frame, text="Node ID:").pack(anchor="w")
        self.node_id_var = tk.StringVar()
        self.node_id_entry = ttk.Entry(properties_frame, textvariable=self.node_id_var, state='readonly')
        self.node_id_entry.pack(fill=tk.X, pady=(0, 5))
        
        # Node Name
        ttk.Label(properties_frame, text="Node Name:").pack(anchor="w")
        self.node_name_var = tk.StringVar()
        self.node_name_entry = ttk.Entry(properties_frame, textvariable=self.node_name_var)
        self.node_name_entry.pack(fill=tk.X, pady=(0, 5))
        self.node_name_entry.bind("<KeyRelease>", self.on_property_change)
        
        # Node Type
        ttk.Label(properties_frame, text="Node Type:").pack(anchor="w")
        self.node_type_var = tk.StringVar()
        self.node_type_combo = ttk.Combobox(properties_frame, textvariable=self.node_type_var,
                                           values=list(self.node_colors.keys()), state='readonly')
        self.node_type_combo.pack(fill=tk.X, pady=(0, 5))
        self.node_type_combo.bind("<<ComboboxSelected>>", self.on_property_change)
        
        # Experiment Assignment
        ttk.Label(properties_frame, text="Assigned Experiment:").pack(anchor="w")
        self.assigned_exp_var = tk.StringVar()
        self.assigned_exp_combo = ttk.Combobox(properties_frame, textvariable=self.assigned_exp_var,
                                              state='readonly')
        self.assigned_exp_combo.pack(fill=tk.X, pady=(0, 10))
        self.assigned_exp_combo.bind("<<ComboboxSelected>>", self.on_property_change)
        
        # Action buttons
        ttk.Button(properties_frame, text="Edit Experiment", 
                  command=self.edit_node_experiment).pack(fill=tk.X, pady=2)
        ttk.Button(properties_frame, text="Delete Node", 
                  command=self.delete_selected_node).pack(fill=tk.X, pady=2)
        ttk.Button(properties_frame, text="Clear Selection", 
                  command=self.clear_selection).pack(fill=tk.X, pady=2)
        
        # Log panel
        log_frame = ttk.LabelFrame(self.right_frame, text="Messages", padding=5)
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, bg="#2c3e50", fg="white", 
                               font=("Consolas", 9), wrap=tk.WORD, state=tk.DISABLED)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

    def update_unit_config(self, *args):
        """Update unit configuration from UI."""
        self.unit_config = {
            'Visual ID': self.visual_id_var.get(),
            'Bucket': self.bucket_var.get(),
            'COM Port': self.com_port_var.get(),
            'IP Address': self.ip_address_var.get(),
            '600W Unit': self.unit_600w_var.get(),
            'Check Core': self.check_core_var.get()
        }

    def import_flow_config(self):
        """Import flow configuration from existing files."""
        # Select folder containing configuration files
        folder_path = filedialog.askdirectory(title="Select Flow Configuration Folder")
        
        if not folder_path:
            return
        
        try:
            # Look for the three required files
            structure_file = os.path.join(folder_path, "FrameworkAutomationStructure.json")
            flows_file = os.path.join(folder_path, "FrameworkAutomationFlows.json")
            ini_file = os.path.join(folder_path, "FrameworkAutomationInit.ini")
            
            # Check if files exist
            missing_files = []
            if not os.path.exists(structure_file):
                missing_files.append("FrameworkAutomationStructure.json")
            if not os.path.exists(flows_file):
                missing_files.append("FrameworkAutomationFlows.json")
            if not os.path.exists(ini_file):
                missing_files.append("FrameworkAutomationInit.ini")
            
            if missing_files:
                messagebox.showerror("Missing Files", 
                                   "The following required files are missing:\n" + 
                                   "\n".join(f"• {f}" for f in missing_files))
                return
            
            # Load structure file
            with open(structure_file, 'r') as f:
                structure_data = json.load(f)
            
            # Load flows file
            with open(flows_file, 'r') as f:
                flows_data = json.load(f)
            
            # Convert to internal format
            self.flow_nodes = {}
            self.experiments = flows_data
            
            # Convert structure to nodes
            for node_id, node_config in structure_data.items():
                # Calculate position (will be auto-layouted later)
                x = 100 + (len(self.flow_nodes) % 3) * 220
                y = 100 + (len(self.flow_nodes) // 3) * 180
                
                # Create node data
                node_data = {
                    'id': node_id,
                    'name': node_config.get('name', node_id),
                    'type': node_config.get('instanceType', 'SingleFailFlowInstance'),
                    'x': x,
                    'y': y,
                    'experiment': node_config.get('flow') if node_config.get('flow') != 'default' else None,
                    'connections': {}
                }
                
                # Convert output connections
                output_map = node_config.get('outputNodeMap', {})
                for port, target_id in output_map.items():
                    node_data['connections'][int(port)] = target_id
                
                self.flow_nodes[node_id] = node_data
            
            # Update node counter to max existing node ID + 1 to avoid overrides
            max_node_num = 0
            for node_id in self.flow_nodes.keys():
                if node_id.startswith('NODE_'):
                    try:
                        node_num = int(node_id.split('_')[1])
                        max_node_num = max(max_node_num, node_num)
                    except (IndexError, ValueError):
                        pass
            self.node_counter = max_node_num + 1
            
            # Update experiments listbox
            self.experiments_listbox.delete(0, tk.END)
            for exp_name in self.experiments.keys():
                self.experiments_listbox.insert(tk.END, exp_name)
            
            # Update experiment combo in properties
            exp_names = ["None"] + list(self.experiments.keys())
            self.assigned_exp_combo.configure(values=exp_names)
            
            # Check for positions file and load if available
            positions_file = os.path.join(folder_path, "FrameworkAutomationPositions.json")
            positions_loaded = False
            if os.path.exists(positions_file):
                try:
                    with open(positions_file, 'r') as f:
                        positions_data = json.load(f)
                    
                    # Apply saved positions
                    for node_id, pos in positions_data.items():
                        if node_id in self.flow_nodes:
                            self.flow_nodes[node_id]['x'] = pos['x']
                            self.flow_nodes[node_id]['y'] = pos['y']
                    
                    positions_loaded = True
                    self.log_message("Loaded saved node positions", "success")
                except Exception as e:
                    self.log_message(f"Could not load positions: {str(e)}", "warning")
            
            # Draw nodes (use saved positions or auto-layout)
            if positions_loaded:
                for node_data in self.flow_nodes.values():
                    self.draw_node(node_data)
                self.draw_connections()
            else:
                # Auto-layout if no positions file
                self.auto_layout_nodes()
            
            # Ensure canvas scroll region is updated
            self._update_canvas_scroll_region()
            
            position_msg = " (positions restored)" if positions_loaded else " (auto-layouted)"
            self.log_message(f"Imported flow configuration with {len(self.flow_nodes)} nodes{position_msg}", "success")
            self.status_label.configure(text=f"Imported {len(self.flow_nodes)} nodes - Ready to edit")
            
        except Exception as e:
            self.log_message(f"Error importing configuration: {str(e)}", "error")
            messagebox.showerror("Import Error", f"Failed to import configuration:\n{str(e)}")

    def load_flow_design(self):
        """Load a previously saved flow design."""
        file_path = filedialog.askopenfilename(
            title="Load Flow Design",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                flow_design = json.load(f)
            
            # Load flow data
            self.flow_nodes = flow_design.get('nodes', {})
            self.experiments = flow_design.get('experiments', {})
            
            # Load metadata
            metadata = flow_design.get('metadata', {})
            
            # Calculate node_counter from max existing node ID to avoid overrides
            max_node_num = 0
            for node_id in self.flow_nodes.keys():
                if node_id.startswith('NODE_'):
                    try:
                        node_num = int(node_id.split('_')[1])
                        max_node_num = max(max_node_num, node_num)
                    except (IndexError, ValueError):
                        pass
            self.node_counter = max(metadata.get('node_counter', 0), max_node_num + 1)
            
            # Load unit config if available
            if 'unit_config' in flow_design:
                unit_config = flow_design['unit_config']
                self.visual_id_var.set(unit_config.get('Visual ID', ''))
                self.bucket_var.set(unit_config.get('Bucket', ''))
                self.com_port_var.set(unit_config.get('COM Port', ''))
                self.ip_address_var.set(unit_config.get('IP Address', ''))
                self.unit_600w_var.set(unit_config.get('600W Unit', False))
                self.check_core_var.set(unit_config.get('Check Core', None))
            
            # Update UI
            self.experiments_listbox.delete(0, tk.END)
            for exp_name in self.experiments.keys():
                self.experiments_listbox.insert(tk.END, exp_name)
            
            exp_names = ["None"] + list(self.experiments.keys())
            self.assigned_exp_combo.configure(values=exp_names)
            
            # Draw the flow
            for node_data in self.flow_nodes.values():
                self.draw_node(node_data)
            self.draw_connections()
            
            # Update canvas scroll region to include all nodes
            self._update_canvas_scroll_region()
            
            self.log_message(f"Loaded flow design with {len(self.flow_nodes)} nodes", "success")
            self.status_label.configure(text=f"Loaded {len(self.flow_nodes)} nodes - Ready to edit")
            
        except Exception as e:
            self.log_message(f"Error loading flow design: {str(e)}", "error")
            messagebox.showerror("Load Error", f"Failed to load flow design:\n{str(e)}")

    def open_experiment_editor(self, exp_name, exp_data):
        """Open the experiment editor dialog."""
        editor = ExperimentEditor(
                                    parent=self.root, 
                                    exp_name=exp_name, 
                                    exp_data=exp_data, 
                                    unit_config=self.unit_config,
                                    save_callback=self.save_experiment_changes, 
                                    existing_experiments=self.experiments
                                    )
        editor.show()

    def save_experiment_changes(self, exp_name, updated_data):
        """Save changes from experiment editor."""
        # Get the original experiment name from the selected node
        original_exp_name = None
        if self.selected_node:
            node_data = self.flow_nodes[self.selected_node]
            original_exp_name = node_data.get('experiment')
        
        # Update experiments dictionary with new experiment
        self.experiments[exp_name] = updated_data
        
        # Update node to point to new experiment name
        if self.selected_node:
            node_data = self.flow_nodes[self.selected_node]
            node_data['experiment'] = exp_name
            
            # Redraw node to show updated experiment
            self.draw_node(node_data)
            self.draw_connections()
            
            # Update properties panel
            self.assigned_exp_var.set(exp_name)
        
        # Update experiments listbox
        self.experiments_listbox.delete(0, tk.END)
        for name in sorted(self.experiments.keys()):
            self.experiments_listbox.insert(tk.END, name)
        
        # Update experiment combo
        exp_names = ["None"] + sorted(list(self.experiments.keys()))
        self.assigned_exp_combo.configure(values=exp_names)
        
        # Log the action
        if original_exp_name and original_exp_name != exp_name:
            self.log_message(f"Created new experiment: {exp_name} (based on {original_exp_name})", "success")
        elif original_exp_name == exp_name:
            self.log_message(f"Updated experiment: {exp_name}", "success")
        else:
            self.log_message(f"Created new experiment: {exp_name}", "success")

    def generate_unique_experiment_name(self, base_name):
        """Generate a unique experiment name by appending numbers if needed."""
        if base_name not in self.experiments:
            return base_name
        
        counter = 1
        while f"{base_name}_{counter}" in self.experiments:
            counter += 1
        
        return f"{base_name}_{counter}"
           
    def draw_grid(self):
        """Draw grid on canvas for alignment."""
        self.canvas.delete("grid")
        
        # Vertical lines
        for x in range(0, self.canvas_width, self.grid_size):
            self.canvas.create_line(x, 0, x, self.canvas_height, 
                                   fill="#E0E0E0", tags="grid")
        
        # Horizontal lines  
        for y in range(0, self.canvas_height, self.grid_size):
            self.canvas.create_line(0, y, self.canvas_width, y, 
                                   fill="#E0E0E0", tags="grid")
            
    def load_experiments(self):
        """Load experiments from Excel or JSON file."""
        file_path = filedialog.askopenfilename(
            title="Load Experiments",
            filetypes=[("Excel files", "*.xlsx"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # Load experiments using standalone functions
            self.experiments = load_experiments_from_file(file_path)
            
            # Update experiments listbox
            self.experiments_listbox.delete(0, tk.END)
            for exp_name in self.experiments.keys():
                self.experiments_listbox.insert(tk.END, exp_name)
            
            # Update experiment combo in properties
            exp_names = ["None"] + list(self.experiments.keys())
            self.assigned_exp_combo.configure(values=exp_names)
            
            self.log_message(f"Loaded {len(self.experiments)} experiments from {os.path.basename(file_path)}", "success")
            self.status_label.configure(text=f"Loaded {len(self.experiments)} experiments - Ready to design")
            
        except Exception as e:
            self.log_message(f"Error loading experiments: {str(e)}", "error")
            messagebox.showerror("Load Error", f"Failed to load experiments:\n{str(e)}")
            
    def add_node(self, node_type: str, x: int = None, y: int = None):
        """Add a new node to the canvas."""
        if not self.experiments and node_type not in ['StartNode', 'EndNode']:
            self.log_message("Please load experiments before adding flow nodes", "warning")
            return
        
        # Generate unique node ID
        node_id = f"NODE_{self.node_counter:03d}"
        self.node_counter += 1
        
        # Default position
        if x is None or y is None:
            x = 100 + (len(self.flow_nodes) % 5) * 200
            y = 100 + (len(self.flow_nodes) // 5) * 150
        
        # Snap to grid
        x = round(x / self.grid_size) * self.grid_size
        y = round(y / self.grid_size) * self.grid_size
        
        # Create node data
        node_data = {
            'id': node_id,
            'name': f"{node_type}_{self.node_counter-1}",
            'type': node_type,
            'x': x,
            'y': y,
            'experiment': None,
            'connections': {}  # port -> target_node_id
        }
        
        self.flow_nodes[node_id] = node_data
        
        # Draw node on canvas
        self.draw_node(node_data)
        
        # Select the new node
        self.select_node(node_id)
        
        self.log_message(f"Added {node_type} node: {node_id}")

    def _get_display_name(self, node_type):
        """Get display name for node type."""
        display_names = {
            'StartNode': 'Start',
            'EndNode': 'End',
            'SingleFailFlowInstance': 'SingleFail',
            'AllFailFlowInstance': 'AllFail',
            'MajorityFailFlowInstance': 'MajorityFail',
            'AdaptiveFlowInstance': 'Adaptive',
            'CharacterizationFlowInstance': 'Characterization',
            'DataCollectionFlowInstance': 'DataCollection',
            'AnalysisFlowInstance': 'Analysis'
        }
        return display_names.get(node_type, node_type)

    def draw_node(self, node_data: Dict):
        """Draw a node using the execution interface style."""
        node_id = node_data['id']
        x, y = node_data['x'], node_data['y']
        node_type = node_data['type']
        
        # Remove existing node graphics
        self.canvas.delete(f"node_{node_id}")
        
        # Node styling
        bg_color = self.node_colors.get(node_type, '#E8E8E8')
        text_color = self.node_text_colors.get(node_type, 'black')
        
        # Special styling for start/end nodes
        border_color = 'black'
        border_width = 2
        
        if node_type == "StartNode":
            border_color = '#2E7D32'  # Dark green
            border_width = 3
        elif node_type == "EndNode":
            border_color = '#C62828'  # Dark red
            border_width = 3
        
        # Draw main rectangle
        rect = self.canvas.create_rectangle(
            x, y, x + self.node_width, y + self.node_height,
            fill=bg_color, outline=border_color, width=border_width,
            tags=f"node_{node_id}"
        )
        
        # Draw status indicator (top-left corner)
        indicator_size = 20
        indicator_x = x + 8
        indicator_y = y + 8
        
        indicator_color = '#CCCCCC'  # Default idle color
        if node_type == "StartNode":
            indicator_color = '#4CAF50'  # Green
        elif node_type == "EndNode":
            indicator_color = '#F44336'  # Red
        
        indicator = self.canvas.create_oval(
            indicator_x, indicator_y,
            indicator_x + indicator_size, indicator_y + indicator_size,
            fill=indicator_color, outline='black', width=2,
            tags=f"node_{node_id}"
        )
        
        # Status symbol
        symbol_map = {
            'StartNode': '▶',
            'EndNode': '■',
            'SingleFailFlowInstance': '○',
            'AllFailFlowInstance': '○',
            'MajorityFailFlowInstance': '○',
            'AdaptiveFlowInstance': '○',
            'CharacterizationFlowInstance': '◐',  # Half-filled circle for characterization
            'DataCollectionFlowInstance': '●',    # Filled circle for data collection
            'AnalysisFlowInstance': '◆'           # Diamond for analysis
        }
        
        symbol = symbol_map.get(node_type, '○')
        symbol_color = 'white' if node_type in ['StartNode', 'EndNode'] else 'black'
        
        symbol_text = self.canvas.create_text(
            indicator_x + indicator_size // 2,
            indicator_y + indicator_size // 2,
            text=symbol, fill=symbol_color,
            font=("Arial", 10, "bold"),
            tags=f"node_{node_id}"
        )
        
        # Node name (larger, bold)
        name_text = self.canvas.create_text(
            x + self.node_width // 2, y + 35,
            text=node_data['name'], fill=text_color,
            font=("Arial", 10, "bold"),
            width=self.node_width - 10,
            tags=f"node_{node_id}"
        )
        
        # Node ID
        id_text = self.canvas.create_text(
            x + self.node_width // 2, y + 55,
            text=f"ID: {node_id}", fill=text_color,
            font=("Arial", 8),
            tags=f"node_{node_id}"
        )
        
        # Instance type (cleaned up)
        type_display = node_type.replace('FlowInstance', '').replace('Node', '')
        if not type_display:
            type_display = "Flow"
        
        type_text = self.canvas.create_text(
            x + self.node_width // 2, y + 72,
            text=type_display, fill=text_color,
            font=("Arial", 8, "italic"),
            tags=f"node_{node_id}"
        )
        
        # Experiment info (only for non-start/end nodes)
        if node_type not in ['StartNode', 'EndNode']:
            exp_name = node_data.get('experiment', 'No Experiment')
            if exp_name and exp_name != 'None':
                exp_display = exp_name[:15] + "..." if len(exp_name) > 15 else exp_name
                exp_color = 'blue' if text_color == 'black' else 'lightblue'
            else:
                exp_display = "No Experiment"
                exp_color = 'gray'
            
            exp_text = self.canvas.create_text(
                x + self.node_width // 2, y + 92,
                text=exp_display, fill=exp_color,
                font=("Arial", 7), width=self.node_width - 10,
                tags=f"node_{node_id}"
            )
        else:
            # For start/end nodes, show their purpose
            purpose_text = "Entry Point" if node_type == "StartNode" else "Exit Point"
            purpose_display = self.canvas.create_text(
                x + self.node_width // 2, y + 92,
                text=purpose_text, fill='gray',
                font=("Arial", 8, "italic"),
                tags=f"node_{node_id}"
            )
        
        # Draw connection ports
        self.draw_connection_ports(node_data)
        
        # Store canvas items for this node
        node_data['canvas_items'] = [rect, indicator, symbol_text, name_text, id_text, type_text]

    def draw_connection_ports(self, node_data: Dict):
        """Draw connection ports matching execution interface style."""
        node_id = node_data['id']
        x, y = node_data['x'], node_data['y']
        node_type = node_data['type']
        

        # Output ports (bottom of node) - only for non-end nodes
        if node_type != 'EndNode':
            port_size = 10
            port_spacing = 25
            
            # Determine number of ports based on node type
            if node_type == 'StartNode':
                ports = [0]  # Start node only has success path
            elif node_type in ['CharacterizationFlowInstance', 'DataCollectionFlowInstance', 'AnalysisFlowInstance', 'AdaptiveFlowInstance']:
                ports = [0, 3]  # New nodes only use Port 0 and Port 3 (error)
            else:
                ports = [0, 1, 2, 3]  # Regular nodes have all ports
            
            # Calculate starting position to center ports
            total_width = len(ports) * port_spacing
            start_x = x + (self.node_width - total_width) // 2 + port_spacing // 2
            port_y = y + self.node_height - port_size - 5
            
            for i, port in enumerate(ports):
                port_x = start_x + i * port_spacing
                port_color = self.connection_colors.get(port, '#666666')
                
                # Port rectangle
                port_rect = self.canvas.create_rectangle(
                    port_x, port_y,
                    port_x + port_size, port_y + port_size,
                    fill=port_color, outline='black', width=1,
                    tags=f"node_{node_id}"
                )
                
                # Port number
                port_text = self.canvas.create_text(
                    port_x + port_size//2, port_y + port_size//2,
                    text=str(port), fill='white',
                    font=("Arial", 6, "bold"),
                    tags=f"node_{node_id}"
                )
        
        # Input port (top of node) - only for non-start nodes
        if node_type != 'StartNode':
            input_port_size = 8
            input_port = self.canvas.create_rectangle(
                x + self.node_width//2 - input_port_size//2, y - 2,
                x + self.node_width//2 + input_port_size//2, y + input_port_size - 2,
                fill='gray', outline='black', width=1,
                tags=f"node_{node_id}"
            )

    def draw_connections(self):
        """Draw all connections between nodes with top-to-bottom routing."""
        self.canvas.delete("connection")
        
        # Group connections by node pairs to handle multiple connections
        connection_groups = {}
        for node_id, node_data in self.flow_nodes.items():
            for port, target_id in node_data.get('connections', {}).items():
                if target_id in self.flow_nodes:
                    key = (node_id, target_id)
                    if key not in connection_groups:
                        connection_groups[key] = []
                    connection_groups[key].append(int(port))
        
        # Draw each connection with appropriate offset for multiple connections
        for (from_node_id, to_node_id), ports in connection_groups.items():
            sorted_ports = sorted(ports)
            max_port = max(sorted_ports)  # Use highest port for line color
            for idx, port in enumerate(sorted_ports):
                self.draw_connection(from_node_id, port, to_node_id, idx, len(ports), max_port)

    def draw_connection(self, from_node_id: str, port: int, to_node_id: str, connection_index: int = 0, total_connections: int = 1, max_port: int = 0):
        """Draw a connection with top-to-bottom routing.
        
        Args:
            from_node_id: Source node ID
            port: Output port number
            to_node_id: Target node ID
            connection_index: Index of this connection among multiple connections (0-based)
            total_connections: Total number of connections between these nodes
            max_port: Highest port number for this connection (used for line color)
        """
        from_node = self.flow_nodes[from_node_id]
        to_node = self.flow_nodes[to_node_id]
        
        # Calculate connection points for top-to-bottom flow
        from_x = from_node['x'] + self.node_width // 2
        from_y = from_node['y'] + self.node_height
        
        to_x = to_node['x'] + self.node_width // 2
        to_y = to_node['y']
        
        # Draw the line only once (on first connection)
        if connection_index == 0:
            # Connection color - use highest port's color
            color = self.connection_colors.get(max_port, '#666666')
            
            # Smart routing for top-to-bottom layout
            if abs(to_x - from_x) < 50:
                # Direct vertical connection
                line = self.canvas.create_line(
                    from_x, from_y, to_x, to_y,
                    fill=color, width=3, arrow=tk.LAST,
                    arrowshape=(10, 12, 3),
                    tags="connection"
                )
            else:
                # Curved connection for horizontal offset
                mid_y = from_y + (to_y - from_y) * 0.6
                
                points = [
                    from_x, from_y,
                    from_x, mid_y,
                    to_x, mid_y,
                    to_x, to_y
                ]
                
                line = self.canvas.create_line(
                    points,
                    fill=color, width=3, arrow=tk.LAST,
                    arrowshape=(10, 12, 3),
                    smooth=True,
                    tags="connection"
                )
        
        # Port label color for this specific port
        port_color = self.connection_colors.get(port, '#666666')
        
        # Position port labels horizontally along the connection
        if abs(to_x - from_x) > 100:
            # For angled connections, position at midpoint with horizontal offset
            label_x = (from_x + to_x) // 2 - 30 + (connection_index * 30)
            label_y = from_y + (to_y - from_y) * 0.6
        else:
            # For vertical connections, stagger labels horizontally
            spacing = 30
            total_width = (total_connections - 1) * spacing
            label_x = from_x + 25 - total_width / 2 + connection_index * spacing
            label_y = (from_y + to_y) // 2
        
        # Port label with background circle
        label_bg = self.canvas.create_oval(
            label_x - 12, label_y - 12,
            label_x + 12, label_y + 12,
            fill='white', outline=port_color, width=2,
            tags="connection"
        )
        
        port_label = self.canvas.create_text(
            label_x, label_y,
            text=str(port), fill=port_color,
            font=("Arial", 8, "bold"),
            tags="connection"
        )

    def auto_layout_nodes(self):
        """Automatically arrange nodes in a top-to-bottom hierarchical layout."""
        if not self.flow_nodes:
            self.log_message("No nodes to layout", "warning")
            return
        
        # Find start node
        start_nodes = [node for node in self.flow_nodes.values() if node['type'] == 'StartNode']
        
        if not start_nodes:
            # If no start node, use first node
            start_node_id = list(self.flow_nodes.keys())[0]
        else:
            start_node_id = start_nodes[0]['id']
        
        # Calculate node levels using BFS
        node_levels, node_parents = self._calculate_node_levels(start_node_id)
        
        # Position nodes by level
        self._position_nodes_by_level(node_levels, node_parents)
        
        # Redraw all nodes and connections
        for node_data in self.flow_nodes.values():
            self.draw_node(node_data)
        
        self.draw_connections()
        
        # Update canvas scroll region
        self._update_canvas_scroll_region()
        
        self.log_message("Auto-layout completed", "success")

    def _calculate_node_levels(self, start_node_id):
        """Calculate hierarchical levels for nodes using BFS with cycle detection."""
        node_levels = {}
        in_progress = set()
        queue = [(start_node_id, 0)]
        visited = set()
        
        # Track parent nodes for better positioning
        node_parents = {}
        
        while queue:
            node_id, level = queue.pop(0)
            
            if node_id in visited:
                # If we see a node again, it might be reachable via multiple paths
                # Keep it at the earliest level (closest to start)
                if level < node_levels.get(node_id, float('inf')):
                    node_levels[node_id] = level
                continue
            
            visited.add(node_id)
            node_levels[node_id] = level
            
            # Add connected nodes to queue
            node_data = self.flow_nodes.get(node_id, {})
            connections = node_data.get('connections', {})
            
            for target_id in connections.values():
                if target_id in self.flow_nodes:
                    # Track parent relationships
                    if target_id not in node_parents:
                        node_parents[target_id] = []
                    node_parents[target_id].append(node_id)
                    
                    # Check for back edges (cycles)
                    if target_id in visited and node_levels.get(target_id, 999) <= level:
                        # This is a back edge - don't reprocess
                        continue
                    
                    queue.append((target_id, level + 1))
        
        # Handle unconnected nodes
        for node_id in self.flow_nodes.keys():
            if node_id not in node_levels:
                node_levels[node_id] = 999  # Put at bottom
        
        return node_levels, node_parents

    def _position_nodes_by_level(self, node_levels, node_parents):
        """Position nodes based on their hierarchical levels with smart ordering."""
        # Group nodes by level
        levels = {}
        for node_id, level in node_levels.items():
            if level not in levels:
                levels[level] = []
            levels[level].append(node_id)
        
        # Layout parameters
        horizontal_spacing = 220  # Space between nodes horizontally
        vertical_spacing = 180    # Space between levels
        margin_x = 80
        margin_y = 60
        
        # Track node positions for smart ordering
        node_positions = {}
        
        # Position nodes level by level (top to bottom)
        for level in sorted(levels.keys()):
            nodes_in_level = levels[level]
            
            # Smart ordering: position nodes close to their parents
            if level == 0:
                # First level - sort by name
                nodes_in_level.sort(key=lambda x: self.flow_nodes[x]['name'])
            else:
                # Sort by average parent position
                def get_parent_avg_x(node_id):
                    parents = node_parents.get(node_id, [])
                    if not parents:
                        return 9999  # Orphan nodes go to the right
                    
                    parent_positions = [node_positions.get(p, 9999) for p in parents]
                    valid_positions = [pos for pos in parent_positions if pos != 9999]
                    
                    if valid_positions:
                        return sum(valid_positions) / len(valid_positions)
                    return 9999
                
                nodes_in_level.sort(key=get_parent_avg_x)
            
            # Check if nodes fit in a reasonable width
            max_width = 1800  # Maximum preferred width
            nodes_per_row = len(nodes_in_level)
            
            # If too wide, consider multiple rows at same level
            if nodes_per_row > 8:
                # Split into multiple sub-levels
                chunk_size = 6
                chunks = [nodes_in_level[i:i + chunk_size] for i in range(0, len(nodes_in_level), chunk_size)]
                
                for sub_idx, chunk in enumerate(chunks):
                    y = margin_y + (level * vertical_spacing) + (sub_idx * 130)
                    self._position_nodes_in_row(chunk, y, margin_x, horizontal_spacing, node_positions)
            else:
                # Normal single row
                y = margin_y + (level * vertical_spacing)
                self._position_nodes_in_row(nodes_in_level, y, margin_x, horizontal_spacing, node_positions)
    
    def _position_nodes_in_row(self, nodes, y, margin_x, horizontal_spacing, node_positions):
        """Position a row of nodes horizontally."""
        # Calculate total width needed
        total_width = len(nodes) * self.node_width + (len(nodes) - 1) * (horizontal_spacing - self.node_width)
        
        # Center the row horizontally
        canvas_width = max(1000, total_width + 2 * margin_x)
        start_x = (canvas_width - total_width) // 2
        
        # Position each node
        for i, node_id in enumerate(nodes):
            x = start_x + i * horizontal_spacing
            
            # Update node position
            self.flow_nodes[node_id]['x'] = x
            self.flow_nodes[node_id]['y'] = y
            
            # Track position for parent-child alignment
            node_positions[node_id] = x

    def _update_canvas_scroll_region(self):
        """Update canvas scroll region based on node positions."""
        if not self.flow_nodes:
            return
        
        # Calculate bounds
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for node_data in self.flow_nodes.values():
            x, y = node_data['x'], node_data['y']
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + self.node_width)
            max_y = max(max_y, y + self.node_height)
        
        # Add margin
        margin = 100
        self.canvas.configure(scrollregion=(
            min_x - margin, min_y - margin,
            max_x + margin, max_y + margin
        ))

    def on_canvas_click(self, event):
        """Handle canvas click events."""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Find clicked item
        item = self.canvas.find_closest(canvas_x, canvas_y)[0]
        tags = self.canvas.gettags(item)
        
        if self.connection_mode:
            self.handle_connection_click(canvas_x, canvas_y, tags)
        else:
            self.handle_normal_click(canvas_x, canvas_y, tags)

    def handle_normal_click(self, x: float, y: float, tags: List[str]):
        """Handle normal click (selection/dragging)."""
        # Check if clicking on a node
        node_id = None
        for tag in tags:
            if tag.startswith("node_"):
                node_id = tag.split("_", 1)[1]
                break
        
        if node_id:
            self.select_node(node_id)
        else:
            self.clear_selection()

    def handle_connection_click(self, x: float, y: float, tags: List[str]):
        """Handle click in connection mode."""
        # Find node under cursor
        node_id = None
        for tag in tags:
            if tag.startswith("node_"):
                node_id = tag.split("_", 1)[1]
                break
        
        if not node_id:
            return
        
        if self.connection_start is None:
            # Start connection
            self.connection_start = node_id
            self.log_message(f"Connection started from {node_id}. Click target node.")
            self.status_label.configure(text=f"Select target node for connection from {node_id}")
        else:
            # Complete connection
            if node_id != self.connection_start:
                self.create_connection_dialog(self.connection_start, node_id)
            else:
                self.log_message("Cannot connect node to itsel", "warning")
            
            self.connection_start = None
            self.toggle_connection_mode()  # Exit connection mode

    def create_connection_dialog(self, from_node_id: str, to_node_id: str):
        """Show dialog to select connection port."""
        from_node = self.flow_nodes[from_node_id]
        to_node = self.flow_nodes[to_node_id]
        
        # Check if source node can have outputs
        if from_node['type'] == 'EndNode':
            self.log_message("End nodes cannot have output connections", "warning")
            return
        
        # Check if target node can have inputs
        if to_node['type'] == 'StartNode':
            self.log_message("Start nodes cannot have input connections", "warning")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Connection")
        dialog.geometry("300x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Connection info
        info_frame = ttk.Frame(dialog)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(info_frame, text=f"From: {from_node['name']}").pack(anchor="w")
        ttk.Label(info_frame, text=f"To: {to_node['name']}").pack(anchor="w")
        
        # Port selection
        port_frame = ttk.Frame(dialog)
        port_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(port_frame, text="Output Port:").pack(anchor="w")
        
        port_var = tk.StringVar(value="0")  # Default to success path
        
        # Determine available ports based on source node type
        if from_node['type'] == 'StartNode':
            port_options = [("0 - PASS Path", "0")]
        elif from_node['type'] in ['CharacterizationFlowInstance', 'DataCollectionFlowInstance', 'AnalysisFlowInstance', 'AdaptiveFlowInstance']:
            port_options = [
                ("0 - PASS Path", "0"),
                ("3 - ERROR Path", "3")
            ]
        else:
            port_options = [
                ("0 - PASS Path", "0"),
                ("1 - FAIL Path", "1"),
                ("2 - FLAKY Path", "2"),
                ("3 - ERROR Path", "3")
            ]
        
        for text, value in port_options:
            ttk.Radiobutton(port_frame, text=text, variable=port_var, value=value).pack(anchor="w")
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def create_connection():
            port = int(port_var.get())
            self.flow_nodes[from_node_id]['connections'][port] = to_node_id
            self.draw_connections()
            self.log_message(f"Connected {from_node_id} port {port} to {to_node_id}", "success")
            dialog.destroy()
        
        def cancel_connection():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Create", command=create_connection).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel_connection).pack(side=tk.RIGHT)

    def select_node(self, node_id: str):
        """Select a node and update properties panel."""
        self.selected_node = node_id
        node_data = self.flow_nodes[node_id]
        
        # Highlight selected node
        self.canvas.delete("selection")
        x, y = node_data['x'], node_data['y']
        self.canvas.create_rectangle(
            x - 3, y - 3, x + self.node_width + 3, y + self.node_height + 3,
            outline='red', width=3, tags="selection"
        )
        
        # Temporarily block property change callbacks to prevent recursion
        self._updating_properties = True
        
        # Update properties panel
        self.node_id_var.set(node_data['id'])
        self.node_name_var.set(node_data['name'])
        self.node_type_var.set(node_data['type'])
        
        # Update experiment assignment
        exp_value = node_data.get('experiment', None)
        if exp_value is None or exp_value == '':
            self.assigned_exp_var.set('None')
        else:
            self.assigned_exp_var.set(exp_value)
        
        # Re-enable callbacks
        self._updating_properties = False
        
        # Force UI update
        self.root.update_idletasks()
        
        self.log_message(f"Selected node: {node_id} | Type: {node_data['type']} | Exp: {exp_value}")

    def clear_selection(self):
        """Clear node selection."""
        self.selected_node = None
        self.canvas.delete("selection")
        
        # Block property change callbacks
        self._updating_properties = True
        
        # Clear properties panel
        self.node_id_var.set("")
        self.node_name_var.set("")
        self.node_type_var.set("")
        self.assigned_exp_var.set("")
        
        # Re-enable callbacks
        self._updating_properties = False

    def on_property_change(self, event=None):
        """Handle property changes."""
        if not self.selected_node or getattr(self, '_updating_properties', False):
            return
        
        node_data = self.flow_nodes[self.selected_node]
        
        # Update node data
        node_data['name'] = self.node_name_var.get()
        node_data['type'] = self.node_type_var.get()
        
        # Handle experiment assignment for special nodes
        if node_data['type'] in ['StartNode', 'EndNode']:
            node_data['experiment'] = None  # Special nodes don't have experiments
            self.assigned_exp_var.set('None')
        else:
            node_data['experiment'] = self.assigned_exp_var.get() if self.assigned_exp_var.get() != 'None' else None
        
        # Redraw node
        self.draw_node(node_data)
        self.draw_connections()
        
        # Maintain selection
        self.select_node(self.selected_node)

    def toggle_connection_mode(self):
        """Toggle connection mode."""
        self.connection_mode = not self.connection_mode
        self.connection_start = None
        
        if self.connection_mode:
            self.connection_button.configure(text="Exit Connect Mode")
            self.mode_label.configure(text="Mode: Connect")
            self.status_label.configure(text="Connection mode - Click source node, then target node")
        else:
            self.connection_button.configure(text="Connect Nodes")
            self.mode_label.configure(text="Mode: Design")
            self.status_label.configure(text="Design mode - Click nodes to select, drag to move")

    def delete_selected_node(self):
        """Delete the selected node."""
        if not self.selected_node:
            self.log_message("No node selected", "warning")
            return
        
        node_id = self.selected_node
        
        # Remove connections to this node
        for other_node_data in self.flow_nodes.values():
            connections_to_remove = []
            for port, target_id in other_node_data.get('connections', {}).items():
                if target_id == node_id:
                    connections_to_remove.append(port)
            
            for port in connections_to_remove:
                del other_node_data['connections'][port]
        
        # Remove the node
        self.canvas.delete(f"node_{node_id}")
        del self.flow_nodes[node_id]
        
        self.clear_selection()
        self.draw_connections()
        
        self.log_message(f"Deleted node: {node_id}", "success")

    def validate_flow(self):
        """Validate the current flow design."""
        errors = []
        warnings = []
        
        # Check for nodes
        if not self.flow_nodes:
            errors.append("Flow is empty - add some nodes")
            
        # Check for start node
        start_nodes = [n for n in self.flow_nodes.values() if n['type'] == 'StartNode']
        if not start_nodes:
            errors.append("Flow must have a StartNode")
        elif len(start_nodes) > 1:
            warnings.append("Multiple StartNodes found - only first will be used")
        
        # Check for end nodes
        end_nodes = [n for n in self.flow_nodes.values() if n['type'] == 'EndNode']
        if not end_nodes:
            warnings.append("No EndNode found - flow may run indefinitely")
        
        # Check for unconnected nodes (except start node)
        connected_nodes = set()
        for node_data in self.flow_nodes.values():
            for target_id in node_data.get('connections', {}).values():
                connected_nodes.add(target_id)
        
        if start_nodes:
            connected_nodes.add(start_nodes[0]['id'])
        
        unconnected = set(self.flow_nodes.keys()) - connected_nodes
        if unconnected:
            warnings.append(f"Unconnected nodes: {', '.join(unconnected)}")
        
        # Check for nodes without experiments (excluding start/end nodes)
        no_experiment = []
        for node_data in self.flow_nodes.values():
            if (node_data['type'] not in ['StartNode', 'EndNode'] and 
                not node_data.get('experiment')):
                no_experiment.append(node_data['id'])
        
        if no_experiment:
            errors.append(f"Nodes without experiments: {', '.join(no_experiment)}")
        
        # Show validation results
        self.show_validation_results(errors, warnings)

    def show_validation_results(self, errors: List[str], warnings: List[str]):
        """Show validation results in a dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Flow Validation Results")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        
        # Results text
        results_text = tk.Text(dialog, wrap=tk.WORD, font=("Consolas", 10))
        results_scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=results_text.yview)
        results_text.configure(yscrollcommand=results_scrollbar.set)
        
        results_text.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        results_scrollbar.pack(side="right", fill="y", pady=10)
        
        # Add results
        if not errors and not warnings:
            results_text.insert(tk.END, "✓ Flow validation passed!\n\n", "success")
            results_text.insert(tk.END, "The flow design appears to be valid and ready for export.")
        else:
            if errors:
                results_text.insert(tk.END, "ERRORS:\n", "error")
                for error in errors:
                    results_text.insert(tk.END, f"  ✗ {error}\n", "error")
                results_text.insert(tk.END, "\n")
            
            if warnings:
                results_text.insert(tk.END, "WARNINGS:\n", "warning")
                for warning in warnings:
                    results_text.insert(tk.END, f"  ⚠ {warning}\n", "warning")
        
        # Configure text colors
        results_text.tag_config("success", foreground="green", font=("Consolas", 10, "bold"))
        results_text.tag_config("error", foreground="red")
        results_text.tag_config("warning", foreground="orange")
        
        results_text.configure(state=tk.DISABLED)

    def apply_unit_config_overrides(self):
        """Apply unit configuration overrides to all experiments with confirmation."""
        # Check if any overrides are set
        overrides = {}
        if self.visual_id_var.get().strip():
            overrides['Visual ID'] = self.visual_id_var.get().strip()
        if self.bucket_var.get().strip():
            overrides['Bucket'] = self.bucket_var.get().strip()
        if self.com_port_var.get().strip():
            overrides['COM Port'] = self.com_port_var.get().strip()
        if self.ip_address_var.get().strip():
            overrides['IP Address'] = self.ip_address_var.get().strip()
        if self.unit_600w_var.get():
            overrides['600W Unit'] = self.unit_600w_var.get()
        if self.check_core_var.get():
            overrides['Check Core'] = int(self.check_core_var.get())
        
        # If no overrides, return True (proceed without changes)
        if not overrides:
            return True
        
        # Show confirmation dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Apply Unit Configuration Overrides")
        dialog.geometry("550x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + (self.root.winfo_width() - 550) // 2,
            self.root.winfo_rooty() + (self.root.winfo_height() - 450) // 2
        ))
        
        # Header
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(header_frame, 
                 text="Unit Configuration Overrides Detected",
                 font=("Arial", 11, "bold")).pack(anchor="w")
        ttk.Label(header_frame,
                 text="The following configuration will be applied to ALL experiments:",
                 font=("Arial", 9)).pack(anchor="w", pady=(5, 0))
        
        # Overrides display
        overrides_frame = ttk.LabelFrame(dialog, text="Configuration Changes", padding=10)
        overrides_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Create scrollable text widget
        overrides_text = tk.Text(overrides_frame, wrap=tk.WORD, height=12, 
                                font=("Consolas", 9), bg="#f0f0f0")
        overrides_scroll = ttk.Scrollbar(overrides_frame, orient="vertical", 
                                        command=overrides_text.yview)
        overrides_text.configure(yscrollcommand=overrides_scroll.set)
        
        overrides_text.pack(side="left", fill="both", expand=True)
        overrides_scroll.pack(side="right", fill="y")
        
        # Show what will change
        overrides_text.insert(tk.END, f"Affected experiments: {len(self.experiments)}\n\n", "bold")
        overrides_text.insert(tk.END, "Changes to apply:\n", "bold")
        
        for field, value in overrides.items():
            overrides_text.insert(tk.END, f"  • {field}: ", "field")
            overrides_text.insert(tk.END, f"{value}\n", "value")
        
        overrides_text.insert(tk.END, "\n")
        overrides_text.insert(tk.END, "Experiment List:\n", "bold")
        for exp_name in sorted(self.experiments.keys()):
            overrides_text.insert(tk.END, f"  - {exp_name}\n")
        
        # Configure text colors
        overrides_text.tag_config("bold", font=("Consolas", 9, "bold"))
        overrides_text.tag_config("field", foreground="#0066cc", font=("Consolas", 9, "bold"))
        overrides_text.tag_config("value", foreground="#006600", font=("Consolas", 9, "bold"))
        
        overrides_text.configure(state=tk.DISABLED)
        
        # User decision variable
        user_decision = tk.BooleanVar(value=False)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=15, pady=10)
        
        def apply_changes():
            user_decision.set(True)
            dialog.destroy()
        
        def skip_changes():
            user_decision.set(False)
            dialog.destroy()
        
        ttk.Button(button_frame, text="Apply to All Experiments", 
                  command=apply_changes).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Skip (No Changes)", 
                  command=skip_changes).pack(side=tk.RIGHT)
        
        # Wait for user decision
        dialog.wait_window()
        
        # Apply overrides if confirmed
        if user_decision.get():
            for exp_name, exp_data in self.experiments.items():
                for field, value in overrides.items():
                    exp_data[field] = value
            
            self.log_message(f"Applied unit configuration to {len(self.experiments)} experiments", "success")
            return True
        else:
            self.log_message("Unit configuration overrides skipped", "info")
            return True  # Still proceed with export/save

    def export_flow(self):
        """Export the flow to JSON files."""
        if not self.flow_nodes:
            self.log_message("No flow to export", "warning")
            return
        
        # Validate first
        errors = []
        start_nodes = [n for n in self.flow_nodes.values() if n['type'] == 'StartNode']
        if not start_nodes:
            errors.append("Flow must have a StartNode")
        
        no_experiment = []
        for node_data in self.flow_nodes.values():
            if (node_data['type'] not in ['StartNode', 'EndNode'] and 
                not node_data.get('experiment')):
                no_experiment.append(node_data['id'])
        
        if no_experiment:
            errors.append(f"Nodes without experiments: {', '.join(no_experiment)}")
        
        if errors:
            messagebox.showerror("Export Error", "Cannot export flow with errors:\n" + "\n".join(errors))
            return
        
        # Apply unit configuration overrides with confirmation
        if not self.apply_unit_config_overrides():
            return
        
        # Select export directory
        export_dir = filedialog.askdirectory(title="Select Export Directory")
        if not export_dir:
            return
        
        try:
            # Generate structure file
            structure_data = {}
            for node_id, node_data in self.flow_nodes.items():
                output_map = {}
                for port, target_id in node_data.get('connections', {}).items():
                    output_map[str(port)] = target_id
                
                structure_data[node_id] = {
                    "name": node_data['name'],
                    "instanceType": node_data['type'],
                    "flow": node_data.get('experiment', 'default'),
                    "outputNodeMap": output_map
                }
            
            # Generate flows file (experiments)
            flows_data = {}
            for node_data in self.flow_nodes.values():
                exp_name = node_data.get('experiment')
                if exp_name and exp_name in self.experiments:
                    flows_data[exp_name] = self.experiments[exp_name]
            
            # Generate INI file content
            ini_content = "[DEFAULT]\n"
            ini_content += "# Automation Flow Configuration\n"
            ini_content += f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for exp_name in flows_data.keys():
                ini_content += f"[{exp_name}]\n"
                ini_content += "# Add experiment-specific configuration here\n\n"
            
            # Generate positions file to preserve layout
            positions_data = {}
            for node_id, node_data in self.flow_nodes.items():
                positions_data[node_id] = {
                    'x': node_data['x'],
                    'y': node_data['y']
                }
            
            # Write files
            structure_file = os.path.join(export_dir, "FrameworkAutomationStructure.json")
            flows_file = os.path.join(export_dir, "FrameworkAutomationFlows.json")
            ini_file = os.path.join(export_dir, "FrameworkAutomationInit.ini")
            positions_file = os.path.join(export_dir, "FrameworkAutomationPositions.json")
            
            with open(structure_file, 'w') as f:
                json.dump(structure_data, f, indent=2)
            
            with open(flows_file, 'w') as f:
                json.dump(flows_data, f, indent=2)
            
            with open(ini_file, 'w') as f:
                f.write(ini_content)
            
            with open(positions_file, 'w') as f:
                json.dump(positions_data, f, indent=2)
            
            self.log_message(f"Flow exported successfully to {export_dir}", "success")
            messagebox.showinfo("Export Complete", 
                              "Flow exported successfully!\n\nFiles created:\n"
                              f"• {os.path.basename(structure_file)}\n"
                              f"• {os.path.basename(flows_file)}\n"
                              f"• {os.path.basename(ini_file)}\n"
                              f"• {os.path.basename(positions_file)}")
            
        except Exception as e:
            self.log_message(f"Export error: {str(e)}", "error")
            messagebox.showerror("Export Error", f"Failed to export flow:\n{str(e)}")

    def save_flow(self):
        """Save the current flow design."""
        if not self.flow_nodes:
            self.log_message("No flow to save", "warning")
            return
        
        # Apply unit configuration overrides with confirmation
        if not self.apply_unit_config_overrides():
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Flow Design",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            flow_design = {
                'nodes': self.flow_nodes,
                'experiments': self.experiments,
                'unit_config': self.unit_config,
                'metadata': {
                    'created': datetime.now().isoformat(),
                    'version': '1.8',
                    'node_counter': self.node_counter
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(flow_design, f, indent=2)
            
            self.log_message(f"Flow saved to {os.path.basename(file_path)}", "success")
            
        except Exception as e:
            self.log_message(f"Save error: {str(e)}", "error")
            messagebox.showerror("Save Error", f"Failed to save flow:\n{str(e)}")

    def new_flow(self):
        """Create a new flow (clear current)."""
        if self.flow_nodes:
            if not messagebox.askyesno("New Flow", "This will clear the current flow. Continue?"):
                return
        
        # Clear everything
        self.flow_nodes.clear()
        self.canvas.delete("all")
        self.draw_grid()
        self.clear_selection()
        self.node_counter = 1
        
        self.log_message("New flow created", "success")
        self.status_label.configure(text="New flow - Load experiments to begin")
     
    def preview_flow(self):
        """Show a preview of the flow execution order."""
        if not self.flow_nodes:
            self.log_message("No flow to preview", "warning")
            return
        
        # Find start node
        start_nodes = [n for n in self.flow_nodes.values() if n['type'] == 'StartNode']
        if not start_nodes:
            self.log_message("No StartNode found for preview", "error")
            return
        
        # Trace execution path
        execution_order = []
        visited = set()
        
        def trace_path(node_id, path):
            if node_id in visited or len(path) > 20:  # Prevent infinite loops
                return
            
            visited.add(node_id)
            node_data = self.flow_nodes.get(node_id)
            if not node_data:
                return
            
            path.append({
                'id': node_id,
                'name': node_data['name'],
                'type': node_data['type'],
                'experiment': node_data.get('experiment')
            })
            
            # Follow connections (prefer success path first)
            connections = node_data.get('connections', {})
            for port in sorted(connections.keys()):
                target_id = connections[port]
                if target_id not in visited:
                    trace_path(target_id, path.copy())
        
        trace_path(start_nodes[0]['id'], [])
        
        # Show preview dialog
        self.show_flow_preview(execution_order)

    def show_flow_preview(self, execution_order: List[Dict]):
        """Show flow preview dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Flow Preview")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        
        # Preview text
        preview_text = tk.Text(dialog, wrap=tk.WORD, font=("Consolas", 10))
        preview_scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=preview_text.yview)
        preview_text.configure(yscrollcommand=preview_scrollbar.set)
        
        preview_text.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        preview_scrollbar.pack(side="right", fill="y", pady=10)
        
        # Add preview content
        preview_text.insert(tk.END, "AUTOMATION FLOW PREVIEW\n", "title")
        preview_text.insert(tk.END, "=" * 50 + "\n\n", "title")
        
        if execution_order:
            for i, node_info in enumerate(execution_order, 1):
                preview_text.insert(tk.END, f"{i}. {node_info['name']}\n", "node")
                preview_text.insert(tk.END, f"   Type: {node_info['type']}\n")
                if node_info['experiment']:
                    preview_text.insert(tk.END, f"   Experiment: {node_info['experiment']}\n", "experiment")
                elif node_info['type'] in ['StartNode', 'EndNode']:
                    purpose = "Entry Point" if node_info['type'] == 'StartNode' else "Exit Point"
                    preview_text.insert(tk.END, f"   Purpose: {purpose}\n", "special")
                preview_text.insert(tk.END, "\n")
        else:
            preview_text.insert(tk.END, "No execution path found.\n", "error")
            preview_text.insert(tk.END, "Check that nodes are properly connected.\n")
        
        # Configure text styles
        preview_text.tag_config("title", font=("Consolas", 12, "bold"))
        preview_text.tag_config("node", font=("Consolas", 10, "bold"), foreground="blue")
        preview_text.tag_config("experiment", foreground="green")
        preview_text.tag_config("special", foreground="purple")
        preview_text.tag_config("error", foreground="red")
        
        preview_text.configure(state=tk.DISABLED)

    def on_experiment_double_click(self, event):
        """Handle double-click on experiment list."""
        selection = self.experiments_listbox.curselection()
        if selection and self.selected_node:
            # Check if selected node can have experiments
            node_data = self.flow_nodes[self.selected_node]
            if node_data['type'] in ['StartNode', 'EndNode']:
                self.log_message("Start and End nodes cannot have experiments assigned", "warning")
                return
            
            exp_name = self.experiments_listbox.get(selection[0])
            self.assigned_exp_var.set(exp_name)
            self.on_property_change()
            self.log_message(f"Assigned experiment '{exp_name}' to {self.selected_node}")

    def show_tooltip(self, text: str):
        """Show tooltip (simplified implementation)."""
        self.status_label.configure(text=text)

    def on_canvas_drag(self, event):
        """Handle canvas dragging (node movement)."""
        if self.selected_node and not self.connection_mode:
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            
            # Snap to grid
            x = round(canvas_x / self.grid_size) * self.grid_size
            y = round(canvas_y / self.grid_size) * self.grid_size
            
            # Update node position
            node_data = self.flow_nodes[self.selected_node]
            node_data['x'] = x
            node_data['y'] = y
            
            # Redraw
            self.draw_node(node_data)
            self.draw_connections()
            self.select_node(self.selected_node)

    def on_canvas_release(self, event):
        """Handle canvas mouse release."""
        pass  # Placeholder for future drag completion logic

    def on_canvas_right_click(self, event):
        """Handle right-click context menu."""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Find clicked item
        item = self.canvas.find_closest(canvas_x, canvas_y)[0]
        tags = self.canvas.gettags(item)
        
        # Check if clicking on a node
        node_id = None
        for tag in tags:
            if tag.startswith("node_"):
                node_id = tag.split("_", 1)[1]
                break
        
        # Create context menu
        context_menu = tk.Menu(self.root, tearoff=0)
        
        if node_id:
            # Node-specific menu
            node_data = self.flow_nodes[node_id]
            context_menu.add_command(
                label=f"Node: {node_data['name']}",
                state=tk.DISABLED
            )
            context_menu.add_separator()
            
            if node_data['type'] not in ['StartNode', 'EndNode']:
                context_menu.add_command(
                    label="Edit Experiment",
                    command=lambda: self.edit_node_experiment_by_id(node_id)
                )
                context_menu.add_separator()
            
            context_menu.add_command(
                label="Delete Node",
                command=lambda: self.delete_node_by_id(node_id)
            )
        else:
            # Canvas menu
            node_menu = tk.Menu(context_menu, tearoff=0)
            for display_name, class_name in [
                ("Start Node", "StartNode"),
                ("Single Fail Node", "SingleFailFlowInstance"),
                ("All Fail Node", "AllFailFlowInstance"), 
                ("Majority Fail Node", "MajorityFailFlowInstance"),
                ("Adaptive Node", "AdaptiveFlowInstance"),
                ("Characterization Node", "CharacterizationFlowInstance"),
                ("Data Collection Node", "DataCollectionFlowInstance"),
                ("Analysis Node", "AnalysisFlowInstance"),
                ("End Node", "EndNode")
            ]:
                node_menu.add_command(
                    label=display_name,
                    command=lambda cn=class_name, x=canvas_x, y=canvas_y: self.add_node(cn, x, y)
                )
            
            context_menu.add_cascade(label="Add Node", menu=node_menu)
            context_menu.add_separator()
            context_menu.add_command(label="Auto Layout", command=self.auto_layout_nodes)
        
        # Show menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def edit_node_experiment(self):
        """Edit the experiment configuration for the selected node."""
        if not self.selected_node:
            self.log_message("No node selected", "warning")
            return
        
        node_data = self.flow_nodes[self.selected_node]
        
        # Check if node can have experiments
        if node_data['type'] in ['StartNode', 'EndNode']:
            self.log_message("Start and End nodes cannot have experiments", "warning")
            return
        
        # Get experiment data
        exp_name = node_data.get('experiment')
        if not exp_name or exp_name not in self.experiments:
            # Create new experiment
            exp_data = self.create_default_experiment()
            if not exp_name:
                # Generate unique name based on node name
                base_name = f"Experiment_{node_data['name']}"
                exp_name = self.generate_unique_experiment_name(base_name)
        else:
            exp_data = self.experiments[exp_name].copy()
            # Suggest a new name based on the original
            exp_name = self.generate_unique_experiment_name(f"{exp_name}_Copy")
        
        # Open experiment editor
        self.open_experiment_editor(exp_name, exp_data)

    def edit_node_experiment_by_id(self, node_id):
        """Edit the experiment configuration for a specific node by ID."""
        if node_id not in self.flow_nodes:
            self.log_message(f"Node {node_id} not found", "error")
            return
        
        # Select the node first
        self.select_node(node_id)
        
        # Then edit its experiment
        self.edit_node_experiment()

    def delete_node_by_id(self, node_id):
        """Delete a specific node by ID."""
        # Select the node first
        self.select_node(node_id)
        # Then delete it
        self.delete_selected_node()
        
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def log_message(self, message: str, level: str = "info"):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        color_map = {
            "error": "red",
            "warning": "yellow",
            "success": "green", 
            "info": "white"
        }
        color = color_map.get(level.lower(), "white")
        
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.configure(state=tk.NORMAL)
        
        start_pos = self.log_text.index(tk.END)
        self.log_text.insert(tk.END, log_entry)
        end_pos = self.log_text.index(tk.END)
        
        tag_name = f"level_{level}_{timestamp.replace(':', '_')}"
        self.log_text.tag_add(tag_name, start_pos, end_pos)
        self.log_text.tag_config(tag_name, foreground=color)
        
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def run(self):
        """Start the designer interface."""
        self.root.mainloop()

class ExperimentEditor:
    """Dialog for editing experiment configurations."""
    
    def __init__(self, parent, exp_name, exp_data, unit_config, save_callback, existing_experiments=None):
        self.parent = parent
        self.exp_name = exp_name
        self.exp_data = exp_data.copy()
        self.unit_config = unit_config
        self.save_callback = save_callback
        self.existing_experiments = existing_experiments or {}
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Edit Experiment: {exp_name}")
        self.dialog.geometry("600x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.center_dialog()
        
        # Create UI
        self.create_widgets()
        
        # Load data
        self.load_experiment_data()

    def center_dialog(self):
        """Center the dialog on parent window."""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def create_widgets(self):
        """Create the editor widgets."""
        # Main container
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Experiment name
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(name_frame, text="Experiment Name:").pack(side=tk.LEFT)
        self.exp_name_var = tk.StringVar(value=self.exp_name)
        self.exp_name_entry = ttk.Entry(name_frame, textvariable=self.exp_name_var, width=30)
        self.exp_name_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_experiment_config_tab()
        self.create_defeature_tab()
        self.create_content_tab()
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save_changes).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT)

    def create_defeature_tab(self):
        """Create the defeature tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Defeature")
        
        # Store variables for defeature config
        self.defeature_vars = {}
        
        # Core License options
        core_license_options = [
            "None",
            "1: SSE/128",
            "2: AVX2/256 Light", 
            "3: AVX2/256 Heavy",
            "4: AVX3/512 Light",
            "5: AVX3/512 Heavy",
            "6: TMUL Light",
            "7: TMUL Heavy"
        ]
        
        # Defeature fields - Updated with all required fields
        defeature_fields = [
            ("Voltage Type", "combo", ["ppvc", "fixed", "vbump"]),
            ("Voltage IA", "entry"),
            ("Voltage CFC", "entry"),
            ("Frequency IA", "entry"),
            ("Frequency CFC", "entry"),
            ("Pseudo Config", "check"),
            ("Disable 2 Cores", "entry"),
            ("Core License", "combo", core_license_options)
           
        ]
        
        for field_info in defeature_fields:
            field_name = field_info[0]
            field_type = field_info[1]
            
            # Create frame for field
            field_frame = ttk.Frame(tab_frame)
            field_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Label
            ttk.Label(field_frame, text=f"{field_name}:", width=15).pack(side=tk.LEFT)
            
            # Create appropriate widget
            if field_type == "entry":
                var = tk.StringVar()
                widget = ttk.Entry(field_frame, textvariable=var, width=60)
            elif field_type == "combo":
                var = tk.StringVar()
                values = field_info[2] if len(field_info) > 2 else []
                widget = ttk.Combobox(field_frame, textvariable=var, values=values, width=57)
            elif field_type == "check":
                var = tk.BooleanVar()
                widget = ttk.Checkbutton(field_frame, variable=var)
            
            widget.pack(side=tk.LEFT, padx=(10, 0))
            self.defeature_vars[field_name] = var

    def create_content_tab(self):
        """Create the content configuration tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Content")
        
        # Scrollable frame
        canvas = tk.Canvas(tab_frame)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Store variables for content config
        self.content_vars = {}
        
        # Linux Section
        linux_frame = ttk.LabelFrame(scrollable_frame, text="Linux Section", padding=10)
        linux_frame.pack(fill=tk.X, padx=5, pady=5)
        
        linux_fields = [
            "Linux Pre Command",
            "Linux Post Command", 
            "Linux Pass String",
            "Linux Fail String",
            "Startup Linux",
            "Linux Path",
            "Linux Content Wait Time",
            "Linux Content Line 0",
            "Linux Content Line 1",
            "Linux Content Line 2",
            "Linux Content Line 3",
            "Linux Content Line 4",
            "Linux Content Line 5"
        ]
        
        for field_name in linux_fields:
            field_frame = ttk.Frame(linux_frame)
            field_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(field_frame, text=f"{field_name}:", width=20).pack(side=tk.LEFT)
            var = tk.StringVar()
            widget = ttk.Entry(field_frame, textvariable=var, width=60)
            widget.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
            self.content_vars[field_name] = var
        
        # Dragon Section
        dragon_frame = ttk.LabelFrame(scrollable_frame, text="Dragon Section", padding=10)
        dragon_frame.pack(fill=tk.X, padx=5, pady=5)
        
        dragon_fields = [
            ("Dragon Pre Command", "entry"),
            ("Dragon Post Command", "entry"),
            ("Startup Dragon", "entry"),
            ("ULX Path", "entry"),
            ("ULX CPU", "entry"),
            ("Product Chop", "entry"),
            ("VVAR0", "entry"),
            ("VVAR1", "entry"),
            ("VVAR2", "entry"),
            ("VVAR3", "entry"),
            ("VVAR_EXTRA", "entry"),
            ("Dragon Content Path", "entry"),
            ("Dragon Content Line", "entry"),
            ("Stop on Fail", "check"),
            ("Merlin Name", "entry"),
            ("Merlin Drive", "entry"),
            ("Merlin Path", "entry")
        ]
        
        for field_info in dragon_fields:
            field_name = field_info[0]
            field_type = field_info[1]
            
            field_frame = ttk.Frame(dragon_frame)
            field_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(field_frame, text=f"{field_name}:", width=20).pack(side=tk.LEFT)
            
            if field_type == "entry":
                var = tk.StringVar()
                widget = ttk.Entry(field_frame, textvariable=var, width=50)
            elif field_type == "check":
                var = tk.BooleanVar()
                widget = ttk.Checkbutton(field_frame, variable=var)
            
            widget.pack(side=tk.LEFT, padx=(10, 0))
            if field_type == "entry":
                widget.pack(fill=tk.X, expand=True)
            
            self.content_vars[field_name] = var
 
    def create_experiment_config_tab(self):
        """Create the experiment configuration tab."""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Experiment Configuration")
        
        # Scrollable frame
        canvas = tk.Canvas(tab_frame)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Store variables for experiment config
        self.exp_config_vars = {}
        
        # Configuration fields - Updated with all required fields
        config_fields = [
            ("Test Name", "entry"),
            ("Test Mode", "combo", ["Mesh", "Slice"]),
            ("Test Type", "combo", ["Loops", "Sweep", "Shmoo"]),
            ("TTL Folder", "entry"),
            ("Scripts File", "entry"),
            ("Post Process", "entry"),
            ("Pass String", "entry"),
            ("Fail String", "entry"),
            ("Content", "combo", ["Dragon", "Linux", "PYSVConsole"]),
            ("Test Number", "entry"),
            ("Test Time", "entry"),
            ("Reset", "check"),
            ("Reset on PASS", "check"),
            ("FastBoot", "check"),
            ("Boot Breakpoint", "entry"),
            # Conditional Field -- Based on Test Mode
            ("Configuration (Mask)","combo",[""]),
            # Conditional fields - will be shown/hidden based on Test Type
            ("Loops", "entry"),  # Show if Test Type is Loops
            ("Type", "combo", ["Voltage", "Frequency"]),  # Show if Test Type is Sweep
            ("Domain", "combo", ["IA", "CFC"]),  # Show if Test Type is Sweep
            ("Start", "entry"),  # Show if Test Type is Sweep
            ("End", "entry"),  # Show if Test Type is Sweep
            ("Steps", "entry"),  # Show if Test Type is Sweep
            ("ShmooFile", "entry"),  # Show if Test Type is Shmoo
            ("ShmooLabel", "entry")  # Show if Test Type is Shmoo
        ]
        
        # Store field frames for conditional display
        self.conditional_fields = {}
        
        for i, field_info in enumerate(config_fields):
            field_name = field_info[0]
            field_type = field_info[1]
            
            # Create frame for field
            field_frame = ttk.Frame(scrollable_frame)
            field_frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Store conditional field frames
            if field_name in ["Loops", "Type", "Domain", "Start", "End", "Steps", "ShmooFile", "ShmooLabel"]:
                self.conditional_fields[field_name] = field_frame
            
            # Label
            ttk.Label(field_frame, text=f"{field_name}:", width=15).pack(side=tk.LEFT)
            
            # Create appropriate widget
            if field_type == "entry":
                var = tk.StringVar()
                widget = ttk.Entry(field_frame, textvariable=var, width=60)
            elif field_type == "combo":
                var = tk.StringVar()
                values = field_info[2] if len(field_info) > 2 else []
                widget = ttk.Combobox(field_frame, textvariable=var, values=values, width=57)
            elif field_type == "check":
                var = tk.BooleanVar()
                widget = ttk.Checkbutton(field_frame, variable=var)
            
            widget.pack(side=tk.LEFT, padx=(10, 0))
            self.exp_config_vars[field_name] = var
            
            # Special handling for Test Type to show/hide conditional fields
            if field_name == "Test Type":
                var.trace('w', self.on_test_type_change)

            # Special handling for Test Mode to update Configuration (Mask) options
            if field_name == "Test Mode":
                var.trace('w', self.on_test_mode_change)
                # Store reference to Configuration (Mask) widget for updates
                if field_name == "Test Mode":
                    self.test_mode_widget = widget
            
            # Store reference to Configuration (Mask) widget for dynamic updates
            if field_name == "Configuration (Mask)":
                self.config_mask_widget = widget

        # Initially hide conditional fields
        self.update_conditional_fields()
        self.update_configuration_mask_options()

    def on_test_mode_change(self, *args):
        """Handle Test Mode change to update Configuration (Mask) options."""
        self.update_configuration_mask_options()

    def update_configuration_mask_options(self):
        """Update Configuration (Mask) options based on Test Mode."""
        test_mode = self.exp_config_vars.get("Test Mode", tk.StringVar()).get()
        
        if hasattr(self, 'config_mask_widget'):
            if test_mode == "Mesh":
                # Mesh mode options
                mesh_options = ["", "FirstPass", "SecondPass", "ThirdPass", "RowPass1", "RowPass2", "RowPass3"]
                self.config_mask_widget.configure(values=mesh_options)
                print("Updated Configuration (Mask) options for Mesh mode")
            elif test_mode == "Slice":
                # Slice mode options (0 to 179)
                slice_options = [""] + [str(i) for i in range(180)]  # 0 to 179
                self.config_mask_widget.configure(values=slice_options)
                print("Updated Configuration (Mask) options for Slice mode (0-179)")
            else:
                # Default/unknown mode
                default_options = [""]
                self.config_mask_widget.configure(values=default_options)
                print("Updated Configuration (Mask) options for default mode")
                
    def update_conditional_fields(self):
        """Update visibility of conditional fields based on Test Type."""
        test_type = self.exp_config_vars.get("Test Type", tk.StringVar()).get()
        
        # Hide all conditional fields first
        for field_name, frame in self.conditional_fields.items():
            frame.pack_forget()
        
        # Show relevant fields based on Test Type
        if test_type == "Loops":
            if "Loops" in self.conditional_fields:
                self.conditional_fields["Loops"].pack(fill=tk.X, padx=5, pady=2)
        
        elif test_type == "Sweep":
            sweep_fields = ["Type", "Domain", "Start", "End", "Steps"]
            for field in sweep_fields:
                if field in self.conditional_fields:
                    self.conditional_fields[field].pack(fill=tk.X, padx=5, pady=2)
        
        elif test_type == "Shmoo":
            shmoo_fields = ["ShmooFile", "ShmooLabel"]
            for field in shmoo_fields:
                if field in self.conditional_fields:
                    self.conditional_fields[field].pack(fill=tk.X, padx=5, pady=2)
       
    def on_test_type_change(self, *args):
        """Handle Test Type change to show/hide conditional fields."""
        self.update_conditional_fields()

    def load_experiment_data(self):
        """Load experiment data into the form."""
        # Load experiment config data
        for field_name, var in self.exp_config_vars.items():
            value = self.exp_data.get(field_name, "")
            if isinstance(var, tk.BooleanVar):
                var.set(bool(value))
            else:
                var.set(str(value) if value is not None else "")
        
        # Load defeature data
        for field_name, var in self.defeature_vars.items():
            value = self.exp_data.get(field_name, "")
            var.set(str(value) if value is not None else "")

        # Load experiment config data
        for field_name, var in self.content_vars.items():
            value = self.exp_data.get(field_name, "")
            if isinstance(var, tk.BooleanVar):
                var.set(bool(value))
            else:
                var.set(str(value) if value is not None else "")

        # Update Configuration (Mask) options after loading data
        self.update_configuration_mask_options()
                
    def save_changes(self):
        """Save changes and close dialog."""
        # Update experiment data from form
        for field_name, var in self.exp_config_vars.items():
            if isinstance(var, tk.BooleanVar):
                self.exp_data[field_name] = var.get()
            else:
                value = var.get()
                # Try to convert to appropriate type
                if field_name in ["Test Number", "Test Time", "Loops"]:
                    try:
                        self.exp_data[field_name] = int(value) if value else None
                    except ValueError:
                        self.exp_data[field_name] = value
                elif field_name in ["Start", "End", "Steps"]:
                    try:
                        self.exp_data[field_name] = float(value) if value else None
                    except ValueError:
                        self.exp_data[field_name] = value
                else:
                    self.exp_data[field_name] = value if value else None
        
        # Update defeature data
        for field_name, var in self.defeature_vars.items():
            if isinstance(var, tk.BooleanVar):
                self.exp_data[field_name] = var.get()
            elif field_name == "Core License":
                value = var.get()
                if value == "None" or not value:
                    self.exp_data[field_name] = None
                else:
                    self.exp_data[field_name] = value
            else:
                value = var.get()
                if field_name in ["Voltage IA", "Voltage CFC", "Frequency IA", "Frequency CFC"]:
                    try:
                        self.exp_data[field_name] = float(value) if value else None
                    except ValueError:
                        self.exp_data[field_name] = value if value else None
                else:
                    self.exp_data[field_name] = value if value else None
        
        # Update content data
        for field_name, var in self.content_vars.items():
            if isinstance(var, tk.BooleanVar):
                self.exp_data[field_name] = var.get()
            else:
                value = var.get()
                # Handle special numeric fields
                if field_name in ["VVAR1"]:
                    try:
                        self.exp_data[field_name] = int(value) if value else None
                    except ValueError:
                        self.exp_data[field_name] = value if value else None
                elif field_name in ["Linux Content Wait Time"]:
                    try:
                        self.exp_data[field_name] = float(value) if value else None
                    except ValueError:
                        self.exp_data[field_name] = value if value else None
                else:
                    self.exp_data[field_name] = value if value else None
        
        # Get updated experiment name
        new_exp_name = self.exp_name_var.get().strip()
        
        # Validate experiment name
        if not new_exp_name:
            messagebox.showerror("Invalid Name", "Experiment name cannot be empty.")
            return
        
        # Check if this is creating a new experiment or modifying existing
        original_exp_name = self.exp_name
        is_new_experiment = (new_exp_name != original_exp_name)
        
        # If creating new experiment, check for conflicts
        if is_new_experiment:
            # Check if experiment name already exists
            if hasattr(self, 'existing_experiments') and new_exp_name in self.existing_experiments:
                # Show confirmation dialog
                result = messagebox.askyesnocancel(
                    "Experiment Exists", 
                    f"An experiment named '{new_exp_name}' already exists.\n\n"
                    "Click 'Yes' to override the existing experiment.\n"
                    "Click 'No' to choose a different name.\n"
                    "Click 'Cancel' to abort the save operation.",
                    icon='warning'
                )
                
                if result is None:  # Cancel
                    return
                elif result is False:  # No - don't override, let user change name
                    messagebox.showinfo("Choose Different Name", 
                                    "Please choose a different experiment name.")
                    return
                # If Yes (True), continue with override
        
        # Call save callback with the new experiment name and data
        self.save_callback(new_exp_name, self.exp_data)
        
        # Close dialog
        self.dialog.destroy()
   
    def show(self):
        """Show the dialog."""
        self.dialog.focus_set()

# Standalone function to start the designer
def start_automation_flow_designer(parent=None):
    """
    Start the automation flow designer interface.
    Args:
        parent: Optional parent window (for Toplevel mode)
    """
    designer = AutomationFlowDesigner(parent=parent)
    if parent is None:
        designer.run()
    # If parent exists, window is already visible as Toplevel

if __name__ == '__main__':
    start_automation_flow_designer()