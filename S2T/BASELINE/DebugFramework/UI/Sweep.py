import tkinter as tk
from tkinter import ttk

class SweepGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Debug Framework Sweep Test")
        
        # Initialize variables
        self.target_var = tk.StringVar(value="mesh")
        self.test_type_var = tk.StringVar(value="frequency")
        self.domain_var = tk.StringVar(value="cfc")
        self.content_var = tk.StringVar(value="Dragon")
        self.fastboot_var = tk.BooleanVar(value=True)
        self.u600w_var = tk.BooleanVar(value=False)
        self.reset_var = tk.BooleanVar(value=True)
        self.resetonpass_var = tk.BooleanVar(value=True)
        self.summary_var = tk.BooleanVar(value=True)
        self.ia_config_var = tk.BooleanVar(value=True)
        self.cfc_config_var = tk.BooleanVar(value=True)

        # Configure grid
        for i in range(6):
            self.root.grid_columnconfigure(i, weight=1)

        # Build the GUI
        self.build_gui()

    def build_gui(self):
        # Row 0
        self.create_label_entry("Test Number", 0, 0, default="1")
        self.create_label_entry("Visual ID", 0, 2)
        self.create_label_entry("Bucket", 0, 4)

        # Row 1
        self.create_label_entry("Name", 1, 0, width=50, colspan=5)

        # Row 2
        self.create_separator("Sweep Configuration", 2, 0, 6)

        # Row 3
        self.create_combobox("Target", ["Slice", "Mesh"], self.target_var, 3, 0, self.update_mask_options)
        self.mask_label = tk.Label(self.root, text="Mask", anchor="e")
        self.mask_label.grid(row=3, column=2, padx=5, pady=5, sticky="ew")
        self.mask_combobox = ttk.Combobox(self.root)
        self.mask_combobox.grid(row=3, column=3, padx=5, pady=5, sticky="ew")
        self.mask_combobox.bind("<<ComboboxSelected>>", self.update_fastboot_conditions)

        self.pseudo_label = tk.Label(self.root, text="Pseudo", anchor="e")
        self.pseudo_label.grid(row=3, column=4, padx=5, pady=5, sticky="ew")
        self.pseudo_combobox = ttk.Combobox(self.root)
        self.pseudo_combobox.grid(row=3, column=5, padx=5, pady=5, sticky="ew")

        # Row 4
        self.corelic_label = tk.Label(self.root, text="Check Core", anchor="e")
        self.corelic_label.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        self.corelic_entry = tk.Entry(self.root)
        self.corelic_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        self.create_label_entry("Test Time", 4, 2)
        self.create_combobox("Voltage Type", ["vbump", "fixed"], None, 4, 4, default="vbump")

        # Row 5
        self.create_combobox("Test Type", ["voltage", "frequency"], self.test_type_var, 5, 0, self.update_ia_cfc_conditions)
        self.create_combobox("Domain", ["ia", "cfc"], self.domain_var, 5, 2, self.update_ia_cfc_conditions)
        self.create_combobox("Content", ["Dragon", "Linux"],  self.content_var, 5, 4)

        # Row 6
        self.create_separator("Sweep Range", 6, 0, 6)

        # Row 7
        self.create_label_entry("Start", 7, 0)
        self.create_label_entry("End", 7, 2)
        self.create_label_entry("Step", 7, 4)

        # Row 8
        self.create_separator("Additional Configurations", 8, 0, 6)

        # Row 9
        self.create_checkbox("IA Configuration", self.ia_config_var, 9, 0, self.update_ia_cfc_conditions)
        self.voltage_ia_entry = self.create_label_entry("Voltage IA", 9, 1, width=15)
        self.frequency_ia_entry = self.create_label_entry("Frequency IA", 9, 3, width=15)

        # Row 10
        self.create_checkbox("CFC Configuration", self.cfc_config_var, 10, 0, self.update_ia_cfc_conditions)
        self.voltage_cfc_entry = self.create_label_entry("Voltage CFC", 10, 1, width=15)
        self.frequency_cfc_entry = self.create_label_entry("Frequency CFC", 10, 3, width=15)

        # Row 11 - Checkboxes
        self.fastboot_checkbox = tk.Checkbutton(self.root, text="Fast Boot", variable=self.fastboot_var)
        self.fastboot_checkbox.grid(row=11, column=0, padx=5, pady=5, sticky="w")

        self.u600w_checkbox = tk.Checkbutton(self.root, text="600w Unit", variable=self.u600w_var)
        self.u600w_checkbox.grid(row=11, column=1, padx=5, pady=5, sticky="w")
        self.u600w_checkbox.bind("<ButtonRelease-1>", self.update_fastboot_conditions)

        self.create_checkbox("Reset", self.reset_var, 11, 2)
        self.create_checkbox("Reset on Pass", self.resetonpass_var, 11, 3)
        self.create_checkbox("Build Summary", self.summary_var, 11, 4)

        # Row 12
        self.create_separator("", 12, 0, 6)

        # Row 13
        self.create_button("Run", self.run_sweep, 13, 4, width=10)
        self.create_button("Close", self.close_app, 13, 5, width=10)

        # Initialize conditions
        self.update_mask_options()
        self.update_ia_cfc_conditions()

    def create_label_entry(self, label_text, row, column, default="", width=20, colspan=1):
        label = tk.Label(self.root, text=label_text, anchor="e")
        label.grid(row=row, column=column, padx=5, pady=5, sticky="ew")
        entry = tk.Entry(self.root, width=width)
        entry.insert(0, default)
        entry.grid(row=row, column=column+1, columnspan=colspan, padx=5, pady=5, sticky="ew")
        return entry

    def create_combobox(self, label_text, values, var, row, column, command=None, default=None):
        label = tk.Label(self.root, text=label_text, anchor="e")
        label.grid(row=row, column=column, padx=5, pady=5, sticky="ew")
        combobox = ttk.Combobox(self.root, textvariable=var, values=values)
        if default:
            combobox.set(default)
        combobox.grid(row=row, column=column+1, padx=5, pady=5, sticky="ew")
        if command:
            combobox.bind("<<ComboboxSelected>>", command)
        return combobox

    def create_checkbox(self, label_text, var, row, column, command=None):
        checkbox = tk.Checkbutton(self.root, text=label_text, variable=var, command=command)
        checkbox.grid(row=row, column=column, padx=5, pady=5, sticky="ew")
        return checkbox

    def create_separator(self, text, row, column, colspan):
        separator = ttk.Separator(self.root, orient='horizontal')
        separator.grid(row=row, column=column, columnspan=colspan, sticky='ew', padx=5, pady=5)
        if text:
            separator_label = tk.Label(self.root, text=text, anchor="center", relief='ridge')
            separator_label.grid(row=row, column=column+colspan//2-1, columnspan=2, padx=5, pady=5, sticky="ew") #column=column+colspan//2

    def create_button(self, text, command, row, column, width=8):
        button = tk.Button(self.root, text=text, command=command, width=width)
        button.grid(row=row, column=column, padx=5, pady=5, sticky="ew")
        return button

    def update_mask_options(self, *args):
        target = self.target_var.get()
        if target == 'slice':
            self.mask_label.config(text="Phys Core")
            self.mask_combobox.config(values=[i for i in range(1, 17)])  # Example range for Phys Core
            self.mask_combobox.set(1)
        elif target == 'mesh':
            self.mask_label.config(text="Mask")
            self.mask_combobox.config(values=["None", "FirstPass", "SecondPass", "ThirdPass", "RowPass1", "RowPass2", "RowPass3", "Compute0", "Compute1", "Compute2"])
            self.mask_combobox.set("None")
        self.update_pseudo_options()

    def update_pseudo_options(self, *args):
        target = self.target_var.get()
        if target == 'slice':
            self.pseudo_combobox.config(state='disabled')
            self.pseudo_combobox.set("NO")
        else:
            self.pseudo_combobox.config(state='normal')
            self.pseudo_combobox.config(values=["YES", "NO"])
            self.pseudo_combobox.set("YES")

    def update_ia_cfc_conditions(self, *args):
        test_type = self.test_type_var.get()
        domain = self.domain_var.get()
        
        # IA Configuration
        if self.ia_config_var.get():
            if test_type == 'voltage' and domain == 'ia':
                self.voltage_ia_entry.config(state='disabled')
                self.frequency_ia_entry.config(state='normal')
            elif test_type == 'frequency' and domain == 'ia':
                self.voltage_ia_entry.config(state='normal')
                self.frequency_ia_entry.config(state='disabled')
            else:
                self.voltage_ia_entry.config(state='normal')
                self.frequency_ia_entry.config(state='normal')
        else:
            self.voltage_ia_entry.config(state='disabled')
            self.frequency_ia_entry.config(state='disabled')

        # CFC Configuration
        if self.cfc_config_var.get():
            if test_type == 'voltage' and domain == 'cfc':
                self.voltage_cfc_entry.config(state='disabled')
                self.frequency_cfc_entry.config(state='normal')
            elif test_type == 'frequency' and domain == 'cfc':
                self.voltage_cfc_entry.config(state='normal')
                self.frequency_cfc_entry.config(state='disabled')
            else:
                self.voltage_cfc_entry.config(state='normal')
                self.frequency_cfc_entry.config(state='normal')
        else:
            self.voltage_cfc_entry.config(state='disabled')
            self.frequency_cfc_entry.config(state='disabled')

    def update_fastboot_conditions(self, *args):
        mask = self.mask_combobox.get()
        u600w = self.u600w_var.get()
        if mask != "None" or u600w:
            self.fastboot_var.set(False)
            self.fastboot_checkbox.config(state='disabled')
        else:
            self.fastboot_checkbox.config(state='normal')

    def run_sweep(self):
        # Implement the logic to run the sweep
        pass

    def close_app(self):
        self.root.destroy()

# Create the main window and run the GUI
root = tk.Tk()
app = SweepGUI(root)
root.mainloop()