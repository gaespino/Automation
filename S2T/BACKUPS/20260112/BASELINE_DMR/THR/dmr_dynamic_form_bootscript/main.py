from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.product_specific.boot_selector import BootSelector
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.product_independent.json_reader import JsonReader
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.gui.ui.scrollable_frame import ScrollableFrame
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.gui.models.user_execution import UserExecution
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.gui.ui.form import RecipeForm
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.CONSTANTS import Constants
from diamondrapids.users.THR.product_independent.loggers.logger import Logger
import tkinter as tk
import json


class Main:
    def __init__(self, sv, ipc, root=None, **args):
        self._sv = sv
        self._ipc = self._itp = ipc
        self.root = root
        self._args = args
        self._logger = Logger()
        self.json_recipe_data = JsonReader(logger=self._logger, file_path="data/recipe_data.json")

    def open_gui(self):
        self.root = tk.Tk()
        self.root.geometry("700x900")
        self.root.resizable(True, True)
        self.root.title("Dynamic Recipe Form")
        self.scrollable_container = ScrollableFrame(self.root)
        self.scrollable_container.pack(fill="both", expand=True)
        self.form = RecipeForm(logger=self._logger, view=self.scrollable_container.scrollable_frame,
                               json_recipe_data=self.json_recipe_data, root=self.root, sv=self._sv, ipc=self._ipc)
        self.form.pack(fill=tk.BOTH, expand=True)
        self.root.mainloop()

    def re_open_gui(self):
        if self.root is not None:
            self.root.deiconify()
            self.root.mainloop()

    def go(self, thr_fast_boot=False, **args):
        new_args = {}
        boot_type = "Bootscript" if thr_fast_boot is False else "fast_boot"
        user_execution = UserExecution(logger=self._logger, boot_type=boot_type, json_recipe_data=self.json_recipe_data,
                                       bootscript_params=[], recipes=[])
        user_execution.set_default_bootscript_parameters()
        user_execution.set_args(**args)
        if user_execution.bootscript_params is not None:
            for item in user_execution.bootscript_params:
                new_args[item.name] = item.value
        boot_selector = BootSelector(logger=self._logger, user_execution=user_execution, sv=self._sv, ipc=self._ipc)
        thr_fast_boot = user_execution.boot_type != Constants.COMBOBOX_BOOT_TYPE_DEFAULT_OPTION
        result = boot_selector.go(
            thr_fast_boot=thr_fast_boot,
            **new_args)
        return result

    def _recover_pythonsv(self):
        for i in range(0, 5):
            try:
                self._logger.log("THR dynamic injection -> Recovering pythonsv")
                self._itp.forcereconfig()
                self._sv.refresh()
                self._itp.unlock()
                return True
            except Exception as e:
                self._logger.log("[WARNING ]THR dynamic injection -> Recovering pythonsv Failed, trying to reconnect()")
                self._itp.reconnect()
        return False

    def disable_power_downs(self, include_cbbs_powerdowns: bool = True, include_imhs_powerdowns: bool = False):
            if not self._recover_pythonsv():
                self._logger.log("[ERROR]THR dynamic injection -> There is an issue recovering pythonsv")
            self._itp.halt()
            for reg_line in Constants.POWER_DOWN_REGISTERS:
                name, value = reg_line.strip().split("=")
                new_name = ".".join(name.split(".")[1::])
                for socket in self._sv.sockets:
                    regs = []
                    if str(name).startswith("cbbs.") and include_cbbs_powerdowns:
                        regs = socket.cbbs.get_by_path(new_name)
                    if str(name).startswith("imhs.") and include_imhs_powerdowns:
                        regs = socket.imhs.get_by_path(new_name)
                    new_value = int(value,16)
                    for reg in regs:
                        self._logger.log(f"[INFO]THR dynamic injection -> Disabling power downs {name}->"
                                         f"0x{int(new_value):016x}")
                        reg.write(new_value)
            self._itp.go()


if __name__ == "__main__":
    from namednodes import sv
    import common.baseaccess as baseaccess
    itp = baseaccess.getglobalbase().getapi()
    itp.forcereconfig()
    itp.unlock()
    sv.refresh()
    thr_ui = Main(sv=sv, ipc=itp)
