from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.product_specific.fuse_actions import FuseActions
from diamondrapids.users.THR.product_independent.adapters.sv_adapter import SvAdapter
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog
from users.THR.product_independent.adapters.ipc_adapter import IpcAdapter
from pysvtools.bootscript import FrameworkVars
from typing import List


class DmrDynamicInjection:
    def __init__(self, logger: ILog, die_str_exp: str, sv: SvAdapter, itp: IpcAdapter,
                 fuses: List[str] = None,
                 socket: str = None, die: str = None):
        self._logger = logger
        self._fuses = fuses
        self._socket = socket
        self._die = die
        self._sv = sv
        self._itp = self._ipc = itp
        self._die_str_exp = die_str_exp
        self._loaded_die_fuses = []
        self._fuse_actions = FuseActions(logger=self._logger, sv=self._sv, ignore_zero_values=False)

    def add_fuse(self, fuse_str: str):
        if not self._fuses:
            self._fuses = []
        self._fuses.append(fuse_str)

    def get_die_str_exp(self):
        return self._die_str_exp

    def _recover_pythonsv(self):
        self._logger.log("THR dynamic injection -> Recovering pythonsv")
        self._itp.forcereconfig()
        self._sv.refresh()

    def _test_pythonsv_integrity(self):
        try:
            self._logger.log("THR dynamic injection -> Testing pythonsv integrity")
            self._sv.socket0.show()
            self._logger.log(f"THR dynamic injection -> sv items:{len(self._sv.socket0.sub_groups['dies'])}")
            if len(self._sv.socket0.sub_groups["dies"]) < 3:
                self._recover_pythonsv()
        except:
            self._recover_pythonsv()
        self._logger.log("THR dynamic injection -> ipc is up")

    def _load_fuse_ram_and_go_offline(self):
        self._die_obj.fuses.load_fuse_ram()
        self._die_obj.fuses.go_offline()

    def _flush_fuse_ram_and_go_online(self):
        self._die_obj.fuses.flush_fuse_ram()
        self._die_obj.fuses.go_online()

    def _perform_voltage_bump(self) -> int:
        result = FrameworkVars.SUCCESS
        current_die = None
        for fuse in self._fuses:
            if "*" in fuse:
                fuse_str, offset_str = fuse.strip().split("*")
                self._logger.log(f"THR Dynamic Inject -> Checking fuse: {fuse_str}. Curren die is: {self._die}")
                if str(fuse_str).startswith(self._die):
                    offset = float(offset_str)
                    result = self._fuse_actions.perform_voltage_bump(socket=self._socket, offset=offset,
                                                               search_string=fuse_str)
                    if result != FrameworkVars.SUCCESS:
                        return result
        return result

    def _perform_fuse_override(self) -> int:
        result = FrameworkVars.SUCCESS
        for fuse in self._fuses:
            if "=" in fuse:
                fuse_str, new_value_str = fuse.strip().split("=")
                self._logger.log(f"THR Dynamic Inject -> Checking fuse: {fuse_str}. Curren die is: {self._die}, \
                trying to set value {new_value_str}")
                if str(fuse_str).startswith(self._die):
                    new_value = int(new_value_str,16)
                    result = self._fuse_actions.perform_override(socket=self._socket, new_value=new_value,
                                                                 search_string=fuse_str)
                    if result != FrameworkVars.SUCCESS:
                        return result
        return result

    def _get_cbb_base_id(self)->int:
        return int(self._die.split(".")[0].replace("cbb", ""))

    def _get_relative_bit(self, module_str: str)->List[int]:
        cbb_id = self._get_cbb_base_id()
        module = int(module_str)
        relative_module = module - (32 * cbb_id)
        return relative_module

    def perform_core_module_disabling(self) -> int:
        result = FrameworkVars.SUCCESS
        relative_bits = []
        modules = []
        for fuse in self._fuses:
            if "core_module" in fuse:
                self._logger.log(f"THR Dynamic Inject -> Socket:{self._socket} - die: {self._die} - module:{fuse}")
                die_str, x, module_str, enable_str = fuse.strip().split("-")
                if str(die_str).startswith(self._die):
                    relative_bits.append(self._get_relative_bit(module_str=module_str))
                    modules.append(module_str)
        if len(relative_bits) > 0:
            enable = False if enable_str == "False" else True
            self._logger.log(f"THR Dynamic Inject -> Socket:{self._socket} - die: {self._die} - "
                             f"Performing core disabling for modules: {','.join(modules)}")
            result = self._fuse_actions.perform_core_module_disabling(
                socket=self._socket, relative_bits=relative_bits,
                search_string=f"{self._die}.fuses.punit_fuses.fw_fuses_sst_pp_0_module_disable_mask", enable=enable,
                die=self._die)
        return result

    def perform_slice_cbo_disabling(self) -> int:
        result = FrameworkVars.SUCCESS
        slice_cbos = []
        for fuse in self._fuses:
            if "slice_cbo" in fuse:
                self._logger.log(f"THR Dynamic Inject -> Socket:{self._socket} - die: {self._die} - slice cbo:{fuse}")
                die_str, x, slice_cbo_str, enable_str = fuse.strip().split("-")
                if str(die_str).startswith(self._die):
                    slice_cbos.append(int(slice_cbo_str))
        if len(slice_cbos) > 0:
            enable = False if enable_str == "False" else True
            self._logger.log(f"THR Dynamic Inject -> Socket:{self._socket} - die: {self._die} - "
                             f"Performing slice disabling for slice_cbos: {','.join(map(str, slice_cbos))}")
            result = self._fuse_actions.perform_slice_cbo_disabling(
                socket=self._socket, relative_bits=slice_cbos,
                search_string=f"{self._die}.fuses.punit_fuses.fw_fuses_llc_slice_ia_ccp_dis", enable=enable,
                die=self._die)
        return result

    def _provide_fuse_override_iteration(self) -> int:
        self._test_pythonsv_integrity()
        self._logger.log("THR Dynamic Inject -> checking sv.socket0.imh0.taps.cltap0."
                         "cltap_vmchsftop_tap_gba_tl1parcfg.pwrgood_override_en")
        self._sv.socket0.imh0.taps.cltap0.cltap_vmchsftop_tap_gba_tl1parcfg.pwrgood_override_en.show()
        if int(self._sv.socket0.imh0.taps.cltap0.cltap_vmchsftop_tap_gba_tl1parcfg.pwrgood_override_en) > 0:
            self._logger.log("THR Dynamic Inject -> It is ready to perform overrides")
            return 1
        self._logger.log("THR Dynamic Inject -> It is not ready to perform overrides")
        return 0

    def perform_override(self, socket: str, die: str, fuse_override_iteration=None)->int:
        self._fuses.sort()
        self._logger.log(f"THR dynamic injection -> Socket:{socket} -> die:{die}")
        result = FrameworkVars.SUCCESS
        self._socket = socket
        self._die = die
        self._die_obj = self._sv.sockets[int(socket)].get_by_path(f"{die}")
        #self._load_fuse_ram_and_go_offline()
        if fuse_override_iteration is None:
            fuse_override_iteration = self._provide_fuse_override_iteration()
        if not fuse_override_iteration:
            return result
        result = self._perform_voltage_bump()
        if result != FrameworkVars.SUCCESS:
            self._logger.log(f"THR dynamic injection -> Socket:{socket} -> die:{die} -> Result:{result}")
            return result
        result = self._perform_fuse_override()
        if result != FrameworkVars.SUCCESS:
            self._logger.log(f"THR dynamic injection -> Socket:{socket} -> die:{die} -> Result:{result}")
            return result
        result = self.perform_core_module_disabling()
        if result != FrameworkVars.SUCCESS:
            self._logger.log(f"THR dynamic injection -> Socket:{socket} -> die:{die} -> Result:{result}")
            return result
        result = self.perform_slice_cbo_disabling()
        if result != FrameworkVars.SUCCESS:
            self._logger.log(f"THR dynamic injection -> Socket:{socket} -> die:{die} -> Result:{result}")
            return result
        #self._flush_fuse_ram_and_go_online()        
        return result

    def get_dict(self):
        return {self._die_str_exp: self.perform_override}
