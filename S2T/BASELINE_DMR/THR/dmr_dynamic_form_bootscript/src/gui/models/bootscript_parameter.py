from users.THR.dmr_dynamic_form_bootscript.CONSTANTS import Constants


class BootscriptParameter:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def is_valid(self):
        return self.name not in Constants.COMBOBOX_BOOT_TYPE_DEFAULT_OPTION
