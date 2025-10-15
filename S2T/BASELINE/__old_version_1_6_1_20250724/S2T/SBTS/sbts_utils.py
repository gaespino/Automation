import __main__
scope = __main__




import sys
#import cStringIO

import os
import socket as ws
import datetime


try:
    import sbts
    import sbft.util as util
    #import util
    dut = __main__.dut  # will be assign to core/gt instantiated class
    rpd = __main__.rpd
    tap = __main__.dut.tap
    ctap = __main__.dut.ctap

except:
    print( "DUT or CTAP OR TAP RPD NOT AVAILABLE!")

use_itp=False
try:
    import itpii
    itp = itpii.baseaccess()
    use_itp=True
except:
    pass

verbose=False


def set_F1(license="avx3", core_voltage=0.480):
    set_vfl(8, core_voltage, license, 8)

def set_F4(license="avx3", core_voltage=0.750):
    set_vfl(32, core_voltage, license, 22)

def set_F7(license="avx3", core_voltage=0.9):
    set_vfl(42, core_voltage, license, 22)

def set_vfl(core_ratio, core_voltage, license="avx3",cfc_ratio=22, cfc_voltage=0.8):
    set_license(license)
    set_core_ratio(core_ratio)
    set_core_voltage(core_voltage)
    set_cfc_ratio(cfc_ratio)
    set_cfc_voltage(cfc_voltage)

def setupDCF():
    set_vfl(32, 0.8)
    sbts.general.vvar_val=0xf0000
    sbts.general.vvar_num=1
    waittime(10)
    sbts.general.dcf=True
    sbts.general.dcf_ratio=2

def set_vfl(core_ratio, core_voltage, license="avx3",cfc_ratio=22, cfc_voltage=0.8):
    set_license(license)
    set_core_ratio(core_ratio)
    set_core_voltage(core_voltage)
    set_cfc_ratio(cfc_ratio)
    set_cfc_voltage(cfc_voltage)

def set_core_voltage(voltage):
    sbts.vr.setv['CDIE_CORE'] = voltage

def set_core_ratio(ratio):
    sbts.dut.busratio["CDIE_CORE"]=ratio

def set_cfc_ratio(ratio):
    sbts.dut.busratio["CDIE_CFC"]=ratio

def set_cfc_voltage(voltage):
    sbts.vr.setv["CDIE_CFC"]=voltage

def set_license(lic): 
    if lic=="tmul": lic="amx"
    if lic=="avx": lic="sse"
    if lic == "amx" or lic=="avx2" or lic=="avx3" or lic =="sse":
        sbts.general.coreExtension=lic
    else:
        print ("DID NOT SET LICENSE: default is SSE")
        print ("Use sse, avx2, avx3, amx ")

def get_license(): 
    print(sbts.general.coreExtension)

def drDump(c=0, t=0, start_string = "", csv=False, printit=True, include_header=True):
    is_bsp = dut.ctap.crb64(0x53a,core = c, thread = t)[8]
    is_running = int(dut.ctap.crb64(0x2aa, core=c, thread=t)>> t) & 1  # ROB1_CR_MISC_INFO.thread_activet[01]
    dr0 = dut.ctap.crb64(0x6dc,core = c, thread = t)
    dr1 = dut.ctap.crb64(0x6de,core = c, thread = t)
    dr2 = dut.ctap.crb64(0x6e0,core = c, thread = t)
    dr3 = dut.ctap.crb64(0x6e2,core = c, thread = t)
    ifu_linaddr = dut.ctap.crb64(0x558,core = c, thread = t)

    if (printit and include_header):
        util.printcol(drDumpHeader(csv), "BLUE")
        if (start_string == ""):
            start_string = dut.testname
    if (csv):
        result  = ("%s,%2.2d,%1.1d,%1.1d,%1.1d,0x%16.16x,0x%16.16x,0x%16.16x,0x%16.16x,0x%16.16x" %(start_string, c,t, is_bsp, is_running, dr0,  dr1, dr2, dr3, ifu_linaddr))
    else:
        result  = ("%s %2.2d %1.1d %1.1d %1.1d 0x%16.16x 0x%16.16x 0x%16.16x 0x%16.16x 0x%16.16x" % 
            ("{:<24}".format(start_string), c,t, is_bsp, is_running, dr0,  dr1, dr2, dr3, ifu_linaddr))
    if (printit):
        if (dr0 == 0xACED):
            util.printcol(result, "GREEN")
        else:
            util.printcol(result, "YELLOW")
        return("")
    else:
        return (result)
        
def print_tap_config(c=0, t=0):
    ctap_cr_tap_config = dut.ctap.crb(0x114, core=c, thread=t)
    print("ctap_cr_tap_config.config_restart 0x%x" % ctap_cr_tap_config[00])
    print("ctap_cr_tap_config.disable_prefetchers 0x%x" % ctap_cr_tap_config[1])
    print("ctap_cr_tap_config.disable_panic_mode 0x%x" % ctap_cr_tap_config[2])
    print("ctap_cr_tap_config.at_field_core_isolation 0x%x" % ctap_cr_tap_config[3])
    print("ctap_cr_tap_config.kill_idi 0x%x" % ctap_cr_tap_config[4])
    print("ctap_cr_tap_config.disable_power_gating 0x%x" % ctap_cr_tap_config[5])
    print("ctap_cr_tap_config.hash_map_coallocated_llc 0x%x" % ctap_cr_tap_config[6])
    print("ctap_cr_tap_config.rsvd0 0x%x" % ctap_cr_tap_config[7])
    print("ctap_cr_tap_config.sbft_mode 0x%x" % ctap_cr_tap_config[8])
    print("ctap_cr_tap_config.run_bist 0x%x" % ctap_cr_tap_config[9])
    print("ctap_cr_tap_config.disable_mc_init 0x%x" % ctap_cr_tap_config[10])
    print("ctap_cr_tap_config.dis_cpuid 0x%x" % ctap_cr_tap_config[11])
    print("ctap_cr_tap_config.disable_uncore_ucode_init 0x%x" % ctap_cr_tap_config[12])
    print("ctap_cr_tap_config.bist_in_progress 0x%x" % ctap_cr_tap_config[13])
    print("ctap_cr_tap_config.disable_power_downs 0x%x" % ctap_cr_tap_config[14])
    print("ctap_cr_tap_config.alt_reset_vector 0x%x" % ctap_cr_tap_config[15])
    print("ctap_cr_tap_config.ucode_stall_enable 0x%x" % ctap_cr_tap_config[16])
    print("ctap_cr_tap_config.stop_ucode_at_end_macro 0x%x" % ctap_cr_tap_config[17])
    print("ctap_cr_tap_config.bist_result 0x%x" % ctap_cr_tap_config[18])
    print("ctap_cr_tap_config.rsvd1 0x%x" % ctap_cr_tap_config[19])
    print("ctap_cr_tap_config.drop_llc_special_cycles 0x%x" % ctap_cr_tap_config[20])
    print("ctap_cr_tap_config.sv_reset 0x%x" % ctap_cr_tap_config[21])
    print("ctap_cr_tap_config.signtrst_cb 0x%x" % ctap_cr_tap_config[22])
    print("ctap_cr_tap_config.clear_sticky_tapcr_clken 0x%x" % ctap_cr_tap_config[23])
    print("ctap_cr_tap_config.en_tap_clks_in_tlreset 0x%x" % ctap_cr_tap_config[24])
    print("ctap_cr_tap_config.mlc_miss_isolation 0x%x" % ctap_cr_tap_config[25])
    print("ctap_cr_tap_config.dft_stop_mclk 0x%x" % ctap_cr_tap_config[26])
    print("ctap_cr_tap_config.disable_cr_writes_to_tap_reg 0x%x" % ctap_cr_tap_config[27])
    print("ctap_cr_tap_config.resume_mclk 0x%x" % ctap_cr_tap_config[28])
    print("ctap_cr_tap_config.resume_mnsclk 0x%x" % ctap_cr_tap_config[29])
    print("ctap_cr_tap_config.dft_mclk_en 0x%x" % ctap_cr_tap_config[30])
    print("ctap_cr_tap_config.lock_status 0x%x" % ctap_cr_tap_config[31])


def dumpInfo(c=0, t=0):
    ctap_cr_tap_config = dut.ctap.crb(0x114, core=c, thread=t)
    print ("ctap_cr_tap_config 0x%x"  % ctap_cr_tap_config)
    print ("\tctap_cr_tap_config.config_restart 0x%x"  % ctap_cr_tap_config[0])
    print ("\tctap_cr_tap_config.disable_prefetchers 0x%x"  % ctap_cr_tap_config[1])
    print ("\tctap_cr_tap_config.sbft_mode 0x%x"  % ctap_cr_tap_config[8])
    print ("\tctap_cr_tap_config.dis_cpuid 0x%x"  % ctap_cr_tap_config[11])
    print ("\tctap_cr_tap_config.disable_uncore_ucode_init 0x%x"  % ctap_cr_tap_config[12])
    print ("\tctap_cr_tap_config.disable_panic_mode 0x%x"  % ctap_cr_tap_config[1])
    print ("\tctap_cr_tap_config.resume_mclk 0x%x"  % ctap_cr_tap_config[28])
    print ("\tctap_cr_tap_config.resume_mnsclk 0x%x"  % ctap_cr_tap_config[29])
    ctap_cr_tap_config2 = dut.ctap.crb(0x116, core=c, thread=t)
    print ("ctap_cr_tap_config2 0x%x"  % ctap_cr_tap_config2)
    print ("\tctap_cr_tap_config2.disable_dcf_mode 0x%x"  % ctap_cr_tap_config2[4])
    print ("\tctap_cr_tap_config2.high_current_disable 0x%x"  % ctap_cr_tap_config2[5])
    print ("\tctap_cr_tap_config2.disable_mlc_cache_init 0x%x"  % ctap_cr_tap_config2[14])
    ml5_cr_dcf_control = dut.ctap.crb64(0x2fa, core=c, thread=t)
    print ("ml5_cr_dcf_control 0x%x"  % ml5_cr_dcf_control)
    print ("\tml5_cr_dcf_control.current_dcf_ratio 0x%x"  % ml5_cr_dcf_control[63:60])
    ml3_cr_gv_ctrl_debug = dut.ctap.crb(0x257, core=c, thread=t)
    print ("ml3_cr_gv_ctrl_debug. 0x%x"  % ml3_cr_gv_ctrl_debug)
    print ("\tml3_cr_gv_ctrl_debug.force_debug 0x%x"  % ml3_cr_gv_ctrl_debug[0])
    print ("\tml3_cr_gv_ctrl_debug.pll_ratio_valid 0x%x"  % ml3_cr_gv_ctrl_debug[1])
    print ("\tml3_cr_gv_ctrl_debug.pll_ratio 0x%x"  % ml3_cr_gv_ctrl_debug[8:2])
    print ("\tml3_cr_gv_ctrl_debug.tsc_gv_behavior_enable 0x%x"  % ml3_cr_gv_ctrl_debug[10])
    print ("\tml3_cr_gv_ctrl_debug.dbg_dcf_master 0x%x"  % ml3_cr_gv_ctrl_debug[19])
    print ("\tml3_cr_gv_ctrl_debug.dbg_dcf_ratio 0x%x"  % ml3_cr_gv_ctrl_debug[23:20])
    ml3_cr_pic_boot_message = dut.ctap.crb(0x3c2, core=c, thread=t)
    print ("ml3_cr_pic_boot_message 0x%x"  % ml3_cr_pic_boot_message )
    print ("\tml3_cr_pic_boot_message.coreratio 0x%x"  % ml3_cr_pic_boot_message[16:10] )
    ml3_cr_pwrdn_ovrd = dut.ctap.crb(0x280, core=c, thread=t)
    print ("ml3_cr_pwrdn_ovrd 0x%x" % ml3_cr_pwrdn_ovrd)
    print ("\tml3_cr_pwrdn_ovrd.tap_dcf_en 0x%x" % ml3_cr_pwrdn_ovrd[28])
    print ("\tml3_cr_pwrdn_ovrd.dcf_disable 0x%x" % ml3_cr_pwrdn_ovrd[22])
    print_timers(c,t)
    
def print_timers(c=6,t=0):
    ml3_cr_pic_tsc = dut.ctap.crb(0x3c6, core=c, thread=t)
    print ("ml3_cr_pic_tsc 0x%x" % ml3_cr_pic_tsc)
    ml3_cr_mlc_acnt_counter = dut.ctap.crb(0x6d4, core=c, thread=t)
    print ("ml3_cr_mlc_acnt_counter 0x%x" % ml3_cr_mlc_acnt_counter)

def write_clock_ctrl(c=6, value=0x40):
    dut.ctap.tap_wr("CORE_CLOCKCTRL",value, core=c)
    
def dcf_effectiveness(c=0, t=0, sleep=10):
    import time
    ml3_cr_mlc_acnt_counter = dut.ctap.crb(0x6d4, core=c, thread=t)
    ml3_cr_pic_tsc = dut.ctap.crb(0x3c6, core=c, thread=t)
    print("ACNT %d TSC %d"  % (ml3_cr_mlc_acnt_counter, ml3_cr_pic_tsc))
    time.sleep(sleep)
    ml3_cr_mlc_acnt_counter_delta = dut.ctap.crb(0x6d4, core=c, thread=t) - ml3_cr_mlc_acnt_counter
    ml3_cr_pic_tsc_delta = dut.ctap.crb(0x3c6, core=c, thread=t) - ml3_cr_pic_tsc
    print("ACNT %d TSC %d effectiveness = %f"  % (ml3_cr_mlc_acnt_counter_delta, ml3_cr_pic_tsc_delta, ( ml3_cr_pic_tsc_delta/ml3_cr_mlc_acnt_counter_delta)))
    
def dcf_set_ratio(dcf_ratio, c, t=0):
    ml3_cr_gv_ctrl_debug = dut.ctap.crb(0x257, core=c, thread=t)
    ml3_cr_gv_ctrl_debug[0] =1 # force_debug
    ml3_cr_gv_ctrl_debug[23:20] =dcf_ratio
    ml3_cr_gv_ctrl_debug[19]=1 # dbg_dcf_ratio
    dut.ctap.crb(0x257, data=int(ml3_cr_gv_ctrl_debug), core=c, thread=t)
    ml5_cr_dcf_control = dut.ctap.crb64(0x2fa, core=c, thread=t)
    current_dcf_ratio = ml5_cr_dcf_control[63:60]
    if (dcf_ratio != current_dcf_ratio):
        print("DCF ratio was not set:  Expected: 0x%x Actual: 0x%x" % (dcf_ratio, current_dcf_ratio))

def pll_set_ratio(pll_ratio, c, t=0):
    ml3_cr_gv_ctrl_debug = dut.ctap.crb(0x257, core=c, thread=t)
    ml3_cr_gv_ctrl_debug[0] =1 # force_debug
    ml3_cr_gv_ctrl_debug[1] =1 # pll_ratio_valid
    ml3_cr_gv_ctrl_debug[8:2] = pll_ratio
    dut.ctap.crb(0x257, data=int(ml3_cr_gv_ctrl_debug), core=c, thread=t)

def dcf_read_ratio(dcf_ratio, c, t):
    print ("ml5_cr_dcf_control 0x%x"  % dut.ctap.crb64(0x2fa, core=c, thread=t))

def drDumpHeader(csv=False):
    if (csv):
        return("TEST,CORE,THREAD,BSP,ACTIVE,DR0,DR1,DR2,DR3,IFU_LINADR")
    else:
        return("%s  C T B A %s %s %s %s %s" % ("{0:^24}".format("TEST"), "{0:^18}".format("DR0"), "{0:^18}".format("DR1"), "{0:^18}".format("DR2"),"{0:^18}".format("DR3"),"{0:^18}".format("IFU_LINADR")))
    
def drDumpAll(csv=False, start_string = "", bsp_only=False, printit=True, include_header=True, print_t1 = False):
     core_cr_apic_base = 0x53a
     return_str = ""
     #sep_str = ","  if csv_ret else '\n'
     sep_str = '\n'
     if (start_string == ""):
        start_string = dut.testname
     #if (csv_ret==False):
     if (include_header):
         return_str = drDumpHeader(csv) + sep_str
         if (printit):  util.printcol(return_str, "YELLOW")
     for i in dut._act_cores:
        if ( (dut.ctap.crb64(core_cr_apic_base, core=i, thread=0)[8] == 1) or (bsp_only == False ) ):
            if (i!=dut._act_cores[0]): return_str += sep_str
            return_str += drDump(i, 0, start_string=start_string, csv=csv, printit=printit, include_header=False)
            if (print_t1): return_str += sep_str + drDump(i, 1, start_string=start_string, printit=printit, include_header=False, csv=csv)
     if (printit==False): 
        return return_str

def read_cr(cr, c):
    crb = dut.ctap.crb64(cr,core=c,cmpmask=0xfffffffff)
    util.printlog(f"cr = 0x%x core = {c} " %(crb), 'screen', 'yellow', verbose=True)

def write_cr(cr,c, data):
     dut.ctap.crb64(cr,core=c,data=data)

def clearWaitBSPDR0(c=0, t=0):
    dut.ctap.crb64(0x6dc,core = c, thread = t, data=0xd05e3a17)

def setVVWAIT():
    sbts.general.vvar_num=0x340
    sbts.general.vvar_val=0x4

def vvarOverrideAtBSPWait(c=0, vvar_num=0, vvar_val=0):
    dut.ctap.crb64(0xda,core = c, thread = 0, data=0x80000000  | vvar_num)  
    dut.ctap.crb64(0xa8,core = c, thread = 0, data=vvar_val)  

def activeThreads(c=0):
    rob1_cr_misc_info = int(dut.ctap.crb64(0x2aa,core = c))
    print ("C%d T0: %d" %( (c, rob1_cr_misc_info & 1)))
    print ("C%d T1: %d" %( (c, (rob1_cr_misc_info>>1) & 1)))
    
def convert(obj):
    #dut.dfx.asmobj2vec(obj)
    dut.set_mode('slcvec')
    dut.pat_conv(obj)

def mcdump(c=0, t=0):
     print ("C%dT%d: MC0_STATUS: 0x%x:" % ( c,t, dut.ctap.crb64(1808,core = c, thread = t) ))
     print ("C%dT%d: MC1_STATUS: 0x%x:" % ( c,t, dut.ctap.crb64(1744,core = c, thread = t) ))
     print ("C%dT%d: MC2_STATUS: 0x%x" % ( c,t, dut.ctap.crb64(558,core = c, thread = t) ))
     print ("C%dT%d: MC3_STATUS: 0x%x" % ( c,t, dut.ctap.crb64(632,core = c, thread = t) ))
     #IF BIT 63=1 and MISC==1
     print ("C%dT%d: MC3_MISC: 0x%x" % ( c,t, dut.ctap.crb64(0x274,core = c, thread = t) ))
     print ("C%dT%d: MC3_MISC2: 0x%x" % ( c,t, dut.ctap.crb64(0x276,core = c, thread = t) ))
     #IF BIT 63=1 and VAL_ADDR==1
     print ("C%dT%d: MC3_ADDRESS: 0x%x" % ( c,t, dut.ctap.crb64(0x270,core = c, thread = t) ))

def timerOff():
    sbts.psm.autoofftimer(False)

def timerReset():
    sbts.psm.autoofftimer(False)
    sbts.psm.autoofftimer(True)

def addPadding(pre_pad = 16, post_pad=16):
    """
    Run this before generating patterns
    This is needed for tools like imunch
    """
    dut.dfx.stf.entry_post_pad=post_pad
    dut.dfx.stf.entry_pre_pad=pre_pad
    

def builduBCAction(mbp=None, toggle_allocator_stall=False, config_restart_toggle=False, cr_access_b=False, debug_counter_toggle=False, so_rst_pulse=False):
    ret_val = 0
    if mbp!=None:
        ret_val = mbp
    if toggle_allocator_stall:
        ret_val += (3<<23)
    if config_restart_toggle:
        ret_val += (1<<28)
    if cr_access_b:
        ret_val += (1<<4)
    if debug_counter_toggle:
        ret_val += (1<<29)
    if so_rst_pulse:
        ret_val += (1<<20)
    print ("0x%x" % ret_val)
    return ret_val

def builduBCTrigger(mbp = None, debugcounter_match=None):
    ret_val=1<<33 #watchdog
    if mbp!=None:
        ret_val = mbp
    if debugcounter_match!=None:
        ret_val |= (debugcounter_match<<19)
    print ("trigger = 0x%x"  % ret_val)
    return ret_val

def programuBPC(num, core, trigger=None, action=None, ecc=None, trigger_now=False, mbp_arm=None):
    action_base = 238 # add 2 for each #
    trigger_base = 250
    ecc_base = 262
    action_crb = num*2 + action_base
    if action !=None:
        writeCRB(action_crb, core, action, name="action")
    trigger_crb = num*2 + trigger_base
    if trigger !=None:
        writeCRB(trigger_crb, core, trigger,name="trigger")
    ecc_crb = num*2 + ecc_base
    if ecc==None:
        ecc = 0x300001 # DR_CONTROLS_TRIGGER_DETECT_EDGE and DR_CONTROLS_TRIGGER_DETECT_MODE
    if trigger_now:
        ecc |= 1<<23
    if mbp_arm != None:
        ecc |= (mbp_arm<<32)
        ecc &= 0xfffffffffffffffe
    writeCRB(ecc_crb,core = core, data=ecc,name="ecc")

def clearBP(c):
    programuBPC(0, core=c, trigger=0, action=0, ecc=0)
    programuBPC(1, core=c, trigger=0, action=0, ecc=0)
    programuBPC(2, core=c, trigger=0, action=0, ecc=0)
    programuBPC(3, core=c, trigger=0, action=0, ecc=0)
    programuBPC(4, core=c, trigger=0, action=0, ecc=0)
    programuBPC(5, core=c, trigger=0, action=0, ecc=0)
    printAlluBPState(c) # Clears out the state

def testuBP(c):
    programuBPC(0, core=c, trigger=0, action=0,  trigger_now=True)
    programuBPC(1, core=c, trigger=0, action=0,  trigger_now=True)
    programuBPC(2, core=c, trigger=0, action=0,  trigger_now=True)
    programuBPC(3, core=c, trigger=0, action=0,  trigger_now=True)
    programuBPC(4, core=c, trigger=0, action=0,  trigger_now=True)
    programuBPC(5, core=c, trigger=0, action=0,  trigger_now=True)
    printAlluBPState(c)

def testuBP1(c):
    #clearBP(c)
    printAlluBPState(c)
    print("------------------")

    t = builduBCTrigger(mbp=4)
    a = builduBCAction(mbp=8)
    programuBPC(2, core=c, trigger=t, action=a)

    t = builduBCTrigger(mbp=2)
    a = builduBCAction(mbp=4)
    programuBPC(3, core=c, trigger=t, action=a)

    t = builduBCTrigger(mbp=1)
    a = builduBCAction(mbp=4)
    programuBPC(4, core=c, trigger=t, action=a)
    
    #printAlluBPState(c)
    print("------------------")
    a = builduBCAction(mbp=1)
    programuBPC(5, core=c, trigger=0, action=a,  trigger_now=True)
    #printAlluBPState(c)


def testuBP2(c):
    #clearBP(c)
    printAlluBPState(c)
    print("------------------")
    writeCRB(274, core=c, data=(150000 | 1 << 31), name="debugcounter")
    t = builduBCTrigger(debugcounter_match=0x1)
    a = builduBCAction(mbp=8)
    programuBPC(2, core=c, trigger=t, action=a)

    t = builduBCTrigger(mbp=2)
    a = builduBCAction(debug_counter_toggle=True)
    programuBPC(3, core=c, trigger=t, action=a)

    #t = builduBCTrigger(mbp=1)
    #a = builduBCAction(mbp=4)
    #programuBPC(4, core=c, trigger=t, action=a)
    
    #printAlluBPState(c)
    print("------------------")
    a = builduBCAction(mbp=2)
    programuBPC(5, core=c, trigger=0, action=a,  trigger_now=True)
    #printAlluBPState(c)



def printAlluBPState(c):
    printuBPState(c,0)
    printuBPState(c,1)
    printuBPState(c,2)
    printuBPState(c,3)
    printuBPState(c,4)
    printuBPState(c,5)

def writeCRB(crb, core, data, sixtyfour=True, name=""):
    if sixtyfour:
        if use_itp:
            if verbose: print (f"itp.threads[%d].crb64(0x%x,0x%x) # %s" % (core, crb, data,name))
            itp.threads[core].crb64(crb, data)
        else:
            if verbose: print (f"dut.ctap.crb64(0x%x,core = %d, data=0x%x) # %s" % (crb, core, data,name))
            dut.ctap.crb64(crb,core = core, data=data)
    else:
        if use_itp:
            if verbose: print (f"itp.threads[%d].crb(0x%x,0x%x) # %s" % (core, crb, data,name))
            itp.threads[core].crb(crb, data)
        else:
            if verbose: print (f"dut.ctap.crb(0x%x,core = %d, data=0x%x) # s" % (crb, core, data, name))
            dut.ctap.crb(crb,core = core, data=data)

def readCRB(crb, core, sixtyfour=True, name=""):
    if sixtyfour:
        if use_itp:
            if verbose: print (f"itp.threads[%d].crb64(0x%x) # %s" % (core, crb,name))
            return(itp.threads[core].crb64(crb))
        else:
            if verbose: print (f"dut.ctap.crb64(0x%x,core = %d)# %s" % (crb, core,name))
            return (dut.ctap.crb64(crb,core = core))
    else:
        if use_itp:
            if verbose: print (f"itp.threads[%d].crb(0x%x) # %s" % (core, crb,name))
            return(itp.threads[core].crb(crb))
        else:
            if verbose:print (f"dut.ctap.crb(0x%x,core = %d) # s" % (crb, core, name))
            return(dut.ctap.crb(crb,core = core))


def printuBPState(core, num):
    state_crb = num*2 + 314
    brkptstate = readCRB(state_crb,core = core)
    
    if (brkptstate[16] == 1) :
        print ("Core: %d ctap_cr_brkptstate_%d 0x%x"  % (core, num, brkptstate))
        print ("\tctap_cr_brkptstate_%d.action_occured=%d"  % (num,brkptstate[16]))
        #print ("\tctap_cr_brkptstate_%d.mbp=0x%x"  % (num,brkptstate[20:17]))
        print ("\tctap_cr_brkptstate_%d.debugcounter_match=%d"  % (num,brkptstate[38:36]))
    print ("\tctap_cr_brkptstate_%d.mbp=0x%x"  % (num,brkptstate[20:17]))

def printuBP(core):
  util.printlog("!!!actions_0 0x%x" % dut.ctap.crb(238, core=core)  ) 
  util.printlog("!!!actions_1 0x%x" % dut.ctap.crb(240, core=core)  ) 
  util.printlog("!!!actions_2 0x%x" % dut.ctap.crb(242, core=core)  ) 
  util.printlog("!!!actions_3 0x%x" % dut.ctap.crb(244, core=core)  ) 
  util.printlog("!!!actions_4 0x%x" % dut.ctap.crb(246, core=core)  ) 
  util.printlog("!!!actions_5 0x%x" % dut.ctap.crb(248, core=core)  ) 
  util.printlog("!!!triggers_0 0x%x" % dut.ctap.crb(250, core=core)  ) 
  util.printlog("!!!triggers_1 0x%x" % dut.ctap.crb(252, core=core)  ) 
  util.printlog("!!!triggers_2 0x%x" % dut.ctap.crb(254, core=core)  ) 
  util.printlog("!!!triggers_3 0x%x" % dut.ctap.crb(256, core=core)  ) 
  util.printlog("!!!triggers_4 0x%x" % dut.ctap.crb(258, core=core)  ) 
  util.printlog("!!!triggers_5 0x%x" % dut.ctap.crb(260, core=core)  ) 
  util.printlog("!!!ecc_0 0x%x" % dut.ctap.crb(262, core=core)  ) 
  util.printlog("!!!ecc_1 0x%x" % dut.ctap.crb(264, core=core)  ) 
  util.printlog("!!!ecc_2 0x%x" % dut.ctap.crb(266, core=core)  ) 
  util.printlog("!!!ecc_3 0x%x" % dut.ctap.crb(268, core=core)  ) 
  util.printlog("!!!ecc_4 0x%x" % dut.ctap.crb(270, core=core)  ) 
  util.printlog("!!!ecc_5 0x%x" % dut.ctap.crb(272, core=core)  ) 
  util.printlog("!!!state_0 0x%x" % dut.ctap.crb(314, core=core)  ) 
  util.printlog("!!!state_1 0x%x" % dut.ctap.crb(316, core=core)  ) 
  util.printlog("!!!state_2 0x%x" % dut.ctap.crb(318, core=core)  ) 
  util.printlog("!!!state_3 0x%x" % dut.ctap.crb(320, core=core)  ) 
  util.printlog("!!!state_4 0x%x" % dut.ctap.crb(322, core=core)  ) 
  util.printlog("!!!state_5 0x%x" % dut.ctap.crb(324, core=core)  ) 
    
def lfsr_hunt(lfsr_start, lfsr_end, scale_start, scale_end, scale_inc, result_core=4, stop_on_fail = False, dryrun=False):
    from tabulate import tabulate
    l_index=0
    s_index=0
    rows = lfsr_end-lfsr_start+1
    cols = (int((scale_end-scale_start+scale_inc)/scale_inc))
    #print(f"{rows} {cols}")
    pfarray=[["-" for i in range(cols)] for j in range(rows)]
    for lfsr in range (lfsr_start, lfsr_end+1):
        s_index=0
        #print(tabulate(pfarray, tablefmt="grid"))
        sbts.general.vvar_override_lfsr=lfsr
        for scale in range (scale_start, scale_end +scale_inc, scale_inc):
            #print(f"{l_index} {s_index}")
            sbts.general.vvar_num=1
            sbts.general.vvar_val=scale
            if dryrun:
                drresult=0xACED
            else:
                result=runtest(result_core)
                print (f"RESULT = {result[0]}")
                drresult = dut.ctap.crb64(0x6dc,core = result_core, thread = 0)
            if ( (stop_on_fail==True) and (drresult !=ACED) ):
                break
            #result= f"{s_index} {l_index} 0x%8.8x" % drresult
            result= f"0x%8.8x" % drresult
            #pfarray[v_index][r_index]=drresult
            #print(f"{v_index} {r_index} = {result}")
            pfarray[l_index][s_index]=result
            s_index+=1
        l_index+=1
    print(tabulate(pfarray, tablefmt="grid"))

    
def runtime_hunt(ratio_start, ratio_end, ratio_inc, scale_start, scale_end, scale_inc, result_core=26, stop_on_fail = False, dryrun=False):
    from tabulate import tabulate
    l_index=0
    s_index=0
    rows = ratio_end-ratio_start+1
    cols = (int((scale_end-scale_start+scale_inc)/scale_inc))
    footer = ["ratio/scale"]
    pfarray=[["-" for i in range(cols)] for j in range(rows)]
    for ratio in range (ratio_start, ratio_end+ratio_inc, ratio_inc):
        s_index=1
        #print(tabulate(pfarray, tablefmt="grid"))
        set_core_ratio(ratio)
        for scale in range (scale_start, scale_end +scale_inc, scale_inc):
            footer.append(scale)
            sbts.general.vvar_num=1
            sbts.general.vvar_val=scale
            if dryrun:
                drresult=0xACED
            else:
                result=runtest(result_core)
                print (f"RESULT = {result[0]}")
                drresult = dut.ctap.crb64(0x6dc,core = result_core, thread = 0)
            if ( (stop_on_fail==True) and (drresult !=ACED) ):
                break
            #result= f"{s_index} {l_index} 0x%8.8x" % drresult
            result= f"0x%8.8x" % drresult
            #pfarray[v_index][r_index]=drresult
            #print(f"{v_index} {r_index} = {result}")
            pfarray[l_index][s_index]=result
            s_index+=1
        l_index+=1
    print(tabulate(pfarray, tablefmt="grid"))

def doNothing(i):
    print(f"DN{i}")

def setScale(scale):
    sbts.general.vvar_num=1
    sbts.general.vvar_scale=scale
    
def setDCF(dcf_ratio):
    sbts.general.dcf=True
    sbts.general.dcf_ratio=dcf_ratio

def setCoreMV(mv):
    voltage = mv/1000
    sbts.vr.setv['CDIE_CORE'] = voltage

def vr_shmoo(mv_start, mv_end, mv_inc, r_start, r_end, r_inc, result_core=21, dryrun=False):
    su.shmoo("mV", mv_sart,mv_end, mv_inc ,"setCoreMV", "ratio", r_start, r_end, r_inc,"set_core_ratio")

#set_core_ratio(ratio)    
#su.shmoo("SCALE", 0x1000,0x2000,0x1000,"setScale", "DCF", 1,2,1,"setDCF")
#su.shmoo("RATIO", 32,38,4 ,"set_core_ratio", "MV", 800,900,50,"setCoreMV", result_core=18)
def shmoo(x_name, x_start, x_end, x_inc, x_cmd_string, y_name, y_start, y_end, y_inc, y_cmd_string, result_core=26, stop_on_fail = False, dryrun=False):
    from tabulate import tabulate

    colsX = (int((x_end-x_start+x_inc)/x_inc)) +1 
    rows = (int((y_end-y_start+y_inc)/y_inc)) +1
    y_index=rows-2
    pfarray=[["-" for i in range(colsX)] for j in range(rows)]
    pfarray[rows-1][0]=f"{x_name}/{y_name}"
    #print(tabulate(pfarray, tablefmt="grid"))
    #for x in range (x_start, x_end+x_inc, x_inc):
    for y in range (y_start, y_end+y_inc, y_inc):
        x_index=1
        pfarray[y_index][0]=f"{y}"
        eval(f"{y_cmd_string}({y})")
        #print(tabulate(pfarray, tablefmt="grid"))
        #set_core_ratio(ratio)
        for x in range (x_start, x_end+x_inc, x_inc):
            pfarray[rows-1][x_index]=f"0x%x" %x
            eval(f"{x_cmd_string}({y})")
            #footer.append(scale)
            #sbts.general.vvar_num=1
            #sbts.general.vvar_val=scale
            if dryrun:
                drresult=0xACED
            else:
                result=runtest(result_core)
                print (f"RESULT = {result[0]}")
                drresult = dut.ctap.crb64(0x6dc,core = result_core, thread = 0)
            if ( (stop_on_fail==True) and (drresult !=ACED) ):
                break
            result= f"0x%8.8x" % drresult
            #pfarray[v_index][r_index]=drresult
            #print(f"{v_index} {r_index} = {result}")
            #pfarray[x_index][y_index]=result
            #print(f"{x_index}_{y_index}")
            #print(tabulate(pfarray, tablefmt="grid"))
            #pfarray[y_index][x_index]=f"X{x_index}_{x}:Y{y_index}_{y}"
            pfarray[y_index][x_index]=result
            #pfarray[y_index][x_index]=f"X_{x}:Y_{y}"
            x_index+=1
        y_index-=1
    print(tabulate(pfarray, tablefmt="grid"))
    


    
def runtest(result_core=None, vecx=None, core_ratio=None, core_voltage=None, cores_list=[], fullDRDump=False, dontRetry=False ):
    result = None
    done = False
    retry=5
    timerReset()
    if (len(cores_list) > 0):
        print("enabling cores")
        enableCores(cores_list)
    if (core_ratio != None):
        set_core_ratio(core_ratio)
    if (core_voltage != None):
        set_core_voltage(core_voltage)
    if (vecx!=None):
        print ("loading %s" % vecx)
        dut.load_test(vecx)
        print ("Done loading %s" % vecx)
        print ("TESTNAME = %s" % dut.testname)
    #result_core = ffc(general.coreOnVal)
    while ((done == False) and (retry > 0)):
        result = dut.run_test()
        if (result[0] != 0):
            first_thread_result = dut.ctap.crb64(0x6dc,core = result_core, thread = 0)
            if ((first_thread_result == 0) and (dontRetry == False)):
                util.printcol("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!","RED")
                util.printcol("!!!CORE %d DR0==0. TEST DIDN'T START --> RETRYING !!!" % result_core,"RED")
                util.printcol("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!","RED")
                retry-=1
            else:
                done = True
        else:
            done = True
    if (fullDRDump):
        drDumpAll(start_string = os.path.basename(vecx))
    if (result != None):
        return result

def waittime(s):
    dut.test_execution_delay = s
    #general.test_execution_delay = s

def fastpreamble():
    sbts.general.fastpreamble = True

def convert(obj):
    dut.dfx.asmobj2vec(obj)

    

def iosf_read(address, core=0, bits64=False):
    #ctap_cr_ucode_iosf_control (0x5a3)
    #0x00000000 : width (00:00) (rw) -- Message data width:  0 - 32 bit 1 - 64 bit
    #0x00000000 : dest_portid (08:01) (rw) -- Destination Port ID for the IOSF message
    #0x0000102c : address (24:09) (rw) -- Address for the IOSF message
    #0x00000000 : opcode (26:25) (rw) -- Opcode encoding: 00 - CR Read  01 - Posted CR Write  10 - non-posted CR Write
    #0x00000001 : internal (28:28) (rw) -- 1 - ignoring Dest PortID and issuing this to Core internal PMSB/GPSB PMA range...
    #0x00000001 : iosf_type (29:29) (rw) -- 0 - GPSB, 1 - PMSB
    #0x00000001 : trusted (30:30) (rw) -- 1 - trusted: use trusted ucode SAI 0 - untrusted: use untrusted ucode SAI
    #0x00000000 : runbusy (31:31) (ro_v) -- Set by Ucode upone write. Bit is reset by HW when Data/completion done
    control = 0xf0000000 | ( (address & 0x7fff )<< 9) |  ( 1<<28 ) | (1<<29) | (1<<30) 
    if bits64: control |=1
    print(f"{core} crb:0x5a3 = 0x%x" % control)
    #itp.threads[itp_thread].crb(0x5a3,control)
    print(f"data = dut.ctap.crb64(0x5a3,core = {core}, data=0x%x)" % control)
    dut.ctap.crb64(0x5a3,core = core, data=control)

    if bits64:
        #print(f"itp.threads[{itp_thread}].crb64(0x630)")
        print(f"data = dut.ctap.crb64(0x630,core = {core})")
        data = dut.ctap.crb64(0x630,core = core)
    else:
        #print(f"itp.threads[{itp_thread}].crb(0x630)")
        print(f"data = dut.ctap.crb(0x630,core = {core})")
        data =  dut.ctap.crb(0x630,core = core)
    print("0x%x" % data)
    
#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
# items below this line need to be updated

    
def iosf_write(address, itp_thread, data):
    #ctap_cr_ucode_iosf_control (0x5a3)
    #0x00000000 : width (00:00) (rw) -- Message data width:  0 - 32 bit 1 - 64 bit
    #0x00000000 : dest_portid (08:01) (rw) -- Destination Port ID for the IOSF message
    #0x0000102c : address (24:09) (rw) -- Address for the IOSF message
    #0x00000000 : opcode (26:25) (rw) -- Opcode encoding: 00 - CR Read  01 - Posted CR Write  10 - non-posted CR Write
    #0x00000001 : internal (28:28) (rw) -- 1 - ignoring Dest PortID and issuing this to Core internal PMSB/GPSB PMA range...
    #0x00000001 : iosf_type (29:29) (rw) -- 0 - GPSB, 1 - PMSB
    #0x00000001 : trusted (30:30) (rw) -- 1 - trusted: use trusted ucode SAI 0 - untrusted: use untrusted ucode SAI
    #0x00000000 : runbusy (31:31) (ro_v) -- Set by Ucode upone write. Bit is reset by HW when Data/completion done
    control = 0xf0000000 | ( (address & 0x7fff )<< 9) |  ( 1<<28 ) | (1<<29) | (1<<30) | (1<<25)
    print(f"itp.threads[{itp_thread}].crb(0x5a3,0x%x)" % control)
    itp.threads[itp_thread].crb(0x630, data)
    itp.threads[itp_thread].crb(0x5a3,control)
    #data = itp.threads[itp_thread].crb(0x630)
    #print("0x%x" % data)
    #ctap_cr_ucode_iosf_data (0x630)0xf0205800

def rerun(t=3):
    dut.shmoo_rerun = t

def switchITP():
    if (rpd.cv.tapmaster.lower() == 'itp'):
        print ("tapmaster switching to fpga")
        rpd.cv.tapmaster = 'fpga'
    else:
        print ("tapmaster switching to itp")
        rpd.cv.tapmaster = 'itp'
    rpd.forcereconfig()

def enableCores(list):
    sbts.dut.vp = list


def run_dir(path, num_runs_per_pattern = 1, stop_on_fail = False, logfile= None, csv=False, fullDRDump=True, match=None, continueonseed=None):
    if (logfile ==None):
        logfile = path + r"\%s_sbts_utils_batch.log" % timeStamped(ws.gethostname())
    print("LOGFILE = %s" %logfile)
    skip_execution = True if (continueonseed != None) else False
    f = open (logfile, 'w')
    pass_count = 0
    pattern_count = 0
    fail_list = []
    dprint(drDumpHeader(csv),f, print_to_file = (csv==False));
    for vecx in (os.listdir(path)):
        if (skip_execution and (continueonseed in vecx)):
            skip_execution = False
        if (vecx.endswith(".vecx") and (skip_execution == False) and ( (match == None) or (match in vecx) )):
          for n in range(0, num_runs_per_pattern):
              pattern_count +=1
              fullname = os.path.join(path, vecx)
              s = " "
              result = runtest(fullname, fullDRDump = False)
              if (fullDRDump == False):
                  dprint (vecx +": " + s.join(result[1]), f)
              if (result[0] == 0):
                  if (fullDRDump): dprint (drDumpAll(bsp_only=True, printit=False, csv=csv, include_header=False), f)
                  pass_count +=1
              else:
                  dprint (drDumpAll(bsp_only=False, printit=False, csv=csv, include_header=False), f)
                  fail_list.append(fullname)
                  if(stop_on_fail):
                      dprint ("!!!!!!!!!!!!!!!!!!!!!!!!!!", f, "RED")
                      dprint ("!!!! STOPPING ON FAIL !!!!", f, "RED")
                      dprint ("!!!!!!!!!!!!!!!!!!!!!!!!!!", f, "RED")
                      break
          else:
              continue
          break
    if ((len(fail_list) > 0) and (csv ==False)):
        dprint ("### FAIL LIST ####", f)
        dprint ("{",f)
        for test in (fail_list):
            dprint (test,f)
        dprint ("}", f)
    dprint ("Summary of batch_test :", f, print_to_file = (csv==False))
    dprint("  total number of patterns   : %d" % pattern_count, f , print_to_file = (csv==False))
    dprint("  number of passing patterns : %d" % pass_count,f, print_to_file = (csv==False))
    dprint("  number of failing patterns : %d" % (len(fail_list)),f, print_to_file = (csv==False))
    dprint("  number of invalid patterns : TBD",f, print_to_file = (csv==False))
    f.close()

def dprint(text, filehandle, col = "GREEN", print_to_file=True):
    util.printcol(text, col)
    if (print_to_file): filehandle.write(text +"\n")

def runTilFail(vecx=None, cores_list=[], core_ratio=-1, maxcount=50):
    result=True
    if (len(cores_list) > 0):
      enableCores(cores_list)
    if (core_ratio != -1):
        general.coreRatio = core_ratio
    first_core = sbts.general.vp[0] / 2 # numThreads
    pass_count = 0
    bad_count = 0
    run_count = 0
    for n in range(0,maxcount):
        stdout_ = sys.stdout #Keep track of the previous value.
        stderr_ = sys.stderr 
        stream = cStringIO.StringIO()
        streamERR = cStringIO.StringIO()
        sys.stdout = stream
        sys.stderr = streamERR
        if (vecx==None):
            dut.run_test()
        else:
            dut.load_and_run(vecx)
        run_count += 1
        sys.stdout = stdout_ # restore the previous stdout.
        sys.stderr = stderr_ # restore the previous stderr.
        output = stream.getvalue()
        first_thread_result = dut.ctap.crb64(0x6dc,core = first_core, thread = 0)
        print ("FIRST THREAD RESULT == %x" % first_thread_result)
        if "TEST PASS ACED !!!" in output:
            pass_count +=1
            util.printcol("%s PASSED %d TIMES out of %d runs ( %d are invalid ).  Will exit after %d runs." % (dut.testname, run_count, pass_count, bad_count, maxcount), "GREEN")
        elif ( first_thread_result == 0):
            # print output
            bad_count +=1
            util.printcol( "!!!! %s RESULT NOT VALID as test didn't start: DR0 == 0" % (dut.testname), "RED")
        else:
            print ("!!!! %s FAILED!!!" % dut.testname)
            print ("!!!! %s PASSED %d TIMES" % (dut.testname, pass_count))
            print (output)
            return False
    #print output
    util.printcol("----------------------------------", "GREEN")
    util.printcol("PASSED   : %d TIMES out of %d runs" % (dut.testname, pass_count, run_count), "GREEN")
    #util.printcol("NOT VALID: %d TIMES out of %d runs" % (dut.testname, pass_count, bad_count), "YELLOW")
    util.printcol("----------------------------------", "GREEN")
    return True
    
def vvar_override(vvar, val):
    reinit()
    sbts.general.vvar_num=vvar     
    sbts.general.vvar_val=val 

def run_time_cpu_cycles(cpu_cycles, VVAR0=2000000):
    # TSC = (VVAR0 * VVAR1)/0x1000
    sec_scale = (cpu_cycles * 0x1000)/VVAR0
    vvar_override(1, int(sec_scale))
    print("set scale is:",sec_scale)
    print ("CPU CYCLES = %d. Setting VVAR 1 = %d" % (cpu_cycles, sec_scale))

def run_time_secs(seconds, VVAR0=2000000, ratio = None):
    reinit() 
    # TSC = (VVAR0 * VVAR1)/0x1000
    if (ratio == None ):
        ratio = general.coreRatio

    TSC = ratio * 100 * 1000000 * seconds
    sec_scale = (TSC*0x1000)/VVAR0
    print ("TSC = %x. Setting VVAR 1 = 0x%x" % (TSC, sec_scale))
    vvar_override(1, sec_scale)
    waittime(seconds + 1)
    print ("dut.test_execution_delay == %d" % dut.test_execution_delay)

def set_llc_readreturn(val =  True):
    general.llc_readreturn=val

def set_ht_enable(val = True):
    general.ht_enable=val

def reinit():
    dut = __main__.dut  # will be assign to core/gt instantiated class
    rpd = __main__.rpd


def timeStamped(fname, fmt='%Y-%m-%d-%H-%M-%S_{fname}'):
    return datetime.datetime.now().strftime(fmt).format(fname=fname)

def ffs(x):
    """Returns the index, counting from 0, of the
    least significant set bit in `x`.
    """
    return (x&-x).bit_length()-1


def ffc(x):
    """Returns the index, counting from 0, of the
    least significant cleared bit in `x`.
    """
    return ffs(~x)
