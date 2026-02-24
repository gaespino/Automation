"""
Fuse File UI - Engineering Tools Interface

Interactive GUI for selecting, filtering, and generating fuse configuration files.
Part of the PPV Engineering Tools suite.

Features:
- Load and display fuse data from CSV files
- Column selection and filtering
- Search by description or instance
- Table view with sortable columns
- Selection tools (select all, clear all, select filtered, clear filtered)
- Fuse generation with product-specific IP configuration
- Support for GNR, CWF, and DMR products

Author: Engineering Tools Team
Date: February 2026
"""

import sys
import os

# Add parent directory to path for imports
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import List, Dict, Optional, Set

try:
    from ..utils.fusefilegenerator import FuseFileGenerator, load_product_fuses, validate_fuse_value
    from ..utils.status_bar import StatusBar
except ImportError:
    from utils.fusefilegenerator import FuseFileGenerator, load_product_fuses, validate_fuse_value
    from utils.status_bar import StatusBar


class FuseFileUI:
    """Main UI for Fuse File Generator tool"""

    # Engineering Tools color scheme
    ENGINEERING_COLOR = '#e67e22'  # Orange theme for engineering tools
    ENGINEERING_DARK = '#d35400'
    ENGINEERING_LIGHT = '#f39c12'

    def __init__(self, parent: Optional[tk.Tk] = None, default_product: str = 'GNR'):
        """
        Initialize the Fuse File UI.

        Args:
            parent: Tkinter parent window (creates one if None)
            default_product: Default product to load (GNR, CWF, or DMR)
        """
        if parent is None:
            self.root = tk.Tk()
            self.standalone = True
        else:
            self.root = tk.Toplevel(parent)
            self.standalone = False

        self.default_product = default_product
        self.generator: Optional[FuseFileGenerator] = None
        self.current_data: List[Dict] = []
        self.filtered_data: List[Dict] = []
        self.selected_fuse_ids: Set[str] = set()  # Store fuse IDs instead of indices
        self.display_columns: List[str] = []
        self.column_filters: Dict[str, str] = {}  # Column-specific filters

        # Pre-filters (applied before showing data)
        self.pre_filters = {
            'instance': '',
            'description': '',
            'ip': ''
        }

        self._setup_window()
        self._create_widgets()

        # Auto-load product data only if a default product was specified
        if self.default_product:
            self._load_product_data(self.default_product)

    def _setup_window(self):
        """Configure main window"""
        self.root.title("Fuse File Generator - Engineering Tools")
        self.root.geometry("1400x900")
        self.root.state('zoomed')

        # Configure grid weights
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

    def _create_widgets(self):
        """Create all UI widgets"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.rowconfigure(3, weight=1)  # Changed from row 2 to row 3
        main_frame.columnconfigure(0, weight=1)

        # Header
        self._create_header(main_frame)

        # Content notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)

        # Tab 1: Data Selection & Filtering
        self.data_tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.data_tab, text="📊 Data Selection & Filtering")
        self._create_data_tab()

        # Footer
        self._create_footer(main_frame)

    def _create_header(self, parent):
        """Create header section with THR tools standard styling"""
        # Colored accent line at top (matching other tools)
        header_accent = tk.Frame(parent, bg=self.ENGINEERING_COLOR, height=12)
        header_accent.grid(row=0, column=0, sticky="ew")
        header_accent.grid_propagate(False)

        # Configuration section
        config_frame = tk.LabelFrame(
            parent,
            text="Configuration",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=15
        )
        config_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 0))

        # Product selection with combobox (matching other tools)
        tk.Label(
            config_frame,
            text="Product:",
            font=("Segoe UI", 9)
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.product_var = tk.StringVar(value=self.default_product)
        product_combo = ttk.Combobox(
            config_frame,
            textvariable=self.product_var,
            values=['GNR', 'CWF', 'DMR'],
            state='readonly',
            width=15
        )
        product_combo.grid(row=0, column=1, sticky="w", padx=(0, 20))
        product_combo.bind('<<ComboboxSelected>>', lambda e: self._on_product_change())

        # Fuse files location display
        tk.Label(
            config_frame,
            text="Fuse Files:",
            font=("Segoe UI", 9)
        ).grid(row=0, column=2, sticky="w", padx=(20, 10))

        self.fuse_location_var = tk.StringVar(value="configs/fuses/")
        tk.Entry(
            config_frame,
            textvariable=self.fuse_location_var,
            font=("Segoe UI", 9),
            width=35,
            state='readonly',
            relief=tk.FLAT,
            bg='#f0f0f0'
        ).grid(row=0, column=3, sticky="w", padx=(0, 5))

        tk.Button(
            config_frame,
            text="📁",
            command=self._browse_fuse_location,
            font=("Segoe UI", 9),
            width=3,
            cursor="hand2"
        ).grid(row=0, column=4, sticky="w")

        # Info label on next row
        tk.Label(
            config_frame,
            text="Folder structure: GNR/CWF (compute.csv, io.csv) | DMR (cbbsbase.csv, cbbstop.csv, imhs.csv)",
            font=("Segoe UI", 8),
            foreground="gray"
        ).grid(row=1, column=0, columnspan=5, sticky="w", pady=(5, 0))

        # Status message bar (below configuration) - using StatusBar component
        self.status_bar = StatusBar(parent, height=50)
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 5))

    def _show_status(self, message: str, msg_type: str = 'info'):
        """Show a status message in the status bar

        Args:
            message: Message to display
            msg_type: Type of message - 'info', 'success', 'warning', 'error'
        """
        self.status_bar.show(message, msg_type)

    def _create_data_tab(self):
        """Create the main data selection and filtering tab"""
        self.data_tab.rowconfigure(3, weight=1)
        self.data_tab.columnconfigure(0, weight=1)

        # Control panel - simplified with indicators only
        control_frame = tk.Frame(self.data_tab, bg='white', padx=10, pady=10)
        control_frame.grid(row=0, column=0, sticky="ew")
        control_frame.columnconfigure(2, weight=1)

        # Filter configuration button
        tk.Button(
            control_frame,
            text="⚙️ Configure Filters",
            command=self._open_filter_config,
            bg=self.ENGINEERING_COLOR,
            fg='white',
            font=("Segoe UI", 9, "bold"),
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        ).grid(row=0, column=0, padx=5, sticky="w")

        # Column selector button
        tk.Button(
            control_frame,
            text="📋 Select Columns",
            command=self._open_column_selector,
            bg=self.ENGINEERING_COLOR,
            fg='white',
            font=("Segoe UI", 9, "bold"),
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        ).grid(row=0, column=1, padx=5, sticky="w")

        # Status indicators frame
        status_frame = tk.Frame(control_frame, bg='#ecf0f1', relief=tk.RIDGE, bd=1)
        status_frame.grid(row=0, column=2, sticky="ew", padx=(20, 0))
        status_frame.columnconfigure(1, weight=1)

        # Active filters indicator
        tk.Label(
            status_frame,
            text="Active Filters:",
            font=("Segoe UI", 9, "bold"),
            bg='#ecf0f1'
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.filter_indicator = tk.Label(
            status_frame,
            text="None",
            font=("Segoe UI", 9),
            bg='#ecf0f1',
            fg='#7f8c8d',
            anchor='w'
        )
        self.filter_indicator.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Column count indicator
        tk.Label(
            status_frame,
            text="Columns:",
            font=("Segoe UI", 9, "bold"),
            bg='#ecf0f1'
        ).grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.column_indicator = tk.Label(
            status_frame,
            text="0 selected",
            font=("Segoe UI", 9),
            bg='#ecf0f1',
            fg='#7f8c8d',
            anchor='w'
        )
        self.column_indicator.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Show Data button (applies filters and displays)
        tk.Button(
            control_frame,
            text="🔄 Apply & Show Data",
            command=self._apply_filters_and_show,
            bg=self.ENGINEERING_DARK,
            fg='white',
            font=("Segoe UI", 10, "bold"),
            padx=25,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2"
        ).grid(row=0, column=3, padx=10, sticky="e")

        # Info banner about column filtering
        info_banner = tk.Frame(self.data_tab, bg='#d4edda', relief=tk.RIDGE, bd=1)
        info_banner.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 0))

        tk.Label(
            info_banner,
            text="💡 Click on any column header to filter that column. Filtered columns will show a 🔽 indicator.",
            font=("Segoe UI", 9),
            bg='#d4edda',
            fg='#155724',
            anchor='w'
        ).pack(padx=10, pady=8, fill=tk.X)

        # Search panel (for quick searching within displayed data)
        search_frame = tk.Frame(self.data_tab, bg='#ecf0f1', padx=10, pady=10)
        search_frame.grid(row=2, column=0, sticky="ew")
        search_frame.columnconfigure(1, weight=1)

        tk.Label(
            search_frame,
            text="🔍 Quick Search (in displayed data):",
            font=("Segoe UI", 9, "bold"),
            bg='#ecf0f1'
        ).grid(row=0, column=0, padx=(0, 10))

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            width=50
        )
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        search_entry.bind('<Return>', lambda e: self._apply_search())

        tk.Button(
            search_frame,
            text="Search",
            command=self._apply_search,
            bg=self.ENGINEERING_COLOR,
            fg='white',
            font=("Segoe UI", 9, "bold"),
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        ).grid(row=0, column=2, padx=5)

        tk.Button(
            search_frame,
            text="Clear Search",
            command=self._clear_search,
            bg='#95a5a6',
            fg='white',
            font=("Segoe UI", 9),
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        ).grid(row=0, column=3)

        tk.Button(
            search_frame,
            text="Clear All Column Filters",
            command=self._clear_all_column_filters,
            bg='#e74c3c',
            fg='white',
            font=("Segoe UI", 9),
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        ).grid(row=0, column=4, padx=5)

        # Data table with filters
        table_frame = tk.Frame(self.data_tab, bg='white')
        table_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        table_frame.rowconfigure(1, weight=1)  # Tree row gets all space
        table_frame.columnconfigure(0, weight=1)

        # Inline filter row frame (will be populated when columns are shown)
        self.filter_row_frame = tk.Frame(table_frame, bg='#f8f9fa', relief=tk.RIDGE, bd=1)
        self.filter_row_frame.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        self.inline_filter_vars = {}  # Will store StringVars for each column filter

        # Scrollable tree container
        tree_container = tk.Frame(table_frame, bg='white')
        tree_container.grid(row=1, column=0, sticky="nsew")

        # Create treeview with scrollbars
        tree_scroll_y = tk.Scrollbar(tree_container)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        tree_scroll_x = tk.Scrollbar(tree_container, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree = ttk.Treeview(
            tree_container,
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            selectmode='extended',
            show='tree headings'
        )
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure Excel-like styling
        style = ttk.Style()
        style.configure("Treeview",
                       background="white",
                       foreground="black",
                       rowheight=25,
                       fieldbackground="white",
                       borderwidth=1,
                       relief="solid")
        style.configure("Treeview.Heading",
                       background="#e8e8e8",
                       foreground="#2c3e50",
                       relief="raised",
                       borderwidth=1,
                       font=("Segoe UI", 9, "bold"))
        style.map('Treeview',
                 background=[('selected', '#0078d7')],
                 foreground=[('selected', 'white')])
        style.map('Treeview.Heading',
                 background=[('active', '#d0d0d0')])

        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        # Selection toolbar
        selection_frame = tk.Frame(self.data_tab, bg='#ecf0f1', padx=10, pady=10)
        selection_frame.grid(row=4, column=0, sticky="ew")

        self.selection_label = tk.Label(
            selection_frame,
            text="Selected: 0 fuses",
            font=("Segoe UI", 9, "bold"),
            bg='#ecf0f1'
        )
        self.selection_label.pack(side=tk.LEFT, padx=(0, 20))

        # Add Selection button (adds currently highlighted rows to selection)
        tk.Button(
            selection_frame,
            text="➕ Add Selection",
            command=self._add_highlighted_to_selection,
            bg='#27ae60',
            fg='white',
            font=("Segoe UI", 9, "bold"),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        # View/Manage Selection button
        tk.Button(
            selection_frame,
            text="📋 View & Manage Selection",
            command=self._open_selection_viewer,
            bg='#3498db',
            fg='white',
            font=("Segoe UI", 9, "bold"),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        # Start Fuse Generation button
        tk.Button(
            selection_frame,
            text="▶ Start Fuse Generation",
            command=self._start_fuse_generation,
            bg=self.ENGINEERING_COLOR,
            fg='white',
            font=("Segoe UI", 10, "bold"),
            padx=25,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=5)

    def _create_footer(self, parent):
        """Create footer with action buttons"""
        footer_frame = tk.Frame(parent, bg='#ecf0f1', pady=10)
        footer_frame.grid(row=4, column=0, sticky="ew")  # Changed from row 3 to row 4

        tk.Button(
            footer_frame,
            text="💾 Import Configuration",
            command=self._import_configuration,
            bg='#3498db',
            fg='white',
            font=("Segoe UI", 9),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            footer_frame,
            text="📤 Export Configuration",
            command=self._export_configuration,
            bg='#16a085',
            fg='white',
            font=("Segoe UI", 9),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            footer_frame,
            text="Export to CSV",
            command=self._export_csv,
            bg='#27ae60',
            fg='white',
            font=("Segoe UI", 9),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            footer_frame,
            text="Close",
            command=self._on_close,
            bg='#7f8c8d',
            fg='white',
            font=("Segoe UI", 9),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=10)

    def _browse_fuse_location(self):
        """Browse for custom fuse file location"""
        directory = filedialog.askdirectory(
            title="Select Fuse Files Directory",
            initialdir=self.fuse_location_var.get()
        )

        if directory:
            self.fuse_location_var.set(directory)
            product = self.product_var.get()
            if messagebox.askyesno(
                "Reload Fuses",
                f"Load {product} fuses from:\n{directory}\n\nExpected files:\n" +
                ("• compute.csv, io.csv" if product in ['GNR', 'CWF'] else "• cbbsbase.csv, cbbstop.csv, imhs.csv")
            ):
                self._load_product_data_from_path(product, directory)

    def _load_product_data(self, product: str):
        """Load fuse data for the specified product from default location"""
        default_path = f"configs/fuses/{product.lower()}"
        self.fuse_location_var.set(default_path)
        self._load_product_data_from_path(product, default_path)

    def _load_product_data_from_path(self, product: str, path: str):
        """Load fuse data for the specified product from given path"""
        try:
            # Show loading message
            self.root.config(cursor="wait")
            self.root.update()

            self.generator = load_product_fuses(product)

            if self.generator:
                self.current_data = self.generator.fuse_data.copy()

                # Pre-compute fuse IDs and initialize selection/value columns for performance
                for idx, row in enumerate(self.current_data):
                    row['_fuse_id'] = f"{row.get('IP_Origin', '')}_{row.get('Instance', '')}_{row.get('ip_name', '')}_{idx}"
                    row['selected'] = False  # Initialize selection state

                    # Initialize default value from fuse data or use 0x0
                    default_val = row.get('default', '')
                    if default_val and str(default_val).strip().lower() not in ['', 'none', 'null']:
                        # Convert to hex if needed
                        if not str(default_val).startswith('0x'):
                            try:
                                default_val = f"0x{int(default_val):X}"
                            except (ValueError, TypeError):
                                default_val = '0x0'
                    else:
                        default_val = '0x0'
                    row['value'] = default_val

                self.filtered_data = self.current_data.copy()

                # Reset filters
                self.pre_filters = {'instance': '', 'description': '', 'ip': ''}
                self._update_filter_indicator()

                # Set default columns if not already set
                if not self.display_columns:
                    default_cols = ['IP_Origin', 'ip_name', 'Instance', 'description']
                    available_cols = self.generator.get_available_columns()
                    self.display_columns = [col for col in default_cols if col in available_cols]
                    self._update_column_indicator()

                # Show statistics
                stats = self.generator.get_statistics()
                ip_summary = ", ".join([f"{ip}({count})" for ip, count in stats['ip_origins'].items()])
                self._show_status(
                    f"✓ Loaded {stats['total_fuses']} fuses from {stats['files_loaded']} files | Location: {path}",
                    'success'
                )
            else:
                self._show_status(
                    f"✗ Failed to load fuse data from: {path}",
                    'error'
                )

        finally:
            self.root.config(cursor="")

    def _open_filter_config(self):
        """Open filter configuration window"""
        if not self.generator:
            self._show_status("⚠ Please load product data first", 'warning')
            return

        FilterConfigWindow(self.root, self)

    def _open_column_selector(self):
        """Open column selector window"""
        if not self.generator:
            self._show_status("⚠ Please load product data first", 'warning')
            return

        ColumnSelectorWindow(self.root, self)

    def _update_filter_indicator(self):
        """Update the filter status indicator"""
        active_filters = []
        if self.pre_filters['instance']:
            active_filters.append(f"Instance: {self.pre_filters['instance']}")
        if self.pre_filters['description']:
            active_filters.append(f"Description: {self.pre_filters['description']}")
        if self.pre_filters['ip']:
            active_filters.append(f"IP: {self.pre_filters['ip']}")

        if active_filters:
            self.filter_indicator.config(
                text=" | ".join(active_filters),
                fg='#27ae60'
            )
        else:
            self.filter_indicator.config(
                text="None",
                fg='#7f8c8d'
            )

    def _update_column_indicator(self):
        """Update the column count indicator"""
        count = len(self.display_columns)
        if count > 0:
            self.column_indicator.config(
                text=f"{count} selected: {', '.join(self.display_columns[:3])}{'...' if count > 3 else ''}",
                fg='#27ae60'
            )
        else:
            self.column_indicator.config(
                text="0 selected",
                fg='#e74c3c'
            )

    def _apply_filters_and_show(self):
        """Apply pre-filters and show the data"""
        if not self.generator:
            self._show_status("⚠ Please load product data first", 'warning')
            return

        if not self.display_columns:
            self._show_status("⚠ Please select at least one column to display", 'warning')
            return

        # Start with all data
        filtered = self.current_data.copy()

        # Apply pre-filters
        if self.pre_filters['instance']:
            filtered = [row for row in filtered
                       if self.pre_filters['instance'].lower() in str(row.get('Instance', '')).lower()]

        if self.pre_filters['description']:
            filtered = [row for row in filtered
                       if self.pre_filters['description'].lower() in str(row.get('description', '')).lower()]

        if self.pre_filters['ip']:
            filtered = [row for row in filtered
                       if self.pre_filters['ip'].lower() in str(row.get('IP_Origin', '')).lower()]

        # Update filtered data
        self.filtered_data = filtered

        # Note: Keep selections (no need to clear since we use fuse IDs now)

        # Display the data
        self._show_data()

        self._show_status(
            f"✓ Showing {len(self.filtered_data)} fuses (filtered from {len(self.current_data)} total) | {len(self.display_columns)} columns",
            'success'
        )

    def _show_data(self):
        """Display data in table with selected columns"""
        if not self.display_columns:
            self._show_status("⚠ Please select columns first using 'Select Columns' button", 'warning')
            return

        # Clear existing tree
        self.tree.delete(*self.tree.get_children())

        # Configure columns
        self.tree['columns'] = self.display_columns
        self.tree['show'] = 'headings'  # Hide tree column

        # Clear and rebuild inline filter row
        for widget in self.filter_row_frame.winfo_children():
            widget.destroy()
        self.inline_filter_vars.clear()

        # Create filter entries for each column
        for idx, col in enumerate(self.display_columns):
            # Display column name with filter indicator
            display_text = col
            if col in self.column_filters and self.column_filters[col]:
                display_text = f"🔽 {col} 🔽"

            self.tree.heading(col, text=display_text)

            # Set column widths based on content type
            if col == 'IP_Origin':
                col_width = 120
                self.tree.column(col, width=col_width, minwidth=100, stretch=True)
            elif col == 'Instance':
                col_width = 250
                self.tree.column(col, width=col_width, minwidth=150, stretch=True)
            elif col == 'ip_name':
                col_width = 180
                self.tree.column(col, width=col_width, minwidth=120, stretch=True)
            elif col == 'description':
                col_width = 450
                self.tree.column(col, width=col_width, minwidth=250, stretch=True)
            elif col == 'FUSE_WIDTH':
                col_width = 100
                self.tree.column(col, width=col_width, minwidth=80, stretch=False)
            else:
                col_width = 150
                self.tree.column(col, width=col_width, minwidth=100, stretch=True)

            # Create inline filter entry for this column
            filter_var = tk.StringVar()
            if col in self.column_filters:
                filter_var.set(self.column_filters[col])

            self.inline_filter_vars[col] = filter_var

            # Filter entry with proper sizing
            filter_entry = tk.Entry(
                self.filter_row_frame,
                textvariable=filter_var,
                font=("Segoe UI", 8),
                relief=tk.SOLID,
                bd=1,
                bg='white'
            )
            filter_entry.grid(row=0, column=idx, sticky="ew", padx=1, pady=2)
            self.filter_row_frame.columnconfigure(idx, weight=1, minsize=col_width)

            # Bind Enter key to apply filter
            filter_entry.bind('<Return>', lambda e, c=col: self._apply_inline_filter(c))
            filter_entry.bind('<KeyRelease>', lambda e, c=col: self._apply_inline_filter_delayed(c))

        # Populate data
        self._populate_tree()

    def _apply_inline_filter(self, column):
        """Apply filter from inline filter entry"""
        filter_value = self.inline_filter_vars[column].get().strip()
        if filter_value:
            self.column_filters[column] = filter_value
        elif column in self.column_filters:
            del self.column_filters[column]
        self._apply_column_filters()
        self._show_data()  # Refresh to update filter indicators

    def _apply_inline_filter_delayed(self, column):
        """Apply filter after a short delay (for live filtering)"""
        # Cancel any existing delayed filter
        if hasattr(self, '_filter_timer'):
            self.root.after_cancel(self._filter_timer)
        # Set new timer (500ms delay)
        self._filter_timer = self.root.after(500, lambda: self._apply_inline_filter(column))

    def _create_filter_row(self):
        """Create filter input row at top of tree (simulated)"""
        # Note: Treeview doesn't support widgets in cells, so we'll handle filtering via search
        pass

    def _populate_tree(self):
        """Populate treeview with current filtered data with Excel-like alternating rows"""
        self.tree.delete(*self.tree.get_children())

        for idx, row in enumerate(self.filtered_data):
            # Get fuse ID from pre-computed value
            fuse_id = row.get('_fuse_id', f"{row.get('IP_Origin', '')}_{row.get('Instance', '')}_{idx}")

            # Get values and fix multiline descriptions
            values = []
            for col in self.display_columns:
                value = row.get(col, '')
                # Remove newlines and excessive whitespace from descriptions
                if isinstance(value, str):
                    value = ' '.join(value.split())
                values.append(value)

            # Tag rows with alternating colors and selection
            tags = [fuse_id]

            # Add alternating row color (Excel-like)
            if idx % 2 == 0:
                tags.append('evenrow')
            else:
                tags.append('oddrow')

            # Mark selected rows
            if row.get('selected', False):
                tags.append('selected')

            item_id = self.tree.insert('', tk.END, values=values, tags=tuple(tags))

        # Configure tag styling for Excel-like appearance
        self.tree.tag_configure('evenrow', background='#ffffff')
        self.tree.tag_configure('oddrow', background='#f7f7f7')
        self.tree.tag_configure('selected', background='#cfe2ff', foreground='#084298')

    def _apply_search(self):
        """Apply search filter"""
        search_term = self.search_var.get().strip()

        if not search_term:
            self.filtered_data = self.current_data.copy()
        else:
            # Search in displayed columns only
            search_columns = self.display_columns if self.display_columns else None
            self.filtered_data = self.generator.search_fuses(search_term, search_columns)

        self._populate_tree()
        self._update_selection_label()

    def _clear_search(self):
        """Clear search and show all data"""
        self.search_var.set('')
        self.filtered_data = self.current_data.copy()
        self._populate_tree()
        self._update_selection_label()

    def _open_column_filter(self, col):
        """Open filter dialog for specific column"""
        ColumnFilterDialog(self.root, self, col)

    def _apply_column_filters(self):
        """Apply all active column filters to data"""
        # Start with current_data (which already has pre-filters applied)
        filtered = self.current_data.copy()

        # Apply each column filter
        for col, filter_value in self.column_filters.items():
            if filter_value:  # Only apply non-empty filters
                filtered = [row for row in filtered
                           if filter_value.lower() in str(row.get(col, '')).lower()]

        self.filtered_data = filtered
        self._populate_tree()
        self._update_selection_label()

    def _clear_column_filter(self, col):
        """Clear filter for specific column"""
        if col in self.column_filters:
            del self.column_filters[col]
        self._apply_column_filters()
        self._show_data()  # Refresh to update heading display

    def _clear_all_column_filters(self):
        """Clear all column filters"""
        self.column_filters.clear()
        self.filtered_data = self.current_data.copy()
        self._populate_tree()
        self._update_selection_label()
        self._show_data()  # Refresh to update heading display

    def _sort_column(self, col):
        """Sort treeview by column with progress indication"""
        # Disable sorting for large datasets to prevent hanging
        item_count = len(self.tree.get_children(''))
        if item_count > 1000:
            self._show_status(
                f"⚠ Sorting disabled for {item_count} rows (max 1000). Use filters to reduce dataset size",
                'warning'
            )
            return

        # Show busy cursor
        self.root.config(cursor="watch")
        self.root.update()

        try:
            # Get data with current column
            data = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]

            # Try numeric sort first, fall back to string sort
            try:
                data.sort(key=lambda x: float(x[0]) if x[0] else 0, reverse=False)
            except (ValueError, TypeError):
                data.sort(key=lambda x: str(x[0]).lower(), reverse=False)

            # Rearrange items in sorted positions
            for index, (val, item) in enumerate(data):
                self.tree.move(item, '', index)
        finally:
            # Restore normal cursor
            self.root.config(cursor="")

    def _add_highlighted_to_selection(self):
        """Add currently highlighted rows to the selection"""
        # Get all highlighted items in the tree
        highlighted_items = self.tree.selection()

        if not highlighted_items:
            self._show_status("⚠ Please highlight rows in the table (click or Ctrl+Click) before adding to selection", 'warning')
            return

        # Add each highlighted item to selection
        added_count = 0
        for item in highlighted_items:
            tags = self.tree.item(item, 'tags')
            if tags:
                fuse_id = tags[0]
                # Find and mark row as selected
                for row in self.current_data:
                    if row.get('_fuse_id') == fuse_id and not row.get('selected', False):
                        row['selected'] = True
                        self.selected_fuse_ids.add(fuse_id)  # Keep set in sync
                        added_count += 1
                        break

        # Update display
        self._populate_tree()
        self._update_selection_label()

        if added_count > 0:
            self._show_status(f"✓ Added {added_count} fuse(s) to selection", 'success')

    def _open_selection_viewer(self):
        """Open selection viewer window"""
        SelectionViewerWindow(self.root, self)

    def _update_selection_label(self):
        """Update selection count label"""
        count = sum(1 for row in self.current_data if row.get('selected', False))
        self.selection_label.config(text=f"Selected: {count} fuses")

    def _start_fuse_generation(self):
        """Open fuse generation configuration window"""
        # Get selected fuses
        selected_fuses = [row for row in self.current_data if row.get('selected', False)]

        if not selected_fuses:
            self._show_status("⚠ Please select at least one fuse to generate configuration", 'warning')
            return

        # Open generation window
        FuseGenerationWindow(self.root, self.generator, selected_fuses, self.product_var.get())

    def _export_csv(self):
        """Export current filtered data to CSV"""
        if not self.filtered_data:
            self._show_status("⚠ No data to export", 'warning')
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export to CSV"
        )

        if filename:
            columns = self.display_columns if self.display_columns else None
            if self.generator.export_to_csv(self.filtered_data, filename, columns):
                self._show_status(f"✓ Exported {len(self.filtered_data)} fuses to: {filename}", 'success')

    def _export_configuration(self):
        """Export current data with selection and value columns for later import"""
        if not self.current_data:
            self._show_status("⚠ No data to export", 'warning')
            return

        # Create options dialog
        options_window = tk.Toplevel(self.root)
        options_window.title("Export Options")
        options_window.geometry("400x250")
        options_window.transient(self.root)
        options_window.grab_set()

        # Center the dialog
        options_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (options_window.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (options_window.winfo_height() // 2)
        options_window.geometry(f"+{x}+{y}")

        tk.Label(
            options_window,
            text="Export Configuration Options",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=15)

        # Column selection option
        column_var = tk.StringVar(value="selected")

        tk.Radiobutton(
            options_window,
            text="Export with selected columns only (current view)",
            variable=column_var,
            value="selected",
            font=("Segoe UI", 10)
        ).pack(anchor='w', padx=30, pady=5)

        tk.Radiobutton(
            options_window,
            text="Export with all available columns",
            variable=column_var,
            value="all",
            font=("Segoe UI", 10)
        ).pack(anchor='w', padx=30, pady=5)

        # Index column option
        index_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_window,
            text="Include index column (for tracking)",
            variable=index_var,
            font=("Segoe UI", 10)
        ).pack(anchor='w', padx=30, pady=10)

        tk.Label(
            options_window,
            text="Note: 'selected' and 'value' columns are always included",
            font=("Segoe UI", 8),
            foreground="gray"
        ).pack(pady=5)

        # Buttons
        button_frame = tk.Frame(options_window)
        button_frame.pack(pady=15)

        result = {'export': False}

        def do_export():
            result['export'] = True
            result['columns'] = column_var.get()
            result['include_index'] = index_var.get()
            options_window.destroy()

        tk.Button(
            button_frame,
            text="Export",
            command=do_export,
            bg='#16a085',
            fg='white',
            font=("Segoe UI", 9),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="Cancel",
            command=options_window.destroy,
            bg='#7f8c8d',
            fg='white',
            font=("Segoe UI", 9),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

        # Wait for dialog to close
        self.root.wait_window(options_window)

        if not result['export']:
            return

        # Proceed with export
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Configuration",
            initialfile=f"{self.product_var.get()}_config.csv"
        )

        if not filename:
            return

        try:
            import csv

            # Determine columns to export
            if result['columns'] == 'selected':
                export_columns = self.display_columns.copy() if self.display_columns else []
            else:
                export_columns = self.generator.get_available_columns()

            # Add index column if requested
            if result['include_index']:
                export_columns.insert(0, 'index')

            # Ensure selected and value columns are included
            if 'selected' not in export_columns:
                export_columns.append('selected')
            if 'value' not in export_columns:
                export_columns.append('value')

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=export_columns, extrasaction='ignore')
                writer.writeheader()

                for idx, row in enumerate(self.current_data):
                    export_row = row.copy()
                    if result['include_index']:
                        export_row['index'] = idx
                    writer.writerow(export_row)
        except Exception as e:
            self._show_status(f"✗ Export failed: {str(e)}", 'error')

    def _validate_fuse_value(self, value: str, fuse_width, numbits) -> tuple:
        """Validate a fuse value against bit width. Returns (is_valid, error_message)"""
        if not value or str(value).strip().lower() in ['', 'none', 'null']:
            return True, None

        # Get bit width
        bit_width = None
        if fuse_width:
            try:
                bit_width = int(fuse_width)
            except (ValueError, TypeError):
                pass
        if bit_width is None and numbits:
            try:
                bit_width = int(numbits)
            except (ValueError, TypeError):
                pass

        if bit_width is None:
            return True, None  # Can't validate without width

        # Parse value
        try:
            value_str = str(value).strip()
            if value_str.startswith('0x') or value_str.startswith('0X'):
                int_val = int(value_str, 16)
            elif value_str.startswith('0b') or value_str.startswith('0B'):
                int_val = int(value_str, 2)
            else:
                int_val = int(value_str)

            # Check if value fits in bit width
            max_val = (2 ** bit_width) - 1
            if int_val < 0 or int_val > max_val:
                return False, f"Value {value} exceeds {bit_width}-bit width (max: 0x{max_val:X})"

            return True, None
        except (ValueError, TypeError) as e:
            return False, f"Invalid value format: {value}"

    def _import_configuration(self):
        """Import configuration file with selections and values"""
        if not self.generator:
            self._show_status("⚠ Please load product data first", 'warning')
            return

        filename = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Import Configuration"
        )

        if not filename:
            return

        try:
            import csv

            # Read the import file
            imported_data = []
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                imported_data = list(reader)

            if not imported_data:
                self._show_status("⚠ Import file is empty", 'warning')
                return

            # Create a lookup dict - try index first, then fallback to field matching
            import_lookup = {}
            has_index = 'index' in imported_data[0]

            for row in imported_data:
                if has_index and row.get('index'):
                    # Use index-based matching (fastest and most reliable)
                    try:
                        idx = int(row['index'])
                        import_lookup[idx] = {
                            'selected': row.get('selected', '').lower() in ['true', '1', 'yes'],
                            'value': row.get('value', '0x0')
                        }
                    except (ValueError, TypeError):
                        pass
                else:
                    # Fallback to field-based matching
                    key = f"{row.get('IP_Origin', '')}_{row.get('Instance', '')}_{row.get('ip_name', '')}"
                    import_lookup[key] = {
                        'selected': row.get('selected', '').lower() in ['true', '1', 'yes'],
                        'value': row.get('value', '0x0')
                    }

            # First pass: validate all values before applying
            validation_errors = []
            for idx, row in enumerate(self.current_data):
                imported = None

                # Try index-based lookup first
                if has_index and idx in import_lookup:
                    imported = import_lookup[idx]
                else:
                    # Try field-based lookup
                    key = f"{row.get('IP_Origin', '')}_{row.get('Instance', '')}_{row.get('ip_name', '')}"
                    imported = import_lookup.get(key)

                if imported:
                    # Validate the value
                    value = imported['value']
                    is_valid, error_msg = self._validate_fuse_value(
                        value,
                        row.get('FUSE_WIDTH'),
                        row.get('numbits')
                    )
                    if not is_valid:
                        validation_errors.append({
                            'index': idx,
                            'instance': row.get('Instance', 'Unknown'),
                            'value': value,
                            'width': row.get('FUSE_WIDTH') or row.get('numbits'),
                            'error': error_msg
                        })

            # If there are validation errors, show summary and cancel
            if validation_errors:
                self._show_validation_errors(validation_errors)
                self._show_status(f"✗ Import cancelled: {len(validation_errors)} validation error(s)", 'error')
                return

            # All validations passed, apply the changes
            matched_count = 0
            selected_count = 0

            for idx, row in enumerate(self.current_data):
                imported = None

                # Try index-based lookup first
                if has_index and idx in import_lookup:
                    imported = import_lookup[idx]
                else:
                    # Try field-based lookup
                    key = f"{row.get('IP_Origin', '')}_{row.get('Instance', '')}_{row.get('ip_name', '')}"
                    imported = import_lookup.get(key)

                if imported:
                    row['selected'] = imported['selected']
                    row['value'] = imported['value']
                    matched_count += 1
                    if imported['selected']:
                        selected_count += 1
                        # Keep set in sync
                        self.selected_fuse_ids.add(row.get('_fuse_id'))
                    else:
                        fuse_id = row.get('_fuse_id')
                        if fuse_id in self.selected_fuse_ids:
                            self.selected_fuse_ids.discard(fuse_id)
                else:
                    # Not in import file, clear selection
                    row['selected'] = False
                    fuse_id = row.get('_fuse_id')
                    if fuse_id in self.selected_fuse_ids:
                        self.selected_fuse_ids.discard(fuse_id)

            # Refresh display
            self._populate_tree()
            self._update_selection_label()

            match_method = "index-based" if has_index else "field-based"
            self._show_status(
                f"✓ Imported configuration ({match_method}): {matched_count} fuses matched, {selected_count} selected",
                'success'
            )

        except Exception as e:
            self._show_status(f"✗ Import failed: {str(e)}", 'error')

    def _show_validation_errors(self, errors):
        """Show validation errors in a dialog window"""
        error_window = tk.Toplevel(self.root)
        error_window.title("Import Validation Errors")
        error_window.geometry("700x400")
        error_window.transient(self.root)
        error_window.grab_set()

        # Header
        header_frame = tk.Frame(error_window, bg='#e74c3c', pady=10)
        header_frame.pack(fill=tk.X)

        tk.Label(
            header_frame,
            text=f"⚠ Import Validation Failed: {len(errors)} Error(s)",
            font=("Segoe UI", 12, "bold"),
            bg='#e74c3c',
            fg='white'
        ).pack()

        tk.Label(
            header_frame,
            text="The following fuses have invalid values that exceed their bit width:",
            font=("Segoe UI", 9),
            bg='#e74c3c',
            fg='white'
        ).pack()

        # Error list with scrollbar
        list_frame = tk.Frame(error_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        error_text = tk.Text(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 9),
            wrap=tk.WORD,
            bg='#fff3cd',
            relief=tk.FLAT
        )
        error_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=error_text.yview)

        # Show first 50 errors
        for i, err in enumerate(errors[:50], 1):
            error_text.insert(tk.END, f"{i}. ")
            error_text.insert(tk.END, f"Index {err['index']}: {err['instance']}\n", 'bold')
            error_text.insert(tk.END, f"   Value: {err['value']} | Width: {err['width']} bits\n")
            error_text.insert(tk.END, f"   Error: {err['error']}\n\n")

        if len(errors) > 50:
            error_text.insert(tk.END, f"\n... and {len(errors) - 50} more errors\n")

        error_text.tag_config('bold', font=("Consolas", 9, "bold"))
        error_text.config(state=tk.DISABLED)

        # Button
        tk.Button(
            error_window,
            text="Close",
            command=error_window.destroy,
            bg='#7f8c8d',
            fg='white',
            font=("Segoe UI", 9),
            padx=30,
            pady=5
        ).pack(pady=10)

    def _on_product_change(self):
        """Handle product selection change"""
        new_product = self.product_var.get()

        if messagebox.askyesno("Change Product", f"Load fuse data for {new_product}?"):
            self._load_product_data(new_product)

    def _on_close(self):
        """Handle window close"""
        if self.standalone:
            self.root.quit()
        else:
            self.root.destroy()

    def run(self):
        """Run the GUI (for standalone mode)"""
        if self.standalone:
            self.root.mainloop()


class FuseGenerationWindow:
    """
    Window for configuring individual fuse values with spreadsheet-like interface.

    Workflow:
    1. User selects socket checkboxes (sockets, socket0, socket1)
    2. User selects IP checkboxes (computes, compute0, compute1, ios, io0, io1, etc.)
    3. Click "Generate List" - creates all socket+IP+fuse combinations
    4. Table shows explicit rows for each combination with value assignment
    5. Generate file creates properly formatted .fuse sections

    Example: If user selects socket0, socket1 and compute0, compute1 with 1 fuse:
    - Row 1: socket0 | compute0 | fuse_instance | value
    - Row 2: socket0 | compute1 | fuse_instance | value
    - Row 3: socket1 | compute0 | fuse_instance | value
    - Row 4: socket1 | compute1 | fuse_instance | value
    """

    def __init__(self, parent, generator: FuseFileGenerator, selected_fuses: List[Dict], product: str):
        """
        Initialize fuse generation configuration window.

        Args:
            parent: Parent window (Tkinter widget)
            generator: FuseFileGenerator instance for backend operations
            selected_fuses: List of fuse dictionaries selected by user
            product: Product name (GNR, CWF, or DMR) determines available IPs
        """
        self.window = tk.Toplevel(parent)
        self.generator = generator
        self.selected_fuses = selected_fuses
        self.product = product

        # Socket checkbox variables
        self.socket_vars = {
            'sockets': tk.BooleanVar(value=True),  # Default: plural
            'socket0': tk.BooleanVar(value=False),
            'socket1': tk.BooleanVar(value=False)
        }

        # IP checkbox variables - populated based on product
        self.ip_vars: Dict[str, tk.BooleanVar] = {}

        # Generated combinations: List of (socket, ip, fuse_dict, value_var)
        self.generated_combinations: List[tuple] = []

        self._setup_window()
        self._create_widgets()

    def _setup_window(self):
        """
        Configure main window properties.
        """
        self.window.title(f"Fuse Generation - {self.product}")
        self.window.geometry("1600x900")

        # Allow fuse table row to expand (now row 6 instead of row 4)
        self.window.rowconfigure(6, weight=1)
        self.window.columnconfigure(0, weight=1)

    def _create_widgets(self):
        """
        Create all UI widgets for the fuse generation window.

        Layout structure (new checkbox-based approach):
        Row 0: Header with product name and fuse count
        Row 1: Socket checkboxes (sockets/socket0/socket1)
        Row 2: IP checkboxes (product-specific: computes, compute0-2, ios, io0-1, etc.)
        Row 3: Generate List button (creates combinations)
        Row 4: Quick apply toolbar for batch value assignment
        Row 5: Main fuse table with columns: Socket, IP Instance, Fuse Instance, Fuse Width, Description, Value
        Row 6: Footer with Generate File and Cancel buttons
        """
        # Header
        header_frame = tk.Frame(self.window, bg=FuseFileUI.ENGINEERING_COLOR, pady=15)
        header_frame.grid(row=0, column=0, sticky="ew")

        tk.Label(
            header_frame,
            text=f"⚙ Fuse Value Assignment - {self.product}",
            font=("Segoe UI", 16, "bold"),
            bg=FuseFileUI.ENGINEERING_COLOR,
            fg='white'
        ).pack()

        tk.Label(
            header_frame,
            text=f"Select sockets and IPs, then generate combinations for {len(self.selected_fuses)} fuses",
            font=("Segoe UI", 10),
            bg=FuseFileUI.ENGINEERING_COLOR,
            fg='#ecf0f1'
        ).pack()

        # Status bar right below header
        self.status_bar = StatusBar(self.window, height=40)
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))

        # Step 1: Socket Selection (Checkboxes)
        socket_frame = tk.Frame(self.window, bg='#d5f4e6', padx=15, pady=10)
        socket_frame.grid(row=2, column=0, sticky="ew")

        tk.Label(
            socket_frame,
            text="Step 1: Select Sockets",
            font=("Segoe UI", 10, "bold"),
            bg='#d5f4e6',
            fg='#2c3e50'
        ).pack(side=tk.LEFT, padx=(0, 15))

        # Socket checkboxes
        for socket_key in ['sockets', 'socket0', 'socket1']:
            label = {
                'sockets': 'All Sockets (plural)',
                'socket0': 'Socket 0',
                'socket1': 'Socket 1'
            }[socket_key]

            tk.Checkbutton(
                socket_frame,
                text=label,
                variable=self.socket_vars[socket_key],
                bg='#d5f4e6',
                font=("Segoe UI", 9),
                selectcolor='white'
            ).pack(side=tk.LEFT, padx=10)

        # Step 2: IP Selection (Product-specific checkboxes)
        self._create_ip_checkboxes()

        # Step 3: Generate List Button
        generate_frame = tk.Frame(self.window, bg='#ecf0f1', pady=15)
        generate_frame.grid(row=4, column=0, sticky="ew")  # Changed from row 3 to row 4

        tk.Button(
            generate_frame,
            text="⚡ Generate Combination List",
            command=self._generate_combination_list,
            bg=FuseFileUI.ENGINEERING_COLOR,
            fg='white',
            font=("Segoe UI", 11, "bold"),
            padx=30,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack()

        # Step 4: Quick apply toolbar - Batch value assignment tools (after list is generated)
        toolbar_frame = tk.Frame(self.window, bg='#ecf0f1', padx=10, pady=10)
        toolbar_frame.grid(row=5, column=0, sticky="ew")  # Changed from row 4 to row 5

        tk.Label(
            toolbar_frame,
            text="Quick Apply:",
            font=("Segoe UI", 9, "bold"),
            bg='#ecf0f1'
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.quick_value_var = tk.StringVar(value='0x0')
        tk.Entry(
            toolbar_frame,
            textvariable=self.quick_value_var,
            font=("Consolas", 10),
            width=15
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            toolbar_frame,
            text="Apply to All",
            command=lambda: self._apply_to_all(),
            bg=FuseFileUI.ENGINEERING_COLOR,
            fg='white',
            font=("Segoe UI", 9, "bold"),
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            toolbar_frame,
            text="Apply to Selected Rows",
            command=lambda: self._apply_to_selected(),
            bg='#3498db',
            fg='white',
            font=("Segoe UI", 9, "bold"),
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            toolbar_frame,
            text="🗑 Remove Selected Rows",
            command=lambda: self._remove_selected_rows(),
            bg='#e74c3c',
            fg='white',
            font=("Segoe UI", 9, "bold"),
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        # Step 5: Combination table - Shows all socket×IP×fuse combinations
        # This table displays generated combinations with editable values
        table_container = tk.Frame(self.window, bg='white')
        table_container.grid(row=6, column=0, sticky="nsew", padx=10, pady=10)  # Changed from row 5 to row 6
        table_container.rowconfigure(0, weight=1)
        table_container.columnconfigure(0, weight=1)

        # Create treeview with scrollbars for large datasets
        tree_scroll_y = tk.Scrollbar(table_container)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        tree_scroll_x = tk.Scrollbar(table_container, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # New table columns for combination-based approach:
        # - Socket: Target socket (sockets, socket0, socket1)
        # - IP Instance: Target IP instance (compute0, computes, io1, etc.)
        # - IP Name: IP type from CSV (compute, io, cbb, imh, etc.)
        # - Fuse Instance: Fuse instance name
        # - Fuse Width: Bit width of the fuse
        # - Description: Human-readable description
        # - Value: Assigned hex value (editable via double-click)
        self.fuse_tree = ttk.Treeview(
            table_container,
            columns=('Socket', 'IP Instance', 'IP Name', 'Fuse Instance', 'Fuse Width', 'Description', 'Value'),
            show='headings',
            selectmode='extended',
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )
        self.fuse_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tree_scroll_y.config(command=self.fuse_tree.yview)
        tree_scroll_x.config(command=self.fuse_tree.xview)

        # Configure column headers and widths
        self.fuse_tree.heading('Socket', text='Socket')
        self.fuse_tree.heading('IP Instance', text='IP Instance')
        self.fuse_tree.heading('IP Name', text='IP Name')
        self.fuse_tree.heading('Fuse Instance', text='Fuse Instance')
        self.fuse_tree.heading('Fuse Width', text='Fuse Width')
        self.fuse_tree.heading('Description', text='Description')
        self.fuse_tree.heading('Value', text='Assigned Value')

        self.fuse_tree.column('Socket', width=100, minwidth=80)
        self.fuse_tree.column('IP Instance', width=120, minwidth=100)
        self.fuse_tree.column('IP Name', width=100, minwidth=80)
        self.fuse_tree.column('Fuse Instance', width=250, minwidth=150)
        self.fuse_tree.column('Fuse Width', width=100, minwidth=80)
        self.fuse_tree.column('Description', width=350, minwidth=200)
        self.fuse_tree.column('Value', width=120, minwidth=100)

        # Apply Excel-like styling
        style = ttk.Style()
        style.configure("Treeview",
                       background="white",
                       foreground="black",
                       rowheight=25,
                       fieldbackground="white")
        style.configure("Treeview.Heading",
                       background="#e8e8e8",
                       foreground="#2c3e50",
                       relief="raised",
                       font=("Segoe UI", 9, "bold"))

        # Bind double-click on Value column for inline editing (Excel-style)
        self.fuse_tree.bind('<Double-Button-1>', self._on_double_click)

        # Variable to track inline editing
        self.edit_entry = None

        # Step 6: Footer with action buttons
        footer_frame = tk.Frame(self.window, bg='#ecf0f1', pady=15)
        footer_frame.grid(row=7, column=0, sticky="ew")  # Changed from row 6 to row 7

        tk.Button(
            footer_frame,
            text="✓ Generate Fuse File",
            command=self._generate_fuse_file,
            bg='#27ae60',
            fg='white',
            font=("Segoe UI", 10, "bold"),
            padx=30,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=20)

        tk.Button(
            footer_frame,
            text="Cancel",
            command=self.window.destroy,
            bg='#95a5a6',
            fg='white',
            font=("Segoe UI", 10),
            padx=30,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=20)

    def _create_ip_checkboxes(self):
        """
        Create IP selection checkboxes based on product type.

        For GNR/CWF:
        - Computes: computes (plural), compute0, compute1, compute2
        - IOs: ios (plural), io0, io1

        For DMR:
        - CBBs: cbbs (plural), cbb0, cbb1, cbb2, cbb3
        - IMHs: imhs (plural), imh0, imh1
        """
        ip_frame = tk.Frame(self.window, bg='#fff3cd', padx=15, pady=10)
        ip_frame.grid(row=3, column=0, sticky="ew")  # Changed from row 2 to row 3

        tk.Label(
            ip_frame,
            text="Step 2: Select IP Instances",
            font=("Segoe UI", 10, "bold"),
            bg='#fff3cd',
            fg='#2c3e50'
        ).pack(side=tk.LEFT, padx=(0, 15))

        # Product-specific IP options
        if self.product in ['GNR', 'CWF']:
            # Computes section - all in one row
            computes_frame = tk.LabelFrame(
                ip_frame,
                text="Computes",
                bg='#fff3cd',
                font=("Segoe UI", 9, "bold"),
                fg='#2c3e50'
            )
            computes_frame.pack(side=tk.LEFT, padx=10)

            for ip_key in ['computes', 'compute0', 'compute1', 'compute2']:
                self.ip_vars[ip_key] = tk.BooleanVar(value=False)
                label = 'All Computes' if ip_key == 'computes' else ip_key.title()
                tk.Checkbutton(
                    computes_frame,
                    text=label,
                    variable=self.ip_vars[ip_key],
                    bg='#fff3cd',
                    font=("Segoe UI", 9),
                    selectcolor='white'
                ).pack(side=tk.LEFT, padx=5, pady=2)

            # IOs section - all in one row
            ios_frame = tk.LabelFrame(
                ip_frame,
                text="IOs",
                bg='#fff3cd',
                font=("Segoe UI", 9, "bold"),
                fg='#2c3e50'
            )
            ios_frame.pack(side=tk.LEFT, padx=10)

            for ip_key in ['ios', 'io0', 'io1']:
                self.ip_vars[ip_key] = tk.BooleanVar(value=False)
                label = 'All IOs' if ip_key == 'ios' else ip_key.upper()
                tk.Checkbutton(
                    ios_frame,
                    text=label,
                    variable=self.ip_vars[ip_key],
                    bg='#fff3cd',
                    font=("Segoe UI", 9),
                    selectcolor='white'
                ).pack(side=tk.LEFT, padx=5, pady=2)

        elif self.product == 'DMR':
            # CBBs section - all in one row
            cbbs_frame = tk.LabelFrame(
                ip_frame,
                text="CBBs",
                bg='#fff3cd',
                font=("Segoe UI", 9, "bold"),
                fg='#2c3e50'
            )
            cbbs_frame.pack(side=tk.LEFT, padx=10)

            for ip_key in ['cbbs', 'cbb0', 'cbb1', 'cbb2', 'cbb3']:
                self.ip_vars[ip_key] = tk.BooleanVar(value=False)
                label = 'All CBBs' if ip_key == 'cbbs' else ip_key.upper()
                tk.Checkbutton(
                    cbbs_frame,
                    text=label,
                    variable=self.ip_vars[ip_key],
                    bg='#fff3cd',
                    font=("Segoe UI", 9),
                    selectcolor='white'
                ).pack(side=tk.LEFT, padx=5, pady=2)

            # Computes section (for CBBSTOP fuses)
            computes_frame = tk.LabelFrame(
                ip_frame,
                text="Computes",
                bg='#fff3cd',
                font=("Segoe UI", 9, "bold"),
                fg='#2c3e50'
            )
            computes_frame.pack(side=tk.LEFT, padx=10)

            for ip_key in ['computes', 'compute0', 'compute1', 'compute2', 'compute3']:
                self.ip_vars[ip_key] = tk.BooleanVar(value=False)
                label = 'All Computes' if ip_key == 'computes' else ip_key.title()
                tk.Checkbutton(
                    computes_frame,
                    text=label,
                    variable=self.ip_vars[ip_key],
                    bg='#fff3cd',
                    font=("Segoe UI", 9),
                    selectcolor='white'
                ).pack(side=tk.LEFT, padx=5, pady=2)

            # IMHs section - all in one row
            imhs_frame = tk.LabelFrame(
                ip_frame,
                text="IMHs",
                bg='#fff3cd',
                font=("Segoe UI", 9, "bold"),
                fg='#2c3e50'
            )
            imhs_frame.pack(side=tk.LEFT, padx=10)

            for ip_key in ['imhs', 'imh0', 'imh1']:
                self.ip_vars[ip_key] = tk.BooleanVar(value=False)
                label = 'All IMHs' if ip_key == 'imhs' else ip_key.upper()
                tk.Checkbutton(
                    imhs_frame,
                    text=label,
                    variable=self.ip_vars[ip_key],
                    bg='#fff3cd',
                    font=("Segoe UI", 9),
                    selectcolor='white'
                ).pack(side=tk.LEFT, padx=5, pady=2)

    def _generate_combination_list(self):
        """
        Generate all socket × IP × fuse combinations based on selected checkboxes.

        This creates the cartesian product of:
        - Selected sockets (sockets, socket0, socket1)
        - Selected IP instances (compute0, computes, io1, etc.)
        - All selected fuses

        Each combination becomes a row in the table with:
        (socket, ip_instance, fuse_dict, value_var)

        Example:
        - Sockets checked: socket0, socket1
        - IPs checked: compute0, compute1
        - Fuses: 2 selected
        - Result: 2 × 2 × 2 = 8 rows in table
        """
        # Collect selected sockets
        selected_sockets = [
            socket_key for socket_key, var in self.socket_vars.items()
            if var.get()
        ]

        # Collect selected IPs
        selected_ips = [
            ip_key for ip_key, var in self.ip_vars.items()
            if var.get()
        ]

        # Validation
        if not selected_sockets:
            self.status_bar.show("⚠ Please select at least one socket (sockets, socket0, or socket1)", 'warning')
            return

        if not selected_ips:
            self.status_bar.show("⚠ Please select at least one IP instance", 'warning')
            return

        # Clear existing combinations
        self.generated_combinations.clear()
        for item in self.fuse_tree.get_children():
            self.fuse_tree.delete(item)

        # Generate cartesian product based on product type
        # DMR: Special handling for CBBSTOP (needs cbb × compute)
        # GNR/CWF: Standard socket × IP × fuse

        if self.product == 'DMR':
            # Separate CBB, Compute, and IMH instances
            selected_cbbs = [ip for ip in selected_ips if ip.startswith('cbb')]
            selected_computes = [ip for ip in selected_ips if ip.startswith('compute')]
            selected_imhs = [ip for ip in selected_ips if ip.startswith('imh')]

            for socket in selected_sockets:
                for fuse in self.selected_fuses:
                    fuse_ip_origin = fuse.get('IP_Origin', '').lower()

                    if fuse_ip_origin == 'cbbsbase':
                        # CBBSBASE: Only needs CBB instances (socket + cbb)
                        for cbb in selected_cbbs:
                            # Use value from fuse data or default to 0x0
                            default_value = fuse.get('value', '0x0')
                            value_var = tk.StringVar(value=default_value)
                            # Store (socket, cbb, None, fuse, value_var) where None = no compute needed
                            self.generated_combinations.append(
                                (socket, cbb, None, fuse, value_var)
                            )

                    elif fuse_ip_origin == 'cbbstop':
                        # CBBSTOP: Needs CBB × Compute instances (socket + cbb + compute)
                        for cbb in selected_cbbs:
                            for compute in selected_computes:
                                # Use value from fuse data or default to 0x0
                                default_value = fuse.get('value', '0x0')
                                value_var = tk.StringVar(value=default_value)
                                # Store (socket, cbb, compute, fuse, value_var)
                                self.generated_combinations.append(
                                    (socket, cbb, compute, fuse, value_var)
                                )

                    elif fuse_ip_origin == 'imhs':
                        # IMHS: Only needs IMH instances (socket + imh)
                        for imh in selected_imhs:
                            # Use value from fuse data or default to 0x0
                            default_value = fuse.get('value', '0x0')
                            value_var = tk.StringVar(value=default_value)
                            self.generated_combinations.append(
                                (socket, imh, None, fuse, value_var)
                            )
        else:
            # GNR/CWF: Standard handling
            for socket in selected_sockets:
                for ip_instance in selected_ips:
                    for fuse in self.selected_fuses:
                        # Get the IP origin of the fuse (COMPUTE, IO, etc.)
                        fuse_ip_origin = fuse.get('IP_Origin', '').lower()

                        # Extract the base IP type from ip_instance
                        # Handle plural forms: computes → compute, ios → io
                        if ip_instance.endswith('s') and not ip_instance[-2].isdigit():
                            ip_base = ip_instance.rstrip('s')
                        else:
                            import re
                            ip_base = re.sub(r'\d+$', '', ip_instance)

                        # Match fuse origin with IP base
                        if fuse_ip_origin != ip_base:
                            continue

                        # Create StringVar for this specific combination's value
                        # Use value from fuse data or default to 0x0
                        default_value = fuse.get('value', '0x0')
                        value_var = tk.StringVar(value=default_value)

                        # Store combination tuple: (socket, ip_instance, None, fuse_dict, value_var)
                        # None = no secondary instance (GNR/CWF don't need it)
                        self.generated_combinations.append(
                            (socket, ip_instance, None, fuse, value_var)
                        )

        # Now populate the tree view with all combinations
        for combo in self.generated_combinations:
            socket, ip1, ip2, fuse, value_var = combo

            # Build display string for IP column
            if ip2:  # DMR CBBSTOP: has both cbb and compute
                ip_display = f"{ip1}+{ip2}"
            else:  # Single IP instance
                ip_display = ip1

            # Get ip_name from fuse CSV data (e.g., 'bgr_c01_fuse2rb', 'ioss_fuse_pkg', etc.)
            ip_name = fuse.get('ip_name', '').lower()  # Get from original fuse file, convert to lowercase

            # Insert into table
            self.fuse_tree.insert(
                '',
                'end',
                values=(
                    socket,
                    ip_display,
                    ip_name,
                    fuse['Instance'],
                    fuse['FUSE_WIDTH'],
                    fuse.get('description', ''),
                    value_var.get()
                ),
                tags=('odd',) if len(self.fuse_tree.get_children()) % 2 == 1 else ('even',)
            )

        # Apply alternating row colors for Excel-like appearance
        self.fuse_tree.tag_configure('odd', background='#ffffff')
        self.fuse_tree.tag_configure('even', background='#f7f7f7')

        # Show success message
        total_combinations = len(self.generated_combinations)
        ip_summary = f"{len(selected_sockets)} sockets × {len(selected_ips)} IPs × {len(self.selected_fuses)} fuses = {total_combinations} combinations"
        self.status_bar.show(f"✓ Generated {total_combinations} combinations | {ip_summary}", 'success')

    def _on_double_click(self, event):
        """
        Handle double-click events for inline editing (Excel-style).

        Column #7 (Value): Creates inline entry widget for editing

        Args:
            event: Tkinter event object containing click coordinates
        """
        # Identify clicked item and column
        item = self.fuse_tree.identify('item', event.x, event.y)
        column = self.fuse_tree.identify('column', event.x, event.y)

        if not item or column != '#7':  # Only edit Value column (#7)
            return

        # Get the row index in generated_combinations
        item_index = self.fuse_tree.index(item)

        if item_index >= len(self.generated_combinations):
            return

        _, _, _, _, value_var = self.generated_combinations[item_index]
        current_value = value_var.get()

        # Get the bounding box of the cell
        bbox = self.fuse_tree.bbox(item, column)
        if not bbox:
            return

        # Destroy any existing edit entry
        if self.edit_entry:
            self.edit_entry.destroy()

        # Create an entry widget positioned over the cell
        x, y, width, height = bbox
        self.edit_entry = tk.Entry(self.fuse_tree, font=("Consolas", 10))
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self.edit_entry.insert(0, current_value)
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.focus_set()

        # Store the item and index for saving
        self.edit_entry.item_id = item
        self.edit_entry.item_index = item_index

        # Bind events
        self.edit_entry.bind('<Return>', self._save_inline_edit)
        self.edit_entry.bind('<Escape>', lambda e: self._cancel_inline_edit())
        self.edit_entry.bind('<FocusOut>', self._save_inline_edit)

    def _save_inline_edit(self, event=None):
        """Save the inline edit to the tree and data"""
        if not self.edit_entry:
            return

        new_value = self.edit_entry.get().strip()
        item_id = self.edit_entry.item_id
        item_index = self.edit_entry.item_index

        # Get fuse details for validation
        _, _, _, fuse, value_var = self.generated_combinations[item_index]
        fuse_width = fuse.get('FUSE_WIDTH')
        numbits = fuse.get('numbits')

        # Convert to int if they are strings
        if fuse_width:
            try:
                fuse_width = int(fuse_width)
            except (ValueError, TypeError):
                fuse_width = None
        if numbits:
            try:
                numbits = int(numbits)
            except (ValueError, TypeError):
                numbits = None

        # Validate value with bit width check
        if validate_fuse_value(new_value, fuse_width, numbits):
            # Update the StringVar in the combination tuple
            value_var.set(new_value)

            # Update tree display
            current_values = list(self.fuse_tree.item(item_id, 'values'))
            current_values[6] = new_value  # Value is column #7 (index 6)
            self.fuse_tree.item(item_id, values=current_values)
        else:
            # Provide specific error message
            bit_width = fuse_width or numbits
            if bit_width:
                try:
                    max_val = (2 ** int(bit_width)) - 1
                    self.status_bar.show(
                        f"⚠ '{new_value}' exceeds fuse width ({bit_width} bits, max: 0x{max_val:X})",
                        'warning'
                    )
                except:
                    self.status_bar.show(f"⚠ '{new_value}' is not valid. Use hex (0xFF), decimal (255), or binary (0b11111111)", 'warning')
            else:
                self.status_bar.show(f"⚠ '{new_value}' is not valid. Use hex (0xFF), decimal (255), or binary (0b11111111)", 'warning')

        # Remove the entry widget
        self._cancel_inline_edit()

    def _cancel_inline_edit(self):
        """Cancel inline editing and remove entry widget"""
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None

    def _apply_to_all(self):
        """Apply quick value to all combinations in the table"""
        if not self.generated_combinations:
            self.status_bar.show("⚠ Please generate combinations first using the 'Generate Combination List' button", 'warning')
            return

        value = self.quick_value_var.get().strip()

        # Find the minimum bit width among all fuses (most restrictive)
        min_bit_width = None
        for _, _, _, fuse, _ in self.generated_combinations:
            fuse_width = fuse.get('FUSE_WIDTH')
            numbits = fuse.get('numbits')
            bit_width = fuse_width or numbits
            if bit_width:
                try:
                    bw = int(bit_width)
                    if min_bit_width is None or bw < min_bit_width:
                        min_bit_width = bw
                except:
                    pass

        # Validate with the most restrictive width
        if not validate_fuse_value(value, min_bit_width, min_bit_width):
            if min_bit_width:
                max_val = (2 ** min_bit_width) - 1
                self.status_bar.show(
                    f"⚠ '{value}' exceeds smallest fuse width ({min_bit_width} bits, max: 0x{max_val:X}). Use hex/decimal/binary format",
                    'warning'
                )
            else:
                self.status_bar.show(f"⚠ '{value}' is not valid. Use hex (0xFF), decimal (255), or binary (0b11111111)", 'warning')
            return

        # Update all combination value_vars
        for idx, (socket, ip1, ip2, fuse, value_var) in enumerate(self.generated_combinations):
            value_var.set(value)
            # Update tree display
            item_id = self.fuse_tree.get_children()[idx]
            current_values = list(self.fuse_tree.item(item_id, 'values'))
            current_values[6] = value  # Value is column #7 (index 6)
            self.fuse_tree.item(item_id, values=current_values)

        self.status_bar.show(f"✓ Value {value} applied to all {len(self.generated_combinations)} combinations", 'success')

    def _apply_to_selected(self):
        """Apply quick value to selected rows in tree"""
        selected_items = self.fuse_tree.selection()
        if not selected_items:
            self.status_bar.show("⚠ Please select rows in the table first", 'warning')
            return

        value = self.quick_value_var.get().strip()

        # Check if value is valid for all selected fuses
        invalid_fuses = []
        for item in selected_items:
            idx = self.fuse_tree.index(item)
            if idx < len(self.generated_combinations):
                _, _, _, fuse, _ = self.generated_combinations[idx]
                fuse_width = fuse.get('FUSE_WIDTH')
                numbits = fuse.get('numbits')
                # Convert to int
                if fuse_width:
                    try:
                        fuse_width = int(fuse_width)
                    except (ValueError, TypeError):
                        fuse_width = None
                if numbits:
                    try:
                        numbits = int(numbits)
                    except (ValueError, TypeError):
                        numbits = None
                if not validate_fuse_value(value, fuse_width, numbits):
                    fuse_name = fuse.get('Instance', 'Unknown')
                    bit_width = fuse_width or numbits
                    invalid_fuses.append(f"{fuse_name} ({bit_width} bits)")

        if invalid_fuses:
            fuse_list = ", ".join(invalid_fuses[:3]) + ("..." if len(invalid_fuses) > 3 else "")
            self.status_bar.show(
                f"⚠ '{value}' exceeds bit width for {len(invalid_fuses)} fuse(s): {fuse_list}",
                'warning'
            )
            return

        # Update selected combinations
        for item in selected_items:
            idx = self.fuse_tree.index(item)
            if idx < len(self.generated_combinations):
                _, _, _, _, value_var = self.generated_combinations[idx]
                value_var.set(value)
                # Update tree display
                current_values = list(self.fuse_tree.item(item, 'values'))
                current_values[6] = value  # Value is column #7 (index 6)
                self.fuse_tree.item(item, values=current_values)

        self.status_bar.show(f"✓ Value {value} applied to {len(selected_items)} selected combination(s)", 'success')

    def _remove_selected_rows(self):
        """Remove selected rows from the combination table"""
        selected_items = self.fuse_tree.selection()
        if not selected_items:
            self.status_bar.show("⚠ Please select rows in the table to remove", 'warning')
            return

        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Removal",
            f"Remove {len(selected_items)} selected row(s) from the list?\n\nThis cannot be undone."
        )

        if not result:
            return

        # Get indices of selected items (in reverse order to avoid index shifting)
        indices_to_remove = []
        for item in selected_items:
            idx = self.fuse_tree.index(item)
            indices_to_remove.append(idx)

        # Sort in reverse order to remove from back to front
        indices_to_remove.sort(reverse=True)

        # Remove from generated_combinations list
        for idx in indices_to_remove:
            if idx < len(self.generated_combinations):
                del self.generated_combinations[idx]

        # Clear and rebuild the tree
        for item in self.fuse_tree.get_children():
            self.fuse_tree.delete(item)

        # Repopulate tree with remaining combinations
        for idx, (socket, ip1, ip2, fuse, value_var) in enumerate(self.generated_combinations):
            # Build display string for IP column
            if ip2:  # DMR CBBSTOP: has both cbb and compute
                ip_display = f"{ip1}+{ip2}"
            else:  # Single IP instance
                ip_display = ip1

            ip_name = fuse.get('ip_name', '').lower()
            self.fuse_tree.insert(
                '',
                'end',
                values=(
                    socket,
                    ip_display,
                    ip_name,
                    fuse['Instance'],
                    fuse['FUSE_WIDTH'],
                    fuse.get('description', ''),
                    value_var.get()
                ),
                tags=('odd',) if idx % 2 == 1 else ('even',)
            )

        # Apply alternating row colors
        self.fuse_tree.tag_configure('odd', background='#ffffff')
        self.fuse_tree.tag_configure('even', background='#f7f7f7')

        messagebox.showinfo("Removed", f"Removed {len(indices_to_remove)} row(s). Remaining: {len(self.generated_combinations)}")

    def _generate_fuse_file(self):
        """
        Generate the final .fuse file with proper section headers from combinations.

        New process (checkbox-based):
        1. Iterates through all generated combinations (socket, ip, fuse, value)
        2. Builds section header: sv.{socket}.{ip}.fuses
        3. Groups fuses by section header
        4. Writes .fuse file with all sections and assignments

        Example output sections:
        - [sv.sockets.compute0.fuses]
        - [sv.socket0.io1.fuses]
        - [sv.socket1.computes.fuses]
        """
        # Validate we have combinations
        if not self.generated_combinations:
            self.status_bar.show(
                "⚠ Please generate combinations first using the 'Generate Combination List' button",
                'warning'
            )
            return

        # Ask for output location
        filename = filedialog.asksaveasfilename(
            defaultextension=".fuse",
            filetypes=[("Fuse files", "*.fuse"), ("All files", "*.*")],
            title="Save Fuse Configuration"
        )

        if not filename:
            return

        try:
            # Build section-based fuse map
            # Format: {section_header: {fuse_instance: value}}
            # Example: {'sv.sockets.compute0.fuses': {'register_name': '0x1'}}
            section_fuse_map = {}

            for socket, ip1, ip2, fuse, value_var in self.generated_combinations:
                # Get fuse details
                fuse_instance = fuse.get('Instance', 'unknown').lower()  # Lowercase instance
                ip_name = fuse.get('ip_name', '').lower()  # Get ip_name from original fuse file, lowercase
                value = value_var.get()
                fuse_width = fuse.get('FUSE_WIDTH')
                numbits = fuse.get('numbits')
                # Convert to int
                if fuse_width:
                    try:
                        fuse_width = int(fuse_width)
                    except (ValueError, TypeError):
                        fuse_width = None
                if numbits:
                    try:
                        numbits = int(numbits)
                    except (ValueError, TypeError):
                        numbits = None

                # Validate value
                if not validate_fuse_value(value, fuse_width, numbits):
                    bit_width = fuse_width or numbits
                    self.status_bar.show(
                        f"⚠ Fuse '{fuse_instance}' has invalid value '{value}' (width: {bit_width} bits). Using 0x0",
                        'warning'
                    )
                    value = '0x0'

                # Get IP origin to determine section header structure
                fuse_ip_origin = fuse.get('IP_Origin', '').lower()

                # Build section header based on product and IP origin
                if self.product == 'DMR':
                    # DMR has special structure
                    if fuse_ip_origin == 'cbbsbase':
                        # CBBSBASE: sv.socket{socket}.cbb{cbb}.base.fuses
                        if ip1 == 'cbbs':
                            section_header = f"sv.{socket}.cbbs.base.fuses"
                        else:
                            # Extract cbb number from ip1 (e.g., 'cbb0' -> '0')
                            cbb_num = ip1.replace('cbb', '')
                            section_header = f"sv.{socket}.cbb{cbb_num}.base.fuses"
                    elif fuse_ip_origin == 'cbbstop':
                        # CBBSTOP: sv.socket{socket}.cbb{cbb}.compute{compute}.fuses
                        # ip1 = cbb instance, ip2 = compute instance
                        if ip1 == 'cbbs':
                            # All CBBs selected
                            if ip2 == 'computes':
                                section_header = f"sv.{socket}.cbbs.computes.fuses"
                            else:
                                compute_num = ip2.replace('compute', '')
                                section_header = f"sv.{socket}.cbbs.compute{compute_num}.fuses"
                        else:
                            # Specific CBB
                            cbb_num = ip1.replace('cbb', '')
                            if ip2 == 'computes':
                                section_header = f"sv.{socket}.cbb{cbb_num}.computes.fuses"
                            else:
                                compute_num = ip2.replace('compute', '')
                                section_header = f"sv.{socket}.cbb{cbb_num}.compute{compute_num}.fuses"
                    elif fuse_ip_origin == 'imhs':
                        # IMHS: sv.socket{socket}.imh{imh}.fuses
                        if ip1 == 'imhs':
                            section_header = f"sv.{socket}.imhs.fuses"
                        else:
                            imh_num = ip1.replace('imh', '')
                            section_header = f"sv.{socket}.imh{imh_num}.fuses"
                    else:
                        # Fallback
                        section_header = f"sv.{socket}.{ip1}.fuses"
                else:
                    # GNR/CWF: Standard structure
                    section_header = f"sv.{socket}.{ip1}.fuses"

                # Build full fuse name: ip_name.instance (both lowercase) or just instance if ip_name is blank
                if ip_name:
                    full_fuse_name = f"{ip_name}.{fuse_instance}"
                else:
                    full_fuse_name = fuse_instance

                # Group fuses by section header
                if section_header not in section_fuse_map:
                    section_fuse_map[section_header] = {}

                section_fuse_map[section_header][full_fuse_name] = value

            # Write .fuse file manually with proper formatting
            with open(filename, 'w', encoding='utf-8') as f:
                # Write header comments
                f.write(f"# Fuse configuration file for {self.product}\n")
                f.write(f"# Generated by PPV Engineering Tools - Fuse File Generator\n")
                f.write(f"# Total combinations: {len(self.generated_combinations)}\n")
                f.write(f"# Unique fuses: {len(self.selected_fuses)}\n")
                f.write(f"#\n")
                f.write(f"# This file is compatible with fusefilegen.py\n\n")

                # Write each section
                for section_header in sorted(section_fuse_map.keys()):
                    f.write(f"[{section_header}]\n")

                    # Write fuse assignments for this section
                    for fuse_name, value in sorted(section_fuse_map[section_header].items()):
                        f.write(f"{fuse_name} = {value}\n")

                    f.write("\n")  # Blank line between sections

            messagebox.showinfo(
                "Success",
                f"Fuse configuration file generated successfully!\n\n"
                f"File: {filename}\n"
                f"Total combinations: {len(self.generated_combinations)}\n"
                f"Sections created: {len(section_fuse_map)}"
            )
            self.window.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Error generating fuse file:\n{e}")


class SelectionViewerWindow:
    """Dedicated window for viewing and managing fuse selections"""

    def __init__(self, parent, main_ui: FuseFileUI):
        """
        Initialize selection viewer window.

        Args:
            parent: Parent window
            main_ui: Reference to main FuseFileUI instance
        """
        self.window = tk.Toplevel(parent)
        self.main_ui = main_ui

        self._setup_window()
        self._create_widgets()
        self._refresh_display()

    def _setup_window(self):
        """Configure window"""
        self.window.title("Selection Viewer & Manager")
        self.window.geometry("1100x700")

        self.window.rowconfigure(1, weight=1)
        self.window.columnconfigure(0, weight=1)

    def _create_widgets(self):
        """Create all widgets"""
        # Header
        header_frame = tk.Frame(self.window, bg='#3498db', height=12)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)

        # Main container
        main_container = tk.Frame(self.window)
        main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        main_container.rowconfigure(1, weight=1)
        main_container.columnconfigure(0, weight=1)

        # Info frame
        info_frame = tk.LabelFrame(
            main_container,
            text="Selection Information",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=10
        )
        info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.info_label = tk.Label(
            info_frame,
            text="",
            font=("Segoe UI", 9),
            justify=tk.LEFT
        )
        self.info_label.pack(anchor="w")

        # Selection table
        table_frame = tk.LabelFrame(
            main_container,
            text="Selected Fuses",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        table_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Scrollbars for selection tree
        tree_scroll_y = tk.Scrollbar(table_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        tree_scroll_x = tk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Selection treeview
        self.selection_tree = ttk.Treeview(
            table_frame,
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            selectmode='extended',
            show='headings'
        )
        self.selection_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tree_scroll_y.config(command=self.selection_tree.yview)
        tree_scroll_x.config(command=self.selection_tree.xview)

        # Action buttons
        button_frame = tk.Frame(main_container, bg='#ecf0f1', pady=10, padx=10)
        button_frame.grid(row=2, column=0, sticky="ew")

        btn_config = {
            'font': ("Segoe UI", 9, "bold"),
            'padx': 20,
            'pady': 8,
            'relief': tk.FLAT,
            'cursor': "hand2"
        }

        # Left side buttons
        left_buttons = tk.Frame(button_frame, bg='#ecf0f1')
        left_buttons.pack(side=tk.LEFT)

        tk.Button(
            left_buttons,
            text="✓ Select All",
            command=self._select_all,
            bg='#27ae60',
            fg='white',
            **btn_config
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            left_buttons,
            text="✗ Clear All",
            command=self._clear_all,
            bg='#e74c3c',
            fg='white',
            **btn_config
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            left_buttons,
            text="☑ Select Filtered",
            command=self._select_filtered,
            bg='#3498db',
            fg='white',
            **btn_config
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            left_buttons,
            text="☐ Clear Filtered",
            command=self._clear_filtered,
            bg='#95a5a6',
            fg='white',
            **btn_config
        ).pack(side=tk.LEFT, padx=2)

        # Right side buttons
        right_buttons = tk.Frame(button_frame, bg='#ecf0f1')
        right_buttons.pack(side=tk.RIGHT)

        tk.Button(
            right_buttons,
            text="Remove Selected from View",
            command=self._remove_from_selection,
            bg='#e67e22',
            fg='white',
            **btn_config
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            right_buttons,
            text="Close",
            command=self.window.destroy,
            bg='#7f8c8d',
            fg='white',
            **btn_config
        ).pack(side=tk.LEFT, padx=5)

    def _refresh_display(self):
        """Refresh the display with current selection"""
        # Update info
        total_filtered = len(self.main_ui.filtered_data)
        selected_count = sum(1 for row in self.main_ui.current_data if row.get('selected', False))

        info_text = f"Total Fuses in Current View: {total_filtered}\n"
        info_text += f"Selected Fuses: {selected_count}"
        if total_filtered > 0:
            percentage = (selected_count / total_filtered) * 100
            info_text += f" ({percentage:.1f}%)"

        self.info_label.config(text=info_text)

        # Setup columns
        if self.main_ui.display_columns:
            self.selection_tree['columns'] = self.main_ui.display_columns

            for col in self.main_ui.display_columns:
                self.selection_tree.heading(col, text=col)
                self.selection_tree.column(col, width=120, minwidth=80)

        # Clear and repopulate
        self.selection_tree.delete(*self.selection_tree.get_children())

        # Show only selected fuses
        for row in self.main_ui.current_data:
            if row.get('selected', False):
                fuse_id = row.get('_fuse_id')
                values = [row.get(col, '') for col in self.main_ui.display_columns]
                self.selection_tree.insert('', tk.END, values=values, tags=(fuse_id,))

    def _select_all(self):
        """Select all fuses in current_data"""
        for row in self.main_ui.current_data:
            row['selected'] = True
            fuse_id = row.get('_fuse_id')
            if fuse_id:
                self.main_ui.selected_fuse_ids.add(fuse_id)
        self.main_ui._populate_tree()
        self.main_ui._update_selection_label()
        self._refresh_display()

    def _clear_all(self):
        """Clear all selections"""
        for row in self.main_ui.current_data:
            row['selected'] = False
        self.main_ui.selected_fuse_ids.clear()
        self.main_ui._populate_tree()
        self.main_ui._update_selection_label()
        self._refresh_display()

    def _select_filtered(self):
        """Select all currently filtered fuses"""
        for row in self.main_ui.filtered_data:
            row['selected'] = True
            fuse_id = row.get('_fuse_id')
            if fuse_id:
                self.main_ui.selected_fuse_ids.add(fuse_id)
        self.main_ui._populate_tree()
        self.main_ui._update_selection_label()
        self._refresh_display()

    def _clear_filtered(self):
        """Clear selection for filtered fuses"""
        for row in self.main_ui.filtered_data:
            row['selected'] = False
            fuse_id = row.get('_fuse_id')
            if fuse_id:
                self.main_ui.selected_fuse_ids.discard(fuse_id)
        self.main_ui._populate_tree()
        self.main_ui._update_selection_label()
        self._refresh_display()

    def _remove_from_selection(self):
        """Remove selected items from selection"""
        # Get selected items in viewer
        selected_items = self.selection_tree.selection()
        if not selected_items:
            self.main_ui._show_status("⚠ Please select items to remove from selection", 'warning')
            return

        # Remove from main selection
        for item in selected_items:
            tags = self.selection_tree.item(item, 'tags')
            if tags:
                fuse_id = tags[0]
                # Find and unmark the row
                for row in self.main_ui.current_data:
                    if row.get('_fuse_id') == fuse_id:
                        row['selected'] = False
                        self.main_ui.selected_fuse_ids.discard(fuse_id)
                        break

        # Update displays
        self.main_ui._populate_tree()
        self.main_ui._update_selection_label()
        self._refresh_display()


class ColumnFilterDialog:
    """Dialog for filtering a specific column"""

    def __init__(self, parent, main_ui, column_name):
        self.main_ui = main_ui
        self.column_name = column_name

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Filter: {column_name}")
        self.dialog.geometry("450x250")
        self.dialog.configure(bg='white')
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Header
        header = tk.Frame(self.dialog, bg='#e67e22', height=12)
        header.pack(fill=tk.X)

        # Main content
        main_frame = tk.Frame(self.dialog, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        tk.Label(
            main_frame,
            text=f"Filter Column: {column_name}",
            font=("Segoe UI", 11, "bold"),
            bg='white',
            fg='#2c3e50'
        ).pack(pady=(0, 15))

        # Current filter info
        current_filter = main_ui.column_filters.get(column_name, '')
        if current_filter:
            info_frame = tk.Frame(main_frame, bg='#d4edda', relief=tk.RIDGE, bd=1)
            info_frame.pack(fill=tk.X, pady=(0, 10))
            tk.Label(
                info_frame,
                text=f"Current filter: '{current_filter}'",
                font=("Segoe UI", 9),
                bg='#d4edda',
                fg='#155724'
            ).pack(padx=10, pady=5)

        # Filter input
        tk.Label(
            main_frame,
            text="Enter filter value (case-insensitive, partial match):",
            font=("Segoe UI", 9),
            bg='white',
            anchor='w'
        ).pack(fill=tk.X, pady=(0, 5))

        self.filter_var = tk.StringVar(value=current_filter)
        filter_entry = tk.Entry(
            main_frame,
            textvariable=self.filter_var,
            font=("Segoe UI", 11),
            relief=tk.SOLID,
            bd=1
        )
        filter_entry.pack(fill=tk.X, pady=(0, 5))
        filter_entry.focus_set()
        filter_entry.bind('<Return>', lambda e: self._apply())

        # Hint
        tk.Label(
            main_frame,
            text="Example: Type 'compute' to show only rows containing 'compute' in this column",
            font=("Segoe UI", 8),
            bg='white',
            fg='#7f8c8d',
            anchor='w',
            wraplength=400,
            justify=tk.LEFT
        ).pack(fill=tk.X, pady=(0, 15))

        # Get unique values preview (for small datasets)
        if len(main_ui.current_data) <= 1000:
            unique_values = set(str(row.get(column_name, '')) for row in main_ui.current_data[:100])
            if unique_values and len(unique_values) <= 10:
                tk.Label(
                    main_frame,
                    text=f"Sample values: {', '.join(sorted(list(unique_values)[:5]))}...",
                    font=("Segoe UI", 8),
                    bg='white',
                    fg='#3498db',
                    anchor='w',
                    wraplength=400
                ).pack(fill=tk.X, pady=(0, 10))

        # Buttons
        button_frame = tk.Frame(main_frame, bg='white')
        button_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(
            button_frame,
            text="Apply Filter",
            command=self._apply,
            bg='#e67e22',
            fg='white',
            font=("Segoe UI", 9, "bold"),
            padx=15,
            pady=6,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            button_frame,
            text="Clear Filter",
            command=self._clear,
            bg='#95a5a6',
            fg='white',
            font=("Segoe UI", 9),
            padx=15,
            pady=6,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            button_frame,
            text="Sort A→Z",
            command=lambda: self._sort(False),
            bg='#3498db',
            fg='white',
            font=("Segoe UI", 9),
            padx=15,
            pady=6,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy,
            bg='#7f8c8d',
            fg='white',
            font=("Segoe UI", 9),
            padx=15,
            pady=6,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=2)

    def _apply(self):
        """Apply the filter"""
        filter_value = self.filter_var.get().strip()

        if filter_value:
            self.main_ui.column_filters[self.column_name] = filter_value
        elif self.column_name in self.main_ui.column_filters:
            del self.main_ui.column_filters[self.column_name]

        self.main_ui._apply_column_filters()
        self.main_ui._show_data()  # Refresh to update heading display
        self.dialog.destroy()

    def _clear(self):
        """Clear the filter for this column"""
        self.main_ui._clear_column_filter(self.column_name)
        self.dialog.destroy()

    def _sort(self, reverse):
        """Sort by this column"""
        self.main_ui._sort_column(self.column_name)
        self.dialog.destroy()


class FilterConfigWindow:
    """Window for configuring pre-filters (Instance, Description, IP)"""

    def __init__(self, parent, main_ui):
        self.main_ui = main_ui
        self.window = tk.Toplevel(parent)
        self.window.title("Configure Filters")
        self.window.geometry("600x400")
        self.window.configure(bg='white')
        self.window.transient(parent)
        self.window.grab_set()

        # Header
        header = tk.Frame(self.window, bg='#e67e22', height=12)
        header.pack(fill=tk.X)

        # Main content
        main_frame = tk.LabelFrame(
            self.window,
            text="Pre-Filters (Applied before displaying data)",
            font=("Segoe UI", 10, "bold"),
            bg='white',
            padx=20,
            pady=20
        )
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create filter inputs
        self.instance_var = tk.StringVar(value=main_ui.pre_filters['instance'])
        self.description_var = tk.StringVar(value=main_ui.pre_filters['description'])
        self.ip_var = tk.StringVar(value=main_ui.pre_filters['ip'])

        row = 0

        # Instance filter
        tk.Label(
            main_frame,
            text="Instance (contains):",
            font=("Segoe UI", 9, "bold"),
            bg='white'
        ).grid(row=row, column=0, sticky="w", pady=10)

        tk.Entry(
            main_frame,
            textvariable=self.instance_var,
            font=("Segoe UI", 10),
            width=40
        ).grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=10)

        tk.Label(
            main_frame,
            text="Example: core, cha, imc",
            font=("Segoe UI", 8),
            fg='#7f8c8d',
            bg='white'
        ).grid(row=row+1, column=1, sticky="w", padx=(10, 0))

        row += 2

        # Description filter
        tk.Label(
            main_frame,
            text="Description (contains):",
            font=("Segoe UI", 9, "bold"),
            bg='white'
        ).grid(row=row, column=0, sticky="w", pady=10)

        tk.Entry(
            main_frame,
            textvariable=self.description_var,
            font=("Segoe UI", 10),
            width=40
        ).grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=10)

        tk.Label(
            main_frame,
            text="Example: enable, disable, config",
            font=("Segoe UI", 8),
            fg='#7f8c8d',
            bg='white'
        ).grid(row=row+1, column=1, sticky="w", padx=(10, 0))

        row += 2

        # IP filter
        tk.Label(
            main_frame,
            text="IP Origin (contains):",
            font=("Segoe UI", 9, "bold"),
            bg='white'
        ).grid(row=row, column=0, sticky="w", pady=10)

        tk.Entry(
            main_frame,
            textvariable=self.ip_var,
            font=("Segoe UI", 10),
            width=40
        ).grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=10)

        tk.Label(
            main_frame,
            text="Example: computes, ios, cbbs",
            font=("Segoe UI", 8),
            fg='#7f8c8d',
            bg='white'
        ).grid(row=row+1, column=1, sticky="w", padx=(10, 0))

        main_frame.columnconfigure(1, weight=1)

        # Buttons
        button_frame = tk.Frame(self.window, bg='white', pady=10)
        button_frame.pack(fill=tk.X, padx=20)

        tk.Button(
            button_frame,
            text="Apply Filters",
            command=self._apply,
            bg='#e67e22',
            fg='white',
            font=("Segoe UI", 9, "bold"),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="Clear All",
            command=self._clear,
            bg='#95a5a6',
            fg='white',
            font=("Segoe UI", 9),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy,
            bg='#7f8c8d',
            fg='white',
            font=("Segoe UI", 9),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=5)

        # Info label
        info_frame = tk.Frame(self.window, bg='#ecf0f1', relief=tk.RIDGE, bd=1)
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Label(
            info_frame,
            text="💡 Filters use case-insensitive partial matching. All filters are combined with AND logic.",
            font=("Segoe UI", 8),
            bg='#ecf0f1',
            fg='#34495e',
            anchor='w',
            wraplength=550,
            justify=tk.LEFT
        ).pack(padx=10, pady=5)

    def _apply(self):
        """Apply the filters"""
        self.main_ui.pre_filters['instance'] = self.instance_var.get().strip()
        self.main_ui.pre_filters['description'] = self.description_var.get().strip()
        self.main_ui.pre_filters['ip'] = self.ip_var.get().strip()
        self.main_ui._update_filter_indicator()
        self.main_ui._show_status("✓ Filters configured. Click 'Apply & Show Data' to see results", 'info')
        self.window.destroy()

    def _clear(self):
        """Clear all filters"""
        self.instance_var.set('')
        self.description_var.set('')
        self.ip_var.set('')


class ColumnSelectorWindow:
    """Window for selecting columns to display"""

    def __init__(self, parent, main_ui):
        self.main_ui = main_ui
        self.window = tk.Toplevel(parent)
        self.window.title("Select Columns to Display")
        self.window.geometry("700x600")
        self.window.configure(bg='white')
        self.window.transient(parent)
        self.window.grab_set()

        # Header
        header = tk.Frame(self.window, bg='#e67e22', height=12)
        header.pack(fill=tk.X)

        # Main content
        main_frame = tk.LabelFrame(
            self.window,
            text="Available Columns",
            font=("Segoe UI", 10, "bold"),
            bg='white',
            padx=20,
            pady=20
        )
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Get available columns
        available_columns = self.main_ui.generator.get_available_columns()

        # Info label
        tk.Label(
            main_frame,
            text="Select columns to display in the data table (use Ctrl+Click for multiple selection):",
            font=("Segoe UI", 9),
            bg='white',
            anchor='w'
        ).pack(fill=tk.X, pady=(0, 10))

        # Column listbox with scrollbar
        list_frame = tk.Frame(main_frame, bg='white')
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.columns_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.MULTIPLE,
            font=("Consolas", 9),
            yscrollcommand=scrollbar.set,
            height=20
        )
        self.columns_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.columns_listbox.yview)

        # Populate listbox
        for col in available_columns:
            self.columns_listbox.insert(tk.END, col)
            # Select currently selected columns
            if col in main_ui.display_columns:
                idx = available_columns.index(col)
                self.columns_listbox.selection_set(idx)

        # Quick selection buttons
        quick_frame = tk.Frame(main_frame, bg='white')
        quick_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(
            quick_frame,
            text="Select Default",
            command=self._select_default,
            bg='#3498db',
            fg='white',
            font=("Segoe UI", 8),
            padx=10,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            quick_frame,
            text="Select All",
            command=lambda: self.columns_listbox.selection_set(0, tk.END),
            bg='#3498db',
            fg='white',
            font=("Segoe UI", 8),
            padx=10,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            quick_frame,
            text="Clear All",
            command=lambda: self.columns_listbox.selection_clear(0, tk.END),
            bg='#95a5a6',
            fg='white',
            font=("Segoe UI", 8),
            padx=10,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)

        # Buttons
        button_frame = tk.Frame(self.window, bg='white', pady=10)
        button_frame.pack(fill=tk.X, padx=20)

        tk.Button(
            button_frame,
            text="Apply Selection",
            command=self._apply,
            bg='#e67e22',
            fg='white',
            font=("Segoe UI", 9, "bold"),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy,
            bg='#7f8c8d',
            fg='white',
            font=("Segoe UI", 9),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=5)

        # Selection count label
        self.count_label = tk.Label(
            self.window,
            text=f"Selected: {len(main_ui.display_columns)} columns",
            font=("Segoe UI", 9, "bold"),
            bg='white',
            fg='#27ae60'
        )
        self.count_label.pack(pady=(0, 10))

        # Update count on selection change
        self.columns_listbox.bind('<<ListboxSelect>>', self._update_count)

    def _select_default(self):
        """Select default important columns"""
        default_cols = ['IP_Origin', 'Instance', 'description']
        self.columns_listbox.selection_clear(0, tk.END)

        for i in range(self.columns_listbox.size()):
            col = self.columns_listbox.get(i)
            if col in default_cols:
                self.columns_listbox.selection_set(i)

        self._update_count(None)

    def _update_count(self, event):
        """Update selection count label"""
        count = len(self.columns_listbox.curselection())
        self.count_label.config(text=f"Selected: {count} columns")

    def _apply(self):
        """Apply column selection"""
        selected_indices = self.columns_listbox.curselection()
        if not selected_indices:
            self.main_ui._show_status("⚠ Please select at least one column", 'warning')
            return

        self.main_ui.display_columns = [self.columns_listbox.get(i) for i in selected_indices]
        self.main_ui._update_column_indicator()
        self.main_ui._show_status(f"✓ {len(self.main_ui.display_columns)} columns selected", 'success')
        self.window.destroy()


def main():
    """Main entry point for standalone execution"""
    # Pass None as parent so FuseFileUI creates its own root window
    app = FuseFileUI(parent=None, default_product=None)
    # Schedule product data loading after window is shown
    app.root.after(100, lambda: app._load_product_data('GNR'))
    app.root.mainloop()


if __name__ == "__main__":
    main()
