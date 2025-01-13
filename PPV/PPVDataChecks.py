import tkinter as tk
from tkinter import filedialog, messagebox
from MCAparser import ppv_report as mcap

class PPVReportGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DPMB Report Builder")
        self.root.geometry("650x250")  # Set fixed size for the window
        self.root.resizable(False, False)  # Disable resizing

        # Name
        self.name_label = tk.Label(root, text="Product:")
        self.name_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.name_entry = tk.Entry(root)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # Week
        self.week_label = tk.Label(root, text="Week:")
        self.week_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.week_entry = tk.Entry(root)
        self.week_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Label
        self.label_label = tk.Label(root, text="Label:")
        self.label_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.label_entry = tk.Entry(root)
        self.label_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Source File
        self.source_file_label = tk.Label(root, text="Bucketer File:")
        self.source_file_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.source_file_entry = tk.Entry(root, width=75)
        self.source_file_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew", columnspan=2)
        self.source_file_button = tk.Button(root, text="Browse", command=self.browse_source_file)
        self.source_file_button.grid(row=3, column=3, padx=10, pady=5)

        # Report
        self.report_label = tk.Label(root, text="Report:")
        self.report_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.report_entry = tk.Entry(root, width=75)
        self.report_entry.grid(row=4, column=1, padx=10, pady=5, sticky="ew", columnspan=2)
        self.report_button = tk.Button(root, text="Browse", command=self.browse_report)
        self.report_button.grid(row=4, column=3, padx=10, pady=5)

        # Reduced
        self.reduced_var = tk.BooleanVar(value=True)
        self.reduced_check = tk.Checkbutton(root, text="Reduced", variable=self.reduced_var)
        self.reduced_check.grid(row=5, columnspan=1, padx=10, pady=5, sticky="w")

        # Overview
        self.overview_var = tk.BooleanVar(value=True)
        self.overview_check = tk.Checkbutton(root, text="Overview", variable=self.overview_var)
        self.overview_check.grid(row=5, column=1, columnspan=3, padx=10, pady=5, sticky="w")

        # MCA Checker
        self.mcfile_var = tk.BooleanVar(value=True)
        self.mcfile_check = tk.Checkbutton(root, text="MCA Checker", variable=self.mcfile_var)
        self.mcfile_check.grid(row=6, column=0, columnspan=1, padx=10, pady=5, sticky="w")

        # Decode
        self.decode_var = tk.BooleanVar(value=True)
        self.decode_check = tk.Checkbutton(root, text="MCA decode", variable=self.decode_var)
        self.decode_check.grid(row=6, column=1, columnspan=3, padx=10, pady=5, sticky="w")

        # Submit Button
        self.submit_button = tk.Button(root, text="Submit", command=self.submit)
        self.submit_button.grid(row=6, column=2, padx=1, pady=10, sticky="e")

        # Close Button
        self.close_button = tk.Button(root, text="Close", command=root.destroy)
        self.close_button.grid(row=6, column=3, padx=10, pady=10, sticky="e")

        # Configure column weights for proper resizing
        root.grid_columnconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=1)
        root.grid_columnconfigure(3, weight=1)

    def browse_source_file(self):
        file_path = filedialog.askopenfilename()
        self.source_file_entry.delete(0, tk.END)
        self.source_file_entry.insert(0, file_path)

    def browse_report(self):
        file_path = filedialog.askdirectory()
        self.report_entry.delete(0, tk.END)
        self.report_entry.insert(0, file_path)

    def submit(self):
        data = {
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
        
        PPVMCAs.run(options=['MESH', 'CORE'])
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