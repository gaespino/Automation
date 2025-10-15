import csv
import datetime
import time
import numpy as np
from collections import OrderedDict 
import os
import ipccli
import namednodes
import tempfile, shutil
sv = namednodes.sv #shortcut
sv.initialize()
ipc = ipccli.baseaccess()
itp = ipc
import subprocess
from svtools.logging import colorapi as _colorapi
import warnings
PSExe=r"C:\SVShare\SetupExecutables\PowerSplitter\PowerSplitterCL.exe"
powerOnCmd = r"C:\SVShare\SetupExecutables\PowerSplitter\PowerSplitterCL portpower 0 true"
powerOffCmd = r"C:\SVShare\SetupExecutables\PowerSplitter\PowerSplitterCL portpower 0 false"
warnings.filterwarnings('ignore',category=FutureWarning, module='numpy')
import users.THR.PythonScripts.thr.GNRFuseOverride as gfo
import users.THR.PythonScripts.thr.GNRCoreDebugUtils as gcd
verbose=False

print ("Rev 1.2")

# @check_execution_time
def run_test(obj,compute,core):
    
    if (parseObj(obj,start_way=0, pada = 16, padb = 1) == 'FAIL'): return

    # ipc.halt()
    # cachesetup_mtl(core)
    # ipc.go()
    
    resetarray(compute,core)
    with ipc.device_locker():
        load_RWC_MLC(os.path.splitext(obj)[0]+'.img',compute,core)
        
    tapconfig(compute,core,cr=0,sbft=1)

    _colorapi.setFgColor("iyellow") 
    print ("\n\n--------Triggering resettarget--------")
    _colorapi.resetColor()     
       
    ipc.resettarget()
    # read_dr()    

def get_to_good_state():
    ipc.cv.resetbreak=0
    ipc.cv.resetbreak=1
    try:
        itp.halt()
        itp.threads[0].wbinvd()
        itp.cv.resetbreak=1
        #itp.resettarget()
    except:
        if os.path.isfile(PSExe):
            print("powering off system")
            os.system(powerOffCmd)
            time.sleep(10)
            print("powering on system")
            os.system(powerOnCmd)
        else:
            wait_result=False
            print("Please power off system, wait 10 seconds, then turn on. hit enter when done power cycling") 
            time.sleep(3)
            print("Hit enter when done power cycling") 
            input() 
            print("Enter hit.. waiting 60 seconds") 
            time.sleep(60)
            while (wait_result==False):
                wait_result=itp.wait(30)
   
    wait_result=False
    itp.resettarget() 
    wait_result=itp.wait(60)
    if (wait_result==False):
        print ("Could not get to reset break. Please retry ")
    return

def run(obj, cores = [0], license=None, ratio=None, voltage = None, vvar_num=None, vvar_val=None,  skip_reset=False, force_parse=False, wait=1):
    ipc.cv.manualscans=False
    get_to_good_state()

    if isinstance(cores,int):cores = [cores] # put core into array if needed.  
    img = os.path.splitext(obj)[0]+'.img'
    if force_parse or (os.path.exists(img) == False):
        if (parseObj(obj,start_way=0, pada = 16, padb = 1) == 'FAIL'): return
    else:
        print(f"Found {img} --> using this instead of a fresh OBJ parse")
    itp.unlock()
    for core in cores:
        compute = core_to_compute(core)
        if compute != None:
            print (f"setting up COMPUTE={compute}, CORE= {core}")
            cr_cachesetup(compute, core)
            print (f"resetarray COMPUTE={compute}, CORE= {core}")
            resetarray(compute,core)
            with ipc.device_locker():
                print (f"loading {img} COMPUTE={compute}, CORE= {core}")
                #load_RWC_MLC(os.path.splitext(obj)[0]+'.img',compute,core)
                load_RWC_MLC(img,compute,core)
                tapconfig(compute,core,cr=0,sbft=1)

    if (skip_reset == False):
        _colorapi.setFgColor("iyellow") 
        print ("\n\n--------Triggering resettarget--------")
        _colorapi.resetColor()     
        reset_with_license_ratio_voltage(license, ratio, voltage)
        # cant do VVARS until breakpoint resets are used.
        if vvar_num!=None:
             print("VVAR overrides are not working yet.  Please update vvars in ASM and recompile" )
        #    dragon_vvar_override(compute, core, vvar_num, vvar_val)
        #    cpu_tap=eval(f"sv.socket0.compute{compute}.taps.scf_gnr_maxi_coretile_phy{core}_xi_core_rwc_core_ip_tap")
        #    ipc.cv.manualscans = True
        #    cpu_tap.core_tapconfig.cfg_config_restart = 0
        #    ipc.cv.manualscans = False
    
    time.sleep(wait)
    for core in cores:
        read_dr_h(core)
    itp.cv.resetbreak=0
    return


def run_in_loop(test, cores=[0], license=None, ratio=None, voltage=None, vvar_num=None, vvar_val=None, skip_reset=False, force_parse=False, wait_time_seconds=1, force_config=False, loop=1):
    ipc.cv.manualscans = False
    if isinstance(cores, int): cores = [cores]  # put single core input into array.
    if islocked(): itp.unlock()
    
    for _ in range(loop):  # Loop to execute the function multiple times
        if license is not None or ratio is not None or voltage is not None:
            compute = core_to_compute(cores[0])
            ratioCheck = (ratio == gcd.read_current_core_ratio(cores[0], compute))
            voltageCheck = (voltage == (round(gcd.read_current_core_voltage(cores[0], compute), 2)))
            if ratioCheck and voltageCheck:
                print("Voltage and Ratio seem to be set already. Skipping override. If not, please use force_config=True option")
            else:
                get_to_good_state()
                fuse_string = reset_with_license_ratio_voltage(license, ratio, voltage)
                time.sleep(20)
                retry = 2
                if islocked and retry > 0:
                    print("!!!! System is locked! Setting license/ratio did not work. Power cycle likely occurred during ipc.resettarget. Can not set license/voltage/ratio!!!")
                    itp.unlock()
                    print("!!! RETRYING")
                    fuse_string = reset_with_license_ratio_voltage(license, ratio, voltage)
                    retry -= 1

                if islocked and retry == 0:
                    print("!!! Can not unlock. Exiting")
                    return

        if test.endswith(".img"):
            img = test
        elif test.endswith(".obj"):
            img = os.path.splitext(test)[0] + '.img'
            if force_parse or (os.path.exists(img) == False):
                if parseObj(test, start_way=0, pada=16, padb=1) == 'FAIL': return
            else:
                print(f"Found {img} --> using this instead of a fresh OBJ parse")
        else:
            print("Input was not OBJ or IMG file. Exiting")
            return

        for core in cores:
            compute = core_to_compute(core)
            cpu = eval(f"sv.socket0.compute{compute}.cpu.core{core}")

            # Sometimes the run does not start on the first try. Need to figure this out someday.
            retry_count = 2
            dr0_t0 = 0
            while retry_count > 0 and dr0_t0 == 0:
                setupUBP(compute, core)
                cr_cachesetup(compute, core)
                allocator_stall_thread(compute, core)
                cpu.ml6_cr_cache_reset = 9
                print("loading image...")
                load_RWC_MLC(img, compute, core)
                print("done loading image")
                assert_reset(compute, core)
                allocator_stall_config_reset(compute, core)
                allocator_stall_config_reset(compute, core)
                tester_tapconfig(compute, core)
                deassert_reset(compute, core)
                so_rst_pulse(compute, core)
                allocator_stall_config_reset(compute, core)
                allocator_stall_config_reset(compute, core)
                assert_reset(compute, core)
                allocator_stall_config_reset(compute, core)
                allocator_stall_config_reset(compute, core)
                tester_tapconfig(compute, core)
   
                deassert_reset(compute, core)
                if vvar_num is not None and vvar_val is not None: dragon_vvar_override(compute, core, vvar_num, vvar_val)

                allocator_stall_config_reset(compute, core)
                time.sleep(wait_time_seconds)
                dr0_t0 = cpu.thread0.ifu_cr_dr0
                if dr0_t0 == 0:
                    print(f"Run did not start. Retries = {retry_count}")
                retry_count -= 1
            read_dr_h(core=core, init=0)




def run_sbft_reset(test, cores = [0], license=None, ratio=None, voltage = None, vvar_num=None, vvar_val=None,  skip_reset=False, force_parse=False, wait_time_seconds=1, force_config=False):
    ipc.cv.manualscans=False
    if isinstance(cores,int):cores = [cores] # put single core input into array.
    if (islocked()): itp.unlock()
    if license !=None or ratio!=None or voltage!=None:
        compute = core_to_compute(cores[0])
        ratioCheck = (ratio == gcd.read_current_core_ratio(cores[0], compute))
        voltageCheck = (voltage == (round(gcd.read_current_core_voltage(cores[0], compute),2)))
        if ratioCheck and voltageCheck:
             print ("Voltage and Ratio seem to be set already.  Skipping override.  If not, please use force_config=True option")
        else:
            get_to_good_state()
            fuse_string=reset_with_license_ratio_voltage(license, ratio, voltage)
            time.sleep(20)
            retry=2
            if (islocked and retry>0):
                print("!!!! System is locked!  Setting license/ratio did not work.  Power cycle likely occurred during ipc.resettarget. Can not set license/voltage/ratio!!!")
                itp.unlock()
                print ("!!! RETRYING")
                fuse_string=reset_with_license_ratio_voltage(license, ratio, voltage)
                retry-=1

            if (islocked and retry == 0):
                print ("!!! Can not unlock. Exiting")
                return

    if test.endswith(".img"): 
        img = test
    elif test.endswith(".obj"):
        img = os.path.splitext(test)[0]+'.img'
        if force_parse or (os.path.exists(img) == False):
            if (parseObj(test,start_way=0, pada = 16, padb = 1) == 'FAIL'): return
        else:
            print(f"Found {img} --> using this instead of a fresh OBJ parse")
    else: 
        print ("Input was not OBJ or IMG file. Exiting")
        return
    for core in cores:
        compute = core_to_compute(core)
        cpu=eval(f"sv.socket0.compute{compute}.cpu.core{core}")

        # Sometimes the run does not start on the first try. Need to figure this out someday.
        retry_count=2
        dr0_t0 = 0
        while ( retry_count >0 and dr0_t0 == 0):
            setupUBP(compute,core)
            cr_cachesetup(compute,core)
            allocator_stall_thread(compute,core)
            cpu.ml6_cr_cache_reset=9
            print("loading image...")
            load_RWC_MLC(img, compute,core)
            print("done loading image")
            assert_reset(compute,core)
            allocator_stall_config_reset(compute,core)
            allocator_stall_config_reset(compute,core)
            tester_tapconfig(compute,core)
            deassert_reset(compute,core)
            so_rst_pulse(compute,core)
            allocator_stall_config_reset(compute,core)
            allocator_stall_config_reset(compute,core)
            assert_reset(compute,core)
            allocator_stall_config_reset(compute,core)
            allocator_stall_config_reset(compute,core)
            tester_tapconfig(compute,core)
            deassert_reset(compute,core)
            if vvar_num != None and vvar_val !=None: dragon_vvar_override(compute,core, vvar_num, vvar_val)
            # TODO  ADD S2T regs.  
            allocator_stall_config_reset(compute,core)
            time.sleep(wait_time_seconds)
            dr0_t0 = cpu.thread0.ifu_cr_dr0
            if dr0_t0 == 0:
                print ( f"Run did not start. Retries = {retry_count}")
            retry_count-=1
        read_dr_h(core=core, init=0)



def runDir(directory, cores=[0], license=None, ratio=None, voltage=None, vvar_num=None, vvar_val=None, skip_reset=False, force_parse=False, wait_time_seconds=1, force_config=False):
    ipc.cv.manualscans = False
    if isinstance(cores, int):
        cores = [cores]  # put single core input into array.
    if islocked():
        itp.unlock()
    if license is not None or ratio is not None or voltage is not None:
        compute = core_to_compute(cores[0])
        ratioCheck = (ratio == gcd.read_current_core_ratio(cores[0], compute))
        voltageCheck = (voltage == round(gcd.read_current_core_voltage(cores[0], compute), 2))
        if ratioCheck and voltageCheck:
            print("Voltage and Ratio seem to be set already. Skipping override. If not, please use force_config=True option")
        else:
            get_to_good_state()
            fuse_string = reset_with_license_ratio_voltage(license, ratio, voltage)
            time.sleep(20)
            retry = 2
            while islocked() and retry > 0:
                print("!!!! System is locked! Setting license/ratio did not work. Power cycle likely occurred during ipc.resettarget. Can not set license/voltage/ratio!!!")
                itp.unlock()
                print("!!! RETRYING")
                fuse_string = reset_with_license_ratio_voltage(license, ratio, voltage)
                retry -= 1

            if islocked() and retry == 0:
                print("!!! Can not unlock. Exiting")
                return

    # Iterar sobre todos los archivos en el directorio
    for testname in os.listdir(directory):
        if testname.endswith('.obj'):
            test = os.path.join(directory, testname)
            img = os.path.splitext(test)[0] + '.img'
            if force_parse or not os.path.exists(img):
                if parseObj(test, start_way=0, pada=16, padb=1) == 'FAIL':
                    return
            else:
                print(f"Found {img} --> using this instead of a fresh OBJ parse")
        else:
            print("Input was not OBJ or IMG file. Exiting")
            continue  # Cambiado de return a continue para seguir iterando

        for core in cores:
            compute = core_to_compute(core)
            cpu = eval(f"sv.socket0.compute{compute}.cpu.core{core}")

            # Sometimes the run does not start on the first try. Need to figure this out someday.
            retry_count = 2
            dr0_t0 = 0
            while retry_count > 0 and dr0_t0 == 0:
                setupUBP(compute, core)
                cr_cachesetup(compute, core)
                allocator_stall_thread(compute, core)
                cpu.ml6_cr_cache_reset = 9
                print("loading image...")
                load_RWC_MLC(img, compute, core)
                print("done loading image")
                assert_reset(compute, core)
                allocator_stall_config_reset(compute, core)
                allocator_stall_config_reset(compute, core)
                tester_tapconfig(compute, core)
                deassert_reset(compute, core)
                so_rst_pulse(compute, core)
                allocator_stall_config_reset(compute, core)
                allocator_stall_config_reset(compute, core)
                assert_reset(compute, core)
                allocator_stall_config_reset(compute, core)
                allocator_stall_config_reset(compute, core)
                tester_tapconfig(compute, core)
                deassert_reset(compute, core)
                if vvar_num is not None and vvar_val is not None:
                    dragon_vvar_override(compute, core, vvar_num, vvar_val)
                # TODO  ADD S2T regs.
                allocator_stall_config_reset(compute, core)
                time.sleep(wait_time_seconds)
                dr0_t0 = cpu.thread0.ifu_cr_dr0
                if dr0_t0 == 0:
                    print(f"Run did not start. Retries = {retry_count}")
                retry_count -= 1
            read_dr_h(core=core, init=0)




def islocked():
    ret=None
    cpu=eval(f"sv.socket0.computes[0].cpu.cores[0]")
    save_dr0_t0 = cpu.thread0.ifu_cr_dr0
    cpu.thread0.ifu_cr_dr0=0x1234
    if cpu.thread0.ifu_cr_dr0==0x1234:
        ret=False
    else:
        ret=True
    cpu.thread0.ifu_cr_dr0=save_dr0_t0
    return ret

def check_execution_time(func):
    def run(*args, **kwargs):
        t0 = datetime.datetime.now()
        ret = func(*args, **kwargs)
        _colorapi.setFgColor("icyan")
        print ("  >> Done %15s " %func.__name__,end="")
        print (datetime.datetime.now() - t0)
        _colorapi.resetColor()
        return ret
    return run

@check_execution_time    
def load_RWC_MLC(img,compute,core):
    type_ =[]
    mesi_ =[]
    address_ =[]
    tag_ =[]
    set_ =[]
    way_ =[]
    data_ =[]
    
    with open(img,"r") as f1:
        a= csv.DictReader(f1)
        for row in a:
            type_.append(row['TYPE'].strip())
            mesi_.append(row['MESI'].strip()) 
            address_.append(row['ADDRESS'].strip()) 
            tag_.append(row['TAG'].strip())
            set_.append(int(row['SET'].strip())) 
            way_.append(int(row['WAY'].strip())) 
            data_.append(row['DATA'].strip()) 
    

    global cpu
    cpu=eval(f"sv.socket0.compute{compute}.cpu.core{core}")
    
    # _colorapi.setFgColor("iyellow")
    # print(f"     loading {os.path.splitext(img)[0]+'.obj'} into RWC{core} MLC...")
    # _colorapi.resetColor()
    
    ipc.cv.manualscans=True
    
    ##data##
    cnt=0
    temp=0
    for i in range(len(data_)):
        if cnt==0 or temp!=data_[i]:
            data(data_[i],core)
            cnt=1
            temp=data_[i]
        else:
            pass
        sdat_write(set_[i],way_[i],"d",core)
        pdat_write(set_[i],way_[i],"d",core)

    ##tag##
    cnt=0
    temp=0    
    for i in range(len(tag_)):
        if cnt==0 or temp!=tag_[i]:
            tag(tag_[i],core)
            cnt=1
            temp=tag_[i]
        else:
            pass
        sdat_write(set_[i],way_[i],"t",core)
        pdat_write(set_[i],way_[i],"t",core)
    
    ##state##
    cnt=0
    temp=0    
    for i in range(len(mesi_)):
        if cnt==0 or temp!=mesi_[i]:
            mesi(mesi_[i],core)
            cnt=1
            temp=mesi_[i]
        else:
            pass
        sdat_write(set_[i],way_[i],"s",core)
        pdat_write(set_[i],way_[i],"s",core) 
        
    cpu.ml2_cr_sdat = 0x0
    cpu.ml2_cr_pdat = 0x0  
    ipc.cv.manualscans=False
    

WRTAG   =  11
WRSTATE = 3
WRDATA  = 10
def sdat_write(sets,ways,target,core):
    if target == "d":
        banksel = (ways & 0x3) << 2 |\
                  (sets & 1)
        s=0x10000 | (WRDATA << 5) | banksel
        cpu.ml2_cr_sdat= s
    elif target == "t":
        banksel = ((sets >> 10) & 1) << 2 |\
                  (ways & 1) << 1 |\
                  (sets & 1)               
        s=0x10000 | (WRTAG << 5) | banksel
        cpu.ml2_cr_sdat= s    
    elif target == "s":
        banksel =  ((sets >> 10) & 1)  << 2 |\
                   ((sets >> 9) & 1)  << 1|\
                    sets & 1               
        s=0x10000 | (WRSTATE << 5) | banksel
        cpu.ml2_cr_sdat=s    
    return 0

def pdat_write(sets,ways,target,core):
    if target == "d":
        fastaddr = (ways >> 2) << 10 |\
                   (sets >> 1) & 0x3ff   
        p=0x800000 | fastaddr 
        cpu.ml2_cr_pdat= p    
    elif target == "t":
        fastaddr = (ways >> 1) << 9 |\
                   (sets >> 1)  & 0x1ff  
        p=0x800000 | fastaddr
        cpu.ml2_cr_pdat=p    
    elif target == "s":
        fastaddr = ways  << 8 |\
                   ( sets >> 1) & 0xff              
        p=0x8000000 | fastaddr
        cpu.ml2_cr_pdat=p   
    return 0

def data(d,core):
    # print(d)
    cpu.ml6_cr_datin = (int(d,16) ) & 0xffffffff
    cpu.ml6_cr_datin1 = (int(d,16) >> 1*32) &0xffffffff
    cpu.ml6_cr_datin2 = (int(d,16) >> 2*32) &0xffffffff
    cpu.ml6_cr_datin3 = (int(d,16) >> 3*32) &0xffffffff
    cpu.ml6_cr_datin4 = (int(d,16) >> 4*32) &0xffffffff
    cpu.ml6_cr_datin5 = (int(d,16) >> 5*32) &0xffffffff
    cpu.ml6_cr_datin6 = (int(d,16) >> 6*32) &0xffffffff
    cpu.ml6_cr_datin7 = (int(d,16) >> 7*32) &0xffffffff
    
    cpu.ml6_cr_datin11 = (int(d,16) >> 8*32) &0xffffffff
    cpu.ml6_cr_datin12 = (int(d,16) >> 9*32) &0xffffffff
    cpu.ml6_cr_datin13 = (int(d,16) >> 10*32) &0xffffffff
    cpu.ml6_cr_datin14 = (int(d,16) >> 11*32) &0xffffffff
    cpu.ml6_cr_datin15 = (int(d,16) >> 12*32) &0xffffffff
    cpu.ml6_cr_datin16 = (int(d,16) >> 13*32) &0xffffffff
    cpu.ml6_cr_datin17 = (int(d,16) >> 14*32) &0xffffffff
    cpu.ml6_cr_datin18 = (int(d,16) >> 15*32) &0xffffffff
    return 0
    
def tag(t,core):
    # print(t)
    cpu.ml2_cr_datin9 = int(t,16) & 0xffffffff
    cpu.ml2_cr_datin10 = int(t,16)>>32 & 0xffffffff
    return 0

def mesi(m,core):
    # print(m)
    cpu.ml2_cr_datin10 = int(m,16)
    return 0

def mem_write():
    string =[
    "mov rcx,0x2ff",
    "xor rdx, rdx",
    "mov rax, 0x806",
    "wrmsr",
    "xor rdx, rdx",
    "xor rax, rax",
    "mov rcx, 0x800000",
    "mov rax, 0x00000000",
    "mov rdx, 0x10000000",
    
    "mov [rdx+rax], rax",
    "add rax, 0x8",
    
    "loop $-0x0a",
    
    "jmp $",
    "jmp $",
    "jmp $"
    ]    
    
    print(string)
    
    print("setting mtrrdefault to 0x806 through asm code:")
    ipc.threads[0].asm("$",*string)
    ipc.threads[0].asm("$",10)
    

    ipc.go()
    ipc.wait(1)
    ipc.halt()

def addr_translation(phys_addr):
    sets= (phys_addr >> 6) &0x7ff
    tags= phys_addr >>17
    states= 0x2   #default, exclusive?
    print(f"physical address: {hex(phys_addr)}\nset: {sets}\ntag: {tags}\nstate: {states}")

def write_MLC(copmute,core,sets,ways,datas,states,tags):
    global cpu
    cpu=eval(f"sv.socket0.compute{compute}.cpu.core{core}") 
    #data    
    data(datas,core)
    sdat_write(sets,ways,"d",core)
    pdat_write(sets,ways,"d",core)
    #tag
    tag(tags,core)    
    sdat_write(sets,ways,"t",core)
    pdat_write(sets,ways,"t",core)
    #state
    mesi(states,core)
    sdat_write(sets,ways,"s",core)
    pdat_write(sets,ways,"s",core) 
    
def read_MLC(sets,ways,core):
    cpu=eval(f"sv.socket0.compute{compute}.cpu.core{core}") 
    WRTAG   =  11
    WRSTATE = 3
    WRDATA  = 10
    ary=[]
    
    ############################################
    dword=0
    dword_2nd=0

    for i in range (0,16):
        if i<=7:
            #sdat data
            banksel = (ways & 0x3) << 2 |\
                      (sets & 1)
            s=0x10000 | (dword << 12) | (WRDATA << 5) | banksel
            cpu.ml2_cr_sdat= s
            
            #pdat data
            fastaddr = (ways >> 2) << 10 |\
                       (sets >> 1) & 0x3ff   
            p=0xc00000 | fastaddr 
            cpu.ml2_cr_pdat= p
            
            cpu.ml2_cr_datout
            data=cpu.ml2_cr_datout
            data='0x{:08x}'.format(data)
            # print(data)
            ary.append(data)
            dword += 1
        else:
            #sdat data
            banksel = (ways & 0x3) << 2 |\
                      (sets & 1)
            s=0x10000 | (dword_2nd << 12) | (WRDATA << 5) | banksel | 0x2
            cpu.ml2_cr_sdat= s
            
            #pdat data
            fastaddr = (ways >> 2) << 10 |\
                       (sets >> 1) & 0x3ff   
            p=0xc00000 | fastaddr 
            cpu.ml2_cr_pdat=p
            
            cpu.ml2_cr_datout
            data=cpu.ml2_cr_datout
            data='0x{:08x}'.format(data)
            # print(data)
            ary.append(data)
            dword_2nd += 1
    # print(ary)
    tmp=[]
    for i in reversed(ary):
        a=hex(int(i,16))[2:].zfill(8)
        tmp.append(a)
    result='0x'+''.join(tmp)
    print(f"data for way {ways} and set {sets} is: \n{result}")
    
    ############################################
    
    #sdat tag
    banksel = ((sets >> 10) & 1) << 2 |\
              (ways & 1) << 1 |\
              (sets & 1)
    s=0x10000 | (WRTAG << 5) | banksel
    cpu.ml2_cr_sdat= s
    
    #pdat tag
    fastaddr = (ways >> 1) << 9 |\
               (sets >> 1)  & 0x1ff  
    p=0xc00000 | fastaddr
    cpu.ml2_cr_pdat=p
    cpu.ml2_cr_datout
    print(f"tag for way {ways} and set {sets} is: \n{cpu.ml2_cr_datout} ")
    
    #############################################
    
    # sdat state
    banksel =  ((sets >> 10) & 1)  << 2 |\
               ((sets >> 9) & 1)  << 1|\
                sets & 1 
    s=0x10000 | (WRSTATE << 5) | banksel
    cpu.ml2_cr_sdat=s
    
    # pdat state
    fastaddr = ways  << 8 |\
               ( sets >> 1) & 0xff    
    p=0xc00000 | fastaddr
    cpu.ml2_cr_pdat=p
    print(f"MESI for way {ways} and set {sets} is: \n{cpu.ml2_cr_datout} ")
    
    cpu.ml2_cr_sdat = 0x0
    cpu.ml2_cr_pdat = 0x0    

def dump_mtrr_reg(compute,core):
    cpu= eval(f"sv.socket0.compute{compute}.cpu.core{core}")
    
    print(f"sv.socket0.compute{compute}.cpu.core{core}.pmh_cr_mtrrdefault = {cpu.pmh_cr_mtrrdefault}")
    # print(f'sv.socket0.compute{compute}.cpu.core{core}.thread0.ucode_cr_mtrrcap = {cpu.thread0.ucode_cr_mtrrcap}')
    print(f"fixed range MTRR: sv.socket0.compute{compute}.cpu.core{core}.pmh_cr_mtrrfix64k = {cpu.pmh_cr_mtrrfix64k}")
    print(f"fixed range MTRR: sv.socket0.compute{compute}.cpu.core{core}.pmh_cr_mtrrfix16k8 = {cpu.pmh_cr_mtrrfix16k8}")
    print(f"fixed range MTRR: sv.socket0.compute{compute}.cpu.core{core}.pmh_cr_mtrrfix16ka = {cpu.pmh_cr_mtrrfix16ka}")
    print(f"fixed range MTRR: sv.socket0.compute{compute}.cpu.core{core}.pmh_cr_mtrrfix4kc0 = {cpu.pmh_cr_mtrrfix4kc0}")
    print(f"fixed range MTRR: sv.socket0.compute{compute}.cpu.core{core}.pmh_cr_mtrrfix4kc8 = {cpu.pmh_cr_mtrrfix4kc8}")
    print(f"fixed range MTRR: sv.socket0.compute{compute}.cpu.core{core}.pmh_cr_mtrrfix4kd0 = {cpu.pmh_cr_mtrrfix4kd0}")
    print(f"fixed range MTRR: sv.socket0.compute{compute}.cpu.core{core}.pmh_cr_mtrrfix4kd8 = {cpu.pmh_cr_mtrrfix4kd8}")
    print(f"fixed range MTRR: sv.socket0.compute{compute}.cpu.core{core}.pmh_cr_mtrrfix4ke0 = {cpu.pmh_cr_mtrrfix4ke0}")
    print(f"fixed range MTRR: sv.socket0.compute{compute}.cpu.core{core}.pmh_cr_mtrrfix4ke8 = {cpu.pmh_cr_mtrrfix4ke8}")
    print(f"fixed range MTRR: sv.socket0.compute{compute}.cpu.core{core}.pmh_cr_mtrrfix4kf0 = {cpu.pmh_cr_mtrrfix4kf0}")
    print(f"fixed range MTRR: sv.socket0.compute{compute}.cpu.core{core}.pmh_cr_mtrrfix4kf8 = {cpu.pmh_cr_mtrrfix4kf8}")

# def dump_mtrr_msr():

def cachesetup():
    # cr0=ipc.threads[core].state.regs.cr0    
    # ipc.threads[core].state.regs.cr0 =(cr0 & 0x9fffffff)
    # ipc.cores[0].threads[0].invd()
    # ipc.cores[0].threads[1].invd()
    
    # ipc.cores.threads.state.regs.cr0 = 0x10;     #ori=0x80010013
    #ipc.cores.threads.state.regs.cr0 = 0x80000010
    # ipc.cores.threads[0].state.regs.cr0 = 0x10;
    ipc.msr(0x2ff, 0x806)
    ipc.msr(0x277,0x0606060606060606)
    ipc.msr(0x2ff, 0x806)
    ipc.msr(0x200, 0xfee00000)
    ipc.msr(0x201, 0x7ffff00800)
    ipc.msr(0x202, 0xfed10000)
    ipc.msr(0x203, 0x7ffff00800)
    ipc.msr(0x205, 0x0)
    ipc.msr(0x207, 0x0)
    ipc.msr(0x209, 0x0)
    ipc.msr(0x20b, 0x0)
    ipc.msr(0x20d, 0x0)
    ipc.msr(0x20f, 0x0)
    ipc.msr(0x211, 0x0)
    ipc.msr(0x213, 0x0)

def cr_cachesetup(compute, core):
    svcore=eval(f"sv.socket0.compute{compute}.cpu.core{core}")
    #ipc.cores.threads.state.regs.cr0 = 0x80000010

    svcore.threads.pmh_cr_pat = 0x0606060606060606 # MSR 0x277
    svcore.pmh_cr_mtrrdefault = 0x806 # MSR 0x2FF
    svcore.pmh_cr_mtrrvarbase0 = 0x806 # MSR 0x200
    svcore.pmh_cr_mtrrvarmask0 = 0x7ffff00800 # MSR 0x201
    svcore.pmh_cr_mtrrvarbase1 = 0xfed10000  # MSR 0x202
    svcore.pmh_cr_mtrrvarmask1 = 0x7ffff00800 # MSR 0x203
    svcore.pmh_cr_mtrrvarbase2 = 0
    svcore.pmh_cr_mtrrvarmask2 = 0
    svcore.pmh_cr_mtrrvarbase2 = 0
    svcore.pmh_cr_mtrrvarmask3 = 0
    svcore.pmh_cr_mtrrvarbase2 = 0
    svcore.pmh_cr_mtrrvarmask4 = 0
    svcore.pmh_cr_mtrrvarbase2 = 0
    svcore.pmh_cr_mtrrvarmask5 = 0
    svcore.pmh_cr_mtrrvarbase2 = 0
    svcore.pmh_cr_mtrrvarmask6 = 0
    svcore.pmh_cr_mtrrvarbase2 = 0
    svcore.pmh_cr_mtrrvarmask7 = 0
    svcore.pmh_cr_mtrrvarbase2 = 0
    svcore.pmh_cr_mtrrvarmask8 = 0
    svcore.pmh_cr_mtrrvarbase2 = 0

def dragon_vvar_override(compute,core, vvar_num, vvar_val):
    cpu=eval(f"sv.socket0.compute{compute}.cpu.core{core}")
    if verbose: print(f"overriding vvars : {vvar_num} {vvar_val}")
    cpu.ml1_cr_sdat = 0x80000000 | vvar_num
    cpu.ml1_cr_compare_mask = vvar_val

def print_dragon_vvar_override(compute,core):
    cpu=eval(f"sv.socket0.compute{compute}.cpu.core{core}")
    print ("ml1_cr_sdat=0x%x ml1_cr_compare_mask=0x%x" %(cpu.ml1_cr_sdat, cpu.ml1_cr_compare_mask))

@check_execution_time
def resetarray(compute,core):
    cpu=eval(f"sv.socket0.compute{compute}.cpu.core{core}")
    #reset_array for MTL
    ipc.cv.manualscans = True
    # mlc bist
    CORE_CR_SDAT_INIT_MODE_MASK = 0x0030000
    DCU_SDAT_ARYSEL2_BIT_TEMP_MASK = 0x00000040
    DSBFE_BP_CR_SDAT_MODE_MSB_TEMP_MASK = 0x00020260
    CORE_CR_PDAT_SEQEN_VAL  = 0x02030000
    ML2_CR_PWRDN_OVRD_MLSQCGD_MASK = 0x00000040
    ML2_CR_PWRDN_OVRD_MLTAGARYSERD_MASK = 0x200
    START_BIST_COMMAND_MASK = 0x00000009
    ML1_CR_DIR_ENG_CONTROL_EN_ECC_CMP_MASK  = 0x000004000
    ML1_CR_DIR_ENG_CONTROL_TEST_ECC_PARITY_MASK = 0x10000000
    CTAP_CR_TAP_CONFIG_BIST_IN_PROGRESS_MASK    = 0x00002000
    
    
    
    cpu.ml2_cr_mcg_contain=0
    cpu.ml2_cr_pwrdn_ovrd = ML2_CR_PWRDN_OVRD_MLSQCGD_MASK | ML2_CR_PWRDN_OVRD_MLTAGARYSERD_MASK
    
    cpu.ml1_cr_dir_eng_control= START_BIST_COMMAND_MASK | ML1_CR_DIR_ENG_CONTROL_EN_ECC_CMP_MASK | ML1_CR_DIR_ENG_CONTROL_TEST_ECC_PARITY_MASK
    cpu.ctap_cr_tap_config  = CTAP_CR_TAP_CONFIG_BIST_IN_PROGRESS_MASK
    # cpu.ctap_cr_tap_config  = 0x70105de6
    
    cpu.ml2_cr_pwrdn_ovrd
    
    cpu.ctap_cr_tap_config.bist_in_progress =0
    # Initialize MLC state and LRU arrays 
    cpu.ml6_cr_cache_reset.flush_spc_cyc = 0x9;
    
    
    SDAT_DFT_ARYSEL2     = 0x00010040
    MI_CR_PDAT_WR_ADDR0  = 0x08000000
    
    
    cpu.mi_cr_sdat
    cpu.mi_cr_pdat  = MI_CR_PDAT_WR_ADDR0
    cpu.mi_cr_pdat  = MI_CR_PDAT_WR_ADDR0 | 1
    cpu.mi_cr_sdat  = 0
    
    cpu.dcu_cr_sdat     = CORE_CR_SDAT_INIT_MODE_MASK | DCU_SDAT_ARYSEL2_BIT_TEMP_MASK
    cpu.dcu_cr_pdat = CORE_CR_PDAT_SEQEN_VAL
    time.sleep(0.1)
    cpu.dcu_cr_sdat = 0
    cpu.dcu_cr_pdat = 0
    
    # Need SQDB initialization
    cpu.ml2_cr_sdat     = CORE_CR_SDAT_INIT_MODE_MASK
    cpu.ml2_cr_pdat = CORE_CR_PDAT_SEQEN_VAL
    time.sleep(0.1)
    cpu.ml2_cr_sdat = 0
    cpu.ml2_cr_pdat = 0
    
    
    cpu.mi_cr_sdat      = CORE_CR_SDAT_INIT_MODE_MASK
    cpu.mi_cr_pdat = CORE_CR_PDAT_SEQEN_VAL
    time.sleep(0.1)
    cpu.mi_cr_sdat = 0
    cpu.mi_cr_pdat = 0
    
    
    cpu.bpu1_cr_sdat    = CORE_CR_SDAT_INIT_MODE_MASK | DSBFE_BP_CR_SDAT_MODE_MSB_TEMP_MASK
    cpu.bpu1_cr_pdat = CORE_CR_PDAT_SEQEN_VAL
    time.sleep(0.1)
    cpu.bpu1_cr_sdat = 0
    cpu.bpu1_cr_pdat = 0
    
    
    CORE_CR_PDAT_XQ_VAL = 0x0000c203
    ML2_CR_SDAT_MODE_MSB_TEMP_MASK = 0x00020100
    
    SDAT_DFT_ARYSEL0_IFU_ATTR_ARYSEL_8_BIT_8 = 0x00010100
    PDAT_CMDA1_WR_IROM = 0x00800000 
    cpu.bpu1_cr_sdat    = SDAT_DFT_ARYSEL0_IFU_ATTR_ARYSEL_8_BIT_8
    cpu.bpu1_cr_pdat = PDAT_CMDA1_WR_IROM
    time.sleep(0.1)
    cpu.bpu1_cr_sdat = 0
    cpu.bpu1_cr_pdat = 0
    ipc.cv.manualscans = False

def setupUBP(compute,core):
    corepma_tap=eval(f"sv.socket0.compute{compute}.taps.scf_gnr_maxi_coretile_phy{core}_xi_core_corepma_tap")
    corepma_tap.corepma_brkptctl3.actions_deassert_core_reset=1
    corepma_tap.corepma_brkptctl3.controls_trigger_detect_edge=1
    corepma_tap.corepma_brkptctl3.controls_trigger_detect_mode=1
    corepma_tap.corepma_brkptctl3.controls_pulse_mode=1
    corepma_tap.corepma_brkptctl3.counter_value=4
    corepma_tap.corepma_brkptctl3.triggers_mbp=1
    corepma_tap.corepma_brkptctl3.actions_mbp=8
    corepma_tap.corepma_brkpten3=0
    corepma_tap.corepma_brkptctl2.actions_assert_core_reset=1
    corepma_tap.corepma_brkptctl2.controls_trigger_detect_edge=1
    corepma_tap.corepma_brkptctl2.controls_trigger_detect_mode=1
    corepma_tap.corepma_brkptctl2.controls_pulse_mode=1
    corepma_tap.corepma_brkptctl2.counter_value=4
    corepma_tap.corepma_brkptctl2.triggers_mbp=1
    corepma_tap.corepma_brkptctl2.actions_mbp=8
    corepma_tap.corepma_brkpten2=0
    cpu_tap=eval(f"sv.socket0.compute{compute}.taps.scf_gnr_maxi_coretile_phy{core}_xi_core_rwc_core_ip_tap")
    cpu_tap.core_brkptctl1=0x20004000000000080100430000018
    cpu_tap.core_brkptctl2=0x80000046000020000018
    cpu_tap.core_brkptctl3=0x18
    cpu_tap.core_brkptctl4=0x80000006000020000018
    cpu_tap.core_brkptctl5=0x18

def ubp_reset(compute,core):
    setupUBP(compute,core)
    corepma_tap=eval(f"sv.socket0.compute{compute}.taps.scf_gnr_maxi_coretile_phy{core}_xi_core_corepma_tap")
    corepma_tap.corepma_brkpten3=1
    corepma_tap.corepma_brkpten2=1
    corepma_tap.corepma_brkptctl2.controls_triggers_now=1# ASSERT_CORE_RESET
    corepma_tap.corepma_brkptstate2.show()
    corepma_tap.corepma_brkptctl3.controls_triggers_now=1# DEASSERT_CORE_RESET
    corepma_tap.corepma_brkptstate3.show()

def allocator_stall_config_reset(compute,core):
    cpu_tap=eval(f"sv.socket0.compute{compute}.taps.scf_gnr_maxi_coretile_phy{core}_xi_core_rwc_core_ip_tap")
    cpu_tap.core_brkpten2=1
    cpu_tap.core_brkptctl2.dr_controls_triggers_now=1
    #return cpu_tap.core_brkptstate2.dr_action_occurred

def allocator_stall_thread(compute,core):
    cpu_tap=eval(f"sv.socket0.compute{compute}.taps.scf_gnr_maxi_coretile_phy{core}_xi_core_rwc_core_ip_tap")
    cpu_tap.core_brkpten4=1
    cpu_tap.core_brkptctl4.dr_controls_triggers_now=1
    if verbose and  cpu_tap.core_brkptstate4.dr_action_occurred == 1 : print ("allocator_stall_thread_occurred")

def debug_counter(compute,core):
    cpu_tap=eval(f"sv.socket0.compute{compute}.taps.scf_gnr_maxi_coretile_phy{core}_xi_core_rwc_core_ip_tap")
    cpu_tap.core_debugcounter0.dr_counter_match_value=64
    cpu_tap.core_debugcounter0.dr_counting_mode=0
    cpu_tap.core_debugcounter0.dr_reset_mode=1
    cpu_tap.core_debugcounter0.dr_functional_reset_dis=0
    cpu_tap.core_debugcounter0.dr_toggle_counting_with_mbp=0
    cpu_tap.core_brkpten1=1

def so_rst_pulse(compute,core):
    cpu_tap=eval(f"sv.socket0.compute{compute}.taps.scf_gnr_maxi_coretile_phy{core}_xi_core_rwc_core_ip_tap")
    cpu_tap.core_brkpten0=1
    cpu_tap.core_brkptctl0.dr_controls_triggers_now=1
    if verbose and cpu_tap.core_brkptstate0.dr_action_occurred == 1 : print ("so_rst_pulse occurred")

def assert_reset(compute,core):
    #setupUBP(compute,core)
    corepma_tap=eval(f"sv.socket0.compute{compute}.taps.scf_gnr_maxi_coretile_phy{core}_xi_core_corepma_tap")
    corepma_tap.corepma_brkpten2=1
    corepma_tap.corepma_brkptctl2.controls_triggers_now=1# ASSERT_CORE_RESET
    #corepma_tap.corepma_brkptstate2.show()
    if verbose and corepma_tap.corepma_brkptstate2.action_occurred == 1 : print ("assert_reset occured")

def deassert_reset(compute,core):
    #setupUBP(compute,core)
    corepma_tap=eval(f"sv.socket0.compute{compute}.taps.scf_gnr_maxi_coretile_phy{core}_xi_core_corepma_tap")
    corepma_tap.corepma_brkpten3=1
    corepma_tap.corepma_brkptctl3.controls_triggers_now=1# DEASSERT_CORE_RESET
    if verbose and corepma_tap.corepma_brkptstate3.action_occurred == 1: print("deassert_reset occurred")

def working(compute,c):
    itp.unlock()
    setupUBP(compute,c)
    cr_cachesetup(compute,c)
    allocator_stall_thread(compute,c)
    cpu=eval(f"sv.socket0.compute{compute}.cpu.core{c}")
    cpu.ml6_cr_cache_reset=9
    load_RWC_MLC(r"C:\Temp\itploader\DQ02_0Demo_08100152.img", compute,c)
    # TODO SET AVX
    assert_reset(compute,c)
    allocator_stall_config_reset(compute,c)
    allocator_stall_config_reset(compute,c)
    tester_tapconfig(compute,c)
    deassert_reset(compute,c)
    so_rst_pulse(compute,c)
    allocator_stall_config_reset(compute,c)
    allocator_stall_config_reset(compute,c)
    assert_reset(compute,c)
    allocator_stall_config_reset(compute,c)
    allocator_stall_config_reset(compute,c)
    tester_tapconfig(compute,c)
    deassert_reset(compute,c)
    allocator_stall_config_reset(compute,c)
    time.sleep(1)
    read_dr(compute=compute,core=c,init=1)

def tester_tapconfig(compute,core):
    cpu_tap=eval(f"sv.socket0.compute{compute}.taps.scf_gnr_maxi_coretile_phy{core}_xi_core_rwc_core_ip_tap")
    ipc.cv.manualscans = True
    
    cpu_tap.core_tapconfig.cfg_config_restart = 1
    cpu_tap.core_tapconfig.cfg_disable_prefetchers = 1
    cpu_tap.core_tapconfig.cfg_disable_panic_mode  = 1
    cpu_tap.core_tapconfig.cfg_kill_idi    = 1
    cpu_tap.core_tapconfig.cfg_disable_power_gating    = 1
    cpu_tap.core_tapconfig.cfg_sbft_mode = 1
    cpu_tap.core_tapconfig.cfg_disable_mc_init = 1  
    cpu_tap.core_tapconfig.cfg_dis_cpuid   = 1
    cpu_tap.core_tapconfig.cfg_disable_uncore_ucode_init = 1
    cpu_tap.core_tapconfig.cfg_mlc_miss_isolation  = 1
    cpu_tap.core_tapconfig.cfg_resume_mnsclk   = 1
    cpu_tap.core_tapconfig.cfg_resume_mclk = 1
    cpu_tap.core_tapconfig.cfg_dft_mclk_en = 1
    
    
    cpu_tap.core_tapconfig2.cfg_disable_mlc_cache_init = 1
    
    #cpu_tap.core_tapconfig.cfg_drop_llc_special_cycles = 1   #0
    #cpu_tap.core_tapconfig.cfg_hash_map_coallocated_llc    = 1    #0
    #cpu_tap.core_tapconfig.cfg_stop_ucode_at_end_macro = 0
    #cpu_tap.core_tapconfig.cfg_ucode_stall_enable   = 0
    #cpu_tap.core_tapconfig.cfg_sv_reset  = 0
    ipc.cv.manualscans = False

def tapconfig(compute,core,cr,sbft):
    cpu_tap=eval(f"sv.socket0.compute{compute}.taps.scf_gnr_maxi_coretile_phy{core}_xi_core_rwc_core_ip_tap")
    ##tapconfig for MTL
    ipc.cv.manualscans = True
    
    cpu_tap.core_tapconfig.cfg_config_restart = cr
    cpu_tap.core_tapconfig.cfg_dft_mclk_en = 1
    cpu_tap.core_tapconfig2.cfg_disable_mlc_cache_init = 1
    cpu_tap.core_tapconfig.cfg_disable_panic_mode  = 1
    cpu_tap.core_tapconfig.cfg_disable_power_gating    = 1
    cpu_tap.core_tapconfig.cfg_disable_prefetchers = 1
    # cpu_tap.core_tapconfig.cfg_disable_power_downs = 1   
    
    
    cpu_tap.core_tapconfig.cfg_disable_uncore_ucode_init = 1
    
    cpu_tap.core_tapconfig.cfg_dis_cpuid   = 1
    cpu_tap.core_tapconfig.cfg_drop_llc_special_cycles = 1   #0
    cpu_tap.core_tapconfig.cfg_hash_map_coallocated_llc    = 1    #0
    
    cpu_tap.core_tapconfig.cfg_kill_idi    = 0   #1
    cpu_tap.core_tapconfig.cfg_mlc_miss_isolation  = 0   #1
    
    cpu_tap.core_tapconfig.cfg_resume_mnsclk   = 1
    cpu_tap.core_tapconfig.cfg_resume_mclk = 1
    
    cpu_tap.core_tapconfig.cfg_sbft_mode   = sbft
    
    cpu_tap.core_tapconfig.cfg_stop_ucode_at_end_macro = 0
    cpu_tap.core_tapconfig.cfg_ucode_stall_enable   = 0
    cpu_tap.core_tapconfig.cfg_sv_reset  = 0
    
    cpu_tap.core_tapconfig.cfg_disable_mc_init = 1  
    ipc.cv.manualscans = False

def read_dr_h(core,init=0):
    compute = core_to_compute(core)
    if compute != None:
        cpu=eval(f"sv.socket0.compute{compute}.cpu.core{core}")
        ipc.cv.manualscans=True
        dr0_t0 = cpu.thread0.ifu_cr_dr0
        dr0_t1 = cpu.thread1.ifu_cr_dr0
        dr1_t0 = cpu.thread0.ifu_cr_dr1
        dr1_t1 = cpu.thread1.ifu_cr_dr1
        dr2_t0 = cpu.thread0.ifu_cr_dr2
        dr2_t1 = cpu.thread1.ifu_cr_dr2
        dr3_t0 = cpu.thread0.ifu_cr_dr3
        dr3_t1 = cpu.thread1.ifu_cr_dr3
        color = "31m"
        if dr0_t0 == 0xaced: color = "32m"
        
        print ("           DR0               DR1                DR2                DR3 ")
        print ("\033[{}C{:2}:T0 0x{:016x} 0x{:016x} 0x{:016x} 0x{:016x}\033[0m".format(color,core, dr0_t0, dr1_t0, dr2_t0, dr3_t0))
        print ("\033[{}C{:2}:T1 0x{:016x} 0x{:016x} 0x{:016x} 0x{:016x}\033[0m".format(color,core, dr0_t1, dr1_t1, dr2_t1, dr3_t1))
        
        if init ==1:
            cpu.thread0.ifu_cr_dr0 = 0
            cpu.thread1.ifu_cr_dr0 = 0
            cpu.thread0.ifu_cr_dr1 = 0
            cpu.thread1.ifu_cr_dr1 = 0
        cpu.thread0.ifu_cr_dr2 = 0
        cpu.thread1.ifu_cr_dr2 = 0
        cpu.thread0.ifu_cr_dr3 = 0
        cpu.thread1.ifu_cr_dr3 = 0
        
        ipc.cv.manualscans=False

def read_dr(compute,core,init=0):
    #init=1 : to clear dr register 
    cpu=eval(f"sv.socket0.compute{compute}.cpu.core{core}")
    
    ipc.cv.manualscans=True
    print(f"""
    core{core} thread0 DR0: {cpu.thread0.ifu_cr_dr0}
    core{core} thread1 DR0: {cpu.thread1.ifu_cr_dr0}
    
    core{core} thread0 DR1: {cpu.thread0.ifu_cr_dr1}
    core{core} thread1 DR1: {cpu.thread1.ifu_cr_dr1}
    
    core{core} thread0 DR2: {cpu.thread0.ifu_cr_dr2}
    core{core} thread1 DR2: {cpu.thread1.ifu_cr_dr2}
    
    core{core} thread0 DR3: {cpu.thread0.ifu_cr_dr3}
    core{core} thread1 DR3: {cpu.thread1.ifu_cr_dr3}""")
    if init ==1:
        cpu.thread0.ifu_cr_dr0 = 0
        cpu.thread1.ifu_cr_dr0 = 0
        cpu.thread0.ifu_cr_dr1 = 0
        cpu.thread1.ifu_cr_dr1 = 0
        cpu.thread0.ifu_cr_dr2 = 0
        cpu.thread1.ifu_cr_dr2 = 0
        cpu.thread0.ifu_cr_dr3 = 0
        cpu.thread1.ifu_cr_dr3 = 0
        
    ipc.cv.manualscans=False

@check_execution_time
def parseObj(objfile, start_way=0, pada = 0, padb = 0):
    """
      parse obj file
      input = obj file path and name
   
    """
    # print ("  >> pad %d cache line before address x  " %padb)
    # print ("  >> pad %d cache line after address x  " %pada)
   
    WAY_MAX = 16
    SET_MAX = 2048
   
    obj = open_ascii_obj(objfile)
    
    org_valid = False
    data_valid = False
    current_address = 0
    current_address_align = 0
    current_data = []
    ###llcSlice = []
   
    global memdata
    global memdata_np
    global memdata_size
   
   
    memdata = {}
    memInfo = {}
   
    totalCacheLine = 0
    startTime = datetime.datetime.now()
    PADADDR = 0xffffffffffffffc0 
   
   
    # force padding at address 0
    # for SBFT compliance
    ## for ii in xrange(16):
    ##   memdata[ ii * 0x40 ] = ['00'] * 64
   
   
   
    for line in obj:
      # found = re.findall('(\w+)', line)
      #found = line.strip('/\r\n ').split()
      found = line.split()
      #next
      if found[0x0] == '/origin':
        # print "    * found %s" %found[1]
        found[0x1] = int(found[0x1], 16)
        if len(found) == 0x3:
          found[0x2] = int(found[0x2], 16)
   
        # change the address to new found address
        current_address = found[0x1]
        current_address_align = current_address - (current_address % 0x40)
   
        if not (current_address_align & PADADDR) in memdata:
          # print "%#x" % (current_address_align)
          memdata[current_address_align & PADADDR] = ['00'] * 64
        # else:
        #   print "address exist : %s" % hex(current_address)
   
        org_valid = True
        data_valid = True
        current_data = []
        
      elif found[0x0] == '/symbol':
        if len(current_data) != 0x0:
          memdata[current_address] = current_data
   
        org_valid = False
        data_valid = False
        current_address = 0x0
        current_data = []
   
      elif found[0x0] == '/eof':
        # Updata data to library
        if len(current_data) != 0x0 and current_address != 0xfffffff0:
          memdata[current_address] = current_data
        org_valid = False
        data_valid = False
        current_address = 0x0
        current_data = []
      else:
        # Update currently data only origin and data valid
        if org_valid == True and data_valid == True:
          datlen = len(found)
          n = current_address-current_address_align
          if n == 0x40:
            current_address_align += 0x40
            n = 0
            if not (current_address_align & PADADDR) in memdata:
              memdata[current_address_align & PADADDR] = ['00'] * 64
   
          memdata[current_address_align & PADADDR][n:(n+datlen)] = found
          current_address += datlen
          
    # if len(current_data) != 0x0:
    #   memdata[current_address] = current_data
    obj.close()
   
    if 0xffffffc0 in memdata:
      if 0x1f000 in memdata:
        print("Seed not compliant : 0x1f000")
        return "FAIL"
      elif 0x8000 in memdata:
        print("Seed not compliant : 0x1f000")
        return "FAIL"
      else:
        print(" Use alternate reset vector at 0x1f000")
        memdata[0x1f000] = ['00'] * 64
        memdata[0x8000] = ['90'] * 64
        memdata[0x8000][0] = 'f4' 
        memdata[0x8000][1] = 'eb' 
        memdata[0x8000][2] = 'fd' 
      
        for ii in range(0x10):
          memdata[0x1f000][ii] = memdata[0xffffffc0][0x30 + ii]
    else:
      print("resetvector not found")
      return 'FAIL'
   
   
    ###loopcnt = 0x1
    ###if cha == 'ALL':
    ###  hardcode_chaid = 0
    ###else:
    ###  hardcode_chaid = None
   
    #for current_address in sorted(memdata.keys()):
    #  print hex(current_address), "".join (memdata[current_address])
   
    old = 99999999999999999
   
   
    memdata_size =  len(memdata)
    memdata_np = np.full((memdata_size), 0, 
      dtype=[
          ('addr',np.uint64, 1),
          ('tag', np.compat.long), 
          ###('mlc',np.object),
          ###('slice', np.uint),
          ('sets', np.uint32),
          ('ways', np.uint),
          ('mesi', np.uint32),
          ('data',np.uint64,8),
          ("datas",object),
          ("addrtype", np.uint32)])
          
    _colorapi.setFgColor("iyellow")  
    print ("  >> total cache line:",memdata_size, ", size = %dk" %(memdata_size * 64 / 1024.0))
    _colorapi.resetColor()    
    
    idx = 0
   
    for current_address in sorted(memdata.keys()):
      if current_address == old:
        print (hex(current_address))
      else:
        old = current_address
        tmp256 = "".join (memdata[current_address][::-1])
        memdata_np['addr'][idx] = current_address
        tmpdata = int(tmp256, 16)
        memdata_np['datas'][idx] = tmpdata
   
        idx = idx + 1
   
    memdata_np['tag']     =   memdata_np['addr'] >> 17
    memdata_np['sets']    =   memdata_np['addr'] >> 6 & 0x7ff
    memdata_np['mesi']    =   0x2
    memdata_np['ways']    =   0xff
    memdata_np['addrtype']=   0x00    # 0x00 : address from obj file
   
    #### calculate hash
    ###if cha=='ALL':
    ###  memdata_np['cboid']    = 0
    ###else:
    ###  memdata_np['cboid']   =   llcHash(memdata_np['addr'], cha)
    ###  memdata_np.sort(order = 'cboid')
   
    ###if cha == "ALL":
    waycount = np.empty((1,SET_MAX), dtype = np.int32)
    waycount.fill(start_way)
    ###else:
    ###  waycount = np.empty((cha, SET_MAX), dtype = np.int32)
    ###  waycount.fill(start_way)
   
   
    # assign way
    for ii in range(memdata_size):
      ###cid  = memdata_np['mlc'][ii]  
      sets = memdata_np['sets'][ii]  
      ways = waycount[0][sets]
      #print ways
      if ways == WAY_MAX:
        print("Test cannot fit into MLC. WAYS=0x%x MAX_WAYS=0x%x" % ( ways, WAY_MAX))
        ###if cha=='ALL':
        ###  memdata_np['cboid']    = 'ALL'
        ###else:
        ###  #memdata_np['cboid']   =   llcHash(memdata_np['addr'], cha)
        ###  memdata_np.sort(order = 'cboid')
        ###  memdata_np['cboid'] = np.vectorize(str)(memdata_np['cboid']) # convert int to string
        
        with open(objfile[:-4] + ".error" , r'w') as RAW:
          RAW.write( "ADDRESS,TAG,SET,WAY,DATA\n")
          for jj in range(memdata_size):
              if jj == ii:
                  RAW.write( "ERROR\n")
              RAW.write( "0x%012x, 0x0, 0x%08x, 0x%03x, 0x%02x, 0x%0128x\n" %(\
                      ###memdata_np['cboid'][jj],\
                      memdata_np['addr' ][jj], \
                      memdata_np['tag'  ][jj],\
                      memdata_np['sets' ][jj],\
                      memdata_np['ways' ][jj],\
                      memdata_np['datas'][jj]))
        #return 1
        return "FAIL"
      
      memdata_np['ways'][ii] = ways 
      waycount[0][sets] = ways + 1
   
    pad_addr = padimg(list(memdata_np['addr']) , pada, padb)
    paddata_size =  len(pad_addr)
   
    memdata_np_pad = np.full((paddata_size), 0, 
      dtype=[
          ('addr',np.uint64, 1),
          ('tag', np.compat.long), 
          ###('cboid',np.object),
          ###('slice', np.uint),
          ('sets', np.uint32),
          ('ways', np.uint),
          ('mesi', np.uint),
          ('data',np.uint64,8),
          ("datas",object), 
          ("addrtype", np.uint32)])
   
    memdata_np_pad['addr']    = pad_addr
    memdata_np_pad['tag']     = memdata_np_pad['addr'] >> 17
    memdata_np_pad['sets']    = memdata_np_pad['addr'] >> 6 & 0x7ff
    memdata_np_pad['mesi']    = 0x2
    memdata_np_pad['ways']    = 0xff
    memdata_np_pad['addrtype']= 0x1    # 0x00 : address from obj file
   
    # calculate hash for padded address
    ###if cha=='ALL':
    ###  memdata_np_pad['cboid']    = 0
    ###else:
    ###  memdata_np_pad['cboid']   =   llcHash(memdata_np_pad['addr'], cha)
    ###  memdata_np_pad.sort(order = 'cboid')
   
    # assign way
    for ii in range(paddata_size):
      ###cid  = memdata_np_pad['cboid'][ii]  
      sets = memdata_np_pad['sets'][ii]  
      ways = waycount[0][sets]
      if ways == WAY_MAX:
          continue    
      memdata_np_pad['ways'][ii] = ways 
      waycount[0][sets] = ways + 1
   
    memdata_np = np.concatenate((memdata_np, memdata_np_pad), axis = 0)
   
    memdata_np.sort(order = 'addr')
    ###memdata_np.sort(order = 'cboid')
    memdata_size = len(memdata_np) 
   
    testname = os.path.splitext(objfile)[0]
    ###if cha=='ALL':
    ###  memdata_np['cboid']    = 0xff
   
    with open(testname + ".img" , r'w',  buffering = 8*1024 * 1024) as RAW:
    ###  memdata_np['cboid'] = np.vectorize(str)(memdata_np['cboid']) # convert int to string
      ###print >> RAW, "-----------------------------------------------"
      RAW.write( "TYPE,MESI,ADDRESS,TAG,SET,WAY,DATA\n")
      for ii in range(memdata_size):
        ###print >> RAW, ">>>>> %04d" %(ii)
   
        if memdata_np['ways' ][ii] < 0xff:
          #print >> RAW, "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
          RAW.write( "%02d,%d, 0x%012x, 0x%08x, %4d, %2d, 0x%0128x\n" %(\
                  memdata_np['addrtype'  ][ii],\
                  memdata_np['mesi'      ][ii],\
                  memdata_np['addr'      ][ii],\
                  memdata_np['tag'       ][ii],\
                  memdata_np['sets'      ][ii],\
                  memdata_np['ways'      ][ii],\
                  memdata_np['datas'     ][ii]))
   
   
    return 

def padimg(img, pada = 0, padb=0):
    start = datetime.datetime.now()
    #global cl, addr_range, addr,  pad_addr_b, pad_addr_a

    addr = [int(ii) for ii in sorted(img)]
    start_addr = 0
    end_addr   = 0xffffffffffffffff
    addr_range = OrderedDict()
    for ii in addr:
        if ii != end_addr + 0x40:
            addr_range[ii]=[ii,ii]
            start_addr  = ii
            end_addr    = ii
        else:
            end_addr    = ii
            addr_range[start_addr][1] = ii

    addrd = {ii:1 for ii in addr}
    addr_start  = {ii:1 for ii in addr_range}
    addr_end    = {addr_range[ii][1]:1 for ii in addr_range} 
    pad_addr_b = OrderedDict()

    for ii in range(1,padb + 1):
        for address in sorted(addr_range):
            addr_before = address - (ii * 0x40)
            if  addr_before >= 0:
                if not (addr_before in pad_addr_b): #and  not (addr_before  in addr):
                    if not (addr_before in addrd): 
                        pad_addr_b[addr_before] = 1

    pad_addr_a = OrderedDict()
    for ii in range(1,pada + 1):
        for address in sorted(addr_range):
            addr_after = addr_range[address][1] + (ii * 0x40)
            if not (addr_after in pad_addr_a): #and  not (addr_before  in addr):
                if not (addr_after in pad_addr_b): #and  not (addr_before  in addr):
                    if not (addr_after in addrd): 
                        pad_addr_a[addr_after] = 1
    #print(pad_addr_a.keys()) 
    #print(pad_addr_b.keys()) 
    #ret =  OrderedDict(list(pad_addr_b.items() + pad_addr_a.items())   ).keys()
    ret =  list(OrderedDict(list(pad_addr_b.items()) + list(pad_addr_a.items())).keys())

    return ret

def reset_with_license_ratio_voltage(license, ratio, voltage):
    license_array = gfo.ia_fixed_license_array(license) if license !=None else []
    #ratio_array=gfo.ia_fixed_ratio_array(ratio) if ratio !=None else []
    #voltage_array = gfo.ia_vbump_array(fixed_voltage=voltage, computes=len(sv.sockets.computes) ) if voltage !=None else []
    boot_array = gfo.ia_fixed_boot_array(ratio, voltage)
    fuse_string = license_array+boot_array
    if len(fuse_string) > 0:
        gfo.fuse_cmd_override_reset (fuse_string, skip_init=True)
    else:
        itp.resettarget()
    return fuse_string

# @check_execution_time
def run_test_withconfig(obj,compute,core):    
    if (parseObj(obj,start_way=0, pada = 16, padb = 1) == 'FAIL'): return
    resetarray(compute,core)    

    with ipc.device_locker():
        load_RWC_MLC(os.path.splitext(obj)[0]+'.img',compute,core)
        
    tapconfig(compute,core,cr=1,sbft=1)
    ipc.resettarget()
     
    ####set your config here################ 
    sv.sockets.compute0.uncore.pcodeio_map.io_microcontroller_configuration.halt_microcontroller=1
    sv.sockets.compute1.uncore.pcodeio_map.io_microcontroller_configuration.halt_microcontroller=1
    sv.sockets.computes.cpu.cores.ml5_cr_mlc_iccp_pcu_config.iccp_max_license = 7
    sv.sockets.computes.cpu.cores.ml5_cr_mlc_iccp_pcu_config.iccp_min_license = 7
    sv.socket0.computes.uncore.core_pmsb.core_pmsbs.core_pmsb_instance.pmsb_top.pma_core.core_license_control=0xC0000007  
    ########################################
    # print("storage value: ",sv.socket0.compute0.uncore.core_pmsb.core_pmsb0.core_pmsb_instance.pmsb_top.pma_core.core_license_storage)

        
    cpu_tap=eval(f"sv.socket0.compute{compute}.taps.scf_gnr_maxi_coretile_phy{core}_xi_core_rwc_core_ip_tap")
    cpu_tap.core_tapconfig = 0x70105de6
    # tapconfig(compute,core,cr=0,sbft=1)
    # cpu_tap.core_tapconfig.cfg_config_restart = 0
    # ipc.resettarget()   
    
def open_ascii_obj(objfile):
    iasm_exe = '\\\\crcv03a-cifs.cr.intel.com\mpe_spr_003\DPM_Debug\content\EFI\iasm.exe'
    if (is_binary_obj(objfile)):
        print (" File is binary.. converting to ASCII");
        tmpdir = tempfile.mkdtemp()
        current_directory = os.getcwd()
        os.chdir(tmpdir)
        (base, ext) = os.path.splitext(os.path.basename(objfile))
        asciiFilename = tmpdir + os.sep +  base + "_8.obj"
        print(" Converting %s to ascii object file '%s'" % (objfile, asciiFilename))
        shutil.copy(objfile, asciiFilename)
        if os.path.exists(iasm_exe) == False:
            raise FileNotFountError("This script needs to convert the binary file to ascii and IASM is not available at {iasm_exe}")
        cmd = ("%s -out8 %s" % (iasm_exe, asciiFilename))
        print( cmd )
        result = subprocess.check_output([iasm_exe, '-out8', asciiFilename], text=True)
        print(result)
        if ( is_binary_obj(asciiFilename) == True ):
            raise FileNotFoundError("BINARY TO ASCII CONVERSION DID NOT WORK {iasm_exe}")
        objfile = asciiFilename
        os.chdir(current_directory)
    print (f"Opening {objfile}")
    obj = open(objfile, 'r')
    return obj

def print_fivr_info(compute=0):
    import graniterapids.fivr.common.Utils as utils
    utils.dut.Miscellaneous.ENABLE_NN_LOGGER = False
    utils.FivrState.get_status(DieIndex = compute, RegAccess = 'TAP2REG').get_status_of_fivr = 'cdie'

def is_binary_obj(objfile):
    obj = open(objfile, 'rb')
    bin_obj_start = 0x40
    b = ord(obj.read(1))
    print (f"{b}")
    obj.close()
    return(b == bin_obj_start)

def core_to_compute(core):
    for compute in (sv.socket0.computes):
        for c in compute.cpu.cores:
            if core == c.instance:
                #print (f"CORE {core} {c.instance} is in compute {compute.instance}")
                return compute.instance
                #break
    print ("CORE NOT FOUND!!!\n")
    return None

def core_to_itp(core):
    compute = core_to_compute(core)
    cpu=eval(f"sv.socket0.compute{compute}.cpu.core{core}")
    apic = cpu.thread0.ml3_cr_pic_legacy_local_apic_id
    for i in range(len(itp.threads)):
            if (itp.threads[i].msr(0x802) == apic):
                return i
    print ("ITP  NOT FOUND!!!\n")
    return None



