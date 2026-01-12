from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.product_specific.dynamic_injection import DmrDynamicInjection
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.interfaces.iboot_script_adapter import IBootScriptAdapter
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.gui.models.recipe import Recipe
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.interfaces.iboot import IBoot
from diamondrapids.users.THR.product_independent.adapters.sv_adapter import SvAdapter
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog
from users.THR.product_independent.adapters.ipc_adapter import IpcAdapter
from typing import List
import re


class PlatformBoot(IBoot):
    def __init__(self, logger: ILog, recipes: List[Recipe], sv: SvAdapter, itp: IpcAdapter,
                 bootscript: IBootScriptAdapter) -> None:
        self._bootscript = bootscript
        self._thr_injections = []
        self._recipes = recipes
        self._logger = logger
        self._itp = self._ipc = itp
        self._sv = sv

    def _add_thr_injection_to_list(self, die_str_exp: str, fuse: str):
        found = False
        for index, injection in enumerate(self._thr_injections):
            if injection.get_die_str_exp() == die_str_exp:
                self._thr_injections[index].add_fuse(fuse)
                found = True
                break
        if not found:
            thr_injection = DmrDynamicInjection(logger=self._logger, die_str_exp=die_str_exp,
                                                sv=self._sv, itp=self._itp)
            thr_injection.add_fuse(fuse_str=fuse)
            self._thr_injections.append(thr_injection)
        return found

    @staticmethod
    def _get_die_str(fuse: str, socket_id: str):
        die = ""
        die_str_exp = ""
        if re.findall(r"cbb\d\.base.*", fuse):
            die = f"{fuse.split('.')[0]}"
            die = die.replace("cbb", "cbb_base")
            die_str_exp = f"{die}_s{socket_id}"
        elif re.findall(r"cbb\d\.compute.*", fuse):
            die = f"{fuse.split('.')[0]}"
            compute = f"{fuse.split('.')[1]}"
            compute_id  = compute.replace("compute", "")
            die_str_exp = f"{die}_top{compute_id}_s{socket_id}"
        elif fuse.startswith("imh"):
            die = f"{fuse.split('.')[0]}"
            die_str_exp = f"{die}_s{socket_id}"
        else:
            die_str_exp = f"{fuse.split('.')[0]}_s{socket_id}"
        return die_str_exp

    def _post_process_recipes(self):
        for recipe in self._recipes:
            for socket in recipe.sockets:
                for fuse_str in recipe.fuses:
                    self._logger.log(f"THR dynamic injection -> validating recipe: {recipe.name}-> Fuse {fuse_str}")
                    if recipe.recipe_type == "voltage_bump":
                        value = recipe.fields["offset"]
                        fuse_str = f"{fuse_str}*{value}"
                    elif recipe.recipe_type == "fuse_override":
                        value = recipe.fields["new_value"]
                        fuse_str = f"{fuse_str}={value}"
                    elif recipe.recipe_type in ["ip_disable"]:
                        fuse_str = f"{fuse_str}-{True}"
                    self._logger.log(f"THR dynamic injection -> Fuse {fuse_str} - {recipe.recipe_type}")
                    socket_id = socket.replace('socket', '')
                    die_str_exp = self._get_die_str(fuse=fuse_str, socket_id=socket_id)
                    self._add_thr_injection_to_list(die_str_exp=die_str_exp, fuse=fuse_str)


    def go(self, **args)->int:
        self._logger.log(f"Post-procesing bootscript parameters:{dict(args)}")
        self._post_process_recipes()
        if self._thr_injections:
            dict_injections = {}
            for injection in self._thr_injections:
                dict_injections.update(injection.get_dict())
            if "dynamic_fuse_inject" in args:
                args["dynamic_fuse_inject"].update(dict_injections)
            else:
                args["dynamic_fuse_inject"] = dict_injections
            self._logger.log(f"Executing command line\nbs.go({str(args)})")
        return self._bootscript.go(**args)

