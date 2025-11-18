"""
CWF (Clearwater Forest) MCA Bank Definitions and Decoder
Author: gaespino
Last update: 12/11/25

Provides comprehensive MCA bank information for CWF product including:
- Bank ID to name mapping
- Scope information (Core, Module, Socket, Uncore)
- Physical instance counts
- Decoding utilities
"""

# ANSI Color codes for console output (Python 3.8+ compatible)
class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    @staticmethod
    def success(text):
        return f"{Colors.GREEN}{text}{Colors.RESET}"
    
    @staticmethod
    def error(text):
        return f"{Colors.RED}{text}{Colors.RESET}"
    
    @staticmethod
    def info(text):
        return f"{Colors.CYAN}{text}{Colors.RESET}"
    
    @staticmethod
    def warning(text):
        return f"{Colors.YELLOW}{text}{Colors.RESET}"

# CWF MCA Bank Definitions
# Based on CWF architecture with Atom cores (4 cores per module)

CWF_MCA_BANKS = {
    # Core-scoped banks (0-3) - Atom core specific
    0: {
        'name': 'IC',
        'full_name': 'Instruction Cache',
        'scope': 'Core',
        'merged': False,
        'instances': '1 per Atom core (4 per module)',
        'description': 'Instruction Cache errors',
        'register_path': 'sv.sockets.computes.cpu.modules.cores.ic_cr_mci_status',
        'notes': 'Atom core architecture'
    },
    1: {
        'name': 'MEC',
        'full_name': 'Memory Execution Cluster',
        'scope': 'Core',
        'merged': False,
        'instances': '1 per Atom core (4 per module)',
        'description': 'Memory Execution Cluster (data cache and TLB) errors',
        'register_path': 'sv.sockets.computes.cpu.modules.cores.mec_cr_mci_status',
        'notes': 'Combines data cache and TLB functionality'
    },
    2: {
        'name': 'BBL',
        'full_name': 'Back-End Logic',
        'scope': 'Module',
        'merged': False,
        'instances': '1 per module',
        'description': 'Back-End Logic errors',
        'register_path': 'sv.sockets.computes.cpu.modules.bbl_cr_mci_status',
        'notes': 'Module-level back-end execution'
    },
    3: {
        'name': 'BUS',
        'full_name': 'Bus Interface Unit',
        'scope': 'Module',
        'merged': False,
        'instances': '1 per module',
        'description': 'Bus Interface Unit errors',
        'register_path': 'sv.sockets.computes.cpu.modules.bus_cr_mci_status',
        'notes': 'Module to uncore interface'
    },
    
    # Module L2 cache
    4: {
        'name': 'L2',
        'full_name': 'L2 Cache',
        'scope': 'Module',
        'merged': False,
        'instances': '1 per module',
        'description': 'Module-level L2 Cache errors',
        'register_path': 'sv.sockets.computes.cpu.modules.l2_cr_mci_status',
        'notes': 'Shared by 4 Atom cores in module'
    },
    
    # Uncore banks (5+)
    5: {
        'name': 'CHA',
        'full_name': 'Caching and Home Agent',
        'scope': 'Uncore',
        'merged': False,
        'instances': 'Variable per socket',
        'description': 'LLC slice and home agent errors',
        'register_path': 'sv.sockets.computes.uncore.cha.chas.util.mc_status',
        'notes': 'One per LLC slice/CHA'
    },
    6: {
        'name': 'IMC',
        'full_name': 'Integrated Memory Controller',
        'scope': 'Uncore',
        'merged': False,
        'instances': 'Variable per socket',
        'description': 'Memory controller errors',
        'register_path': 'sv.sockets.computes.uncore.memss.mcs.chs.mcchan.imc0_mc_status',
        'notes': 'Includes channel and sub-channel errors'
    },
    7: {
        'name': 'B2CMI',
        'full_name': 'Box to Channel Memory Interface',
        'scope': 'Uncore',
        'merged': False,
        'instances': 'Variable per socket',
        'description': 'Box to Channel Memory Interface errors',
        'register_path': 'sv.sockets.computes.uncore.memss.b2cmis.mci_status'
    },
    8: {
        'name': 'MSE',
        'full_name': 'Memory Subsystem Error',
        'scope': 'Uncore',
        'merged': False,
        'instances': 'Variable per socket',
        'description': 'Memory subsystem errors',
        'register_path': 'sv.sockets.computes.uncore.memss.mcs.chs.mse.mse_mci_status'
    },
    9: {
        'name': 'LLC',
        'full_name': 'Last Level Cache',
        'scope': 'Uncore',
        'merged': False,
        'instances': 'Variable per socket',
        'description': 'LLC (L3) cache errors in SCF',
        'register_path': 'sv.sockets.computes.uncore.scf.scf_llc.scf_llcs.mci_status'
    },
    10: {
        'name': 'UPI',
        'full_name': 'Ultra Path Interconnect',
        'scope': 'IO',
        'merged': False,
        'instances': 'Variable per socket',
        'description': 'UPI link errors',
        'register_path': 'sv.sockets.ios.uncore.upi.upis.upi_regs.kti_mc_st',
        'notes': 'Socket-to-socket interconnect'
    },
    11: {
        'name': 'UBOX',
        'full_name': 'System Configuration Controller',
        'scope': 'IO',
        'merged': False,
        'instances': '1 per socket',
        'description': 'UBOX system configuration errors',
        'register_path': 'sv.sockets.io0.uncore.ubox.ncevents.ncevents_cr_ubox_mci_status',
        'notes': 'Includes IERR and MCERR logging'
    },
    12: {
        'name': 'PUNIT',
        'full_name': 'Power Control Unit',
        'scope': 'Socket',
        'merged': False,
        'instances': '2 per socket (compute + IO)',
        'description': 'Power management unit errors',
        'register_path': 'sv.sockets.computes.uncore.punit.ptpcfsms.ptpcfsms.mc_status',
        'notes': 'Separate instances for compute and IO tiles'
    },
    13: {
        'name': 'M2MEM',
        'full_name': 'Mesh to Memory',
        'scope': 'Uncore',
        'merged': False,
        'instances': 'Variable per socket',
        'description': 'Mesh to memory interface errors',
        'register_path': 'sv.sockets.computes.uncore.m2mem'
    },
    14: {
        'name': 'IIO',
        'full_name': 'Integrated IO',
        'scope': 'IO',
        'merged': False,
        'instances': 'Variable per socket',
        'description': 'PCIe root complex and IIO stack errors',
        'register_path': 'sv.sockets.ios.uncore.iio'
    }
}

# Additional CWF-specific information
CWF_NOTES = {
    'core_architecture': 'CWF uses Atom core (E-core) architecture with 4 cores per module',
    'module_concept': 'Module is the basic building block with 4 Atom cores and shared L2',
    'threading': 'Each Atom core typically supports 1 thread (no hyperthreading)',
    'llc_distribution': 'LLC is distributed across CHA slices',
    'memory_channels': 'Variable memory channels depending on SKU',
    'core_differences': 'Different from GNR: no PMSB, different core MCA banks (IC, MEC vs IFU, DCU)',
    'l2_sharing': 'L2 cache is shared among 4 Atom cores in a module',
    'bus_interface': 'BUS bank handles module to uncore communication'
}

# CWF Module architecture
CWF_MODULE_INFO = {
    'cores_per_module': 4,
    'architecture': 'Atom (E-core)',
    'l2_per_module': 1,
    'banks_per_core': 2,  # IC, MEC
    'banks_per_module': 3,  # BBL, BUS, L2
    'total_module_banks': 11  # 4*2 (core banks) + 3 (module banks)
}


def get_bank_info(bank_id):
    """
    Get detailed information about a specific MCA bank.
    
    Args:
        bank_id (int): MCA bank ID
        
    Returns:
        dict: Bank information or None if bank not found
    """
    return CWF_MCA_BANKS.get(bank_id)


def get_bank_name(bank_id):
    """
    Get the short name of an MCA bank.
    
    Args:
        bank_id (int): MCA bank ID
        
    Returns:
        str: Bank name or 'UNKNOWN'
    """
    bank = CWF_MCA_BANKS.get(bank_id)
    return bank['name'] if bank else f'UNKNOWN_BANK_{bank_id}'


def get_bank_full_name(bank_id):
    """
    Get the full descriptive name of an MCA bank.
    
    Args:
        bank_id (int): MCA bank ID
        
    Returns:
        str: Full bank name
    """
    bank = CWF_MCA_BANKS.get(bank_id)
    return bank['full_name'] if bank else f'Unknown Bank {bank_id}'


def decode_bank_error(bank_id, status_value=None, addr_value=None, misc_value=None):
    """
    Decode MCA bank error with additional context.
    
    Args:
        bank_id (int): MCA bank ID
        status_value (int, optional): MCi_STATUS register value
        addr_value (int, optional): MCi_ADDR register value
        misc_value (int, optional): MCi_MISC register value
        
    Returns:
        dict: Decoded error information
    """
    bank = get_bank_info(bank_id)
    if not bank:
        return {'error': f'Invalid bank ID: {bank_id}'}
    
    result = {
        'bank_id': bank_id,
        'bank_name': bank['name'],
        'full_name': bank['full_name'],
        'scope': bank['scope'],
        'merged': bank['merged'],
        'instances': bank['instances'],
        'description': bank['description']
    }
    
    if 'notes' in bank:
        result['notes'] = bank['notes']
    
    if status_value is not None:
        # Decode STATUS register fields
        result['valid'] = bool(status_value & (1 << 63))
        result['overflow'] = bool(status_value & (1 << 62))
        result['uc'] = bool(status_value & (1 << 61))  # Uncorrected
        result['en'] = bool(status_value & (1 << 60))  # Error enabled
        result['miscv'] = bool(status_value & (1 << 59))  # MISC valid
        result['addrv'] = bool(status_value & (1 << 58))  # ADDR valid
        result['pcc'] = bool(status_value & (1 << 57))  # Processor context corrupt
        result['mca_error_code'] = status_value & 0xFFFF
    
    return result


def format_bank_error(bank_id, register_path='', status_value=None, module_id=None, core_id=None):
    """
    Format a human-readable MCA bank error message.
    
    Args:
        bank_id (int): MCA bank ID
        register_path (str): Full register path
        status_value (int, optional): MCi_STATUS value
        module_id (int, optional): Module ID for module/core scoped errors
        core_id (int, optional): Core ID within module for core scoped errors
        
    Returns:
        str: Formatted error message
    """
    bank = get_bank_info(bank_id)
    if not bank:
        return f'MCA Bank {bank_id}: UNKNOWN'
    
    msg = f"MCA Bank {bank_id}: {bank['name']} ({bank['full_name']})\n"
    msg += f"  Scope: {bank['scope']} | Instances: {bank['instances']}"
    
    if bank['merged']:
        msg += " | MERGED"
    
    # Add module/core context for CWF
    if module_id is not None:
        msg += f"\n  Module: {module_id}"
        if core_id is not None:
            msg += f" | Core: {core_id} (within module)"
    
    msg += f"\n  Description: {bank['description']}"
    
    if 'notes' in bank:
        msg += f"\n  Notes: {bank['notes']}"
    
    if register_path:
        msg += f"\n  Register: {register_path}"
    
    if status_value is not None:
        msg += f"\n  STATUS: 0x{status_value:016x}"
        if status_value & (1 << 63):
            msg += " [VALID]"
        if status_value & (1 << 61):
            msg += " [UNCORRECTED]"
    
    return msg


def get_banks_by_scope(scope):
    """
    Get all banks for a specific scope.
    
    Args:
        scope (str): 'Core', 'Module', 'Uncore', 'IO', or 'Socket'
        
    Returns:
        dict: Banks in the specified scope
    """
    return {k: v for k, v in CWF_MCA_BANKS.items() if v['scope'] == scope}


def get_core_banks():
    """
    Get all Atom core-scoped MCA banks.
    
    Returns:
        dict: Core-scoped banks
    """
    return get_banks_by_scope('Core')


def get_module_banks():
    """
    Get all module-scoped MCA banks.
    
    Returns:
        dict: Module-scoped banks
    """
    return get_banks_by_scope('Module')


def print_bank_table():
    """
    Print a formatted table of all MCA banks.
    """
    print("\n" + "="*100)
    print("CWF (Clearwater Forest) MCA Bank Table")
    print("="*100)
    print(f"{'Bank':<6}{'Name':<12}{'Scope':<10}{'Merged':<8}{'Instances':<30}{'Description':<35}")
    print("-"*100)
    
    for bank_id in sorted(CWF_MCA_BANKS.keys()):
        bank = CWF_MCA_BANKS[bank_id]
        merged = 'Yes' if bank['merged'] else 'No'
        desc = bank['description'][:33]
        print(f"{bank_id:<6}{bank['name']:<12}{bank['scope']:<10}{merged:<8}{bank['instances']:<30}{desc:<35}")
    
    print("="*100)
    print("\nCWF Module Architecture:")
    print(f"  Cores per Module: {CWF_MODULE_INFO['cores_per_module']}")
    print(f"  Core Architecture: {CWF_MODULE_INFO['architecture']}")
    print(f"  L2 per Module: {CWF_MODULE_INFO['l2_per_module']} (shared by all 4 cores)")
    print(f"  MCA Banks per Core: {CWF_MODULE_INFO['banks_per_core']} (IC, MEC)")
    print(f"  MCA Banks per Module: {CWF_MODULE_INFO['banks_per_module']} (BBL, BUS, L2)")
    
    print("\nArchitecture Notes:")
    for key, note in CWF_NOTES.items():
        print(f"  - {note}")
    print()


def compare_with_gnr():
    """
    Print comparison between CWF and GNR core MCA banks.
    """
    print("\n" + "="*80)
    print("CWF vs GNR Core MCA Bank Comparison")
    print("="*80)
    print("\nCWF (Atom cores):")
    print("  Bank 0: IC  (Instruction Cache)")
    print("  Bank 1: MEC (Memory Execution Cluster - combines data cache + TLB)")
    print("  Bank 2: BBL (Back-End Logic - module level)")
    print("  Bank 3: BUS (Bus Interface - module level)")
    print("  Bank 4: L2  (L2 Cache - module level, shared by 4 cores)")
    
    print("\nGNR (Big cores):")
    print("  Bank 0: IFU  (Instruction Fetch Unit)")
    print("  Bank 1: DCU  (Data Cache Unit)")
    print("  Bank 2: DTLB (Data TLB)")
    print("  Bank 3: ML2  (Mid-Level L2 Cache)")
    print("  Bank 4: PMSB (Power Management State Buffer)")
    
    print("\nKey Differences:")
    print("  - CWF has 4 Atom cores per module; GNR has 1 big core")
    print("  - CWF MEC combines DCU + DTLB functionality")
    print("  - CWF has module-level BBL and BUS banks")
    print("  - CWF L2 is shared across 4 cores; GNR L2 is per-core")
    print("  - GNR has PMSB; CWF does not")
    print("="*80 + "\n")


def decode_mca_bank(register_path, status_value=None):
    """
    CWF-specific MCA bank decoder
    Decode MCA bank information from register path and status value.
    
    Args:
        register_path (str): Full register path from pysvtools
        status_value (int, optional): MCi_STATUS register value
        
    Returns:
        str: Formatted bank information or empty string if bank not identified
    """
    try:
        bank_id = None
        
        # Core banks (0-1) and Module banks (2-4)
        if 'ic_cr_mci' in register_path.lower():
            bank_id = 0
        elif 'mec_cr_mci' in register_path.lower():
            bank_id = 1
        elif 'bbl_cr_mci' in register_path.lower():
            bank_id = 2
        elif 'bus_cr_mci' in register_path.lower():
            bank_id = 3
        elif 'l2_cr_mci' in register_path.lower():
            bank_id = 4
        # Uncore banks
        elif 'cha' in register_path.lower() and 'util.mc_status' in register_path.lower():
            bank_id = 5
        elif 'mcchan' in register_path.lower() or 'imc0_mc' in register_path.lower():
            bank_id = 6
        elif 'b2cmi' in register_path.lower():
            bank_id = 7
        elif 'mse' in register_path.lower() and 'mci_status' in register_path.lower():
            bank_id = 8
        elif 'scf_llc' in register_path.lower():
            bank_id = 9
        elif 'upi' in register_path.lower() or 'kti_mc' in register_path.lower():
            bank_id = 10
        elif 'ubox' in register_path.lower():
            bank_id = 11
        elif 'punit' in register_path.lower() and 'ptpcfsm' in register_path.lower():
            bank_id = 12
        
        if bank_id is not None:
            bank_info = get_bank_info(bank_id)
            if bank_info:
                decoded = f" --> MCA Bank {bank_id}: {bank_info['name']} ({bank_info['full_name']})"
                decoded += f"\n     Scope: {bank_info['scope']} | {bank_info['description']}"
                if bank_info.get('notes'):
                    decoded += f"\n     Note: {bank_info['notes']}"
                return decoded
        
    except Exception as e:
        # Silently fail if decoding fails
        pass
    
    return ""


class MCADecoders:
    """
    CWF-specific MCA decoder manager.
    Single source of truth for all decoder imports.
    
    This class uses direct imports and provides a clean interface to access
    product-specific decoders. If a decoder is not available, it returns None.
    """
    
    def __init__(self):
        """Load all available decoders using direct imports."""
        # MCA Decoders
        self.cha = self._import_decoder('pysvtools.server_ip_debug.cha', 'cha')
        self.llc = None # self._import_decoder('toolext.server_ip_debug.llc', 'llc')
        self.ubox = self._import_decoder('pysvtools.server_ip_debug.ubox', 'ubox')
        self.punit = self._import_decoder('toolext.server_ip_debug.punit', 'punit')
        self.pm = self._import_decoder('pysvtools.server_ip_debug.pm', 'pm')
        
        # Tools
        self.tileview = self._import_module('pysvtools.server_wave_4.tileview')
        self.dimm_info = self._import_module('mc.cwfDimmInfo')
        
        # Debug tools
        self.core_debug = self._import_module('core.debug')
        self.debug_mca = self._import_module('pysvtools.debug_mca')
        
        # Not available for CWF
        self.ccf = None
        self.ula = None
    
    def _import_decoder(self, module_path, class_name):
        """
        Import a decoder class from a module.
        
        Args:
            module_path: Full module path (e.g., 'pysvtools.server_ip_debug.cha')
            class_name: Class name to extract (e.g., 'cha')
        
        Returns:
            Decoder class or None if import fails
        """
        try:
            module = __import__(module_path, fromlist=[class_name])
            decoder = getattr(module, class_name)
            print(f"  {Colors.success('[+]')} Loaded {Colors.BOLD}{class_name}{Colors.RESET} for CWF")
            return decoder
        except ImportError:
            print(f"  {Colors.error('[X]')} {class_name} not available")
            return None
        except Exception as e:
            print(f"  {Colors.error('[X]')} Error loading {class_name}: {e}")
            return None
    
    def _import_module(self, module_path):
        """
        Import a module directly.
        
        Args:
            module_path: Full module path
        
        Returns:
            Module or None if import fails
        """
        try:
            module = __import__(module_path, fromlist=[''])
            module_name = module_path.split('.')[-1]
            print(f"  {Colors.success('[+]')} Loaded {Colors.BOLD}{module_name}{Colors.RESET} for CWF")
            return module
        except ImportError:
            module_name = module_path.split('.')[-1]
            print(f"  {Colors.error('[X]')} {module_name} not available")
            return None
        except Exception as e:
            module_name = module_path.split('.')[-1]
            print(f"  {Colors.error('[X]')} Error loading {module_name}: {e}")
            return None
    
    def get_decoder(self, decoder_name):
        """
        Get a decoder by name.
        
        Args:
            decoder_name: Name of the decoder (e.g., 'cha', 'llc', 'tileview')
        
        Returns:
            Decoder module/class or None if not available
        """
        return getattr(self, decoder_name.lower(), None)
    
    def list_decoders(self):
        """List all available decoders and their status."""
        decoders = {
            'cha': self.cha,
            'ccf': self.ccf,
            'llc': self.llc,
            'ubox': self.ubox,
            'ula': self.ula,
            'punit': self.punit,
            'pm': self.pm,
            'core_debug': self.core_debug,
            'debug_mca': self.debug_mca,
        }
        
        tools = {
            'tileview': self.tileview,
            'dimm_info': self.dimm_info,
        }
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*50}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}  CWF MCA Decoders Status{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*50}{Colors.RESET}")
        for name, decoder in sorted(decoders.items()):
            if decoder is not None:
                print(f"  {Colors.success('[+]')} {name:<15} {Colors.info('Available')}")
            else:
                print(f"  {Colors.error('[X]')} {name:<15} {Colors.warning('Not available')}")
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}  Tools:{Colors.RESET}")
        for name, tool in sorted(tools.items()):
            if tool is not None:
                print(f"  {Colors.success('[+]')} {name:<15} {Colors.info('Available')}")
            else:
                print(f"  {Colors.error('[X]')} {name:<15} {Colors.warning('Not available')}")
        print(f"{Colors.CYAN}{'='*50}{Colors.RESET}\n")


# Alias for backward compatibility
mca_decoders = MCADecoders


def mca_dump(sv, itp, verbose=True):
    """
    CWF-specific MCA dump function
    Dumps all Machine Check Architecture banks for CWF product (Atom cores)
    
    Args:
        sv: pysvtools sv object (socket view)
        verbose (bool): If True, prints detailed register information
        
    Returns:
        tuple: (mcadata dict, pysvdecode dict) - mcadata contains TestName/TestValue lists,
               pysvdecode contains flags for which banks have errors
               
    Dumps the following banks:
    - Bank 0: IC (Instruction Cache - Core-scoped)
    - Bank 1: MEC (Memory Execution Cluster - Core-scoped, combines DCU + DTLB)
    - Bank 2: BBL (Back-End Logic - Module-scoped)
    - Bank 3: BUS (Bus Interface - Module-scoped)
    - Bank 4: L2 (L2 Cache - Module-scoped, shared by 4 cores)
    - Bank 5: CHA (Caching Home Agent)
    - Bank 6: iMC (Integrated Memory Controller)
    - Bank 7-9: B2CMI, MSE, LLC
    - UPI, UBOX, PUNIT
    
    Note: CWF uses Atom cores (4 cores per module), no PMSB bank
    """

    def print_valid(i,a,mc,e,b=63,save=False):
        try:
            if verbose: 
                status_val = i.read()
                print("%s = 0x%x" %(i.path, status_val))
                # Add decoded bank information
                #decoded_info = decode_mca_bank(i.path, status_val)
                #if decoded_info:
                #    print(decoded_info)
            
            if i.bits(b,1): 
                a.append(i)
                mc.append(i)
                
                return True
            else:
                if save: mc.append(i)
                return False
        except:
            #print("Access failed to: {}".format(i.path))
            print("%s = <error reading>" %(i.path))
            e.append(i)
            return False

    a=[] #mcas
    e=[] #errors
    mc=[]
    mcadata = {'TestName':[],	'TestValue':[]}

    sv.sockets.computes.cpu.modules.setaccess('crb') #no halt required

    with itp.device_locker():
        for i in sv.sockets.computes.cpu.modules.cores.mec_cr_mci_status:
            if print_valid(i,a,mc,e):
                for th in i.parent.threads:
                    mc.append(th.mec_cr_mcg_contain)
                    if i.bits(59,1): 
                        mc.append(th.mec_cr_mci_misc)
                if i.bits(58,1): 
                    a.append(i.parent.mec_cr_mci_addr)
                    mc.append(i.parent.mec_cr_mci_addr)
                
        for i in sv.sockets.computes.cpu.modules.bus_cr_mci_status:
            if print_valid(i,a,mc,e):
                if i.bits(58,1): 
                    a.append(i.parent.bus_cr_mci_addr) 
                    mc.append(i.parent.bus_cr_mci_addr)
                if i.bits(59,1):
                    mc.append(i.parent.bus_cr_mci_misc)
        for i in sv.sockets.computes.cpu.modules.bbl_cr_mci_status:
            if print_valid(i,a,mc,e):
                pass
        for i in sv.sockets.computes.cpu.modules.cores.ic_cr_mci_status:
            if print_valid(i,a,mc,e):
                if i.bits(58,1): 
                    a.append(i.parent.ic_cr_mci_addr)
                    mc.append(i.parent.ic_cr_mci_addr)
                if i.bits(59,1):
                    mc.append(i.parent.ic_cr_mci_misc)

        for i in sv.sockets.computes.cpu.modules.l2_cr_mci_status:
            if print_valid(i,a,mc,e):
                if i.bits(58,1): 
                    a.append(i.parent.l2_cr_mci_addr)
                    mc.append(i.parent.l2_cr_mci_addr)
                if i.bits(59,1):
                    mc.append(i.parent.l2_cr_mci_misc)
    for i in sv.sockets.computes.uncore.cha.chas.util.mc_status:
        if print_valid(i,a,mc,e):
            if i.bits(58,1): 
                a.append(i.parent.mc_addr)
            mc.append(i.parent.mc_addr)
            if i.bits(59,1): 
                mc.append(i.parent.mc_misc)
                mc.append(i.parent.mc_misc2)
                mc.append(i.parent.mc_misc3)
    try:
        for i in sv.sockets.computes.uncore.memss.mcs.chs.mcchan.imc0_mc_status:
            if print_valid(i,a,mc,e):
                if i.bits(58,1): 
                    a.append(i.parent.imc0_mc8_addr)
                    mc.append(i.parent.imc0_mc8_addr)
                if i.bits(59,1): 
                    mc.append(i.parent.imc0_mc_misc)
    except:
        for i in sv.sockets.soc.memss.mcs.chs.mcchan.imc0_mc_status:
            if print_valid(i,a,mc,e):
                if i.bits(58,1): 
                    a.append(i.parent.imc0_mc8_addr)
                    mc.append(i.parent.imc0_mc8_addr)
                if i.bits(59,1):
                    mc.append(i.parent.imc0_mc_misc)
    try:
        for i in sv.sockets.computes.uncore.memss.b2cmis.mci_status:
            if print_valid(i,a,mc,e):
                if i.bits(58,1): 
                    a.append(i.parent.mci_addr)
                    mc.append(i.parent.mci_addr)
                if i.bits(59,1):
                    mc.append(i.parent.mci_misc)
    except:
        for i in sv.sockets.soc.memss.b2cmis.mci_status:
            if print_valid(i,a,mc,e):
                if i.bits(58,1): 
                    a.append(i.parent.mci_addr)
                    mc.append(i.parent.mci_addr)
                if i.bits(59,1):
                    mc.append(i.parent.mci_misc)
    try:
        for i in sv.sockets.computes.uncore.memss.mcs.chs.mse.mse_mci_status:
            if print_valid(i,a,mc,e):
                if i.bits(58,1): 
                    a.append(i.parent.mse_mci_addr)
                    mc.append(i.parent.mse_mci_addr)
                if i.bits(59,1):
                    mc.append(i.parent.mci_misc)
    except:
        for i in sv.sockets.soc.memss.mcs.chs.mse.mse_mci_status:
            if print_valid(i,a,mc,e):
                if i.bits(58,1): 
                    a.append(i.parent.mse_mci_addr)
                    mc.append(i.parent.mse_mci_addr)
                if i.bits(59,1):
                    mc.append(i.parent.mci_misc)
    for i in sv.sockets.computes.uncore.scf.scf_llc.scf_llcs.mci_status:
        if print_valid(i,a,mc,e):
            if i.bits(58,1): 
                a.append(i.parent.mci_addr)
                mc.append(i.parent.mci_addr)
            if i.bits(59,1):
                mc.append(i.parent.mci_misc)
    try:
        for i in sv.sockets.ios.uncore.upi.upis.upi_regs.kti_mc_st:
            if print_valid(i,a,mc,e):
                if i.bits(58,1): 
                    a.append(i.parent.kti_mc_ad)
                    mc.append(i.parent.kti_mc_ad)
    except:
        print('WARNING: skipping kti, not working - sv.sockets.ios.uncore.upi.upis.upi_regs.kti_mc_st')
    try:
        for i in sv.sockets.io0.uncore.ubox.ncevents.ncevents_cr_ubox_mci_status:
            print_valid(i,a,mc,e)
        for i in sv.sockets.io0.uncore.ubox.ncevents.ierrloggingreg:
            print_valid(i,a,mc,e,b=16)
        for i in sv.sockets.io0.uncore.ubox.ncevents.ncuevdbgsts:
            mc.append(i)
        for i in sv.sockets.io0.uncore.ubox.ncevents.ncevents_cr_ubox_mci_ctl:
            mc.append(i)
        for i in sv.sockets.io0.uncore.ubox.ncevents.mcerrloggingreg:
            mc.append(i)
        for i in sv.sockets.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg:
            mc.append(i)
    except:
        print('WARNING: skipping ubox, not working - sv.sockets.io0.uncore.ubox.ncevents.ncevents_cr_ubox_mci_status')
    try:
        for i in sv.sockets.computes.uncore.punit.ptpcfsms.ptpcfsms.mc_status:
            if print_valid(i,a,mc,e):
                if i.bits(59,1): 
                    a.append(i.parent.mc_misc)
                    mc.append(i.parent.mc_misc)
                a.append(i.parent.parent.parent.parent.pcodeio_map.io_firmware_mca_command)
                mc.append(i.parent.parent.parent.parent.pcodeio_map.io_firmware_mca_command)
        for i in sv.sockets.ios.uncore.punit.ptpcfsms.ptpcfsms.mc_status:
            if print_valid(i,a,mc,e):
                if i.bits(59,1): 
                    a.append(i.parent.mc_misc)
                    mc.append(i.parent.mc_misc)
                a.append(i.parent.parent.parent.parent.pcodeio_map.io_firmware_mca_command)
                mc.append(i.parent.parent.parent.parent.pcodeio_map.io_firmware_mca_command)

    except:
        print('WARNING: skipping punit, not working - sv.sockets.computes.uncore.punit.ptpcfsms.ptpcfsms.mc_status')
        
    pysvdecode = {'cha':False, 'llc':False, 'ubox':False, 'punit':False, 'pm':False, 'core':False  }
    if mc != []:
        for i in mc:
            mcadata['TestName'].append("%s" % i.path)
            mcadata['TestValue'].append("0x%x" % i.get_value())
    if a != []:
        print('\nFOUND VALID MCA')
        print('='*80)
        for i in a:
            status_val = i.get_value()
            print("%s = 0x%x" %(i.path, status_val))
            # Add decoded bank information for summary
            decoded_info = decode_mca_bank(i.path, status_val)
            if decoded_info:
                print(decoded_info)
            print('-'*80)
            if 'cha' in i.path: pysvdecode['cha'] = True
            if 'scf_llc' in i.path: pysvdecode['llc'] = True
            if 'ubox' in i.path: pysvdecode['ubox'] = True
            if 'punit' in i.path: pysvdecode['punit'] = True
            if 'punit' in i.path: pysvdecode['pm'] = True
            if 'cpu.module' in i.path: pysvdecode['core'] = True
            if verbose: print("%s \n"%i.show())
    else:
        print('did not find valid MCA')
    
    if e != []:
        print('errors found during mca_dump. see above')
        for i in e:
            print(f"  Error accessing: {i.path if hasattr(i, 'path') else i}")
    
    sv.sockets.computes.cpu.modules.setaccess('default') #restore
    return mcadata, pysvdecode


if __name__ == '__main__':
    # Example usage
    print_bank_table()
    
    print("\nExample: Decoding Bank 0 (IC):")
    print(format_bank_error(0, module_id=5, core_id=2))
    
    print("\nExample: Decoding Bank 1 (MEC) with STATUS:")
    status = 0xBE00000000800150  # Example valid uncorrected error
    print(format_bank_error(1, status_value=status, module_id=3, core_id=1))
    
    print("\nExample: Get all Core-scoped banks:")
    core_banks = get_core_banks()
    for bank_id, bank in core_banks.items():
        print(f"  Bank {bank_id}: {bank['name']} - {bank['description']}")
    
    print("\nExample: Get all Module-scoped banks:")
    module_banks = get_module_banks()
    for bank_id, bank in module_banks.items():
        print(f"  Bank {bank_id}: {bank['name']} - {bank['description']}")
    
    # Show comparison with GNR
    compare_with_gnr()
