import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import json
import os


import ShmooReport as shr
import ItuffReport as itr

def display_banner():
    # Create the banner text
    banner_text = rf'''
=================================================================================================
   _______   ______     _____ __  ____  _______  ____     ____  ___    ____  _____ __________ 
  / ____/ | / / __ \   / ___// / / /  |/  / __ \/ __ \   / __ \/   |  / __ \/ ___// ____/ __ \
 / / __/  |/ / /_/ /   \__ \/ /_/ / /|_/ / / / / / / /  / /_/ / /| | / /_/ /\__ \/ __/ / /_/ /
/ /_/ / /|  / _, _/   ___/ / __  / /  / / /_/ / /_/ /  / ____/ ___ |/ _, _/___/ / /___/ _, _/ 
\____/_/ |_/_/ |_|   /____/_/ /_/_/  /_/\____/\____/  /_/   /_/  |_/_/ |_|/____/_____/_/ |_|  
                                                                                                   
=================================================================================================
    '''
    
    # Print the banner
    print(banner_text)


RowsConfigs = { 'Header': 0,
                'Browse TP': 1,
                'Frequency': 2,
                'product':2,
                'Group':2,
                'Content': 3,
                'Plist':4,
                'Shmoo':5,
                'ShmooSet':5,
                'ShmooRemove':5,
                'Masking':9,
                'Submit':10,
                'Cancel':11,

}

class TPConfigEditor(tk.Tk):
    def __init__(self, RowsConfigs):
        super().__init__()
        self.title("Shmoo Parser GNR")
        self.RowsConfigs = RowsConfigs
        #self.frequencies = Frequencies
        #self.dropdowns = []
        self.palette = {    'RED':'Reds','BLUE':'Blues','GREEN':'Greens', 
                            'YlGnBl':'YlGnBl', 'RdYlBu':'RdYlBu', 'COOLWARM':'coolwarm', 
                            'MAGMA':'magma', 'PLASMA':'plasma', 'INFERNO':'inferno',
                            'MAGMA':'magma', 'PLASMA':'plasma', 'INFERNO':'inferno',
                            'CIVIDS':'cividis',
                            'VIRIDIS':'viridis'}
        self.plot_option = {'ALL':'all', 'IMAGES':'img', 'EXCEL':'xls'}

        self.sources = ['VPO', 'ITUFF', 'TESTER']
        self.plot_options = [o for o in self.plot_option.keys()] #['ALL', 'IMAGES', 'EXCEL']
        self.plot_colors = [cl for cl in self.palette.keys()] #['RED', 'GREEN', 'BLUE']
        #self.plot_types = ['PARSE', 'PLOT']
        
        self.ui_config()
        self.ui_grid()
    
    def ui_config(self):
        
        self.columns = 5
        size = 25
        # Configure grid columns
        for column in range(self.columns):
            self.grid_columnconfigure(column, minsize=size, pad=10)

        # Set last column
        self.grid_columnconfigure(self.columns, minsize=10, pad=10)

        # Row 0 - Title
        tk.Label(self, text="GNR - Shmoo Parser UI", font=("Arial", 16)).grid(row=0, column=0, columnspan=self.columns+1, pady=10)
        
        # Labels
        self._browse =  tk.Label(self, text="Folder:")
        
        self._filename = tk.Label(self, text="Report Name:")
        self._vpos = tk.Label(self, text="VPO Numbers: \n (comma split)")
        self._source = tk.Label(self, text="Source:")
        self._plt_opt = tk.Label(self, text="Option:")
        self._plt_color = tk.Label(self, text="Colors:")
        self.plt_Info = tk.Label(self, text="Plot Configuration:")


        # Entries 
        self.shmoo_path = tk.Entry(self, width=100, justify="left") # Browse TP
        self.filename_entry = tk.Entry(self, width=100, state=tk.DISABLED)
        self.VPO_entry = tk.Entry(self, width=100, state=tk.DISABLED)

        # Buttons
        self.browse_button = tk.Button(self, text="Browse", width=10, command=self.browse_directory) # Browse TP
        self._submit = tk.Button(self, text="Submit", width=10, command=self.submit)
        self._quit = tk.Button(self, text="Cancel", width=10, command=self.quit)

        # ComboBox
        self.source = ttk.Combobox(self, values=self.sources, width=10, state=tk.DISABLED)
        self.plt_opt = ttk.Combobox(self, values=self.plot_options, width=10, state=tk.DISABLED)
        self.plt_color = ttk.Combobox(self, values=self.plot_colors, width=10, state=tk.DISABLED)
        self.plt_color.set('RED')
        self.plt_opt.set('ALL')
        #self.plt_type = ttk.Combobox(self, values=[], width=20, state=tk.DISABLED)

        #Lists
        #self.content_info = tk.Listbox(self, selectmode=tk.EXTENDED, width=75, height=4, state=tk.DISABLED)


        #Checks
        self.plt_check = tk.IntVar(value=True)
        self._plt_check = tk.Checkbutton(self, text="Plot", width=10, variable=self.plt_check, state=tk.DISABLED, command=self.toggle_plot)

        # Texts
        #self.plot_info = tk.Text(self, width=50, height=10, state=tk.DISABLED)
        

        # Configurations
        # Binds the Group selection based on product selection
        self.source.bind("<<ComboboxSelected>>", self.update_source)
        self.plt_opt.bind("<<ComboboxSelected>>", self.on_combobox_select)
        self.plt_color.bind("<<ComboboxSelected>>", self.on_combobox_select)

    def ui_grid(self):
        # Grid configs
        # Row 1 - Browse TP
        self._browse.grid(row=1, column=0, sticky='e')
        self.shmoo_path.grid(row=1, column=1, columnspan=4, sticky='w')
        self.browse_button.grid(row=1, column=5, padx=10, sticky='e')
        
        # Row 2 - Frequency, Product, Group
        self._filename.grid(row=2, column=0, sticky='e')
        self.filename_entry.grid(row=2, column=1, columnspan=4, sticky='w')
        self._plt_check.grid(row=2, column=5, sticky='w', pady=10)

        # Separator before Shmoo
        ttk.Separator(self, orient='horizontal').grid(row=3, column=0, columnspan=self.columns+1, sticky='ew', pady=10)
          

        # Row 4 - Frequency, Product, Group
        self._source.grid(row=4, column=0, pady=10, sticky='e')
        self.source.grid(row=4, column=1, pady=10, sticky='w')
        
 
        self._vpos.grid(row=5, column=0, pady=10, sticky='e')
        self.VPO_entry.grid(row=5, column=1, columnspan=4, pady=10, sticky='w')


         
        # Separator before Shmoo
        ttk.Separator(self, orient='horizontal').grid(row=6, column=0, columnspan=self.columns+1, sticky='ew', pady=10)
          
    
        # Row 6 - Content Selection
  
        self.plt_Info.grid(row=7, column=0, sticky='e', pady=10)
        self._plt_opt.grid(row=7, column=1, sticky='e', pady=10)
        self.plt_opt.grid(row=7, column=2, pady=10, sticky='w')

        self.plt_color.grid(row=7, column=3, sticky='w', pady=10)
        self._plt_color.grid(row=7, column=2, pady=10, sticky='e')

        # Separator before Shmoo
        ttk.Separator(self, orient='horizontal').grid(row=8, column=0, columnspan=self.columns+1, sticky='ew', pady=10)
 
        # Row 10 - Submit and Cancel buttons
        self._submit.grid(row=9, column=5,padx=10,  sticky='e')
        self._quit.grid(row=9, column=4,padx=10,  sticky='w')

        # Separator after Save Array
        ttk.Separator(self, orient='horizontal').grid(row=10, column=0, columnspan=self.columns+1, sticky='ew', pady=10)

    def update_source(self, event):
        # Print Selection on screen
        self.on_combobox_select(event)

        select = self.source.get()
        if select == 'VPO':
            self.VPO_entry.config(state=tk.NORMAL)
        else:
            self.VPO_entry.config(state=tk.DISABLED)


    def on_combobox_select(self, event):
        # This function will be called when a combobox selection is made
        selected_value = event.widget.get()
        print(f"Selected: {selected_value}")

    def on_listbox_select(self, event, listbox):
        # This function will be called when a listbox selection is made
        selected_indices = listbox.curselection()
        selected_values = [listbox.get(i) for i in selected_indices]
        print(f"Selected: {selected_values}")

    def browse_directory(self):
        self.shmoo_path.delete(0, tk.END)
        self.directory = filedialog.askdirectory()
        if self.directory:
            self.shmoo_path.insert(0, self.directory)
            self.filename_entry.config(state=tk.NORMAL)
            self.source.config(state=tk.NORMAL)
            self._plt_check.config(state=tk.NORMAL)
            self.toggle_plot()

    def toggle_plot(self):
        if self.plt_check.get():
            self.plt_opt.config(state=tk.NORMAL)
            self.plt_color.config(state=tk.NORMAL)
        else:
            self.plt_opt.config(state=tk.DISABLED)
            self.plt_color.config(state=tk.DISABLED)

    def read_ui(self):
        # Gather all the selected/entered data
        ituff_vpos = self.VPO_entry.get().replace(" ","").split(",")
        
        data = {
            "Log": self.shmoo_path.get(),
            "Source": self.source.get().lower(),
            "Plot Option": self.plot_option[self.plt_opt.get()] if self.plt_check.get() else '',
            "Plot Colors": self.palette[self.plt_color.get()] if self.plt_check.get() else None,
            "Name": self.filename_entry.get(),
            "VPOS": ituff_vpos if self.source.get() == 'VPO' else None,
            "type": 'parse' if self.plt_check.get() else ''
        }


        return data

    def submit(self):
        data = self.read_ui()
        # Here you can add the logic to handle the gathered data
        print('Used configuration', json.dumps(data, indent=1))  # For demonstration purposes, printing the data
       # print('Used configuration', json.dumps(data_evg, indent=1))
        messagebox.showinfo("Submitted", "Configuration submitted successfully!")

        if data['Source'].lower() == 'vpo':
            itr.ui_run(dest=data['Log'], vpo=data['VPOS'], plt_opt=data['Plot Option'], palette=data["Plot Colors"], filetype=data["type"], filename=data['Name'], source="ituff_gnr", axisfix= "auto")
        elif data['Source'].lower() == 'tester':
            shr.ui_run(path=data['Log'], plt_opt=data['Plot Option'], palette=data["Plot Colors"], filetype=data["type"], filename=data['Name'], source="gnr", axisfix= "auto")
        elif data['Source'].lower() == 'ituff':
            shr.ui_run(path=data['Log'], plt_opt=data['Plot Option'], palette=data["Plot Colors"], filetype=data["type"], filename=data['Name'], source="ituff_gnr", axisfix= "auto")

if __name__ == "__main__":
    display_banner()
    app = TPConfigEditor(RowsConfigs=RowsConfigs)
    app.mainloop()