from diamondrapids.users.THR.product_independent.adapters.call_forwarder import CallForwarder
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog
from diamondrapids.users.THR.product_independent.adapters.sv_adapter import SvAdapter
from time import sleep
import psutil


class IpcAdapter(CallForwarder):
    def __init__(self, sv: SvAdapter, logger: ILog):
        import ipccli
        self._ipc = ipccli.baseaccess()
        self._sv = sv
        self._logger = logger
        self._base_access = None
        self._sleep_time_for_force_reconfig = 2
        super(IpcAdapter, self).__init__(self._ipc)

    def force_reconfig_with_retries(self, attempts=3, expression_to_wait_on="self._ipc.uncores==None"):
        # type: (int, str) -> bool
        self._logger.log("Force Reconfig: Expression to wait on successful re-config: %s" % str(expression_to_wait_on))
        self._logger.log("Force Reconfig: Attempts to wait on successful re-config  : %s" % str(attempts))

        result = False
        for currentAttempt in range(0, attempts):
            self._logger.log("Force Reconfig: attempt #: %s" % str(currentAttempt))
            try:
                self._ipc.forcereconfig()
                sleep(self._sleep_time_for_force_reconfig)
                expression_result = eval(expression_to_wait_on)
                if not expression_result:
                    self._logger.log("Force Reconfig: successful reconfiguration!")
                    result = True
                    break
            except Exception as e:
                self._logger.log(
                    "Force Reconfig: Error while trying to re-config, will attempt to reconnect to OpenIPC. "
                    "Error Details: %s" % str(e))
                self.reconnect_ipc()
        return result

    def reconnect_ipc(self):
        self._logger.log("Restarting and reconnecting to OpenIPC...")
        self._kill_open_ipc()
        sleep(self._sleep_time_for_force_reconfig)
        self._ipc = self._ipc_creator()
        self._ipc.reconnect()
        sleep(self._sleep_time_for_force_reconfig)
        self._sv.recover()

    @staticmethod
    def _kill_open_ipc():
        open_ipc_name = "OpenIPC_x64.exe"
        procs = psutil.process_iter()
        for proc in procs:
            # check whether the process name matches
            if proc.name() == open_ipc_name:
                proc.kill()
