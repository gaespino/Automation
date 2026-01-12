"""
PPV Developer Environment v1.0
Comprehensive configuration management tool for PPV Tools Hub

This is a standalone utility tool for developers to manage configurations
of all PPV tools. It should be run independently from the utils folder.

Features:
- Field configuration manager for ExperimentBuilder
- Data structure editor for parsers and analyzers
- Template generator for new tools
- Config file validator
- Version control helpers

Usage:
    python PPV/utils/DeveloperEnvironment.py
"""

import sys
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from typing import Dict, Any, List
from datetime import datetime
import shutil

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class DeveloperEnvironmentGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PPV Developer Environment v1.0")
        self.root.geometry("1400x900")

        # Color scheme
        self.colors = {
            'primary': '#1e3a8a',      # Deep blue
            'secondary': '#374151',     # Dark gray
            'accent': '#3b82f6',        # Bright blue
            'success': '#10b981',       # Green
            'warning': '#f59e0b',       # Orange
            'danger': '#ef4444',        # Red
            'light': '#f3f4f6',         # Light gray
            'dark': '#111827'           # Very dark gray
        }

        # Data structures
        self.current_tool = None
        self.config_data = {}
        self.modified = False

        # Setup UI
        self.create_main_layout()

    def create_main_layout(self):
        """Create the main application layout"""
        # Header
        header = tk.Frame(self.root, bg=self.colors['primary'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text="🛠 PPV Developer Environment",
                font=('Segoe UI', 18, 'bold'), bg=self.colors['primary'], fg='white').pack(side='left', padx=30, pady=20)

        tk.Label(header, text="Configuration Management for PPV Tools Hub",
                font=('Segoe UI', 10), bg=self.colors['primary'], fg='white').pack(side='left', padx=10)

        # Main content area with sidebar
        main_content = tk.Frame(self.root, bg='white')
        main_content.pack(fill='both', expand=True)

        # Sidebar
        self.create_sidebar(main_content)

        # Content area
        self.create_content_area(main_content)

        # Status bar
        self.create_status_bar()

    def create_sidebar(self, parent):
        """Create sidebar with tool selection"""
        sidebar = tk.Frame(parent, bg=self.colors['light'], width=250)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="🔧 Tools", font=('Segoe UI', 12, 'bold'),
                bg=self.colors['light'], fg=self.colors['primary']).pack(pady=15, padx=10, anchor='w')

        # Tool buttons
        tools = [
            ("📝 ExperimentBuilder", "experiment_builder", "Manage experiment fields and config"),
            ("📊 Framework Parser", "framework_parser", "Configure framework data structures"),
            ("🔍 MCA Parser", "mca_parser", "Configure MCA analysis fields"),
            ("📈 Overview Analyzer", "overview_analyzer", "Configure overview metrics"),
            ("🔄 PPV Loops Parser", "loops_parser", "Configure loop structure"),
            ("🎯 Decoder Configs", "decoder", "Manage decoder configurations"),
            ("📁 Template Generator", "template_gen", "Generate new tool templates"),
            ("✓ Config Validator", "validator", "Validate all configurations"),
        ]

        for label, tool_id, description in tools:
            btn_frame = tk.Frame(sidebar, bg='white', relief='flat', bd=1)
            btn_frame.pack(fill='x', padx=10, pady=5)

            btn = tk.Button(btn_frame, text=label, font=('Segoe UI', 10, 'bold'),
                           bg='white', fg=self.colors['primary'],
                           command=lambda t=tool_id: self.load_tool(t),
                           relief='flat', anchor='w', padx=15, pady=10)
            btn.pack(fill='x')

            tk.Label(btn_frame, text=description, font=('Segoe UI', 8),
                    bg='white', fg='#666', anchor='w').pack(fill='x', padx=15, pady=(0, 5))

            # Hover effects
            def on_enter(e, frame=btn_frame):
                frame.config(bg=self.colors['accent'])
                for child in frame.winfo_children():
                    if hasattr(child, 'config'):
                        child.config(bg=self.colors['accent'], fg='white')

            def on_leave(e, frame=btn_frame):
                frame.config(bg='white')
                for child in frame.winfo_children():
                    if isinstance(child, tk.Button):
                        child.config(bg='white', fg=self.colors['primary'])
                    elif hasattr(child, 'config'):
                        child.config(bg='white', fg='#666')

            btn_frame.bind('<Enter>', on_enter)
            btn_frame.bind('<Leave>', on_leave)
            for child in btn_frame.winfo_children():
                child.bind('<Enter>', on_enter)
                child.bind('<Leave>', on_leave)

        # Quick Actions
        tk.Label(sidebar, text="⚡ Quick Actions", font=('Segoe UI', 12, 'bold'),
                bg=self.colors['light'], fg=self.colors['primary']).pack(pady=(30, 15), padx=10, anchor='w')

        quick_actions = [
            ("📂 Open Config Folder", self.open_config_folder),
            ("💾 Backup All Configs", self.backup_all_configs),
            ("🔄 Refresh All", self.refresh_all_tools),
        ]

        for label, command in quick_actions:
            tk.Button(sidebar, text=label, font=('Segoe UI', 9),
                     bg=self.colors['accent'], fg='white',
                     command=command, relief='flat', padx=10, pady=8).pack(fill='x', padx=10, pady=3)

    def create_content_area(self, parent):
        """Create main content area"""
        self.content_frame = tk.Frame(parent, bg='white')
        self.content_frame.pack(side='left', fill='both', expand=True)

        # Welcome screen
        self.show_welcome_screen()

    def create_status_bar(self):
        """Create status bar at bottom"""
        self.status_bar = tk.Frame(self.root, bg=self.colors['dark'], height=30)
        self.status_bar.pack(side='bottom', fill='x')
        self.status_bar.pack_propagate(False)

        self.status_label = tk.Label(self.status_bar, text="Ready", font=('Segoe UI', 9),
                                     bg=self.colors['dark'], fg='white', anchor='w')
        self.status_label.pack(side='left', padx=10)

        self.tool_label = tk.Label(self.status_bar, text="No tool selected", font=('Segoe UI', 9),
                                   bg=self.colors['dark'], fg='#888', anchor='e')
        self.tool_label.pack(side='right', padx=10)

    def show_welcome_screen(self):
        """Show welcome screen"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        welcome = tk.Frame(self.content_frame, bg='white')
        welcome.pack(fill='both', expand=True, padx=50, pady=50)

        tk.Label(welcome, text="👋 Welcome to PPV Developer Environment",
                font=('Segoe UI', 20, 'bold'), bg='white', fg=self.colors['primary']).pack(pady=20)

        tk.Label(welcome, text="Select a tool from the sidebar to begin configuration management.",
                font=('Segoe UI', 12), bg='white', fg='#666').pack(pady=10)

        # Feature cards
        features_frame = tk.Frame(welcome, bg='white')
        features_frame.pack(pady=30)

        features = [
            ("🎯", "Field Management", "Add, edit, and remove fields from tool configurations"),
            ("📝", "Config Editor", "Direct JSON editing with validation and syntax highlighting"),
            ("💾", "Version Control", "Export/import configs for version control integration"),
            ("🔄", "Template Generator", "Generate boilerplate code for new tools"),
        ]

        for row, (icon, title, desc) in enumerate(features):
            col = row % 2
            row = row // 2

            card = tk.Frame(features_frame, bg='#f8fafc', relief='solid', bd=1, width=300, height=120)
            card.grid(row=row, column=col, padx=15, pady=15, sticky='nsew')
            card.grid_propagate(False)

            tk.Label(card, text=icon, font=('Segoe UI', 30), bg='#f8fafc').pack(pady=10)
            tk.Label(card, text=title, font=('Segoe UI', 11, 'bold'), bg='#f8fafc', fg=self.colors['primary']).pack()
            tk.Label(card, text=desc, font=('Segoe UI', 9), bg='#f8fafc', fg='#666', wraplength=250).pack(pady=5)

    def load_tool(self, tool_id):
        """Load a specific tool configuration"""
        self.current_tool = tool_id
        self.tool_label.config(text=f"Tool: {tool_id.replace('_', ' ').title()}")
        self.update_status(f"Loading {tool_id}...")

        # Clear content area
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if tool_id == "experiment_builder":
            self.show_experiment_builder_config()
        elif tool_id == "template_gen":
            self.show_template_generator()
        elif tool_id == "validator":
            self.show_config_validator()
        else:
            self.show_generic_config_editor(tool_id)

        self.update_status(f"Loaded {tool_id}")

    def show_experiment_builder_config(self):
        """Show ExperimentBuilder configuration manager"""
        container = tk.Frame(self.content_frame, bg='white')
        container.pack(fill='both', expand=True, padx=20, pady=20)

        # Header
        header = tk.Frame(container, bg='white')
        header.pack(fill='x', pady=(0, 20))

        tk.Label(header, text="📝 ExperimentBuilder Field Configuration",
                font=('Segoe UI', 16, 'bold'), bg='white', fg=self.colors['primary']).pack(side='left')

        # Load current config
        try:
            from PPV.gui.ExperimentBuilder import ExperimentBuilderGUI
            temp_instance = ExperimentBuilderGUI()
            self.config_data = temp_instance.config_template
            temp_instance.root.destroy()
        except:
            self.config_data = self.get_default_experiment_config()

        # Toolbar
        toolbar = tk.Frame(container, bg='white')
        toolbar.pack(fill='x', pady=(0, 10))

        tk.Button(toolbar, text="💾 Export Config", font=('Segoe UI', 10),
                 bg=self.colors['success'], fg='white',
                 command=self.export_config, relief='flat', padx=15, pady=8).pack(side='left', padx=5)

        tk.Button(toolbar, text="📂 Import Config", font=('Segoe UI', 10),
                 bg=self.colors['accent'], fg='white',
                 command=self.import_config, relief='flat', padx=15, pady=8).pack(side='left', padx=5)

        tk.Button(toolbar, text="➕ Add Field", font=('Segoe UI', 10),
                 bg=self.colors['primary'], fg='white',
                 command=self.add_field_dialog, relief='flat', padx=15, pady=8).pack(side='left', padx=5)

        tk.Button(toolbar, text="✏️ Edit Field", font=('Segoe UI', 10),
                 bg=self.colors['warning'], fg='white',
                 command=self.edit_field_dialog, relief='flat', padx=15, pady=8).pack(side='left', padx=5)

        tk.Button(toolbar, text="🗑 Delete Field", font=('Segoe UI', 10),
                 bg=self.colors['danger'], fg='white',
                 command=self.delete_field_dialog, relief='flat', padx=15, pady=8).pack(side='left', padx=5)

        # Split view: Field list + JSON editor
        split_frame = tk.Frame(container, bg='white')
        split_frame.pack(fill='both', expand=True)

        # Left: Field list
        left_frame = tk.Frame(split_frame, bg='white')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        tk.Label(left_frame, text="Fields List:", font=('Segoe UI', 11, 'bold'),
                bg='white', fg=self.colors['primary'], anchor='w').pack(fill='x', pady=(0, 5))

        # Search bar
        search_frame = tk.Frame(left_frame, bg='white')
        search_frame.pack(fill='x', pady=(0, 10))

        tk.Label(search_frame, text="🔍", font=('Segoe UI', 12), bg='white').pack(side='left', padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_fields())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=('Segoe UI', 10))
        search_entry.pack(side='left', fill='x', expand=True)

        # Fields listbox with scrollbar
        list_frame = tk.Frame(left_frame, bg='white')
        list_frame.pack(fill='both', expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')

        self.fields_listbox = tk.Listbox(list_frame, font=('Consolas', 9),
                                         yscrollcommand=scrollbar.set, selectmode='single')
        self.fields_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.fields_listbox.yview)

        self.fields_listbox.bind('<<ListboxSelect>>', self.on_field_select)

        # Right: JSON editor
        right_frame = tk.Frame(split_frame, bg='white')
        right_frame.pack(side='left', fill='both', expand=True)

        tk.Label(right_frame, text="Configuration JSON:", font=('Segoe UI', 11, 'bold'),
                bg='white', fg=self.colors['primary'], anchor='w').pack(fill='x', pady=(0, 5))

        json_frame = tk.Frame(right_frame, bg='white')
        json_frame.pack(fill='both', expand=True)

        json_scrollbar = tk.Scrollbar(json_frame)
        json_scrollbar.pack(side='right', fill='y')

        self.json_text = scrolledtext.ScrolledText(json_frame, font=('Consolas', 9),
                                                   wrap='none', yscrollcommand=json_scrollbar.set)
        self.json_text.pack(fill='both', expand=True)
        json_scrollbar.config(command=self.json_text.yview)

        # Populate field list
        self.populate_fields_list()

        # Display JSON
        self.update_json_display()

    def populate_fields_list(self):
        """Populate the fields listbox"""
        self.fields_listbox.delete(0, tk.END)

        # Support both new field_configs and old data_types format
        if 'field_configs' in self.config_data:
            fields = sorted(self.config_data['field_configs'].keys())
            for field in fields:
                field_config = self.config_data['field_configs'][field]
                field_type = field_config.get('type', 'str')
                section = field_config.get('section', 'Unknown')
                display_text = f"{field:<35} [{field_type:<6}] ({section})"
                self.fields_listbox.insert(tk.END, display_text)
        elif 'data_types' in self.config_data:
            fields = sorted(self.config_data['data_types'].keys())
            for field in fields:
                field_type = self.config_data['data_types'][field][0] if self.config_data['data_types'][field] else 'unknown'
                display_text = f"{field:<40} [{field_type}]"
                self.fields_listbox.insert(tk.END, display_text)

    def filter_fields(self):
        """Filter fields based on search"""
        search_term = self.search_var.get().lower()
        self.fields_listbox.delete(0, tk.END)

        # Support both new field_configs and old data_types format
        if 'field_configs' in self.config_data:
            fields = sorted(self.config_data['field_configs'].keys())
            for field in fields:
                if search_term in field.lower() or search_term in self.config_data['field_configs'][field].get('section', '').lower():
                    field_config = self.config_data['field_configs'][field]
                    field_type = field_config.get('type', 'str')
                    section = field_config.get('section', 'Unknown')
                    display_text = f"{field:<35} [{field_type:<6}] ({section})"
                    self.fields_listbox.insert(tk.END, display_text)
        elif 'data_types' in self.config_data:
            fields = sorted(self.config_data['data_types'].keys())
            for field in fields:
                if search_term in field.lower():
                    field_type = self.config_data['data_types'][field][0] if self.config_data['data_types'][field] else 'unknown'
                    display_text = f"{field:<40} [{field_type}]"
                    self.fields_listbox.insert(tk.END, display_text)

    def on_field_select(self, event):
        """Handle field selection"""
        selection = self.fields_listbox.curselection()
        if selection:
            field_text = self.fields_listbox.get(selection[0])
            field_name = field_text.split('[')[0].strip()
            self.update_status(f"Selected: {field_name}")

    def update_json_display(self):
        """Update JSON text display"""
        self.json_text.delete('1.0', tk.END)
        json_str = json.dumps(self.config_data, indent=2)
        self.json_text.insert('1.0', json_str)

    def add_field_dialog(self):
        """Show dialog to add new field"""
        dialog = tk.Toplevel(self.root)
        dialog.title("➕ Add New Field")
        dialog.geometry("500x500")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="➕ Add New Field",
                font=('Segoe UI', 14, 'bold'), bg='white', fg=self.colors['primary']).pack(pady=20)

        # Form
        form = tk.Frame(dialog, bg='white')
        form.pack(fill='both', expand=True, padx=30)

        entries = {}
        fields_config = [
            ("Field Name", "name", "str", "e.g., 'CPU Frequency'"),
            ("Field Type", "type", "combo", ["str", "int", "float", "bool"]),
            ("Section", "section", "combo", ["Basic Information", "Test Configuration",
                                            "Advanced Configuration", "Voltage & Frequency",
                                            "Loops", "Sweep", "Shmoo", "Linux", "Dragon", "Merlin"]),
            ("Default Value", "default", "str", "Optional default value (type-appropriate)"),
            ("Description", "description", "str", "Field description/tooltip text"),
        ]

        for idx, (label, key, field_type, help_text) in enumerate(fields_config):
            tk.Label(form, text=f"{label}:", font=('Segoe UI', 10, 'bold'),
                    bg='white', anchor='w').grid(row=idx*2, column=0, sticky='w', pady=(10, 2))

            if field_type == "combo":
                var = tk.StringVar(value=help_text[0])
                widget = ttk.Combobox(form, textvariable=var, values=help_text, width=40, state='readonly')
            else:
                var = tk.StringVar()
                widget = tk.Entry(form, textvariable=var, width=43, font=('Segoe UI', 10))
                tk.Label(form, text=help_text, font=('Segoe UI', 8, 'italic'),
                        bg='white', fg='#666', anchor='w').grid(row=idx*2+1, column=0, columnspan=2, sticky='w')

            widget.grid(row=idx*2, column=1, sticky='ew', padx=5)
            entries[key] = var

        form.grid_columnconfigure(1, weight=1)

        # Buttons
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(fill='x', padx=30, pady=20)

        def add_field():
            field_name = entries['name'].get().strip()
            field_type = entries['type'].get()
            section = entries['section'].get()
            default_value = entries['default'].get().strip()
            description = entries['description'].get().strip()

            if not field_name:
                messagebox.showwarning("Missing Data", "Please enter a field name.")
                return

            # Check for duplicates in both formats
            if field_name in self.config_data.get('field_configs', {}):
                messagebox.showwarning("Duplicate", f"Field '{field_name}' already exists.")
                return
            if field_name in self.config_data.get('data_types', {}):
                messagebox.showwarning("Duplicate", f"Field '{field_name}' already exists.")
                return

            # Convert default value to appropriate type
            if default_value:
                try:
                    if field_type == 'int':
                        default_value = int(default_value)
                    elif field_type == 'float':
                        default_value = float(default_value)
                    elif field_type == 'bool':
                        default_value = default_value.lower() in ['true', '1', 'yes']
                except ValueError:
                    messagebox.showwarning("Invalid Default", f"Default value '{default_value}' is not a valid {field_type}")
                    return
            else:
                # Set type-appropriate defaults
                default_value = '' if field_type == 'str' else (0 if field_type == 'int' else (0.0 if field_type == 'float' else False))

            # Ensure we're using field_configs structure
            if 'field_configs' not in self.config_data:
                self.config_data['field_configs'] = {}

            # Add to config with full metadata
            self.config_data['field_configs'][field_name] = {
                'section': section,
                'type': field_type,
                'default': default_value,
                'description': description or f'{field_name} field',
                'required': False
            }

            self.modified = True

            # Refresh display
            self.populate_fields_list()
            self.update_json_display()

            messagebox.showinfo("Success", f"Field '{field_name}' added successfully!\n\n"
                                          f"Section: {section}\n"
                                          f"Type: {field_type}\n"
                                          f"Default: {default_value}")
            dialog.destroy()

        tk.Button(btn_frame, text="✓ Add Field", bg=self.colors['success'], fg='white',
                 command=add_field, font=('Segoe UI', 11, 'bold'),
                 relief='flat', padx=20, pady=10).pack(side='left', padx=5)

        tk.Button(btn_frame, text="✖ Cancel", bg=self.colors['danger'], fg='white',
                 command=dialog.destroy, font=('Segoe UI', 11),
                 relief='flat', padx=20, pady=10).pack(side='right', padx=5)

    def edit_field_dialog(self):
        """Edit selected field"""
        selection = self.fields_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a field to edit.")
            return

        field_text = self.fields_listbox.get(selection[0])
        field_name = field_text.split('[')[0].strip()

        messagebox.showinfo("Edit Field",
                           f"Editing field: {field_name}\n\n"
                           "Use the JSON editor on the right to modify the configuration directly.")

    def delete_field_dialog(self):
        """Delete selected field"""
        selection = self.fields_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a field to delete.")
            return

        field_text = self.fields_listbox.get(selection[0])
        field_name = field_text.split('[')[0].strip()

        if messagebox.askyesno("Confirm Delete", f"Delete field '{field_name}'?\n\nThis cannot be undone."):
            # Delete from whichever structure exists
            if 'field_configs' in self.config_data and field_name in self.config_data['field_configs']:
                del self.config_data['field_configs'][field_name]
            elif 'data_types' in self.config_data and field_name in self.config_data['data_types']:
                del self.config_data['data_types'][field_name]

            self.modified = True
            self.populate_fields_list()
            self.update_json_display()
            self.update_status(f"Deleted field: {field_name}")

    def export_config(self):
        """Export configuration to file"""
        file_path = filedialog.asksaveasfilename(
            title="Export Configuration",
            defaultextension=".json",
            initialfile=f"{self.current_tool}_config.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.config_data, f, indent=2)
                messagebox.showinfo("Success", f"Configuration exported to:\n{file_path}")
                self.update_status(f"Exported to {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export:\n{str(e)}")

    def import_config(self):
        """Import configuration from file"""
        file_path = filedialog.askopenfilename(
            title="Import Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    new_config = json.load(f)

                if messagebox.askyesno("Confirm Import",
                                      f"Import configuration from:\n{file_path}\n\n"
                                      "This will replace current configuration."):
                    self.config_data = new_config
                    self.modified = True
                    self.populate_fields_list()
                    self.update_json_display()
                    messagebox.showinfo("Success", "Configuration imported successfully!")
                    self.update_status(f"Imported from {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import:\n{str(e)}")

    def show_template_generator(self):
        """Show template generator for new tools"""
        container = tk.Frame(self.content_frame, bg='white')
        container.pack(fill='both', expand=True, padx=20, pady=20)

        tk.Label(container, text="📁 Template Generator",
                font=('Segoe UI', 16, 'bold'), bg='white', fg=self.colors['primary']).pack(pady=20)

        tk.Label(container, text="Generate boilerplate code for new PPV tools",
                font=('Segoe UI', 11), bg='white', fg='#666').pack(pady=10)

        # Template options
        templates = [
            ("GUI Tool Template", "Create a new GUI tool with standard layout", self.generate_gui_template),
            ("Parser Template", "Create a new parser with standard structure", self.generate_parser_template),
            ("Analyzer Template", "Create a new analyzer with standard methods", self.generate_analyzer_template),
        ]

        for title, desc, command in templates:
            frame = tk.Frame(container, bg='#f8fafc', relief='solid', bd=1)
            frame.pack(fill='x', pady=10)

            tk.Label(frame, text=title, font=('Segoe UI', 12, 'bold'),
                    bg='#f8fafc', fg=self.colors['primary'], anchor='w').pack(fill='x', padx=20, pady=10)

            tk.Label(frame, text=desc, font=('Segoe UI', 10),
                    bg='#f8fafc', fg='#666', anchor='w').pack(fill='x', padx=20, pady=(0, 10))

            tk.Button(frame, text="Generate Template", bg=self.colors['accent'], fg='white',
                     command=command, font=('Segoe UI', 10),
                     relief='flat', padx=15, pady=8).pack(anchor='e', padx=20, pady=10)

    def show_config_validator(self):
        """Show configuration validator"""
        container = tk.Frame(self.content_frame, bg='white')
        container.pack(fill='both', expand=True, padx=20, pady=20)

        tk.Label(container, text="✓ Configuration Validator",
                font=('Segoe UI', 16, 'bold'), bg='white', fg=self.colors['primary']).pack(pady=20)

        tk.Button(container, text="🔍 Run Validation", bg=self.colors['success'], fg='white',
                 command=self.run_validation, font=('Segoe UI', 12, 'bold'),
                 relief='flat', padx=30, pady=15).pack(pady=20)

        # Results area
        self.validation_text = scrolledtext.ScrolledText(container, font=('Consolas', 9), height=30)
        self.validation_text.pack(fill='both', expand=True, pady=10)

    def run_validation(self):
        """Run configuration validation"""
        self.validation_text.delete('1.0', tk.END)
        self.validation_text.insert('1.0', "Running validation...\n\n")
        self.root.update()

        results = []
        results.append("=" * 80)
        results.append("PPV Tools Configuration Validation Report")
        results.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        results.append("=" * 80)
        results.append("")

        # Validate ExperimentBuilder
        results.append("📝 ExperimentBuilder Configuration")
        results.append("-" * 80)
        try:
            from PPV.gui.ExperimentBuilder import ExperimentBuilderGUI
            temp = ExperimentBuilderGUI()
            config = temp.config_template
            temp.root.destroy()

            results.append("✓ Config loaded successfully")
            results.append(f"✓ Fields defined: {len(config.get('data_types', {}))}")
            results.append(f"✓ Test modes: {len(config.get('TEST_MODES', []))}")
            results.append(f"✓ Test types: {len(config.get('TEST_TYPES', []))}")
        except Exception as e:
            results.append(f"✗ Error: {str(e)}")
        results.append("")

        # Check file structure
        results.append("📁 File Structure Validation")
        results.append("-" * 80)

        required_dirs = [
            'PPV/gui',
            'PPV/parsers',
            'PPV/utils',
            'PPV/Decoder',
            'PPV/api'
        ]

        ppv_root = os.path.dirname(os.path.dirname(__file__))
        for dir_path in required_dirs:
            full_path = os.path.join(ppv_root, dir_path)
            if os.path.exists(full_path):
                results.append(f"✓ {dir_path}")
            else:
                results.append(f"✗ {dir_path} (missing)")

        results.append("")
        results.append("=" * 80)
        results.append("Validation Complete")
        results.append("=" * 80)

        self.validation_text.delete('1.0', tk.END)
        self.validation_text.insert('1.0', '\n'.join(results))

    def show_generic_config_editor(self, tool_id):
        """Show generic configuration editor for other tools"""
        container = tk.Frame(self.content_frame, bg='white')
        container.pack(fill='both', expand=True, padx=20, pady=20)

        tk.Label(container, text=f"🔧 {tool_id.replace('_', ' ').title()} Configuration",
                font=('Segoe UI', 16, 'bold'), bg='white', fg=self.colors['primary']).pack(pady=20)

        tk.Label(container, text="Configuration editor coming soon...",
                font=('Segoe UI', 11), bg='white', fg='#666').pack(pady=10)

    def generate_gui_template(self):
        """Generate GUI tool template"""
        messagebox.showinfo("Template Generator", "GUI template generation - Coming soon!")

    def generate_parser_template(self):
        """Generate parser template"""
        messagebox.showinfo("Template Generator", "Parser template generation - Coming soon!")

    def generate_analyzer_template(self):
        """Generate analyzer template"""
        messagebox.showinfo("Template Generator", "Analyzer template generation - Coming soon!")

    def open_config_folder(self):
        """Open configuration folder"""
        ppv_root = os.path.dirname(os.path.dirname(__file__))
        os.startfile(ppv_root)

    def backup_all_configs(self):
        """Backup all configurations"""
        backup_dir = filedialog.askdirectory(title="Select Backup Location")
        if backup_dir:
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = os.path.join(backup_dir, f"ppv_config_backup_{timestamp}")

                # Create backup
                ppv_root = os.path.dirname(os.path.dirname(__file__))
                shutil.copytree(
                    ppv_root,
                    backup_path,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git')
                )

                messagebox.showinfo("Success", f"Backup created at:\n{backup_path}")
                self.update_status(f"Backup created: {timestamp}")
            except Exception as e:
                messagebox.showerror("Backup Error", f"Failed to create backup:\n{str(e)}")

    def refresh_all_tools(self):
        """Refresh all tool configurations"""
        if messagebox.askyesno("Refresh All", "Reload all tool configurations?\n\nUnsaved changes will be lost."):
            self.config_data = {}
            self.modified = False
            if self.current_tool:
                self.load_tool(self.current_tool)
            else:
                self.show_welcome_screen()
            self.update_status("Refreshed all tools")

    def get_default_experiment_config(self):
        """Get default ExperimentBuilder config with enhanced field metadata"""
        return {
            "field_configs": {},
            "TEST_MODES": ["Mesh", "Slice"],
            "TEST_TYPES": ["Loops", "Sweep", "Shmoo"],
            "CONTENT_OPTIONS": ["Linux", "Dragon", "PYSVConsole"]
        }

    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    app = DeveloperEnvironmentGUI()
    app.run()


if __name__ == '__main__':
    main()
