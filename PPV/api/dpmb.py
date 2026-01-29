import http.client
import json
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import getpass
from datetime import datetime

dpmb_host = "https://dpmb-api.intel.com/api" #"https://dpmb-api.app.intel.com/api/"#"https://dpmb-api.intel.com/api"
dpmb_api = "dpmb-api.intel.com"
#vidlist = 'D491916S00148'

#if __name__ == "__main__":
#    dpmb(vidlist)

class dpmbGUI:
	def __init__(self, root, default_product="GNR"):
		self.root = root
		self.default_product = default_product  # Store default product
		self.root.title("DPMB Bucketer Requests")
		self.root.geometry("800x700")  # Increased size
		self.root.resizable(True, True)  # Allow resizing

		# Configure grid weights
		self.root.rowconfigure(0, weight=0)
		self.root.rowconfigure(1, weight=1)
		self.root.columnconfigure(0, weight=1)

		# Header frame with color accent
		header_frame = tk.Frame(self.root, bg='#9b59b6', height=12)
		header_frame.grid(row=0, column=0, sticky="ew")
		header_frame.grid_propagate(False)

		# Main container
		main_container = tk.Frame(self.root)
		main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
		main_container.rowconfigure(3, weight=1)
		main_container.columnconfigure(0, weight=1)

		# Visual IDs section
		vid_frame = tk.LabelFrame(main_container, text="Visual IDs",
		                         font=("Segoe UI", 10, "bold"), padx=15, pady=15)
		vid_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
		vid_frame.columnconfigure(0, weight=1)

		tk.Label(vid_frame, text="VID List (one per line):",
		        font=("Segoe UI", 9)).grid(row=0, column=0, padx=5, pady=(0, 5), sticky="w")

		# VIDs text area with scrollbar
		self.vidlist_frame = tk.Frame(vid_frame)
		self.vidlist_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
		self.vidlist_frame.columnconfigure(0, weight=1)

		self.vidlist_text = tk.Text(self.vidlist_frame, width=30, height=8,
		                            font=("Consolas", 9), relief=tk.SOLID, borderwidth=1)
		self.vidlist_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		self.vidlist_scrollbar = tk.Scrollbar(self.vidlist_frame, command=self.vidlist_text.yview)
		self.vidlist_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		self.vidlist_text.config(yscrollcommand=self.vidlist_scrollbar.set)

		# User section
		user_frame = tk.LabelFrame(main_container, text="User Configuration",
		                          font=("Segoe UI", 10, "bold"), padx=15, pady=15)
		user_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
		user_frame.columnconfigure(1, weight=1)

		tk.Label(user_frame, text="User:", font=("Segoe UI", 9)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
		self.user_entry = tk.Entry(user_frame, width=50, font=("Segoe UI", 9))
		self.user_entry.insert(0, get_current_user())
		self.user_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

		# Time Range section
		time_frame = tk.LabelFrame(main_container, text="Time Range",
		                          font=("Segoe UI", 10, "bold"), padx=15, pady=15)
		time_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

		# Start WW
		start_frame = tk.Frame(time_frame)
		start_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
		tk.Label(start_frame, text="Start Year:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 5))
		self.start_year_var = tk.IntVar(value=datetime.now().year)
		self.start_year_combobox = ttk.Combobox(start_frame, textvariable=self.start_year_var,
		                                        values=list(range(2020, datetime.now().year + 1)), width=8)
		self.start_year_combobox.pack(side=tk.LEFT, padx=(0, 15))

		tk.Label(start_frame, text="Start WW:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 5))
		self.start_ww_var = tk.IntVar(value='')
		self.start_ww_combobox = ttk.Combobox(start_frame, textvariable=self.start_ww_var,
		                                      values=list(range(1, 53)), width=5)
		self.start_ww_combobox.pack(side=tk.LEFT)

		# End WW
		end_frame = tk.Frame(time_frame)
		end_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
		tk.Label(end_frame, text="End Year:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 5))
		self.end_year_var = tk.IntVar(value=datetime.now().year)
		self.end_year_combobox = ttk.Combobox(end_frame, textvariable=self.end_year_var,
		                                      values=list(range(2020, datetime.now().year + 1)), width=8)
		self.end_year_combobox.pack(side=tk.LEFT, padx=(0, 15))

		tk.Label(end_frame, text="End WW:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 5))
		self.end_ww_var = tk.IntVar(value='')
		self.end_ww_combobox = ttk.Combobox(end_frame, textvariable=self.end_ww_var,
		                                    values=list(range(1, 53)), width=5)
		self.end_ww_combobox.pack(side=tk.LEFT)

		# Product & Operations section
		config_frame = tk.LabelFrame(main_container, text="Request Configuration",
		                            font=("Segoe UI", 10, "bold"), padx=15, pady=15)
		config_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
		config_frame.rowconfigure(1, weight=1)
		config_frame.columnconfigure(1, weight=1)

		tk.Label(config_frame, text="Product:", font=("Segoe UI", 9)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
		self.product_var = tk.StringVar(value="GNR3")
		self.product_combobox = ttk.Combobox(config_frame, textvariable=self.product_var,
		                                     values=["GNR", "GNR3", "CWF", "DMR"], width=15)
		self.product_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")

		tk.Label(config_frame, text="Operations:", font=("Segoe UI", 9)).grid(row=1, column=0, padx=5, pady=5, sticky="nw")

		ops_container = tk.Frame(config_frame)
		ops_container.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
		ops_container.rowconfigure(0, weight=1)
		ops_container.columnconfigure(0, weight=1)

		self.operations_listbox = tk.Listbox(ops_container, selectmode=tk.MULTIPLE,
		                                     font=("Consolas", 9), height=6, relief=tk.SOLID, borderwidth=1)
		self.operations_listbox.grid(row=0, column=0, sticky="nsew")
		self.operations_listbox.insert(1, "8749")
		self.operations_listbox.insert(2, "8748")
		self.operations_listbox.insert(3, "8657")
		self.operations_listbox.insert(4, "7682")
		self.operations_listbox.insert(5, "7681")
		self.operations_listbox.insert(6, "7775")

		ops_scrollbar = tk.Scrollbar(ops_container, command=self.operations_listbox.yview)
		ops_scrollbar.grid(row=0, column=1, sticky="ns")
		self.operations_listbox.config(yscrollcommand=ops_scrollbar.set)

		# Action buttons
		button_frame = tk.Frame(main_container)
		button_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
		button_frame.columnconfigure(0, weight=1)

		btn_container = tk.Frame(button_frame)
		btn_container.pack(side="right")

		# Submit Button
		self.submit_button = tk.Button(btn_container, text="Submit Request", command=self.submit_form,
		                              bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"),
		                              padx=25, pady=10, relief=tk.FLAT, cursor="hand2")
		self.submit_button.pack(side="left", padx=5)

		# Close Button
		self.close_button = tk.Button(btn_container, text="Close", command=root.destroy,
		                             bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"),
		                             padx=25, pady=10, relief=tk.FLAT, cursor="hand2")
		self.close_button.pack(side="left", padx=5)

	# Function to handle the submission of the form
	def submit_form(self):
		vidlist = self.vidlist_text.get("1.0", tk.END).strip().split('\n')
		user = self.user_entry.get()
		startY = self.start_year_var.get()
		startW = self.start_ww_var.get()
		endY = self.end_year_var.get()
		endW = self.end_ww_var.get()
		startWW = f'{startY}{startW:02d}'
		endWW = f'{endY}{endW:02d}'
		product = self.product_var.get()
		operations = [self.operations_listbox.get(i) for i in self.operations_listbox.curselection()]

		vidlist_str = ','.join(vidlist)
		operations_str = ','.join(operations)
		delta = abs(int(startWW)-int(endWW))

		print(f"VID List: {vidlist_str}")
		print(f"User: {user}")
		print(f"Start WW: {startWW}")
		print(f"End WW: {endWW}")
		print(f"Delta: {delta}")
		print(f"Product: {product}")
		print(f"Operations: {operations_str}")


		data = dpmb(vidlist=vidlist_str, user=user, startWW=startWW, endWW=endWW, product=product, operations=operations_str, delta=delta)
		data.request()
		data.status()

class dpmb:
	def __init__(self, vidlist, user, startWW, endWW, product, operations, delta):
		self.vidlist = vidlist
		self.user = user
		self.startWW = startWW
		self.endWW = endWW
		self.product = product
		self.operations = operations
		self.delta = delta
		self.conn = http.client.HTTPSConnection(dpmb_api)

		self.payload = json.dumps({
			"createdBy": self.user,
			"endWW": self.endWW,
			"operationCsv": self.operations,
			"product": self.product,
			"scriptId": 1,
			"startWW": self.startWW,
			"status": "Pending",
			"updatedBy": self.user,
			"visualIdCsv": self.vidlist,
			"wwDelta": str(self.delta)
		})
		self.headers = {
			'Content-Type': 'application/json'
		}

	def request(self):

		self.conn.request("POST", "/api/job/create", self.payload, self.headers)
		res = self.conn.getresponse()
		data = res.read()
		print(data.decode("utf-8"))

	def status(self):

		## Get last job status
		self.conn.request("GET", f"/api/job/users/{self.user}/products/{self.product}/last", self.payload, self.headers)
		res = self.conn.getresponse()
		data = res.read()
		print(data.decode("utf-8"))

# Function to get the current system username
def get_current_user():
		return getpass.getuser()

if __name__ == "__main__":
		root = tk.Tk()
		app = dpmbGUI(root)
		root.mainloop()
