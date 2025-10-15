from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.interfaces.iboot_script_adapter import IBootScriptAdapter


class DmrBootScriptAdapter(IBootScriptAdapter):
    def __init__(self):
        from diamondrapids.toolext.bootscript import boot as b
        self._boot_script_sdk = b
        super(DmrBootScriptAdapter, self).__init__(self._boot_script_sdk)

    def check_boot_script_step_succeeded(self, boot_script_step_result):
        # type: (int) -> bool
        return boot_script_step_result == self._boot_script_sdk.boot_vars.framework_vars.SUCCESS
