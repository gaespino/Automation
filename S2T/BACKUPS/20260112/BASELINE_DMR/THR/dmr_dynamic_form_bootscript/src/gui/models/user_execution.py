from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.gui.models.bootscript_parameter import BootscriptParameter
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.product_independent.json_reader import JsonReader
from diamondrapids.users.THR.dmr_dynamic_form_bootscript.CONSTANTS import Constants
from users.THR.dmr_dynamic_form_bootscript.src.gui.models.recipe import Recipe
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog
import itertools


class UserExecution:
    def __init__(self, logger: ILog, boot_type, json_recipe_data: JsonReader,
                 bootscript_params: list, recipes: list):
        self._logger = logger
        self.recipes = recipes
        self.boot_type = boot_type
        self.bootscript_params = bootscript_params
        self.json_data = json_recipe_data.get("dynamic_injections")

    def set_default_bootscript_parameters(self):
        for key, value in Constants.BOOTSCRIPT_DEFAULT_ARGUMENTS.items():
            bootscript_param = BootscriptParameter(name=key, value=value)
            self.bootscript_params.append(bootscript_param)

    def get_default_fuses(self, injection_name: str):
        fuses = []
        recipe_settings = self.json_data.get(injection_name)
        for item in recipe_settings["fuses"]:
            keys = item["parameters"].keys()
            values = [item["parameters"][k] for k in keys]
            for combination in itertools.product(*values):
                full_string = item["template"]
                for key, val in zip(keys, combination):
                    full_string = full_string.replace(f"&{key}&", val)
                fuses.append(full_string)
        return fuses

    def _validate_core_or_slice_required_parameters(self, injection_name: str, injection_item: dict):
        required_parameters = {'cbb': int, 'core_modules': list} if injection_name == "core_disabling" \
            else {'cbb': int, 'core_modules': list}
        for parameter in required_parameters:
            if parameter not in injection_item.keys():
                self._logger.log(f"[ERROR] THR Dynamic Injection ->"
                                 f"Recipe {injection_name} -> parameter '{parameter}' is required parameter")
                raise ValueError
            if type(injection_item[parameter]) != required_parameters[parameter]:
                self._logger.log(f"[ERROR] THR Dynamic Injection ->"
                                 f"Recipe {injection_name} -> parameter '{parameter}' expected type is "
                                 f"'{required_parameters[parameter].__name__}' not "
                                 f"'{type(injection_item[parameter]).__name__}'")
                raise ValueError
        try:
            cbb_id = int(injection_item[list(required_parameters.keys())[0]])
            modules = [int(x) for x in injection_item[required_parameters.keys()[1]]]
            return cbb_id, modules
        except Exception as e:
            self._logger.log(f"[ERROR] THR Dynamic Injection ->"
                             f"For recipe {injection_name}. Parameter'core_modules' must be a "
                             f"List of integers and 'cbb' must be an integer")
            raise e

    def _get_core_or_slice_fuses(self, injection_name: str, injection_item: dict):
        cbb_id = None
        core_modules = None
        fuses = []
        cbb_id, modules = self._validate_core_or_slice_required_parameters(injection_name=injection_name,
                                                                           injection_item=injection_item)
        if injection_name == "core_disabling":
            for core_module in modules:
                fuses.append[f"cbb{cbb_id}.base-core_module-{core_module}"]
        elif injection_name == "slice_disabling":
            for slice_module in modules:
                fuses.append[f"cbb{cbb_id}.base-slice_cbo-{slice_module}"]
        return fuses

    def _add_recipe(self, injection_name: str, injection_item: dict):
        recipe_settings = self.json_data.get(injection_name)
        fields = {}
        for field in recipe_settings["fields"]:
            if (field["required"] and field["name"] not in injection_item.keys() and injection_name not in
                    ["core_disabling", "slice_disabling"]):
                self._logger.log(f"[ERROR] THR Dynamic Injection ->"
                                 f"Parameter  '{recipe_settings['fields']['name']}' "
                                 f"is required for injection {injection_name}")
                raise ValueError
            if field["type"] != type(injection_item[field['name']]).__name__:
                self._logger.log(f"[ERROR] THR Dynamic Injection ->"
                                 f"Please add a valid type for injection {injection_name}\n"
                                 f"The type of Parameter {field['name']} is invalid")
                raise TypeError
            if field["name"] in injection_item.keys():
                fields[field["name"]] = injection_item[field['name']]
        if "sockets" not in injection_item.keys():
            injection_item["sockets"]=recipe_settings["sockets"]
        injection_item["type"]=recipe_settings["type"]
        if injection_name in ["core_disabling", "slice_disabling"]:
            injection_item["fuses"] = self._get_core_or_slice_fuses(injection_name=injection_name,
                                                                    injection_item=injection_item)
        elif "fuses" not in injection_item.keys():
            injection_item["fuses"]=self.get_default_fuses(injection_name=injection_name)
        recipe = Recipe(name=injection_name,
                        recipe_type=recipe_settings["type"],
                        fields=fields,
                        sockets=injection_item["sockets"],
                        fuses=injection_item["fuses"])
        self.recipes.append(recipe)

    def _post_process_fuse_list_overrides(self, injection_name: str, fuse_list_overrides: list):
        for item in fuse_list_overrides:
            if type(item) != dict:
                self._logger.log(f"Please check injections {injection_name}, "
                                 f"Parameter:\n{item}\n is invalid the value for this parameter must be DICT:\n"
                                 f"Expected 'DICT' but got '{str(type(item)).upper()}'")
                raise ValueError
            self._add_recipe(injection_name=injection_name, injection_item=item)


    def _post_process_injection(self, injection_name: str, injection_value: list or dict):
        fuse_list_overrides = []
        if type(injection_value)==dict:
            fuse_list_overrides.append(injection_value)
        elif type(injection_value)==list:
            fuse_list_overrides = injection_value
        else:
            self._logger.log(f"Please check injections {injection_name}, "
                             f"the value for this parameter must be LIST or DICT:\n"                             
                             f"Expected 'DICT' or 'LIST' but got '{str(type(injection_value)).upper()}'")
            raise ValueError
        self._post_process_fuse_list_overrides(injection_name=injection_name, fuse_list_overrides=fuse_list_overrides)

    def _post_process_injections(self, injections: dict):
        if type(injections) != dict:
            self._logger.log(f"Please provide a valid set of injections, value type in parameter:"
                             f"{Constants.DEFAULT_PARAMETER_THR_DINAMYC_INJECTION_NAME} is invalid\n"
                             f"Expected 'DICT' but got '{str(type(injections)).upper()}'")
            raise ValueError
        for injection_name, injection_value in injections.items():
            self._post_process_injection(injection_name=injection_name, injection_value=injection_value)

    def set_args(self, **args):
        for name, value in args.items():
            if name == "thr_dynamic_injections":
                self._post_process_injections(injections=value)
            else:
                bootscript_parameter = BootscriptParameter(name=name, value=value)
                self.bootscript_params.append(bootscript_parameter)
