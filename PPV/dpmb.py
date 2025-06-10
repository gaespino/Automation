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
	def __init__(self, root):
		self.root = root
		self.root.title("DPMB Bucketer")
		self.root.geometry("475x520")  # Set fixed size for the window
		self.root.resizable(False, False)  # Disable resizing

		# Create and place the widgets
		tk.Label(root, text="VID List (one per line):").grid(row=0, column=0, padx=10, pady=5)
		self.vidlist_frame = tk.Frame(root)
		self.vidlist_frame.grid(row=0, column=1, padx=10, pady=5)
		self.vidlist_text = tk.Text(self.vidlist_frame, width=30, height=10)
		self.vidlist_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		self.vidlist_scrollbar = tk.Scrollbar(self.vidlist_frame, command=self.vidlist_text.yview)
		self.vidlist_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		self.vidlist_text.config(yscrollcommand=self.vidlist_scrollbar.set)

		tk.Label(root, text="User:").grid(row=1, column=0, padx=10, pady=5)
		self.user_entry = tk.Entry(root, width=50)
		self.user_entry.insert(0, get_current_user())
		self.user_entry.grid(row=1, column=1, padx=10, pady=5)

		# Year and WW selection for Start WW
		tk.Label(root, text="Start Year:").grid(row=2, column=0, padx=10, pady=5)
		self.start_year_var = tk.IntVar(value=datetime.now().year)
		self.start_year_combobox = ttk.Combobox(root, textvariable=self.start_year_var, values=list(range(2020, datetime.now().year + 1)))
		self.start_year_combobox.grid(row=2, column=1, padx=10, pady=5, sticky='w')

		tk.Label(root, text="Start WW:").grid(row=2, column=1, padx=10, pady=5, sticky='e')
		self.start_ww_var = tk.IntVar(value='')
		self.start_ww_combobox = ttk.Combobox(root, textvariable=self.start_ww_var, values=list(range(1, 53)))
		self.start_ww_combobox.grid(row=2, column=1, padx=10, pady=5, sticky='e')

		# Year and WW selection for End WW
		tk.Label(root, text="End Year:").grid(row=3, column=0, padx=10, pady=5)
		self.end_year_var = tk.IntVar(value=datetime.now().year)
		self.end_year_combobox = ttk.Combobox(root, textvariable=self.end_year_var, values=list(range(2020, datetime.now().year + 1)))
		self.end_year_combobox.grid(row=3, column=1, padx=10, pady=5, sticky='w')

		tk.Label(root, text="End WW:").grid(row=3, column=1, padx=10, pady=5, sticky='e')
		self.end_ww_var = tk.IntVar(value='')
		self.end_ww_combobox = ttk.Combobox(root, textvariable=self.end_ww_var, values=list(range(1, 53)))
		self.end_ww_combobox.grid(row=3, column=1, padx=10, pady=5, sticky='e')

		tk.Label(root, text="Product:").grid(row=4, column=0, padx=10, pady=5)
		self.product_var = tk.StringVar(value="GNR3")
		self.product_combobox = ttk.Combobox(root, textvariable=self.product_var, values=["GNR", "GNR3", "CWF"])
		self.product_combobox.grid(row=4, column=1, padx=10, pady=5, sticky='w')

		tk.Label(root, text="Operations:").grid(row=5, column=0, padx=10, pady=5)
		self.operations_listbox = tk.Listbox(root, selectmode=tk.MULTIPLE)
		self.operations_listbox.insert(1, "8749")
		self.operations_listbox.insert(2, "7775")
		self.operations_listbox.grid(row=5, column=1, padx=10, pady=5, sticky='w')

		# Submit Button
		self.submit_button = tk.Button(root, text="Submit", command=self.submit_form)
		self.submit_button.grid(row=6, column=1, padx=5, pady=10, sticky="ew")

		# Close Button
		self.close_button = tk.Button(root, text="Close", command=root.destroy)
		self.close_button.grid(row=6, column=0, padx=10, pady=10, sticky="ew")

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
		#  'Authorization': 'Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJuYW1laWQiOiIxMTQxMjU2MCIsIndpbmFjY291bnRuYW1lIjoiR0FSXFxsYXlrZWVuZSIsImdpdmVuX25hbWUiOiJMYXkgS2VlIiwiZmFtaWx5X25hbWUiOiJOZXciLCJ1bmlxdWVfbmFtZSI6Ik5ldywgTGF5IEtlZSIsImVtYWlsIjoibGF5LmtlZS5uZXdAaW50ZWwuY29tIiwiaW50ZWx1c2VydHlwZSI6IldvcmtlciIsImludGVsd3dpZCI6IjExNDEyNTYwIiwicm9sZSI6WyJOb25lIiwiRHVtbXkiLCJVc2VyIiwiTWlkYXMiLCJBZG1pbmlzdHJhdG9yIl0sImxvZ2luc2Vzc2lvbmlkIjoiMzhkZjg3ZGItMzc5Mi00ZTQxLWIyMjYtODYwMGEzMjQ1NjA1IiwibmJmIjoxNjM3OTEyMjU5LCJleHAiOjE2Mzc5MTQwNjQsImlhdCI6MTYzNzkxMjI2NCwiaXNzIjoiaHR0cHM6Ly9kcG1iLWludGcuYXBwLmludGVsLmNvbSJ9.FJgeJhW8AvVokEyqsQIRkhi5UN31tbQcjmCjRQy9iCSRnSmMOTwQD6Ju7w2RFksfzxXzuHdSNyMYnzio-WN_Pw',
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