from diamondrapids.users.THR.product_independent.adapters.call_forwarder import CallForwarder


class IBootScriptAdapter(CallForwarder):
    def check_boot_script_step_succeeded(self, boot_script_step_result):
        # type: (int) -> bool
        raise NotImplementedError
