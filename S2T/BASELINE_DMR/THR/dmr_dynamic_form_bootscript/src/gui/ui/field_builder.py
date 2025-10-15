import tkinter as tk
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.gui.utils.validator import validate_field


class FieldBuilder:
    @staticmethod
    def build_fields(parent, fields_data, store):
        frame = tk.LabelFrame(parent, text="Fields")
        field_values = {}
        for field in fields_data:
            row = tk.Frame(frame)
            label = tk.Label(row, text=field["name"])
            entry_var = tk.StringVar()
            entry = tk.Entry(row, textvariable=entry_var)

            row.pack(fill=tk.X, pady=2)
            label.pack(side=tk.LEFT)
            entry.pack(side=tk.RIGHT, expand=True, fill=tk.X)

            field_values[field["name"]] = (entry_var, field)

        store["fields"] = field_values
        return frame

    @staticmethod
    def build_sockets(parent, sockets, store):
        frame = tk.LabelFrame(parent, text="Sockets")
        socket_vars = {}
        for socket in sockets:
            var = tk.BooleanVar(value=True)
            chk = tk.Checkbutton(frame, text=socket, variable=var)
            chk.pack(anchor=tk.W)
            socket_vars[socket] = var

        store["sockets"] = socket_vars
        return frame