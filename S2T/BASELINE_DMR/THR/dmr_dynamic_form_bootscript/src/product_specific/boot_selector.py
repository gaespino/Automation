from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.product_specific.boot_script_adapter import DmrBootScriptAdapter
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.product_specific.fast_platform_boot import FastPlatformBoot
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.product_specific.platform_boot import PlatformBoot
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.gui.models.user_execution import UserExecution
from diamondrapids.users.THR.product_independent.adapters.ipc_adapter import IpcAdapter
from diamondrapids.users.THR.product_independent.adapters.sv_adapter import SvAdapter
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.CONSTANTS import Constants
from users.THR.dmr_dynamic_form_bootscript.src.gui.models.recipe import Recipe
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog
from typing import List
import namednodes
import re


class BootSelector:
    def __init__(self, logger: ILog, user_execution: UserExecution, sv: SvAdapter, ipc: IpcAdapter,
                 platform_boot:PlatformBoot=None, fast_platform_boot: FastPlatformBoot=None, fast_boot: bool=False,
                 bootscript: DmrBootScriptAdapter = None, initialized: bool=False):
        self._fast_platform_boot = fast_platform_boot
        self._user_execution = user_execution
        self._platform_boot = platform_boot
        self._initialized = initialized
        self._bootscript = bootscript
        self._fast_boot = fast_boot
        self._logger = logger
        self._ipc = self._itp = ipc
        self._sv = sv

    def _initialize_bootscript(self):
        from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.product_specific.boot_script_adapter import \
            DmrBootScriptAdapter
        self._bootscript = DmrBootScriptAdapter()

    def go(self, thr_fast_boot: bool = False, **args):
        if thr_fast_boot:
            self._fast_platform_boot = FastPlatformBoot(logger=self._logger, recipes=self._user_execution.recipes,
                                                        sv=self._sv, ipc=self._ipc)
            self._fast_platform_boot.go(**args)
        else:
            self._initialize_bootscript()
            self._platform_boot = PlatformBoot(logger=self._logger, recipes=self._user_execution.recipes,
                                               sv=self._sv, itp=self._itp, bootscript=self._bootscript)
            self._platform_boot.go(**args)
