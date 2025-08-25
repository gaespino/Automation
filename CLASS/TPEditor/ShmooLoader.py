import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import json
import os


from GNRSetShmooInstance import jsonfinder as shmoos
from GNRSetShmooInstance import class_instances as instances
from GNRSetShmooInstance import fungroup as functional
from GNRSetShmooInstance import TPEdit
import ShmooInstances as shi

#directory = r'I:\intel\engineering\dev\user_links\gaespino\GNR\GNRSVXXXXHXRG00S420\Modules\FUN_UNCORE_COMP\InputFiles'
#file = shmoos(directory)



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
        self.title("TP Configuration Editor")
        self.RowsConfigs = RowsConfigs
        #self.frequencies = Frequencies
        self.dropdowns = []

        self.ShmooConfigs = shi.Configuration_dict()

        self.Frequencies = {key:value['Freq'] for key, value in self.ShmooConfigs.items()}
        self.func_groups = [key for key in self.ShmooConfigs.keys()]
        self.group_products = {g:[p for p in self.ShmooConfigs[g]['Products'].keys()] for g in self.ShmooConfigs.keys()}
        self.TPPath = "/Shared/Common/TPLOAD"
        self.ConfigJSON = "DPMTPConfiguration.json"
        self.ConfigPY = "GNRTPEdit.py"
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.files_dir = os.path.join(self.base_dir, 'TPFiles')
        self.JSONloc = os.path.join(self.files_dir, self.ConfigJSON)
        self.EditPYloc = os.path.join(self.files_dir, self.ConfigPY)
        
        shi.configSave(selection=None, config=None, savefile=self.JSONloc, clear=True)
        print('Functional Groups:', self.func_groups)
        print('Frequencies:', self.Frequencies)
        print('Group Products:', self.group_products)

        self.ui_config()
    
    def ui_config(self):
        
        columns = 5
        size = 25
        # Configure grid columns
        for column in range(columns):
            self.grid_columnconfigure(column, minsize=size, pad=10)

        # Set last column
        self.grid_columnconfigure(columns, minsize=10, pad=10)
        
        #self.grid_columnconfigure(0, minsize=50)
        #self.grid_columnconfigure(1, minsize=60)
        #self.grid_columnconfigure(2, minsize=60)
        #self.grid_columnconfigure(3, minsize=60)
        #self.grid_columnconfigure(4, minsize=60)

        # Row 0 - Title
        tk.Label(self, text="Test Program Configuration Editor", font=("Arial", 16)).grid(row=0, column=0, columnspan=columns+1, pady=10)
        
        # Labels
        self._browse =  tk.Label(self, text="Browse TP:")
        self._frequency = tk.Label(self, text="Frequency:")
        self._product = tk.Label(self, text="Product:")
        self._group = tk.Label(self, text="Group:")
        self._savecfg = tk.Label(self, text="Test Config:")
        self._content = tk.Label(self, text="Content:")
        self._Plist = tk.Label(self, text="Plist:")
        self._ShmooSection = tk.Label(self, text="Shmoo Configuration:")


        # Entries 
        self.tp_path = tk.Entry(self, width=100, justify="left") # Browse TP
        self.plist_entry = tk.Entry(self, width=100, state=tk.DISABLED)

        # Buttons
        browse_button = tk.Button(self, text="Browse", width=10, command=self.browse_directory) # Browse TP
        self._submit = tk.Button(self, text="Submit", width=10, command=self.submit)
        self._quit = tk.Button(self, text="Cancel", width=10, command=self.quit)
        self._savebutton = tk.Button(self, text="Save Test", width=10, command=self.savedata)

        # ComboBox
        self.frequency = ttk.Combobox(self, values=[], width=3, state=tk.DISABLED)
        self.product = ttk.Combobox(self, values=[], width=8, state=tk.DISABLED)
        self.group = ttk.Combobox(self, values=self.func_groups, width=8, state=tk.DISABLED)
        self.content = ttk.Combobox(self, values=[], width=20, state=tk.DISABLED)
        self.shmoo_list = ttk.Combobox(self, values=[], width=20, state=tk.DISABLED)
        self.savecfg = ttk.Combobox(self, values=['NONE','Config1','Config2','Config3'], width=8)
        self.savecfg.set('NONE')
        #Lists

        self.content_info = tk.Listbox(self, selectmode=tk.EXTENDED, width=75, height=4, state=tk.DISABLED)


        # Dropdown Lists
        self.var_fca = tk.StringVar(self, value='NONE')
        self.list_fca = ttk.OptionMenu(self, self.var_fca, 'NONE')
        self.list_fca.config(state="disabled")
        self.list_fca.variable = self.var_fca

        self.var_fcb = tk.StringVar(self, value='NONE')
        self.list_fcb = ttk.OptionMenu(self, self.var_fcb, 'NONE')
        self.list_fcb.config(state="disabled")
        self.list_fcb.variable = self.var_fcb

        self.var_fcc = tk.StringVar(self, value='NONE')
        self.list_fcc = ttk.OptionMenu(self, self.var_fcc, 'NONE')
        self.list_fcc.config(state="disabled")
        self.list_fcc.variable = self.var_fcc

        self.var_fcd = tk.StringVar(self, value='NONE')
        self.list_fcd = ttk.OptionMenu(self, self.var_fcd, 'NONE')
        self.list_fcd.config(state="disabled")
        self.list_fcd.variable = self.var_fcd
        
        self.dropdowns.append(self.list_fca)
        self.dropdowns.append(self.list_fcb)
        self.dropdowns.append(self.list_fcc)
        self.dropdowns.append(self.list_fcd)

        #Checks
        self.plist_check = tk.IntVar()
        self._plist_check = tk.Checkbutton(self, text="Plist", variable=self.plist_check, command=self.toggle_plist)
        
        self.shmoo_check = tk.IntVar()
        self._shmoo_check = tk.Checkbutton(self, text="Enable", variable=self.shmoo_check, command=self.toggle_shmoo)

        self.shmoo_remove_check = tk.IntVar()
        self._shmoo_remove_check =tk.Checkbutton(self, text="Remove from instance", variable=self.shmoo_remove_check)

        self.checkbox_fca = tk.BooleanVar(value=False)
        self._checkbox_fca = tk.Checkbutton(self, text="FCTrackingA : ", variable=self.checkbox_fca, onvalue=True, offvalue=False,
                                    command= lambda var=self.checkbox_fca, fclist=self.list_fca: self.toggle_fctracks(var, fclist))

        self.checkbox_fcb = tk.BooleanVar(value=False)
        self._checkbox_fcb = tk.Checkbutton(self, text="FCTrackingB : ", variable=self.checkbox_fcb, onvalue=True, offvalue=False,
                                    command= lambda var=self.checkbox_fcb, fclist=self.list_fcb: self.toggle_fctracks(var, fclist))
        
        self.checkbox_fcc = tk.BooleanVar(value=False)
        self._checkbox_fcc = tk.Checkbutton(self, text="FCTrackingC : ", variable=self.checkbox_fcc, onvalue=True, offvalue=False,
                                    command= lambda var=self.checkbox_fcc, fclist=self.list_fcc: self.toggle_fctracks(var, fclist))
        
        self.checkbox_fcd = tk.BooleanVar(value=False)
        self._checkbox_fcd = tk.Checkbutton(self, text="FCTrackingD : ", variable=self.checkbox_fcd, onvalue=True, offvalue=False,
                                    command= lambda var=self.checkbox_fcd, fclist=self.list_fcd: self.toggle_fctracks(var, fclist))

        # Texts
        self.shmoo_info = tk.Text(self, width=50, height=10, state=tk.DISABLED)
        

        # Configurations
        # Binds the Group selection based on product selection
        self.group.bind("<<ComboboxSelected>>", self.update_prod_selection)
        

        # Binds the freq and product selection to change displayed content
        self.product.bind("<<ComboboxSelected>>", self.update_content_selection)
        self.frequency.bind("<<ComboboxSelected>>", self.update_content_selection)

        # Binds the Shmoo List to appear once there is something selected
        self.shmoo_list.bind("<<ComboboxSelected>>", self.display_shmoo_info)

        # Binds the Content List to appear once there is something selected
        self.content.bind("<<ComboboxSelected>>", self.display_content_info)

        #self.group.bind("<<ComboboxSelected>>", self.on_combobox_select)
        #self.product.bind("<<ComboboxSelected>>", self.on_combobox_select)
        #self.frequency.bind("<<ComboboxSelected>>", self.on_combobox_select)
        #self.shmoo_list.bind("<<ComboboxSelected>>", self.on_combobox_select)
        #self.content.bind("<<ComboboxSelected>>", self.on_combobox_select)


        # Grid configs
        # Row 1 - Browse TP
        self._browse.grid(row=1, column=0, sticky='e')
        self.tp_path.grid(row=1, column=1, columnspan=4, sticky='w')
        browse_button.grid(row=1, column=5, padx=10, sticky='e')

        # Row 2 - Frequency, Product, Group
        self._frequency.grid(row=2, column=2, pady=10, sticky='e', padx=(100, 0))
        self.frequency.grid(row=2, column=3, pady=10, sticky='w')

        self._product.grid(row=2, column=1, sticky='e', pady=10 ,padx=(100, 0))
        self.product.grid(row=2, column=2, pady=10, sticky='w')

        self._group.grid(row=2, column=0, sticky='e', pady=10)
        self.group.grid(row=2, column=1, pady=10, sticky='w')

        
        # Row 3 - Content Selection
        self._content.grid(row=3, column=0, pady=10, sticky='e')
        self.content.grid(row=3, column=1, columnspan=2, pady=10, sticky='w')
        self.content_info.grid(row=3, column=2, columnspan=3, sticky='e')
        
        # Row 4 - Plist
        self._plist_check.grid(row=4, column=0, pady=10, sticky='e')
        self.plist_entry.grid(row=4, column=1, columnspan=4, pady=10, sticky='w')
        
        
        # Separator before Shmoo
        ttk.Separator(self, orient='horizontal').grid(row=5, column=0, columnspan=columns+1, sticky='ew', pady=10)
          
        # Row 5 - Shmoo
        self._ShmooSection.grid(row=6, column=1, padx=10, pady=10, sticky='w')      # Shmoo Section Text
        self._shmoo_check.grid(row=6, column=2, sticky='w')                         # Shmoo Enable Checkbox
        self._shmoo_remove_check.grid(row=6, column=3, sticky='w')                  # Shmoo Remove Check
        self.shmoo_list.grid(row=7, column=1, columnspan=1, sticky='nw')             # Shmoo List
        self.shmoo_info.grid(row=7, column=2, columnspan=2, sticky='e')             # Shmoo Info Box


        
        # Separator before Masking
        ttk.Separator(self, orient='horizontal').grid(row=8, column=0, columnspan=columns+1, sticky='ew', pady=10)
                
        # Row 9,10 - Masking
        #self.fctrackdrop()
        self.list_fca.grid(row=9, column=1, columnspan=2, sticky='w')
        self.list_fcb.grid(row=10, column=1, columnspan=2, sticky='w')
        self.list_fcc.grid(row=9, column=3, columnspan=2, sticky='w')
        self.list_fcd.grid(row=10, column=3, columnspan=2, sticky='w')
        
        self._checkbox_fca.grid(row=9, column=0, sticky='e')
        self._checkbox_fcb.grid(row=10, column=0, sticky='e')
        self._checkbox_fcc.grid(row=9, column=2, sticky='e')
        self._checkbox_fcd.grid(row=10, column=2, sticky='e')
        #tk.Label(self, text="Masking:").grid(row=6, column=0, sticky='e')
        #self.masking = ttk.Combobox(self, values=self.load_masking_data())
        #self.masking.grid(row=6, column=1, columnspan=2, sticky='w')
        
        # Separator after Masking
        ttk.Separator(self, orient='horizontal').grid(row=11, column=0, columnspan=columns+1, sticky='ew', pady=10)
                
        # Row 10 - Submit and Cancel buttons
        self._submit.grid(row=9, column=5,padx=10,  sticky='e')
        self._quit.grid(row=10, column=5,padx=10,  sticky='e')

        # Row 12 - Submit and Cancel buttons
        self._savebutton.grid(row=12, column=5,padx=10,  sticky='e')
        self._savecfg.grid(row=12, column=2, sticky='e', pady=10)
        self.savecfg.grid(row=12, column=3, pady=10, sticky='w')
        # Separator after Save Array
        ttk.Separator(self, orient='horizontal').grid(row=13, column=0, columnspan=columns+1, sticky='ew', pady=10)
        
    def on_combobox_select(self, event):
        # This function will be called when a combobox selection is made
        selected_value = event.widget.get()
        print(f"Selected: {selected_value}")

    def on_listbox_select(self, event, listbox):
        # This function will be called when a listbox selection is made
        selected_indices = listbox.curselection()
        selected_values = [listbox.get(i) for i in selected_indices]
        print(f"Selected: {selected_values}")

    def display_shmoo_info(self, event):
        # Print Selection on screen
        self.on_combobox_select(event)

        selected_index = self.shmoo_list.get()
        if selected_index:
            selected_key = selected_index
            shmoo_info = self.shmoo_data.get(selected_key, {})
            self.shmoo_info.config(state=tk.NORMAL)
            self.shmoo_info.delete(1.0, tk.END)
            for sh, val in shmoo_info.items():
                self.shmoo_info.insert(tk.END, f'{sh} : {val} \n')
            #self.shmoo_info.insert(tk.END, json.dumps(shmoo_info, indent=4))
            self.shmoo_info.config(state=tk.DISABLED)

    def display_content_info(self, event):
        # Print Selection on screen
        self.on_combobox_select(event)

        selected = self.content.get()
        frequency = self.frequency.get()
        product = self.product.get()
        group = self.group.get()
        #print(self.ShmooConfigs)
        
        self.cinstance = None
        clist = None
        
        if selected != 'EXTERNAL':

            idict = self.ShmooConfigs[group]['Products'][product]['Instances'][selected]
            self.cinstance = idict[frequency]
            clist = [c.split("::")[1] for c in self.cinstance]
 
        elif selected == 'EXTERNAL':

            self.cinstance = idict['FILE']
            clist = [c.split("::")[1] for c in self.cinstance]

        if clist:  

            self.content_info.config(state=tk.NORMAL)
            self.content_info.delete(0, tk.END)
            for idx, lst in enumerate(clist):
         
                self.content_info.insert(idx, lst)

    def update_dropdowns(self,selected_directory):
        function_name_dict = shmoos(selected_directory)
        options = function_name_dict.get('InitialDefeatureTracking', [])
       
        for dropdown in self.dropdowns:
            dropdown['menu'].delete(0, 'end')
            dropdown.config(state="disabled")
            for name in options:
                dropdown['menu'].add_command(label=name, command=tk._setit(dropdown.variable, name))

    def browse_directory(self):
        self.directory = filedialog.askdirectory()
        if self.directory:
            self.tp_path.insert(0, self.directory)
            self.group.config(state=tk.NORMAL)
            
    def content_directory(self, group, product):
        #func = functional(self.group.get(), self.product.get())
        func = self.ShmooConfigs[group]['Products'][product]['Configuration']
        funcpath = func['path']
        directory = os.path.join(self.directory, funcpath)
        print('Searching for TP Configurations in folder:', directory)
        if directory:
            self.update_dropdowns(directory)
            self.load_shmoo_data(directory)
           
    def toggle_dropdown(self, check_var, dropdown):
        if check_var.get():
            dropdown.config(state="normal")
        else:
            dropdown.config(state="disabled")
            dropdown.variable.set('NONE')

    def update_content_selection(self, event):
        # Print Selection on screen
        self.on_combobox_select(event)

        group = self.group.get()
        product = self.product.get()
        self.content.delete(0, tk.END)
        cdict = self.ShmooConfigs[group]['Products'][product]['Instances']
        #self.frequency.delete(0, tk.END)
        #self.product.delete(0, tk.END)
        
        if self.frequency.get() and self.product.get():
            self.content['values'] = [key for key in cdict.keys()]
            self.content.config(state=tk.NORMAL)
            self.content_directory(group, product)
        else:
            self.content.config(state=tk.DISABLED)
        #for g in self.func_groups:

    def update_prod_selection(self, event):
        # Print Selection on screen
        self.on_combobox_select(event)

        group = self.group.get()
        #self.content.delete(0, tk.END)
        self.frequency.delete(0, tk.END)
        self.product.delete(0, tk.END)
        
        self.frequency['values'] = self.Frequencies[group]
        self.product['values'] = self.group_products[group]
        self.frequency.config(state=tk.NORMAL)
        self.product.config(state=tk.NORMAL)
        #for g in self.func_groups:

    def toggle_plist(self):
        if self.plist_check.get():
            self.plist_entry.config(state=tk.NORMAL)
        else:
            self.plist_entry.config(state=tk.DISABLED)

    def toggle_fctracks(self, fclist, fctracks):
        if fclist.get():
            fctracks.config(state="normal")
        else:
            fctracks.config(state="disabled")
            fctracks.variable.set('NONE')

    def toggle_shmoo(self):
        if self.shmoo_check.get():
            self.shmoo_list.config(state=tk.NORMAL)
        else:
            self.shmoo_list.config(state=tk.DISABLED)
    
    def load_shmoo_data(self, selected_directory):
        function_name_dict = shmoos(selected_directory)
        self.shmoofile = function_name_dict.get('shmoo', [])
        sfile = os.path.join(selected_directory, self.shmoofile[0] + '.json')
        try:
            with open(sfile, "r") as file:
                self.shmoo_data = json.load(file)
                self.shmoo_list.config(state=tk.NORMAL)
                self.shmoo_list['values'] = list(self.shmoo_data.keys())
                #for idx, key in enumerate(self.shmoo_data.keys()):
                    #print(key)
                    
                    #self.shmoo_list.insert(idx, key)
                self.shmoo_list.config(state=tk.DISABLED)
        except FileNotFoundError:
            messagebox.showerror("Error", "UncoreFCShmoo.json file not found.")
    
    def load_masking_data(self):
        masking_files = []
        masking_folder = "path_to_masking_folder"  # Update this path accordingly
        if os.path.exists(masking_folder):
            for file in os.listdir(masking_folder):
                if file.endswith(".mask"):
                    masking_files.append(file)
        return masking_files
    
    def read_ui(self):
        # Gather all the selected/entered data
        masking = { 'FCTRACKINGA':self.list_fca,
                    'FCTRACKINGB':self.list_fcb,
                    'FCTRACKINGC':self.list_fcc,
                    'FCTRACKINGD':self.list_fcd,}
        
        iMasks = []
        patterns = []
        freq = self.frequency.get()
        product = self.product.get()
        group = self.group.get()
        cont = self.content.get()
        shmoo = self.shmoo_list.get() if self.shmoo_check.get() else None
        plist = self.plist_entry.get() if self.plist_check.get() else None
        tp_path = self.tp_path.get()
        #JSONloc =  self.JSONloc #os.path.join(self.files_dir, self.ConfigJSON)
        #SCRIPTloc =  self.EditPYloc #os.path.join(self.files_dir, self.ConfigPY)
        CONFIGsel = self.savecfg.get() if self.savecfg.get() != 'NONE' else None
        iDict = self.ShmooConfigs[group]['Products'][product]['FCTRACKING'][freq]#instances(freq)
        
        content = {self.content_info.get(i):i for i in self.content_info.curselection()}


        iMasks = {iDict[f'{k}_{freq}']:v.variable.get() for k, v in masking.items() if v.variable.get() != 'NONE'}
        patterns = [self.cinstance[c] for c in self.content_info.curselection()]


        data = {
            "tp_path": tp_path,
            "frequency": freq,
            "product": product,
            "group": group,
            "content": cont,
            "instance": patterns, # [self.content_info.get(i) for i in self.content_info.curselection() if i in self.cinstance],
            "plist": shmoo,
            "shmoo": plist,
            "shmoo_remove": bool(self.shmoo_remove_check.get()),
            "masking": iMasks
        }


        func = self.ShmooConfigs[group]['Products'][product]['Configuration']
        shmoopath = func['path']
        shmoofile = func['shmoo']

        ConfigFile = func['ConfigFile'] #"~HDMT_TPL_DIR/Modules/FUN_UNCORE_COMP/InputFiles/"
        fctracking = func['fctracking']
        fcFile = {k:f"{ConfigFile}{MaskFile}{fctracking}" for k, MaskFile in iMasks.items()}

        data_evg = {
            "tp_path": self.tp_path.get(),
            "frequency": freq,
            "product": product,
            "group": group,
            "content": cont,
            "instance": patterns, # [self.content_info.get(i) for i in self.content_info.curselection() if i in self.cinstance],
            "plist": plist,
            "shmoo": rf"./{shmoopath}/{shmoofile}!{shmoo}" if self.shmoo_check.get() else None,
            "shmoo_remove": bool(self.shmoo_remove_check.get()),
            "masking": fcFile
        }

        return data, data_evg, CONFIGsel

    def submit(self):
        data, data_evg, CONFIGsel = self.read_ui()
        # Here you can add the logic to handle the gathered data
        print('Used configuration', json.dumps(data, indent=1))  # For demonstration purposes, printing the data
        print('Used configuration', json.dumps(data_evg, indent=1))
        messagebox.showinfo("Submitted", "Configuration submitted successfully!")       

        # Calls the editor for the selected configuration
        tp = TPEdit(selection=data['group'], product=data['product'], verif=True)
        

        #if data['plist']:
        #    print('Modifying plist for selected instances: ', data['instance'])
        #    tp.ContentChange(plist=data['plist'],instances=data['instance'])


        #if data['shmoo'] and not data['shmoo_remove']:
        #    print(f'Modifying Shmoo to use configuration {data['shmoo']} for selected instances: ', data['instance'])
        #    tp.ShmooChange(shmoo=data['shmoo'],instances=data['instance'])
        #    tp.ShmooSet(instances=data['instance'])
        
        #elif data['shmoo_remove']
        #    print(f'Disabling Shmoo for selected Instances: ', data['instance'])
        #    tp.ShmooUnSet(instances=data['instance'])
        #    print('This will only disables the shmoo it doesnt remove the configuration done previously')

    def savedata(self):
        data, data_evg, CONFIGsel = self.read_ui()

        ## Test Program Files

        testprogram = f"{self.tp_path.get()}{self.TPPath}"
        tstJSONloc =  os.path.join(testprogram, self.ConfigJSON)
        tstSCRIPTloc =  os.path.join(testprogram, self.ConfigPY)



        if CONFIGsel:         

            shi.configSave(selection=CONFIGsel, config=data_evg, savefile=self.JSONloc)
            #shi.configSave(selection=CONFIGsel, config=data_evg, savefile=tstJSONloc)      
            shi.filecopy(src=self.JSONloc,dst=tstJSONloc)
            shi.filecopy(src=self.EditPYloc,dst=tstSCRIPTloc, overwrite=False)

        #else:
    
if __name__ == "__main__":
    app = TPConfigEditor(RowsConfigs=RowsConfigs)
    app.mainloop()