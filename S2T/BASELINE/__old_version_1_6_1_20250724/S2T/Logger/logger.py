import http.client
import json
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import getpass
from datetime import datetime
try: import  users.THR.PythonScripts.thr.S2T.Logger.ErrorReport as dpmlog
except: dpmlog = None

#if __name__ == "__main__":
#    dpmb(vidlist)

class loggerGUI:
	def __init__(self, root, qdf = '', ww='', product = 'GNRAP'):
		self.root = root
		self.root.title(f"{product} Error Logger")
		self.root.geometry("675x250")  # Set fixed size for the window
		self.root.resizable(False, False)  # Disable resizing
		self.product = product
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

		# Submit Button
		self.submit_button = tk.Button(root, text=" Run ", command=self.submit_form)
		self.submit_button.grid(row=6, column=1, padx=5, pady=10, sticky="ew")

		# Close Button
		self.close_button = tk.Button(root, text=" Close ", command=root.destroy)
		self.close_button.grid(row=6, column=0, padx=10, pady=10, sticky="ew")

	def browse_report(self):
		file_path = filedialog.askdirectory()
		self.report_entry.delete(0, tk.END)
		self.report_entry.insert(0, file_path)

	# Function to handle the submission of the form
	def submit_form(self):

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
		print(f"Creating System Log with the following configuration")
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

		dpmlog.run(visual = visual, Testnumber=Testnumber, TestName=TestName, chkmem = checkmem, debug_mca = debugmca, dr_dump= drdump, folder=reportfolder,  WW = ww, Bucket = bucket, product = product, QDF = qdf)
		#self.root.destroy()

def callUI(qdf, ww, product):

	root = tk.Tk()
	app = loggerGUI(root,qdf, ww, product)
	root.mainloop()

if __name__ == "__main__":

		root = tk.Tk()
		app = loggerGUI(root)
		root.mainloop()