import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
from tabulate import tabulate

# Modern color scheme
COLORS = {
	'bg_primary': '#2c3e50',      # Dark blue-gray
	'bg_secondary': '#34495e',    # Lighter blue-gray
	'bg_tertiary': '#ecf0f1',     # Light gray
	'accent': '#3498db',          # Blue
	'accent_hover': '#2980b9',    # Darker blue
	'success': '#27ae60',         # Green
	'warning': '#f39c12',         # Orange
	'danger': '#e74c3c',          # Red
	'text_dark': '#2c3e50',       # Dark text
	'text_light': '#ecf0f1',      # Light text
	'border': '#bdc3c7'           # Border gray
}

class ModernButton(tk.Button):
	"""Modern styled button with hover effects"""
	def __init__(self, parent, **kwargs):
		# Extract custom parameters
		bg_color = kwargs.pop('bg_color', COLORS['accent'])
		hover_color = kwargs.pop('hover_color', COLORS['accent_hover'])
		
		super().__init__(parent, 
						bg=bg_color,
						fg=COLORS['text_light'],
						font=('Segoe UI', 10, 'bold'),
						relief=tk.FLAT,
						borderwidth=0,
						padx=20,
						pady=10,
						cursor='hand2',
						**kwargs)
		
		self.bg_color = bg_color
		self.hover_color = hover_color
		
		self.bind('<Enter>', self._on_enter)
		self.bind('<Leave>', self._on_leave)
	
	def _on_enter(self, e):
		self['background'] = self.hover_color
	
	def _on_leave(self, e):
		self['background'] = self.bg_color

class ConfigApp:
	def __init__(self, root, S2TFlow, debug=False):
		self.root = root
		self.root.title("System 2 Tester Configuration")
		self.root.configure(bg=COLORS['bg_tertiary'])
		self.s2t_flow = S2TFlow
		self.debug = debug
		
		# Set minimum window size
		self.root.minsize(800, 400)
		
		self.create_widgets()

	def create_widgets(self):
		# Main container with padding
		main_frame = tk.Frame(self.root, bg=COLORS['bg_tertiary'])
		main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
		
		# Title
		title = tk.Label(main_frame, 
						text="System 2 Tester Configuration Manager",
						font=('Segoe UI', 16, 'bold'),
						bg=COLORS['bg_tertiary'],
						fg=COLORS['text_dark'])
		title.pack(pady=(0, 20))
		
		# Load Config Section
		load_frame = tk.Frame(main_frame, bg=COLORS['bg_tertiary'])
		load_frame.pack(fill=tk.X, pady=10)

		load_label = tk.Label(load_frame, 
							 text="Configuration File:",
							 font=('Segoe UI', 11),
							 bg=COLORS['bg_tertiary'],
							 fg=COLORS['text_dark'])
		load_label.pack(anchor=tk.W, pady=(0, 5))

		# Path entry and button frame
		path_frame = tk.Frame(load_frame, bg=COLORS['bg_tertiary'])
		path_frame.pack(fill=tk.X)
		
		self.load_path_var = tk.StringVar()
		self.load_path_entry = tk.Entry(path_frame, 
										textvariable=self.load_path_var,
										state='readonly',
										font=('Segoe UI', 10),
										relief=tk.FLAT,
										borderwidth=2)
		self.load_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)

		self.load_button = ModernButton(path_frame, text="Browse", command=self.load_config, width=12)
		self.load_button.pack(side=tk.LEFT, padx=(10, 0))

		# Status Label
		self.waiting_label = tk.Label(main_frame, 
									 text="",
									 font=('Segoe UI', 10, 'italic'),
									 bg=COLORS['bg_tertiary'],
									 fg=COLORS['warning'])
		self.waiting_label.pack(pady=20)

		# Action Buttons Frame
		button_frame = tk.Frame(main_frame, bg=COLORS['bg_tertiary'])
		button_frame.pack(pady=20)

		self.run_button = ModernButton(button_frame, 
									   text="Run Configuration",
									   command=self.run_config,
									   bg_color=COLORS['success'],
									   hover_color='#229954',
									   width=18)
		self.run_button.pack(side=tk.LEFT, padx=5)

		self.close_button = ModernButton(button_frame,
										 text="Close",
										 command=self.root.destroy,
										 bg_color=COLORS['danger'],
										 hover_color='#c0392b',
										 width=18)
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
		self.update_timer()
		threading.Thread(target=self.run_config_thread).start()

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
		if self.run_button['state'] == tk.DISABLED:
			self.root.after(1000, self.update_timer)

class QuickDefeatureTool:
	def __init__(self, root, s2t, mode='mesh', product='GNRAP'):
		self.root = root
		self.mode = mode
		self.product = product
		
		# Set window title based on mode
		title = "MESH Quick Defeature Tool" if mode == 'mesh' else "Slice Quick Defeature Tool"
		self.root.title(title)
		self.root.configure(bg=COLORS['bg_tertiary'])
		
		# Set minimum window size
		self.root.minsize(650, 850)
		
		## S2T Class variables Call
		self.s2t = s2t
		self.features = s2t.features() if s2t != None else None
		self.variables = s2t.variables() if s2t != None else None
		self.core_type = s2t.core_type if s2t != None else None
		
		# Use domains instead of computes (works for computes, cbbs, etc.)
		self.domains = [d.capitalize() for d in s2t.domains.keys()] if s2t != None else ['Compute0', 'Compute1', 'Compute2']
		self.domain_type = s2t.domain_type if s2t != None else 'Compute'  # 'Compute' or 'CBB'
		
		self.validclass = s2t.validclass if s2t != None else []
		self.dis2cpm_valid = [v for k,v in s2t.dis2cpm_dict.items()] if s2t != None else []
		self.dis2cpm_options = ["None"] + self.dis2cpm_valid
		self.voltage_options = ["fixed", "vbump", "ppvc"]
		
		## Modes Configuration
		self.mesh_config_options = ["None"] + self.validclass + self.domains + ["RightSide", "LeftSide"]
		self.license_data = {v:k for k,v in self.s2t.license_dict.items() } if s2t != None else { 
			"Don't set license":0,"SSE/128":1,"AVX2/256 Light":2, "AVX2/256 Heavy":3, 
			"AVX3/512 Light":4, "AVX3/512 Heavy":5, "TMUL Light":6, "TMUL Heavy":7
		}
		
		self.enabledCores = []
		
		self.create_modern_ui()
	
	def create_modern_ui(self):
		"""Create modern styled UI"""
		# Main container with scrollbar
		main_container = tk.Frame(self.root, bg=COLORS['bg_tertiary'])
		main_container.pack(fill=tk.BOTH, expand=True)
		
		# Canvas for scrolling
		canvas = tk.Canvas(main_container, bg=COLORS['bg_tertiary'], highlightthickness=0)
		scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
		scrollable_frame = tk.Frame(canvas, bg=COLORS['bg_tertiary'])
		
		scrollable_frame.bind(
			"<Configure>",
			lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
		)
		
		canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
		canvas.configure(yscrollcommand=scrollbar.set)
		
		canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
		scrollbar.pack(side="right", fill="y")
		
		# Title
		title_text = f"{self.mode.upper()} Quick Defeature Tool - {self.product}"
		title = tk.Label(scrollable_frame,
						text=title_text,
						font=('Segoe UI', 14, 'bold'),
						bg=COLORS['bg_tertiary'],
						fg=COLORS['text_dark'])
		title.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")
		
		row = 1
		
		# Configuration Section
		self.add_section_header(scrollable_frame, row, "Configuration")
		row += 1
		
		# Domain/Mask Configuration
		config_label_text = f"{self.domain_type} Configuration" if self.mode == 'mesh' else "Target Physical Core"
		self.mesh_config_label = self.add_label(scrollable_frame, row, config_label_text)
		
		self.mesh_config_var = tk.StringVar(value="None")
		self.mesh_config_dropdown = self.add_combobox(scrollable_frame, row, self.mesh_config_var, self.mesh_config_options)
		row += 1
		
		# License Level
		self.license_level_label = self.add_label(scrollable_frame, row, "Core License")
		self.license_level_var = tk.StringVar(value="Don't set license")
		self.license_level_options = [k for k,v in self.license_data.items()]
		self.license_level_dropdown = self.add_combobox(scrollable_frame, row, self.license_level_var, self.license_level_options)
		row += 1
		
		self.add_separator(scrollable_frame, row)
		row += 1
		
		# Frequency Section
		self.add_section_header(scrollable_frame, row, "Frequency Configuration")
		row += 1
		
		self.freq_defeature_label = self.add_label(scrollable_frame, row, "Enable Frequency Defeature")
		self.freq_defeature_var = tk.BooleanVar()
		self.freq_defeature_checkbox = self.add_checkbox(scrollable_frame, row, self.freq_defeature_var, self.toggle_frequency_fields)
		row += 1
		
		self.flat_core_freq_label = self.add_label(scrollable_frame, row, f"Flat {self.s2t.core_string if self.s2t else 'Core'} Frequency (MHz)")
		self.flat_core_freq_entry = self.add_entry(scrollable_frame, row, state='disabled')
		row += 1
		
		self.flat_mesh_freq_label = self.add_label(scrollable_frame, row, "Flat Mesh Frequency (MHz)")
		self.flat_mesh_freq_entry = self.add_entry(scrollable_frame, row, state='disabled')
		row += 1
		
		self.add_separator(scrollable_frame, row)
		row += 1
		
		# Voltage Section
		self.add_section_header(scrollable_frame, row, "Voltage Configuration")
		row += 1
		
		self.volt_defeature_label = self.add_label(scrollable_frame, row, "Voltage Defeature Mode")
		self.volt_defeature_var = tk.StringVar(value="None")
		self.volt_defeature_options = ["None", "vbump", "fixed", "ppvc"]
		self.volt_defeature_dropdown = self.add_combobox(scrollable_frame, row, self.volt_defeature_var, self.volt_defeature_options)
		self.volt_defeature_dropdown.bind("<<ComboboxSelected>>", self.update_voltage_fields)
		row += 1
		
		self.core_vbumps_label = self.add_label(scrollable_frame, row, "Core Voltage")
		self.core_vbumps_entry = self.add_entry(scrollable_frame, row, state='disabled')
		row += 1
		
		self.mesh_vbumps_label = self.add_label(scrollable_frame, row, "Mesh Voltage")
		self.mesh_vbumps_entry = self.add_entry(scrollable_frame, row, state='disabled')
		row += 1
		
		self.add_separator(scrollable_frame, row)
		row += 1
		
		# ATE Registers Section
		self.add_section_header(scrollable_frame, row, "ATE Registers")
		row += 1
		
		reg_label_text = "ATE Registers Configuration" if self.mode == 'slice' else "ATE Registers (Mesh Disabled)"
		self.registers_label = self.add_label(scrollable_frame, row, reg_label_text)
		self.registers_var = tk.BooleanVar()
		self.registers_checkbox = self.add_checkbox(scrollable_frame, row, self.registers_var, self.toggle_register_fields)
		if self.mode == 'mesh':
			self.registers_checkbox.config(state=tk.DISABLED)
		row += 1
		
		self.registers_min_label = self.add_label(scrollable_frame, row, "ATE Regs Min (0x0)")
		self.registers_min_entry = self.add_entry(scrollable_frame, row, state='disabled')
		row += 1
		
		self.registers_max_label = self.add_label(scrollable_frame, row, "ATE Regs Max (0xFFFF)")
		self.registers_max_entry = self.add_entry(scrollable_frame, row, state='disabled')
		row += 1
		
		self.add_separator(scrollable_frame, row)
		row += 1
		
		# Options Section
		self.add_section_header(scrollable_frame, row, "Options")
		row += 1
		
		# Row with two checkboxes
		option_frame = tk.Frame(scrollable_frame, bg=COLORS['bg_tertiary'])
		option_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
		
		self.fastboot_var = tk.BooleanVar(value=True)
		self.fastboot_checkbox = ttk.Checkbutton(option_frame, text="FastBoot", variable=self.fastboot_var)
		self.fastboot_checkbox.pack(side=tk.LEFT, padx=10)
		
		self.reset_unit_var = tk.BooleanVar()
		self.reset_unit_checkbox = ttk.Checkbutton(option_frame, text="Reset Unit", variable=self.reset_unit_var)
		self.reset_unit_checkbox.pack(side=tk.LEFT, padx=10)
		row += 1
		
		# Row with two more checkboxes
		option_frame2 = tk.Frame(scrollable_frame, bg=COLORS['bg_tertiary'])
		option_frame2.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
		
		self.ht_disable_var = tk.BooleanVar()
		self.ht_disable_checkbox = ttk.Checkbutton(option_frame2, text="HT Disable", variable=self.ht_disable_var)
		self.ht_disable_checkbox.pack(side=tk.LEFT, padx=10)
		if self.mode == 'slice':
			self.ht_disable_checkbox.config(state=tk.DISABLED)
		
		self.w600_var = tk.BooleanVar()
		self.w600_checkbox = ttk.Checkbutton(option_frame2, text="600W Fuses", variable=self.w600_var, command=self.toggle_600w_fields)
		self.w600_checkbox.pack(side=tk.LEFT, padx=10)
		row += 1
		
		# 2CPM disable
		self.dis_2CPM_config_label = self.add_label(scrollable_frame, row, "Cores Module to Disable")
		self.dis_2CPM_var = tk.StringVar(value="None")
		self.dis_2CPM_dropdown = self.add_combobox(scrollable_frame, row, self.dis_2CPM_var, self.dis2cpm_options)
		if self.mode == 'slice':
			self.dis_2CPM_dropdown.config(state=tk.DISABLED)
		row += 1
		
		self.add_separator(scrollable_frame, row)
		row += 1
		
		# Action Buttons
		button_frame = tk.Frame(scrollable_frame, bg=COLORS['bg_tertiary'])
		button_frame.grid(row=row, column=0, columnspan=2, pady=20)
		
		self.run_button = ModernButton(button_frame, 
									   text="Run Configuration",
									   command=self.run,
									   bg_color=COLORS['success'],
									   hover_color='#229954',
									   width=18)
		self.run_button.pack(side=tk.LEFT, padx=10)
		
		self.cancel_button = ModernButton(button_frame,
										  text="Close",
										  command=self.root.destroy,
										  bg_color=COLORS['danger'],
										  hover_color='#c0392b',
										  width=18)
		self.cancel_button.pack(side=tk.LEFT, padx=10)
		row += 1
		
		# Status Label
		self.waiting_label = tk.Label(scrollable_frame,
									 text="",
									 font=('Segoe UI', 10, 'italic'),
									 bg=COLORS['bg_tertiary'],
									 fg=COLORS['warning'])
		self.waiting_label.grid(row=row, column=0, columnspan=2, pady=10)
		
		# Initialize mode-specific settings
		if self.s2t != None:
			self.show_ate()
		self.modeselect()
		if self.s2t != None:
			self.features_check()
		
		# Bind fastboot check
		self.mesh_config_var.trace_add("write", self.check_fastboot)
	
	def add_section_header(self, parent, row, text):
		"""Add a section header"""
		header = tk.Label(parent,
						 text=text,
						 font=('Segoe UI', 12, 'bold'),
						 bg=COLORS['bg_tertiary'],
						 fg=COLORS['accent'])
		header.grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 5))
		return header
	
	def add_label(self, parent, row, text):
		"""Add a label"""
		label = tk.Label(parent,
						text=text,
						font=('Segoe UI', 10),
						bg=COLORS['bg_tertiary'],
						fg=COLORS['text_dark'])
		label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
		return label
	
	def add_combobox(self, parent, row, variable, values):
		"""Add a combobox"""
		combo = ttk.Combobox(parent, textvariable=variable, values=values, width=30)
		combo.grid(row=row, column=1, padx=10, pady=5, sticky="w")
		return combo
	
	def add_entry(self, parent, row, state='normal', width=30):
		"""Add an entry field"""
		entry = ttk.Entry(parent, width=width)
		entry.grid(row=row, column=1, padx=10, pady=5, sticky="w")
		if state != 'normal':
			entry.config(state=state)
		return entry
	
	def add_checkbox(self, parent, row, variable, command=None):
		"""Add a checkbox"""
		checkbox = ttk.Checkbutton(parent, variable=variable, command=command)
		checkbox.grid(row=row, column=1, padx=10, pady=5, sticky="w")
		return checkbox
	
	def add_separator(self, parent, row):
		"""Add a horizontal separator"""
		separator = ttk.Separator(parent, orient='horizontal')
		separator.grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)

	def corelist(self):
		cores = []
		for listkeys in self.s2t.array['CORES'].keys():
			cores.extend(self.s2t.array['CORES'][listkeys])
		
		self.enabledCores = cores

	def modeselect(self):
		if self.mode == 'slice':
			self.corelist()
			self.mesh_config_dropdown.config(values=self.enabledCores)
			
		if self.s2t != None: 
			if not self.s2t.qdf600w:
				self.w600_checkbox.config(state=tk.DISABLED)
		
		if self.mesh_config_var.get() == 'None' or self.mode == 'slice': 
			self.fastboot_checkbox.config(state='normal')
			
	def show_ate(self):
		print('--- ATE Frequency Configurations Available --- ')
		self.s2t.ate_data(mode=self.mode)
		print('--- ATE Safe Voltage Values --- ')
		print(self.s2t.voltstable)

	def toggle_frequency_fields(self):
		state = 'normal' if self.freq_defeature_var.get() else 'disabled'
		self.flat_core_freq_entry.config(state=state)
		self.flat_mesh_freq_entry.config(state=state)

	def toggle_600w_fields(self):
		if self.w600_var.get():
			self.fastboot_var.set(False)
			self.fastboot_checkbox.config(state='disabled')
		else:
			if self.mesh_config_var.get() == 'None': 
				self.fastboot_checkbox.config(state='normal')
		
	def toggle_voltage_fields(self):
		state = 'normal' if self.volt_defeature_var.get() else 'disabled'
		self.core_vbumps_entry.config(state=state)
		self.mesh_vbumps_entry.config(state=state)

	def update_voltage_fields(self, event=None):
		selection = self.volt_defeature_var.get()
		if selection == "None":
			self.core_vbumps_label.config(text="Core Voltage")
			self.mesh_vbumps_label.config(text="Mesh Voltage")
			self.core_vbumps_entry.config(state='disabled')
			self.mesh_vbumps_entry.config(state='disabled')
		elif selection == "vbump":
			self.core_vbumps_label.config(text= "Core vBumps (-0.2V to 0.2V)" if 'GNR' in self.product else "Core Fixed Voltage (+HDC)")
			self.mesh_vbumps_label.config(text= "Mesh vBumps (-0.2V to 0.2V)(+HDC)" if 'GNR' in self.product else "Mesh Fixed Voltage (CFC)")
			self.core_vbumps_entry.config(state='normal')
			self.mesh_vbumps_entry.config(state='normal')
		elif selection == "fixed":
			self.core_vbumps_label.config(text="Core Fixed Voltage" if 'GNR' in self.product else "Core vBumps (-0.2V to 0.2V)(+HDC)")
			self.mesh_vbumps_label.config(text="Mesh Fixed Voltage (CFC/HDC)" if 'GNR' in self.product else "Mesh vBumps (-0.2V to 0.2V)")
			self.core_vbumps_entry.config(state='normal')
			self.mesh_vbumps_entry.config(state='normal')
		elif selection == "ppvc":
			self.core_vbumps_label.config(text="Core PPVC Conditions")
			self.mesh_vbumps_label.config(text="Mesh PPVC Conditions")
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
		if (self.mesh_config_var.get() == "None") or self.mode == 'slice':
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
		self.core_vbumps_entry.config(state=tk.DISABLED)
		self.mesh_vbumps_entry.config(state=tk.DISABLED)
		self.fastboot_checkbox.config(state=tk.DISABLED)
		self.reset_unit_checkbox.config(state=tk.DISABLED)
		self.ht_disable_checkbox.config(state=tk.DISABLED)
		self.registers_checkbox.config(state=tk.DISABLED)
		self.registers_max_entry.config(state=tk.DISABLED)
		self.registers_min_entry.config(state=tk.DISABLED)
		self.dis_2CPM_dropdown.config(state=tk.DISABLED)
		self.volt_defeature_dropdown.config(state=tk.DISABLED)
		self.w600_checkbox.config(state=tk.DISABLED)
	
	def features_check(self):
		if self.features is None:
			return
			
		license_level = not self.features['license_level']['enabled']
		core_freq = not self.features['core_freq']['enabled']
		mesh_freq = not self.features['mesh_freq']['enabled']
		core_volt = not self.features['core_volt']['enabled']
		mesh_cfc_volt = not self.features['mesh_cfc_volt']['enabled']
		mesh_hdc_volt = not self.features['mesh_hdc_volt']['enabled']
		dis_ht = not self.features['dis_ht']['enabled']
		dis_2CPM = not self.features['dis_2CPM']['enabled']
		fastboot = not self.features['fastboot']['enabled']
		reg_select = not self.features['reg_select']['enabled']
		
		if license_level: self.license_level_dropdown.config(state=tk.DISABLED)
		if core_freq and mesh_freq: self.freq_defeature_checkbox.config(state=tk.DISABLED)
		if core_freq: self.flat_core_freq_entry.config(state=tk.DISABLED)
		if mesh_freq: self.flat_mesh_freq_entry.config(state=tk.DISABLED)
		if core_volt and mesh_cfc_volt: self.volt_defeature_dropdown.config(state=tk.DISABLED)
		if core_volt: self.core_vbumps_entry.config(state=tk.DISABLED)
		if mesh_cfc_volt: self.mesh_vbumps_entry.config(state=tk.DISABLED)
		if fastboot: self.fastboot_checkbox.config(state=tk.DISABLED)
		if dis_2CPM: self.dis_2CPM_dropdown.config(state=tk.DISABLED)
		if dis_ht: self.ht_disable_checkbox.config(state=tk.DISABLED)
		if reg_select: self.registers_checkbox.config(state=tk.DISABLED)

	def run(self):
		# Run the S2T Quick option
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
		self.waiting_label.config(text="Running Configuration...")
		self.disablefields()
		self.start_time = time.time()
		threading.Thread(target=self.run_config_thread).start()
		self.update_timer()

	def run_config_thread(self):
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
		self.waiting_label.config(text="")
		self.run_button.config(state=tk.NORMAL)
		self.cancel_button.config(state=tk.NORMAL)
		messagebox.showinfo("Info", "Configuration run successfully")

	def update_timer(self):
		elapsed_time = int(time.time() - self.start_time)
		self.waiting_label.config(text=f"Running... Please wait. Time: {elapsed_time} s")
		if self.run_button['state'] == tk.DISABLED:
			self.root.after(1000, self.update_timer)		
	
	def get_options(self):
		options = {
			"Configuration": self.mesh_config_var.get(),
			"Frequency Defeature": self.freq_defeature_var.get(),
			"Flat Core Frequency": None if self.flat_core_freq_entry.get() == '' else int(self.flat_core_freq_entry.get(),10),
			"Flat Mesh Frequency": None if self.flat_mesh_freq_entry.get() == '' else int(self.flat_mesh_freq_entry.get(),10),
			"License Level":self.license_data[self.license_level_var.get()],
			"Voltage Defeature": self.volt_defeature_var.get(),
			"Core vBumps": None if self.core_vbumps_entry.get() == '' else float(self.core_vbumps_entry.get()),
			"Mesh vBumps": None if self.mesh_vbumps_entry.get() == '' else float(self.mesh_vbumps_entry.get()),
			"FastBoot": self.fastboot_var.get(),
			"Reset Unit": self.reset_unit_var.get(),
			"HT Disable": self.ht_disable_var.get(),
			"600W Unit": self.w600_var.get(),
			"Disable 2C Module": self.dis_2CPM_var.get(),
			"Registers Select": 2 if self.registers_var.get() else 1,
			"Registers Max": 0xFFFF if not self.registers_var.get() else int(self.registers_max_entry.get(),16),
			"Registers Min": 0xFFFF if not self.registers_var.get() else int(self.registers_min_entry.get(),16),
		}
		return options

	def updates2t(self, options):
		core_freq = options["Flat Core Frequency"]
		mesh_freq = options["Flat Mesh Frequency"]
		vbump_core = options["Core vBumps"]
		vbump_mesh = options["Mesh vBumps"]
		dis_2CPM = options["Disable 2C Module"]
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
		
		if dis_2CPM in self.dis2cpm_valid:
			self.s2t.dis_2CPM = dis_2CPM
		if core_freq != None:
			self.s2t.core_freq = core_freq
		if mesh_freq != None:
			self.s2t.mesh_freq = mesh_freq

		voltage_type_dict = {'None': 1, 'fixed' : 2, 'vbump' : 3, 'ppvc' : 4 }
		self.s2t.voltselect = voltage_type_dict[vtype]

		if self.mode == 'mesh':
			valid_configs = {v:k for k,v in self.s2t.ate_masks.items()}
			customs = {'LeftSide':self.s2t.left_hemispthere,'RightSide':self.s2t.right_hemispthere}
			domain_names = list(self.s2t.domains.keys())  # Use domains instead of computes
			
			if vbump_core != None:
				self.s2t.qvbumps_core = vbump_core
			if vbump_mesh != None:
				self.s2t.qvbumps_mesh = vbump_mesh			
			if Mask in valid_configs.keys():
				self.s2t.targetTile = 1
				self.s2t.target = Mask
			elif any(dom == Mask.lower() for dom in domain_names):  # Check against domain names
				self.s2t.targetTile = 2
				self.s2t.target = Mask.lower() 
			elif Mask in customs.keys():
				self.s2t.targetTile = 3
				self.s2t.target = 'Custom'
				self.s2t.custom_list = customs[Mask]
			else:
				self.s2t.targetTile = 4

		if self.mode == 'slice':
			if vbump_core != None:
				self.s2t.qvbumps_core = vbump_core
			if vbump_mesh != None:
				self.s2t.qvbumps_mesh = vbump_mesh		
			self.s2t.targetLogicalCore = int(Mask)

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

def mesh_ui(S2TFlow, product):
	root = tk.Tk()
	app = QuickDefeatureTool(root, S2TFlow, mode='mesh', product=product)
	root.mainloop()

def slice_ui(S2TFlow, product):
	root = tk.Tk()
	app = QuickDefeatureTool(root, S2TFlow, mode='slice', product=product)
	root.mainloop()

if __name__ == "__main__":
	s2t = None
	mesh_ui(s2t, 'GNR')
