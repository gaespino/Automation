import tkinter as tk
from tkinter import filedialog, ttk, messagebox
#from MCAparser import ppv_report as mcap
import PPVReportMerger as prm

class FileHandlerGUI:
    def __init__(self, root):
        #super().__init__()
        self.root = root
        self.root.title("Report Tools - Merge / Append Report Data")
        self.root.geometry("650x190")  # Set fixed size for the window
        self.root.resizable(False, False)  # Disable resizing
        self.sources = ['Merge', 'Append', 'RawMerge']
        # Bucket
        #self.name_label = tk.Label(root, text="Bucket:")
        #self.name_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        #self.name_entry = tk.Entry(root)
        #self.name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")


        # Modes
        self._source = tk.Label(root, text="Mode:")
        self._source.grid(row=0, column=0, pady=10, sticky='e')
        self.source = ttk.Combobox(root, values=self.sources, width=10, state=tk.NORMAL)

        self.source.grid(row=0, column=1, pady=10, sticky='w')
        self.source.bind("<<ComboboxSelected>>", self.update_source)

        # Destination File
        self.target_file_label = tk.Label(root, text="Output File:")
        self.target_file_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.target_file_entry = tk.Entry(root, width=75, state=tk.DISABLED)
        self.target_file_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew", columnspan=2)
        self.target_file_button = tk.Button(root, text=" Browse ", command=self.browse_destination_file, state=tk.DISABLED)
        self.target_file_button.grid(row=1, column=3, padx=10, pady=5)

        # Source Folder
        self.folder_label = tk.Label(root, text="Source Folder:")
        self.folder_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.folder_entry = tk.Entry(root, width=75, state=tk.DISABLED)
        self.folder_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew", columnspan=2)
        self.folder_button = tk.Button(root, text=" Browse ", command=self.browse_output, state=tk.DISABLED)
        self.folder_button.grid(row=2, column=3, padx=10, pady=5)

        # Submit Button
        self.submit_button = tk.Button(root, text="Submit", command=self.submit)
        self.submit_button.grid(row=3, column=2, padx=1, pady=10, sticky="e")

        # Close Button
        self.close_button = tk.Button(root, text="Close", command=root.destroy)
        self.close_button.grid(row=3, column=3, padx=10, pady=10, sticky="e")

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
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, file_path)
    
    def browse_output(self):
        if self.source.get() == 'Append': file_path = filedialog.askopenfilename()
        else: file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, file_path)

    def browse_destination_file(self):
        if self.source.get() == 'Append': file_path = filedialog.askopenfilename()
        else: file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        self.target_file_entry.delete(0, tk.END)
        self.target_file_entry.insert(0, file_path)


    def update_source(self, event):
        # Print Selection on screen

        select = self.source.get()
        self.target_file_entry.config(state=tk.NORMAL)
        self.target_file_button.config(state=tk.NORMAL)
        self.folder_entry.config(state=tk.NORMAL)
        self.folder_button.config(state=tk.NORMAL)

        if select == 'Append':
            self.target_file_label.config(text='Target File:')
            self.folder_label.config(text='Source File:')
        else:
            self.target_file_label.config(text='Output File:')
            self.folder_label.config(text='Source Directory:')

    def submit(self):
        data = {
        'Source' : self.folder_entry.get(),
        'Target' : self.target_file_entry.get(),
        'Mode' : self.source.get(),

        #overview = self.overview_var.get()
        }
        
        # ['Merge', 'Append', 'RawMerge']
        if data['Mode'] == 'Append':
            prm.append_excel_tables(source_file=data['Source'], target_file=data['Target'], sheet_names=prm.sheet_names)
        elif data['Mode'] == 'Merge':
            prm.merge_specific_tables(input_folder=data['Source'], output_file=data['Target'], sheet_names=prm.sheet_names )
        elif data['Mode'] == 'RawMerge':
            prm.merge_excel_files(input_folder=data['Source'], output_file=data['Target'])

        # You can add your logic here to handle the submitted data
        #messagebox.showinfo("Submitted Data", f"Bucket: {data['bucket']}\nWeek: {data['week']}\nSequence Key: {keyEntry}\nSave File: {data['output_file']}\nLoops Folder: {data['report']}\nPythonSV Format: {data['dpmb']}\nZipFile: {data['zfile']}\n --")
        # Copy the template file to the new target file
        #PPVLoops = ptc(StartWW = data['week'], bucket = data['bucket'], LotsSeqKey = keyEntry, folder_path=data['report'], output_file=data['output_file'], zipfile=data['zfile'], dpmbformat=data['dpmb'])
        #self.header(data)
        #PPVLoops.run()

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
    app = FileHandlerGUI(root)
    root.mainloop()