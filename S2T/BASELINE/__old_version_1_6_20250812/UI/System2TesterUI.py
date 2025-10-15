import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
from tabulate import tabulate



class ConfigApp:
	def __init__(self, root, S2TFlow, debug= False):
		self.root = root
		self.root.title("System 2 Tester Configuration")
		self.s2t_flow = S2TFlow
		self.debug = debug
		self.create_widgets()

	def create_widgets(self):
		# Frame for Load Config
		self.load_frame = tk.Frame(self.root)
		self.load_frame.pack(pady=10)

		# Load Config Button
		self.load_button = tk.Button(self.load_frame, text="Load Config", command=self.load_config)
		self.load_button.pack(side=tk.LEFT, padx=5)

		# Load Path Entry
		self.load_path_var = tk.StringVar()
		self.load_path_entry = tk.Entry(self.load_frame, textvariable=self.load_path_var, state='readonly', width=100)
		self.load_path_entry.pack(side=tk.LEFT, padx=5)

		# Run and Close Buttons Frame
		self.run_close_frame = tk.Frame(self.root)
		self.run_close_frame.pack(pady=10)

		# Run Config Button
		self.run_button = tk.Button(self.run_close_frame, text="Run Config", command=self.run_config)
		self.run_button.pack(side=tk.LEFT, padx=5)

		# Close Button
		self.close_button = tk.Button(self.run_close_frame, text="Close", command=self.root.destroy)
		self.close_button.pack(side=tk.LEFT, padx=5)
		# Waiting Label
		self.waiting_label = tk.Label(self.root, text="", fg="red")
		self.waiting_label.pack(pady=10)

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
	def __init__(self, root, s2t, mode = 'mesh', product = 'GNRAP'):
		self.root = root
		self.root.title("MESH Quick Defeature Tool" if mode == 'mesh' else "Slice Quick Defeature Tool")
		
		## S2T Class variables Call
		self.s2t = s2t
		self.features = s2t.features() if s2t != None else None
		self.variables = s2t.variables() if s2t != None else None
		self.core_type = s2t.core_type if s2t != None else None
		self.computes = [c.capitalize() for c in s2t.computes] if s2t != None else ['Compute0', 'Compute1', 'Compute2']
		self.validclass = s2t.validclass if s2t != None else []
		self.dis2cpm_valid = [v for k,v in s2t.dis2cpm_dict.items()] if s2t != None else []
		self.dis2cpm_options = ["None"] + self.dis2cpm_valid
		self.voltage_options = ["fixed", "vbump", "ppvc"]
		## Modes Configuration
		self.mesh_config_options = ["None"] + self.validclass + self.computes + ["RightSide", "LeftSide"]
		self.license_data = {v:k for k,v in self.s2t.license_dict.items() } if s2t != None else { "Don't set license":0,"SSE/128":1,"AVX2/256 Light":2, "AVX2/256 Heavy":3, "AVX3/512 Light":4, "AVX3/512 Heavy":5, "TMUL Light":6, "TMUL Heavy":7}
		self.mode = mode
		self.enabledCores = []
		self.product = product
		
		# Row 1: Dropdown List selection
		self.mesh_config_label = ttk.Label(root, text="Mesh Configuration")
		self.mesh_config_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
		
		self.mesh_config_var = tk.StringVar(value="None")
		
		# This will select the masking options based on product
		#if product == "GNRAP": self.mesh_config_options = ["None", "FirstPass", "SecondPass", "ThirdPass", "RowPass1", "RowPass2", "RowPass3", "RightSide", "LeftSide", "Compute0", "Compute1", "Compute2"]
		#elif product == "GNRSP": self.mesh_config_options = ["None", "FirstPass", "SecondPass","RowPass1", "RowPass2", "RightSide", "LeftSide", "Compute0", "Compute1"]
		#else: self.mesh_config_options = ["None", "RightSide", "LeftSide"]

		self.mesh_config_dropdown = ttk.Combobox(root, textvariable=self.mesh_config_var, values=self.mesh_config_options)
		self.mesh_config_dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="w")

		# Row 2: Dropdown List License Level
		self.license_level_label = ttk.Label(root, text="Core License")
		self.license_level_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

		self.license_level_var = tk.StringVar(value="Don't set license")
		self.license_level_options = [k for k,v in self.license_data.items()]
		self.license_level_dropdown = ttk.Combobox(root, textvariable=self.license_level_var, values=self.license_level_options)
		self.license_level_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="w")


		# Row 2: Separator Line
		self.add_separator(root, 2)

		# Row 3: Frequency Defeature Label with Checkbox
		self.freq_defeature_label = ttk.Label(root, text="Frequency Defeature")
		self.freq_defeature_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
		
		self.freq_defeature_var = tk.BooleanVar()
		self.freq_defeature_checkbox = ttk.Checkbutton(root, variable=self.freq_defeature_var, command=self.toggle_frequency_fields)
		self.freq_defeature_checkbox.grid(row=3, column=1, padx=10, pady=5, sticky="w")

		# Row 4: Flat Core Frequency Entry Field
		self.flat_core_freq_label = ttk.Label(root, text="Flat Core Frequency")
		self.flat_core_freq_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
		
		self.flat_core_freq_entry = ttk.Entry(root)
		self.flat_core_freq_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")
		self.flat_core_freq_entry.config(state='disabled')

		# Row 5: Flat Mesh Frequency Entry Field
		self.flat_mesh_freq_label = ttk.Label(root, text="Flat Mesh Frequency")
		self.flat_mesh_freq_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")
		
		self.flat_mesh_freq_entry = ttk.Entry(root)
		self.flat_mesh_freq_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")
		self.flat_mesh_freq_entry.config(state='disabled')

		# Row 6: Separator Line
		self.add_separator(root, 6)

		# Row 7: Voltage Defeature Label with Checkbox
		#self.volt_defeature_label = ttk.Label(root, text="Voltage Defeature")
		#self.volt_defeature_label.grid(row=7, column=0, padx=10, pady=5, sticky="w")

		# Row 7: Voltage Defeature Label with Dropdown
		self.volt_defeature_label = ttk.Label(root, text="Voltage Defeature")
		self.volt_defeature_label.grid(row=7, column=0, padx=10, pady=5, sticky="w")

		self.volt_defeature_var = tk.StringVar(value="None")
		self.volt_defeature_options = ["None", "vbump", "fixed", "ppvc"]
		self.volt_defeature_dropdown = ttk.Combobox(root, textvariable=self.volt_defeature_var, values=self.volt_defeature_options)
		self.volt_defeature_dropdown.grid(row=7, column=1, padx=10, pady=5, sticky="w")
		self.volt_defeature_dropdown.bind("<<ComboboxSelected>>", self.update_voltage_fields)


		#self.volt_defeature_var = tk.BooleanVar()
		#self.volt_defeature_checkbox = ttk.Checkbutton(root, variable=self.volt_defeature_var, command=self.toggle_voltage_fields)
		#self.volt_defeature_checkbox.grid(row=7, column=1, padx=10, pady=5, sticky="w")

		core_label = "Core Voltage" 
		mesh_label = "Mesh Voltage" 
		
		# Row 8: Core vBumps Entry Field
		self.core_vbumps_label = ttk.Label(root, text=core_label)
		self.core_vbumps_label.grid(row=8, column=0, padx=10, pady=5, sticky="w")
		
		self.core_vbumps_entry = ttk.Entry(root)
		self.core_vbumps_entry.grid(row=8, column=1, padx=10, pady=5, sticky="w")
		self.core_vbumps_entry.config(state='disabled')

		# Row 9: Mesh vBumps Entry Field
		self.mesh_vbumps_label = ttk.Label(root, text=mesh_label)
		self.mesh_vbumps_label.grid(row=9, column=0, padx=10, pady=5, sticky="w")
		
		self.mesh_vbumps_entry = ttk.Entry(root)
		self.mesh_vbumps_entry.grid(row=9, column=1, padx=10, pady=5, sticky="w")
		self.mesh_vbumps_entry.config(state='disabled')

		# Row 10: Separator Line
		self.add_separator(root, 10)

		# Row 11: Voltage Defeature Label with Checkbox
		self.registers_label = ttk.Label(root, text="ATE Registers Configuration")
		self.registers_label.grid(row=11, column=0, padx=10, pady=5, sticky="w")
		
		self.registers_var = tk.BooleanVar()
		self.registers_checkbox = ttk.Checkbutton(root, variable=self.registers_var, command=self.toggle_register_fields)
		self.registers_checkbox.grid(row=11, column=1, padx=10, pady=5, sticky="w")
		self.registers_checkbox.config(state=tk.NORMAL)

		# Row 12: Registers Min
		self.registers_min_label = ttk.Label(root, text="ATE Regs Min (Min=0)")
		self.registers_min_label.grid(row=12, column=0, padx=10, pady=5, sticky="w")
		
		self.registers_min_entry = ttk.Entry(root)
		self.registers_min_entry.grid(row=12, column=1, padx=10, pady=5, sticky="w")
		self.registers_min_entry.config(state='disabled')

		# Row 13: Registers Max
		self.registers_max_label = ttk.Label(root, text="ATE Regs Max (Max=65535)")
		self.registers_max_label.grid(row=13, column=0, padx=10, pady=5, sticky="w")
		
		self.registers_max_entry = ttk.Entry(root)
		self.registers_max_entry.grid(row=13, column=1, padx=10, pady=5, sticky="w")
		self.registers_max_entry.config(state='disabled')

		# Row 14: Separator Line
		self.add_separator(root, 14)

		# Row 15: FastBoot Checkbox
		self.fastboot_var = tk.BooleanVar(value=True)
		self.fastboot_checkbox = ttk.Checkbutton(root, text="FastBoot", variable=self.fastboot_var, state='disabled')
		self.fastboot_checkbox.grid(row=15, column=0, padx=10, pady=5, sticky="w")

		# Row 15: Reset Unit Checkbox
		self.reset_unit_var = tk.BooleanVar()
		self.reset_unit_checkbox = ttk.Checkbutton(root, text="Reset Unit", variable=self.reset_unit_var)
		self.reset_unit_checkbox.grid(row=15, column=1, padx=10, pady=5, sticky="w")

		# Row 16: HT Disable Checkbox
		self.ht_disable_var = tk.BooleanVar()
		self.ht_disable_checkbox = ttk.Checkbutton(root, text="HT Disable", variable=self.ht_disable_var)
		self.ht_disable_checkbox.grid(row=16, column=0, padx=10, pady=5, sticky="w")

		# Row 16: HT Disable Checkbox
		
		self.w600_var = tk.BooleanVar()
		self.w600_checkbox = ttk.Checkbutton(root, text="600W Fuses", variable=self.w600_var, command=self.toggle_600w_fields)
		self.w600_checkbox.grid(row=16, column=1, padx=10, pady=5, sticky="w")

		# Row 17: Disable 2 Cores per module
		self.dis_2CPM_config_label = ttk.Label(root, text="Cores Module to dis:")
		self.dis_2CPM_config_label.grid(row=17, column=0, padx=10, pady=5, sticky="w")
		
		self.dis_2CPM_var = tk.StringVar(value="None")
		self.dis_2CPM_dropdown = ttk.Combobox(self.root, textvariable=self.dis_2CPM_var, values=self.dis2cpm_options)
		self.dis_2CPM_dropdown.grid(row=17, column=1, padx=10, pady=5, sticky="w")

		# Row 17: Separator Line
		self.add_separator(root, 18)

		# Row 18: Run and Cancel Buttons
		self.run_button = tk.Button(root, text="  Run  ", command=self.run)
		self.run_button.grid(row=19, column=0, padx=10, pady=5, sticky="ew")

		self.cancel_button = tk.Button(root, text=" Close ", command=root.destroy)
		self.cancel_button.grid(row=19, column=1, padx=10, pady=5, sticky="ew")

		# Disable FastBoot if a selection other than None is made in Dropdown of Row 1
		#if self.mode == 'mesh':# and not self.s2t.qdf600w: 
		self.mesh_config_var.trace_add("write", self.check_fastboot)

		# Waiting Label
		self.waiting_label = tk.Label(self.root, text="", fg="red")
		self.waiting_label.grid(row=20, column=0, padx=10, pady=5, sticky="ew")

		if s2t != None: self.show_ate()
		self.modeselect()
		if s2t != None: self.features_check()

	def corelist(self):
		cores = []
		for listkeys in self.s2t.array['CORES'].keys():
			cores.extend(self.s2t.array['CORES'][listkeys])
		
		self.enabledCores = cores

	def modeselect(self):

		if self.mode == 'mesh':
			self.registers_checkbox.config(state=tk.DISABLED)
			self.registers_label.config(text="ATE Registers Configuration (Mesh Disabled)")
			self.mesh_config_label.config(text="Mesh Configuration")
			self.ht_disable_checkbox.config(state=tk.NORMAL)

		if self.mode == 'slice':
			self.corelist()
			self.registers_checkbox.config(state=tk.NORMAL)
			self.registers_label.config(text="ATE Registers Configuration")
			self.mesh_config_label.config(text="Target Physical Core")
			self.mesh_config_dropdown.config(values=self.enabledCores)
			self.ht_disable_checkbox.config(state=tk.DISABLED)
			self.dis_2CPM_dropdown.config(state=tk.DISABLED)
		
		if s2t != None: 
			if not self.s2t.qdf600w:
				self.w600_checkbox.config(state=tk.DISABLED)
		
		if self.mesh_config_var.get() == 'None' or self.mode == 'slice': 
			self.fastboot_checkbox.config(state='normal')
			
	def show_ate(self):
		print('--- ATE Frequency Configurations Available --- ')
		self.s2t.ate_data(mode=self.mode)
		print('--- ATE Safe Voltage Values --- ')
		print(self.s2t.voltstable)

	def add_separator(self, parent, row):
		separator = ttk.Separator(parent, orient='horizontal')
		separator.grid(row=row, columnspan=2, sticky="ew", pady=5)

	def toggle_frequency_fields(self):
		state = 'normal' if self.freq_defeature_var.get() else 'disabled'
		self.flat_core_freq_entry.config(state=state)
		self.flat_mesh_freq_entry.config(state=state)

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
			min = 0x0
			max = 0xFFFF
		
		else:
			state = 'disabled'
			min = 0xFFFF
			max = 0xFFFF   			
		
	
		self.registers_min_entry.config(state=state)
		self.registers_max_entry.config(state=state)

		self.registers_min_entry.delete(0, tk.END)
		self.registers_min_entry.insert(0, min)
		self.registers_max_entry.delete(0, tk.END)
		self.registers_max_entry.insert(0, max)

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
		self.volt_defeature_checkbox.config(state=tk.DISABLED)
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
		license_level = not self.features['license_level']['enabled']
		core_freq = not self.features['core_freq']['enabled']
		mesh_freq = not self.features['mesh_freq']['enabled']
		core_volt = not self.features['core_volt']['enabled']
		mesh_cfc_volt = not self.features['mesh_cfc_volt']['enabled'] # Using CFC only for now
		mesh_hdc_volt = not self.features['mesh_hdc_volt']['enabled']
		dis_ht = not self.features['dis_ht']['enabled']
		dis_2CPM = not self.features['dis_2CPM']['enabled']
		fastboot = not self.features['fastboot']['enabled']
		reg_select = not self.features['reg_select']['enabled']
		core_type = self.core_type # Might need this, for HTDIS / DIS2CPM disabling
		if license_level: self.license_level_dropdown.config(state=tk.DISABLED)
		if core_freq and mesh_freq: self.freq_defeature_checkbox.config(state=tk.DISABLED)
		if core_freq: self.flat_core_freq_entry.config(state=tk.DISABLED)
		if mesh_freq: self.flat_mesh_freq_entry.config(state=tk.DISABLED)
		if core_volt and mesh_cfc_volt: self.volt_defeature_checkbox.config(state=tk.DISABLED)
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
		#self.s2t.setupMeshMode()
		#self.run_config_done()
		
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
			"Registers Max": 0xFFFF if not self.registers_var.get() else int(self.registers_max_entry.get(),10),
			"Registers Min": 0xFFFF if not self.registers_var.get() else int(self.registers_min_entry.get(),10),
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
			computes = self.computes
			if vbump_core != None:
				#self.s2t.voltselect = 3
				self.s2t.qvbumps_core = vbump_core
			if vbump_mesh != None:
				#self.s2t.voltselect = 3
				self.s2t.qvbumps_mesh = vbump_mesh			
			if Mask in valid_configs.keys():
				self.s2t.targetTile = 1
				self.s2t.target = Mask
				#self.s2t.fastboot = False
			elif any(comp.lower() == Mask.lower() for comp in computes): # Assuring all of them are lower Case
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