import namednodes
#import math #jarojasg
import itpii
import ipccli
#import sys #jarojasg
from ipccli import BitData
#import colorama #jarojasg
#from colorama import Fore #jarojasg
import pm.pmutils.tools as cvt

#import time #jarojasg
# import pm.pmutils.pstatesDebug as pd #jarojasg


import support_files.read_fuses
import importlib
importlib.reload(support_files.read_fuses)
from support_files.read_fuses import generate_fuses


print ("DMR Fuse Override || REV 0.9")



#jarojasg
# sv.project ==> diamondrapids

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=================================== IPC AND SV SETUP ===================================================#
#========================================================================================================#

ipc = None
api = None

sv = None
sv = namednodes.sv
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

#jarojasg
ipc = _get_global_ipc()
sv = _get_global_sv()
itp = itpii.baseaccess()

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== CONSTANTS AND GLOBAL VARIABLES =========================================================#
#========================================================================================================#

#dis_itd_array=["sv.sockets.computes.fuses.pcu.pcode_itd_cutoff_tj=0"] #jarojasg
#mlog ="" #jarojasg

#CWF architecture
COMPUTE_COLUMNS = 10
COMPUTE_ROWS = 8
CORETYPE = "atomcore"
#========================================================================================================#
#=============== DEBUG SCRIPTS ==========================================================================#
#========================================================================================================#

def _set_range(limit, target=None):
    """
    Sets the start and end range for a variable based on a target.
    This is auxiliary function that is used in other functions.

    :param limit: The maximum limit for the variable.
    :param target: The specific target value, if any.
    :return: A tuple containing the start and end values.
    """
    start = 0
    end = limit
    if target is not None:
        start = target
        end = target + 1
    return start, end


def init_routine(init=True, load_fuses=True, halt = False):
    """
    This funtion executes the normal routine for unit initialization and fuse loads.
    
    Inputs:
        init: (Boolean, Default=True) Executes the environment initialization. (itp.forcereconfig, itp.unlock and sv.refresh)
        load_fuses: (Boolean, Default=True) Executes the load_fuse_ram() commands.
        halt: (Boolean, Default=False) Executes itp.halt() command if True.
    """
    if halt: itp.halt()
    if init:
        itp.forcereconfig()
        itp.unlock()
        sv.refresh()
    if load_fuses:
        sv.sockets.imhs.fuses.load_fuse_ram()
        sv.sockets.cbbs.computes.fuses.load_fuse_ram()


def read_array(fuse_array, init=False, load_fuses=False):
    """
    Reads all values of a given register array with the ".get_value()" command.
    
    Inputs:
	    fuse_array: (String array) array of fuses/registers to be read.
	    init: (Boolean, Default=False) if True, execute initialization through init_routine()
	    load_fuses: (Boolean, Default=False) if True, execute fuse loads through init_routine()
    """
    # Environment init and fuse loads 
    init_routine(init, load_fuses, halt = True)
    for f in (fuse_array):
        #For each fuse, evaluate it with ".get_value()" to obtain its values
        value = eval(f+".get_value()")
        print(f"{f} = {value}")

def fuse_cmd_override_reset(fuse_cmd_array, init=False, load_fuses=False, dryrun=False, read=False):
    """
    Given a Fuse or Register array, it has the option to read the value of each register and/or execute its content.
    After this, execute sv.sockets.flush_fuse_ram() and itp.resettarget()

    Inputs:
        fuse_cmd_array: (String array) Fuse/Register array to be read and/or executed.
        init: (Boolean, Default=False) allows to skip sv.refresh and sv.load_fuse_ram commands. 
        dryrun: (Boolean, Default=False) if False, allows to execute the registers given by fuse_cmd_array. 
        read: (Boolean, Default=False) Allows to read and print values of all registers in fuse_cmd_array.   
    """
    # Environment init and fuse loads
    init_routine(init, load_fuses, halt=True) 

    for f in (fuse_cmd_array):
        if read:
            # Get fuse value
            value = eval(f"{f}.get_value()")
            # Print fuse with its respective value
            print(f"{f} = {value}")

        if not dryrun:
            # Executes the fuse
            exec(f)

    sv.sockets.imhs.fuses.load_fuse_ram()
    sv.sockets.cbbs.computes.fuses.load_fuse_ram()

    itp.go()
    itp.resettarget()

def coretile_array(value, verbose=False):
    """
    Given a command string "cmd_string", try to overwrite every register on the coretile with the same name with the specified value.
    This function writes to the registers:
        sv.socket{socket}.cbb{cbb}.compute{compute}.fuses.core{core}_fuse.core_fuse_core_fuse_ucode_fma5_dis

    Inputs:
        Value: (Int) value to write on every register.
        Verbose: (Boolean) shows more info for debugging.

    Output:
        retarray: (String array) Array with the coretile registers for the specified cmd_string.
    """
    CORE_NUMBER = 7
    retarray = []
    for socket in range(len(sv.sockets)): #For each available socket
        for cbb in range(len(sv.socket0.cbbs)): # For each cbb
            for compute in range(len(sv.socket0.cbb0.computes)): #For each available compute
                for core in range(CORE_NUMBER): #For each core
                    try:
                        fuse_str = f"socket{socket}.cbb{cbb}.compute{compute}.fuses.core{core}_fuse.core_fuse_core_fuse_ucode_fma5_dis"

                        # Create a string with the fuse and value being written to return it
                        cmd = f"sv.{fuse_str}={value}"

                        # Write fuse
                        sv.get_by_path(fuse_str).write(value)

                        retarray.append(cmd)                        
                        if verbose: print (f"{cmd} found !!")
                    except:
                        if verbose: print (f"{cmd} not found")
    return retarray

def core_vf_mapping_array():  
    """
    There"s no mapping in DMR since every DCM (Dual Core Module) has its own vf curves.
    """
    raise Exception("There is no mapping in DMR since every DCM (Dual Core Module) has its own vf curves.")


def cfc_fixed_ratio_array(ratio):
    """
    Given a ratio, returns an array with all cfc_ratio registers as strings to be set to that value. 
    THIS FUNCTION DOES NOT WRITE THE VALUES TO THE REGISTERS, it only returns an array with the 
    fuses and their assigned values.
    
    Input:
	    ratio: (Int) value to be assigned on every register.
	
    Output:
        ret_array: (String array) array containing the registers and their assigned values
    """
    fuses = generate_fuses("cfc_flat_ratios")
    return[f"{fuse} = {ratio}" for fuse in fuses]
  

def cfc_ratio_array(): 
    """
    Returns an array with all cfc_ratio registers.

    Output:
        ret_array: (String array) array containing the cfc_ratio registers
    """
    return generate_fuses("cfc_flat_ratios")

def ia_fixed_ratio_array(ratio):
    """
    Given a ratio, returns an array with all ia_ratio registers as strings to be set to that value. 
    THIS FUNCTION DOES NOT WRITE THE VALUES TO THE REGISTERS, it only returns an array with the 
    fuses and their assigned values.

    Input:
        ratio: (Int) value to be assigned on every register.
        
    Output:
        ret_array: (String array) array containing the registers and their assigned values 
    """
    fuses = generate_fuses("ia_flat_ratios")
    return[f"{fuse} = {ratio}" for fuse in fuses]

def ia_ratio_array():
    """
    Returns an array with all ia_ratio registers.

    Output:
        ret_array: (String array) array containing the ia_ratio registers
    """
    return generate_fuses("ia_flat_ratios")

def RWA_override(wl_bias_fuse, wl_bias_step_fuse, wr_ast_pw_fuse, wr_ast_strength_fuse):
    return[
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r5.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r5.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r6.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r6.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r7.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r7.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r5.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r5.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r6.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r6.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r7.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r7.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r5.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r5.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r6.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r6.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r7.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r7.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r5.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r5.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r6.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r6.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r7.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r7.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r5.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r5.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r6.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r6.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r7.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r7.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r5.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r5.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r6.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r6.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r7.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r7.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r5.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r5.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r6.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r6.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r7.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r7.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r5.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r5.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r6.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r6.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r7.core_fb_pma_l2dat_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r7.core_fb_pma_l2tag_wl_bias_fuse = {wl_bias_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r5.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r5.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r6.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r6.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r7.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r7.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r5.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r5.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r6.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r6.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r7.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r7.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r5.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r5.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r6.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r6.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r7.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r7.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r5.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r5.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r6.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r6.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r7.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r7.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r5.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r5.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r6.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r6.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r7.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r7.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r5.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r5.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r6.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r6.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r7.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r7.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r5.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r5.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r6.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r6.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r7.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r7.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r5.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r5.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r6.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r6.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r7.core_fb_pma_l2dat_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r7.core_fb_pma_l2tag_wl_bias_step_fuse = {wl_bias_step_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r5.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r5.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r6.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r6.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r7.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r7.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r5.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r5.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r6.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r6.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r7.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r7.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r5.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r5.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r6.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r6.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r7.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r7.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r5.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r5.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r6.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r6.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r7.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r7.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r5.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r5.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r6.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r6.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r7.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r7.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r5.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r5.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r6.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r6.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r7.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r7.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r5.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r5.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r6.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r6.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r7.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r7.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r5.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r5.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r6.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r6.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r7.core_fb_pma_l2dat_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r7.core_fb_pma_l2tag_wr_ast_pw_fuse = {wr_ast_pw_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r5.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r5.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r6.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r6.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r7.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c1_r7.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r5.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r5.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r6.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r6.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r7.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c2_r7.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r5.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r5.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r6.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r6.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r7.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c3_r7.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r5.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r5.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r6.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r6.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r7.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c4_r7.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r5.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r5.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r6.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r6.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r7.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c5_r7.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r5.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r5.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r6.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r6.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r7.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c6_r7.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r5.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r5.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r6.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r6.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r7.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c7_r7.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r5.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r5.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r6.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r6.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r7.core_fb_pma_l2dat_wr_ast_strength_fuse = {wr_ast_strength_fuse}",
     f"sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c8_r7.core_fb_pma_l2tag_wr_ast_strength_fuse = {wr_ast_strength_fuse}"
    ]

def iccp_fixed_array():
    """
    Returns an array with all ia_iccp_voltage_index registers, to be set to a specific value. 
    THIS FUNCTION DOES NOT WRITE THE VALUES TO THE REGISTERS, it only returns an array with the fuses and their assigned values.

    Output:
        ret_array: (String array) array containing the registers and their assigned values 
    """
    return[
    "sv.sockets.computes.fuses.pcu.pcode_ia_iccp0_to_voltage_index_map = 0x1",
    "sv.sockets.computes.fuses.pcu.pcode_ia_iccp1_to_voltage_index_map = 0x1",
    "sv.sockets.computes.fuses.pcu.pcode_ia_iccp2_to_voltage_index_map = 0x2",
    "sv.sockets.computes.fuses.pcu.pcode_ia_iccp3_to_voltage_index_map = 0x2",
    "sv.sockets.computes.fuses.pcu.pcode_ia_iccp4_to_voltage_index_map = 0x3",
    "sv.sockets.computes.fuses.pcu.pcode_ia_iccp5_to_voltage_index_map = 0x3",
    "sv.sockets.computes.fuses.pcu.pcode_ia_iccp6_to_voltage_index_map = 0x4",
    "sv.sockets.computes.fuses.pcu.pcode_ia_iccp7_to_voltage_index_map = 0x4"
    ]
 
def ia_vbump_array(offset: float = 0, rgb_array={}, init=False, target_socket=None, target_die=None,  target_compute=None, target_core=None, target_index=None, target_point=None, fixed_voltage=None):
    """
    Returns an array with specific ia_vf_voltage_curve registers and values. This script allows targeting specific or multiple computes, curve points, indexes and voltage points. It is possible to apply an offset to each point with the rgb dictionary, as well as apply a fixed voltage value with fixed_voltage.

    Inputs:
        offset: (Int) first offset modifier, value in Volts.
        rgb_array: (Dictionary) Reduced GuardBand array, it is a secondary offset modifier, modifies only the specific licence. Its content keys must be named RGB_<Licence>_F<1-6> and its assigned value must be a float, representing Voltage offset.
            Example:
                rgb_array={ 
                    "RGB_SSE_F1" : 0.003
                    "RGB_SSE_F3" : 0.001
                    "RGB_AVX2_F4" : 0.002
                    "RGB_AVX3_F2" : 0.001
                    "RGB_TMUL_F1" : 0.004}
        init: (Boolean, Default=False) start init sequence.
        target_die: (Int, Default=None) Sets start and end die register to a single target.
        target_compute: (Int, Default=None) Sets start and end compute register to a single target.
        target_core: (Int, Default=None) Sets start and end core register to a single target.
        target_index: (Int, Default=None) Sets start and end index to a single target.
        target_point: (Int, Default=None) Sets start and end point register to a single target.
        Fixed_voltage: (Float, Default=None) Overwrites final voltage value. THIS SHOULD BE IN MILLIVOLTS
        
    Output:
    ret_array: (String array) array containing the registers and their assigned values.
    """
    init_routine(init, init) # Executes init and fuse load sequence if specified

    sockets=len(sv.sockets)
    dies = len(sv.socket0.cbbs)
    computes = len(sv.socket0.cbb0.computes)
    indexes = 4 # Index limit
    points = 12 # Point limit
    cores = 8

    # Return array
    ret_array=[]

    start_die, end_die = _set_range(dies, target_die)
    start_compute, end_compute = _set_range(computes, target_compute)
    start_core, end_core = _set_range(cores, target_core)
    start_index, end_index = _set_range(indexes, target_index)
    start_point, end_point = _set_range(points, target_point)
    
    # Filters to obtain the fuses
    filter_params = {
        "dies": [f"cbb{i}" for i in range(start_die, end_die + 1)],
        "computes": [f"compute{i}" for i in range(start_compute, end_compute + 1)],
        "cores": [f"core{i}" for i in range(start_core, end_core + 1)],
        "idx": [f"idx{i}" for i in range(start_index, end_index + 1)],
        "vf_points": [str(i) for i in range(start_point, end_point + 1)]
    }

    fuses = generate_fuses("ia_voltage_bump", filter_params=filter_params)
    if target_socket is not None:
        fuses = [fuse for fuse in fuses if f"socket{target_socket}" in fuse]

    print(f"target sockets socket{target_socket} fuses")
    
    if target_index is not None:
        fuses = [fuse for fuse in fuses if "idx" in fuse]
    else: 
        fuses = [fuse for fuse in fuses if "base" in fuse]

    for fuse in fuses:
        search_str= fuse
        old_bin = eval(f"{search_str}.get_value()") # For each fuse, evaluate it with ".get_value()" to obtain its values
        old_float = cvt.convert.bin2float(old_bin,"U8.8") # Set recieved value to U8.8 float format
        new_float = old_float + offset # Adds offset to the U8.8 float to obtain new_float

        if fixed_voltage: new_float = fixed_voltage #Overwrites new_float with a fixed input value.

        new_bin = cvt.convert.float2bin(new_float,"U8.8") # Convert final float value (with offset or fixed) into binary format
        print (f"{search_str} : {old_float}:0x%x > {new_float}: 0x%x" % (old_bin, new_bin))
        ret_array.append(f"{search_str} = 0x{new_bin}") 
    return ret_array


    

def ia_vbump_array_bk (offset: float = 0, rgb_array={}, init=False, target_curve=None, target_point=None, target_index=None, target_compute=None, fixed_voltage=None):
    """
    Returns an array with specific ia_vf_voltage_curve registers and values. This script allows targeting specific or multiple computes, curve points, indexes and voltage points. It is possible to apply an offset to each point with the rgb dictionary, as well as apply a fixed voltage value with fixed_voltage.

    Inputs:
        offset: (Int) first offset modifier, value in Volts.
        rgb_array: (Dictionary) Reduced GuardBand array, it is a secondary offset modifier, modifies only the specific licence. Its content keys must be named RGB_<Licence>_F<1-6> and its assigned value must be a float, representing Voltage offset.
            Example:
                rgb_array={ 
                    "RGB_SSE_F1" : 0.003
                    "RGB_SSE_F3" : 0.001
                    "RGB_AVX2_F4" : 0.002
                    "RGB_AVX3_F2" : 0.001
                    "RGB_TMUL_F1" : 0.004}
        init: (Boolean, Default=False) start init sequence.
        target_curve: (Int, Default=None) Sets start and end curve register to a single target.
        target_point: (Int, Default=None) Sets start and end point register to a single target.
        target_index: (Int, Default=None) Sets start and end index register to a single target.
        target_compute: (Int, Default=None) Sets start and end compute to a single target.
        Fixed_voltage: (Float, Default=None) Overwrites final voltage value. THIS SHOULD BE IN MILLIVOLTS
        
    Output:
    ret_array: (String array) array containing the registers and their assigned values.
    """
    curves = []
    sockets=len(sv.sockets)
    cbbs = len(sv.socket0.cbbs)
    computes = len(sv.socket0.cbb0.computes)
    indexes = 12 # Index limit
    points = 6 # Point limit
    #indexes = 4 # Index limit
    ret_array=[] # Return array

    start_compute=0
    end_compute=computes 
    if (target_compute!=None): # Sets start and end compute to set a single target.
        start_compute=target_compute
        end_compute=target_compute+1 
    
    start_curve=0
    end_curve=curves 
    if (target_curve!=None): # Sets start and end curve register to a single target.
        start_curve=target_curve
        end_curve=target_curve+1
    
    start_point=0
    end_point=points 
    if (target_point!=None): # Sets start and end points register to a single target.
        start_point=target_point
        end_point=target_point+1
    
    start_index=0
    end_index=indexes 
    if (target_index!=None): # Sets start and end index register to a single target.
        start_index=target_index
        end_index=target_index+1 
    
    init_routine(init, init) # Executes init and fuse load sequence if specified

    for socket in range(sockets): # For each socket
        for c in range (start_curve, end_curve): # For each curve point from start to end
            for i in range (start_index, end_index): # For each index from start to end
                for p in range (start_point, end_point): # For each point from start to end
                    toffset=offset #* 0.001 # Default offset

                    if rgb_array != {}: # Adds each value specified in rgb_array (Reduced GuarBand) to modify the offset, depending on each specific index and point and the 
                        if i==0 and p == 0: toffset -= rgb_array["RGB_IA_SSE_F1"]
                        elif i==0 and p == 1: toffset -= rgb_array["RGB_IA_SSE_F2"]
                        elif i==0 and p == 2: toffset -= rgb_array["RGB_IA_SSE_F3"]
                        elif i==0 and p == 3: toffset -= rgb_array["RGB_IA_SSE_F4"]
                        elif i==0 and p == 4: toffset -= rgb_array["RGB_IA_SSE_F5"]
                        elif i==0 and p == 5: toffset -= rgb_array["RGB_IA_SSE_F6"]
                        elif i==1 and p == 0: toffset -= rgb_array["RGB_IA_AVX2_F1"]
                        elif i==1 and p == 1: toffset -= rgb_array["RGB_IA_AVX2_F2"]
                        elif i==1 and p == 2: toffset -= rgb_array["RGB_IA_AVX2_F3"]
                        elif i==1 and p == 3: toffset -= rgb_array["RGB_IA_AVX2_F4"]
                        elif i==1 and p == 4: toffset -= rgb_array["RGB_IA_AVX2_F5"]
                        elif i==1 and p == 5: toffset -= rgb_array["RGB_IA_AVX2_F6"]
                        elif i==2 and p == 0: toffset -= rgb_array["RGB_IA_AVX3_F1"]
                        elif i==2 and p == 1: toffset -= rgb_array["RGB_IA_AVX3_F2"]
                        elif i==2 and p == 2: toffset -= rgb_array["RGB_IA_AVX3_F3"]
                        elif i==2 and p == 3: toffset -= rgb_array["RGB_IA_AVX3_F4"]
                        elif i==2 and p == 4: toffset -= rgb_array["RGB_IA_AVX3_F5"]
                        elif i==2 and p == 5: toffset -= rgb_array["RGB_IA_AVX3_F6"]
                        elif i==3 and p == 0: toffset -= rgb_array["RGB_IA_AMX_F1"]
                        elif i==3 and p == 1: toffset -= rgb_array["RGB_IA_AMX_F2"]
                        elif i==3 and p == 2: toffset -= rgb_array["RGB_IA_AMX_F3"]
                        elif i==3 and p == 3: toffset -= rgb_array["RGB_IA_AMX_F4"]
                        elif i==3 and p == 4: toffset -= rgb_array["RGB_IA_AMX_F5"]
                        elif i==3 and p == 5: toffset -= rgb_array["RGB_IA_AMX_F6"]

                    for t in range (start_compute, end_compute): # From each compute from start to end (or target)
                        search_str= (f"sv.socket{socket}.compute{t}.fuses.pcu.pcode_ia_vf_voltage_curve{c}_voltage_index{i}_voltage_point{p}")           
                        old_bin = eval(search_str+".get_value()") # For each fuse, evaluate it with ".get_value()" to obtain its values
                        old_float = cvt.convert.bin2float(old_bin,"U8.8") # Set recieved value to U8.8 float format
                        new_float = old_float + toffset # Adds offset to the U8.8 float to obtain new_float

                        if fixed_voltage !=None: new_float = fixed_voltage #Overwrites new_float with a fixed input value.

                        new_bin = cvt.convert.float2bin(new_float,"U8.8") # Convert final float value (with offset or fixed) into binary format
                        print (f"{search_str} : {old_float}:0x%x > {new_float}: 0x%x" % (old_bin, new_bin))
                        ret_array.append(search_str+ "= 0x%x" % new_bin) # Adds fuse and new binary value into the return string
        return(ret_array)

def cfc_vbump_array(offset: float = 0, rgb_array={}, init=False, target_point=None, target_compute=None, fixed_voltage=None): 
    """
    Returns an array with specific cfc_vf_voltage_point registers and values. This script allows targeting specific or multiple computes and curve points. It is possible to apply an offset to all values, as well as apply a fixed voltage value with fixed_voltage.

    Inputs:
        offset: (Int) voltage modifier, value in Volts.
        init: (Boolean, Default=False) start init sequence.
        target_point: (Int, Default=None) Sets start and end point register to a single target.
        target_compute: (Int, Default=None) Sets start and end compute to a single target.
        Fixed_voltage: (Float, Default=None) Overwrites final voltage value. THIS SHOULD BE IN MILLIVOLTS
        
    Output:
    ret_array: (String array) array containing the registers and their assigned values.
    """
    
    sockets=len(sv.sockets)
    computes = len(sv.socket0.computes)
    points=6 # Total curve points
    
    #Start values
    start_socket=0
    start_compute=0
    start_point=0

    #End values
    end_socket=sockets
    end_compute=computes
    end_point=points 

    ret_array=[] #Return array

    if (target_compute!=None): # Sets start and end compute to set a single target.
        start_compute=target_compute
        end_compute=target_compute+1 
    
    if (target_point!=None): # If a target point is given, assign it as start and end
        start_point=target_point
        end_point=target_point+1

    init_routine(init, init) # Executes init and fuse load sequence if specified

    for socket in range (start_socket, end_socket): # For each socket
        for p in range (start_point, end_point): # For each point
            toffset=offset
            if(rgb_array!={}):
                if p == 0: toffset -= rgb_array["RGB_CFC_F1"]
                elif p == 1: toffset -= rgb_array["RGB_CFC_F2"]
                elif p == 2: toffset -= rgb_array["RGB_CFC_F3"]
                elif p == 3: toffset -= rgb_array["RGB_CFC_F4"]
                elif p == 4: toffset -= rgb_array["RGB_CFC_F4"]
                elif p == 5: toffset -= rgb_array["RGB_CFC_F4"]


            for t in range (start_compute, end_compute): #For each compute
                search_str= (f"sv.socket{socket}.compute{t}.fuses.pcu.pcode_cfc_vf_voltage_point{p}")
                old_bin = eval(search_str+".get_value()") # For each fuse, evaluate it with ".get_value()" to obtain its values
                
                old_float = cvt.convert.bin2float(old_bin,"U8.8") # Set recieved value to U8.8 float format
                new_float = old_float + offset # Adds offset to the U8.8 float to obtain new_float

                if fixed_voltage !=None: new_float = fixed_voltage #Overwrites new_float with a fixed input value.

                new_bin = cvt.convert.float2bin(new_float,"U8.8") # Convert final float value (with offset or fixed) into binary format
                print (f"{search_str} : {old_float}:0x%x > {new_float}: 0x%x" % (old_bin, new_bin))
                ret_array.append(search_str+ "= 0x%x" % new_bin) # Adds fuse and new binary value into the return string

    return(ret_array)

def hdc_vbump_array(offset: float = 0, rgb_array={}, init=False, target_point=None, target_compute=None, fixed_voltage=None): 
    """
    Returns an array with specific cfc_vf_voltage_point registers and values. This script allows targeting specific or multiple computes and curve points. It is possible to apply an offset to all values, as well as apply a fixed voltage value with fixed_voltage.

    Inputs:
        offset: (Int) voltage modifier, value in Volts.
        init: (Boolean, Default=False) start init sequence.
        target_point: (Int, Default=None) Sets start and end point register to a single target.
        target_compute: (Int, Default=None) Sets start and end compute to a single target.
        Fixed_voltage: (Float, Default=None) Overwrites final voltage value. THIS SHOULD BE IN MILLIVOLTS
        
    Output:
    ret_array: (String array) array containing the registers and their assigned values.
    """
    CONFIG = CORETYPE

    ## Default to bigcore (GNR)
    RGBStrings = {      "fuse": "pcode_hdc_vf_voltage_point",
                        "P0" : "RGB_HDC_F1",
                        "P1" : "RGB_HDC_F2",
                        "P2" : "RGB_HDC_F3",
                        "P3" : "RGB_HDC_F4",
                        "P4" : "RGB_HDC_F4",
                        "P5" : "RGB_HDC_F4",
                } 
    ## Configuration for HDC in Atomcore
    if CONFIG == "atomcore": 
        RGBStrings = {  "fuse": "pcode_l2_vf_voltage_point",
                        "P0" : "RGB_L2_F1",
                        "P1" : "RGB_L2_F2",
                        "P2" : "RGB_L2_F3",
                        "P3" : "RGB_L2_F4",
                        "P4" : "RGB_L2_F5",
                        "P5" : "RGB_L2_F6",
                        } 

    sockets=len(sv.sockets)
    computes = len(sv.socket0.computes)
    points=6 # Total curve points
    
    #Start values
    start_socket=0
    start_compute=0
    start_point=0

    #End values
    end_socket=sockets
    end_compute=computes
    end_point=points 

    ret_array=[] #Return array

    if (target_compute!=None): # Sets start and end compute to set a single target.
        start_compute=target_compute
        end_compute=target_compute+1 
    
    if (target_point!=None): # If a target point is given, assign it as start and end
        start_point=target_point
        end_point=target_point+1

    init_routine(init, init) # Executes init and fuse load sequence if specified

    for socket in range (start_socket, end_socket):
        for p in range (start_point, end_point): 

            toffset=offset
            if(rgb_array!={}):
                if p == 0: toffset -= rgb_array[RGBStrings["P0"]]
                elif p == 1: toffset -= rgb_array[RGBStrings["P1"]]
                elif p == 2: toffset -= rgb_array[RGBStrings["P2"]]
                elif p == 3: toffset -= rgb_array[RGBStrings["P3"]]
                elif p == 4: toffset -= rgb_array[RGBStrings["P4"]]
                elif p == 5: toffset -= rgb_array[RGBStrings["P5"]]

            for t in range (start_compute, end_compute):
                search_str= (f"sv.socket{socket}.compute{t}.fuses.pcu.{RGBStrings['fuse']}{p}")
                #print (f"{search_str}")
                old_bin = eval(search_str+".get_value()")
                #print (f"{old_bin}")
                old_float = cvt.convert.bin2float(old_bin,"U8.8")
                new_float = old_float + toffset

                if fixed_voltage !=None: new_float = fixed_voltage 

                new_bin = cvt.convert.float2bin(new_float,"U8.8")
                print (f"{search_str} : {old_float}:0x%x > {new_float}: 0x%x" % (old_bin, new_bin))
                ret_array.append(search_str+ "= 0x%x" % new_bin)

    return(ret_array)

def ddrd_vbump_array(offset: float = 0, rgb_array={}, init=False, target_point=None, target_compute=None, fixed_voltage=None): 
    """
    Returns an array with specific cfc_vf_voltage_point registers and values. This script allows targeting specific or multiple computes and curve points. It is possible to apply an offset to all values, as well as apply a fixed voltage value with fixed_voltage.

    Inputs:
        offset: (Int) voltage modifier, value in Volts.
        init: (Boolean, Default=False) start init sequence.
        target_point: (Int, Default=None) Sets start and end point register to a single target.
        target_compute: (Int, Default=None) Sets start and end compute to a single target.
        Fixed_voltage: (Float, Default=None) Overwrites final voltage value. THIS SHOULD BE IN MILLIVOLTS
        
    Output:
    ret_array: (String array) array containing the registers and their assigned values.
    """
    
    sockets=len(sv.sockets)
    computes = len(sv.socket0.computes)
    points=4 # Total curve points
    
    #Start values
    start_socket=0
    start_compute=0
    start_point=0

    #End values
    end_socket=sockets
    end_compute=computes
    end_point=points 

    ret_array=[] #Return array

    if (target_compute!=None): # Sets start and end compute to set a single target.
        start_compute=target_compute
        end_compute=target_compute+1 
    
    if (target_point!=None): # If a target point is given, assign it as start and end
        start_point=target_point
        end_point=target_point+1

    init_routine(init, init) # Executes init and fuse load sequence if specified

    for socket in range (start_socket, end_socket):
        for p in range (start_point, end_point): 

            toffset=offset
            if(rgb_array!={}):
                if p == 0: toffset -= rgb_array["RGB_DDRD_F1"]
                elif p == 1: toffset -= rgb_array["RGB_DDRD_F2"]
                elif p == 2: toffset -= rgb_array["RGB_DDRD_F3"]
                elif p == 3: toffset -= rgb_array["RGB_DDRD_F4"]

            for t in range (start_compute, end_compute):
                search_str= (f"sv.socket{socket}.compute{t}.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point{p}")
                #print (f"{search_str}")
                old_bin = eval(search_str+".get_value()")
                #print (f"{old_bin}")
                old_float = cvt.convert.bin2float(old_bin,"U8.8")
                new_float = old_float + toffset

                if fixed_voltage !=None: new_float = fixed_voltage 

                new_bin = cvt.convert.float2bin(new_float,"U8.8")
                print (f"{search_str} : {old_float}:0x%x > {new_float}: 0x%x" % (old_bin, new_bin))
                ret_array.append(search_str+ "= 0x%x" % new_bin) 

    return(ret_array)

def ddra_vbump_array(offset: float = 0, rgb_array={}, init=False, target_point=None, target_compute=None, fixed_voltage=None): 
    """
    Returns an array with specific cfc_vf_voltage_point registers and values. This script allows targeting specific or multiple computes and curve points. It is possible to apply an offset to all values, as well as apply a fixed voltage value with fixed_voltage.

    Inputs:
        offset: (Int) voltage modifier, value in Volts.
        init: (Boolean, Default=False) start init sequence.
        target_point: (Int, Default=None) Sets start and end point register to a single target.
        target_compute: (Int, Default=None) Sets start and end compute to a single target.
        Fixed_voltage: (Float, Default=None) Overwrites final voltage value. THIS SHOULD BE IN MILLIVOLTS
        
    Output:
    ret_array: (String array) array containing the registers and their assigned values. Placeholder, not available for DDRA
    """
    
    sockets=len(sv.sockets)
    computes = len(sv.socket0.computes)
    points=4 # Total curve points
    
    #Start values
    start_socket=0
    start_compute=0
    start_point=0

    #End values
    end_socket=sockets
    end_compute=computes
    end_point=points 

    ret_array=[] #Return array

    if (target_compute!=None): # Sets start and end compute to set a single target.
        start_compute=target_compute
        end_compute=target_compute+1 
    
    if (target_point!=None): # If a target point is given, assign it as start and end
        start_point=target_point
        end_point=target_point+1

    init_routine(init, init) # Executes init and fuse load sequence if specified

    for socket in range (start_socket, end_socket):
        for p in range (start_point, end_point): 

            toffset=offset
            #if(rgb_array!={}):
            #    if p == 0: toffset -= rgb_array["RGB_DDRD_F1"]
            #    elif p == 1: toffset -= rgb_array["RGB_DDRD_F2"]
            #    elif p == 2: toffset -= rgb_array["RGB_DDRD_F3"]
            #    elif p == 3: toffset -= rgb_array["RGB_DDRD_F4"]

            for t in range (start_compute, end_compute):
                search_str= (f"sv.socket{socket}.compute{t}.fuses.pcu.pcode_ddrd_mcr_vf_voltage_point{p}")
                #print (f"{search_str}")
                old_bin = eval(search_str+".get_value()")
                #print (f"{old_bin}")
                old_float = cvt.convert.bin2float(old_bin,"U8.8")
                new_float = old_float + toffset

                if fixed_voltage !=None: new_float = fixed_voltage 

                new_bin = cvt.convert.float2bin(new_float,"U8.8")
                print (f"{search_str} : {old_float}:0x%x > {new_float}: 0x%x" % (old_bin, new_bin))
                ret_array.append(search_str+ "= 0x%x" % new_bin) 

    return(ret_array)

def cfc_io_vbump_array(offset: float = 0, rgb_array={}, init=False, target_point=None, target_io=None, fixed_voltage=None): 
    """
    Returns an array with specific cfc_vf_voltage_point registers and values. This script allows targeting specific or multiple computes and curve points. It is possible to apply an offset to all values, as well as apply a fixed voltage value with fixed_voltage.

    Inputs:
        offset: (Int) voltage modifier, value in Volts.
        init: (Boolean, Default=False) start init sequence.
        target_point: (Int, Default=None) Sets start and end point register to a single target.
        target_io: (Int, Default=None) Sets start and end IO to a single target.
        Fixed_voltage: (Float, Default=None) Overwrites final voltage value. THIS SHOULD BE IN MILLIVOLTS
        
    Output:
    ret_array: (String array) array containing the registers and their assigned values.
    """
    
    sockets=len(sv.sockets)
    io_dies = len(sv.socket0.ios)
    points=6 # Total curve points
    
    #Start values
    start_socket=0
    start_io_die=0
    start_point=0

    #End values
    end_socket=sockets
    end_io_die=io_dies
    end_point=points 

    ret_array=[] #Return array

    if (target_io!=None): # Sets start and end compute to set a single target.
        start_io_die=target_io
        end_io_die=target_io+1 
    
    if (target_point!=None): # If a target point is given, assign it as start and end
        start_point=target_point
        end_point=target_point+1

    init_routine(init, init) # Executes init and fuse load sequence if specified

    for socket in range (start_socket, end_socket):
        for p in range (start_point, end_point): 

            toffset=offset
            if(rgb_array!={}):
                if p == 0: toffset -= rgb_array["RGB_CFCXIO_F1"]
                elif p == 1: toffset -= rgb_array["RGB_CFCXIO_F2"]
                elif p == 2: toffset -= rgb_array["RGB_CFCXIO_F3"]
                elif p == 3: toffset -= rgb_array["RGB_CFCXIO_F4"]
                elif p == 4: toffset -= rgb_array["RGB_CFCXIO_F4"]
                elif p == 5: toffset -= rgb_array["RGB_CFCXIO_F4"]
                

            for t in range (start_io_die, end_io_die):
                search_str= (f"sv.socket{socket}.io{t}.fuses.punit_iosf_sb.pcode_cfc_vf_voltage_point{p}")
                #print (f"{search_str}")
                old_bin = eval(search_str+".get_value()")
                #print (f"{old_bin}")
                old_float = cvt.convert.bin2float(old_bin,"U8.8")
                new_float = old_float + toffset

                if fixed_voltage !=None: new_float = fixed_voltage 

                new_bin = cvt.convert.float2bin(new_float,"U8.8")
                print (f"{search_str} : {old_float}:0x%x > {new_float}: 0x%x" % (old_bin, new_bin))
                ret_array.append(search_str+ "= 0x%x" % new_bin) 


    return(ret_array)

def cfn_vbump_array(offset: float = 0, rgb_array={}, init=False, target_io=None, fixed_voltage=None): 
    """
    Returns an array with specific cfc_vf_voltage_point registers and values. This script allows targeting specific or multiple computes and curve points. It is possible to apply an offset to all values, as well as apply a fixed voltage value with fixed_voltage.

    Inputs:
        offset: (Int) voltage modifier, value in Volts.
        init: (Boolean, Default=False) start init sequence.
        target_io: (Int, Default=None) Sets start and end IO to a single target.
        Fixed_voltage: (Float, Default=None) Overwrites final voltage value. THIS SHOULD BE IN MILLIVOLTS
        
    Output:
    ret_array: (String array) array containing the registers and their assigned values.
    """
    
    sockets=len(sv.sockets)
    io_dies = len(sv.socket0.ios)

    
    #Start values
    start_socket=0
    start_io_die=0
    #start_point=0

    #End values
    end_socket=sockets
    end_io_die=io_dies
    #end_point=points 

    ret_array=[] #Return array

    if (target_io!=None): # Sets start and end compute to set a single target.
        start_io_die=target_io
        end_io_die=target_io+1 

    init_routine(init, init) # Executes init and fuse load sequence if specified
    
    toffset=offset
    if(rgb_array!={}):
        toffset-=rgb_array["RGB_CFN"]    

    for socket in range (start_socket, end_socket):

        for t in range (start_io_die, end_io_die):

            fuses_to_mod=[f"sv.socket{socket}.io{t}.fuses.punit_iosf_sb.pcode_hca_active_voltage",
                          f"sv.socket{socket}.io{t}.fuses.punit_iosf_sb.pcode_pi5_active_voltage",
                          f"sv.socket{socket}.io{t}.fuses.punit_iosf_sb.pcode_piu5_active_voltage"]
                          
            for fuse in fuses_to_mod:

                old_bin = eval(fuse+".get_value()")
                old_float = cvt.convert.bin2float(old_bin,"U8.8")
                new_float = old_float + toffset

                if fixed_voltage !=None: new_float = fixed_voltage 

                new_bin = cvt.convert.float2bin(new_float,"U8.8")
                print (f"{fuse} : {old_float}:0x%x > {new_float}: 0x%x" % (old_bin, new_bin))
                ret_array.append(fuse+ "= 0x%x" % new_bin) 
    
    return(ret_array)

def vccinf_vbump_array(offset: float = 0, rgb_array={}, init=False, target_io=None, target_compute=None, fixed_voltage=None): 
    """
    Returns an array with specific cfc_vf_voltage_point registers and values. This script allows targeting specific or multiple computes and curve points. It is possible to apply an offset to all values, as well as apply a fixed voltage value with fixed_voltage.

    Inputs:
        offset: (Int) voltage modifier, value in Volts.
        init: (Boolean, Default=False) start init sequence.
        target_io: (Int, Default=None) Sets start and end IO to a single target.
        target_compute: (Int, Default=None) Sets start and end compute to a single target.
        Fixed_voltage: (Float, Default=None) Overwrites final voltage value. THIS SHOULD BE IN MILLIVOLTS
        
    Output:
    ret_array: (String array) array containing the registers and their assigned values.
    """
    
    sockets=len(sv.sockets)
    io_dies = len(sv.socket0.ios)
    computes = len(sv.socket0.computes)
    
    #Start values
    start_socket=0
    start_io_die=0
    start_compute=0
    skip_ios = False
    skip_computes = False
    #start_point=0

    #End values
    end_socket=sockets
    end_io_die = io_dies
    end_compute = computes
    #end_point=points 

    ret_array=[] #Return array

    if (target_io!=None) and (target_compute!=None): # This sets an specific Comptue and IO
        start_io_die=target_io
        end_io_die=target_io+1
        start_compute=start_compute
        end_compute=end_compute+1

    elif (target_io!=None): # Sets start and end io to set a single target.
        start_io_die=target_io
        end_io_die=target_io+1
        skip_computes = True # Condition to only set IO

    elif (target_compute!=None): # Sets start and end compute to set a single target.
        start_compute=start_compute
        end_compute=end_compute+1
        skip_ios = True # Condition to only set Compute

    init_routine(init, init) # Executes init and fuse load sequence if specified
    
    toffset=offset
    if(rgb_array!={}):
        toffset-=rgb_array["RGB_VCCINF"]

    for socket in range (start_socket, end_socket):
    
        fuses_to_mod=[]
        if not skip_ios:
            for t in range (start_io_die, end_io_die):

                fuses_to_mod+=[f"sv.socket{socket}.io{t}.fuses.punit_iosf_sb.pcode_vccinf_active_vid",
                            f"sv.socket{socket}.io{t}.fuses.punit_iosf_sb.pcode_vccinf_idle_vid"]

        if not skip_computes:                
            for t in range (start_compute, end_compute):

                fuses_to_mod+=[f"sv.socket{socket}.compute{t}.fuses.pcu.pcode_vccinf_active_vid",
                            f"sv.socket{socket}.compute{t}.fuses.pcu.pcode_vccinf_idle_vid"]
                            
        for fuse in fuses_to_mod:

            old_bin = eval(fuse+".get_value()")
            old_float = cvt.convert.bin2float(old_bin,"U8.8")
            new_float = old_float + toffset

            if fixed_voltage !=None: new_float = fixed_voltage 

            new_bin = cvt.convert.float2bin(new_float,"U8.8")
            print (f"{fuse} : {old_float}:0x%x > {new_float}: 0x%x" % (old_bin, new_bin))
            ret_array.append(fuse+ "= 0x%x" % new_bin) 
    
    return(ret_array)

def ht_dis_array():
        """
        For other products, this function returns an array with all ht_dis registers, to be set to a specific value.
        For DMR raises an exception as this product does not have Hyper Threading.

        Output:
            ret_array: (String array) array containing the registers and their assigned values.
        """
        raise NotImplementedError("DMR does not have Hyper Threading")

def acp_ready_global_status():
    """
    Returns the value of the following register, for all sockets and computes:
        sv.sockets.computes.pcudata.acp_ready

    Output:
        sv_regs: (ComponentGroup) basic multiple-register output, returns an object containing the name and values of the read registers.
    """
    return sv.sockets.computes.pcudata.acp_ready

def _clear_bit(value, bit_position): 
    """
    Overwrites a single bit to 0, of the given input value for the input position.

    Inputs:
        value: (int) decimal number.
        bit_position: (int) bit index to overwrite with 0.

    Outputs:
        value: (int) result value of setting input bit position to 0.
    """
    print ("_clear_bit(0x%x, %d)" %(value, bit_position))
    return value & ~(1<<bit_position) # To the given value, set given bit position to 0

def ia_vf_voltage_curve_override(socket_id: int, compute_id: int, verbose = False) -> int:
    """
    Overwrites all values from registers "pcode_ia_vf_voltage_curve" with 0x100, for a specified socket and compute.

    Inputs:
        socket_id: (Int) Specific socket to overwrite values.
        compute_id: (Int) Specific compute to overwrite values.
        verbose: (Boolean, Default=False) more info for debugging.
    """
    
    reg_path_list = sv.sockets[socket_id].sub_components[f"compute{compute_id}"].search("pcode_ia_vf_voltage_curve") #Returns a list with all the fuse names that contain this string, STARTING AFTER computeX.
   
    for index, reg_path in enumerate(reg_path_list): # For each of the previously recieved fuses
        if verbose: print(f"INFO -> THR Dynamic Injection: Processing string:{reg_path}") # Print more info
        fuse_obj = sv.sockets[socket_id].sub_components[f"compute{compute_id}"].get_by_path(reg_path) # Returns the fuse value of the current fuse in the list
        if int(fuse_obj) > 0: # If value greater than 0 (converted to decimal)
            fuse_obj.write(0x100) # Set current fuse to 0x100 (256 decimal)

def ppvc_rgb_reduction(fuses=[]):

    rgb_values = get_rgb_values()

    fuses+=ia_vbump_array(rgb_array=rgb_values) # Adding IA fuses
    fuses+=cfc_vbump_array(rgb_array=rgb_values) # Adding CFC fuses
    fuses+=hdc_vbump_array(rgb_array=rgb_values) # Adding HDC fuses
    fuses+=ddrd_vbump_array(rgb_array=rgb_values) # Adding DDRD fuses
    fuses+=cfc_io_vbump_array(rgb_array=rgb_values) # Adding CFCxIO fuses
    fuses+=cfn_vbump_array(rgb_array=rgb_values) # Adding CFN fuses
    fuses+=vccinf_vbump_array(rgb_array=rgb_values) # Adding VCCINF fuses

    fuse_cmd_override_reset(fuses) # Conditioning boot so we can add some additional experiments by using the array



#Function made to get the RGB values for a given QDF 
def get_rgb_values(qdf_str = None):
    
    import xml.etree.ElementTree as ET
    import os
    
    #Paths to the fuses of each product (Paths to another products can be added if needed)
    paths=  {
                "CWF AP XDCC X3":"I:\\fuse\\release\\CWF\\Clearwater_Forest_AP_XDCC",
                "CWF SP HDCC X2":"I:\\fuse\\release\\CWF\\Clearwater_Forest_SP_HDCC",
     
            }
    
    #Nested function made to display a selection menu for a set of given products
    def _select_path(values):
        
        #List of available selection numbers 
        keys=[]
        
        #Options string that will be displayed on console
        options_string=""
        
        #For cycle that is used to assemble the options_string
        for i in range(len(values)):
            
            #Assembling the option_string
            options_string+="-> "+ str(i+1)+". "+values[i]+"\n"
            
            #Saving the valid selection numbers for the options to be displayed
            keys+=[i]
        
        #Creating a dictionary from the available options and its corresponding selection number
        options_dict=dict(zip(keys,values))
        
        #Variable that will store the selection made by the user
        selection=-1
        
        #Displaying the available products that can be selected
        print("Available products: \n")
        print(options_string)
        
        #While cycle to keep asking for input while the selection made by the user is invalid
        while(selection==-1):
            
            try:
                #Asking the user for a numeric value from the ones available in the keys list
                selection=int(input("Please select the option number of the product you are working on: "))
                
                #Checking if the selected value is in the range of valid options
                if(selection in range(1,len(values)+1)): break
                    
                else:
                    # If the user inputs something invalid, keep the selection variable as invalid
                    print("Please select a valid option\n")
                    selection=-1
                        
            except:
                # If the user inputs something invalid, keep the selection variable as invalid
                print("Please select a valid option\n")
                selection=-1
            
        #Returning the selected product       
        return options_dict[selection-1]

    #Nested function made to parse the content of a given lineitemdata.xml file in the search for the RGB values for a given QDF
    def _get_rgb_from_xml(xml_path,qdf):
        
        rgb_keys=   (   "RGB_IA_SSE_F1",
                        "RGB_IA_SSE_F2",
                        "RGB_IA_SSE_F3",
                        "RGB_IA_SSE_F4",
                        "RGB_IA_SSE_F5",
                        "RGB_IA_SSE_F6",
                        "RGB_IA_AVX2_F1",
                        "RGB_IA_AVX2_F2",
                        "RGB_IA_AVX2_F3",
                        "RGB_IA_AVX2_F4",
                        "RGB_IA_AVX2_F5",
                        "RGB_IA_AVX2_F6",
                        "RGB_IA_AVX3_F1",
                        "RGB_IA_AVX3_F2",
                        "RGB_IA_AVX3_F3",
                        "RGB_IA_AVX3_F4",
                        "RGB_IA_AVX3_F5",
                        "RGB_IA_AVX3_F6",
                        "RGB_IA_AMX_F1",
                        "RGB_IA_AMX_F2",
                        "RGB_IA_AMX_F3",
                        "RGB_IA_AMX_F4",
                        "RGB_IA_AMX_F5",
                        "RGB_IA_AMX_F6",
                        "RGB_CFC_F1",
                        "RGB_CFC_F2",
                        "RGB_CFC_F3",
                        "RGB_CFC_F4",
                        "RGB_CFCXIO_F1",
                        "RGB_CFCXIO_F2",
                        "RGB_CFCXIO_F3",
                        "RGB_CFCXIO_F4",
                        "RGB_CFN",
                        "RGB_DDRD_F1",
                        "RGB_DDRD_F2",
                        "RGB_DDRD_F3",
                        "RGB_DDRD_F4",
                        "RGB_HDC_F1",
                        "RGB_HDC_F2",
                        "RGB_HDC_F3",
                        "RGB_HDC_F4",
                        "RGB_L2_F1",
                        "RGB_L2_F2",
                        "RGB_L2_F3",
                        "RGB_L2_F4",
                        "RGB_L2_F5",
                        "RGB_L2_F6",
                        "RGB_VCCINF"
                    )
        
        #Generating a tree from the XML file
        tree = ET.parse(xml_path)
        
        #Getting the root of the tree
        root = tree.getroot()

        #Dictionary that will store the RGB values for the given QDF
        rgb_values={}
        
        #Fetching the RGB values from inside the tree
        for element in root:
            if(element.tag == "LineItemValues"):
                
                for lineItem in element:
                    
                    if(lineItem.attrib["qdfSspec"].lower()==qdf):
                        
                        print("RGB Values found at "+xml_path)
                        
                        for attribute in lineItem:
                            
                            if(attribute.attrib["name"].upper() in rgb_keys): ## ADded the upper to avoid any lower case issue when reading RGB
                                
                                rgb_values[attribute.attrib["name"].upper()]=float(attribute.text)
                            
        return rgb_values
    
    #Nested function designed to get a list of direcdtories/files from a given path    
    def _get_files(path,get_directories=False):
        
        #Getting a list of the files/directories on the given path 
        entries=os.listdir(path)
     
        #List that will store tuples of the found files/directories and its creation date
        values=[]
        
        #Parsing the entries
        for entry in entries:
            
            #Getting the full path to the directory/file
            full_path=os.path.join(path,entry)
            
            #Checking if we are looking for directories
            if(get_directories):
                
                #Checking if the current entry is a directory
                if (os.path.isdir(full_path)):
                    
                    #Adding a tuple that stores the directory path and its creation date
                    values+=[(full_path,os.stat(full_path).st_ctime)]
                    
            else:
                
                #Checking if the entry is a file
                if (not os.path.isdir(full_path)):
                    
                    #Adding a tuple that stores the file path and its creation date
                    values+=[(full_path,os.stat(full_path).st_ctime)]
        
        #If we are searching for directories, we proceed to sort the values list by creation date,in order to have the most recent 
        #directories first on the list
        if(get_directories):    
            values = sorted(values, key=lambda x: x[1], reverse= True)
                
        return values
    
    #Nested function designed to search for a given file inside a given directory
    def _get_file(directory_path,filename):
        
        #Getting the file names inside the given directory
        directory_files=_get_files(directory_path)
        
        #Variable that will store the file path, if found
        found_file=None
        
        #Getting the full path to the file that we are searching for
        full_path=os.path.join(directory_path,filename)
        
        #Going through the file names inside the directory 
        for file in directory_files:
            
            #If one file matches the path of the file we are seaching for, save the file and stop looking (File found!)
            if(file[0]==full_path):
                
                found_file=file[0]
                break

        return found_file
    
    
    
    #Asking the user for the product he is working on
    product=_select_path(values=list(paths.keys()))
    
    #Asking the user for the QDF of the unit hes working with
    qdf = input("Please write the QDF to be found: ").lower() if qdf_str == None else qdf_str.lower()
    
    print("Searching the RGB values for the given QDF...")
    
    #Getting the path to the fuses directories of the selected product
    product_path=paths[product]
    
    #Getting the fuses directories for the given product
    fuse_directories=_get_files(product_path,get_directories=True)
    
    #Dictionary that will store the RGB values found for the given QDF 
    rgb_values={}
    
    #Going through the fuses directories of the given product
    for directory in fuse_directories:
        
        #Searching for the lineitemdata.xml file inside the fuse directory
        line_item_data_file=_get_file(directory[0],"lineitemdata.xml")
        
        #If the lineitemdata.xml file could be found, get the RGB values from it
        if(line_item_data_file!=None):
            
           #Getting the RGB values from the lineitemdata.xml file
           rgb_values=_get_rgb_from_xml(line_item_data_file,qdf)
           
           #If the RGB values could be found, stop searching
           if(rgb_values!={}):break
    
    #If the RGB values couldn"t be found on any of teh directories, notify the user
    if(rgb_values == {}):
        
        print("\nCouldn't find the specified QDF\n")
        return None   
    
    else:
   
        return rgb_values  

#========================================================================================================#
#=============== END OF AVAILABLE SCRIPTS ===============================================================#
#========================================================================================================#

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== DISCONTINUED SCRIPTS FROM GNR TRANSLATION ==============================================#
#========================================================================================================#


# CURRENTLY UNAVAILABLE FOR CWF
def dis_fma5_array():
    return coretile_array(1)


"""Function WIP from GNR. Not implemented
##function is wip.
def core_enable_array(compute0_core=None,compute1_core=None,compute2_core=None): #***********
    mask =0xfffffffffffffff #14??
    mask2=0xfffffffffffffff #15
    ret_array=[]
    if compute0_core is not None and 0 <= compute0_core <=59 :
        C0_mask_reg="sv.socket0.compute0.fuses.hwrs_top_rom.ip_disable_fuses_dword6_core_disable"
        C0_mask_reg_pp0="sv.socket0.compute0.fuses.pcu.pcode_sst_pp_0_core_disable_mask"
        C0_mask_reg_pp1="sv.socket0.compute0.fuses.pcu.pcode_sst_pp_1_core_disable_mask"
        C0_mask_reg_pp2="sv.socket0.compute0.fuses.pcu.pcode_sst_pp_2_core_disable_mask"
        C0_mask_reg_pp3="sv.socket0.compute0.fuses.pcu.pcode_sst_pp_3_core_disable_mask"
        C0_mask_reg_pp4="sv.socket0.compute0.fuses.pcu.pcode_sst_pp_4_core_disable_mask"
        C0_mask_reg_dts="sv.socket0.compute0.fuses.pcu.pcode_disabled_module_dts_mask"
        C0_mask=_clear_bit(mask,compute0_core)
        ret_array.append(C0_mask_reg+ "= 0x%x" % C0_mask)
        C0_mask2=_clear_bit(mask2,compute0_core)
        ret_array.append(C0_mask_reg_pp0+ "= 0x%x" % C0_mask2)
        ret_array.append(C0_mask_reg_pp1+ "= 0x%x" % C0_mask2)
        ret_array.append(C0_mask_reg_pp2+ "= 0x%x" % C0_mask2)
        ret_array.append(C0_mask_reg_pp3+ "= 0x%x" % C0_mask2)
        ret_array.append(C0_mask_reg_pp4+ "= 0x%x" % C0_mask2)
        ret_array.append(C0_mask_reg_dts+ "= 0x%x" % C0_mask2)
    ret_array.append("sv.socket0.compute0.fuses.pcu.capid_capid8_llc_ia_core_en_low=0x3ffff")
    ret_array.append("sv.socket0.compute0.fuses.pcu.capid_capid9_llc_ia_core_en_high=0x0")
    ret_array.append("sv.socket0.compute0.fuses.pcu.pcode_sst_pp_level_en_mask=0x1f")
    return(ret_array)
"""