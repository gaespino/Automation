from users.THR.dmr_dynamic_form_bootscript.src.gui.ui.field_builder import FieldBuilder
from users.THR.dmr_dynamic_form_bootscript.src.gui.ui.fuse_widget import FuseWidget
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.CONSTANTS import Constants
from users.THR.dmr_dynamic_form_bootscript.src.gui.models.recipe import Recipe
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog
import tkinter as tk
import builtins


class RecipesController:
    def __init__(self, view, logger: ILog, json_recipe_data: dict):
        self.view = view
        self.recipes = []
        self._logger = logger
        self.recipe_vars = {}
        self.recipe_items = []
        self.current_recipe_data = None
        self.recipe_var = tk.StringVar()
        self._json_recipe_data = json_recipe_data

    def _get_fuse_str(self):
        fuses = []
        fuse_widgets = self.recipe_vars.get("fuses", [])
        for fuse_widget in fuse_widgets:
            for name, selected in fuse_widget.vars:
                if selected.get():
                    fuses.append(name)
        return fuses

    def _get_selected_sockets(self):
        sockets = []
        socket_widgets = self.recipe_vars.get("sockets", [])
        for  name, selected in dict(socket_widgets).items():
            if selected.get():
                sockets.append(name)
        return sockets

    def on_add_recipe(self):
        name = self.view.recipe_selector.get()
        recipe_type = self._json_recipe_data[name]["type"]
        fields = self._validate_and_get_fields(recipe_name=name)
        sockets = self._get_selected_sockets()
        fuses = self._get_fuse_str()
        if fields is not None:
            recipe = Recipe(name, recipe_type, fields, sockets, fuses)
            self.recipes.append(recipe)
            self._logger.log(f"Added: {recipe}")
            self.add_recipe_to_list(recipe)
            self.recipe_var.set("")
            self.on_select_recipe(None)

    def add_recipe_to_list(self, recipe):
        frame = tk.Frame(self.view.recipe_list_frame)
        frame.pack(fill=tk.X, padx=5, pady=2)

        lbl = tk.Label(frame, text=recipe.name, anchor="w")
        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn = tk.Button(frame, text="❌", fg="red", command=lambda: self.remove_recipe_from_list(frame, recipe))
        btn.pack(side=tk.RIGHT)

    def remove_recipe_from_list(self, frame, recipe):
        frame.destroy()
        self.recipes = [(f, r) for f, r in self.recipe_items if r != recipe]

    def on_select_recipe(self, event):
        for widget in self.view.dynamic_frame.winfo_children():
            widget.destroy()

        recipe_name = self.recipe_var.get()

        if recipe_name == "":
            return  # Don't build anything if empty

        selected = self.view.recipe_selector.get()
        self.current_recipe_data = self._json_recipe_data[selected]

        self.recipe_vars.clear()
        field_frame = FieldBuilder.build_fields(
            self.view.dynamic_frame, self.current_recipe_data["fields"], self.recipe_vars
        )
        field_frame.pack(fill=tk.X, padx=10, pady=5)

        socket_frame = FieldBuilder.build_sockets(
            self.view.dynamic_frame, self.current_recipe_data["sockets"], self.recipe_vars
        )
        socket_frame.pack(fill=tk.X, padx=10, pady=5)

        for fuse in self.current_recipe_data.get("fuses", []):
            fuse_frame = FuseWidget(self.view.dynamic_frame, fuse, self.recipe_vars)
            fuse_frame.pack(fill=tk.X, padx=10, pady=5)

    def _convert_field_value_to_expected(self, field_name: str, value_str: str, expected_type: str, recipe_name: str):
        new_value = None
        try:
            if expected_type == "int":
                new_value = int(value_str)
            elif expected_type == "float":
                new_value = float(value_str)
            elif expected_type == "hex":
                new_value = hex(int(value_str,16))
        except Exception as e:
            message = (f"The value provided in field {field_name} for recipe {recipe_name} "
                       f"is not of the expected data type. "
                       f"Ensure the input meets the required format, expected type is "
                       f"'{expected_type}'.\n{str(e)}")
            self.view.show_message(message=message, message_type=Constants.MESSAGE_TYPE_ERROR)
        return new_value

    def _validate_and_get_fields(self, recipe_name: str)->dict:
        fields = self.recipe_vars.get("fields", {})
        new_fields = {}
        for field_name, value in fields.items():
            value_str = value[0].get().strip()
            required = value[1][Constants.FIELD_PROPERTY_REQUIRED]
            expected_type = value[1][Constants.FIELD_PROPERTY_TYPE]
            if not required and value_str == "":
                new_fields[field_name]=None
                continue
            if required and value_str == "":
                message = f"Parameter {field_name} is required for recipe {recipe_name}."
                self.view.show_message(message=message, message_type=Constants.MESSAGE_TYPE_ERROR)
                return None
            new_value = self._convert_field_value_to_expected(field_name=field_name, value_str=value_str,
                                                              expected_type=expected_type, recipe_name=recipe_name)
            if new_value is None:
                return None
            new_fields[field_name] = new_value
        return new_fields
