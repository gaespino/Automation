from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.product_specific.ipc_adapter import DmrIpcAdapter
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.gui.models.recipe import Recipe
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.interfaces.iboot import IBoot
from diamondrapids.users.THR.product_independent.adapters.sv_adapter import SvAdapter
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog
from pysvtools.bootscript import FrameworkVars
from typing import List



class FastPlatformBoot(IBoot):
    def __init__(self, logger: ILog, sv: SvAdapter, recipes: List[Recipe], ipc: DmrIpcAdapter) -> None:
        self._recipes = recipes
        self._logger = logger
        self._ipc = ipc
        self._sv = sv

    def go(self,  **args) -> int:
        return FrameworkVars.SUCCESS
