import tkinter as tk
import itertools


class FuseWidget(tk.LabelFrame):
    def __init__(self, parent, fuse_data, store):
        super().__init__(parent, text=fuse_data["name"])
        self.template = fuse_data["template"]
        self.parameters = fuse_data["parameters"]
        self.default_vlaue = fuse_data["default_value"]
        self.debug_notes = fuse_data.get("debug_notes", "")
        self.vars = []

        self._build_widget()
        store.setdefault("fuses", []).append(self)

    def _build_widget(self):
        if self.debug_notes:
            note_label = tk.Label(self, text=f"Note: {self.debug_notes}", fg="gray", anchor="w", justify="left")
            note_label.pack(fill=tk.X, padx=5, pady=(2, 0))

        # Control buttons: Select/Deselect All
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(5, 2))

        select_all_btn = tk.Button(btn_frame, text="Select All", command=self._select_all)
        deselect_all_btn = tk.Button(btn_frame, text="Deselect All", command=self._deselect_all)
        select_all_btn.pack(side=tk.LEFT, padx=(10, 5))
        deselect_all_btn.pack(side=tk.LEFT)

        # Scrollable canvas
        canvas = tk.Canvas(self, height=150)
        scrollbar_y = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollbar_x = tk.Scrollbar(self, orient="horizontal", command=canvas.xview)

        self.scroll_frame = tk.Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self._populate_checkboxes()

    def _populate_checkboxes(self):
        keys = self.parameters.keys()
        values = [self.parameters[k] for k in keys]

        max_chars = 80  # Visual string limit

        for combination in itertools.product(*values):
            full_string = self.template
            for key, val in zip(keys, combination):
                full_string = full_string.replace(f"&{key}&", val)

            display_text = (full_string[:max_chars] + "...") if len(full_string) > max_chars else full_string

            var = tk.BooleanVar(value=self.default_vlaue)
            chk = tk.Checkbutton(
                self.scroll_frame,
                text=display_text,
                variable=var,
                anchor="w",
                justify="left"
            )
            chk.pack(fill=tk.X, anchor="w")
            self.vars.append((full_string, var))

    def _select_all(self):
        for _, var in self.vars:
            var.set(True)

    def _deselect_all(self):
        for _, var in self.vars:
            var.set(False)
