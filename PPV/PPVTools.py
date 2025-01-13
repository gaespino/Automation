import tkinter as tk
from tkinter import filedialog, messagebox
import xlwings as xw
from PPVLoopChecks import PTCReportGUI
from PPVDataChecks import PPVReportGUI
from dpmb import dpmbGUI
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
		self.root.geometry("250x200")  # Set fixed size for the window
		self.root.resizable(False, False)  # Disable resizing
		ppv_loop_parser_button = tk.Button(root, text=" PTC Loop Parser ", command=self.open_ppv_loop_parser)
		ppv_loop_parser_button.pack(padx=10, pady=10)


		ppv_mca_report_button = tk.Button(root, text=" PPV MCA Report ", command=self.open_ppv_mca_report)
		ppv_mca_report_button.pack(padx=10, pady=10)


		dpmb_button = tk.Button(root, text=" DPMB Requests ", command=self.open_dpmb)
		dpmb_button.pack(padx=10, pady=10)

		exit_button = tk.Button(root, text=" Close ", command=self.root.quit)
		exit_button.pack(padx=10, pady=10)
		  


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


if __name__ == "__main__":
	display_banner()
	root = tk.Tk(baseName='MainWindow')
	app = Tools(root)
	app.pack(fill='both', expand=True)
	root.mainloop()