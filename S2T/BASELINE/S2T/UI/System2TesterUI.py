import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
from tabulate import tabulate

class ConfigApp:
	def __init__(self, root, S2TFlow, debug=False):
		self.root = root
		self.root.title("System 2 Tester Configuration")
		self.s2t_flow = S2TFlow
		self.debug = debug
		
		# Apply dark theme
		style = ttk.Style()
		available_themes = style.theme_names()
		# Try to use a darker theme if available
		if 'clam' in available_themes:
			style.theme_use('clam')
		elif 'alt' in available_themes:
			style.theme_use('alt')
		
		self.create_widgets()

	def create_widgets(self):
		# Main container
		main_frame = ttk.Frame(self.root, padding="10")
		main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
		
		# Title
		title = ttk.Label(main_frame, text="System 2 Tester Configuration Manager", font=('Segoe UI', 12, 'bold'))
		title.grid(row=0, column=0, columnspan=2, pady=(0, 10))
		
		# Load Config Section
		load_label = ttk.Label(main_frame, text="Configuration File:")
		load_label.grid(row=1, column=0, sticky=tk.W, pady=5)

		self.load_path_var = tk.StringVar()
		self.load_path_entry = ttk.Entry(main_frame, textvariable=self.load_path_var, state='readonly', width=50)
		self.load_path_entry.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)

		self.load_button = ttk.Button(main_frame, text="Browse", command=self.load_config)
		self.load_button.grid(row=2, column=1, padx=(5, 0), pady=5)

		# Status Label
		self.waiting_label = ttk.Label(main_frame, text="", foreground="orange")
		self.waiting_label.grid(row=3, column=0, columnspan=2, pady=10)

		# Action Buttons
		button_frame = ttk.Frame(main_frame)
		button_frame.grid(row=4, column=0, columnspan=2, pady=10)

		self.run_button = ttk.Button(button_frame, text="Run Configuration", command=self.run_config)
		self.run_button.pack(side=tk.LEFT, padx=5)

		self.close_button = ttk.Button(button_frame, text="Close", command=self.root.destroy)
		self.close_button.pack(side=tk.LEFT, padx=5)

	def load_config(self):
		default_path = r'C:\\Temp\\System2TesterRun.json'
		file_path = filedialog.askopenfilename(initialdir=default_path, defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
		if file_path:
			if not self.debug: self.s2t_flow.load_config(file_path)
			self.load_path_var.set(file_path)
			messagebox.showinfo("Info", f"Configuration loaded from {file_path}")

	def run_config(self):
		self.waiting_label.config(text="Running configuration... Please wait.")
		self.run_button.config(state=tk.DISABLED)
		self.close_button.config(state=tk.DISABLED)
		self.start_time = time.time()
		self.root.update_idletasks()  # Force UI update
		threading.Thread(target=self.run_config_thread, daemon=True).start()
		self.root.after(100, self.update_timer)

	def run_config_thread(self):
		self.s2t_flow.run_config()
		self.root.after(0, self.run_config_done)

	def run_config_done(self):
		self.waiting_label.config(text="")
		self.run_button.config(state=tk.NORMAL)
		self.close_button.config(state=tk.NORMAL)
		messagebox.showinfo("Info", "Configuration run successfully")

	def update_timer(self):
		elapsed_time = int(time.time() - self.start_time)
		self.waiting_label.config(text=f"Running configuration... Please wait. Time elapsed: {elapsed_time} seconds")
		self.root.update_idletasks()  # Force UI update
		if self.run_button['state'] == tk.DISABLED:
			self.root.after(1000, self.update_timer)

class QuickDefeatureTool:
	# Tunable expected boot times (in seconds)
	EXPECTED_TIME_FASTBOOT = 600   # 10 minutes
	EXPECTED_TIME_NORMAL = 1200    # 20 minutes
	
	# Test mode settings (shorter durations for testing)
	TEST_MODE_FASTBOOT = 30   # 30 seconds for fast testing
	TEST_MODE_NORMAL = 60     # 60 seconds for normal testing
	
	def __init__(self, root, s2t, mode='mesh', product='GNRAP', test_mode=False):
		self.root = root
		self.mode = mode
		self.product = product
		self.test_mode = test_mode  # Enable test mode for offline testing
		
		# Set window title based on mode
		title = "MESH Quick Defeature Tool" if mode == 'mesh' else "Slice Quick Defeature Tool"
		self.root.title(title)
		
		# Apply dark theme
		style = ttk.Style()
		available_themes = style.theme_names()
		# Try to use a darker theme if available
		if 'clam' in available_themes:
			style.theme_use('clam')
		elif 'alt' in available_themes:
			style.theme_use('alt')
		
		## S2T Class variables Call
		self.s2t = s2t
		self.features = s2t.features() if s2t != None else None
		self.variables = s2t.variables() if s2t != None else None
		self.core_type = s2t.core_type if s2t != None else 'bigcore'
		self.core_string = s2t.core_string if s2t != None else 'CORE'

		# Use domains instead of computes (works for computes, cbbs, etc.)
		self.domains = [d.capitalize() for d in s2t.domains] if s2t != None else ['Compute0', 'Compute1', 'Compute2']
		self.domain_type = s2t.domain_type if s2t != None else 'Compute'  # 'Compute' or 'CBB'
		
		self.validclass = s2t.validclass if s2t != None else []
		self.dis2cpm_valid = [v for k,v in s2t.dis2cpm_dict.items()] if s2t != None else []
		self.dis2cpm_options = ["None"] + self.dis2cpm_valid
		self.dis1cpm_valid = [v for k,v in s2t.dis1cpm_dict.items()] if s2t != None else []
		self.dis1cpm_options = ["None"] + self.dis1cpm_valid
		self.voltage_options = ["fixed", "vbump", "ppvc"]
		
		## Modes Configuration
		self.mesh_config_options = ["None"] + self.validclass + self.domains + ["RightSide", "LeftSide"]
		self.license_data = {v:k for k,v in self.s2t.license_dict.items() } if s2t != None else { 
			"Don't set license":0,"SSE/128":1,"AVX2/256 Light":2, "AVX2/256 Heavy":3, 
			"AVX3/512 Light":4, "AVX3/512 Heavy":5, "TMUL Light":6, "TMUL Heavy":7
		}
		
		self.enabledCores = []
		
		self.create_ui()
	
	def create_ui(self):
		"""Create simple UI with ttk widgets"""
		# Main container
		main_frame = ttk.Frame(self.root, padding="10")
		main_frame.grid(row=0, column=0, sticky="nsew")
		
		row = 0
		
		# Title
		title_text = f"{self.mode.upper()} Quick Defeature Tool - {self.product}"
		ttk.Label(main_frame, text=title_text, font=('Segoe UI', 11, 'bold')).grid(row=row, column=0, columnspan=2, pady=(0, 10), sticky="w")
		row += 1
		
		# Domain/Mask Configuration
		config_label_text = f"{self.domain_type} Configuration:" if self.mode == 'mesh' else f"Target Physical {self.core_string.capitalize()}:"
		ttk.Label(main_frame, text=config_label_text).grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.mesh_config_var = tk.StringVar(value="None")
		self.mesh_config_dropdown = ttk.Combobox(main_frame, textvariable=self.mesh_config_var, values=self.mesh_config_options)
		self.mesh_config_dropdown.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
		row += 1
		
		# License Level
		ttk.Label(main_frame, text="Core License:").grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.license_level_var = tk.StringVar(value="Don't set license")
		self.license_level_options = [k for k,v in self.license_data.items()]
		self.license_level_dropdown = ttk.Combobox(main_frame, textvariable=self.license_level_var, values=self.license_level_options)
		self.license_level_dropdown.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
		row += 1
		
		# Separator
		ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
		row += 1
		
		# Frequency Defeature
		ttk.Label(main_frame, text="Frequency Defeature:").grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.freq_defeature_var = tk.BooleanVar()
		self.freq_defeature_checkbox = ttk.Checkbutton(main_frame, variable=self.freq_defeature_var, command=self.toggle_frequency_fields)
		self.freq_defeature_checkbox.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
		row += 1
		
		# Flat Core Frequency
		ttk.Label(main_frame, text="Flat Core Frequency (100MHz):").grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.flat_core_freq_entry = ttk.Entry(main_frame)
		self.flat_core_freq_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
		self.flat_core_freq_entry.config(state='disabled')
		row += 1
		
		# Flat Mesh Frequency
		ttk.Label(main_frame, text="Flat Mesh Frequency (100MHz):").grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.flat_mesh_freq_entry = ttk.Entry(main_frame)
		self.flat_mesh_freq_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
		self.flat_mesh_freq_entry.config(state='disabled')
		row += 1
		
		# Separator
		ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
		row += 1
		
		# Voltage Defeature
		ttk.Label(main_frame, text="Voltage Defeature Mode:").grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.volt_defeature_var = tk.StringVar(value="None")
		self.volt_defeature_options = ["None", "vbump", "fixed", "ppvc"]
		self.volt_defeature_dropdown = ttk.Combobox(main_frame, textvariable=self.volt_defeature_var, values=self.volt_defeature_options)
		self.volt_defeature_dropdown.bind("<<ComboboxSelected>>", self.update_voltage_fields)
		self.volt_defeature_dropdown.grid(row=row, column=1, padx=10, pady=5, sticky="w")
		row += 1
		
		# Core vBumps
		self.core_vbumps_label = ttk.Label(main_frame, text="Core Voltage:")
		self.core_vbumps_label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.core_vbumps_entry = ttk.Entry(main_frame)
		self.core_vbumps_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
		self.core_vbumps_entry.config(state='disabled')
		row += 1
		
		# Mesh vBumps
		self.mesh_vbumps_label = ttk.Label(main_frame, text="Mesh Voltage:")
		self.mesh_vbumps_label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.mesh_vbumps_entry = ttk.Entry(main_frame)
		self.mesh_vbumps_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
		self.mesh_vbumps_entry.config(state='disabled')
		row += 1
		
		# Separator
		ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
		row += 1
		
		# ATE Registers
		reg_label_text = "ATE Registers Configuration:" if self.mode == 'slice' else "ATE Registers (Mesh Disabled):"
		ttk.Label(main_frame, text=reg_label_text).grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.registers_var = tk.BooleanVar()
		self.registers_checkbox = ttk.Checkbutton(main_frame, variable=self.registers_var, command=self.toggle_register_fields)
		self.registers_checkbox.grid(row=row, column=1, padx=10, pady=5, sticky="w")
		if self.mode == 'mesh':
			self.registers_checkbox.config(state=tk.DISABLED)
		row += 1
		
		# Registers Min
		ttk.Label(main_frame, text="ATE Regs Min (0x0):").grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.registers_min_entry = ttk.Entry(main_frame)
		self.registers_min_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
		self.registers_min_entry.config(state='disabled')
		row += 1
		
		# Registers Max
		ttk.Label(main_frame, text="ATE Regs Max (0xFFFF):").grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.registers_max_entry = ttk.Entry(main_frame)
		self.registers_max_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
		self.registers_max_entry.config(state='disabled')
		row += 1
		
		# Separator
		ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
		row += 1
		
		# Options
		self.fastboot_var = tk.BooleanVar(value=True)
		self.fastboot_checkbox = ttk.Checkbutton(main_frame, text="FastBoot", variable=self.fastboot_var, state='disabled')
		self.fastboot_checkbox.grid(row=row, column=0, padx=10, pady=5, sticky="w")
		
		self.reset_unit_var = tk.BooleanVar()
		self.reset_unit_checkbox = ttk.Checkbutton(main_frame, text="Reset Unit", variable=self.reset_unit_var)
		self.reset_unit_checkbox.grid(row=row, column=1, padx=10, pady=5, sticky="w")
		row += 1
		
		self.ht_disable_var = tk.BooleanVar()
		self.ht_disable_checkbox = ttk.Checkbutton(main_frame, text="HT Disable", variable=self.ht_disable_var)
		self.ht_disable_checkbox.grid(row=row, column=0, padx=10, pady=5, sticky="w")
		
		self.w600_var = tk.BooleanVar()
		self.w600_checkbox = ttk.Checkbutton(main_frame, text="600W Fuses", variable=self.w600_var, command=self.toggle_600w_fields)
		self.w600_checkbox.grid(row=row, column=1, padx=10, pady=5, sticky="w")
		row += 1
		
		# Disable 2 Cores per module (GNR/CWF)
		ttk.Label(main_frame, text="Disable 2C Module:").grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.dis_2CPM_var = tk.StringVar(value="None")
		self.dis_2CPM_dropdown = ttk.Combobox(main_frame, textvariable=self.dis_2CPM_var, values=self.dis2cpm_options)
		self.dis_2CPM_dropdown.grid(row=row, column=1, padx=10, pady=5, sticky="w")
		row += 1
		
		# Disable 1 Core per module (DMR)
		ttk.Label(main_frame, text="Disable 1C Module:").grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.dis_1CPM_var = tk.StringVar(value="None")
		self.dis_1CPM_dropdown = ttk.Combobox(main_frame, textvariable=self.dis_1CPM_var, values=self.dis1cpm_options)
		self.dis_1CPM_dropdown.grid(row=row, column=1, padx=10, pady=5, sticky="w")
		row += 1
		
		# Separator
		ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
		row += 1

		# Core Disable List
		ttk.Label(main_frame, text="Core Disable List:").grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.core_disable_var = tk.StringVar()
		self.core_disable_entry = ttk.Entry(main_frame, textvariable=self.core_disable_var, width=30)
		self.core_disable_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
		row += 1

		# Slice Disable List
		ttk.Label(main_frame, text="Slice Disable List:").grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.slice_disable_var = tk.StringVar()
		self.slice_disable_entry = ttk.Entry(main_frame, textvariable=self.slice_disable_var, width=30)
		self.slice_disable_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
		row += 1

		# Temperature SP
		ttk.Label(main_frame, text="Temperature SP (°C):").grid(row=row, column=0, padx=10, pady=5, sticky="w")
		self.temp_sp_var = tk.StringVar()
		self.temp_sp_entry = ttk.Entry(main_frame, textvariable=self.temp_sp_var, width=30)
		self.temp_sp_entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
		row += 1

		# External Fuse File
		ttk.Label(main_frame, text="External Fuse File (.fuse):").grid(row=row, column=0, padx=10, pady=5, sticky="w")
		fuse_file_frame = ttk.Frame(main_frame)
		fuse_file_frame.grid(row=row, column=1, padx=10, pady=5, sticky="w")
		self.fuse_file_var = tk.StringVar()
		self.fuse_file_entry = ttk.Entry(fuse_file_frame, textvariable=self.fuse_file_var, width=30, state='readonly')
		self.fuse_file_entry.pack(side=tk.LEFT, padx=(0, 5))
		self.fuse_file_browse_button = ttk.Button(fuse_file_frame, text="Browse", command=self.browse_fuse_file)
		self.fuse_file_browse_button.pack(side=tk.LEFT)
		row += 1

		# Separator
		ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
		row += 1

		# Action Buttons
		button_frame = ttk.Frame(main_frame)
		button_frame.grid(row=row, column=0, columnspan=2, pady=10)
		
		self.run_button = ttk.Button(button_frame, text="Run Configuration", command=self.run)
		self.run_button.pack(side=tk.LEFT, padx=5)
		
		self.cancel_button = ttk.Button(button_frame, text="Close", command=self.root.destroy)
		self.cancel_button.pack(side=tk.LEFT, padx=5)
		row += 1
		
		# Status Label
		self.waiting_label = ttk.Label(main_frame, text="", foreground="orange")
		self.waiting_label.grid(row=row, column=0, columnspan=2, pady=5)
		row += 1
		
		# Progress Bar
		self.progress_bar = ttk.Progressbar(main_frame, length=400, mode='determinate')
		self.progress_bar.grid(row=row, column=0, columnspan=2, pady=(0, 5), sticky="ew")
		self.progress_bar.grid_remove()  # Hidden by default
		
		# Progress info label (shows percentage and time remaining)
		self.progress_info_label = ttk.Label(main_frame, text="", font=('Segoe UI', 8))
		self.progress_info_label.grid(row=row+1, column=0, columnspan=2, pady=(0, 5))
		self.progress_info_label.grid_remove()  # Hidden by default
		
		# Initialize mode-specific settings
		if self.s2t != None:
			self.show_ate()
		self.modeselect()

		# Bind fastboot check
		self.mesh_config_var.trace_add("write", self.check_fastboot)

		if self.s2t != None:
			self.features_check()

	def corelist(self):
		cores = []
		for listkeys in self.s2t.array['CORES'].keys():
			cores.extend(self.s2t.array['CORES'][listkeys])
		
		self.enabledCores = cores

	def modeselect(self):

		if self.mode == 'mesh':
			self.registers_checkbox.config(state=tk.DISABLED)
			self.ht_disable_checkbox.config(state=tk.NORMAL)
			
			# Enable appropriate disable dropdown based on product
			# DMR uses dis_1CPM, GNR/CWF use dis_2CPM
			if 'DMR' in self.product.upper():
				self.dis_2CPM_dropdown.config(state=tk.DISABLED)
				self.dis_1CPM_dropdown.config(state=tk.NORMAL)
			else:
				self.dis_2CPM_dropdown.config(state=tk.NORMAL)
				self.dis_1CPM_dropdown.config(state=tk.DISABLED)

		if self.mode == 'slice':
			self.corelist()
			self.registers_checkbox.config(state=tk.NORMAL)
			self.mesh_config_dropdown.config(values=self.enabledCores)
			self.ht_disable_checkbox.config(state=tk.DISABLED)
			self.dis_2CPM_dropdown.config(state=tk.DISABLED)
			self.dis_1CPM_dropdown.config(state=tk.DISABLED)
		
		if self.s2t != None: 
			if not self.s2t.qdf600w:
				self.w600_checkbox.config(state=tk.DISABLED)

		self.check_fastboot()
		#if self.mesh_config_var.get() == 'None' or self.mode == 'slice':
		#	self.fastboot_checkbox.config(state='normal')

	def show_ate(self):
		print('--- ATE Frequency Configurations Available --- ')
		self.s2t.ate_data(mode=self.mode)
		print('--- ATE Safe Voltage Values --- ')
		print(self.s2t.voltstable)

	def toggle_frequency_fields(self):
		state = 'normal' if self.freq_defeature_var.get() else 'disabled'
		self.flat_core_freq_entry.config(state=state)
		self.flat_mesh_freq_entry.config(state=state)

	def browse_fuse_file(self):
		"""Open file dialog to select a .fuse file"""
		file_path = filedialog.askopenfilename(
			title="Select Fuse File",
			filetypes=[("Fuse Files", "*.fuse"), ("All Files", "*.*")],
			initialdir="C:/Temp"
		)
		if file_path:
			self.fuse_file_var.set(file_path)
			print(f"Selected fuse file: {file_path}")

	def toggle_600w_fields(self):
		if self.w600_var.get():
			self.fastboot_var.set(False)
			self.fastboot_checkbox.config(state='disabled')
		else:
			if self.mesh_config_var.get() == 'None': self.fastboot_checkbox.config(state='normal')
		
	def toggle_voltage_fields(self):
		state = 'normal' if self.volt_defeature_var.get() else 'disabled'
		self.core_vbumps_entry.config(state=state)
		self.mesh_vbumps_entry.config(state=state)

	def update_voltage_fields(self, event=None):
		selection = self.volt_defeature_var.get()
		self.voltage_text(selection=selection)

	def voltage_text(self, selection = 'vbump'):

		configs_core = {
					'GNR': {'vbump': "Core vBumps (-0.2V to 0.2V)",
             				'fixed': "Core Fixed Voltage",
                 			'ppvc': "Core PPVC Conditions"},
					'CWF': {'vbump': "Module vBumps (-0.2V to 0.2V)(+HDC)",
             				'fixed': "Module Fixed Voltage (+HDC)",
                 			'ppvc': "Module PPVC Conditions"},
					'DMR': {'vbump': "Module vBumps (-0.2V to 0.2V)(+MLC)",
             				'fixed': "Module Fixed Voltage (+MLC)",
				 			'ppvc': "Module PPVC Conditions"}
					}

		configs_mesh = {
					'GNR': {'vbump': "Mesh vBumps (-0.2V to 0.2V)(+HDC)",
             				'fixed': "Mesh Fixed Voltage (CFC/HDC)",
                 			'ppvc': "Mesh PPVC Conditions"},
					'CWF': {'vbump': "Mesh vBumps (-0.2V to 0.2V)",
             				'fixed': "Mesh Fixed Voltage",
                 			'ppvc': "Mesh PPVC Conditions"},
					'DMR': {'vbump': "Mesh vBumps (-0.2V to 0.2V)",
             				'fixed': "Mesh Fixed Voltage",
                 			'ppvc': "Mesh PPVC Conditions"}
					}
		selection_states = {'vbump': 'normal', 'fixed': 'normal', 'ppvc': 'disabled'}

		if self.product in configs_core and selection != 'None':

			self.core_vbumps_label.config(text=configs_core[self.product][selection])
			self.mesh_vbumps_label.config(text=configs_mesh[self.product][selection])
			self.core_vbumps_entry.config(state=selection_states[selection])
			self.mesh_vbumps_entry.config(state=selection_states[selection])
		else:
			self.core_vbumps_label.config(text="Core Voltage")
			self.mesh_vbumps_label.config(text="Mesh Voltage")
			self.core_vbumps_entry.config(state='disabled')
			self.mesh_vbumps_entry.config(state='disabled')

	def toggle_register_fields(self):
		
		if self.registers_var.get():
			state = 'normal'
			min_val = '0x0'
			max_val = '0xFFFF'
		else:
			state = 'disabled'
			min_val = '0xFFFF'
			max_val = '0xFFFF'   			
		
		self.registers_min_entry.config(state=state)
		self.registers_max_entry.config(state=state)

		self.registers_min_entry.delete(0, tk.END)
		self.registers_min_entry.insert(0, min_val)
		self.registers_max_entry.delete(0, tk.END)
		self.registers_max_entry.insert(0, max_val)

	def check_fastboot(self, *args):
		fastboot_enabled = self.features['fastboot']['enabled'] if self.s2t != None else False
		if ((self.mesh_config_var.get() == "None") or (self.mode == 'slice')) and fastboot_enabled:
			self.fastboot_var.set(True)
			self.fastboot_checkbox.config(state='normal')
		else:
			self.fastboot_var.set(False)
			self.fastboot_checkbox.config(state='disabled')

	def disablefields(self):

		self.run_button.config(state=tk.DISABLED)
		self.cancel_button.config(state=tk.DISABLED)
		self.mesh_config_dropdown.config(state=tk.DISABLED)
		self.license_level_dropdown.config(state=tk.DISABLED)
		self.freq_defeature_checkbox.config(state=tk.DISABLED)
		self.flat_core_freq_entry.config(state=tk.DISABLED)
		self.flat_mesh_freq_entry.config(state=tk.DISABLED)
		#self.volt_defeature_checkbox.config(state=tk.DISABLED)
		self.core_vbumps_entry.config(state=tk.DISABLED)
		self.mesh_vbumps_entry.config(state=tk.DISABLED)
		self.fastboot_checkbox.config(state=tk.DISABLED)
		self.reset_unit_checkbox.config(state=tk.DISABLED)
		self.ht_disable_checkbox.config(state=tk.DISABLED)
		self.registers_checkbox.config(state=tk.DISABLED)
		self.registers_max_entry.config(state=tk.DISABLED)
		self.registers_min_entry.config(state=tk.DISABLED)
		self.dis_2CPM_dropdown.config(state=tk.DISABLED)
		self.dis_1CPM_dropdown.config(state=tk.DISABLED)
		self.volt_defeature_dropdown.config(state=tk.DISABLED)
		self.fuse_file_browse_button.config(state=tk.DISABLED)
		self.core_disable_entry.config(state=tk.DISABLED)
		self.slice_disable_entry.config(state=tk.DISABLED)
		self.temp_sp_entry.config(state=tk.DISABLED)

		self.w600_checkbox.config(state=tk.DISABLED)
	
	def features_check(self):
		if self.features is None:
			return
			
		license_level = not self.features['license_level']['enabled']
		core_freq = not self.features['core_freq']['enabled']
		mesh_freq = not self.features['mesh_freq']['enabled']
		core_volt = not self.features['core_volt']['enabled']
		mesh_cfc_volt = not self.features['mesh_cfc_volt']['enabled'] # Using CFC only for now
		mesh_hdc_volt = not self.features['mesh_hdc_volt']['enabled']
		dis_ht = not self.features['dis_ht']['enabled']
		dis_2CPM = not self.features['dis_2CPM']['enabled']
		dis_1CPM = not self.features['dis_1CPM']['enabled']
		fastboot = not self.features['fastboot']['enabled']
		reg_select = not self.features['reg_select']['enabled']
		core_type = self.core_type # Might need this, for HTDIS / DIS2CPM/DIS1CPM disabling
		if license_level: self.license_level_dropdown.config(state=tk.DISABLED)
		if core_freq and mesh_freq: self.freq_defeature_checkbox.config(state=tk.DISABLED)
		if core_freq: self.flat_core_freq_entry.config(state=tk.DISABLED)
		if mesh_freq: self.flat_mesh_freq_entry.config(state=tk.DISABLED)
		#if core_volt and mesh_cfc_volt: self.volt_defeature_checkbox.config(state=tk.DISABLED)
		if core_volt and mesh_cfc_volt: self.volt_defeature_dropdown.config(state=tk.DISABLED)
		if core_volt: self.core_vbumps_entry.config(state=tk.DISABLED)
		if mesh_cfc_volt: self.mesh_vbumps_entry.config(state=tk.DISABLED)
		if fastboot:
			self.fastboot_checkbox.config(state=tk.DISABLED)
			self.fastboot_var.set(False)
		if dis_2CPM: self.dis_2CPM_dropdown.config(state=tk.DISABLED)
		if dis_1CPM: self.dis_1CPM_dropdown.config(state=tk.DISABLED)
		if dis_ht: self.ht_disable_checkbox.config(state=tk.DISABLED)
		if reg_select: self.registers_checkbox.config(state=tk.DISABLED)

	def validate_core_disable_options(self):
		"""Validate Core/Slice Disable List entries against the current system state.

		Returns True if validation passes (or user accepts warnings), False to block run.
		"""
		core_str = self.core_disable_var.get().strip()
		slice_str = self.slice_disable_var.get().strip()

		if not core_str and not slice_str:
			return True

		# Parse the lists
		try:
			core_disable_list = [int(x.strip()) for x in core_str.split(',') if x.strip()] if core_str else []
		except ValueError:
			messagebox.showerror("Input Error", "Core Disable List must be comma-separated integers (e.g. '62, 70')")
			return False

		try:
			slice_disable_list = [int(x.strip()) for x in slice_str.split(',') if x.strip()] if slice_str else []
		except ValueError:
			messagebox.showerror("Input Error", "Slice Disable List must be comma-separated integers (e.g. '60, 72')")
			return False

		active_list = slice_disable_list if slice_disable_list else core_disable_list
		is_slice_disable = bool(slice_disable_list)

		# Slice mode conflict: target core cannot be in the Slice Disable List
		if self.mode == 'slice' and is_slice_disable:
			try:
				target_core = int(self.mesh_config_var.get())
			except (ValueError, TypeError):
				target_core = None
			if target_core is not None and target_core in slice_disable_list:
				messagebox.showerror(
					"Configuration Error",
					f"Core {target_core} is selected as the slice target and is also in the Slice Disable List.\n"
					"A core cannot be both the test target and disabled. "
					"Please select a different target or remove it from the list."
				)
				return False

		# Check system state using the s2t array (enabled cores = not fuse-disabled)
		if self.s2t is not None:
			enabled_cores = []
			for compute_cores in self.s2t.array['CORES'].values():
				enabled_cores.extend(compute_cores)

			already_disabled = [c for c in active_list if c not in enabled_cores]
			report_lines = [f"{'Slice' if is_slice_disable else 'Core'} Disable Validation Report:"]
			for core in active_list:
				status = "ENABLED (will be disabled)" if core in enabled_cores else "ALREADY DISABLED in current system"
				report_lines.append(f"  Core {core}: {status}")

			if already_disabled:
				report_lines.append(f"\nWarning: {already_disabled} are already fuse-disabled in the current system.")
				proceed = messagebox.askokcancel(
					"Validation Warning",
					"\n".join(report_lines) + "\n\nProceed anyway?"
				)
				return proceed
			else:
				print("\n".join(report_lines))

		return True

	def run(self):
		# Run the S2T Quick option
		if not self.validate_core_disable_options():
			return
		options = self.get_options()
		options_str = "\n".join([f"{key}: {value}" for key, value in options.items()])
		confirm = messagebox.askokcancel("Confirm Configuration", f"Please confirm the following Test Configuration:\n\n{options_str}")

		if confirm:
			print("Confirmed options:\n")
			print(dict2table(options,["Configuration", "Value"]))
			self.updates2t(options)
			self.run_config()

		else:
			print("Test Configuration Cancelled")
	
	def run_config(self):
		self.waiting_label.config(text="Running Configuration..." + (" [TEST MODE]" if self.test_mode else ""))
		self.disablefields()
		
		# Determine expected time based on fastboot setting and test mode
		if self.test_mode:
			self.expected_time = self.TEST_MODE_FASTBOOT if self.fastboot_var.get() else self.TEST_MODE_NORMAL
		else:
			self.expected_time = self.EXPECTED_TIME_FASTBOOT if self.fastboot_var.get() else self.EXPECTED_TIME_NORMAL
		self.start_time = time.time()
		self.is_running = True  # Flag to track if config is running
		
		# Configure progress bar style BEFORE showing it
		style = ttk.Style()
		style.configure("green.Horizontal.TProgressbar", foreground='green', background='green')
		style.configure("red.Horizontal.TProgressbar", foreground='red', background='red')
		
		# Show progress bar and info label
		self.progress_bar['maximum'] = 100
		self.progress_bar['value'] = 0
		self.progress_bar.configure(style="green.Horizontal.TProgressbar")
		self.progress_bar.grid()
		self.progress_info_label.grid()
		
		# Force UI update to show initial state
		self.root.update_idletasks()
		
		threading.Thread(target=self.run_config_thread, daemon=True).start()
		# Schedule the first timer update to run in the UI thread
		self.root.after(1000, self.update_timer)

	def run_config_thread(self):
		# Test mode: simulate a run with sleep instead of actual execution
		if self.test_mode or self.s2t is None:
			print("=" * 60)
			print("TEST MODE: Simulating configuration run...")
			print(f"  Mode: {self.mode}")
			print(f"  FastBoot: {self.fastboot_var.get()}")
			print(f"  Expected Duration: {self.expected_time} seconds")
			print("=" * 60)
			
			# Sleep in small increments so we can see progress
			for i in range(int(self.expected_time)):
				time.sleep(1)
				if i % 5 == 0:
					print(f"  ... {i} seconds elapsed (progress: {(i/self.expected_time)*100:.1f}%)")
			
			print("=" * 60)
			print("TEST MODE: Configuration simulation complete!")
			print("=" * 60)
			self.root.after(0, self.run_config_done)
			return
		
		# Runs Init Flow again to reboot the unit
		if self.mode == "mesh":
			if self.s2t.reset_start:
				self.s2t.mesh_init()
			
			# Set Voltage configs
			self.s2t.set_voltage()

			# Reboots the unit with Configuration
			if not self.s2t.debug: self.s2t.mesh_run()

			# Saves Configuration
			self.s2t.save_config(file_path=self.s2t.defaultSave)
		if self.mode == "slice":
			if self.s2t.reset_start:
				self.s2t.slice_init()
			
			# Set Voltage configs
			self.s2t.set_voltage()

			# Reboots the unit with Configuration
			if not self.s2t.debug: self.s2t.slice_run()

			# Saves Configuration
			self.s2t.save_config(file_path=self.s2t.defaultSave)

		self.root.after(0, self.run_config_done)

	def run_config_done(self):
		self.is_running = False  # Stop the timer
		self.waiting_label.config(text="")
		self.run_button.config(state=tk.NORMAL)
		self.cancel_button.config(state=tk.NORMAL)
		
		# Hide progress bar and info label
		self.progress_bar.grid_remove()
		self.progress_info_label.grid_remove()
		
		messagebox.showinfo("Info", "Configuration run successfully")

	def update_timer(self):
		# Check if we should stop updating
		if not hasattr(self, 'is_running') or not self.is_running:
			return
			
		elapsed_time = int(time.time() - self.start_time)
		
		# Calculate progress percentage
		progress_percent = min(100, (elapsed_time / self.expected_time) * 100)
		
		# Debug output in test mode
		if self.test_mode:
			print(f"[Timer Update] Progress: {progress_percent:.1f}% | Elapsed: {elapsed_time}s/{self.expected_time}s | Bar: {self.progress_bar['value']:.1f}")
		
		# Update progress bar value - set it explicitly
		self.progress_bar['value'] = progress_percent
		
		# Change color to red if exceeding expected time
		if elapsed_time > self.expected_time:
			self.progress_bar.configure(style="red.Horizontal.TProgressbar")
			status_text = "⚠️ Taking longer than expected"
		else:
			time_remaining = self.expected_time - elapsed_time
			mins_remaining = time_remaining // 60
			secs_remaining = time_remaining % 60
			status_text = f"Est. time remaining: {mins_remaining}m {secs_remaining}s"
		
		# Update labels
		self.waiting_label.config(text=f"Running... Time elapsed: {elapsed_time // 60}m {elapsed_time % 60}s")
		self.progress_info_label.config(
			text=f"{progress_percent:.1f}% - {status_text}",
			foreground="red" if elapsed_time > self.expected_time else "blue"
		)
		
		# Force complete UI update to ensure progress bar redraws
		try:
			# This is the key - update the entire window to force redraw
			self.root.update_idletasks()
			# Also update the progress bar widget specifically
			self.progress_bar.update()
		except:
			pass  # In case window is closing
		
		# Keep updating while config is running
		if self.is_running:
			self.root.after(1000, self.update_timer)		
	
	def get_options(self):

		# Registers entry values
		registers_max_entry = self.int_format(self.registers_max_entry.get())
		registers_min_entry = self.int_format(self.registers_min_entry.get())

		options = {
			"Configuration": self.mesh_config_var.get(),
			"Frequency Defeature": self.freq_defeature_var.get(),
			"Flat Core Frequency": None if self.flat_core_freq_entry.get() == '' else int(self.flat_core_freq_entry.get(),0),
			"Flat Mesh Frequency": None if self.flat_mesh_freq_entry.get() == '' else int(self.flat_mesh_freq_entry.get(),0),
			"License Level":self.license_data[self.license_level_var.get()],
			"Voltage Defeature": self.volt_defeature_var.get(),
			"Core vBumps": None if self.core_vbumps_entry.get() == '' else float(self.core_vbumps_entry.get()),
			"Mesh vBumps": None if self.mesh_vbumps_entry.get() == '' else float(self.mesh_vbumps_entry.get()),
			"FastBoot": self.fastboot_var.get(),
			"Reset Unit": self.reset_unit_var.get(),
			"Fuse File": self.fuse_file_var.get() if self.fuse_file_var.get() else None,
			"HT Disable": self.ht_disable_var.get(),
			"600W Unit": self.w600_var.get(),
			"Disable 2C Module": self.dis_2CPM_var.get(),
			"Disable 1C Module": self.dis_1CPM_var.get(),
			"Registers Select": 2 if self.registers_var.get() else 1,
			"Registers Max": registers_max_entry,
			"Registers Min": registers_min_entry,
			"Core Disable List": self.core_disable_var.get().strip() or None,
			"Slice Disable List": self.slice_disable_var.get().strip() or None,
			"Temperature SP": None if self.temp_sp_var.get().strip() == '' else float(self.temp_sp_var.get().strip()),
		}
		return options

	def int_format(self, value, default = 0xFFF):
		if value is None:
			return default
		if value == '':
			return default
		
		if isinstance(value, str):
			return int(value, 0)
		
		return value
	
	def updates2t(self, options):
		# In test mode or when s2t is None, skip updating s2t attributes
		if self.test_mode or self.s2t is None:
			print("TEST MODE: Skipping S2T attribute updates")
			print(f"  Options configured: {list(options.keys())}")
			return

		core_freq = options["Flat Core Frequency"]
		mesh_freq = options["Flat Mesh Frequency"]
		vbump_core = options["Core vBumps"]
		vbump_mesh = options["Mesh vBumps"]
		dis_2CPM = options["Disable 2C Module"]
		dis_1CPM = options["Disable 1C Module"]
		Mask = options["Configuration"]
		vtype = options["Voltage Defeature"]
		 
		self.s2t.fastboot = options["FastBoot"]
		self.s2t.reset_start = options["Reset Unit"]
		self.s2t.dis_ht = options["HT Disable"]
		self.s2t.license_level = options["License Level"] if options["License Level"] != 0 else None
		self.s2t.cr_array_end = options["Registers Max"]
		self.s2t.cr_array_start = options["Registers Min"]
		self.s2t.reg_select = options["Registers Select"]
		self.s2t.u600w = options['600W Unit']
		self.s2t.external_fusefile = options['Fuse File']

		if dis_2CPM in self.dis2cpm_valid:
			self.s2t.dis_2CPM = dis_2CPM
		if dis_1CPM in self.dis1cpm_valid:
			self.s2t.dis_1CPM = dis_1CPM
		if core_freq != None:
			self.s2t.core_freq = core_freq
		if mesh_freq != None:
			self.s2t.mesh_freq = mesh_freq

		voltage_type_dict = {'None': 1, 'fixed' : 2, 'vbump' : 3, 'ppvc' : 4 }
		self.s2t.voltselect = voltage_type_dict[vtype]


		if self.mode == 'mesh':
			valid_configs = {v:k for k,v in self.s2t.ate_masks.items()}
			customs = {'LeftSide':self.s2t.left_hemispthere,'RightSide':self.s2t.right_hemispthere}
			domain_names = list(self.s2t.domains)  # Use domains instead of computes
			if vbump_core != None:
				print(f"Setting Core {vtype} to:", vbump_core)
				self.s2t.qvbumps_core = vbump_core
			if vbump_mesh != None:
				print(f"Setting Mesh {vtype} to:", vbump_mesh)
				self.s2t.qvbumps_mesh = vbump_mesh
			if Mask in valid_configs.keys():
				self.s2t.targetTile = 1
				self.s2t.target = Mask
				#self.s2t.fastboot = False
			elif any(dom == Mask.lower() for dom in domain_names): # Check against domain names
				self.s2t.targetTile = 2
				self.s2t.target = Mask.lower() 
				#self.s2t.fastboot = False
			elif Mask in customs.keys():
				self.s2t.targetTile = 3
				self.s2t.target = 'Custom'
				self.s2t.custom_list = customs[Mask]
				#self.s2t.fastboot = False
			else:
				self.s2t.targetTile = 4

		if self.mode == 'slice': ## Fixed for slice
			if vbump_core != None:
				#self.s2t.voltselect = 2
				self.s2t.qvbumps_core = vbump_core
			if vbump_mesh != None:
				#self.s2t.voltselect = 2
				self.s2t.qvbumps_mesh = vbump_mesh
			self.s2t.targetLogicalCore = int(Mask)

		# Core/Slice Disable List — generate extMask via CoreManipulation and pass through existing extMasks channel
		core_dis_str = options.get("Core Disable List")
		slice_dis_str = options.get("Slice Disable List")
		if core_dis_str:
			self.s2t.extMasks = self.s2t.build_disable_extmask(core_dis_str, 'core')
		elif slice_dis_str:
			self.s2t.extMasks = self.s2t.build_disable_extmask(slice_dis_str, 'slice')

		temp_sp = options.get("Temperature SP")
		if temp_sp is not None:
			try:
				from Tools import TemperatureControl as tc
				tc.set_temperature_sp(temp_sp)
			except Exception as e:
				print(f"Warning: Could not set Temperature SP: {e}")

		# Run Mesh
		#s2tTest.setupMeshMode()
	
def dict2table(dict, header = []):
	table = [header]
	for k,v in dict.items():
		table.append([k,v])
	data = tabulate(table, headers="firstrow", tablefmt="grid")
	return data

def config_ui(S2TFlow):
	root = tk.Tk()
	app = ConfigApp(root, S2TFlow)
	root.mainloop()

def mesh_ui(S2TFlow, product, test_mode=False):
	root = tk.Tk()
	app = QuickDefeatureTool(root, S2TFlow, mode='mesh', product=product, test_mode=test_mode)
	root.mainloop()

def slice_ui(S2TFlow, product, test_mode=False):
	root = tk.Tk()
	app = QuickDefeatureTool(root, S2TFlow, mode='slice', product=product, test_mode=test_mode)
	root.mainloop()

if __name__ == "__main__":
	# Test mode: Run without S2T connection to test UI timer and progress bar
	# Set test_mode=True to use shorter durations (30s/60s instead of 10min/20min)
	TEST_MODE = True  # Change to False for production use
	
	s2t = None  # No S2T object in test mode
	
	print("\n" + "=" * 60)
	if TEST_MODE:
		print("RUNNING IN TEST MODE")
		print("  - No S2T connection required")
		print("  - FastBoot: ~30 seconds")
		print("  - Normal Boot: ~60 seconds")
		print("  - Timer and progress bar will update every second")
	else:
		print("RUNNING IN PRODUCTION MODE (requires S2T connection)")
	print("=" * 60 + "\n")
	
	mesh_ui(s2t, 'GNR', test_mode=TEST_MODE)
	#root = tk.Tk()
	#app = QuickDefeatureTool(s2t, 'mesh', 'GNR')
	#root.mainloop()

#if __name__ == "__main__":
#    ## Dummy
#    S2Tflow = ''
#    root = tk.Tk()
#    app = ConfigApp(root, S2Tflow, debug = True)
#    root.mainloop()

#    root = tk.Tk()
#    app = S2TFlowUI(root)
#    root.mainloop()