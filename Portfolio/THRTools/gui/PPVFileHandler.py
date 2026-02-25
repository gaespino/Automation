import sys
import os
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import tkinter as tk
    from tkinter import filedialog, ttk, messagebox
    _TKINTER_AVAILABLE = True
except ImportError:
    _TKINTER_AVAILABLE = False
#from MCAparser import ppv_report as mcap

try:
    from ..utils import PPVReportMerger as prm
except ImportError:
    try:
        _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if _parent not in sys.path:
            sys.path.insert(0, _parent)
        from utils import PPVReportMerger as prm
    except ImportError:
        prm = None

class FileHandlerGUI:
    def __init__(self, root, default_product="GNR"):
        #super().__init__()
        self.root = root
        self.default_product = default_product  # Store default product
        self.root.title("File Handler - Merge / Append Report Data")
        self.root.geometry("750x350")  # Increased size for better layout
        self.root.resizable(True, True)  # Allow resizing

        # Configure grid weights for responsive design
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Header frame with color accent
        header_frame = tk.Frame(self.root, bg='#f39c12', height=12)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)

        self.sources = ['Merge', 'Append']

        # Main container
        main_container = tk.Frame(self.root)
        main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        main_container.rowconfigure(2, weight=1)
        main_container.columnconfigure(0, weight=1)

        # Title section
        title_frame = tk.LabelFrame(main_container, text="File Operations",
                                    font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Mode Selection
        tk.Label(title_frame, text="Operation Mode:", font=("Segoe UI", 9)).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.source = ttk.Combobox(title_frame, values=self.sources, width=15, state="readonly", font=("Segoe UI", 9))
        self.source.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.source.bind("<<ComboboxSelected>>", self.update_source)

        # Mode description
        self.mode_desc_label = tk.Label(title_frame, text="Select an operation mode to begin",
                                       font=("Segoe UI", 8), fg='#7f8c8d', wraplength=600, justify="left")
        self.mode_desc_label.grid(row=1, column=0, columnspan=3, padx=5, pady=(0, 5), sticky='w')

        # Configuration section
        config_frame = tk.LabelFrame(main_container, text="Configuration",
                                     font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        config_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)

        # Source Folder/File
        self.folder_label = tk.Label(config_frame, text="Source:", font=("Segoe UI", 9))
        self.folder_label.grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.folder_entry = tk.Entry(config_frame, width=75, state=tk.DISABLED, font=("Segoe UI", 9))
        self.folder_entry.grid(row=0, column=1, padx=5, pady=8, sticky="ew")
        self.folder_button = tk.Button(config_frame, text="Browse", command=self.browse_destination_file,
                                       state=tk.DISABLED, bg="#3498db", fg="white", font=("Segoe UI", 8, "bold"),
                                       padx=15, relief=tk.FLAT, cursor="hand2")
        self.folder_button.grid(row=0, column=2, padx=5, pady=8)

        # Target File
        self.target_file_label = tk.Label(config_frame, text="Target:", font=("Segoe UI", 9))
        self.target_file_label.grid(row=1, column=0, padx=5, pady=8, sticky="w")
        self.target_file_entry = tk.Entry(config_frame, width=75, state=tk.DISABLED, font=("Segoe UI", 9))
        self.target_file_entry.grid(row=1, column=1, padx=5, pady=8, sticky="ew")
        self.target_file_button = tk.Button(config_frame, text="Browse", command=self.browse_output,
                                           state=tk.DISABLED, bg="#3498db", fg="white", font=("Segoe UI", 8, "bold"),
                                           padx=15, relief=tk.FLAT, cursor="hand2")
        self.target_file_button.grid(row=1, column=2, padx=5, pady=8)

        # File Keyword (for merge mode)
        self.file_keyword = tk.Label(config_frame, text="File Prefix:", font=("Segoe UI", 9))
        self.file_keyword.grid(row=2, column=0, padx=5, pady=8, sticky="w")
        self.file_keyword_entry = tk.Entry(config_frame, width=75, state=tk.DISABLED, font=("Segoe UI", 9))
        self.file_keyword_entry.grid(row=2, column=1, padx=5, pady=8, sticky="ew", columnspan=2)

        # Add tooltip
        self.add_tooltip(self.file_keyword_entry, "Optional: Filter files by prefix (e.g., 'Summary_', 'Report_')")

        # Action buttons
        button_frame = tk.Frame(main_container)
        button_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        button_frame.columnconfigure(0, weight=1)

        btn_container = tk.Frame(button_frame)
        btn_container.pack(side="right")

        # Submit Button
        self.submit_button = tk.Button(btn_container, text="Process Files", command=self.submit,
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
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, file_path)

    def browse_output(self):
        if self.source.get() == 'Append': file_path = filedialog.askopenfilename()
        else: file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        self.target_file_entry.delete(0, tk.END)
        self.target_file_entry.insert(0, file_path)

    def browse_destination_file(self):
        if self.source.get() == 'Append': file_path = filedialog.askopenfilename()
        else: file_path = filedialog.askdirectory()
        self.folder_entry.delete(0, tk.END)
        self.folder_entry.insert(0, file_path)


    def update_source(self, event):
        """Update UI based on selected operation mode"""
        select = self.source.get()
        self.target_file_entry.config(state=tk.NORMAL)
        self.target_file_button.config(state=tk.NORMAL)
        self.folder_entry.config(state=tk.NORMAL)
        self.folder_button.config(state=tk.NORMAL)

        if select == 'Append':
            self.target_file_label.config(text='Target File:')
            self.folder_label.config(text='Source File:')
            self.file_keyword_entry.config(state=tk.DISABLED)
            self.file_keyword.config(fg='#bdc3c7')
            self.mode_desc_label.config(text="Append mode: Add data from source file to existing target file")
        else:
            self.target_file_label.config(text='Output File:')
            self.folder_label.config(text='Source Directory:')
            self.file_keyword_entry.config(state=tk.NORMAL)
            self.file_keyword.config(fg='#000000')
            self.mode_desc_label.config(text="Merge mode: Combine multiple Excel files from directory into single output file")

    def submit(self):
        data = {
        'Source' : self.folder_entry.get(),
        'Target' : self.target_file_entry.get(),
        'Mode' : self.source.get(),
        'Prefix': rf'{self.file_keyword_entry.get()}' if self.file_keyword_entry.get() != '' else None
        #overview = self.overview_var.get()
        }
        self.header(data)
        # ['Merge', 'Append', 'RawMerge']
        if data['Mode'] == 'Append':
            prm.append_excel_tables(source_file=data['Source'], target_file=data['Target'], sheet_names=prm.sheet_names)
        #elif data['Mode'] == 'Merge':
        #    prm.merge_specific_tables(input_folder=data['Source'], output_file=data['Target'], sheet_names=prm.sheet_names )
        elif data['Mode'] == 'Merge':
            prm.merge_excel_files(input_folder=data['Source'], output_file=data['Target'], prefix = data['Prefix'])

        # You can add your logic here to handle the submitted data
        #messagebox.showinfo("Submitted Data", f"Bucket: {data['bucket']}\nWeek: {data['week']}\nSequence Key: {keyEntry}\nSave File: {data['output_file']}\nLoops Folder: {data['report']}\nPythonSV Format: {data['dpmb']}\nZipFile: {data['zfile']}\n --")
        # Copy the template file to the new target file
        #PPVLoops = ptc(StartWW = data['week'], bucket = data['bucket'], LotsSeqKey = keyEntry, folder_path=data['report'], output_file=data['output_file'], zipfile=data['zfile'], dpmbformat=data['dpmb'])
        #self.header(data)
        #PPVLoops.run()

        #root.quit()
    def header(self, data):
        print(f' {"#"*120}\n')
        print(f'\t{"-"*10} PPV File Handler {"-"*10}')
        print(f'\tNew file will be saved at: {data["Target"]}\n')
        print('\tUsing Configuration:')
        #print(f'\tvpos:   \t{vpo}')
        print(f'\tMode:   \t\t{data["Mode"]}')
        print(f'\tSource:   \t{data["Source"]}')
        print(f'\tTarget: \t\t{data["Target"]}')
        print(f'\tKeyword:   \t{data["Prefix"]}')
        print(f'\n{"#"*120}')
        print(f'{"#"*120}\n')
        print(f'\t{"-"*10} Processing data... Please wait.. {"-"*10} \n')

if __name__ == "__main__":
    root = tk.Tk()
    app = FileHandlerGUI(root)
    root.mainloop()
