import os
import json
from tabulate import tabulate
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import Frameworkparser as fpa


class FrameworkReportBuilder:
	def __init__(self, root):
		self.root = root
		self.root.title("Framework Report Builder")
		
		# Enable full-screen resizing
		self.root.state('zoomed')  # Maximize window on Windows
		self.root.rowconfigure(0, weight=1)
		self.root.columnconfigure(0, weight=1)

		self.initial_df = None
		self.type_entries = {}
		self.content_entries = {}
		self.include_checks = {}
		self.custom_entries = {}
		self.comments_entries = {}
		self.skip_words_excel = ['Invalid']
		self.products = ['GNR', 'CWF']
		self.folders = []
		self.setup_ui()
		self.experiment_types = ["Baseline", "Loops", "Voltage", "Frequency", "Shmoo", "Invalid", "Others"]

		self.content_types = ["DBM", "Pseudo Slice", "Pseudo Mesh", "TSL", "Sandstone", "Imunch", "EFI", "Python", "Linux", "Other"]
		self.DATA_SERVER = r'\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\DebugFramework'

		## Content division for Failing Checks
		self.efi_content = ["DBM", "Pseudo Slice", "Pseudo Mesh", "EFI" ]
		self.linux_content = [ "TSL","Sandstone", "Linux"]
		self.python_content = ["Python"]

	def setup_ui(self):
		# Create main container with two columns
		main_container = tk.Frame(self.root)
		main_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
		main_container.rowconfigure(1, weight=1)
		main_container.columnconfigure(0, weight=3)  # Left side (experiments) - 75% width
		main_container.columnconfigure(1, weight=1)  # Right side (data management) - 25% width
		
		# ==================== LEFT PANEL: Selection and Experiments ====================
		left_panel = tk.Frame(main_container)
		left_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 5))
		left_panel.rowconfigure(1, weight=1)  # Make experiments section expandable
		left_panel.columnconfigure(0, weight=1)
		
		# Top section: Product, Visual ID, Save location
		top_frame = tk.LabelFrame(left_panel, text="Data Source & Output", padx=10, pady=10)
		top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
		
		tk.Label(top_frame, text="Product:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
		self.product_var = tk.StringVar(value='')
		self.product_combobox = ttk.Combobox(top_frame, textvariable=self.product_var, values=self.products, width=20)
		self.product_combobox.grid(row=0, column=1, padx=5, pady=5, sticky='w')
		self.product_combobox.bind("<<ComboboxSelected>>", self.update_visuals_combobox)

		tk.Label(top_frame, text="Visual ID:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
		self.visuals_var = tk.StringVar(value='')
		self.visuals_combobox = ttk.Combobox(top_frame, textvariable=self.visuals_var, values=self.folders, width=20)
		self.visuals_combobox.grid(row=1, column=1, padx=5, pady=5, sticky='w')

		tk.Label(top_frame, text="Save Folder:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
		self.save_entry = tk.Entry(top_frame, width=80)
		self.save_entry.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
		tk.Button(top_frame, text="Browse", command=self.browse_save_location).grid(row=2, column=2, padx=5, pady=5)
		
		top_frame.columnconfigure(1, weight=1)

		# Middle section: Experiments list with scrollbar - EXPANDABLE to fill available space
		exp_frame = tk.LabelFrame(left_panel, text="Experiments Configuration", padx=5, pady=5)
		exp_frame.grid(row=1, column=0, sticky="nsew", pady=5)
		exp_frame.rowconfigure(0, weight=1)
		exp_frame.columnconfigure(0, weight=1)
		
		self.scroll_frame = tk.Frame(exp_frame)
		self.scroll_frame.grid(row=0, column=0, sticky="nsew")
		self.scroll_frame.rowconfigure(0, weight=1)
		self.scroll_frame.columnconfigure(0, weight=1)

		self.canvas = tk.Canvas(self.scroll_frame)
		self.scrollbar_v = tk.Scrollbar(self.scroll_frame, orient="vertical", command=self.canvas.yview)
		self.scrollbar_h = tk.Scrollbar(self.scroll_frame, orient="horizontal", command=self.canvas.xview)
		self.experiment_frame = tk.Frame(self.canvas)

		self.experiment_frame.bind(
			"<Configure>",
			lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
		)

		self.canvas.create_window((0, 0), window=self.experiment_frame, anchor="nw")
		self.canvas.configure(yscrollcommand=self.scrollbar_v.set, xscrollcommand=self.scrollbar_h.set)

		self.canvas.grid(row=0, column=0, sticky="nsew")
		self.scrollbar_v.grid(row=0, column=1, sticky="ns")
		self.scrollbar_h.grid(row=1, column=0, sticky="ew")

		# Bottom section: Generate button - stays at bottom
		bottom_frame = tk.Frame(left_panel)
		bottom_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
		tk.Button(bottom_frame, text=" Generate Framework Files ", command=self.create_report, 
				 bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=20, pady=10).pack(fill="x")

		# ==================== RIGHT PANEL: Data Management ====================
		right_panel = tk.LabelFrame(main_container, text="Data Management", padx=10, pady=10)
		right_panel.grid(row=0, column=1, rowspan=2, sticky="nsew")
		
		# Parse Data section
		parse_section = tk.LabelFrame(right_panel, text="Parse Experiments", padx=10, pady=10)
		parse_section.pack(fill="x", pady=(0, 10))
		
		tk.Button(parse_section, text="Parse Data", command=self.parse_experiments, 
				 bg="#2196F3", fg="white", font=("Arial", 9, "bold"), pady=5).pack(fill="x", pady=(0, 5))
		
		btn_frame = tk.Frame(parse_section)
		btn_frame.pack(fill="x")
		self.select_all_button = tk.Button(btn_frame, text="Select All", command=self.select_all, state="disabled")
		self.select_all_button.pack(side="left", fill="x", expand=True, padx=(0, 2))
		self.remove_all_button = tk.Button(btn_frame, text="Deselect All", command=self.remove_all, state="disabled")
		self.remove_all_button.pack(side="right", fill="x", expand=True, padx=(2, 0))

		# Report Options section
		report_section = tk.LabelFrame(right_panel, text="Report Options", padx=10, pady=10)
		report_section.pack(fill="x", pady=(0, 10))
		
		self.merge_summary_var = tk.BooleanVar(value=True)
		self.generate_report_var = tk.BooleanVar(value=True)
		
		self.merge_summary_check = tk.Checkbutton(report_section, text="Merge Summary Files", 
												  variable=self.merge_summary_var, command=self.toggle_merge_entry)
		self.merge_summary_check.pack(anchor='w', pady=2)
		self.add_tooltip(self.merge_summary_check, "Merge all Excel summary files found")

		tk.Label(report_section, text="Merge Tag:").pack(anchor='w', pady=(5, 0))
		self.merge_file_entry = tk.Entry(report_section)
		self.merge_file_entry.pack(fill="x", pady=(0, 5))
		self.merge_file_entry.insert(0, "")
		self.add_tooltip(self.merge_file_entry, "Tag to be added to generated Framework merge file")

		self.generate_report_check = tk.Checkbutton(report_section, text="Generate Report", 
													variable=self.generate_report_var, command=self.toggle_report_entry)
		self.generate_report_check.pack(anchor='w', pady=2)
		self.add_tooltip(self.generate_report_check, "Create the summary report file")

		tk.Label(report_section, text="Report Tag:").pack(anchor='w', pady=(5, 0))
		self.report_file_entry = tk.Entry(report_section)
		self.report_file_entry.pack(fill="x", pady=(0, 5))
		self.report_file_entry.insert(0, "")
		self.add_tooltip(self.report_file_entry, "Tag to be added to generated Framework report file")

		# Data Collection section
		data_section = tk.LabelFrame(right_panel, text="Data Collection", padx=10, pady=10)
		data_section.pack(fill="x", pady=(0, 10))
		
		self.check_mca_data_var = tk.BooleanVar(value=False)
		self.check_mca_data_check = tk.Checkbutton(data_section, text="Check Logging Data", 
												   variable=self.check_mca_data_var, command=self.toggle_logging_entry)
		self.check_mca_data_check.pack(anchor='w', pady=2)
		self.add_tooltip(self.check_mca_data_check, "Look inside .zip file individual experiment logging to collect additional data")

		tk.Label(data_section, text="Skip Strings:").pack(anchor='w', pady=(5, 0))
		self.logging_entry = tk.Entry(data_section, state="disabled")
		self.logging_entry.pack(fill="x", pady=(0, 10))
		self.logging_entry.insert(0, "")
		self.add_tooltip(self.logging_entry, "Strings to be skipped during FAIL search. Comma separated")

		# Advanced sheets section
		self.generate_dragon_var = tk.BooleanVar(value=True)
		self.generate_core_var = tk.BooleanVar(value=True)
		self.generate_summary_tab_var = tk.BooleanVar(value=False)
		
		dragon_check = tk.Checkbutton(data_section, text="Generate DragonData Sheet", 
					  variable=self.generate_dragon_var)
		dragon_check.pack(anchor='w', pady=2)
		self.add_tooltip(dragon_check, "Generate DragonData sheet with VVAR analysis (requires Check Logging Data)")
		
		core_check = tk.Checkbutton(data_section, text="Generate CoreData Sheet", 
					  variable=self.generate_core_var)
		core_check.pack(anchor='w', pady=2)
		self.add_tooltip(core_check, "Generate CoreData sheet with voltage/VVAR/MCA data (requires Check Logging Data)")
		
		summary_check = tk.Checkbutton(data_section, text="Generate Summary Tab", 
					  variable=self.generate_summary_tab_var)
		summary_check.pack(anchor='w', pady=2)
		self.add_tooltip(summary_check, "Generate comprehensive experiment analysis summary (requires Check Logging Data)")
		
		self.generate_overview_var = tk.BooleanVar(value=True)
		overview_check = tk.Checkbutton(data_section, text="Generate Unit Overview", 
					  variable=self.generate_overview_var)
		overview_check.pack(anchor='w', pady=2)
		self.add_tooltip(overview_check, "Generate stakeholder presentation overview as first tab (requires 'Generate Summary Tab' to be enabled)")

	def update_visuals_combobox(self, event):
		directory_path = os.path.join(self.DATA_SERVER, self.product_var.get())
		

		try:
			# Get a list of all entries in the directory
			entries = os.listdir(directory_path)
			
			# Filter out entries that are directories
			folders = [entry for entry in entries if os.path.isdir(os.path.join(directory_path, entry))]
			
			self.folders = folders

		except Exception as e:
			print(f"An error occurred: {e}")
			self.folders = []
		
		self.visuals_var.set('')
		self.visuals_combobox['values'] = self.folders

	def add_tooltip(self, widget, text):
		tooltip = tk.Toplevel(widget, bg="yellow", padx=5, pady=5)
		tooltip.wm_overrideredirect(True)
		tooltip.withdraw()
		tk.Label(tooltip, text=text, bg="yellow").pack()

		def enter(event):
			x, y, _, _ = widget.bbox("insert")
			x += widget.winfo_rootx() + 25
			y += widget.winfo_rooty() + 20
			tooltip.wm_geometry(f"+{x}+{y}")
			tooltip.deiconify()

		def leave(event):
			tooltip.withdraw()

		widget.bind("<Enter>", enter)
		widget.bind("<Leave>", leave)

	def toggle_merge_entry(self):
		if self.merge_summary_var.get():
			self.merge_file_entry.config(state="normal")
		else:
			self.merge_file_entry.config(state="disabled")

	def toggle_report_entry(self):
		if self.generate_report_var.get():
			self.report_file_entry.config(state="normal")
		else:
			self.report_file_entry.config(state="disabled")

	def toggle_logging_entry(self):
		if self.check_mca_data_var.get():
			self.logging_entry.config(state="normal")
		else:
			self.logging_entry.config(state="disabled")

	def browse_folder(self):
		folder_path = filedialog.askdirectory()
		self.folder_entry.delete(0, tk.END)
		self.folder_entry.insert(0, folder_path)

	def browse_save_location(self):
		#file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
		file_path = filedialog.askdirectory()
		self.save_entry.delete(0, tk.END)
		self.save_entry.insert(0, file_path)

	def parse_experiments(self):
		#folder_path = self.folder_entry.get()
		folder_path = os.path.join(self.DATA_SERVER, self.product_var.get(), self.visuals_var.get())

		if not folder_path:
			messagebox.showerror("Error", "Please select a folder.")
			return

		self.initial_df = fpa.find_files(folder_path)

		# Load config if it exists
		config_path = os.path.join(folder_path, 'Config.json')
		if os.path.exists(config_path):
			with open(config_path, 'r') as config_file:
				config_data = json.load(config_file)
		else:
			config_data = {}

		for widget in self.experiment_frame.winfo_children():
			widget.destroy()

		tk.Label(self.experiment_frame, text=" Include ").grid(row=0, column=0, padx=5, pady=5)
		tk.Label(self.experiment_frame, text=" Experiment ").grid(row=0, column=1, padx=5, pady=5)
		tk.Label(self.experiment_frame, text=" Content ").grid(row=0, column=2, padx=5, pady=5)
		tk.Label(self.experiment_frame, text=" Type ").grid(row=0, column=3, padx=5, pady=5)
		tk.Label(self.experiment_frame, text=" Other Type ").grid(row=0, column=4, padx=5, pady=5)
		tk.Label(self.experiment_frame, text=" Comments ").grid(row=0, column=5, padx=5, pady=5, columnspan=3, sticky='ew')
		

		self.type_entries = {}
		self.include_checks = {}
		self.custom_entries = {}

		# Sort experiments by date (extract from folder name format: YYYYMMDD_HHMMSS_...)
		experiments = self.initial_df['Experiment'].unique()
		try:
			# Try to sort by date prefix in folder name
			sorted_experiments = sorted(experiments, key=lambda x: x.split('_')[0] if '_' in x else x)
		except:
			# If sorting fails, use original order
			sorted_experiments = experiments

		for idx, experiment in enumerate(sorted_experiments, start=1):
			include_var = tk.BooleanVar(value=config_data.get(experiment, {}).get('Include', True))
			include_check = tk.Checkbutton(self.experiment_frame, variable=include_var)
			include_check.grid(row=idx, column=0, padx=5, pady=5)
			self.include_checks[experiment] = include_var

			tk.Label(self.experiment_frame, text=experiment).grid(row=idx, column=1, padx=5, pady=5, sticky='w')

			content_var = tk.StringVar(value=config_data.get(experiment, {}).get('Content', ''))
			content_combobox = ttk.Combobox(self.experiment_frame, textvariable=content_var, values=self.content_types)
			content_combobox.grid(row=idx, column=2, padx=5, pady=5)
			#content_combobox.bind("<<ComboboxSelected>>", lambda e, var=content_var, exp=experiment: self.toggle_custom_type(var, exp))
			self.content_entries[experiment] = content_var

			type_var = tk.StringVar(value=config_data.get(experiment, {}).get('Type', ''))
			type_combobox = ttk.Combobox(self.experiment_frame, textvariable=type_var, values=self.experiment_types)
			type_combobox.grid(row=idx, column=3, padx=5, pady=5)
			type_combobox.bind("<<ComboboxSelected>>", lambda e, var=type_var, exp=experiment: self.toggle_custom_type(var, exp))
			self.type_entries[experiment] = type_var

			custom_type_entry = tk.Entry(self.experiment_frame)
			custom_type_entry.grid(row=idx, column=4, padx=5, pady=5)
			custom_type_entry.insert(0, config_data.get(experiment, {}).get('CustomType', ''))
			custom_type_entry.config(state="normal" if type_var.get() == "Others" else "disabled")
			self.custom_entries[experiment] = custom_type_entry

			comments_entry = tk.Entry(self.experiment_frame, width=55)
			comments_entry.grid(row=idx, column=5, padx=5, pady=5, columnspan=3, sticky='ew')
			comments_entry.insert(0, config_data.get(experiment, {}).get('Comments', ''))
			comments_entry.config(state="normal")
			self.comments_entries[experiment] = comments_entry


		# Enable the Select All and Remove All buttons
		self.select_all_button.config(state="normal")
		self.remove_all_button.config(state="normal")

	def toggle_custom_type(self, type_var, experiment):
		if type_var.get() == "Others":
			self.custom_entries[experiment].config(state="normal")
		else:
			self.custom_entries[experiment].config(state="disabled")

	def select_all(self):
		for var in self.include_checks.values():
			var.set(True)

	def remove_all(self):
		for var in self.include_checks.values():
			var.set(False)

	def create_report(self):
		
		generate_mergefiles = self.merge_summary_var.get()
		generate_report = self.generate_report_var.get()
		validate_loggingdata = self.check_mca_data_var.get()
		selected_product = self.product_var.get()
		tag_merge = f'_{self.merge_file_entry.get()}' if self.merge_file_entry.get() != '' else self.merge_file_entry.get()
		tag_report = f'_{self.report_file_entry.get()}' if self.report_file_entry.get() != '' else self.report_file_entry.get()
		skip_array = self.logging_entry.get().split(",") if self.logging_entry.get() != '' else []

		save_folder = self.save_entry.get()
		if not save_folder:
			messagebox.showerror("Error", "Please select a save location.")
			return

		visual_id = self.initial_df['VID'].unique()[0]
		save_path = os.path.join(save_folder, f'{visual_id}_FrameworkReport{tag_report}.xlsx')
		merged_path = os.path.join(save_folder, f'{visual_id}_MergedSummary{tag_merge}.xlsx')
		selected_experiments = [experiment for experiment, var in self.include_checks.items() if var.get()]
		filtered_df = self.initial_df[self.initial_df['Experiment'].isin(selected_experiments)]

		type_values = {}
		config_data = {}
		content_values = {}
		comments_values = {}
		
		for experiment in self.initial_df['Experiment'].unique():
			type_value = self.type_entries[experiment].get()
			custom_value = self.custom_entries[experiment].get() if type_value == "Others" else ''
			include_value = self.include_checks[experiment].get()
			content_value = self.content_entries[experiment].get()
			comments_value = self.comments_entries[experiment].get()
			if experiment in selected_experiments: 
				type_values[experiment] = custom_value if custom_value else type_value
				content_values[experiment] = content_value
				comments_values[experiment] = comments_value

			config_data[experiment] = {
				'Type': type_value,
				'CustomType': custom_value,
				'Include': include_value,
				'Content': content_value,
				'Comments': comments_value
			}

		# Save the config data to Config.json
		#folder_path = self.folder_entry.get()
		folder_path = os.path.join(self.DATA_SERVER, self.product_var.get(), self.visuals_var.get())
		config_path = os.path.join(folder_path, 'Config.json')
		with open(config_path, 'w') as config_file:
			json.dump(config_data, config_file, indent=4)


		log_path_dict = fpa.create_file_dict(filtered_df, 'Log', type_values, content_values, comments_values)
		excel_path_dict = fpa.create_file_dict(filtered_df, 'Excel', type_values, content_values)
		test_df = fpa.parse_log_files(log_path_dict)

		# Check ZIP Data
		fail_info_df = None
		unique_fails_df = None
		unique_mcas_df = None
		mca_df = None
		vvar_df = None
		core_data_df = None
		experiment_summary_df = None
		dr_df = None
		voltage_df = None
		metadata_df = None
		summary_df = None
		experiment_index_map = None
		
		generate_dragon = self.generate_dragon_var.get()
		generate_core = self.generate_core_var.get()
		
		if validate_loggingdata:
			zip_path_dict = fpa.create_file_dict(filtered_df, 'ZIP', type_values, content_values)
			fail_info_df = fpa.check_zip_data(zip_path_dict, skip_array, test_df)
			test_df = fpa.update_content_results(test_df, fail_info_df)
			unique_fails_df = fpa.generate_unique_fails(fail_info_df)

			# Parse MCA data using LogSummaryParser
			log_summary_parser = fpa.LogSummaryParser(excel_path_dict, test_df, selected_product)
			unique_mcas_df, mca_df = log_summary_parser.parse_mca_tabs_from_files()

			# Update test_df with MCA data
			test_df = fpa.update_mca_results(test_df, fail_info_df, mca_df)

			# Parse DebugFrameworkLogger data for DR registers, voltage/ratio data, and metadata
			# (only if DragonData or CoreData is requested)
			if generate_dragon or generate_core:
				try:
					logger_parser = fpa.DebugFrameworkLoggerParser(log_path_dict, product=selected_product)
					dr_df = logger_parser.parse_dr_data()
					voltage_df = logger_parser.parse_core_voltage_data()
					metadata_df = logger_parser.parse_experiment_metadata()
				except Exception as e:
					print(f"Warning: Could not parse DebugFrameworkLogger data: {e}")
					import traceback
					traceback.print_exc()
					dr_df = None
					voltage_df = None
					metadata_df = None

			# Create summary and experiment index map (needed for VVAR and CoreData parsing)
			summary_df, test_df, experiment_index_map = fpa.create_summary_df(test_df)

			# Parse VVAR data only if DragonData sheet is requested
			if generate_dragon and dr_df is not None and metadata_df is not None:
				try:
					vvar_df = fpa.parse_vvars_from_zip(zip_path_dict, test_df, product=selected_product, vvar_filter=['0x600D600D'], skip_array=skip_array, dr_df=dr_df, metadata_df=metadata_df, experiment_index_map=experiment_index_map)
				except Exception as e:
					print(f"Warning: Could not parse VVAR data: {e}")
					import traceback
					traceback.print_exc()
					vvar_df = None
			
			# Create comprehensive core data report only if CoreData sheet is requested
			if generate_core and voltage_df is not None:
				try:
					core_data_df = fpa.create_core_data_report(voltage_df, dr_df, vvar_df, mca_df, test_df, metadata_df, product=selected_product)
				except Exception as e:
					print(f"Warning: Could not create core data report: {e}")
					import traceback
					traceback.print_exc()
					core_data_df = None
		else:
			# If not validating logging data, still need to create summary
			summary_df, test_df, experiment_index_map = fpa.create_summary_df(test_df)

		# Generate experiment summary analysis if requested
		if validate_loggingdata and self.generate_summary_tab_var.get():
			try:
				print(' --> Generating Experiment Summary Analysis...')
				print(f'     test_df shape: {test_df.shape}, columns: {list(test_df.columns)[:5]}...')
				analyzer = fpa.ExperimentSummaryAnalyzer(test_df, summary_df, fail_info_df, vvar_df, mca_df, core_data_df)
				experiment_summary_df = analyzer.analyze_all_experiments()
				if experiment_summary_df is not None and not experiment_summary_df.empty:
					print(f' --> Experiment Summary generated successfully: {len(experiment_summary_df)} experiments')
				else:
					print(' --> Experiment Summary is empty (no valid experiments found)')
			except Exception as e:
				print(f"Warning: Could not generate experiment summary: {e}")
				import traceback
				traceback.print_exc()
				experiment_summary_df = None

		# Generate Unit Overview if requested (requires experiment_summary_df)
		overview_df = None
		if self.generate_overview_var.get() and experiment_summary_df is not None:
			try:
				print(' --> Generating Unit Overview...')
				from OverviewAnalyzer import OverviewAnalyzer
				overview_analyzer = OverviewAnalyzer(test_df, summary_df, experiment_summary_df, fail_info_df)
				overview_df = overview_analyzer.create_overview()
				if overview_df is not None and not overview_df.empty:
					print(f' --> Unit Overview generated successfully: {len(overview_df)} rows')
				else:
					print(' --> Unit Overview is empty')
			except Exception as e:
				print(f"Warning: Could not generate Unit Overview: {e}")
				import traceback
				traceback.print_exc()
				overview_df = None
		elif not self.generate_overview_var.get():
			print(' --> Unit Overview generation skipped (checkbox disabled)')
		elif experiment_summary_df is None:
			print(' --> Unit Overview generation skipped (experiment_summary_df is None)')
			print('     NOTE: Enable "Generate Summary Tab" to generate Overview')

		# Builds the Framework Report
		if generate_report: 
			print(' --> Building Framework Report Data File')
			fpa.save_to_excel(filtered_df, test_df, summary_df, fail_info_df, unique_fails_df, unique_mcas_df, vvar_df, core_data_df, experiment_summary_df, overview_df, filename=save_path)
		
		# Builds Merged MCA Data -- Mostly used to check data in Danta for multiple experiments
		if generate_mergefiles: 
			print(' --> Building Framework MCA Data Merged File')
			fpa.framework_merge(file_dict = excel_path_dict, output_file=merged_path, prefix = 'Summary', skip=self.skip_words_excel)

		messagebox.showinfo("Success", "Report created successfully.")

def test():
	path = r'R:\DebugFramework\GNR\75VP061900080'
	Excel_kw = 'Summary'
	zip_kw = 'ExperimentData'
	output_file = r'C:\ParsingFiles\DebugFramework\Framework_Report.xlsx'

	data = fpa.find_files(base_folder=path, excel_keyword=Excel_kw, zip_keyword=zip_kw)
	
	log_path_dict = fpa.create_file_dict(data, 'Log')
	excel_path_dict = fpa.create_file_dict(data, 'Excel')
	zip_path_dict = fpa.create_file_dict(data, 'ZIP')
	
	print('Excel Files', excel_path_dict , '\n')
	print('Zip Files', zip_path_dict , '\n')  
	print('Log Files', log_path_dict , '\n')  
	print('Data Files', data , '\n')

	# Parse log files and create test data DataFrame
	test_df = fpa.parse_log_files(log_path_dict)

	# Output results using tabulate
	print("\nTest Data DataFrame:")
	print(tabulate(test_df, headers='keys', tablefmt='grid'))
	
	# Save DataFrames to Excel
	fpa.save_to_excel(data, test_df, filename=output_file)

def test_UI():
	root = tk.Tk()
	app = FrameworkReportBuilder(root)
	root.mainloop()

if __name__ == "__main__":
	
	test_UI()