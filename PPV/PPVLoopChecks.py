import tkinter as tk
from tkinter import filedialog, messagebox
#from MCAparser import ppv_report as mcap
from PPVLoopsParser import LogsPTC as ptc

class PTCReportGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PPV Loops Parser")
        self.root.geometry("650x290")  # Set fixed size for the window
        self.root.resizable(False, False)  # Disable resizing

        # Bucket
        self.name_label = tk.Label(root, text="Bucket:")
        self.name_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.name_entry = tk.Entry(root)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # Week
        self.week_label = tk.Label(root, text="Week:")
        self.week_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.week_entry = tk.Entry(root)
        self.week_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Key
        self.key_label = tk.Label(root, text="Sequence:\nDefault (100)")
        self.key_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.key_entry = tk.Entry(root)
        self.key_entry.insert(0, "100")
        self.key_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Source File
        self.output_file_label = tk.Label(root, text="Output File:")
        self.output_file_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.output_entry = tk.Entry(root, width=75)
        self.output_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew", columnspan=2)
        self.source_file_button = tk.Button(root, text="Browse", command=self.browse_output)
        self.source_file_button.grid(row=3, column=3, padx=10, pady=5)

        # Report
        self.report_label = tk.Label(root, text="Loops Folder:")
        self.report_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.report_entry = tk.Entry(root, width=75)
        self.report_entry.grid(row=4, column=1, padx=10, pady=5, sticky="ew", columnspan=2)
        self.report_button = tk.Button(root, text="Browse", command=self.browse_report)
        self.report_button.grid(row=4, column=3, padx=10, pady=5)

        # Zipfile
        self.zipfile_var = tk.BooleanVar(value=False)
        self.zipfile_check = tk.Checkbutton(root, text="zipfile", variable=self.zipfile_var)
        self.zipfile_check.grid(row=5, columnspan=1, padx=10, pady=5)

        # format
        self.dpmb_var = tk.BooleanVar(value=False)
        self.dpmb_check = tk.Checkbutton(root, text="Pysv logging", variable=self.dpmb_var)
        self.dpmb_check.grid(row=6, columnspan=1, padx=10, pady=5)

        # Overview
        #self.overview_var = tk.BooleanVar(value=True)
        #self.overview_check = tk.Checkbutton(root, text="Overview", variable=self.overview_var)
        #self.overview_check.grid(row=5, column=1, columnspan=3, padx=10, pady=5)


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
        print(f'\tUsing Configuration:')
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