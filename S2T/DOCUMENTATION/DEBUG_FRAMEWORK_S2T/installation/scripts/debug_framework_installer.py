"""
Debug Framework & S2T - GUI Installer (Standalone)
===================================================
Version: 1.7.1
Date: February 16, 2026
Author: Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)

This standalone installer configures a complete Debug Framework and S2T environment.
It replicates the 2-step process (TeratermEnv.ps1 + platform_check) in a single GUI.

Features:
- Dark mode UI with color-coded logging
- Full verbose console output for all executions
- Detailed command logging with stdout/stderr capture
- SSH/SCP transfer support for EFI content
- Standalone operation with local requirements.txt

Usage: python debug_framework_installer.py
       (All installation steps logged to both GUI and console)
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import subprocess
import sys
import os
import shutil
import configparser
from pathlib import Path
import threading
import time

# Import credentials manager for encrypted password handling
try:
    from credentials_manager import CredentialsManager
    CREDENTIALS_MANAGER_AVAILABLE = True
except ImportError:
    CREDENTIALS_MANAGER_AVAILABLE = False
    print("⚠ Warning: credentials_manager not available (credentials.enc won't be used)")


# Dark Mode Theme Colors
class DarkTheme:
    """Dark mode color scheme"""
    BG = "#1e1e1e"
    FG = "#d4d4d4"
    SELECT_BG = "#264f78"
    SELECT_FG = "#ffffff"
    BUTTON_BG = "#0e639c"
    BUTTON_FG = "#ffffff"
    ENTRY_BG = "#3c3c3c"
    ENTRY_FG = "#ffffff"
    FRAME_BG = "#252526"
    LABEL_FG = "#cccccc"
    HEADER_BG = "#007acc"
    LOG_BG = "#1e1e1e"
    LOG_FG = "#d4d4d4"
    SUCCESS = "#4ec9b0"
    WARNING = "#ce9178"
    ERROR = "#f48771"
    INFO = "#9cdcfe"


class DebugFrameworkInstaller:
    """Main installer GUI class - Standalone implementation with dark mode"""

    def __init__(self, root):
        self.root = root
        self.root.title("Debug Framework & S2T Installer v1.7.1")
        self.root.geometry("900x850")
        self.root.resizable(True, True)

        # Set dark theme
        self.root.configure(bg=DarkTheme.BG)

        # Installation state
        self.install_thread = None
        self.is_installing = False
        self.install_success = False

        # Paths
        self.script_dir = Path(__file__).parent.resolve()
        self.s2t_root = self.script_dir.parent.parent.parent
        # Note: Actual framework paths vary by user (users.gaespino, users.THR, etc.)
        # and product (GNR, CWF, DMR). No hardcoded baseline paths needed for installer.
        
        # Initialize credentials manager
        self.credentials_manager = None
        if CREDENTIALS_MANAGER_AVAILABLE:
            self.credentials_manager = CredentialsManager()
            if self.credentials_manager.credentials_exist():
                print("✓ Found encrypted credentials file")
            else:
                print("ⓘ No encrypted credentials file (credentials.enc) found")

        # Setup GUI
        self.setup_ui()

    def setup_ui(self):
        """Create the GUI interface with dark mode"""

        # Header
        header_frame = tk.Frame(self.root, bg=DarkTheme.HEADER_BG, height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="Debug Framework & S2T Installer",
            font=("Segoe UI", 18, "bold"),
            bg=DarkTheme.HEADER_BG,
            fg="white"
        )
        title_label.pack(pady=10)

        subtitle_label = tk.Label(
            header_frame,
            text="Standalone installation for GNR, CWF, and DMR platforms",
            font=("Segoe UI", 10),
            bg=DarkTheme.HEADER_BG,
            fg="white"
        )
        subtitle_label.pack()

        # Main content frame with padding
        main_frame = tk.Frame(self.root, bg=DarkTheme.BG, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Configuration Section
        config_frame = tk.LabelFrame(
            main_frame,
            text="Configuration",
            font=("Segoe UI", 10, "bold"),
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG,
            padx=10,
            pady=10
        )
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # COM Port
        com_frame = tk.Frame(config_frame, bg=DarkTheme.FRAME_BG)
        com_frame.pack(fill=tk.X, pady=5)
        tk.Label(
            com_frame,
            text="COM Port Number:",
            width=20,
            anchor="w",
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG
        ).pack(side=tk.LEFT)
        self.com_port_var = tk.StringVar(value="8")
        com_entry = tk.Entry(
            com_frame,
            textvariable=self.com_port_var,
            width=15,
            bg=DarkTheme.ENTRY_BG,
            fg=DarkTheme.ENTRY_FG,
            insertbackground=DarkTheme.ENTRY_FG
        )
        com_entry.pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(
            com_frame,
            text="(e.g., 8 for COM8)",
            fg=DarkTheme.INFO,
            bg=DarkTheme.FRAME_BG
        ).pack(side=tk.LEFT)

        # IP Address
        ip_frame = tk.Frame(config_frame, bg=DarkTheme.FRAME_BG)
        ip_frame.pack(fill=tk.X, pady=5)
        tk.Label(
            ip_frame,
            text="Linux IP Address:",
            width=20,
            anchor="w",
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG
        ).pack(side=tk.LEFT)
        self.ip_address_var = tk.StringVar(value="192.168.0.2")
        ip_entry = tk.Entry(
            ip_frame,
            textvariable=self.ip_address_var,
            width=15,
            bg=DarkTheme.ENTRY_BG,
            fg=DarkTheme.ENTRY_FG,
            insertbackground=DarkTheme.ENTRY_FG
        )
        ip_entry.pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(
            ip_frame,
            text="(e.g., 192.168.0.2)",
            fg=DarkTheme.INFO,
            bg=DarkTheme.FRAME_BG
        ).pack(side=tk.LEFT)

        # Product Selection
        product_frame = tk.Frame(config_frame, bg=DarkTheme.FRAME_BG)
        product_frame.pack(fill=tk.X, pady=5)
        tk.Label(
            product_frame,
            text="Product:",
            width=20,
            anchor="w",
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG
        ).pack(side=tk.LEFT)
        self.product_var = tk.StringVar(value="")
        # Add trace to update EFI source path when product changes
        self.product_var.trace_add("write", lambda *args: self.update_efi_source_from_product())

        # Style for combobox
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Dark.TCombobox',
            fieldbackground=DarkTheme.ENTRY_BG,
            background=DarkTheme.ENTRY_BG,
            foreground=DarkTheme.ENTRY_FG,
            arrowcolor=DarkTheme.ENTRY_FG
        )

        product_combo = ttk.Combobox(
            product_frame,
            textvariable=self.product_var,
            values=["GNR", "CWF", "DMR"],
            state="readonly",
            width=12,
            style='Dark.TCombobox'
        )
        product_combo.pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(
            product_frame,
            text="(GNR/CWF use BASELINE, DMR uses BASELINE_DMR)",
            fg=DarkTheme.INFO,
            bg=DarkTheme.FRAME_BG,
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        # Advanced TeraTerm Configuration (Collapsible)
        self.show_advanced_var = tk.BooleanVar(value=False)
        advanced_toggle = tk.Checkbutton(
            config_frame,
            text="Show Advanced TeraTerm Paths",
            variable=self.show_advanced_var,
            command=self.toggle_advanced_options,
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG,
            selectcolor=DarkTheme.ENTRY_BG,
            activebackground=DarkTheme.FRAME_BG,
            activeforeground=DarkTheme.LABEL_FG
        )
        advanced_toggle.pack(fill=tk.X, pady=(10, 5))

        # Advanced frame (initially hidden)
        self.advanced_frame = tk.Frame(config_frame, bg=DarkTheme.FRAME_BG)

        # TeraTerm Path
        tt_path_frame = tk.Frame(self.advanced_frame, bg=DarkTheme.FRAME_BG)
        tt_path_frame.pack(fill=tk.X, pady=2)
        tk.Label(
            tt_path_frame,
            text="TeraTerm Path:",
            width=20,
            anchor="w",
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG
        ).pack(side=tk.LEFT)
        self.teraterm_path_var = tk.StringVar(value=r"C:\teraterm")
        tt_path_entry = tk.Entry(
            tt_path_frame,
            textvariable=self.teraterm_path_var,
            width=40,
            bg=DarkTheme.ENTRY_BG,
            fg=DarkTheme.ENTRY_FG,
            insertbackground=DarkTheme.ENTRY_FG
        )
        tt_path_entry.pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(
            tt_path_frame,
            text="(Default: C:\\teraterm)",
            fg=DarkTheme.INFO,
            bg=DarkTheme.FRAME_BG,
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        # TeraTerm RVP Path (SETEO H)
        tt_rvp_frame = tk.Frame(self.advanced_frame, bg=DarkTheme.FRAME_BG)
        tt_rvp_frame.pack(fill=tk.X, pady=2)
        tk.Label(
            tt_rvp_frame,
            text="SETEO H Path:",
            width=20,
            anchor="w",
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG
        ).pack(side=tk.LEFT)
        self.teraterm_rvp_path_var = tk.StringVar(value=r"C:\SETEO H")
        tt_rvp_entry = tk.Entry(
            tt_rvp_frame,
            textvariable=self.teraterm_rvp_path_var,
            width=40,
            bg=DarkTheme.ENTRY_BG,
            fg=DarkTheme.ENTRY_FG,
            insertbackground=DarkTheme.ENTRY_FG
        )
        tt_rvp_entry.pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(
            tt_rvp_frame,
            text="(For TeraTerm source)",
            fg=DarkTheme.INFO,
            bg=DarkTheme.FRAME_BG,
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        # TeraTerm INI File
        tt_ini_frame = tk.Frame(self.advanced_frame, bg=DarkTheme.FRAME_BG)
        tt_ini_frame.pack(fill=tk.X, pady=2)
        tk.Label(
            tt_ini_frame,
            text="TeraTerm INI File:",
            width=20,
            anchor="w",
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG
        ).pack(side=tk.LEFT)
        self.teraterm_ini_var = tk.StringVar(value="TERATERM.INI")
        tt_ini_entry = tk.Entry(
            tt_ini_frame,
            textvariable=self.teraterm_ini_var,
            width=40,
            bg=DarkTheme.ENTRY_BG,
            fg=DarkTheme.ENTRY_FG,
            insertbackground=DarkTheme.ENTRY_FG
        )
        tt_ini_entry.pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(
            tt_ini_frame,
            text="(Config file name)",
            fg=DarkTheme.INFO,
            bg=DarkTheme.FRAME_BG,
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        # Options Section
        options_frame = tk.LabelFrame(
            main_frame,
            text="Installation Options",
            font=("Segoe UI", 10, "bold"),
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG,
            padx=10,
            pady=10
        )
        options_frame.pack(fill=tk.X, pady=(0, 10))

        self.install_deps_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Install Python dependencies",
            variable=self.install_deps_var,
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG,
            selectcolor=DarkTheme.ENTRY_BG,
            activebackground=DarkTheme.FRAME_BG,
            activeforeground=DarkTheme.LABEL_FG
        ).pack(anchor="w")

        self.setup_env_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Configure environment variables",
            variable=self.setup_env_var,
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG,
            selectcolor=DarkTheme.ENTRY_BG,
            activebackground=DarkTheme.FRAME_BG,
            activeforeground=DarkTheme.LABEL_FG
        ).pack(anchor="w")

        self.setup_teraterm_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Configure TeraTerm",
            variable=self.setup_teraterm_var,
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG,
            selectcolor=DarkTheme.ENTRY_BG,
            activebackground=DarkTheme.FRAME_BG,
            activeforeground=DarkTheme.LABEL_FG
        ).pack(anchor="w")

        self.copy_efi_var = tk.BooleanVar(value=False)  # Disabled by default
        efi_checkbox = tk.Checkbutton(
            options_frame,
            text="Transfer EFI content to remote system via SSH",
            variable=self.copy_efi_var,
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG,
            selectcolor=DarkTheme.ENTRY_BG,
            activebackground=DarkTheme.FRAME_BG,
            activeforeground=DarkTheme.LABEL_FG
        )
        efi_checkbox.pack(anchor="w")

        # EFI Source Path
        efi_source_frame = tk.Frame(options_frame, bg=DarkTheme.FRAME_BG)
        efi_source_frame.pack(fill=tk.X, padx=(20, 0), pady=(5, 0))
        tk.Label(
            efi_source_frame,
            text="EFI Source Path:",
            width=18,
            anchor="w",
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG,
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        # EFI source path - will be populated when product is selected
        self.efi_source_var = tk.StringVar(value="")
        efi_source_entry = tk.Entry(
            efi_source_frame,
            textvariable=self.efi_source_var,
            width=35,
            bg=DarkTheme.ENTRY_BG,
            fg=DarkTheme.ENTRY_FG,
            insertbackground=DarkTheme.ENTRY_FG
        )
        efi_source_entry.pack(side=tk.LEFT, padx=(0, 5))
        browse_efi_btn = tk.Button(
            efi_source_frame,
            text="Browse...",
            command=self.browse_efi_source,
            bg=DarkTheme.BUTTON_BG,
            fg=DarkTheme.BUTTON_FG,
            relief=tk.FLAT,
            padx=10
        )
        browse_efi_btn.pack(side=tk.LEFT)

        # SSH Username
        efi_username_frame = tk.Frame(options_frame, bg=DarkTheme.FRAME_BG)
        efi_username_frame.pack(fill=tk.X, padx=(20, 0), pady=(5, 0))
        tk.Label(
            efi_username_frame,
            text="SSH Username:",
            width=18,
            anchor="w",
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG,
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        self.efi_username_var = tk.StringVar(value="root")
        efi_username_entry = tk.Entry(
            efi_username_frame,
            textvariable=self.efi_username_var,
            width=20,
            bg=DarkTheme.ENTRY_BG,
            fg=DarkTheme.ENTRY_FG,
            insertbackground=DarkTheme.ENTRY_FG
        )
        efi_username_entry.pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(
            efi_username_frame,
            text="(Default: root)",
            fg=DarkTheme.INFO,
            bg=DarkTheme.FRAME_BG,
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        # SSH Password
        efi_password_frame = tk.Frame(options_frame, bg=DarkTheme.FRAME_BG)
        efi_password_frame.pack(fill=tk.X, padx=(20, 0), pady=(5, 0))
        tk.Label(
            efi_password_frame,
            text="SSH Password:",
            width=18,
            anchor="w",
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG,
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        self.efi_password_var = tk.StringVar(value="")
        self.efi_password_entry = tk.Entry(
            efi_password_frame,
            textvariable=self.efi_password_var,
            width=20,
            show="*",
            bg=DarkTheme.ENTRY_BG,
            fg=DarkTheme.ENTRY_FG,
            insertbackground=DarkTheme.ENTRY_FG
        )
        self.efi_password_entry.pack(side=tk.LEFT, padx=(0, 5))

        # Show password checkbox
        self.show_password_var = tk.BooleanVar(value=False)
        show_pass_check = tk.Checkbutton(
            efi_password_frame,
            text="Show",
            variable=self.show_password_var,
            command=self.toggle_password_visibility,
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG,
            selectcolor=DarkTheme.ENTRY_BG,
            activebackground=DarkTheme.FRAME_BG,
            activeforeground=DarkTheme.LABEL_FG,
            font=("Segoe UI", 8)
        )
        show_pass_check.pack(side=tk.LEFT, padx=(5, 5))

        tk.Label(
            efi_password_frame,
            text="(Console prompt if sshpass not installed)",
            fg=DarkTheme.WARNING,
            bg=DarkTheme.FRAME_BG,
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        # SSH Remote Path
        efi_remote_frame = tk.Frame(options_frame, bg=DarkTheme.FRAME_BG)
        efi_remote_frame.pack(fill=tk.X, padx=(20, 0), pady=(5, 0))
        tk.Label(
            efi_remote_frame,
            text="Linux Remote Path:",
            width=18,
            anchor="w",
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG,
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        self.efi_remote_path_var = tk.StringVar(value="/run/media/EFI_CONTENT/")
        efi_remote_entry = tk.Entry(
            efi_remote_frame,
            textvariable=self.efi_remote_path_var,
            width=35,
            bg=DarkTheme.ENTRY_BG,
            fg=DarkTheme.ENTRY_FG,
            insertbackground=DarkTheme.ENTRY_FG
        )
        efi_remote_entry.pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(
            efi_remote_frame,
            text="(Target directory on Linux)",
            fg=DarkTheme.INFO,
            bg=DarkTheme.FRAME_BG,
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        # Button Section - Fixed to prevent disappearing (Pack BEFORE progress section)
        button_frame = tk.Frame(main_frame, bg=DarkTheme.BG, height=60)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        button_frame.pack_propagate(False)  # Prevent shrinking

        self.install_button = tk.Button(
            button_frame,
            text="Start Installation",
            command=self.start_installation,
            bg=DarkTheme.BUTTON_BG,
            fg=DarkTheme.BUTTON_FG,
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.install_button.pack(side=tk.LEFT, padx=(0, 10), pady=10)

        self.close_button = tk.Button(
            button_frame,
            text="Close",
            command=self.close_application,
            bg=DarkTheme.ENTRY_BG,
            fg=DarkTheme.LABEL_FG,
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.close_button.pack(side=tk.LEFT, pady=10)

        # Progress Section
        progress_frame = tk.LabelFrame(
            main_frame,
            text="Installation Progress",
            font=("Segoe UI", 10, "bold"),
            bg=DarkTheme.FRAME_BG,
            fg=DarkTheme.LABEL_FG,
            padx=10,
            pady=10
        )
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.progress_text = scrolledtext.ScrolledText(
            progress_frame,
            height=12,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg=DarkTheme.LOG_BG,
            fg=DarkTheme.LOG_FG,
            insertbackground=DarkTheme.LOG_FG
        )
        self.progress_text.pack(fill=tk.BOTH, expand=True)
        self.progress_text.config(state=tk.DISABLED)

        # Configure text tags for colors
        self.progress_text.tag_config("success", foreground=DarkTheme.SUCCESS)
        self.progress_text.tag_config("warning", foreground=DarkTheme.WARNING)
        self.progress_text.tag_config("error", foreground=DarkTheme.ERROR)
        self.progress_text.tag_config("info", foreground=DarkTheme.INFO)

        # Progress bar
        style.configure(
            "Dark.Horizontal.TProgressbar",
            background=DarkTheme.HEADER_BG,
            troughcolor=DarkTheme.ENTRY_BG,
            bordercolor=DarkTheme.FRAME_BG,
            lightcolor=DarkTheme.HEADER_BG,
            darkcolor=DarkTheme.HEADER_BG
        )
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            style="Dark.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))

    def browse_efi_source(self):
        """Browse for EFI source path"""
        path = filedialog.askdirectory(title="Select EFI Content Source Directory")
        if path:
            self.efi_source_var.set(path)

    def update_efi_source_from_product(self):
        """Update EFI source path based on product selection"""
        product = self.product_var.get()
        base_path = r"\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates"
        default_path = f"{base_path}\\{product}\\EFI"

        # Only update if current path is empty or is a default template path
        current_path = self.efi_source_var.get()
        if not current_path or "Templates" in current_path:
            self.efi_source_var.set(default_path)

    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.show_password_var.get():
            self.efi_password_entry.config(show="")
        else:
            self.efi_password_entry.config(show="*")

    def toggle_advanced_options(self):
        """Toggle advanced TeraTerm path options visibility"""
        if self.show_advanced_var.get():
            self.advanced_frame.pack(fill=tk.X, pady=(5, 10))
        else:
            self.advanced_frame.pack_forget()

    def log(self, message, color="normal"):
        """Add message to progress log with color support and print to console"""
        self.progress_text.config(state=tk.NORMAL)

        # Add timestamp
        timestamp = time.strftime("%H:%M:%S")

        # Map color names to tags
        tag_map = {
            "success": "success",
            "green": "success",
            "warning": "warning",
            "orange": "warning",
            "error": "error",
            "red": "error",
            "info": "info",
            "blue": "info",
            "gray": "info"
        }

        tag = tag_map.get(color.lower(), None)

        # Insert text with tag
        self.progress_text.insert(tk.END, f"[{timestamp}] ")
        if tag:
            self.progress_text.insert(tk.END, f"{message}\n", tag)
        else:
            self.progress_text.insert(tk.END, f"{message}\n")

        # Auto-scroll
        self.progress_text.see(tk.END)

        self.progress_text.config(state=tk.DISABLED)

        # VERBOSE: Print to console as well
        print(f"[{timestamp}] {message}")

        self.root.update()

    def run_subprocess(self, cmd, description, timeout=30):
        """Run subprocess with verbose logging of command and output"""
        try:
            # Log the command being executed
            cmd_str = ' '.join([str(c) for c in cmd])
            self.log(f"  VERBOSE: Executing command:", "info")
            self.log(f"    {cmd_str}", "gray")
            print(f"VERBOSE CMD: {cmd_str}")  # Extra console output

            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Log stdout if available
            if result.stdout and result.stdout.strip():
                self.log(f"  VERBOSE: Command output:", "info")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        self.log(f"    {line}", "gray")
                        print(f"STDOUT: {line}")  # Extra console output

            # Log stderr if available
            if result.stderr and result.stderr.strip():
                self.log(f"  VERBOSE: Command stderr:", "warning")
                for line in result.stderr.strip().split('\n'):
                    if line.strip():
                        self.log(f"    {line}", "gray")
                        print(f"STDERR: {line}")  # Extra console output

            # Log return code
            self.log(f"  VERBOSE: Return code: {result.returncode}", "info")
            print(f"VERBOSE: Return code: {result.returncode}")  # Extra console output

            return result

        except subprocess.TimeoutExpired as e:
            self.log(f"  ✗ Command timed out after {timeout}s", "error")
            raise
        except Exception as e:
            self.log(f"  ✗ Command execution failed: {e}", "error")
            raise

    def start_installation(self):
        """Start the installation process in a separate thread"""
        if self.is_installing:
            messagebox.showwarning("Installation In Progress", "Installation is already running!")
            return

        # Validate inputs
        com_port = self.com_port_var.get().strip()
        ip_address = self.ip_address_var.get().strip()

        if not com_port or not com_port.isdigit():
            messagebox.showerror("Invalid Input", "Please enter a valid COM port number (e.g., 8)")
            return

        if not ip_address or not self.validate_ip(ip_address):
            messagebox.showerror("Invalid Input", "Please enter a valid IP address (e.g., 192.168.0.2)")
            return

        # Clear log
        self.progress_text.config(state=tk.NORMAL)
        self.progress_text.delete(1.0, tk.END)
        self.progress_text.config(state=tk.DISABLED)

        # Disable buttons
        self.install_button.config(state=tk.DISABLED)
        self.is_installing = True

        # Start progress bar
        self.progress_bar.start()

        # Start installation in separate thread
        self.install_thread = threading.Thread(target=self.run_installation, daemon=True)
        self.install_thread.start()

    def validate_ip(self, ip):
        """Validate IP address format"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False

    def run_installation(self):
        """Run the installation process - Standalone 2-step implementation"""
        try:
            self.log("=" * 70, "info")
            self.log("DEBUG FRAMEWORK & S2T INSTALLER v1.7.1 (Standalone)", "info")
            self.log("=" * 70, "info")
            self.log("This installer replicates: TeratermEnv.ps1 + platform_check()")
            self.log("")

            # VERBOSE: Log configuration
            self.log("VERBOSE: Installation Configuration", "info")
            self.log(f"  COM Port: {self.com_port_var.get()}", "gray")
            self.log(f"  IP Address: {self.ip_address_var.get()}", "gray")
            self.log(f"  Product: {self.product_var.get()}", "gray")
            self.log(f"  Install Dependencies: {self.install_deps_var.get()}", "gray")
            self.log(f"  Setup Environment: {self.setup_env_var.get()}", "gray")
            self.log(f"  Configure TeraTerm: {self.setup_teraterm_var.get()}", "gray")
            self.log(f"  Transfer EFI via SSH: {self.copy_efi_var.get()}", "gray")
            if self.copy_efi_var.get():
                self.log(f"  EFI Source Path: {self.efi_source_var.get()}", "gray")
                self.log(f"  SSH Username: {self.efi_username_var.get()}", "gray")
                password_display = f"{'*' * len(self.efi_password_var.get())}" if self.efi_password_var.get() else "(not set - will prompt)"
                self.log(f"  SSH Password: {password_display}", "gray")
                self.log(f"  SSH Remote Path: {self.efi_remote_path_var.get()}", "gray")
            self.log(f"  Script Directory: {self.script_dir}", "gray")
            self.log(f"  S2T Root: {self.s2t_root}", "gray")
            self.log("")

            # Step 1: Check Python
            if not self.check_python():
                self.installation_failed("Python check failed")
                return

            # Step 2: Install dependencies
            if self.install_deps_var.get():
                if not self.install_dependencies():
                    self.installation_failed("Dependency installation failed")
                    return
            else:
                self.log("Skipping dependency installation (disabled)")

            # Step 3: Setup environment variables (Step 1 of original 2-step)
            if self.setup_env_var.get():
                if not self.setup_environment_variables():
                    self.installation_failed("Environment variable setup failed")
                    return
            else:
                self.log("Skipping environment variable setup (disabled)")

            # Step 4: Configure TeraTerm (Step 2 of original 2-step - teraterm_check)
            if self.setup_teraterm_var.get():
                if not self.configure_teraterm():
                    self.installation_failed("TeraTerm configuration failed")
                    return
            else:
                self.log("Skipping TeraTerm configuration (disabled)")

            # Step 5: Transfer EFI content via SSH
            if self.copy_efi_var.get() and self.efi_source_var.get():
                if not self.transfer_efi_content_ssh():
                    self.log("WARNING: EFI content transfer failed (non-critical)", "warning")
            elif self.copy_efi_var.get():
                self.log("Skipping EFI content transfer (no source path specified)", "warning")

            # Step 6: Validate installation
            if not self.validate_installation():
                self.installation_failed("Installation validation failed")
                return

            # Success!
            self.installation_complete()

        except Exception as e:
            self.log(f"ERROR: Unexpected error: {e}", "error")
            self.installation_failed(str(e))

    def check_python(self):
        """Check Python installation"""
        self.log("[1/6] Checking Python installation...")
        try:
            result = self.run_subprocess(
                [sys.executable, "--version"],
                "Check Python version",
                timeout=10
            )
            version = result.stdout.strip()
            self.log(f"  ✓ {version} detected", "success")
            return True
        except Exception as e:
            self.log(f"  ✗ Python check failed: {e}", "error")
            return False

    def install_dependencies(self):
        """Install Python dependencies from local requirements.txt"""
        self.log("")
        self.log("[2/6] Installing Python dependencies...")
        self.log("  This may take several minutes...")

        try:
            # Use local requirements.txt in config folder
            requirements_file = self.script_dir.parent / "config" / "requirements.txt"

            if not requirements_file.exists():
                self.log(f"  ✗ Requirements file not found: {requirements_file}", "error")
                return False

            # Upgrade pip first
            self.log("  Upgrading pip...")
            pip_upgrade_result = self.run_subprocess(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                "Upgrade pip",
                timeout=120
            )

            # Install from requirements.txt
            self.log(f"  Installing from {requirements_file}...")
            result = self.run_subprocess(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                "Install requirements",
                timeout=300
            )
            if result.returncode != 0:
                self.log(f"  WARNING: Some packages failed to install", "warning")

            self.log("  ✓ Dependency installation completed", "success")
            return True

        except Exception as e:
            self.log(f"  ✗ Dependency installation failed: {e}", "error")
            return False

    def setup_environment_variables(self):
        """Setup environment variables - Step 1 of original 2-step process"""
        self.log("")
        self.log("[3/6] Configuring environment variables (TeratermEnv.ps1 equivalent)...")

        com_port = self.com_port_var.get()
        ip_address = self.ip_address_var.get()

        # Check if PowerShell script exists
        ps_script = self.script_dir / "TeratermEnv.ps1"

        if ps_script.exists():
            self.log(f"  Running PowerShell configuration script...")
            try:
                # Run PowerShell script with original variable names
                cmd = [
                    "powershell.exe",
                    "-ExecutionPolicy", "Bypass",
                    "-File", str(ps_script),
                    "-com", com_port,
                    "-ip", ip_address
                ]

                result = self.run_subprocess(
                    cmd,
                    "Run TeratermEnv.ps1",
                    timeout=30
                )

                if result.returncode == 0:
                    self.log("  ✓ Environment variables configured via PowerShell", "success")
                    return True
                else:
                    self.log("  WARNING: PowerShell script had issues, setting manually...", "warning")
                    return self.set_env_variables_manually(com_port, ip_address)

            except Exception as e:
                self.log(f"  WARNING: PowerShell failed: {e}", "warning")
                return self.set_env_variables_manually(com_port, ip_address)
        else:
            self.log("  PowerShell script not found, setting variables manually...")
            return self.set_env_variables_manually(com_port, ip_address)

    def set_env_variables_manually(self, com_port, ip_address):
        """Set environment variables manually - with encrypted credentials support"""
        try:
            # SECURITY: Priority order for password retrieval:
            # 1. Encrypted credentials file (credentials.enc)
            # 2. Existing environment variables
            # 3. User prompt via GUI dialogs
            
            framework_pass = ''
            danta_pass = ''
            framework_user = 'root'
            
            # Step 1: Try to load from encrypted credentials file
            if self.credentials_manager and self.credentials_manager.credentials_exist():
                self.log("  Loading credentials from encrypted file...", "info")
                try:
                    # Check if password-based encryption
                    password = None
                    if self.credentials_manager.key_file.exists():
                        with open(self.credentials_manager.key_file, 'rb') as f:
                            key_data = f.read()
                        if key_data.startswith(b'SALT:'):
                            # Prompt for decryption password
                            password = simpledialog.askstring(
                                "Decryption Password",
                                "Enter password to decrypt credentials file:",
                                show='*',
                                parent=self.root
                            )
                            if not password:
                                self.log("  ⚠ No decryption password provided", "warning")
                                raise ValueError("Decryption password required")
                    
                    credentials = self.credentials_manager.load_credentials(password)
                    if credentials:
                        framework_pass = credentials.get('FrameworkDefaultPass', '')
                        danta_pass = credentials.get('DANTA_DB_PASSWORD', '')
                        framework_user = credentials.get('FrameworkDefaultUser', 'root')
                        self.log("  ✓ Credentials loaded from encrypted file", "success")
                        
                        # Store SSH password if available (for later use)
                        if 'SSH_PASSWORD' in credentials and credentials['SSH_PASSWORD']:
                            self.efi_password_var.set(credentials['SSH_PASSWORD'])
                    else:
                        self.log("  ⚠ Failed to decrypt credentials file", "warning")
                        raise ValueError("Decryption failed")
                        
                except Exception as e:
                    self.log(f"  ⚠ Could not load encrypted credentials: {e}", "warning")
                    self.log("  Falling back to environment variables or prompts...", "info")
            
            # Step 2: Check environment variables (if not loaded from file)
            if not framework_pass:
                existing_framework_pass = os.getenv('FrameworkDefaultPass', '')
                if existing_framework_pass:
                    framework_pass = existing_framework_pass
                    self.log("  ✓ Using FrameworkDefaultPass from environment", "success")
            
            if not danta_pass:
                existing_danta_pass = os.getenv('DANTA_DB_PASSWORD', '')
                if existing_danta_pass:
                    danta_pass = existing_danta_pass
                    self.log("  ✓ Using DANTA_DB_PASSWORD from environment", "success")

            
            # Step 3: Prompt user if still not found
            if not framework_pass:
                self.log("  ⓘ FrameworkDefaultPass not found", "info")
                response = messagebox.askyesno(
                    "Password Required",
                    "FrameworkDefaultPass is not set in your environment.\n\n"
                    "This password is required for framework operation.\n\n"
                    "Would you like to enter it now?\n"
                    "(If No, you'll need to set it manually later)",
                    parent=self.root
                )
                if response:
                    password = simpledialog.askstring(
                        "Framework Password",
                        "Enter FrameworkDefaultPass:\n(Contact your team lead if you don't know this)",
                        show='*',
                        parent=self.root
                    )
                    if password:
                        framework_pass = password
                    else:
                        self.log("  ⚠ Skipped FrameworkDefaultPass (set manually later)", "warning")
                else:
                    self.log("  ⚠ Skipped FrameworkDefaultPass (set manually later)", "warning")

            if not danta_pass:
                self.log("  ⓘ DANTA_DB_PASSWORD not found", "info")
                response = messagebox.askyesno(
                    "Database Password Required",
                    "DANTA_DB_PASSWORD is not set in your environment.\n\n"
                    "This password is required for database access.\n\n"
                    "Would you like to enter it now?\n"
                    "(If No, you'll need to set it manually later)",
                    parent=self.root
                )
                if response:
                    password = simpledialog.askstring(
                        "Database Password",
                        "Enter DANTA_DB_PASSWORD:\n(Contact your team lead if you don't know this)",
                        show='*',
                        parent=self.root
                    )
                    if password:
                        danta_pass = password
                    else:
                        self.log("  ⚠ Skipped DANTA_DB_PASSWORD (set manually later)", "warning")
                else:
                    self.log("  ⚠ Skipped DANTA_DB_PASSWORD (set manually later)", "warning")

            # Use original variable names from TeratermEnv.ps1
            variables = {
                'FrameworkSerial': com_port,
                'FrameworkIPAdress': ip_address,
                'FrameworkDefaultPass': framework_pass,
                'FrameworkDefaultUser': framework_user,
                'DANTA_DB_PASSWORD': danta_pass
            }

            self.log("  Setting environment variables (User level)...")
            for var_name, var_value in variables.items():
                # Skip password variables if empty (user chose not to set them)
                if var_name in ['FrameworkDefaultPass', 'DANTA_DB_PASSWORD'] and not var_value:
                    self.log(f"    Skipping {var_name} (not provided)", "warning")
                    continue

                # Log without showing password values
                if var_name in ['FrameworkDefaultPass', 'DANTA_DB_PASSWORD']:
                    self.log(f"    Setting {var_name}=*** (hidden)", "info")
                else:
                    self.log(f"    Setting {var_name}={var_value}", "info")

                self.run_subprocess(
                    ["setx", var_name, var_value],
                    f"Set {var_name}",
                    timeout=10
                )
                # Set in current process too
                os.environ[var_name] = var_value

            self.log("  ✓ Environment variables set (restart PythonSV to load)", "success")
            return True

        except Exception as e:
            self.log(f"  ✗ Failed to set environment variables: {e}", "error")
            return False

    def configure_teraterm(self):
        """Configure TeraTerm - Step 2 of original 2-step (teraterm_check equivalent)"""
        self.log("")
        self.log("[4/6] Configuring TeraTerm (platform_check equivalent)...")

        com_port = self.com_port_var.get()
        ip_address = self.ip_address_var.get()

        teraterm_path = self.teraterm_path_var.get()
        seteo_h_path = self.teraterm_rvp_path_var.get()
        ini_file = self.teraterm_ini_var.get()
        ini_file_path = Path(teraterm_path) / ini_file

        try:
            # Step 1: Check if TERATERM.INI exists, if not copy from SETEO H
            if not ini_file_path.exists():
                self.log(f"  TeraTerm not found at {teraterm_path}")
                self.log(f"  Searching for TeraTerm at {seteo_h_path}...")

                source_folder = Path(seteo_h_path) / "teraterm"
                if source_folder.exists():
                    self.log(f"  Copying TeraTerm from {source_folder}...")
                    shutil.copytree(source_folder, teraterm_path)
                    self.log("  ✓ TeraTerm copied successfully", "success")
                else:
                    self.log(f"  ✗ TeraTerm not found at {seteo_h_path}", "error")
                    self.log(f"  Please install TeraTerm or check SETEO H path", "warning")
                    return False

            # Step 2: Configure TERATERM.INI
            self.log("  Configuring TERATERM.INI...")

            # Configuration values matching FileHandler.teraterm_check
            init_check_variables = {
                'ComPort': str(com_port),
                'BaudRate': '115200',
                'Parity': 'none',
                'DataBit': '8',
                'StopBit': '1',
                'FlowCtrl': 'none',
                'DelayPerChar': '100',
                'DelayPerLine': '100',
            }

            # Read and update INI file
            with open(ini_file_path, 'r') as file:
                lines = file.readlines()

            with open(ini_file_path, 'w') as file:
                for line in lines:
                    written = False
                    for key, value in init_check_variables.items():
                        if line.startswith(f'{key}='):
                            file.write(f'{key}={value}\n')
                            self.log(f"    {key} = {value}", "info")
                            written = True
                            break
                    if not written:
                        file.write(line)

            self.log("  ✓ TeraTerm INI configured successfully", "success")

            # Step 3: Check environment variables
            self.log("  Checking environment variables...")
            env_check_passed = self.check_env_variables(com_port, ip_address)

            if not env_check_passed:
                self.log("  WARNING: Some environment variables are not set correctly", "warning")
                self.log("  They will be available after restarting PythonSV", "warning")

            return True

        except Exception as e:
            self.log(f"  ✗ TeraTerm configuration failed: {e}", "error")
            return False

    def check_env_variables(self, com_port, ip_address):
        """Check environment variables - Standalone version of FileHandler.check_env_variables"""
        host_variables = {
            'FrameworkSerial': com_port,
            'FrameworkIPAdress': ip_address,
            'FrameworkDefaultPass': None,
            'FrameworkDefaultUser': None,
        }

        all_ok = True
        for var_name, desired_value in host_variables.items():
            current_value = os.getenv(var_name, None)

            if current_value is None:
                self.log(f"    X {var_name} not set (will be set after install)", "gray")
                all_ok = False
            elif desired_value is not None and current_value != desired_value:
                self.log(f"    ! {var_name} = {current_value} (expected: {desired_value})", "warning")
                all_ok = False
            else:
                self.log(f"    ✓ {var_name} = {current_value}", "success")

        return all_ok

    def transfer_efi_content_ssh(self):
        """Transfer EFI content to remote system via SSH"""
        self.log("")
        self.log("[5/6] Transferring EFI content via SSH...")

        source_path = Path(self.efi_source_var.get())
        ip_address = self.ip_address_var.get()
        remote_path = self.efi_remote_path_var.get()
        username = self.efi_username_var.get()
        password = self.efi_password_var.get()

        try:
            if not source_path.exists():
                self.log(f"  ✗ Source path does not exist: {source_path}", "error")
                return False

            self.log(f"  Source: {source_path}")
            self.log(f"  Remote: {username}@{ip_address}:{remote_path}")

            # Check if scp or pscp is available
            self.log("  VERBOSE: Checking for SCP/PSCP availability...", "info")
            scp_cmd = None
            try:
                self.log("  VERBOSE: Testing 'scp' command...", "gray")
                subprocess.run(["scp", "-V"], capture_output=True, timeout=5)
                scp_cmd = "scp"
                self.log("  VERBOSE: Found 'scp' command", "success")
            except:
                try:
                    self.log("  VERBOSE: Testing 'pscp' command...", "gray")
                    subprocess.run(["pscp", "-V"], capture_output=True, timeout=5)
                    scp_cmd = "pscp"
                    self.log("  VERBOSE: Found 'pscp' command", "success")
                except:
                    self.log("  ✗ SCP/PSCP not found. Please install OpenSSH or PuTTY", "error")
                    return False

            self.log(f"  Using {scp_cmd} for file transfer...")
            self.log(f"  This may take several minutes depending on content size...")

            # Build command with password authentication
            if scp_cmd == "scp":
                # Use sshpass for OpenSSH scp (if available and password provided)
                password_provided = password and password.strip()
                if password_provided:
                    try:
                        subprocess.run(["sshpass", "-V"], capture_output=True, timeout=5)
                        cmd = [
                            "sshpass", "-p", password,
                            "scp",
                            "-r",
                            "-o", "StrictHostKeyChecking=no",
                            "-o", "UserKnownHostsFile=/dev/null",
                            str(source_path),
                            f"{username}@{ip_address}:{remote_path}"
                        ]
                        self.log("  Using sshpass for password authentication", "info")
                    except:
                        # Fallback to interactive
                        cmd = [
                            "scp",
                            "-r",
                            "-o", "StrictHostKeyChecking=no",
                            "-o", "UserKnownHostsFile=/dev/null",
                            str(source_path),
                            f"{username}@{ip_address}:{remote_path}"
                        ]
                        self.log("  ⚠ sshpass not found - you will be prompted for password in console", "warning")
                        # Alert user to check console
                        self.root.after(0, lambda: messagebox.showinfo(
                            "Password Required",
                            "PASSWORD INPUT REQUIRED\n\n"
                            "sshpass is not installed. You will be prompted to enter\n"
                            "the SSH password in the CONSOLE window.\n\n"
                            "Please check the console window and enter the password there.\n\n"
                            "Install sshpass for automatic password authentication.",
                            parent=self.root
                        ))
                else:
                    # No password provided, interactive prompt
                    cmd = [
                        "scp",
                        "-r",
                        "-o", "StrictHostKeyChecking=no",
                        "-o", "UserKnownHostsFile=/dev/null",
                        str(source_path),
                        f"{username}@{ip_address}:{remote_path}"
                    ]
                    self.log("  ⚠ No password provided - you will be prompted for password in console", "warning")
                    # Alert user to check console
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Password Required",
                        "PASSWORD INPUT REQUIRED\n\n"
                        "No password was provided. You will be prompted to enter\n"
                        "the SSH password in the CONSOLE window.\n\n"
                        "Please check the console window and enter the password there.",
                        parent=self.root
                    ))
            else:
                # Use pscp (PuTTY) with -pw flag if password provided
                password_provided = password and password.strip()
                if password_provided:
                    cmd = [
                        "pscp",
                        "-r",
                        "-pw", password,
                        "-o", "StrictHostKeyChecking=no",
                        "-o", "UserKnownHostsFile=/dev/null",
                        str(source_path),
                        f"{username}@{ip_address}:{remote_path}"
                    ]
                    self.log("  Using pscp with password authentication", "info")
                else:
                    cmd = [
                        "pscp",
                        "-r",
                        "-o", "StrictHostKeyChecking=no",
                        "-o", "UserKnownHostsFile=/dev/null",
                        str(source_path),
                        f"{username}@{ip_address}:{remote_path}"
                    ]
                    self.log("  ⚠ No password provided - you will be prompted for password in console", "warning")
                    # Alert user to check console
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Password Required",
                        "PASSWORD INPUT REQUIRED\n\n"
                        "No password was provided. You will be prompted to enter\n"
                        "the SSH password in the CONSOLE window.\n\n"
                        "Please check the console window and enter the password there.",
                        parent=self.root
                    ))

            self.log("  ℹ Recommended: Set up SSH key authentication for automatic transfers", "info")
            self.log("  ℹ If prompted for password, enter it in the CONSOLE window (not GUI)", "info")

            # Start transfer
            self.log("  Starting SSH transfer (this may take several minutes)...", "info")
            result = self.run_subprocess(
                cmd,
                "SSH/SCP transfer",
                timeout=300
            )

            if result.returncode == 0:
                self.log("  ✓ EFI content transferred successfully", "success")

                # Copy startup files to remote base path
                if not self.copy_startup_files_ssh(source_path, username, ip_address, remote_path, password, scp_cmd):
                    self.log("  ⚠ Startup files copy had issues (non-critical)", "warning")

                return True
            else:
                self.log(f"  ✗ Transfer failed", "error")
                self.log("  Consider setting up SSH key authentication", "warning")
                return False

        except subprocess.TimeoutExpired:
            self.log("  ✗ Transfer timed out (300s limit)", "error")
            return False
        except Exception as e:
            self.log(f"  ✗ Transfer failed: {e}", "error")
            return False

    def copy_startup_files_ssh(self, source_path, username, ip_address, remote_path, password, scp_cmd):
        """Copy startup_linux.nsh and startup_efi.nsh to remote base path"""
        try:
            self.log("  Copying startup files to remote base path...", "info")

            startup_files = ["startup_linux.nsh", "startup_efi.nsh"]
            success_count = 0

            for filename in startup_files:
                source_file = source_path / filename

                if not source_file.exists():
                    self.log(f"    ⚠ {filename} not found in source, skipping", "warning")
                    continue

                # Build SCP command for individual file
                password_provided = password and password.strip()

                if scp_cmd == "scp":
                    if password_provided:
                        try:
                            subprocess.run(["sshpass", "-V"], capture_output=True, timeout=5)
                            cmd = [
                                "sshpass", "-p", password,
                                "scp",
                                "-o", "StrictHostKeyChecking=no",
                                "-o", "UserKnownHostsFile=/dev/null",
                                str(source_file),
                                f"{username}@{ip_address}:{remote_path}"
                            ]
                        except:
                            cmd = [
                                "scp",
                                "-o", "StrictHostKeyChecking=no",
                                "-o", "UserKnownHostsFile=/dev/null",
                                str(source_file),
                                f"{username}@{ip_address}:{remote_path}"
                            ]
                    else:
                        cmd = [
                            "scp",
                            "-o", "StrictHostKeyChecking=no",
                            "-o", "UserKnownHostsFile=/dev/null",
                            str(source_file),
                            f"{username}@{ip_address}:{remote_path}"
                        ]
                else:
                    # pscp
                    if password_provided:
                        cmd = [
                            "pscp",
                            "-pw", password,
                            "-o", "StrictHostKeyChecking=no",
                            "-o", "UserKnownHostsFile=/dev/null",
                            str(source_file),
                            f"{username}@{ip_address}:{remote_path}"
                        ]
                    else:
                        cmd = [
                            "pscp",
                            "-o", "StrictHostKeyChecking=no",
                            "-o", "UserKnownHostsFile=/dev/null",
                            str(source_file),
                            f"{username}@{ip_address}:{remote_path}"
                        ]

                # Execute copy
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    self.log(f"    ✓ Copied {filename} to {remote_path}", "success")
                    success_count += 1
                else:
                    self.log(f"    ✗ Failed to copy {filename}", "error")

            if success_count > 0:
                self.log(f"  ✓ Copied {success_count}/{len(startup_files)} startup files", "success")
                return True
            else:
                self.log("  ⚠ No startup files were copied", "warning")
                return False

        except Exception as e:
            self.log(f"  ✗ Startup files copy failed: {e}", "error")
            return False

    def validate_installation(self):
        """Validate the installation"""
        self.log("")
        self.log("[6/6] Validating installation...")

        validation_passed = True

        # Check critical packages
        critical_packages = ["pandas", "pymongo", "xlwings", "zeep", "openpyxl"]
        self.log("  Checking critical packages...")

        for package in critical_packages:
            try:
                __import__(package)
                self.log(f"    ✓ {package}", "success")
            except ImportError:
                self.log(f"    ✗ {package} (missing)", "error")
                validation_passed = False

        # Check environment variables
        self.log("  Checking environment variables...")
        com_port = os.environ.get("FrameworkSerial")
        ip_address = os.environ.get("FrameworkIPAdress")

        if com_port:
            self.log(f"    ✓ FrameworkSerial = {com_port}", "success")
        else:
            self.log("    ! FrameworkSerial not set in current session", "warning")
            self.log("      (Will be available after restart)")

        if ip_address:
            self.log(f"    ✓ FrameworkIPAdress = {ip_address}", "success")
        else:
            self.log("    ! FrameworkIPAdress not set in current session", "warning")
            self.log("      (Will be available after restart)")

        # Check TeraTerm
        teraterm_ini = Path(self.teraterm_path_var.get()) / self.teraterm_ini_var.get()
        if teraterm_ini.exists():
            self.log("    ✓ TeraTerm configured", "success")
        else:
            self.log("    ✗ TeraTerm not found", "warning")

        return validation_passed

    def installation_complete(self):
        """Handle successful installation"""
        self.log("")
        self.log("=" * 70, "success")
        self.log("INSTALLATION COMPLETED SUCCESSFULLY!", "success")
        self.log("=" * 70, "success")
        self.log("")
        self.log("This installer replicated the 2-step process:")
        self.log("  Step 1: TeratermEnv.ps1 (environment variables)")
        self.log("  Step 2: platform_check() (TeraTerm configuration)")
        self.log("")
        self.log("NEXT STEPS:")
        self.log("1. RESTART PythonSV (close and reopen to load environment variables)")
        self.log("")
        self.log("2. VERIFY installation in PythonSV:")
        self.log("")

        product = self.product_var.get()
        com_port = self.com_port_var.get()
        ip_address = self.ip_address_var.get()

        if product == "DMR":
            self.log("   import users.gaespino.dev.DebugFramework.SystemDebug as gdf", "info")
        elif product == "GNR":
            self.log("   import users.gaespino.DebugFramework.GNRSystemDebug as gdf", "info")
        else:  # CWF
            self.log("   import users.gaespino.DebugFramework.CWFSystemDebug as gdf", "info")

        self.log(f"   gdf.Frameworkutils.platform_check(com_port={com_port}, ip_address='{ip_address}')", "info")
        self.log("")
        self.log("3. Review documentation:")
        self.log(f"   {self.script_dir.parent}")
        self.log("")

        self.progress_bar.stop()
        self.is_installing = False
        self.install_success = True
        self.install_button.config(
            state=tk.NORMAL,
            text="Installation Complete",
            bg="#00aa00"
        )

        messagebox.showinfo(
            "Installation Complete",
            "Debug Framework installation completed successfully!\n\n"
            "Please restart PythonSV and run platform_check() to verify."
        )

    def installation_failed(self, reason):
        """Handle failed installation"""
        self.log("")
        self.log("=" * 70, "error")
        self.log("INSTALLATION FAILED!", "error")
        self.log(f"Reason: {reason}", "error")
        self.log("=" * 70, "error")
        self.log("")
        self.log("Please review the errors above and try again.")
        self.log("For support, contact: gabriel.espinoza.ballestero@intel.com")

        self.progress_bar.stop()
        self.is_installing = False
        self.install_button.config(state=tk.NORMAL)

        messagebox.showerror(
            "Installation Failed",
            f"Installation failed: {reason}\n\n"
            "Please check the log for details."
        )

    def close_application(self):
        """Close the application"""
        if self.is_installing:
            if not messagebox.askyesno(
                "Installation In Progress",
                "Installation is still running. Are you sure you want to close?"
            ):
                return

        self.root.quit()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = DebugFrameworkInstaller(root)
    root.mainloop()


if __name__ == "__main__":
    main()
