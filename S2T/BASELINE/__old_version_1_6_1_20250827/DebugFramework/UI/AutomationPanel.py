import tkinter as tk
from tkinter import messagebox
import json
import socket
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

class AutomationFlowUI:

    def __init__(self, json_config_path):
        self.load_config(os.path.join(current_dir, json_config_path))
        self.root = tk.Tk()
        self.root.title("Automation Flow UI")
        self.root.geometry("340x450")  # Increased width for a prettier layout
        
        # Store references to label widgets
        self.widgets = {}
        self.tooltip = None

        # Initialize the fields with default values
        self.fields = {
            "Visual ID": tk.StringVar(),
            "COM Port": tk.StringVar(value="8"),  
            "IP Address": tk.StringVar(value="192.168.0.2"),
            "CFC Voltage Start": tk.StringVar(value="-0.1"),
            "CFC Voltage End": tk.StringVar(value="0.0"),
            "CFC Voltage Steps": tk.StringVar(value="0.02"),
            "IA Voltage Start": tk.StringVar(value="-0.1"),
            "IA Voltage End": tk.StringVar(value="0.0"),
            "IA Voltage Steps": tk.StringVar(value="0.02"),
            "Temperature": tk.StringVar(value="25.0")
        }
          
        self.setup_form()
        self.root.mainloop()

    def load_config(self, path):
        try:
            with open(path, 'r') as file:
                self.config = json.load(file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON config: {e}")
            self.root.destroy()

    def setup_form(self):
        for idx, (label, var) in enumerate(self.fields.items()):
            lbl = tk.Label(self.root, text=label, pady=5) 
            lbl.grid(row=idx, column=0, padx=10, pady=5, sticky='w')
            entry = tk.Entry(self.root, textvariable=var, width=30)
            entry.grid(row=idx, column=1, padx=10, pady=5, sticky='w')
            self.widgets[label] = lbl
            lbl.bind("<Enter>", lambda event, l=label: self.show_tooltip(event, l))
            lbl.bind("<Leave>", lambda event, l=label: self.hide_tooltip(event, l))
        
        tk.Button(self.root, text="Start", command=self.validate_fields).grid(row=len(self.fields), column=0, columnspan=2, pady=20)

    def validate_fields(self):
        errors = []
        try:
            for field_name, var in self.fields.items():
                self.clear_error(field_name)
                field_info = self.config["fields"].get(field_name, {})
                
                if field_info.get("type") == "str":
                    if not var.get():
                        self.show_error(field_name)
                        errors.append(f"{field_name} must be non-empty.")
                
                elif field_info.get("type") == "int":
                    try:
                        port = int(var.get())
                        with socket.socket() as s:
                            s.bind(('', port))
                    except ValueError:
                        self.show_error(field_name)
                        errors.append(f"{field_name} must be an integer.")
                    except OSError:
                        self.show_error(field_name)
                        errors.append(f"{field_name} must be a valid serial port number (1-65535).")
                
                elif field_info.get("type") == "float":
                    try:
                        value = float(var.get())
                        if value < field_info.get("min", float('-inf')) or value > field_info.get("max", float('inf')):
                            self.show_error(field_name)
                            errors.append(f"{field_name} must be between {field_info['min']} and {field_info['max']}.")
                    except ValueError:
                        self.show_error(field_name)
                        errors.append(f"{field_name} must be a float.")
                
                elif field_name == "IP Address":
                    try:
                        socket.inet_aton(var.get())
                    except socket.error:
                        self.show_error(field_name)
                        errors.append(f"{field_name} must be a valid IP address.")
        
            if not errors:
                messagebox.showinfo("Success", "All fields are validated successfully!")
            elif len(errors) == 1:
                messagebox.showerror("Validation Error", errors[0])
            else:
                messagebox.showerror("Validation Error", "Multiple fields are invalid.")
        
        except ValueError as ve:
            errors.append(str(ve))
            if len(errors) == 1:
                messagebox.showerror("Validation Error", errors[0])
            else:
                messagebox.showerror("Validation Error", "Multiple fields are invalid.")

    def show_error(self, field_name):
        self.widgets[field_name].config(fg="red")

    def clear_error(self, field_name):
        self.widgets[field_name].config(fg="black")

    def show_tooltip(self, event, label):
        tooltip_text = self.config["fields"][label]["tooltip"]
        if self.tooltip:
            self.tooltip.destroy()
        self.tooltip = tk.Label(self.root, text=tooltip_text, bg='yellow', fg='black', relief='solid', borderwidth=1)
        self.tooltip.place(x=self.root.winfo_pointerx() - self.root.winfo_rootx(),
                           y=self.root.winfo_pointery() - self.root.winfo_rooty())

    def hide_tooltip(self, _event, _label):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

if __name__ == "__main__":
    form = AutomationFlowUI("GNRAutomationPanel.json")