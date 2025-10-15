import namednodes
import itpii,struct
import binascii as _binascii

print ("DMR Core Debug Utils || REV 0.0")

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=================================== IPC AND SV SETUP ===================================================#
#========================================================================================================#

ipc = None
api = None

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
#sv = _get_global_sv()
itp = itpii.baseaccess()

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== CONSTANTS AND GLOBAL VARIABLES =========================================================#
#========================================================================================================#

_CR_MCNT = 0x6da
verbose = False

ClassLog2Phy = {0:6,1:13,2:20,3:27,4:7,5:14,6:21,7:28,8:8,9:15,10:22,11:29,12:34,13:41,14:48,15:55,16:35,17:42,18:49,19:56,20:36,21:43,22:50,23:57} # Logical value : Physical value (only active modules in CWF)
phys2ClassLog = {value: key for key, value in ClassLog2Phy.items()} # Physical value : Logical value (only active modules in CWF)
phys2colrow= { 0:[0,1], 1:[0,2], 2:[1,1], 3:[1,2], 4:[1,3], 5:[1,4], 6:[1,5], 7:[1,6], 8:[1,7], 9:[2,1], 10:[2,2], 11:[2,3], 12:[2,4], 13:[2,5], 14:[2,6], 15:[2,7], 16:[3,1], 17:[3,2], 18:[3,3], 19:[3,4], 20:[3,5], 21:[3,6], 22:[3,7], 23:[4,1], 24:[4,2], 25:[4,3], 26:[4,4], 27:[4,5], 28:[4,6], 29:[4,7], 30:[5,1], 31:[5,2], 32:[5,3], 33:[5,4], 34:[5,5], 35:[5,6], 36:[5,7], 37:[6,1], 38:[6,2], 39:[6,3], 40:[6,4], 41:[6,5], 42:[6,6], 43:[6,7], 44:[7,1], 45:[7,2], 46:[7,3], 47:[7,4], 48:[7,5], 49:[7,6], 50:[7,7], 51:[8,1], 52:[8,2], 53:[8,3], 54:[8,4], 55:[8,5], 56:[8,6], 57:[8,7], 58:[9,1], 59:[9,2] } # Physical module : [Column,Row]

#========================================================================================================#
#=============== DEBUG SCRIPTS ==========================================================================#
#========================================================================================================#

def disable_Cstates(): 
  """
  Pcode will prevent any IA thread from going into a C-state deeper than indicated in this field.
  """
  sv = _get_global_sv()
  sv.sockets.cbbs.pcudata.dfx_ctrl_unprotected.core_cstate_limit=0x1 
  sv.sockets.cbbs.pcudata.dfx_ctrl_unprotected.pkg_cstate_limit =0x1 
  print("sv.sockets.cbbs.pcudata.dfx_ctrl_unprotected.core_cstate_limit=0x1")
  print("sv.sockets.cbbs.pcudata.dfx_ctrl_unprotected.pkg_cstate_limit=0x1")

def read_c6_counter(): 
    """
    Prints current c6 counter for each cbb and socket.
    """
    sv = _get_global_sv()
    for s in range (len(sv.sockets)):
      for c in range (len(sv.socket0.cbbs)):
          cmd = f"sv.socket{s}.cbb{c}.pcudata.pc6_rcntr"
          c6_value = eval(cmd) #Evaluate the string and store its return value in c6_value
          print (f"sv.socket{s}.cbb{c}.pcudata.pc6_rcntr: {c6_value}")

def turbo_dis(): 
  """
  Disable Turbo Frequency (P0) and limit processor to Guaranteed Frequency (P1).
  """
  sv = _get_global_sv()
  sv.sockets.cbbs.pcudata.dfx_ctrl_unprotected.turbo_dis=0x1 
  print("sv.sockets.cbbs.pcudata.dfx_ctrl_unprotected.turbo_dis=0x1")


def read_current_fivr_ps(): 
    """
    Inputs:
      Phys_module: (Int) physical module id to read.
      Compute: (Int, Default=0) respective compute of the desired physical module. Default: 0
      Socket: (Int, Default=0) respective socket for the desired compute. Default: 0

    Outputs:
      Cur_ps: (Float) returns current ps state as a float value. -1 if module not available in CWF.

    Given a physical module, read the register based on its respective Row and Column in the coretile.
    """
#    sv = _get_global_sv()
#    if phys_module in phys2ClassLog: #If the module is available in CWF
#      row = phys2colrow[phys_module][1] #Get row value
#      col = phys2colrow[phys_module][0] #Get column value
#      eval_str = f"float(sv.socket{socket}.compute{compute}.uncore.fivrhip.fivr_coretile_c{col}_r{row}.fivrhip_dcfci_vinfgated.vrciregstatus0.fivr_ps_state)"
#      cur_ps = eval(eval_str) #Evaluate the string and store its return value in cur_ps
#      print(f"sv.socket{socket}.compute{compute}.uncore.fivrhip.fivr_coretile_c{col}_r{row}.fivrhip_dcfci_vinfgated.vrciregstatus0.fivr_ps_state = {cur_ps}")
#      return cur_ps
#    else:
#      print(f"Physical module {phys_module} not available in CWF")
#      return -1 

    from diamondrapids.pdi_dev_tools.applications.blocks_handler.CBlocksHandler import blocks_handler
    blocks_handler.measurement_instruments.mi_ngf_fivr_status.Get()


"""
def disable_itd(): NOT FOUND YET IN DMR
    """"""
    Disables itd by setting the following registers:
	    sv.sockets.computes.pcudata.cutoff_tj = 0x0
      sv.sockets.ios.pcudata.cutoff_tj = 0x0
    """"""
    sv = _get_global_sv()
    #sv.sockets.computes.uncore.core_pmsb.core_pmsbs.core_pmsb_instance.pmsb_top.pma_core.acode_dfx_1=0x400000 
    sv.sockets.computes.pcudata.cutoff_tj = 0x0
    sv.sockets.ios.pcudata.cutoff_tj = 0x0
"""

def get_qdf():
    """
    Reads qdf from unit fuses using:
	    sv.sockets.cbbs.base.fuses.dfxagg_base_top.qdf_fuse
	
    Output:
      qdf: (String) Read QDF 
    """
    sv = _get_global_sv() # Load sv
    sv.socket0.cbbs.computes.fuses.load_fuse_ram() # Load fuse ram
    qdf=sv.sockets.cbbs.base.fuses.dfxagg_base_top.qdf_fuse# Read QDF
    # sv.sockets.cbbs.compute0.fuses.dfxagg_compute_top.qdf_fuse
    return (_binascii.unhexlify("%08x" % qdf).decode("utf8")) # Return QDF

def pcu_halt(die = ["all"]):
	global ipc
	ipc = _get_global_ipc()
	sv = _get_global_sv()
	print ("halting PCU" )
	ipc.unlock()
	#sv.refresh()
	dies = die

	if "all" in die:
		dies = []
		dies.extend(sv.socket0.imhs.name)
		#dies.extend(sv.socket0.cbbs.name) ---> since pcode is on IMH, that is why cbbs are not part of the halt?
		
	for _die in dies:
		try:
			print (f"sv.sockets.{_die}.pcodeio_map.io_microcontroller_configuration.halt_microcontroller=1")
			sv.sockets.get_by_path(_die).pcodeio_map.io_microcontroller_configuration.halt_microcontroller=1

			if (sv.sockets.get_by_path(_die).pcodeio_map.io_microcontroller_configuration.halted==1):
				print (f"{_die.upper()} PCU is halted == sv.sockets.imhs.pcodeio_map.io_microcontroller_configuration.halt_microcontroller==1")
			else:
				print (f"!!! {_die.upper()} PCU is NOT halted == sv.sockets.imhs.pcodeio_map.io_microcontroller_configuration.halted==0")
				
		except:
			print (f"!!!! halting PCU for {_die.upper()} got an exception. PCU may not be halted!!!")
		

def pcu_go(die = ["all"]):
	#global ipc
	ipc = _get_global_ipc()
	sv = _get_global_sv()
	print ("Restarting PCU" )
	ipc.unlock()
	#sv.refresh()
	dies = die

	if "all" in die:
		dies = []
		dies.extend(sv.socket0.imhs.name)
		#dies.extend(sv.socket0.computes.name)

	for _die in dies:
		if (sv.sockets.get_by_path(_die).pcodeio_map.io_microcontroller_configuration.halted==1):
			try:
				print (f"sv.sockets.{_die}.pcodeio_map.io_microcontroller_configuration.halt_microcontroller=0", "In progress")
				sv.sockets.get_by_path(_die).pcodeio_map.io_microcontroller_configuration.halt_microcontroller=0
				if (sv.sockets.get_by_path(_die).pcodeio_map.io_microcontroller_configuration.halted==0):
					print (f"{_die.upper()} PCU is Started == sv.sockets.imhs.pcodeio_map.io_microcontroller_configuration.halted==0")
				else:
					print (f"!!! {_die.upper()} PCU is NOT Started == sv.sockets.imhs.pcodeio_map.io_microcontroller_configuration.halted==1")
			except:
				print (f"!!!! Restarting PCU for {_die.upper()} got an exception. PCU may not be Started!!!")
		else:
			print(f"{_die} is already running.")
			
def do_clear_ucode():
	sv = _get_global_sv()
	print ("Clearing out micro_patch_valids")
	for i in range (0,31):
		x =  "sv.sockets.cbbs.computes.modules.cores.ms_cr_micro_patch_valids_reg_%d = 0" % i 
		if verbose:
			print (x)
		exec(x)

"""def dis_2CPM(dis_cores): #Not in use in DMR
  """"""
  dis_cores: "HIGH" or "LOW" to disable globally on all modules. usefull to run pseudo MESH
  """"""
  if dis_cores == "HIGH":
    dis=0xc
  elif dis_cores == "LOW":
    dis=0x3
  elif dis_cores == (0x3|0xc|0x9|0xa|0x5):
    dis = dis_cores
  else:
    print("-E- cores has to be define as LOW or HIGH dependin")
  return[
  f"sv.socket0.computes.fuses.pcu.pcode_lp_disable = {dis}"
  ]
"""

def dis_core_per_DCM(cbb_index=0, compute_index=0, core_index=0, hex_value=0x0,socket_index=None):
    # Define the valid options without the generic "sockets", "cbbs", "computes"
    sockets = ["socket0", "socket1"]
    cbbs = ["cbb0", "cbb1", "cbb2", "cbb3"]
    computes = ["compute0", "compute1", "compute2", "compute3"]
    cores = [f"core{i}" for i in range(8)]

    if socket_index is None:
        socket_index = 0

    # Validate indices
    if not (0 <= cbb_index < len(cbbs)):
        raise ValueError(f"Invalid cbb index: {cbb_index}. Must be between 0 and {len(cbbs) - 1}.")
    if not (0 <= compute_index < len(computes)):
        raise ValueError(f"Invalid compute index: {compute_index}. Must be between 0 and {len(computes) - 1}.")
    if not (0 <= core_index < len(cores)):
        raise ValueError(f"Invalid core index: {core_index}. Must be between 0 and {len(cores) - 1}.")
    if not (0 <= socket_index < len(sockets)):
        raise ValueError(f"Invalid socket index: {socket_index}. Must be between 0 and {len(sockets) - 1}.")

    # Map indices to their corresponding string values
    socket = sockets[socket_index]
    cbb = cbbs[cbb_index]
    compute = computes[compute_index]
    core = cores[core_index]

    # Construct the register path
    fuse_str = f"sv.{socket}.{cbb}.{compute}.fuses.{core}_fuse.core_fuse_core_fuse_pma_lp_enable"

    # Override the register with the hex value
    reg = eval(fuse_str)
    reg.write(hex_value)
    print(f"Your {core} (DCM) placed in {compute}, {cbb} has now a value of 0x{hex_value}")
    print("\nEncoding: BothCoresDisabled = 2'h0; Core0EnabledOnly,2'h1; Core1EnabledOnly,2'h2; BothCoresEnabled,2'h3")
    print(f"\nUse sv.{socket}.{cbb}.{compute}.fuses.{core}_fuse.core_fuse_core_fuse_pma_lp_enable.show to validate")


def set_license(lic="128", disable_cstate=True):
    """sets license level
         lic = "128" or "256" or "512" or "AMX"  or <0-7>
         128 Light = 0
         128 Heavy = 1
         256 Light = 2
         256 Heavy = 3
         512 Light = 4
         512 Heavy = 5
         AMX Light = 6
         AMX Heavy = 7
         Note, this breaks with Cstates
    """
    global sv
    sv = _get_global_sv()
    print ("setting license to {}".format(lic))
    if (lic=="128"): lic = 1
    elif lic=="256": lic = 3
    elif lic=="512": lic = 5
    elif lic=="AMX": lic = 7
    
    if disable_cstate:
        print("!!! DISABLING CSTATES TO MAKE LICENSE LEVEL CHANGE WORK !!!!")
        disable_Cstates()

    if (0 <= lic <= 7):
        sv.sockets.cbbs.base.fuses.punit_fuses.fw_fuses_iccp_max_license = lic
        sv.sockets.cbbs.base.fuses.punit_fuses.fw_fuses_iccp_min_license = lic
        print(f"\nLicense {lic} has been set ")
        print("\nCheck sv.sockets.cbbs.base.fuses.punit_fuses.fw_fuses_iccp_<max/min>_license registers for confirmation ")
        print("""
        Encoding: \n
         128 Light = 0
         128 Heavy = 1
         256 Light = 2
         256 Heavy = 3
         512 Light = 4
         512 Heavy = 5
         AMX Light = 6
         AMX Heavy = 7""")
    else:
        print ("DID NOT SET LICENSE!!!")

def disable_dcf(): 
    global sv
    sv = _get_global_sv()
    sv.socket0.computes.cpu.cores.ml3_cr_pwrdn_ovrd.dcf_disable=1
    print("sv.socket0.computes.cpu.cores.ml3_cr_pwrdn_ovrd.dcf_disable=1")
    

def set_dcf_ratio(ratio=2):
    """
    # Set max divide factor forclock divider 16/8/4/2.
    # 00=2, 01=4, 10=8, 11=16.
    """
    global sv
    sv = _get_global_sv()
    ratio_encoding = {
    2: 0,
    4: 1,
    8: 2,
    16: 3
        
    }

    if ratio in ratio_encoding:
        encoded_value = ratio_encoding[ratio]
        print("sv.sockets.cbbs.computes.pmas.pmsb.throttle_control.throttle_fsm_enable = 0x0 ---> Disabling throttle control FSM")
        print(f"Setting throttle ratio to {ratio} (encoded as {encoded_value})")
        sv.sockets.cbbs.computes.pmas.pmsb.throttle_control.throttle_fsm_enable = 0x0 #this needs to be confirmed once fused units available
        sv.sockets.cbbs.computes.pmas.pmsb.throttle_control.throttle_max_divide_factor=encoded_value
        print(f"sv.sockets.cbbs.computes.pmas.pmsb.throttle_control.throttle_max_divide_factor={encoded_value}")
        print(f"Ratio {ratio} properly set based on {ratio_encoding}")
    else:
        raise ValueError("Invalid ratio. Available clock dividers are: 2, 4, 8, 16")

def disable_pvp():  
    itp.halt()
    sv.sockets.cbbs.computes.modules.cores.rsvec_cr_rs2_dft.ropvp1024block_disable=0x1
    sv.sockets.cbbs.computes.modules.cores.rsvec_cr_rs2_dft.ropvp64block_disable=0x1
    sv.sockets.cbbs.computes.modules.cores.rsvec_cr_rs_pvp2_ctl_0.pvp_enable=0x0
    print("PVP disabled")
    #sv.sockets.computes.cpu.modules.cores.rob1_cr_rs_pvp_ctl = 0 ----> This was not found in DMR
    itp.go()
    
def enable_pvp():  
    itp.halt()
    sv.sockets.cbbs.computes.modules.cores.rsvec_cr_rs2_dft.ropvp1024block_disable=0x0
    sv.sockets.cbbs.computes.modules.cores.rsvec_cr_rs2_dft.ropvp64block_disable=0x0
    sv.sockets.cbbs.computes.modules.cores.rsvec_cr_rs_pvp2_ctl_0.pvp_enable=0x1
    print("PVP enabled")
    #sv.sockets.computes.cpu.modules.cores.rob1_cr_rs_pvp_ctl = 0 ----> This was not found in DMR
    itp.go() 
    
def read_acp_status(phys_core=0, Loop = 1, socket=0):
    print("""
    Encoding: \n
    0000: Idle (can be clock gated)
    0001: Running (Cannot be clock gated)
    0010: Halted (Can get UC reset and enter warm reset / PKGC    
    """)
    
    cbb = phys_core // 32
    compute = (phys_core % 32) // 8
    pma = phys_core
    
    eval_str_status = f"sv.socket{socket}.cbb{cbb}.compute{compute}.pma{phys_core}.pmsb.io_acode_status.status"
    
    for i in range(Loop):
        cur_status = eval(eval_str_status)
        print (eval_str_status, "=", cur_status)
        #return cur_status
    
def read_acp_ready(phys_core=0, Loop = 1, socket=0):
    print("""
    Encoding: \n
    1: Acode ready for ACP mode
    0: Acode not ready for ACP mode
    
    Field should be set by Acode during boot and PKG-C state exit
    """)
    cbb = phys_core // 32
    compute = (phys_core % 32) // 8
    pma = phys_core
    
    eval_str_rst = f"sv.socket{socket}.cbb{cbb}.compute{compute}.pma{phys_core}.pmsb.io_acode_status.acode_reset_done"
    
    for i in range(Loop):
        cur_rst = eval(eval_str_rst)
        print(eval_str_rst, "=", cur_rst)
        #return cur_rst

def print_current_core_info(phys_core, Loop = 1, socket=0):
    for i in range(Loop):
        iaR = read_current_core_ratio(phys_core, Loop, socket)
        iaV = read_current_core_voltage(phys_core, Loop, socket)
        iaL = read_current_license(phys_core, Loop, socket)
        print( "DCM = %s, IA Ratio = %s, IA Volt = %f,  IALicense= %s" % (phys_core, iaR, iaV, iaL))

def read_current_core_voltage(phys_core, Loop = 1, socket=0):
    #Core Voltage. 2.5 mV steps.
    cbb = phys_core // 32
    compute = (phys_core % 32) // 8
    pma = phys_core
    eval_str = f"float(sv.socket{socket}.cbb{cbb}.compute{compute}.pma{phys_core}.pmsb.io_wp1.core_voltage) * 0.0025"
    #eval_str = f"float(sv.socket{socket}.compute{compute}.uncore.core_pmsb.core_pmsb{phys_core}.core_pmsb_instance.pmsb_top.pma_core.acp_state.core_voltage) * 0.0025"
    cur_voltage = eval(eval_str)
    return cur_voltage

def read_current_core_ratio(phys_core, Loop = 1, socket=0):
    #CORE_FREQUENCY: MCLK Ratio or PLL Ratio (specified in 100 MHz bins) not like WP1 PMSB register
    cbb = phys_core // 32
    compute = (phys_core % 32) // 8
    pma = phys_core
    eval_str = f"sv.socket{socket}.cbb{cbb}.compute{compute}.pma{phys_core}.pmsb.io_wp1.core_frequency"
    #eval_str = f"sv.socket{socket}.compute{compute}.uncore.core_pmsb.core_pmsb{phys_core}.core_pmsb_instance.pmsb_top.pma_core.acp_state.core_ratio"
    #pll_str= f"sv.socket{socket}.compute{compute}.taps.scf_gnr_maxi_coretile_bot{phys_core}_xi_core_ljpll_ljpll_tap.ljpll_tapstatus.pll_tap_status_pll_ratio"
    cur_ratio = eval(eval_str)
    #cur_pll_ratio = 0
    #cur_pll_ratio = eval (pll_str)
    return cur_ratio #, cur_pll_ratio

def read_current_license(phys_core, Loop = 1, socket=0):
    cbb = phys_core // 32
    compute = (phys_core % 32) // 8
    pma = phys_core
    eval_str = f"sv.socket{socket}.cbb{cbb}.compute{compute}.pma{phys_core}.pmsb.pma_debug.iccp_granted"
    #eval_str = f"sv.socket{socket}.compute{compute}.uncore.core_pmsb.core_pmsb{phys_core}.core_pmsb_instance.pmsb_top.pma_core.acp_state.iccp_granted"
    cur_lic = eval(eval_str)
    return cur_lic

"""
def set_dragon_lockdelay():
    sv.sockets.io0.uncore.ubox.ncevents.lockcontrol_cfg.lockdelay = 0x1
"""
