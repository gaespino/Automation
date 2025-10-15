from diamondrapids.users.THR.product_independent.adapters.ipc_adapter import IpcAdapter
from diamondrapids.users.THR.product_independent.adapters.sv_adapter import SvAdapter
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog


class PythonSVCommonCommandsController:
    def __init__(self, view, logger: ILog, default_config_path,
                 sv: SvAdapter, ipc: IpcAdapter,current_config: dict = None):
        self._sv = sv
        self._ipc = ipc
        self.view = view
        self._logger = logger

    def reconnect(self):
        self._ipc.reconnect()

    def forcereconfig(self):
        self._ipc.forcereconfig()
        self._sv.refresh()

    def tile_view(self):
        pass

