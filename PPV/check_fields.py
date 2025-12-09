"""Quick field count check"""
import sys
sys.path.insert(0, 'PPV')
from gui.ExperimentBuilder import ExperimentBuilderGUI
import tkinter as tk

root = tk.Tk()
root.withdraw()
app = ExperimentBuilderGUI(root)

fields = sorted(app.config_template['data_types'].keys())
print(f'\nTotal fields: {len(fields)}\n')
print('All fields:')
for i, field in enumerate(fields, 1):
    field_type = app.config_template['data_types'][field][0]
    print(f'{i:2}. {field:40} [{field_type}]')

root.destroy()
