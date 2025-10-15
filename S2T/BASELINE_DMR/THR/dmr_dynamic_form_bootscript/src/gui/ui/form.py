from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.gui.controller.boot_type_controller import BootTypeController
from users.THR.dmr_dynamic_form_bootscript.src.gui.controller.control_buttons_controller import ControlButtonsController
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.gui.controller.recipes_controller import RecipesController
from users.THR.dmr_dynamic_form_bootscript.src.gui.controller.bootscript_controller import BootscriptController
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.product_independent.json_reader import JsonReader
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.gui.models.user_execution import UserExecution
from users.THR.dmr_dynamic_form_bootscript.src.product_specific.boot_selector import BootSelector
from diamondrapids.users.THR.product_independent.adapters.ipc_adapter import IpcAdapter
from diamondrapids.users.THR.product_independent.adapters.sv_adapter import SvAdapter
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.CONSTANTS import Constants
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog
from tkinter import messagebox
from tkinter import filedialog
from datetime import datetime
from tkinter import ttk
import tkinter as tk
import json
import os


class RecipeForm(tk.Frame):
    def __init__(self, view, logger: ILog, json_recipe_data: JsonReader, root, sv: SvAdapter=None, ipc: IpcAdapter=None):
        super().__init__(view)
        self._root = root
        self._sv = sv
        self._ipc = ipc
        self._itp = ipc
        self._view = view
        self._logger = logger
        self._json_recipe_data = json_recipe_data.get("dynamic_injections")
        self._boot_selector = None
        self._initialize()

    def destroy_wait_windows(self):
        self._control_buttons_controller.destroy_wait_windows()

    def _initialize(self):
        self._set_controllers()
        self._set_titles()
        self._create_widgets()
        if self._sv is None:
            from namednodes import sv
            self._sv = sv.get_manager(['socket'])
            self._sv.get_all()
            self._sv.refresh()
        if self._ipc is None:
            import ipccli
            self._itp = self._ipc = ipccli.baseaccess()
            self._itp.unlock()

    def _set_controllers(self):
        self.boot_type_controller = (
            BootTypeController(self, logger=self._logger))

        self._bootscript_controller = BootscriptController(self, logger=self._logger)
        self._control_buttons_controller = (
            ControlButtonsController(view=self,
                                     root=self._root,
                                     sv=self._sv,
                                     ipc=self._ipc,
                                     logger=self._logger,
                                     default_config_path=Constants.DEFAULT_DESTINATION_JSON_FILES_PATH))

        self._recipes_controller = RecipesController(self, logger=self._logger, json_recipe_data=self._json_recipe_data)

    def _set_titles(self):
        self.recipe_frame_title = "Recipe Selector"

    def _draw_boot_type_frame(self, master):
        self.boot_combobox = ttk.Combobox(
            master,
            textvariable=self.boot_type_controller.boot_type_var,
            values=Constants.COMBOBOX_BOOT_TYPE_OPTIONS,
            state=tk.NORMAL, width=70
        )
        self.boot_combobox.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.boot_type_controller.boot_type_var.trace_add("write", self.boot_type_controller.on_boot_type_change)

    def _draw_bootscript_frame(self, master):
        self.bootscript_text_area = tk.Text(master, height=10)
        self.bootscript_text_area.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.bootscript_text_area.delete("1.0", tk.END)  # Clear existing text
        self.bootscript_text_area.insert(tk.END, self._bootscript_controller.get_initial_bootscript_parameters())
        self.bootscript_frame.columnconfigure(0, weight=1)
        self.bootscript_frame.columnconfigure(1, weight=2)

    def _draw_recipe_frame(self, master):
        self.recipe_selector = ttk.Combobox(master, state="readonly", textvariable=self._recipes_controller.recipe_var)
        recipe_names = ["", *list(self._json_recipe_data.keys())]
        self.recipe_selector["values"] = recipe_names
        self.recipe_selector.bind("<<ComboboxSelected>>", self._recipes_controller.on_select_recipe)
        self.recipe_selector.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.add_button = tk.Button(master, text="Add", command=self._recipes_controller.on_add_recipe)
        self.add_button.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _draw_control_buttons(self):
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(fill=tk.X, padx=10, pady=(10, 20))
        tk.Button(self.button_frame, text="Hide",
                  command=self._control_buttons_controller.hide_windows, width=15).pack(pady=5, side=tk.LEFT)
        tk.Button(self.button_frame, text="Load",
                  command=self._control_buttons_controller.load_json, width=15).pack(pady=5, side=tk.LEFT)
        tk.Button(self.button_frame, text="Execute and Save",
                  command=self._control_buttons_controller.execute_and_save, width=15).pack(pady=5, side=tk.LEFT)
        tk.Button(self.button_frame, text="Execute",
                  command=self._control_buttons_controller.execute_only, width=15).pack(pady=5, side=tk.LEFT)
        tk.Button(self.button_frame, text="Save",
                  command=lambda: self._control_buttons_controller.save_json(), width=15).pack(pady=5, side=tk.LEFT)


    def draw_commom_python_commands(self):
        tk.Button(self.button_frame, text="itp.reconnect()",
                  command=lambda: self._control_buttons_controller.reconnect(), width=15).pack(pady=5, side=tk.LEFT)
        tk.Button(self.button_frame, text="itp.forcereconfig();sv.refresh()", row=1,
                  command=lambda: self._control_buttons_controller.forcereconfig(), width=15).pack(pady=5, side=tk.LEFT)


    def _create_widgets(self):
        self._draw_control_buttons()
        # dynamic tables
        self.bootscript_table = tk.LabelFrame(self, text=self._bootscript_controller.bootscript_frame_title)
        self.bootscript_table.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.recipe_list_frame = tk.LabelFrame(self, text=Constants.FRAME_TITLE_RECIPES)
        self.recipe_list_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.pack(fill="both", expand=True)
        self._boot_frame = ttk.Frame(self.main_notebook, width=500, height=750)
        self._boot_frame.pack(fill="both", expand=True)
        self.boot_type_frame = tk.LabelFrame(self._boot_frame, text=self.boot_type_controller.boot_type_frame_title)
        self.boot_type_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        self._draw_boot_type_frame(master=self.boot_type_frame)
        self.bootscript_frame = tk.LabelFrame(self._boot_frame, text=self._bootscript_controller.bootscript_frame_title)
        self.bootscript_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        self._draw_bootscript_frame(master=self.bootscript_frame)
        self.main_notebook.add(self._boot_frame, text=Constants.FRAME_TITLE_BOOT_MAIN)
        self.recipe_frame = tk.LabelFrame(self, text=self.recipe_frame_title)
        self.recipe_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        self._draw_recipe_frame(master=self.recipe_frame)
        self.dynamic_frame = tk.LabelFrame(self.recipe_frame, text=Constants.FRAME_TITLE_RECIPES)
        self.dynamic_frame.pack(fill=tk.BOTH, expand=True)
        self.main_notebook.add(self.recipe_frame, text=Constants.FRAME_TITLE_RECIPES)

    def collect_user_data(self):
        return UserExecution(
            logger=self._logger,
            json_recipe_data=self._json_recipe_data,
            boot_type=self.boot_type_controller.boot_type_var.get(),
            bootscript_params=self._bootscript_controller.get_bootscript_text_area_value(),
            recipes=self._recipes_controller.recipes)

    def show_message(self, message: str, message_type: str = Constants.MESSAGE_TYPE_INFO):
        self._logger.log(f"{message_type}:->{message}")
        if message_type == Constants.MESSAGE_TYPE_INFO:
            messagebox.showinfo(message_type, message)
        elif message_type == Constants.MESSAGE_TYPE_ERROR:
            messagebox.showerror(message_type, message)
        elif message_type == Constants.MESSAGE_TYPE_WARNING:
            messagebox.showwarning(message_type, message)
