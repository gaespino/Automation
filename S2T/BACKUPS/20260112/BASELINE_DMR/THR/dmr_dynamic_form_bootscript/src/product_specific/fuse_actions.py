from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.product_specific.module_mask_manager import \
                ModuleMaskManager
from diamondrapids.users.THR.product_independent.adapters.sv_adapter import SvAdapter
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog
from pysvtools.bootscript import FrameworkVars
from namednodes.registers import RegisterValue
import diamondrapids.pm.pmutils.convert as c
import namednodes.registers
from typing import List


class FuseActions:
    def __init__(self, logger: ILog, sv: SvAdapter, ignore_zero_values: bool=True):
        self._sv = sv
        self._logger = logger
        self._ignore_zero_values = ignore_zero_values

    @staticmethod
    def _get_offset(offset: float) -> int:
        sign = 1
        if offset < 0:
            sign = -1
            offset = abs(offset)
        vid_offset = c.convert.float2bin(offset, "U1.8")
        result_offset = sign * int(vid_offset)
        return result_offset

    def provide_fuse_override_iteration(self) -> int:
        if not self._sv.socket0.io0.taps.cltap0.cltapc_miscstatus1.cpu_powergood or \
                self._sv.socket0.io0.uncore.hwrs.gpsb.hwrs_cmd_current_index < 0x5D:
            return 0
        return 1

    @staticmethod
    def _get_fuse_width(fuse_obj: RegisterValue) -> int:
        fuse_width = int(fuse_obj.get_access_info()['FUSE_WIDTH'])
        return fuse_width

    @staticmethod
    def _get_logging_width(fuse_length: int) -> int:
        length = int(fuse_length / 4)
        if fuse_length % 2 == 0:
            return length
        else:
            return length + 1

    def _get_segment(self) -> str:
        from pysvtools.bootscript import BootVars as bv
        segment = bv.boot_vars.status.get_segment_tap(bv.boot_vars.COMPUTE_CONFIG)
        return segment

    def _get_fuse_obj(self, socket: str, search_string: str)-> namednodes.registers.RegisterValue:
        fuse_obj = None
        try:
            fuse_obj = self._sv.sockets[int(socket)].get_by_path(f"{search_string}")
        except ValueError as ve:
            self._logger.log(f"WARNING -> ValueError -> "
                             f"Unknown path:sv.socket{socket}.{search_string}\n{str(ve)}")
        except Exception as e:
            self._logger.log(
                f"Exception -> reading override for sv.socket{socket}.{search_string}\n{str(e)}")
        return fuse_obj

    def perform_slice_cbo_disabling(self, socket: str, relative_bits: List[int],
                               search_string: str, enable: bool, die: str) -> int:
        fuse_obj = self._get_fuse_obj(socket=socket, search_string=search_string)
        if fuse_obj is not None:
            current_mask = int(hex(fuse_obj), 16)
            fuse_width = self._get_fuse_width(fuse_obj)
            hex_logging_width = self._get_logging_width(fuse_width)
            self._logger.log(f"THR Dynamic Inject -> Reading mask for fuse: {search_string}->"
                             f"0x{current_mask:0{hex_logging_width}x}")
            if self._ignore_zero_values and current_mask == 0:
                return FrameworkVars.SUCCESS
            manager = ModuleMaskManager(
                logger=self._logger, relative_bits=relative_bits, current_mask=current_mask,
                enable=enable)
            new_mask = manager.apply()
            self._logger.log(f"THR Dynamic Inject -> Getting new mask for fuse: {search_string}->"
                             f"0x{current_mask:0{hex_logging_width}x}->0x{new_mask:0{hex_logging_width}x}")
            from diamondrapids.toolext.bootscript.toolbox import fuse_overrides as fo
            slice_disable = fo.LlcSliceDisable(socket_num=int(socket), die=die, disable_mask=new_mask)
            return slice_disable.apply()

    def perform_core_module_disabling(self, socket: str, relative_bits: List[int],
                               search_string: str, enable: bool, die: str) -> int:
        fuse_obj = self._get_fuse_obj(socket=socket, search_string=search_string)
        if fuse_obj is not None:
            current_mask = int(hex(fuse_obj), 16)
            fuse_width = self._get_fuse_width(fuse_obj)
            hex_logging_width = self._get_logging_width(fuse_width)
            self._logger.log(f"THR Dynamic Inject -> Reading mask for fuse: {search_string}->"
                             f"0x{current_mask:0{hex_logging_width}x}")
            if self._ignore_zero_values and current_mask == 0:
                return FrameworkVars.SUCCESS
            self._logger.log(f"THR Dynamic Inject -> Relative bits are: {'.'.join(map(str, relative_bits))}")
            manager = ModuleMaskManager(
                logger=self._logger, relative_bits=relative_bits, current_mask=current_mask,
                enable=enable)
            new_mask = manager.apply()
            self._logger.log(f"THR Dynamic Inject -> Getting new mask for fuse: {search_string}->"
                             f"0x{current_mask:0{hex_logging_width}x}->0x{new_mask:0{hex_logging_width}x}")
            from diamondrapids.toolext.bootscript.toolbox import fuse_overrides as fo
            core_disable = fo.IaCoreDisable(socket_num=int(socket), die=die,
                                            disable_mask=new_mask)
            return core_disable.apply()

    def perform_voltage_bump(self, socket: str, offset: float, search_string: str) -> int:
        self._logger.log(f"INFO -> THR Dynamic Injection: Performing voltage bump for socket"
                         f"sv.socket{socket}.{search_string}")
        try:
            fuse_obj = self._sv.sockets[int(socket)].get_by_path(f"{search_string}")
            current_value = int(hex(fuse_obj), 16)
            current_setting = c.convert.bin2float(fuse_obj, "U1.8")
            if self._ignore_zero_values and current_value == 0:
                return FrameworkVars.SUCCESS
            vid_offset = self._get_offset(offset)
            new_value = int(fuse_obj) + vid_offset
            new_setting = c.convert.bin2float(str(new_value), "U1.8")
            fuse_width = self._get_fuse_width(fuse_obj)
            fuse_obj.write(new_value)
            hex_logging_width = self._get_logging_width(fuse_width)
            self._logger.log(f"INFO -> THR Dynamic Injection -> socket:{socket}, "                             
                             f"sv.socket{socket}.{search_string} = "
                             f"{current_setting:.3f} -> "
                             f"{new_setting:.3f} = "
                             f"0x{int(current_value):0{hex_logging_width}x} -> "
                             f"0x{new_value:0{hex_logging_width}x}")
        except ValueError as ve:
            self._logger.log(f"WARNING -> ValueError -> "
                             f"Unknown path:sv.socket{socket}.{search_string}\n{str(ve)}")
        except Exception as e:
            self._logger.log(
                f"Exception -> running override for sv.socket{socket}.{search_string}\n{str(e)}")
            return FrameworkVars.GENERAL_ERROR
        return FrameworkVars.SUCCESS

    def perform_override(self, socket: str, new_value: int, search_string: str) -> int:
        self._logger.log(f"INFO -> THR Dynamic Injection: Performing voltage bump for socket"
                         f"sv.socket{socket}.{search_string}")
        try:
            fuse_obj = self._sv.sockets[int(socket)].get_by_path(f"{search_string}")
            current_value = int(hex(fuse_obj), 16)
            if self._ignore_zero_values and current_value == 0:
                return FrameworkVars.SUCCESS
            fuse_width = self._get_fuse_width(fuse_obj)
            fuse_obj.write(new_value)
            hex_logging_width = self._get_logging_width(fuse_width)
            self._logger.log(f"INFO -> THR Dynamic Injection -> socket:{socket}, "                            
                             f"sv.socket{socket}.{search_string} = "
                             f"0x{int(current_value):0{hex_logging_width}x} -> "
                             f"0x{new_value:0{hex_logging_width}x}")

        except ValueError as ve:
            self._logger.log(f"WARNING -> ValueError -> "
                             f"Unknown path:sv.socket{socket}.{search_string}\n{str(ve)}")
        except Exception as e:
            self._logger.log(
                f"Exception -> running override for sv.socket{socket}.{search_string}\n{str(e)}")
            return FrameworkVars.GENERAL_ERROR
        return FrameworkVars.SUCCESS
