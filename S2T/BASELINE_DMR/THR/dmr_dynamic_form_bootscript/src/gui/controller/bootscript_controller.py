import tkinter as tk
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.CONSTANTS import Constants
from users.THR.dmr_dynamic_form_bootscript.src.gui.models.bootscript_parameter import BootscriptParameter


class BootscriptController:
    def __init__(self, view, logger: ILog):
        self.view = view
        self._logger = logger
        self.bootscript_rows = []
        self.bootscript_params = []
        self.bootscript_param_var = tk.StringVar()
        self.bootscript_frame_title = Constants.FRAME_TITLE_BOOTSCRIPT_PARAMETERS

    @staticmethod
    def get_bootscript_parameters():
        return Constants.BOOTSCRIPT_ALLOWED_PROJECT_ARGS

    def get_initial_bootscript_parameters(self):
        for key, value in Constants.BOOTSCRIPT_DEFAULT_ARGUMENTS.items():
            param = BootscriptParameter(key, value)
            self.bootscript_params.append(param)
            if self.bootscript_param_var.get() != "":
                self.bootscript_param_var.set(f"{self.bootscript_param_var.get()}{key}={value}\n")
            else:
                self.bootscript_param_var.set(f"{key}={value}\n")
        return self.bootscript_param_var.get()

    @staticmethod
    def _get_real_value(value):
        # Verificar si es un booleano
        if value.lower() in ['true', 'false']:
            return value=="True"

        try:
            return int(value)
        except ValueError:
            pass

        # Verificar si es un float
        try:
            return float(value)
        except ValueError:
            pass
        return value.replace('"', '').replace("'", "")

    def get_bootscript_text_area_value(self):
        lines = self.view.bootscript_text_area.get("1.0", tk.END).split()
        self.bootscript_params = []
        for line in lines:
            try:
                if line.strip() != "":
                    key, value = str(line).strip().split("=")
                    param = BootscriptParameter(key, self._get_real_value(value))
                    self.bootscript_params.append(param)
            except Exception as e:
                self.view.show_message(
                    message=f"Parameter {line} is invalid, please correct it before to proceed.",
                    message_type="ERROR")
                return None
        return self.bootscript_params
