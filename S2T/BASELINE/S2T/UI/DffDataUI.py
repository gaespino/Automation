import tkinter as tk
from tkinter import filedialog, messagebox
import sys
import os

#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

#from GNRDffDataCollector import run
class DFFUI:
    def __init__(self, root, collector):
        self.root = root
        self.collector = collector
        self.root.title("DFF Data Collector -- Unit VMIN")

        self.products_list = ['GNR', 'CWF']
        
        # Updates product variables 
        tk.Label(root, text="Product:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.product_var = tk.StringVar(value="GNRAP")
        tk.OptionMenu(root, self.product_var, "GNRAP", "GNRSP", "CWFAP", "CWFSP").grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # Create and place the widgets
        tk.Label(root, text="VID:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.vid_entry = tk.Entry(root, width=50)
        self.vid_entry.grid(row=1, column=1, padx=10, pady=5)
        tk.Button(root, text="Browse", command=self.browse_file).grid(row=1, column=2, padx=10, pady=5)

        tk.Label(root, text="Option:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.option_var = tk.StringVar(value="uncore")
        tk.OptionMenu(root, self.option_var, "core", "uncore").grid(row=2, column=1, padx=10, pady=5, sticky="w")

        tk.Label(root, text="Output File:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.output_entry = tk.Entry(root, width=50)
        self.output_entry.grid(row=3, column=1, padx=10, pady=5)
        tk.Button(root, text="Save As", command=self.save_file).grid(row=3, column=2, padx=10, pady=5)

        tk.Label(root, text="Flow:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        self.flow_var = tk.StringVar(value="hot")
        tk.OptionMenu(root, self.flow_var, "hot", "cold", "all").grid(row=4, column=1, padx=10, pady=5, sticky="w")

        tk.Button(root, text="Start Data Collection", command=self.start_data_collection).grid(row=4, column=0, columnspan=3, pady=20)
        
    def start_data_collection(self):
        vid = self.vid_entry.get()
        option = self.option_var.get()
        output = self.output_entry.get()
        flow = self.flow_var.get()
        config = self.product_var.get()
        product = None
        for p in self.products_list:
            if p in config:
                product = p
                print(f' Using Product Configuration for {p}')
                break


        if flow == 'all':
            flows = 'all'
        else:
            flows = flow.lower()
        
        self.collector.update_product(product, config)
        self.collector.run(flows, option, vid, output, skipfused = True)
        self.root.destroy()
    
    def browse_file(self):
        filename = filedialog.askopenfilename()
        self.vid_entry.delete(0, tk.END)
        self.vid_entry.insert(0, filename)

    def save_file(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx")
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, filename)

def callUI(collector):
    # Create the main window
    root = tk.Tk()
    app = DFFUI(root, collector)
    root.mainloop()

def callCollector():
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import DffDataCollector as gdc
    collector = gdc.datacollector()
    return collector

if __name__ == "__main__":
    #debug = True
    collector = callCollector()
    root = tk.Tk()
    app = DFFUI(root, collector)
    root.mainloop()

