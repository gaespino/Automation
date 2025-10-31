from tabulate import tabulate
import pandas as pd
import ipccli
import namednodes
import itpii

print ("DMR Module Mapping || REV 1.0 || Validated for DMR X1 \n")

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== IPC, FUSION AND SV SETUP ===============================================================#
#========================================================================================================#

ipc = None
api = None

sv = None
sv = namednodes.sv #shortcut
sv.initialize()

def _get_global_sv():
  # Lazy initialize for the sv 'socket' instance
  # Return
  # ------
  # sv: class 'components.ComponentManager'
  
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
    print(f"IPC: {ipc}")
  return ipc

def _get_global_fusion_api():
    '''
    Lazy initialization for the global ipc and Fusion API instances
    '''
    import fusion
    global api
    if api is None:
        api = fusion.api_access()
    return api

ipc = _get_global_ipc()
sv = _get_global_sv()
itp = itpii.baseaccess()

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== CONSTANTS AND GLOBAL VARIABLES =========================================================#
#========================================================================================================#

#DMR architecture
ACTIVE_MODULES_PER_CBB = 32
TOTAL_MODULES_PER_CBB = 32
TOTAL_MODULES_PER_COMPUTE = 8
CORES_PER_MODULE = 2
THREADS_PER_CORE = 1
APIC_ID_INCREASE_PER_CBB = 128
VVAR_START = 0xc

#---------------------------------------
# PPV Logical Module : Physical module
PPVLog2Phy = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10, 11: 11, 12: 12, 13: 13, 14: 14, 15: 15, 16: 16, 17: 17, 18: 18, 19: 19, 20: 20, 21: 21, 22: 22, 23: 23, 24: 24, 25: 25, 26: 26, 27: 27, 28: 28, 29: 29, 30: 30, 31: 31}
# Physical Module : PPV Logical Module
phys2PPVLog = {value: key for key, value in PPVLog2Phy.items()} 

# Class Logical Module : Physical module
ClassLog2Phy = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10, 11: 11, 12: 12, 13: 13, 14: 14, 15: 15, 16: 16, 17: 17, 18: 18, 19: 19, 20: 20, 21: 21, 22: 22, 23: 23, 24: 24, 25: 25, 26: 26, 27: 27, 28: 28, 29: 29, 30: 30, 31: 31} # Class Logical Module : Physical Module 
# Physical Module : Class Logical Module
phys2ClassLog = {value: key for key, value in ClassLog2Phy.items()} 

phys2EnableOrder = phys2PPVLog 
# Physical Module : Top Die
phys2TopDie = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1, 13: 1, 14: 1, 15: 1, 16: 2, 17: 2, 18: 2, 19: 2, 20: 2, 21: 2, 22: 2, 23: 2, 24: 3, 25: 3, 26: 3, 27: 3, 28: 3, 29: 3, 30: 3, 31: 3}
#========================================================================================================#
#=============== DEBUG SCRIPTS ==========================================================================#
#========================================================================================================#


def load_fuses():
   sv.sockets.cbbs.base.fuses.load_fuse_ram()
   sv.sockets.cbbs.computes.fuses.load_fuse_ram()
   sv.sockets.imhs.fuses.load_fuse_ram()

def flush_fuses():
   sv.sockets.cbbs.base.fuses.flush_fuse_ram()
   sv.sockets.cbbs.computes.fuses.flush_fuse_ram()
   sv.sockets.imhs.fuses.flush_fuse_ram()

def Run(log_path=None, verbose=0):
    '''
    Gathers all physical, logical, OS, ApicID and VVar information for every available module and cores in the system.
    This is then used with the PrintData function to display the information in separate tables for each compute.

    Inputs:
        log_path: (String, Default=None) Path to a desired file, for logging printed data.
        verbose: (Int, Default=0) Additional prints for debugging.
    '''
    print_itp = False
    print_whoami=False
    if(print_itp):
        print(f"+"*38)
        print("| PRINT ITP IS CURRENTLY UNAVAILABLE |")
        print(f"+"*38)
        print_itp=False
    if(print_whoami):
        print(f"+"*41)
        print("| PRINT WHOAMI IS CURRENTLY UNAVAILABLE |")
        print(f"+"*41)
        print_whoami=False

    global ipc
    global sv
    ipc = _get_global_ipc()
    sv = _get_global_sv()
    
    load_fuses()
    
    go_on_exit=False
    if ipc.isrunning:
        go_on_exit=True
        # ipc.halt() # Needed to read APIC IDs. 
    
    os_module = 0 # OS Module counter. Similar concept as "OS Cores".
    os_core = 0 # OS Core counter
    apic_id_t0 = 0 # Apic id of the current module's first core
    socket_id = 0 # Socket ID counter
    drg_vvar = VVAR_START
    for socket in sv.sockets: # For each socket
        for cbb in socket.cbbs: # For each cbb
            physical_to_col_row_array = {} # Physical : Column_Row
            physical_to_global_logical_module = {} # Physical : Local logical [0:59]
            physical_to_global_class = {} # Physical : Global Logical [0:287]
            physical_to_global_os = {} # Physical : Global OS [0:71]
            physical_to_OS_core = {} # Physical : OS Core0
            physical_to_apic_id_array = {} # Physical : Apic id
            physical_to_topdie = {} # Physical : Top Die
            physical_to_vvars = {} # Dragon Vvars
            physical_to_activeBit = {} # State bit
            physical_to_cbb = {} # CBB

            modules_disabled = cbb.base.fuses.punit_fuses.fw_fuses_sst_pp_0_module_disable_mask
            llc_disabled = cbb.base.fuses.punit_fuses.fw_fuses_llc_slice_ia_ccp_dis

            final_modules_disabled = modules_disabled | llc_disabled

            module_is_enabled = {}
            llc_is_enabled = {}

            cbb_instance = cbb.target_info.instance # cbb ID
            global_physical_id = 0

            # Match enabled LLC and DCM 
            for i in range(TOTAL_MODULES_PER_CBB):
                bit_value = (final_modules_disabled >> i) & 1
                module_is_enabled[i] = False if bit_value else True

            # Get the enabled LLC 
            for i in range(TOTAL_MODULES_PER_CBB):
                bit_value = (llc_disabled >> i) & 1
                global_physical_id = i + cbb_instance * TOTAL_MODULES_PER_CBB
                llc_is_enabled[global_physical_id] = False if bit_value else True

            apic_id_t0 = APIC_ID_INCREASE_PER_CBB * cbb_instance # Offset per new cbb
            
            for module_id, enabled in llc_is_enabled.items():
                compute_N = (module_id % TOTAL_MODULES_PER_CBB) // TOTAL_MODULES_PER_COMPUTE
                physical_module_id = module_id % TOTAL_MODULES_PER_CBB
                physical_to_activeBit[physical_module_id] = enabled
                physical_to_cbb[physical_module_id] = cbb_instance
                physical_to_OS_core[physical_module_id] = []
                physical_to_apic_id_array[physical_module_id] = []
                physical_to_vvars[physical_module_id] = []

                if(physical_module_id in phys2ClassLog): 
                    logical_module_id = '--'
                    if enabled:
                        logical_module_id = int(cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map[physical_module_id])
                    physical_to_global_logical_module[physical_module_id] = logical_module_id # Global Logical             
                    physical_to_global_class[physical_module_id] = phys2ClassLog[physical_module_id] + ACTIVE_MODULES_PER_CBB * cbb_instance # Global Class / Physical
                    physical_to_topdie[physical_module_id] = compute_N  # Top Die
                    
                else: # If Physical Module is disabled
                    physical_to_global_logical_module[physical_module_id] = "--" #Local Logical
                    physical_to_global_class[physical_module_id] = "--" # Global Class / Physical
                    physical_to_topdie[physical_module_id] = "-" # Top Die
                         
            physical_to_local_logical_sorted = sorted(phys2EnableOrder.items(), key=lambda item: (item[1] == "--", item[1]))
            
            # Assign APIC IDs for enabled LLCs 
            for physical, logical in physical_to_local_logical_sorted:
                if(physical in phys2ClassLog and physical_to_activeBit[physical] == True):
                    for core in range(CORES_PER_MODULE):
                        for thread in range(THREADS_PER_CORE):   
                            if(module_is_enabled[physical] == True):
                                physical_to_apic_id_array[physical].append("0x%2.3x" % apic_id_t0)
                            else:
                                physical_to_apic_id_array[physical].append("0x---") # APIC ID

                            apic_id_t0 += 2 # Apic id increases by 2 on every consecutive core 
                            
                    apic_id_t0 += 4

                else: # if LLC is disabled
                    for core in range(CORES_PER_MODULE):
                        for thread in range(THREADS_PER_CORE):
                            physical_to_apic_id_array[physical].append("0x---") # APIC ID

                # Assign Dragon VVAR and OS Core for enabled modules                                                                     
                if(physical in phys2ClassLog and module_is_enabled[physical] == True):
                    physical_to_global_os[physical] = os_module
                    physical_to_activeBit[physical] = 'ENABLED'
                    os_module+=1
                    for core in range(CORES_PER_MODULE):
                        for thread in range(THREADS_PER_CORE):  
                            physical_to_vvars[physical].append("0x%2.3x" % drg_vvar)
                            physical_to_OS_core[physical].append("%2.3d" % os_core) # Global OS Core 
                            
                            drg_vvar += 1 # Increase 1 for each core
                            os_core+=1
                            
                else: # physical module is disabled
                    physical_to_global_os[physical] = "--" # Global OS
                    physical_to_activeBit[physical] = 'DISABLED'
                    for core in range(CORES_PER_MODULE):
                        for thread in range(THREADS_PER_CORE):
                            physical_to_OS_core[physical].append("---")
                            physical_to_vvars[physical].append("0x---") # Dragon Vvars


            if verbose >= 2 : # Print dictionary contents
                print(f"physical_to_local_logical: {physical_to_global_logical_module}")
                print("#"*90+"\n")
                print(f"\n\physical_to_global_logical: {physical_to_global_class}")
                print("#"*90+"\n")
                print(f"physical_to_global_os: {physical_to_global_os}")
                print("#"*90+"\n")
                print(f"physical_to_OS_core: {physical_to_OS_core}")
                print("#"*90+"\n")
                print(f"physical_to_apic_id_array: {physical_to_apic_id_array}")
                print("#"*90+"\n")

            # Print a table for each compute
            if verbose: verbose_function(cbb)
            PrintData(log_path=log_path, socket_id=socket_id, cbb_id=cbb_instance, physical_to_activeBit=physical_to_activeBit,  physical_to_cbb=physical_to_cbb, physical_to_global_logical_module=physical_to_global_logical_module, physical_to_global_class=physical_to_global_class, physical_to_global_os=physical_to_global_os, physical_to_OS_core=physical_to_OS_core,physical_to_apic_id_array=physical_to_apic_id_array, physical_to_vvars=physical_to_vvars, physical_to_top_die_array=physical_to_topdie) 
        socket_id += 1 # Socket ID counter
    if go_on_exit:
        ipc.go()


def extract_first_core(os_core):
    if os_core.split(' :: ')[0] == '---':
        return float('inf')  # Using infinite to sort invalids at the end
    return int(os_core.split(' :: ')[0])
     
def PrintData(log_path=None, socket_id=0, cbb_id=0, physical_to_activeBit=None, physical_to_cbb=None,  physical_to_CR_array=None, physical_to_global_logical_module=None, physical_to_global_class=None, physical_to_global_os=None, physical_to_OS_core=None, physical_to_apic_id_array=None, physical_to_vvars=None, htenabled=False, physical_to_top_die_array = None): 
    '''
    Function used by Run() and RunOffline() to print the gathered data as tables.
    It is not recommended to be used by itself, since it requires several dictionaries containing specific information.
    '''
    try:
        if log_path != None: ipc.log(log_path)

        # Table columns
        topdie_str = "TOP DIE"
        phys_mod_str = "LOCAL PHYS MOD"
        die_clid_str = "GLOBAL CLASS/PHYS MOD"
        die_classlid_str = "GLOBAL LOG MOD"
        osmdl_str = "OS MOD"
        linux_str = "OS CORES"
        apic_id_str = "APIC ID "
        drg_vvar_str = "DRAGON_VVAR"
        state_str = "STATE"

        pd_array={ # Entire table string array for printing
                # Single columns
                topdie_str:[], # Top Die
                phys_mod_str:[], # Local Physical module
                die_clid_str:[], # Global Class / Physical Module
                die_classlid_str:[], # Global Logical Module
                osmdl_str:[], # Global OS
                linux_str:[], # OS CPU
                apic_id_str:[], #Apic ID
                drg_vvar_str:[], # VVars
                state_str:[] # State
                }


        physical_to_local_logical_sorted = sorted(physical_to_global_logical_module.items(), key=lambda item: (item[1] == "--", item[1]))  
        for physical_module, logical_module in physical_to_local_logical_sorted: # For each active module, sorted by logical
            if physical_module in phys2ClassLog:
                # Get all module info
                topdie = physical_to_top_die_array[physical_module] # Top Die       
                class_global_logical = physical_to_global_class[physical_module] # Global physical / class module
                class_local_logical = physical_to_global_logical_module[physical_module] #Global logical module
                global_os = physical_to_global_os[physical_module] # Global OS Module
                state = physical_to_activeBit[physical_module] # State
                os_cpu = ' :: '.join(physical_to_OS_core[physical_module])  # OS Cores
                apic_id = ' :: '.join(physical_to_apic_id_array[physical_module])  # Apic_id
                vvars = ' :: '.join(physical_to_vvars[physical_module])  # Vvars

                #Append values to table string
                pd_array[topdie_str].append(topdie) # Append Top Die
                pd_array[phys_mod_str].append(f"{physical_module}") # Append physical module
                pd_array[die_clid_str].append(f"{class_global_logical}") # Append global physical / class module
                pd_array[die_classlid_str].append(f"{class_local_logical}") # Append global logical module
                
                pd_array[osmdl_str].append(f"{global_os}") # Append global OS Module
                pd_array[linux_str].append(os_cpu) # Append OS CPU
                pd_array[apic_id_str].append(apic_id) # Append Apic ID
                pd_array[drg_vvar_str].append(vvars) # Append dragon vvars
                pd_array[state_str].append(state) # Append state

        #Print table 
        df = pd.DataFrame(pd_array)
        df['First Core'] = df['OS CORES'].apply(extract_first_core)

        # Split into valid and invalid cores
        valid_cores = df[df['First Core'] != float('inf')]
        
        invalid_cores = df[df['First Core'] == float('inf')]
        valid_sorted = valid_cores.sort_values(by=['First Core', 'LOCAL PHYS MOD'])

        df_sorted = pd.concat([valid_sorted, invalid_cores], ignore_index=True)
        df_sorted = df_sorted.drop(columns=['First Core']).reset_index(drop=True)
        
        print("+" + "-" * 24 + "+")
        title = f"| Socket {socket_id}  :  CBB {cbb_id} |" # Show socket and compute info
        print(title.center(24))  
        print(tabulate(df_sorted, headers='keys', tablefmt='psql', showindex=False)) # Print table

        if log_path != None:ipc.nolog()
        
    except:
            import traceback
            traceback.print_exc()
            if log_path != None:ipc.nolog()

def verbose_function(cbb):
    cbb_name = cbb.name.upper()

    module_dis_mask = cbb.base.fuses.punit_fuses.fw_fuses_sst_pp_0_module_disable_mask
    print(f"\n\n{cbb_name} cbb.base.fuses.punit_fuses.fw_fuses_sst_pp_0_module_disable_mask : {module_dis_mask}")
    
    llc_slice_ia_cpp_dis = cbb.base.fuses.punit_fuses.fw_fuses_llc_slice_ia_ccp_dis
    print(f"{cbb_name} cbb.base.fuses.punit_fuses.fw_fuses_llc_slice_ia_ccp_dis : {llc_slice_ia_cpp_dis} \n\n")
    
    apic_id = cbb.computes.modules.cores.ml3_cr_pic_extended_local_apic_id
    print(f"APIC IDs {cbb_name}\n{apic_id} \n\n")
    
    print(f"P2L {cbb_name}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at0 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at0}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at1 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at1}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at2 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at2}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at3 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at3}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at4 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at4}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at5 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at5}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at6 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at6}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at7 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at7}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at8 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at8}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at9 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at9}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at10 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at10}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at11 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at11}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at12 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at12}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at13 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at13}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at14 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at14}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at15 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at15}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at16 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at16}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at17 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at17}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at18 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at18}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at19 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at19}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at20 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at20}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at21 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at21}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at22 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at22}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at23 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at23}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at24 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at24}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at25 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at25}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at26 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at26}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at27 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at27}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at28 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at28}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at29 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at29}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at30 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at30}")
    print(f"cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at31 -> {cbb.pcode.vars.ccp_cfg.ccp_physical_to_logical_map.at31}")

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
