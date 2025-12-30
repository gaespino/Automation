import sys
import os
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
import datetime
from tkinter import filedialog, messagebox

try:
    from ..parsers.MCAparser import ppv_report as mcap
except ImportError:
    from parsers.MCAparser import ppv_report as mcap

class PPVReportGUI:
    def __init__(self, root, default_product="GNR"):
        self.root = root
        self.default_product = default_product  # Store default product
        self.root.title("PPV MCA Report Builder")
        self.root.geometry("850x550")  # Increased size
        self.root.resizable(True, True)  # Allow resizing
        
        # Configure grid weights
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # Header frame with color accent
        header_frame = tk.Frame(self.root, bg='#e74c3c', height=12)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)
        
        # Main container
        main_container = tk.Frame(self.root)
        main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        main_container.rowconfigure(2, weight=1)
        main_container.columnconfigure(0, weight=1)
        
        # Configuration section
        config_frame = tk.LabelFrame(main_container, text="Report Configuration", 
                                     font=("Segoe UI", 10, "bold"), padx=15, pady=15)
        config_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        config_frame.columnconfigure(3, weight=1)
        config_frame.columnconfigure(5, weight=1)
        
        # Mode
        tk.Label(config_frame, text="Mode:", font=("Segoe UI", 9)).grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.mode_entry = tk.StringVar(root)
        self.mode_entry.set("Bucketer")
        self.mode_menu = tk.OptionMenu(config_frame, self.mode_entry, "Framework", "Bucketer", "Data", 
                                      command=self.mode_selection)
        self.mode_menu.config(font=("Segoe UI", 9), width=12)
        self.mode_menu.grid(row=0, column=1, padx=5, pady=8, sticky="w")
        self.add_tooltip(self.mode_menu, "Select data source: Framework logs, Bucketer data, or raw Data files")
        
        # Product
        tk.Label(config_frame, text="Product:", font=("Segoe UI", 9)).grid(row=0, column=2, padx=5, pady=8, sticky="w")
        self.name_entry = tk.StringVar(root)
        self.name_entry.set(self.default_product)  # Use default product
        self.product_menu = tk.OptionMenu(config_frame, self.name_entry, "GNR", "CWF", "DMR")
        self.product_menu.config(font=("Segoe UI", 9), width=8)
        self.product_menu.grid(row=0, column=3, padx=5, pady=8, sticky="w")
        self.add_tooltip(self.product_menu, "Product family: GNR, CWF, or DMR")
        
        current_week = datetime.datetime.now().isocalendar()[1]
        
        # Week
        tk.Label(config_frame, text="Week:", font=("Segoe UI", 9)).grid(row=0, column=4, padx=5, pady=8, sticky="w")
        self.week_entry = tk.StringVar(root)
        self.week_entry.set(str(current_week))
        self.week_menu = tk.OptionMenu(config_frame, self.week_entry, *[str(i) for i in range(1, 53)])
        self.week_menu.config(font=("Segoe UI", 9), width=5)
        self.week_menu.grid(row=0, column=5, padx=5, pady=8, sticky="w")
        self.add_tooltip(self.week_menu, "Work week number (1-52)")
        
        # Label
        tk.Label(config_frame, text="Label:", font=("Segoe UI", 9)).grid(row=1, column=0, padx=5, pady=8, sticky="w")
        self.label_entry = tk.Entry(config_frame, font=("Segoe UI", 9))
        self.label_entry.grid(row=1, column=1, columnspan=5, padx=5, pady=8, sticky="ew")
        self.add_tooltip(self.label_entry, "Custom label for the report (e.g., PPV_Batch_001)")
        
        # File paths section
        paths_frame = tk.LabelFrame(main_container, text="Input / Output Files", 
                                    font=("Segoe UI", 10, "bold"), padx=15, pady=15)
        paths_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        paths_frame.columnconfigure(1, weight=1)
        
        # Source File
        self.source_file_label = tk.Label(paths_frame, text="Bucketer File:", font=("Segoe UI", 9))
        self.source_file_label.grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.source_file_entry = tk.Entry(paths_frame, width=75, font=("Segoe UI", 9))
        self.source_file_entry.grid(row=0, column=1, padx=5, pady=8, sticky="ew")
        self.source_file_button = tk.Button(paths_frame, text="Browse", command=self.browse_source_file,
                                           bg="#3498db", fg="white", font=("Segoe UI", 8, "bold"),
                                           padx=15, relief=tk.FLAT, cursor="hand2")
        self.source_file_button.grid(row=0, column=2, padx=5, pady=8)
        
        # Report
        tk.Label(paths_frame, text="Report Output:", font=("Segoe UI", 9)).grid(row=1, column=0, padx=5, pady=8, sticky="w")
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
        
        # Left column options
        left_opts = tk.Frame(options_frame)
        left_opts.grid(row=0, column=0, sticky="w", padx=5)
        
        self.reduced_var = tk.BooleanVar(value=True)
        self.reduced_check = tk.Checkbutton(left_opts, text="Reduced report", 
                                           variable=self.reduced_var, font=("Segoe UI", 9))
        self.reduced_check.pack(anchor="w", pady=3)
        self.add_tooltip(self.reduced_check, "Generate simplified report with essential data only")
        
        self.decode_var = tk.BooleanVar(value=True)
        self.decode_check = tk.Checkbutton(left_opts, text="MCA decode", 
                                          variable=self.decode_var, font=("Segoe UI", 9))
        self.decode_check.pack(anchor="w", pady=3)
        self.add_tooltip(self.decode_check, "Decode Machine Check Architecture errors")
        
        # Right column options
        right_opts = tk.Frame(options_frame)
        right_opts.grid(row=0, column=1, sticky="w", padx=20)
        
        self.overview_var = tk.BooleanVar(value=True)
        self.overview_check = tk.Checkbutton(right_opts, text="Overview sheet", 
                                            variable=self.overview_var, font=("Segoe UI", 9))
        self.overview_check.pack(anchor="w", pady=3)
        self.add_tooltip(self.overview_check, "Include summary overview sheet in report")
        
        self.mcfile_var = tk.BooleanVar(value=False)
        self.mcfile_check = tk.Checkbutton(right_opts, text="MCA Checker file", 
                                          variable=self.mcfile_var, font=("Segoe UI", 9))
        self.mcfile_check.pack(anchor="w", pady=3)
        self.add_tooltip(self.mcfile_check, "Generate separate MCA checker validation file")
        
        # Action buttons
        button_frame = tk.Frame(main_container)
        button_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        button_frame.columnconfigure(0, weight=1)
        
        btn_container = tk.Frame(button_frame)
        btn_container.pack(side="right")
        
        # Submit Button
        self.submit_button = tk.Button(btn_container, text="Generate Report", command=self.submit,
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

    def browse_source_file(self):
        file_path = filedialog.askopenfilename()
        self.source_file_entry.delete(0, tk.END)
        self.source_file_entry.insert(0, file_path)

        # Set the Report field to the directory of the selected Bucketer File
        report_directory = os.path.dirname(file_path)
        self.report_entry.delete(0, tk.END)
        self.report_entry.insert(0, report_directory)

    def browse_report(self):
        file_path = filedialog.askdirectory()
        self.report_entry.delete(0, tk.END)
        self.report_entry.insert(0, file_path)

    def mode_selection(self, value):
        if  value == "Data":
            self.source_file_label.config(text="Data File:")
            self.reduced_check.config(state=tk.DISABLED)
            self.decode_check.config(state=tk.DISABLED)
        else:
            self.source_file_label.config(text="Bucketer File:")
            self.reduced_check.config(state=tk.ACTIVE)
            self.decode_check.config(state=tk.ACTIVE)

    def submit(self):
        data = {
        'mode' : self.mode_entry.get(),
        'name' : self.name_entry.get(),
        'week' : self.week_entry.get(),
        'label' : self.label_entry.get(),
        'source_file' : self.source_file_entry.get(),
        'report' : self.report_entry.get(),
        'reduced' : self.reduced_var.get(),
        'overview' : self.overview_var.get(),
        'decode' : self.decode_var.get(),
        'mcfile' : self.mcfile_var.get()
        }

        # You can add your logic here to handle the submitted data
        messagebox.showinfo("Submitted Data", f"Name: {data['name']}\nWeek: {data['week']}\nLabel: {data['label']}\nSource File: {data['source_file']}\nReport: {data['report']}\nReduced: {data['reduced']}\nOverview: {data['overview']}\nMCA Decode: {data['decode']}")
        # Copy the template file to the new target file
        PPVMCAs = mcap(name=data['name'], week=data['week'], label=data['label'], source_file=data['source_file'], report = data['report'], reduced = data['reduced'], mcdetail=data['mcfile'], overview = data['overview'], decode = data['decode'])
        self.header(data)
        
        if data['mode'] == 'Bucketer' or data['mode'] == 'Framework': 
            PPVMCAs.run(options=['MESH', 'CORE'])
        elif data['mode'] == 'Data': 
            PPVMCAs.gen_auxfiles(data_file=data['source_file'], mca_file=PPVMCAs.mca_file, ovw_file=PPVMCAs.ovw_file, mcfile_on=data['mcfile'], ovw_on= data['overview'], options = ['MESH', 'CORE', 'PPV'])
        else: print(' -- Not a valid mode')
        #self.__init__(self.root)

    def header(self, data):
        print(f' {"#"*120}\n')
        print(f'\t{"-"*10} MCA Parser {"-"*10}')
        print(f'\tParsed datafiles will be saved at location: {data["report"]}\n')
        print(f'\tUsing Configuration:')
        #print(f'\tvpos:   \t{vpo}')		
        print(f'\tName:   \t{data["name"]}')	
        print(f'\tWeek: \t\t{data["week"]}')	
        print(f'\tLabel:   \t{data["label"]}')	
        print(f'\tReport: \t{data["report"]}')	
        print(f'\tSource: \t{data["source_file"]}')
        print(f'\tReduced:   \t\t{data["reduced"]}')
        print(f'\tOverview File:   \t{data["overview"]}')
        print(f'\tMCA Decode:   \t\t{data["decode"]}')
        print(f'\tMCA Check File:   \t{data["mcfile"]}')
        print(f'\n{"#"*120}')
        print(f'{"#"*120}\n')
        print(f'\t{"-"*10} Processing data... Please wait.. {"-"*10} \n')
        
if __name__ == "__main__":
    root = tk.Tk()
    app = PPVReportGUI(root)
    root.mainloop()