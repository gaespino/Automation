import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xlwings as xw
from PPVLoopChecks import PTCReportGUI
from PPVDataChecks import PPVReportGUI
from dpmb import dpmbGUI
from PPVFileHandler import FileHandlerGUI
#import pyfiglet

def display_banner():
    # Create the banner text
    banner_text = rf'''
=============================================================================
    ____  ____  __  ___   ____  ____ _    __   __________  ____  __   _____
   / __ \/ __ \/  |/  /  / __ \/ __ \ |  / /  /_  __/ __ \/ __ \/ /  / ___/
  / / / / /_/ / /|_/ /  / /_/ / /_/ / | / /    / / / / / / / / / /   \__ \ 
 / /_/ / ____/ /  / /  / ____/ ____/| |/ /    / / / /_/ / /_/ / /______/ / 
/_____/_/   /_/  /_/  /_/   /_/     |___/    /_/  \____/\____/_____/____/  
                                                                                                   
=============================================================================
    '''
    
    # Print the banner
    print(banner_text)

# Create the main window

class Tools(tk.Frame):
	def __init__(self, root):
		super().__init__(root)
		self.root = root
		self.root.title("PPV Tools Main")
		self.root.geometry("475x300")  # Set fixed size for the window
		self.root.resizable(False, False)  # Disable resizing
		
		self.ppv_loop_parser_label = tk.Label(root, justify='left', text=" - Parse logs from PTC experiment data. \n > Output is a DPMB report format file.")
		self.ppv_loop_parser_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")		
		ppv_loop_parser_button = tk.Button(root, text=" PTC Loop Parser ", command=self.open_ppv_loop_parser)
		#ppv_loop_parser_button.pack(padx=10, pady=10)
		ppv_loop_parser_button.grid(row=0, column=0, padx=10, pady=5, sticky='ew')
		
		self.add_separator(root, 1)

		self.ppv_mca_report_label = tk.Label(root, justify='left', text=" - Generate a MCA report from a Bucketer report format file\n - Generate a MCA report file from S2T Logger data.")
		self.ppv_mca_report_label.grid(row=2, column=1, padx=10, pady=5, sticky="w")	
		ppv_mca_report_button = tk.Button(root, text=" PPV MCA Report ", command=self.open_ppv_mca_report)
		#ppv_mca_report_button.pack(padx=10, pady=10)
		ppv_mca_report_button.grid(row=2, column=0, padx=10, pady=5, sticky='ew')
		
		self.add_separator(root, 3)

		self.dpmb_label = tk.Label(root, justify='left', text=" - Bucketer requests for PPV runs data. \n > Connects to DPMB API to request Data.")
		self.dpmb_label.grid(row=4, column=1, padx=10, pady=5, sticky="w")		
		dpmb_button = tk.Button(root, text=" DPMB Requests ", command=self.open_dpmb)
		#dpmb_button.pack(padx=10, pady=10)
		dpmb_button.grid(row=4, column=0, padx=10, pady=5, sticky='ew')

		self.add_separator(root, 5)

		self.dpmb_label = tk.Label(root, justify='left', text=" - Tool for handling Data Files. \n > Merge multiple DPMB format files \n > Append MCA Report Files")
		self.dpmb_label.grid(row=6, column=1, padx=10, pady=5, sticky="w")				
		fh_button = tk.Button(root, text=" File Handler ", command=self.open_filehandler)
		#fh_button.pack(padx=10, pady=10)
		fh_button.grid(row=6, column=0, padx=10, pady=5, sticky='ew')
		
		self.add_separator(root, 7)

		exit_button = tk.Button(root, text=" Close ", command=self.root.quit)
		#exit_button.pack(padx=10, pady=10)
		exit_button.grid(row=8, column=0, columnspan=2, padx=10, pady=5, sticky='ew')

	def add_separator(self, parent, row):
		separator = ttk.Separator(parent, orient='horizontal')
		separator.grid(row=row, columnspan=2, sticky="ew", pady=5)


	def open_ppv_loop_parser(self):
		root1 = tk.Toplevel(self.root)
		root1.title('PPV Loop Parser')
		app1 = PTCReportGUI(root1)
		#app1.pack(fill="both", expand=True)
		
	def open_ppv_mca_report(self):
		root2 = tk.Toplevel()
		root2.title('MCA Parser')
		app2 = PPVReportGUI(root2)
		#app2.pack(fill="both", expand=True)

	def open_dpmb(self):
		root3 = tk.Toplevel()
		root3.title('Bucketer Requests')
		app3 = dpmbGUI(root3)
		#app3.pack(fill="both", expand=True)

	def open_filehandler(self):
		root4 = tk.Toplevel()
		root4.title('File Handler')
		app4 = FileHandlerGUI(root4)
		#app3.pack(fill="both", expand=True)


if __name__ == "__main__":
	display_banner()
	root = tk.Tk(baseName='MainWindow')
	app = Tools(root)
	#app.pack(fill='both', expand=True)
	root.mainloop()