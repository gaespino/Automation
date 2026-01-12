import tkinter as tk
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.CONSTANTS import Constants


class BootTypeController:
    def __init__(self, view, logger: ILog):
        self.view = view
        self._logger = logger
        self.boot_type_frame_title = Constants.FRAME_TITLE_BOOT_TYPE
        self.boot_type_var = tk.StringVar(value=Constants.COMBOBOX_BOOT_TYPE_DEFAULT_OPTION)

    def on_boot_type_change(self, *args):
        self._logger.log(str(args))
        is_bootscript = self.boot_type_var.get() == Constants.COMBOBOX_BOOT_TYPE_BOOTSCRIPT
        state = tk.NORMAL if is_bootscript else tk.DISABLED
        self.view.bootscript_combobox.configure(state=state)
        self.view.bootscript_value_entry.configure(state=state)
        self.view.bootscript_add_btn.configure(state=state)
