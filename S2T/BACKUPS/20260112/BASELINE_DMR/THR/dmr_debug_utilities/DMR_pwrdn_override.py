import os
import sys
import namednodes
import ipccli
import itpii
print ("CWF Powerdown Override || REV 0.8")

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=================================== IPC AND SV SETUP ===================================================#
#========================================================================================================#

ipc = None

sv = None
sv = namednodes.sv #shortcut
sv.initialize()

def _get_global_sv():
  # Lazy initialize for the sv "socket" instance
  # Return
  # ------
  # sv: class "components.ComponentManager"
  
  global sv
  if sv is None:
    from namednodes import sv
    sv.initialize()
    #import components.socket as skt
    #skts = skt.getAll()
  if not sv.sockets:
    print("No socketlist detected. Restarting baseaccess and sv.refresh")
    sv.initialize()
    sv.refresh()
  return sv

def _get_global_ipc():
  # Lazy initialize for the global IPC instance
  global ipc
  if ipc is None:
    import ipccli
    ipc = ipccli.baseaccess()
  return ipc

ipc = _get_global_ipc()
sv = _get_global_sv()
itp = itpii.baseaccess()

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== CONSTANTS AND GLOBAL VARIABLES =========================================================#
#========================================================================================================#

cbb_pwrdn_dict = {
    "top_die": {
        "cores": {
            "sv.sockets.cbbs.computes.modules.cores.ifu_cr_pwrdn_ovrd": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.ifu_cr_pwrdn_ovrd2": 0x8000003F,
            "sv.sockets.cbbs.computes.modules.cores.bpu1_cr_pwrdn_ovrd": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.bac_cr_pwrdn_ovrd": 0x1F9F,
            "sv.sockets.cbbs.computes.modules.cores.dsbfe_cr_pwrdn_ovrd": 0x41FFBF,
            "sv.sockets.cbbs.computes.modules.cores.ieslow_cr_ieu_pwrdn_ovrd": 0xFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.ieslow_cr_fp_pwrdn_ovrd": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.ieslow_cr_tm_pwrdn_ovrd": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.ieslow_cr_tm_pwrdn_ovrd2": 0x3FFE,
            "sv.sockets.cbbs.computes.modules.cores.ieslow_cr_si_pwrdn_ovrd": 0x1FFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.ag_cr_pwrdn_ovrd": 0x7F,
            "sv.sockets.cbbs.computes.modules.cores.mi_cr_pwrdn_ovrd": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.mi_cr_pwrdn_ovrd2": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.pmh_cr_pwrdn_ovrd": 0x17FBFD,
            "sv.sockets.cbbs.computes.modules.cores.dcu_cr_pwrdn_ovrd": 0x3F80FFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.dtlb_cr_pwrdn_ovrd": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.mob_cr_pwrdn_ovrd": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.ms_cr_pwrdn_ovrd_2": 0xF80FFFDF,
            "sv.sockets.cbbs.computes.modules.cores.ms_cr_pwrdn_ovrd": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.iq_cr_pwrdn_ovrd": 0x7EFC7BFF,
            "sv.sockets.cbbs.computes.modules.cores.iq_cr_pwrdn_ovrd2": 0x800003F9,
            "sv.sockets.cbbs.computes.modules.cores.rob1_cr_pwrdn_ovrd": 0x1F3FFEFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.rat_cr_pwrdn_ovrd": 0xFDBFFFFFFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.rat_cr_pwrdn_ovrd2": 0x7FFC1FFF,
            "sv.sockets.cbbs.computes.modules.cores.al_cr_alloc_pwrdn_ovrd": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.rs_cr_alloc_pwrdn_ovrd": 0x1FFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.rs_cr_alloc_pwrdn_ovrd1": 0xF,
            "sv.sockets.cbbs.computes.modules.cores.rs_cr_rs_pwrdn_ovrd": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.cores.rsvec_cr_rs2_pwrdn_ovrd": 0x1FFFFFFF
        },
        "modules": {
            "sv.sockets.cbbs.computes.modules.ml2_cr_pwrdn_ovrd": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.ml3_cr_pwrdn_ovrd": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.ml4_cr_pwrdn_ovrd": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.modules.ml6_cr_pwrdn_ovrd": 0xFFFFF,
            "sv.sockets.cbbs.computes.modules.ctap_cr_pwrdn_ovrd_core": 0xFF
        },
        "computes": {
            "sv.sockets.cbbs.computes.mcast_core.core_gpsb_top.core_pma_gpsb.pwrdn_ovrd": 0xFFFFFFFF,
            "sv.sockets.cbbs.computes.pmas.gpsb.pwrdn_ovrd": 0xFFFFFFFF
        }
    },
    "base_die": {
        "sv.sockets.cbbs.base.ccf_pmsb_envs.clr_pmsb_top.pma_regs_cbos.misc_cfg.pwrdn_ovrd": 0x1,
        "sv.sockets.cbbs.base.i_ccf_envs.cbo_dtf_obs_enc_regss.dso_cfg_dtf_src_config_reg.pwrdn_ovrd": 0x1,
        "sv.sockets.cbbs.base.i_ccf_envs.cfi_obss.rx_dso.dso_cfg_dtf_src_config_reg.pwrdn_ovrd": 0x1,
        "sv.sockets.cbbs.base.i_ccf_envs.cfi_obss.tx_dso.dso_cfg_dtf_src_config_reg.pwrdn_ovrd": 0x1,
        "sv.sockets.cbbs.base.i_ccf_envs.egresss.pwrdn_ovrd": 0x7FFFFFFFFF,
        "sv.sockets.cbbs.base.i_ccf_envs.ingresss.cbo_pwrdn_ovrd2": 0x1FF,
        "sv.sockets.cbbs.base.i_ccf_envs.ncu_dtf_obs_enc_regs.dso_cfg_dtf_src_config_reg.pwrdn_ovrd": 0x1,
        "sv.sockets.cbbs.base.punit_regs.punit_gpsb.gpsb_infst_io_regs.misc_pcode_hw_configs_infst.pwrdn_ovrd_st_ios": 0x1,
        "sv.sockets.cbbs.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.pwrdn_ovrd": 0xFFFFFFF,
        "sv.sockets.cbbs.base.punit_regs.punit_gpsb.punit_dso_regs.dso_cfg_dtf_src_config_reg.pwrdn_ovrd": 0x1,
        "sv.sockets.cbbs.base.sb_obss.sb_obs_dtf_obs_enc_regs.dso_cfg_dtf_src_config_reg.pwrdn_ovrd": 0x1,
        "sv.sockets.cbbs.pcudata.pwrdn_ovrd": 0xFFFFFFF,
        "sv.sockets.cbbs.pcudata.misc_pcode_hw_configs_infst.pwrdn_ovrd_st_ios": 0x1,
        "sv.sockets.cbbs.pcudata.dso_cfg_dtf_src_config_reg.pwrdn_ovrd": 0x1
    }
}

cbb_pwrdn_dict_orig = {
    "top_die": {
        "cores": {},
        "modules": {},
        "computes": {}
    },
    "base_die": {}
}

imhs_pwrdn_dict = {
    "sv.sockets.imhs.punit.ptpcfsms.ptpcfsms.pwrdn_ovrd": 0x3F,
    "sv.sockets.imhs.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.pmsb_pwrdn_ovrd": 0x3F,
    "sv.sockets.imhs.punit.ptpcioregs.ptpcioregs.dso_cfg_dtf_src_config.pwrdn_ovrd": 0x1,
    "sv.sockets.imhs.scf.cms.cmss.pwrdn_ovrd": 0xFFFFFFFFF,
    "sv.sockets.imhs.scms_multicasts.cms_uni.pwrdn_ovrd": 0xFFFFFFFFF,
    "sv.sockets.imhs.scf.sca.scas.ingress.ing_pwrdn_ovrd": 0x1FF,
    "sv.sockets.imhs.scf.sca.sca_multi.ingress.ing_pwrdn_ovrd": 0x1FF,
    "sv.sockets.imhs.scf.sca.scas.pipe.pipe_pwrdn_ovrd": 0x1FFFF,
    "sv.sockets.imhs.scf.sca.sca_multi.pipe.pipe_pwrdn_ovrd": 0x1FFFF,
    "sv.sockets.imhs.scf.sca.scas.util.util_pwrdn_ovrd": 0xF,
    "sv.sockets.imhs.scf.sca.sca_multi.util.util_pwrdn_ovrd": 0xF
}

_pwrdn_dict = { 
    #Dictionary containing all "pwrdn_ovrd" register values, with all of their bits set to 1 (0xFFFF…)
    #This dictionary can be modified using the scripts in this file.
"arr_cr_pwrdn_ovrd" : 0x1FFFFFFFF,
"bp_cr_pwrdn_ovrd" : 0x3FFFFFFFFFF,
"fpc_cr_pwrdn_ovrd" : 0xFFFFFFFFFFFFFF,
"ic_cr_pwrdn_ovrd" : 0xFFFFFFFF,
"iec_cr_pwrdn_ovrd" : 0x1FFFFE,
"mec_cr_pwrdn_ovrd_dcu" : 0x7FFFFFFF,
"mec_cr_pwrdn_ovrd_pmh" : 0xA1F,
"ms_cr_pwrdn_ovrd" : 0x3FFFFF   
}            

_pwrdn_dict_orig = {  
    #Dictionary containing all "pwrdn_ovrd" register values, with all of their bits set to 0 (0x0…)
    #This dictionary can be modified using the scripts in this file.
"arr_cr_pwrdn_ovrd" : 0x0,
"bp_cr_pwrdn_ovrd" : 0x0,
"fpc_cr_pwrdn_ovrd" : 0x0,
"ic_cr_pwrdn_ovrd" : 0x0,
"iec_cr_pwrdn_ovrd" : 0x0,
"mec_cr_pwrdn_ovrd_dcu" : 0x0,
"mec_cr_pwrdn_ovrd_pmh" : 0x0,
"ms_cr_pwrdn_ovrd" : 0x0
}

CWF_PYHS_MODULES = [6,7,8,13,14,15,20,21,22,27,28,29,34,35,36,41,42,43,48,49,50,55,56,57]
CWF_CORES_PER_MODULE = 4
#========================================================================================================#
#=============== Helper functions ==========================================================================#
#========================================================================================================#

def _replace_keys_in_string(input_string, replacements_dict):
    """
    Auxiliar function that replaces keys in the input string with their corresponding values from the dictionary.

    :param input_string: The original string where replacements will be made.
    :param replacements_dict: A dictionary where keys are substrings to be replaced and values are the replacements.
    :return: The modified string with all specified keys replaced by their values.
    """
    for key, value in replacements_dict.items():
        input_string = input_string.replace(key, str(value))
    return input_string


def _get_deepest_keys_iteratively(d):
    """
    Iteratively traverse the dictionary to collect keys from the deepest levels.

    :param d: The dictionary to traverse.
    :return: A list of keys from the deepest levels.
    """
    deepest_keys = []
    stack = [d]

    while stack:
        current_dict = stack.pop()
        for key, value in current_dict.items():
            if isinstance(value, dict):
                # Push nested dictionary onto the stack
                stack.append(value)
            else:
                # If the value is not a dictionary, add the key to the list
                deepest_keys.append(key)

    return deepest_keys


def _read_current_pwrdn_values_aux(pwrdns, replacements_dict):
    """
    Evaluate and print the current power-down values for a list of paths.

    This function iterates over a list of power-down paths, replaces placeholders in each path
    using a provided dictionary, evaluates the modified path to read the current power-down value,
    and prints the result.

    :param pwrdns: A list of strings representing paths to power-down values. These paths may contain
                   placeholders that need to be replaced.
    :param replacements_dict: A dictionary where keys are placeholders in the paths and values are
                              the replacements to be used. This dictionary is used to modify each path
                              before evaluation.
    """
    for pwrdn_path in pwrdns:
        eval_str = pwrdn_path
        eval_str = _replace_keys_in_string(eval_str, replacements_dict)
        try:
            # Reads the current value for the power down
            pwrdn_value = eval(eval_str)
            print(f"{eval_str} : {pwrdn_value}")
        except AttributeError as e:
            print(f"An AttributeError occurred reading '{eval_str}': {e}")

#========================================================================================================#
#=============== DEBUG SCRIPTS ==========================================================================#
#========================================================================================================#



def disable_imhs_pwrdn(target_socket=None, target_imh=None):
    pass

def save_register_values_to_orig_pwrdn(target_compute, target_module, target_core, verbose):
    pass
    


def disable_pwrdn(dictionary=_pwrdn_dict, cr_array_start=0, cr_array_end=0xffff, skip_index_array=[], save_orig_values=None, restore_orig_values=False, target_compute=None, target_module=None, target_core=None, verbose=False):  #100%
    """
    Given a pwrdn register dictionary, overwrite all registers assigned to each core of the unit. This script has the option to call save_register_values_to_orig_pwrdn() and write_orig_pwrdn_values_to_registers() 
    (with their own parameters) before executing, to be able to save previous or current values into _pwrdn_dict_orig dictionary.
    It is recommended to use this function with default value array=_pwrdn_dict.

    Inputs:
        array: (Dictionary, Default=_pwrdn_dict)
        cr_array_start: (Hex, Default=0x0) Index to start on in cr_array -- for minimization
        cr_array_end: (Hex, Default=0xffff) Index to end on in cr_end -- for minimization
        skip_index_array: (List, Default = []) array of cr indexes to skip -- for minimization
        save_orig_values (Boolean, Default=None): If set, will save current pwrdn registers value into _pwrdn_dict_orig dictionary, to be able to restore them after overrides.
        restore_orig_values (Boolean, Default=False): If set, will override all pwrdn registers with the values previously saved in _pwrdn_dict_orig dictionary. 
        target_compute: (Int, Default=None) Parameter for both save_register_values_to_orig_pwrdn() and write_orig_pwrdn_values_to_registers() functions. See documentation.
        target_module: (Int, Default=None) Parameter for both save_register_values_to_orig_pwrdn() and write_orig_pwrdn_values_to_registers() functions. See documentation.
        target_core: (Int, Default=None) Parameter for both save_register_values_to_orig_pwrdn() and write_orig_pwrdn_values_to_registers() functions. See documentation.
        verbose: (Boolean, Default=False) more info for debugging.
    """

    if save_orig_values is None:
        raise ValueError("-E- Specify if you want to save original power downs values before disable them") # Throw error
    elif save_orig_values == True:
        save_register_values_to_orig_pwrdn(target_compute=target_compute, target_module=target_module, target_core=target_core, verbose=verbose) # Save current register values into dictionary before executing
    
    if restore_orig_values == True:
        write_orig_pwrdn_values_to_registers(target_compute=target_compute, target_module=target_module, target_core=target_core, verbose=verbose) # Restore dictionary values into registers before executing 
		
    ipc.halt()
    crarray = dictionary # Input register dictionary
    num_crs = len(crarray) # Dictionary size

    # TODO: Check that cr_array_end, cr_array_start and all elements within skip_index_array are within the bounds of the crarray
    if ((cr_array_start !=0) or (cr_array_end != 0xffff)):
        num_crs = cr_array_end - cr_array_start  # Blind calc.  Doesn"t check against number of items in array

    print ("Setting %d CRs " % num_crs)
    index = 0
    for n in sorted(crarray): # For each element in input register dictionary
        if (index not in skip_index_array) and (index >= cr_array_start) and (index<=cr_array_end): #If not skipped
            key = n # Current register name
            value = dictionary[key] # Get value from register 
            reg = sv.socket0.computes.cpu.modules.cores.get_by_path(key) # Get all registers with name given by the dictionary
            if verbose: print(f"Register ovewritten: sv.socket0.computes.cpu.modules.cores.{key}")
            reg.write(value) # Write dictionary value into registers
        else:
            print ("%d: !!!! skipping %s" % (index, n)  )
        index +=1

    ipc.go()
    print("Done")
    return True


def _save_current_pwrdns_values_to_orig_dict(pwrdns, orig_dict, component):
    """
    Save current power-down register values to an original dictionary.
    
    This function iterates over a list of power-down paths, attempts to retrieve their
    current values from the specified component, and stores them in a dictionary for
    later restoration or reference.
    
    Args:
        pwrdns (list): List of power-down register paths (strings) to be processed.
                      Each path should be a valid dot-separated path.
        orig_dict (dict): Dictionary where the original register values will be stored.
                         Modified in-place. Keys will be the full paths and values
                         will be the objects/values obtained from the component.
        component (namednodes.comp._group.ComponentGroup): Component object containing the power-down registers.
                  Must implement the get_by_path() method to access registers by name.
    
    Returns:
        None: The function modifies the orig_dict dictionary directly.
    """
    for pwrdn_path in pwrdns:
        pwrdn_name = pwrdn_path.split(".")[-1]
        try:
            pwrdn_values = component.get_by_path(pwrdn_name).read()
            #if isinstance(pwrdn_values, namednodes.comp._group.ComponentGroup):
            orig_dict[f"sv.{component.path}.{pwrdn_name}"] = component.get_by_path(pwrdn_name)
        except:
            orig_dict[f"sv.{component.path}.{pwrdn_name}"] = None

            if hasattr(component, "__len__"):
                for part in component:
                    print(f"Not possible to access and save this register: 'sv.{part.path}.{pwrdn_name}'")
            else:
                print(f"Not possible to access and save this register: 'sv.{component.path}.{pwrdn_name}'")




def save_register_values_to_orig_cbb_pwrdn(target_socket = None, target_cbb = None, target_compute=None, target_module=None, target_core=None, verbose=False):
    cores_pwrdns = cbb_pwrdn_dict["top_die"]["cores"]
    modules_pwrdns = cbb_pwrdn_dict["top_die"]["modules"]
    computes_pwrdns = cbb_pwrdn_dict["top_die"]["computes"]
    base_die_pwrdns = cbb_pwrdn_dict["base_die"]

    sockets = [eval(f"sv.socket{target_socket}")] if target_socket else sv.sockets

    if target_socket == 0:
        sockets = [sv.socket0]
    elif target_socket == 1:
        sockets = [sv.socket1]
    else:
        sockets = sv.sockets
    
    #cbbs = sockets.get_by_path(f"cbb{target_cbb}") if target_cbb is not None else sockets.cbbs
    #computes = cbbs.get_by_path(f"compute{target_compute}") if target_compute is not None else cbbs.computes
    #modules = [computes.get_by_path(f"module{target_module}")] if target_module is not None else computes.modules
    #cores = [modules.get_by_path(f"core{target_core}")] if target_core is not None else modules.cores

    for socket in sockets:
        cbbs = [socket.get_by_path(f"cbb{target_cbb}")] if target_cbb is not None else socket.cbbs
        for cbb in cbbs:
            computes = [cbb.get_by_path(f"compute{target_compute}")] if target_compute is not None else cbb.computes
            for compute in computes:
                # Save the compute-level power downs
                _save_current_pwrdns_values_to_orig_dict(computes_pwrdns, cbb_pwrdn_dict_orig["top_die"]["computes"], compute)

                modules = [compute.get_by_path(f"module{target_module}")] if target_module is not None else compute.modules

                for module in modules:                    
                    # Save the module-level power downs
                    _save_current_pwrdns_values_to_orig_dict(modules_pwrdns, cbb_pwrdn_dict_orig["top_die"]["modules"], module)

                    cores = [module.get_by_path(f"core{target_core}")] if target_core is not None else module.cores

                    for core in cores:
                        # Save the module-level power downs
                        _save_current_pwrdns_values_to_orig_dict(cores_pwrdns, cbb_pwrdn_dict_orig["top_die"]["cores"], core)


def save_register_values_to_orig_pwrdn_bk(target_compute=None, target_module=None, target_core=None, verbose=False):
    """
    Writes register values into the dictionary "_pwrdn_dict_orig",  from the specified target compute, module and core.

    Inputs:
        target_compute: (Int, Default=None) Specific compute to read. If none is given, read from compute 0.
        target_module: (Int, Default=None) Specific module to read. If none is given, read from module 0.
        target_core: (Int, Default=None) Specific core to read. If none is given, read from core 0.
        verbose: (Boolean, Default=False) more info for debugging.
        
    Output:
        True
    """
    if (target_module==None): # If no target compute is given, set 0 as default 
        target_compute = 0
    if (target_module==None): # If no target module is given, set 6 as default 
        target_module = 6
    if (target_core==None): # If no target core is given, set 0 as default  
        target_core = 0

    ipc.halt()
    for key, value in _pwrdn_dict_orig.items(): # For each key in _pwrdn_dict_orig dictionary 
        eval_str = f"sv.socket0.compute{target_compute}.cpu.module{target_module}.core{target_core}.{key}"  # Add dictionary key to complete the register command
        if(verbose): print(f"Register read: {eval_str}")
        val = eval(eval_str) # Get register value
        _pwrdn_dict_orig[key] = val # Overwrite dictionary with read value.

    ipc.go()
    return True
	
def write_orig_pwrdn_values_to_registers(target_compute=None, target_module=None, target_core=None, verbose=False): 
    """
    Writes dictionary "_pwrdn_dict_orig" values into specified (or all) registers.

    Inputs:
        target_compute: (Int, Default=None) Specific compute to write. If none is given, write to all computes.
        target_module: (Int, Default=None) Specific module to write. If none is given, write to all module.
        target_core: (Int, Default=None) Specific core to write. If none is given, write to all cores.
        verbose: (Boolean, Default=False) more info for debugging.
        
    Output:
        True
    """
    if (target_compute==None): # If no target compute is given, assign an "s" to target all modules
        target_compute = "s"
    if (target_module==None): # If no target module is given, assign an "s" to target all modules 
        target_module = "s"
    if (target_core==None): # If no target core is given, assign an "s" to target all cores 
        target_core = "s"

    ipc.halt()
    for key, value in _pwrdn_dict_orig.items(): # For each dictionary item
        eval_str = f"sv.socket0.compute{target_compute}.cpu.module{target_module}.core{target_core}.{key}"
        if(verbose): print(f"Register written: {eval_str}")
        reg = eval(eval_str) # Get register value
        reg.write(value) # Write dictionary value into register
    ipc.go()
    print(f"Orig_pwrdn values were written into selected compute{target_compute}, module{target_module} and core{target_core}.")
    
    return True	
	
def read_orig_pwrdn_values_bk():
    """
    Prints all keys and values in the dictionary "_pwrdn_dict_orig".

    Output:
        True
    """
    ipc.halt()
    for key, value in _pwrdn_dict_orig.items(): # For each dictionary item
        print ("reg %s : 0x%x" % (key, value)) # Print key and value
    ipc.go()
    return True


def read_current_imh_pwrdn_values():
    """
    Halts the IPC, iterates over each socket and IMH, and reads the current power-down override values
    for each path specified in the imhs_pwrdn_dict. It prints the socket and IMH information along with
    the evaluated power-down values, then resumes the IPC.
    """
    ipc.halt()
    for socket in range (len(sv.sockets)):
        print("\n"+"="*15) 
        print(f"  Socket : {socket}")
        print("="*15)
        for imh in range(len(sv.socket0.imhs)):
            print(f"  IMH : {imh}")
            print("-"*60)

            # Replace the keys by its values in the eval_str
            replacements_dict = {
                "sockets": f"socket{str(socket)}",
                "imhs": f"imh{str(imh)}"
            }
            _read_current_pwrdn_values_aux(imhs_pwrdn_dict, replacements_dict)

            print("-"*60)
    ipc.go()


def read_current_cbb_pwrdn_values():
    # Obtains all cbb powerdowns
    cbb_pwrdns =_get_deepest_keys_iteratively(cbb_pwrdn_dict)
    ipc.halt()
    for socket in range (len(sv.sockets)):
        print("\n"+"="*15) 
        print(f"  Socket : {socket}")
        print("="*15)
        for cbb in range(len(sv.socket0.cbbs)):
            print(f"  CBB : {cbb}")
            print("-"*60)

            replacements_dict = {
                "sockets": f"socket{str(socket)}",
                "cbbs": f"cbb{str(cbb)}"
            }
            _read_current_pwrdn_values_aux(cbb_pwrdns, replacements_dict)
    ipc.go()


def read_current_cbb_pwrdn_values2():
    # Obtains all the power downs in the base die for the cbbs
    base_die_pwrdns = cbb_pwrdn_dict["base_die"]
    cores_top_die_pwrdns = cbb_pwrdn_dict["top_die"]["cores"]
    modules_top_die_pwrdns  = cbb_pwrdn_dict["top_die"]["modules"]
    computes_top_die_pwrdns  = cbb_pwrdn_dict["top_die"]["computes"]

    ipc.halt()
    for socket in range (len(sv.sockets)):
        print("\n"+"="*15) 
        print(f"  Socket : {socket}")
        print("="*15)
        for cbb in range(len(sv.socket0.cbbs)):
            print(f"  CBB : {cbb}")
            print("-"*60)

            # Read power downs in base die
            replacements_dict = {
                "sockets": f"socket{str(socket)}",
                "cbbs": f"cbb{str(cbb)}"
            }
            _read_current_pwrdn_values_aux(base_die_pwrdns, replacements_dict)

            for compute in range(len(sv.socket0.cbb0.computes)):

                # Power downs in top die that reach compute level
                replacements_dict = {
                    "sockets": f"socket{str(socket)}",
                    "cbbs": f"cbb{str(cbb)}",
                    "computes": f"compute{str(compute)}"
                }
                replacements_dict["computes"] = f"compute{str(compute)}"
                _read_current_pwrdn_values_aux(computes_top_die_pwrdns, replacements_dict)

                for module in range(len(sv.socket0.cbb0.compute0.modules)):

                    # Power downs in top die that reach module level
                    replacements_dict = {
                        "sockets": f"socket{str(socket)}",
                        "cbbs": f"cbb{str(cbb)}",
                        "computes": f"compute{str(compute)}",
                        "modules": f"module{str(module)}"
                    }
                    _read_current_pwrdn_values_aux(modules_top_die_pwrdns, replacements_dict)

                    # Power downs in top die that reach core level
                    for core in range(len(sv.socket0.cbb0.compute0.module0.cores)):
                        
                        replacements_dict = {
                            "sockets": f"socket{str(socket)}",
                            "cbbs": f"cbb{str(cbb)}",
                            "computes": f"compute{str(compute)}",
                            "modules": f"module{str(module)}",
                            "cores": f"core{str(core)}"
                        }
                        _read_current_pwrdn_values_aux(cores_top_die_pwrdns, replacements_dict)
    ipc.go()



def read_current_pwrdn_values_bk():
    """
    Prints all current pwrdn register values from all modules and cores.

    Output:
        True
    """
    ipc.halt()
    for socket in range (len(sv.sockets)): # For each socket
        print("\n"+"="*15) 
        print(f"  Socket : {socket}")
        print("="*15)
        for compute in range (len(sv.socket0.computes)): # For each compute   
            print(f"  Compute : {compute}")
            print("-"*60)
            for module in CWF_PYHS_MODULES: # For each module
                for core in range(CWF_CORES_PER_MODULE): # For each core
                    for key, value in _pwrdn_dict_orig.items(): # For each item in _pwrdn_dict_orig dictionary
                        eval_str = f"sv.socket{socket}.compute{compute}.cpu.module{module}.core{core}.{key}" # Add dictionary key to complete the register command
                        val = eval(eval_str) # Get register value
                        print(f"{eval_str} : {val}")
                        #print (f" Phys Module{module} - Core{core}: reg {key} : {val}") # Print information
                    print("-"*60)
            print("="*60+"\n")
   

    ipc.go()
    return True
    

#========================================================================================================#
#=============== END OF AVAILABLE SCRIPTS ===============================================================#
#========================================================================================================#

