#
#   Owner   : fwang8
#   Group   : CQNTHR
#   DATE    : 05/17/2022
#   VERSION : 1.0
#   PRODUCT : SPRSP
#   USAGE   : Convert tsl to baremetal (run on uefi using MerlinX)
#   


import datetime
import os
import json
import random
import re
import __main__
import shutil
import subprocess

MAX_LINEAR_ADDR = 48
MAX_PHY_ADDR    = 48
APIC_ADDRESS    = 0xfee00000

addr_used = {}

iasm_exe = os.path.split( os.path.abspath(__file__) )[0] + r"\\iasm.exe"
if not os.path.exists(iasm_exe):
    print("  !!! iasm.exe not found at %s" %os.path.abspath(__file__)[0])
    print("  !!! Please copy iasm.exe to this folder")

iasm_log = False
iasm_list = False
iasm_logfile = r"C:\Temp\iasm.log"





def check_execution_time(func):
    def run(*args, **kwargs):
        t0 = datetime.datetime.now()
        ret = func(*args, **kwargs)
        print ("  >> Done %15s " %func.__name__, end='')
        print (datetime.datetime.now() - t0)
        return ret

    return run




@check_execution_time
def iasm(asm=None):

    if iasm_list == True:
        iasm_arg = "-sym_extern -b GoldenCove -bin -max_addr 44"
    else:
        iasm_arg = "-sym_extern -no_list -b GoldenCove -bin -max_addr 44"

    if asm == None:
        return

    if not os.path.exists(asm):
        print ("File not exist")
        return 1

    wdir = os.path.dirname(asm)

    p = subprocess.Popen(['cmd'], cwd=wdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True )#creationflags=subprocess.CREATE_NEW_CONSOLE)

    command = '"' + iasm_exe + '"' + " " + iasm_arg + " " + '"' + asm +'"'
    print("Running " , command)

    p.stdin.write(command.encode() )
    

    p.stdin.write("\n".encode())
    os.sys.stdout.flush()  
    out, err = p.communicate()

    if "Error" in out.decode():
        print("\n")
      
        for ii in out.decode().split('\r\n')[2:]:
            print(ii)
            if iasm_log != False:
                print(asm, file=open(iasm_logfile, "a"))
                print("!!!!! FAIL !!!!!", file=open(iasm_logfile, "a"))
                print(ii, file=open(iasm_logfile, "a"))
    else:
        if iasm_log != False:
            print("log to ", iasm_logfile)
            print(asm, file=open(iasm_logfile, "a"))
            print("----- PASS -----", file=open(iasm_logfile, "a"))

        print("  >> iasm pass")

        #print("copy file " + os.path.splitext(asm)[0] + ".obj"+ " to " +  r"c:\temp\trial.obj")
        #shutil.copyfile(os.path.splitext(asm)[0] + ".obj", r"c:\temp\trial.obj")


    





def pagemap(lin, phy, page, msg = None):
    global PAGEMAP
 

    if lin in PAGEMAP:
        print(" !!!!! PAGEMAP %08x from %08x -> %08x" %(lin, PAGEMAP[lin]['PHYADDR'], phy))
        PAGEMAP[lin] = {'PHYADDR':phy, "PAGE":page}
    else:
        PAGEMAP[lin] = {'PHYADDR':phy, "PAGE":page}


#@check_execution_time
def load_address(addrfile=None):

    global memusable
    global memusable_l

    if addrfile == None:
        addrfile = os.path.dirname(os.path.realpath(__file__)) + r"\address.txt"

    if os.path.exists(addrfile):
        input_file = open (addrfile)
        memusable = json.load(input_file)
        input_file.close()
    
        memusable_l = len(memusable) - 1
        delmem = []
        for ii in range(memusable_l):
            if memusable[ii] < 0x10000:
                delmem.append( memusable[ii] )
    
        for ii in delmem:
             memusable.remove(ii)
    
        memusable_l = len(memusable) - 1



def init_paging():

    global PML4_ADDR, PML4, PDPT, PDIR, PTBL, PAGEMAP, USED_PHY_MEM

    USED_PHY_MEM = {}
    PML4 = {}
    PDPT = {}
    PDIR = {}
    PTBL = {}
    PAGEMAP = {}


    PML4_ADDR       = random_address( maxphy = 0x80000000, linaddr_check = True) & 0xfffff000
    pagemap(PML4_ADDR, PML4_ADDR, '4K')

    USED_PHY_MEM[PML4_ADDR] = {'TYPE' : 'PAGING_PML4'}


    PML4[PML4_ADDR] = [0 for ii in range(512)]






@check_execution_time
def parseaddr(obj):


    if not os.path.isfile(obj):
        print("!!! ERROR !!!")
        print("File not available : %s" %obj)
        return

    ascfile = os.path.splitext(obj)[0] + ".asc"
    
    global addr_used
    pagesize = 4096


    with open(obj,r'rb') as OBJ, open(ascfile, r'w', 1024*1024*8) as ASC:
        start = OBJ.read(1)
        if start != b'@':
            print("!!! ERROR !!!")
            print("Invalid obj")
            print(start)
            return

        addr_used = {}

        # APIC address
        addr_used[APIC_ADDRESS] = {'PAGE':pagesize}


        while(1):
            datatype = ord(OBJ.read(1))

            if datatype == 0x41:
                # 32 bit origin
                address  = OBJ.read(4)
                address = list(address)

                addr=0
                for ii in range(4):
                    addr = addr + (address[ii] << (ii*8))

                size = OBJ.read(4)
                size = list(size)

                sz = 0
                for ii in range(4):
                    sz = sz + (size[ii] << (ii*8))
                
                ASC.write("/origin %08x %08x\n" %(addr, sz))

                OBJ.seek(sz, 1) 
                for ii in address_pages(addr, sz, pagesize):
                    ASC.write("    ----> 0x%016x -> 0x%016x \n" %(ii, ii + 4095))
                    if ii in addr_used:
                        print(" Repeated page found : %016x" %(ii))
                    else:
                        addr_used[ii] = {'PAGE':pagesize}

            elif datatype == 0x44:
                # 64 bit origin
                address  = OBJ.read(8)
                address = list(address)

                addr=0
                for ii in range(8):
                    addr = addr + (address[ii] << (ii*8))

                size = OBJ.read(4)
                size = list(size)

                sz = 0
                for ii in range(4):
                    sz = sz + (size[ii] << (ii*8))
                
                addr = hex(addr)[2:]
                if len(addr) == 9:
                    addr = addr.zfill(10)
                else:
                    addr = addr.zfill(16).upper()

                ASC.write("/origin %s %08x \n" %(addr, sz))

                OBJ.seek(sz, 1) 
                
                for ii in address_pages(addr, sz, pagesize):
                    ASC.write("    ----> 0x%016x -> 0x%016x \n" %(ii, ii + 4095))
                    if ii in addr_used:
                        print(" Repeated page found : %016x" %(ii))
                    else:
                        addr_used[ii] = {'PAGE':pagesize}

            elif datatype == 0x43:
                # symbol
                address  = OBJ.read(4)
                address = list(address)

                addr=0
                for ii in range(4):
                    addr = addr + (address[ii] << (ii*8))

                size = OBJ.read(1)
                sz = 0
                for ii in range(1):
                    sz = sz + (size[ii] << (ii*8))

                OBJ.seek(sz, 1) 
                

            elif datatype == 0x46:
                # symbol
                address  = OBJ.read(8)
                address = list(address)

                size = OBJ.read(1)
                sz = 0
                for ii in range(1):
                    sz = sz + (size[ii] << (ii*8))

                addr=0
                for ii in range(8):
                    addr = addr + (address[ii] << (ii*8))

                OBJ.seek(sz, 1) 
                


            elif datatype == 0x4f:
                lastlocation = OBJ.tell()
                ASC.write("/eof")
                break
            else:
                print("!!! ERROR !!!")
                print("Invalid byte read")
                print(datatype)
                loc = OBJ.tell()
                print("%08x" %(loc))
                break

        OBJ.seek(0)
        summ = 0
        cnt = 0

        print(len(addr_used), "pages used")
       
        for ii in addr_used:
            linear2physical_4k(ii)

    os.remove(ascfile)

    return



def address_pages(start, size,pgsz = 4096):
    
    mask = 0xffffffffffffffff - (pgsz - 1) 
    newstart    = start & mask
    newsize     = start - newstart + size
        
    addrpg = {}
    while(newsize > 0):
        addrpg[newstart] = pgsz
        newstart = newstart + pgsz
        newsize  = newsize - pgsz


    return addrpg



def random_address( maxphy = 0xffc0000000, retry = 0xffff, linaddr_check = False):

    global memusable
    global memusable_l
    global USED_PHY_MEM

    cnt = 0

    while(1):
        cnt = cnt + 1
        if cnt > retry:
            print("Fail to get random address after %d retry" %cnt)
            return None

        idx = random.randint(0, memusable_l)
        phyaddr = memusable[idx]

        if linaddr_check != False:
            # physical address crash with the linear address, skip this phy addr
            if phyaddr in addr_used:
                continue
        
        if (phyaddr & 0xfffffffffffff000) in USED_PHY_MEM:
            print(" *** %x" %phyaddr)
            continue
        
        if phyaddr < maxphy:
            #print (hex(phyaddr))
            del memusable[idx]
            memusable_l = len(memusable) - 1
            pass
            pass
            return phyaddr
            break
        else:
            pass


def linear2physical_4k(linaddr, CR3 = None, show = False):

    global USED_PHY_MEM, PAGEMAP

    lin_addr_align = linaddr & 0xfffffffffffff000
    pml4e   = (lin_addr_align >> 39) & 0x1ff
    pdpte   = (lin_addr_align >> 30) & 0x1ff
    pde     = (lin_addr_align >> 21) & 0x1ff
    pte     = (lin_addr_align >> 12) & 0x1ff
    
    if PML4[PML4_ADDR][pml4e] == 0:
        while(True):
            pdpt_addr = random_address( maxphy = 0xc0000000, linaddr_check = True ) & 0xfffff000
            if pdpt_addr in PAGEMAP:
                continue
            else:
                break

        USED_PHY_MEM[pdpt_addr] = {'TYPE':'PAGING'}
        PML4[PML4_ADDR][pml4e] = pdpt_addr
        pagemap(pdpt_addr, pdpt_addr,'4K')
        # set attribute ...
        PML4[PML4_ADDR][pml4e] = PML4[PML4_ADDR][pml4e] | 0x27
        PDPT[pdpt_addr] = [0 for ii in range(512)]    
    else:
        pdpt_addr = ((PML4[PML4_ADDR][pml4e] >> 12 ) & (2**(MAX_PHY_ADDR-12) - 1)) << 12
    

    if PDPT[pdpt_addr][pdpte] == 0:
        while(True):
            pdir_addr = random_address( maxphy = 0xc0000000, linaddr_check = True) & 0xfffff000
            if pdir_addr in PAGEMAP:
                continue
            else:
                break

        USED_PHY_MEM[pdir_addr] = {'TYPE':'PAGING'}
        PDPT[pdpt_addr][pdpte]  = pdir_addr
        pagemap(pdir_addr, pdir_addr,'4K')
        # set attribute
        PDPT[pdpt_addr][pdpte]  = PDPT[pdpt_addr][pdpte] | 0x23
        PDIR[pdir_addr] = [0 for ii in range(512)]
    else:    
        pdir_addr = (( PDPT[pdpt_addr][pdpte] >> 12 ) & (2**(MAX_PHY_ADDR-12) - 1)) << 12


    if PDIR[pdir_addr][pde] == 0:
        while(True):
            ptbl_addr = random_address( maxphy = 0xc0000000, linaddr_check = True) & 0xfffff000
            if ptbl_addr in PAGEMAP:
                continue
            else:
                break

        if ptbl_addr in USED_PHY_MEM:
            print(hex(ptbl_addr))

        USED_PHY_MEM[ptbl_addr] = {'TYPE':'PAGING'}
        PDIR[pdir_addr][pde] = ptbl_addr
        pagemap(ptbl_addr, ptbl_addr,'4K', 'pdir')

        # set attribute
        PDIR[pdir_addr][pde] = PDIR[pdir_addr][pde] | 0x27
        PTBL[ptbl_addr] = [0 for ii in range(512)]
    else:
        ptbl_addr = (( PDIR[pdir_addr][pde] >> 12 ) & (2**(MAX_PHY_ADDR-12) - 1)) << 12


    if PTBL[ptbl_addr][pte] == 0:
        
        if (lin_addr_align < 0x10000) or ( 0xfee00000 <= lin_addr_align < 0x100000000):
            #print("1 to 1 mapping addr %08x" %(lin_addr_align))
            page_addr = lin_addr_align

        else:
            page_addr   = random_address() & 0xfffffffffffff000


        if page_addr in USED_PHY_MEM:
            print(hex(page_addr))
            #return
        USED_PHY_MEM[page_addr] = {'TYPE':'CODE_DATA'}
        PTBL[ptbl_addr][pte]    = page_addr
        # set attribute
        if page_addr == APIC_ADDRESS:
            PTBL[ptbl_addr][pte]    = PTBL[ptbl_addr][pte] | 0x7f
        else:
            PTBL[ptbl_addr][pte]    = PTBL[ptbl_addr][pte] | 0x27

    else:    
        page_addr = (( PTBL[ptbl_addr][pte] >> 12 ) & (2**(MAX_PHY_ADDR-12) - 1)) << 12


    #PAGEMAP[linaddr] = {"PHYADDR":page_addr, 'PAGE':'4K'}
    pagemap(linaddr, page_addr, '4K', "page")
    
    if show != False:
        print("PML4[%3d]     0x%016x " %(pml4e, PML4[PML4_ADDR][pml4e]))
        print("PDPT[%3d]     0x%016x " %(pdpte, PDPT[pdpt_addr][pdpte]))
        print("PDIR[%3d]     0x%016x " %(pde, PDIR[pdir_addr][pde]))
        print("PTBL[%3d]     0x%016x " %(pte, PTBL[ptbl_addr][pte]))


def print_paging():

    for ii in PML4:
        print(" -> PML4 %016x" %ii)
        for jj in range(len(PML4[ii])):
            if jj%8 ==0 and jj == 0:
                pass
                #print("")
            elif jj%8 ==0 and jj != 0:
                print("")
            else:
                print(", ", end = "")

            print("%016x" %PML4[ii][jj], end = "")
        print("\n")
    print("\n")

    for ii in PDIR:
        print(" -> PDIR %016x" %ii)
        for jj in range(len(PDIR[ii])):
            if jj%8 ==0 and jj == 0:
                pass
                #print("")
            elif jj%8 ==0 and jj != 0:
                print("")
            else:
                print(", ", end = "")

            print("%016x" %PDIR[ii][jj], end = "")
        print("\n")
    print("\n")

    for ii in PDIR:
        print(" -> PDIR %016x" %ii)
        for jj in range(len(PDIR[ii])):
            if jj%8 ==0 and jj == 0:
                pass
                #print("")
            elif jj%8 ==0 and jj != 0:
                print("")
            else:
                print(", ", end = "")

            print("%016x" %PDIR[ii][jj], end = "")
        print("\n")
    print("\n")

    for ii in PTBL:
        print(" -> PTBL %016x" %ii)
        for jj in range(len(PTBL[ii])):
            if jj%8 ==0 and jj == 0:
                pass
                #print("")
            elif jj%8 ==0 and jj != 0:
                print("")
            else:
                print(", ", end = "")

            print("%016x" %PTBL[ii][jj], end = "")
        print("\n")
    print("\n")




@check_execution_time
def dol2bm(asm, randomseed = None, target = None):

    global PML4_ADDR, PAGEMAP
   

    if randomseed == None:
        randomseed = random.randint(0,0xfffffff)
        print("  -> random seed = %d" %(randomseed))
    random.seed(randomseed)
 
    load_address()
    init_paging()




    if os.path.exists( os.path.splitext(asm)[0] + ".obj"):
        parseaddr( os.path.splitext(asm)[0] + ".obj")
    else:
        print("    !!!! %s does not exist" %(os.path.splitext(asm)[0] + ".obj"))
        return 1

    PAGEMAPL2P = re.compile("LIN\s+->\s+PHY,\s+PAGETYPE")

    with open(asm, r'r') as ASMRD, open( os.path.splitext(asm)[0] + "_baremetal.asm" , r'w') as ASMBM:
        ASMBM.write("\n\n; TSL random seed : 0x%x\n\n" %(randomseed))

        for line in ASMRD:
            if line[0] == ";":
                ASMBM.write(line)

                found = PAGEMAPL2P.search(line)
                if found:
                    for linaddr in PAGEMAP:
                        
                        if PAGEMAP[linaddr]['PAGE'] == '4K':
                            pagetype = "4K"
                        #ASMBM.write("; 0x%08x -> 0x%08x \n" %(linaddr, PAGEMAP[linaddr]['PHYADDR']))

                        ASMBM.write("PAGEMAP(0x%08x -> 0x%08x, %s)\n" %(linaddr, PAGEMAP[linaddr]['PHYADDR'], pagetype))
                    ASMBM.write("\n\n\n\n\n")
                    continue
                else:
                    continue

            if line[0:10] == "PAGE_TABLE":
                if line[10] != "_":
                    ASMBM.write("PAGE_TABLE\t EQU 0x%08x\n" %(PML4_ADDR))
                    continue
                
            ASMBM.write(line)

        ASMBM.write("\n\n\n\n; ----------------------------------------------------------------------------------------------\n")
        ASMBM.write("; PAGING \n\n")


        count = 0

        for ii in PML4:
            ASMBM.write("data_paging_PML4_%d SEGMENT use64 ;# at 0x%08x" %(count, ii))
            for jj in range( len(PML4[ii]) ):
                if jj%8 == 0 and jj == 0:
                    ASMBM.write("\n\nDQ ")
                    pass
                elif jj%8 == 0 and jj !=0:
                    ASMBM.write("\nDQ ")
                    
                else:
                    ASMBM.write(", ")

                ASMBM.write("0x%016x" %(PML4[ii][jj]))
            ASMBM.write("\n\ndata_paging_PML4_%d ENDS\n\n\n" %(count))
            count = count + 1


        for ii in PDPT:
            ASMBM.write("data_paging_PDPT_%d SEGMENT use64 ;# at 0x%08x" %(count, ii))
            for jj in range( len(PDPT[ii]) ):
                if jj%8 == 0 and jj == 0:
                    ASMBM.write("\n\nDQ ")
                    pass
                elif jj%8 == 0 and jj !=0:
                    ASMBM.write("\nDQ ")
                    
                else:
                    ASMBM.write(", ")

                ASMBM.write("0x%016x" %(PDPT[ii][jj]))
            ASMBM.write("\n\ndata_paging_PDPT_%d ENDS\n\n\n" %(count))
            count = count + 1



        for ii in PDIR:
            ASMBM.write("data_paging_PDIR_%d SEGMENT use64 ;# at 0x%08x" %(count, ii))
            for jj in range( len(PDIR[ii]) ):
                if jj%8 == 0 and jj == 0:
                    ASMBM.write("\n\nDQ ")
                    pass
                elif jj%8 == 0 and jj !=0:
                    ASMBM.write("\nDQ ")
                    
                else:
                    ASMBM.write(", ")

                ASMBM.write("0x%016x" %(PDIR[ii][jj]))
            ASMBM.write("\n\ndata_paging_PDIR_%d ENDS\n\n\n" %(count))
            count = count + 1

        for ii in PTBL:
            ASMBM.write("data_paging_PTBL_%d SEGMENT use64 ;# at 0x%08x" %(count, ii))
            for jj in range( len(PTBL[ii]) ):
                if jj%8 == 0 and jj == 0:
                    ASMBM.write("\n\nDQ ")
                    pass
                elif jj%8 == 0 and jj !=0:
                    ASMBM.write("\nDQ ")
                    
                else:
                    ASMBM.write(", ")

                ASMBM.write("0x%016x" %(PTBL[ii][jj]))
            ASMBM.write("\n\ndata_paging_PTBL_%d ENDS\n\n\n" %(count))
            count = count + 1


    iasm( os.path.splitext(asm)[0] + "_baremetal.asm" )


    newasm = os.path.splitext(asm)[0] + "_baremetal.asm"
    newobj = os.path.splitext(asm)[0] + "_baremetal.obj"


    if target == None:
        target = os.path.split(asm)[0] + r"\target"
        if not os.path.exists(target):
            os.mkdir(target)
        if not os.path.exists(target + r"\src"):
            os.mkdir(target + r"\src")
    else:
        if not os.path.exists(target + r"\src"):
            os.mkdir(target + r"\src")


    folder_asm, filename_asm = os.path.split(newasm)
    folder_obj, filename_obj = os.path.split(newobj)

    shutil.move(newasm, target + r"\\src\\" + filename_asm)
    shutil.move(newobj, target + r"\\" + filename_obj)
    
    os.remove(os.path.splitext(asm)[0] + "_baremetal.lst")
    os.remove(os.path.splitext(asm)[0] + "_baremetal.plst")




def dumpmem():

    with open (r"c:\temp\mem.log", r'w') as MEM:
        for ii in memusable:
            MEM.write("0x%08x\n" %ii) 




import msvcrt 

@check_execution_time
def dol2bm_batch(folder, start = 1):

    #global phymem
    #phymem = {}
    asm = []
    for subdir, dirs, files in os.walk(folder):
        for filename in files:
            if msvcrt.kbhit() != 0:
                return        
            
            if filename.endswith(r".asm"):
                asm.append(subdir + '\\'+ filename)

    asm_l = len(asm)
    count = 1
    for ii in asm:
        if count < start:
            count = count + 1
            continue
        if msvcrt.kbhit() != 0:
            return        
        print("\n\n#####  %4d / %4d  #######################################################################################################################" %(count, asm_l))
        print(ii)
        parseasm(ii)
        count = count + 1




load_address()
init_paging()














