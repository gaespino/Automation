from users.THR.dmr_dynamic_form_bootscript.src.product_specific.boot_selector import BootSelector
from diamondrapids.users.THR.product_independent.adapters.ipc_adapter import IpcAdapter
from diamondrapids.users.THR.product_independent.adapters.sv_adapter import SvAdapter
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.CONSTANTS import Constants
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog
from tkinter import filedialog, messagebox, ttk
import tkinter as tk
import threading
import asyncio
import time
import json
import os


class ControlButtonsController:
    def __init__(self, root, view, logger: ILog, default_config_path,
                 sv: SvAdapter, ipc: IpcAdapter,current_config: dict = None):
        self._sv = sv
        self._ipc = ipc
        self.view = view
        self._root = root
        self._logger = logger
        self.default_path = default_config_path
        self.current_config = current_config

    def hide_windows(self):
        self._root.withdraw()
        self._root.quit()

    def load_json(self):
        file_path = filedialog.askopenfilename(
            initialdir=os.path.dirname(self.default_path),
            title="Select config file",
            filetypes=(("JSON files", "*.json"),)
        )
        if file_path:
            try:
                with open(file_path, "r") as f:
                    self.current_config = json.load(f)
                    messagebox.showinfo("Load", "Configuration loaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load JSON: {e}")

    def save_json(self, path=None):
        if not path:
            path = filedialog.asksaveasfilename(
                defaultextension=".json",
                initialfile=os.path.basename(self.default_path),
                initialdir=os.path.dirname(self.default_path),
                filetypes=(("JSON files", "*.json"),)
            )
        if path:
            try:
                with open(path, "w") as f:
                    json.dump(self.current_config, f, indent=4)
                    messagebox.showinfo("Save", "Configuration saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save JSON: {e}")

    async def async_action(self):
        user_execution = self.view.collect_user_data()
        args = {}
        if user_execution.bootscript_params is not None:
            for item in user_execution.bootscript_params:
                args[item.name] = item.value
        boot_selector = BootSelector(logger=self._logger, user_execution=user_execution, sv=self._sv, ipc=self._ipc)
        thr_fast_boot = user_execution.boot_type != Constants.COMBOBOX_BOOT_TYPE_DEFAULT_OPTION
        result = boot_selector.go(
            thr_fast_boot=thr_fast_boot,
            **args)
        return result

    def execute_async(self):
        asyncio.run(self.async_action())

    def reconnect(self):
        self._ipc.reconnect()

    def forcereconfig(self):
        self._ipc.forcereconfig()
        self._sv.refresh()

    def execute_and_save(self):
        def run():
            asyncio.run(self.async_action())
            self.save_json(self.default_path)
        threading.Thread(target=run).start()

    def execute_only(self):
        threading.Thread(target=self.execute_async).start()