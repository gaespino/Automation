import sys
import os
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import filedialog, messagebox
#from MCAparser import ppv_report as mcap

try:
    from ..parsers.PPVLoopsParser import LogsPTC as ptc
except ImportError:
    from parsers.PPVLoopsParser import LogsPTC as ptc

class PTCReportGUI:
    def __init__(self, root, default_product="GNR"):
        self.root = root
        self.default_product = default_product  # Store default product
        self.root.title("PTC Loop Parser")
        self.root.geometry("800x450")  # Increased size
        self.root.resizable(True, True)  # Allow resizing
        
        # Configure grid weights
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # Header frame with color accent
        header_frame = tk.Frame(self.root, bg='#3498db', height=12)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)
        
        # Main container
        main_container = tk.Frame(self.root)
        main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        main_container.rowconfigure(2, weight=1)
        main_container.columnconfigure(0, weight=1)
        
        # Configuration section
        config_frame = tk.LabelFrame(main_container, text="Experiment Configuration", 
                                     font=("Segoe UI", 10, "bold"), padx=15, pady=15)
        config_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Bucket
        tk.Label(config_frame, text="Bucket:", font=("Segoe UI", 9)).grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.name_entry = tk.Entry(config_frame, font=("Segoe UI", 9))
        self.name_entry.grid(row=0, column=1, padx=5, pady=8, sticky="ew")
        self.add_tooltip(self.name_entry, "Enter bucket identifier (e.g., PPV_Loops_WW45)")
        
        # Week
        tk.Label(config_frame, text="Week:", font=("Segoe UI", 9)).grid(row=0, column=2, padx=5, pady=8, sticky="w")
        self.week_entry = tk.Entry(config_frame, width=10, font=("Segoe UI", 9))
        self.week_entry.grid(row=0, column=3, padx=5, pady=8, sticky="w")
        self.add_tooltip(self.week_entry, "Work week number (e.g., 45)")
        
        # Sequence Key
        tk.Label(config_frame, text="Sequence Key:", font=("Segoe UI", 9)).grid(row=1, column=0, padx=5, pady=8, sticky="w")
        self.key_entry = tk.Entry(config_frame, font=("Segoe UI", 9))
        self.key_entry.insert(0, "100")
        self.key_entry.grid(row=1, column=1, padx=5, pady=8, sticky="ew")
        tk.Label(config_frame, text="(Default: 100)", font=("Segoe UI", 8), fg="#7f8c8d").grid(row=1, column=2, columnspan=2, padx=5, pady=8, sticky="w")
        self.add_tooltip(self.key_entry, "Sequence identifier for organizing loop data")
        
        # File paths section
        paths_frame = tk.LabelFrame(main_container, text="Input / Output Paths", 
                                    font=("Segoe UI", 10, "bold"), padx=15, pady=15)
        paths_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        paths_frame.columnconfigure(1, weight=1)
        
        # Output File
        tk.Label(paths_frame, text="Output File:", font=("Segoe UI", 9)).grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.output_entry = tk.Entry(paths_frame, width=75, font=("Segoe UI", 9))
        self.output_entry.grid(row=0, column=1, padx=5, pady=8, sticky="ew")
        self.source_file_button = tk.Button(paths_frame, text="Browse", command=self.browse_output,
                                           bg="#3498db", fg="white", font=("Segoe UI", 8, "bold"),
                                           padx=15, relief=tk.FLAT, cursor="hand2")
        self.source_file_button.grid(row=0, column=2, padx=5, pady=8)
        
        # Loops Folder
        tk.Label(paths_frame, text="Loops Folder:", font=("Segoe UI", 9)).grid(row=1, column=0, padx=5, pady=8, sticky="w")
        self.report_entry = tk.Entry(paths_frame, width=75, font=("Segoe UI", 9))
        self.report_entry.grid(row=1, column=1, padx=5, pady=8, sticky="ew")
        self.report_button = tk.Button(paths_frame, text="Browse", command=self.browse_report,
                                      bg="#3498db", fg="white", font=("Segoe UI", 8, "bold"),
                                      padx=15, relief=tk.FLAT, cursor="hand2")
        self.report_button.grid(row=1, column=2, padx=5, pady=8)
        
        # Options section
        options_frame = tk.LabelFrame(main_container, text="Processing Options", 
                                     font=("Segoe UI", 10, "bold"), padx=15, pady=15)
        options_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        # Zipfile
        self.zipfile_var = tk.BooleanVar(value=False)
        self.zipfile_check = tk.Checkbutton(options_frame, text="Process ZIP files", 
                                           variable=self.zipfile_var, font=("Segoe UI", 9))
        self.zipfile_check.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.add_tooltip(self.zipfile_check, "Enable if loop data is in compressed ZIP format")
        
        # Format
        self.dpmb_var = tk.BooleanVar(value=False)
        self.dpmb_check = tk.Checkbutton(options_frame, text="PySV logging format", 
                                        variable=self.dpmb_var, font=("Segoe UI", 9))
        self.dpmb_check.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.add_tooltip(self.dpmb_check, "Use PySV logging format for parsing")
        
        # Action buttons
        button_frame = tk.Frame(main_container)
        button_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        button_frame.columnconfigure(0, weight=1)
        
        btn_container = tk.Frame(button_frame)
        btn_container.pack(side="right")
        
        # Submit Button
        self.submit_button = tk.Button(btn_container, text="Parse Loops", command=self.submit,
                                      bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"),
                                      padx=25, pady=10, relief=tk.FLAT, cursor="hand2")
        self.submit_button.pack(side="left", padx=5)
        
        # Close Button
        self.close_button = tk.Button(btn_container, text="Close", command=root.destroy,
                                     bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"),
                                     padx=25, pady=10, relief=tk.FLAT, cursor="hand2")
        self.close_button.pack(side="left", padx=5)
    
    def add_tooltip(self, widget, text):
        """Add tooltip to widget"""
        tooltip = tk.Toplevel(widget, bg="#2c3e50", padx=8, pady=5)
        tooltip.wm_overrideredirect(True)
        tooltip.withdraw()
        label = tk.Label(tooltip, text=text, bg="#2c3e50", fg="white", 
                        font=("Segoe UI", 8), wraplength=300, justify="left")
        label.pack()

        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            tooltip.wm_geometry(f"+{x}+{y}")
            tooltip.deiconify()

        def leave(event):
            tooltip.withdraw()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    #def browse_source_file(self):
    #    file_path = filedialog.askopenfilename()
    #    self.source_file_entry.delete(0, tk.END)
    #    self.source_file_entry.insert(0, file_path)

    def browse_report(self):
        file_path = filedialog.askdirectory()
        self.report_entry.delete(0, tk.END)
        self.report_entry.insert(0, file_path)
    
    def browse_output(self):
        output_selected = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, output_selected)
    
    def submit(self):
        data = {
        'bucket' : self.name_entry.get(),
        'week' : self.week_entry.get(),
        'keyEntry' : self.key_entry.get(),
        'output_file' : self.output_entry.get(),
        'report' : self.report_entry.get(),
        'zfile' : self.zipfile_var.get(),
        'dpmb' : not self.dpmb_var.get(),
        #overview = self.overview_var.get()
        }
        try:
            keyEntry = int(data['keyEntry'])
        except:
            keyEntry = 100
            print('Invalid Key Sequence entry, defaulting to 100')
        data['keyEntry'] = keyEntry

        # You can add your logic here to handle the submitted data
        messagebox.showinfo("Submitted Data", f"Bucket: {data['bucket']}\nWeek: {data['week']}\nSequence Key: {keyEntry}\nSave File: {data['output_file']}\nLoops Folder: {data['report']}\nPythonSV Format: {data['dpmb']}\nZipFile: {data['zfile']}\n --")
        # Copy the template file to the new target file
        PPVLoops = ptc(StartWW = data['week'], bucket = data['bucket'], LotsSeqKey = keyEntry, folder_path=data['report'], output_file=data['output_file'], zipfile=data['zfile'], dpmbformat=data['dpmb'])
        self.header(data)
        PPVLoops.run()

        #root.quit()
    def header(self, data):
        print(f' {"#"*120}\n')
        print(f'\t{"-"*10} PPV Loops Parser {"-"*10}')
        print(f'\tParsed file will be saved at: {data["output_file"]}\n')
        print('\tUsing Configuration:')
        #print(f'\tvpos:   \t{vpo}')		
        print(f'\tBucket:   \t{data["bucket"]}')	
        print(f'\tWeek: \t\t{data["week"]}')	
        print(f'\tKeyentry:   \t{data["keyEntry"]}')	
        print(f'\tReport: \t{data["report"]}')	
        print(f'\tParse File: \t{data["output_file"]}')
        print(f'\tZip File:   \t\t{data["zfile"]}')
        print(f'\tDPMB Format:   \t\t{data["dpmb"]}')
        print(f'\n{"#"*120}')
        print(f'{"#"*120}\n')
        print(f'\t{"-"*10} Processing data... Please wait.. {"-"*10} \n')
 

if __name__ == "__main__":
    root = tk.Tk()
    app = PTCReportGUI(root)
    root.mainloop()