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
		tk.Label(self.root, text="Product:").grid(row=0, column=0, padx=5, pady=5)
		self.product_var = tk.StringVar(value='')
		self.product_combobox = ttk.Combobox(self.root, textvariable=self.product_var, values=self.products)
		self.product_combobox.grid(row=0, column=1, padx=5, pady=5, sticky='w')
		self.product_combobox.bind("<<ComboboxSelected>>", self.update_visuals_combobox)

		tk.Label(self.root, text="Visual ID:").grid(row=1, column=0, padx=5, pady=5)
		self.visuals_var = tk.StringVar(value='')
		self.visuals_combobox = ttk.Combobox(self.root, textvariable=self.visuals_var, values=self.folders)
		self.visuals_combobox.grid(row=1, column=1, padx=5, pady=5, sticky='w')

		#tk.Label(self.root, text="Selected Folder:").grid(row=0, column=0, padx=5, pady=5)
		#self.folder_entry = tk.Entry(self.root, width=160)
		#self.folder_entry.grid(row=0, column=1, padx=5, pady=5)
		#tk.Button(self.root, text=" Source Folder ", command=self.browse_folder).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

		tk.Label(self.root, text="Save Folder:").grid(row=2, column=0, padx=5, pady=5)
		self.save_entry = tk.Entry(self.root, width=160)
		self.save_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
		tk.Button(self.root, text=" Save Folder ", command=self.browse_save_location).grid(row=2, column=2, padx=5, pady=5, sticky="ew")

		# Create a frame with a border for checkboxes and entries
		self.options_frame = tk.Frame(self.root, borderwidth=2, relief="groove")
		self.options_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

		# Add checkboxes for additional options
		self.merge_summary_var = tk.BooleanVar(value=True)
		self.generate_report_var = tk.BooleanVar(value=True)
		self.check_mca_data_var = tk.BooleanVar(value=False)

		self.merge_summary_check = tk.Checkbutton(self.options_frame, text="Merge Summary Files", variable=self.merge_summary_var, command=self.toggle_merge_entry)
		self.merge_summary_check.grid(row=0, columnspan=2, column=0, padx=5, pady=5, sticky="w")
		self.add_tooltip(self.merge_summary_check, "If selected, will merge all Excel files found.")

		self.generate_report_check = tk.Checkbutton(self.options_frame, text="Generate Report", variable=self.generate_report_var, command=self.toggle_report_entry)
		self.generate_report_check.grid(row=0, columnspan=2, column=2, padx=5, pady=5, sticky="w")
		self.add_tooltip(self.generate_report_check, "If selected, will create the summary report file as well.")

		self.check_mca_data_check = tk.Checkbutton(self.options_frame, text="Check Logging Data", variable=self.check_mca_data_var, command=self.toggle_logging_entry)
		self.check_mca_data_check.grid(row=0, columnspan=2, column=4, padx=5, pady=5, sticky="w")
		self.add_tooltip(self.check_mca_data_check, "Will look inside .zip file individual experiment logging to collect additional data")

		# Add entries for file names below each checkbox
		tk.Label(self.options_frame, text="Merge Tag:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
		self.merge_file_entry = tk.Entry(self.options_frame, width=40)
		self.merge_file_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
		self.merge_file_entry.insert(0, "")
		self.merge_file_entry.config(state="normal")
		self.add_tooltip(self.merge_file_entry, "Tag to be added to generated Framework merge file.")

		tk.Label(self.options_frame, text="Report Tag:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
		self.report_file_entry = tk.Entry(self.options_frame, width=40)
		self.report_file_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")
		self.report_file_entry.insert(0, "")
		self.report_file_entry.config(state="normal")
		self.add_tooltip(self.report_file_entry, "Tag to be added to generated Framework report file.")

		tk.Label(self.options_frame, text="Skip Strings:").grid(row=1, column=4, padx=5, pady=5, sticky="w")
		self.logging_entry = tk.Entry(self.options_frame, width=40)
		self.logging_entry.grid(row=1, column=5, padx=5, pady=5, sticky="w")
		self.logging_entry.insert(0, "")
		self.logging_entry.config(state="disabled")
		self.add_tooltip(self.logging_entry, "Strings to be skipped during FAIL search inside individual logs. Comma split for multiple strings")

		# Buttons for Inside Parsed data box control
		tk.Button(self.root, text=" Parse Data ", command=self.parse_experiments).grid(row=4, column=0, padx=5, pady=5)
		self.select_all_button = tk.Button(self.root, text=" Select All ", command=self.select_all, state="disabled")
		self.select_all_button.grid(row=4, column=1, padx=5, pady=5)
		self.remove_all_button = tk.Button(self.root, text=" Remove All ", command=self.remove_all, state="disabled")
		self.remove_all_button.grid(row=4, column=2, padx=5, pady=5)


		# Create a frame for the experiment and type entries with a scrollbar
		self.scroll_frame = tk.Frame(self.root, borderwidth=1, relief="solid")
		self.scroll_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

		self.canvas = tk.Canvas(self.scroll_frame, width=1200, height=500)  # Increased width to fit custom entry
		self.scrollbar = tk.Scrollbar(self.scroll_frame, orient="vertical", command=self.canvas.yview)
		self.experiment_frame = tk.Frame(self.canvas)

		self.experiment_frame.bind(
			"<Configure>",
			lambda e: self.canvas.configure(
				scrollregion=self.canvas.bbox("all")
			)
		)

		self.canvas.create_window((0, 0), window=self.experiment_frame, anchor="nw")
		self.canvas.configure(yscrollcommand=self.scrollbar.set)

		self.canvas.pack(side="left", fill="both", expand=True)
		self.scrollbar.pack(side="right", fill="y")

		tk.Button(self.root, text=" Generate Framework Files ", command=self.create_report).grid(row=6, column=0, columnspan=3, padx=5, pady=5)

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

		for idx, experiment in enumerate(self.initial_df['Experiment'].unique(), start=1):
			include_var = tk.BooleanVar(value=config_data.get(experiment, {}).get('Include', True))
			include_check = tk.Checkbutton(self.experiment_frame, variable=include_var)
			include_check.grid(row=idx, column=0, padx=5, pady=5)
			self.include_checks[experiment] = include_var

			tk.Label(self.experiment_frame, text=experiment).grid(row=idx, column=1, padx=5, pady=5)

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

		summary_df = fpa.create_summary_df(test_df)


		# Builds the Framework Report
		if generate_report: 
			print(' --> Building Framework Report Data File')
			fpa.save_to_excel(filtered_df, test_df, summary_df, fail_info_df, unique_fails_df, unique_mcas_df, filename=save_path)
		
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