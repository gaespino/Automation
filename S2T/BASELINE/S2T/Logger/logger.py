import http.client
import json
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import getpass
from datetime import datetime

# Lazy import to avoid circular dependency - import ErrorReport only when needed
dpmlog = None

# Define default values (will be overridden if ErrorReport imports successfully)
FRAMEWORK_VARS = {	'qdf':'',
		   		'tnum':'',
				'mask':'',
				'corelic':'',
				'bumps':'',
				'htdis':'',
				'dis2CPM':'',
				'freqIA':'',
				'voltIA':'',
				'freqCFC':'',
				'voltCFC':'',
				'content':'',
				'passstring':'',
				'failstring':'',
				'runName':'',
				'runStatus':'',
				'scratchpad':'',
				'seed':'',
				'ttlog':  None
				}
LICENSE_DICT = { 0:"Don't set license",1:"SSE/128",2:"AVX2/256 Light", 3:"AVX2/256 Heavy", 4:"AVX3/512 Light", 5:"AVX3/512 Heavy", 6:"TMUL Light", 7:"TMUL Heavy"}
FRAMEWORK_CORELIC = [f"{k}:{v}" for k,v in LICENSE_DICT.items()]
FRAMEWORK_VTYPES = ["VBUMP", "FIXED", "PPVC"]
FRAMEWORK_RUNSTATUS = ["PASS", "FAIL"]
FRAMEWORK_CONTENT = ["Dragon", "Linux", "PYSVConsole"]

def _lazy_import_dpmlog():
	"""Lazy import of ErrorReport module to avoid circular dependency"""
	global dpmlog, FRAMEWORK_VARS, LICENSE_DICT, FRAMEWORK_CORELIC, FRAMEWORK_VTYPES, FRAMEWORK_RUNSTATUS, FRAMEWORK_CONTENT
	
	if dpmlog is not None:
		return dpmlog
	
	try:
		import users.gaespino.dev.S2T.Logger.ErrorReport as dpmlog_module
		dpmlog = dpmlog_module
		FRAMEWORK_VARS = dpmlog.FRAMEWORK_VARS
		LICENSE_DICT = dpmlog.LICENSE_DICT
		FRAMEWORK_CORELIC = dpmlog.FRAMEWORK_CORELIC
		FRAMEWORK_VTYPES = dpmlog.FRAMEWORK_VTYPES
		FRAMEWORK_RUNSTATUS = dpmlog.FRAMEWORK_RUNSTATUS
		FRAMEWORK_CONTENT = dpmlog.FRAMEWORK_CONTENT
		return dpmlog
	except Exception as e:
		print(f'[-] -- Could not import Logger.ErrorReport -- {e}')
		return None

class loggerGUI:
	def __init__(self, root, qdf = '', ww='', product = 'GNRAP'):
		self.root = root
		self.root.title(f"{product} Error Logger")
		self.root.geometry("675x290")  # Set fixed size for the window
		self.root.resizable(False, False)  # Disable resizing
		self.product = product
		self.default_vars_dict = FRAMEWORK_VARS
		self.framework_lic_dict = LICENSE_DICT
		self.content = FRAMEWORK_CONTENT
		self.vtypes = FRAMEWORK_VTYPES
		self.corelic = FRAMEWORK_CORELIC
		self.runstatus = FRAMEWORK_RUNSTATUS


		# Configure column weights
		self.root.grid_columnconfigure(0, weight=1)
		self.root.grid_columnconfigure(1, weight=1)
		self.root.grid_columnconfigure(2, weight=1)
		self.root.grid_columnconfigure(3, weight=1)

		# Row 0 - Visual ID and QDF entry
		self.visual_label = tk.Label(root, text="Visual ID:")
		self.visual_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
		self.visual_entry = tk.Entry(root)
		self.visual_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

		self.qdf_label = tk.Label(root, text="QDF:")
		self.qdf_label.grid(row=0, column=1, padx=5, pady=5, sticky="e")
		self.qdf_entry = tk.Entry(root)
		self.qdf_entry.insert(0, qdf)
		self.qdf_entry.grid(row=0, column=2, padx=10, pady=5, sticky="w")

		# Row 1 - Bucket and WW entry
		self.bucket_label = tk.Label(root, text="Bucket:")
		self.bucket_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
		self.bucket_entry = tk.Entry(root)
		self.bucket_entry.insert(0, "UNCORE")
		self.bucket_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

		self.ww_label = tk.Label(root, text="WW:")
		self.ww_label.grid(row=1, column=1, padx=5, pady=5, sticky="e")
		self.ww_entry = tk.Entry(root)
		self.ww_entry.insert(0, ww)
		self.ww_entry.grid(row=1, column=2, padx=10, pady=5, sticky="w")

		# Row 2 - TestName Entry
		self.testname_label = tk.Label(root, text="Test Name:")
		self.testname_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
		self.testname_entry = tk.Entry(root)
		self.testname_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

		# Row 3 - TestNumber Entry
		self.testnumber_label = tk.Label(root, text="Test Number:\nDefault (1)")
		self.testnumber_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
		self.testnumber_entry = tk.Entry(root)
		self.testnumber_entry.insert(0, "1")
		self.testnumber_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")

		# Row 4 - Report Entry with the browse button
		self.report_label = tk.Label(root, text="Save Folder:")
		self.report_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
		self.report_entry = tk.Entry(root, width=75)
		self.report_entry.insert(0, r"C:/Temp")
		self.report_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew", columnspan=2)
		self.report_button = tk.Button(root, text=" Browse ", command=self.browse_report)
		self.report_button.grid(row=4, column=3, padx=5, pady=5)

		# Row 5 - Selection for CheckMCA and Debug MCA
		self.checkmem_var = tk.BooleanVar(value=False)
		self.checkmem_check = tk.Checkbutton(root, text="CheckMemory", variable=self.checkmem_var)
		self.checkmem_check.grid(row=5, column=0, columnspan=1, padx=5, pady=5)

		self.DebugMCA_var = tk.BooleanVar(value=False)
		self.DebugMCA_check = tk.Checkbutton(root, text="Debug MCA", variable=self.DebugMCA_var)
		self.DebugMCA_check.grid(row=5, column=1, columnspan=1, padx=5, pady=5)

		self.DRdump_var = tk.BooleanVar(value=False)
		self.DRdump_check = tk.Checkbutton(root, text="DRs Dump", variable=self.DRdump_var)
		self.DRdump_check.grid(row=5, column=2, columnspan=1, padx=5, pady=5)

		# Row 6 - Data options
		self.up_to_disk_var = tk.BooleanVar(value=False)
		self.up_to_disk_check = tk.Checkbutton(root, text="Upload to Disk", variable=self.up_to_disk_var, command=self.toggle_upload_frame)
		self.up_to_disk_check.grid(row=6, column=0, columnspan=1, padx=5, pady=5)

		self.up_to_danta_var = tk.BooleanVar(value=False)
		self.up_to_danta_check = tk.Checkbutton(root, text="Upload to Danta", variable=self.up_to_danta_var, command=self.toggle_upload_frame)
		self.up_to_danta_check.grid(row=6, column=1, columnspan=1, padx=5, pady=5)

		# Upload Frame
		self.upload_frame = tk.Frame(root)
		self.create_upload_frame()
		self.upload_frame.grid(row=7, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
		self.upload_frame.grid_remove()  # Initially hide the frame

		# Submit Button
		self.submit_button = tk.Button(root, text=" Run ", command=self.submit_form)
		self.submit_button.grid(row=8, column=1, padx=5, pady=10, sticky="ew")

		# Close Button
		self.close_button = tk.Button(root, text=" Close ", command=root.destroy)
		self.close_button.grid(row=8, column=0, padx=10, pady=10, sticky="ew")


	def browse_report(self):
		file_path = filedialog.askdirectory()
		self.report_entry.delete(0, tk.END)
		self.report_entry.insert(0, file_path)

	def toggle_upload_frame(self):
		if self.up_to_disk_var.get() or self.up_to_danta_var.get():
			self.upload_frame.grid()
			self.root.geometry("675x625")
		else:
			self.upload_frame.grid_remove()
			self.root.geometry("675x290")

	def create_upload_frame(self):
		# Separator Line
		separator = ttk.Separator(self.upload_frame, orient='horizontal')
		separator.grid(row=0, column=0, columnspan=5, sticky="ew", pady=5)
		separator_label = tk.Label(self.upload_frame, text="Framework Required Data", font=("Arial", 10, "bold"))
		separator_label.grid(row=1, column=0, columnspan=5, pady=5)

		# Content
		self.content_label = tk.Label(self.upload_frame, text="Content:")
		self.content_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
		self.content_var = tk.StringVar()
		self.content_options = self.content
		self.content_menu = ttk.Combobox(self.upload_frame, textvariable=self.content_var, values=self.content_options)
		self.content_menu.grid(row=2, column=1, padx=5, pady=5, sticky="w")

		# Mask
		self.mask_label = tk.Label(self.upload_frame, text="Mask:")
		self.mask_label.grid(row=2, column=2, padx=5, pady=5, sticky="w")
		self.mask_entry = tk.Entry(self.upload_frame)
		self.mask_entry.grid(row=2, column=3, padx=5, pady=5, sticky="w")

		# Corelic
		self.corelic_label = tk.Label(self.upload_frame, text="Corelic:")
		self.corelic_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
		self.corelic_var = tk.StringVar()
		self.corelic_options = self.corelic
		self.corelic_menu = ttk.Combobox(self.upload_frame, textvariable=self.corelic_var, values=self.corelic_options)
		self.corelic_menu.grid(row=3, column=1, padx=5, pady=5, sticky="w")

		# Bumps
		self.bumps_label = tk.Label(self.upload_frame, text="Bumps:")
		self.bumps_label.grid(row=3, column=2, padx=5, pady=5, sticky="w")
		self.bumps_var = tk.StringVar()
		self.bumps_options = self.vtypes
		self.bumps_menu = ttk.Combobox(self.upload_frame, textvariable=self.bumps_var, values=self.bumps_options)
		self.bumps_menu.grid(row=3, column=3, padx=5, pady=5, sticky="w")

		# Frequency and Voltage Entries
		self.freqia_label = tk.Label(self.upload_frame, text="Freq IA:")
		self.freqia_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
		self.freqia_entry = tk.Entry(self.upload_frame)
		self.freqia_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")

		self.freqcfc_label = tk.Label(self.upload_frame, text="Freq CFC:")
		self.freqcfc_label.grid(row=4, column=2, padx=5, pady=5, sticky="w")
		self.freqcfc_entry = tk.Entry(self.upload_frame)
		self.freqcfc_entry.grid(row=4, column=3, padx=5, pady=5, sticky="w")

		self.voltia_label = tk.Label(self.upload_frame, text="Volt IA:")
		self.voltia_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")
		self.voltia_entry = tk.Entry(self.upload_frame)
		self.voltia_entry.grid(row=5, column=1, padx=5, pady=5, sticky="w")

		self.voltcfc_label = tk.Label(self.upload_frame, text="Volt CFC:")
		self.voltcfc_label.grid(row=5, column=2, padx=5, pady=5, sticky="w")
		self.voltcfc_entry = tk.Entry(self.upload_frame)
		self.voltcfc_entry.grid(row=5, column=3, padx=5, pady=5, sticky="w")

		# Pass and Fail Strings
		self.passstring_label = tk.Label(self.upload_frame, text="Pass String:")
		self.passstring_label.grid(row=6, column=0, padx=5, pady=5, sticky="w")
		self.passstring_entry = tk.Entry(self.upload_frame)
		self.passstring_entry.insert(0, "Test Complete")
		self.passstring_entry.grid(row=6, column=1, padx=5, pady=5, sticky="w")

		self.failstring_label = tk.Label(self.upload_frame, text="Fail String:")
		self.failstring_label.grid(row=6, column=2, padx=5, pady=5, sticky="w")
		self.failstring_entry = tk.Entry(self.upload_frame)
		self.failstring_entry.insert(0, "Test Failed")
		self.failstring_entry.grid(row=6, column=3, padx=5, pady=5, sticky="w")

		# Run Status
		self.runstatus_label = tk.Label(self.upload_frame, text="Run Status:")
		self.runstatus_label.grid(row=7, column=0, padx=5, pady=5, sticky="w")
		self.runstatus_var = tk.StringVar()
		self.runstatus_options = self.runstatus
		self.runstatus_menu = ttk.Combobox(self.upload_frame, textvariable=self.runstatus_var, values=self.runstatus_options)
		self.runstatus_menu.grid(row=7, column=1, padx=5, pady=5, sticky="w")

		# Seed
		self.seed_label = tk.Label(self.upload_frame, text="Fail Content:")
		self.seed_label.grid(row=8, column=0, padx=5, pady=5, sticky="w")
		self.seed_entry = tk.Entry(self.upload_frame, width=75)
		self.seed_entry.grid(row=8, column=1, padx=5, pady=5, sticky="ew", columnspan=3)

		# TTLog
		self.ttlog_label = tk.Label(self.upload_frame, text="Serial Log:")
		self.ttlog_label.grid(row=9, column=0, padx=5, pady=5, sticky="w")
		self.ttlog_entry = tk.Entry(self.upload_frame, width=75)
		self.ttlog_entry.grid(row=9, column=1, padx=5, pady=5, sticky="ew", columnspan=3)
		self.ttlog_button = tk.Button(self.upload_frame, text=" Browse ", command=self.browse_ttlog)
		self.ttlog_button.grid(row=9, column=4, padx=5, pady=5, sticky="w")

		last_separator = ttk.Separator(self.upload_frame, orient='horizontal')
		last_separator.grid(row=10, column=0, columnspan=5, sticky="ew", pady=5)

	def browse_ttlog(self):
		file_path = filedialog.askopenfilename()
		self.ttlog_entry.delete(0, tk.END)
		self.ttlog_entry.insert(0, file_path)

	def validate_fields(self):
		# Check if any field in the upload frame is empty
		required_fields = [
			self.content_var.get(),
			self.mask_entry.get(),
			#self.corelic_var.get(),
			self.bumps_var.get(),
			#self.freqia_entry.get(),
			#self.freqcfc_entry.get(),
			#self.voltia_entry.get(),
			#self.voltcfc_entry.get(),
			self.passstring_entry.get(),
			self.failstring_entry.get(),
			self.runstatus_var.get(),
			#self.seed_entry.get(),
			#self.ttlog_entry.get()
		]
		return all(required_fields)

	def check_value(self, var, exclude_if = [None, 'None',''], default=None):
		new_var = var.get() if var.get() not in exclude_if else default
		return new_var

	# Function to handle the submission of the form
	def submit_form(self):

		if (self.up_to_disk_var.get() or self.up_to_danta_var.get()) and not self.validate_fields():
			messagebox.showerror("Error", "All fields must be filled when upload is selected.")
			return

		visual = self.visual_entry.get()
		Testnumber = self.testnumber_entry.get()
		TestName = self.testname_entry.get()
		checkmem = self.checkmem_var.get()
		debugmca = self.DebugMCA_var.get()
		drdump = self.DRdump_var.get()
		reportfolder = self.report_entry.get()
		qdf = self.qdf_entry.get()
		ww = self.ww_entry.get()
		bucket = self.bucket_entry.get()
		product = self.product
		upload_to_danta = self.up_to_danta_var.get()
		upload_to_disk = self.up_to_disk_var.get()

		# Collect additional data if upload options are selected
		if upload_to_disk or upload_to_danta:
			self.default_vars_dict['qdf'] = self.qdf_entry.get()
			self.default_vars_dict['tnum'] = self.testnumber_entry.get()
			self.default_vars_dict['runName'] = self.testname_entry.get()
			self.default_vars_dict['content'] = self.content_var.get()
			self.default_vars_dict['mask'] = self.check_value(self.mask_entry.get(),default='NotDefined')
			self.default_vars_dict['corelic'] = int(self.corelic_var.get().split(":")[0]) if self.corelic_var.get() != None else None
			self.default_vars_dict['bumps'] = self.bumps_var.get()
			self.default_vars_dict['freqIA'] = self.check_value(self.freqia_entry)
			self.default_vars_dict['freqCFC'] = self.check_value(self.freqcfc_entry)
			self.default_vars_dict['voltIA'] = self.check_value(self.voltia_entry)
			self.default_vars_dict['voltCFC'] = self.check_value(self.voltcfc_entry)
			self.default_vars_dict['passstring'] = self.check_value(self.passstring_entry.get(), default='NotDefined')
			self.default_vars_dict['failstring'] = self.check_value(self.failstring_entry.get(), default='NotDefined')
			self.default_vars_dict['runStatus'] = self.runstatus_var.get()
			self.default_vars_dict['seed'] = self.check_value(self.seed_entry)
			self.default_vars_dict['ttlog'] = self.check_value(self.ttlog_entry)
			framework_data = self.default_vars_dict
		else:
			framework_data = None

		print("Creating System Log with the following configuration")
		print(f"\tVisual ID: {visual}")
		print(f"\tQDF: {qdf}")
		print(f"\tProduct: {product}")
		print(f"\tBucket: {bucket}")
		print(f"\tWeek: {ww}")
		print(f"\tTest Number: {Testnumber}")
		print(f"\tTest Name: {TestName}")
		print(f"\tCheck Mem: {checkmem}")
		print(f"\tDebug MCA: {debugmca}")
		print(f"\tDRs Dump: {drdump}")
		print(f"\tSave Location: {reportfolder}")
		print(f"\tUpload to Danta: {upload_to_danta}")
		print(f"\tUpload to Disk: {upload_to_disk}")
		print(f"\tFramework Data: {framework_data}")
		
		# Lazy load dpmlog to avoid circular import
		dpmlog_module = _lazy_import_dpmlog()
		if dpmlog_module is not None:
			dpmlog_module.run(visual = visual, Testnumber=Testnumber, TestName=TestName, chkmem = checkmem, debug_mca = debugmca, dr_dump= drdump, folder=reportfolder,  WW = ww, Bucket = bucket, product = product, QDF = qdf, upload_to_disk = upload_to_disk, upload_to_danta = upload_to_danta, framework_data = framework_data)
		else:
			print('Interface Test Complete')
		#self.root.destroy()

def callUI(qdf, ww, product):

	root = tk.Tk()
	app = loggerGUI(root,qdf, ww, product)
	root.mainloop()

if __name__ == "__main__":

		root = tk.Tk()
		app = loggerGUI(root)
		root.mainloop()
