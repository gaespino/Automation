"""
DMR (Diamond Rapids) MCA Bank Definitions and Decoder
Author: gaespino
Last update: 12/11/25

Provides comprehensive MCA bank information for DMR product including:
- Bank ID to name mapping
- Scope information (Core, Module, CBB, IMH)
- Physical instance counts
- Merged bank information
- Decoding utilities
"""

# DMR MCA Bank Definitions
# Based on DMR architecture with CBB (Core Building Block) and IMH (Integrated Memory Hub) domains
# DMR uses BigCore (PNC cores), not Atom cores - one thread per core (no SMT/HT)

DMR_MCA_BANKS = {
    # Core-scoped banks (0-2)
    0: {
        'name': 'IFU',
        'full_name': 'Instruction Fetch Unit',
        'scope': 'Core',
        'domain': 'CBB',
        'merged': False,
        'instances': '1 per core',
        'description': 'Instruction Fetch Unit errors',
        'register_path': 'sv.socket0.cbbs.computes.modules.cores.ifu_cr_mc0_status',
        'notes': 'BigCore (PNC) implementation, one thread per core'
    },
    1: {
        'name': 'DCU',
        'full_name': 'Data Cache Unit',
        'scope': 'Core',
        'domain': 'CBB',
        'merged': False,
        'instances': '1 per core',
        'description': 'Data Cache Unit errors',
        'register_path': 'sv.socket0.cbbs.computes.modules.cores.dcu_cr_mc1_status',
        'notes': 'BigCore (PNC) implementation'
    },
    2: {
        'name': 'DTLB',
        'full_name': 'Data Translation Lookaside Buffer',
        'scope': 'Core',
        'domain': 'CBB',
        'merged': False,
        'instances': '1 per core',
        'description': 'Data TLB errors',
        'register_path': 'sv.socket0.cbbs.computes.modules.cores.dtlb_cr_mc2_status',
        'notes': 'BigCore (PNC) implementation'
    },
    
    # Module-scoped banks (3)
    3: {
        'name': 'MLC',
        'full_name': 'Module Level Cache',
        'scope': 'Module',
        'domain': 'CBB',
        'merged': False,
        'instances': '1 per module',
        'description': 'Module Level Cache (L2) errors',
        'register_path': 'sv.socket0.cbbs.computes.modules.ml2_cr_mc3_status',
        'notes': 'Module contains BigCore pairs (DCMs formed from pairs of PNC cores)'
    },
    
    # CBB-scoped banks (4-8)
    4: {
        'name': 'PUNIT_CBB',
        'full_name': 'Power Management Unit (CBB)',
        'scope': 'CBB',
        'domain': 'CBB',
        'merged': False,
        'instances': '1 per CBB',
        'description': 'CBB Power Management Unit errors',
        'register_path': 'sv.socket0.cbbs.uncore.punit'
    },
    5: {
        'name': 'NCU',
        'full_name': 'Node Control Unit (sNCU)',
        'scope': 'CBB',
        'domain': 'CBB',
        'merged': False,
        'instances': '1 per CBB',
        'description': 'Node Control Unit (merging agent) errors',
        'register_path': 'sv.socket0.cbbs.uncore.ncu'
    },
    6: {
        'name': 'CCF',
        'full_name': 'Caching/Coherency Fabric',
        'scope': 'CBB',
        'domain': 'CBB',
        'merged': True,
        'instances': '32 per CBB',
        'description': 'Caching and Coherency Fabric errors (merged)',
        'register_path': 'sv.socket0.cbbs.uncore.ccf'
    },
    7: {
        'name': 'D2D_CBB',
        'full_name': 'Die-to-Die Interconnect (CBB)',
        'scope': 'CBB',
        'domain': 'CBB',
        'merged': True,
        'instances': '8 per CBB',
        'description': 'Die-to-Die interconnect errors (merged)',
        'register_path': 'sv.socket0.cbbs.uncore.d2d'
    },
    8: {
        'name': 'SPARE_CBB',
        'full_name': 'Reserved (CBB)',
        'scope': 'CBB',
        'domain': 'CBB',
        'merged': False,
        'instances': 'Reserved',
        'description': 'Reserved for future use',
        'register_path': None
    },
    
    # IMH-scoped banks (9-31)
    9: {
        'name': 'SPARE_IMH_9',
        'full_name': 'Reserved (IMH)',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': False,
        'instances': 'Reserved',
        'description': 'Reserved for future use',
        'register_path': None
    },
    10: {
        'name': 'RASIP',
        'full_name': 'RAS Infrastructure (CXL/PCIe)',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': False,
        'instances': '1 per IMH',
        'description': 'RAS Infrastructure, CXL/PCIe errors',
        'register_path': 'sv.socket0.imhs.uncore.rasip'
    },
    11: {
        'name': 'PUNIT_IMH',
        'full_name': 'Power Management Unit (IMH)',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '1 per IMH',
        'description': 'IMH Power Management Unit errors (merged)',
        'register_path': 'sv.socket0.imhs.uncore.punit'
    },
    12: {
        'name': 'HA_MVF',
        'full_name': 'Home Agent/Memory VF',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '16 per IMH',
        'description': 'Home Agent/Memory Virtual Function errors (merged)',
        'register_path': 'sv.socket0.imhs.uncore.ha'
    },
    13: {
        'name': 'HSF',
        'full_name': 'High Speed Fabric',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '16 per IMH',
        'description': 'High Speed Fabric errors (merged)',
        'register_path': 'sv.socket0.imhs.uncore.hsf'
    },
    14: {
        'name': 'SCA',
        'full_name': 'System Cache Agent',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '16 per IMH',
        'description': 'System Cache Agent errors (merged)',
        'register_path': 'sv.socket0.imhs.uncore.sca'
    },
    15: {
        'name': 'D2D_ULA',
        'full_name': 'Die-to-Die ULA',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '8 per IMH',
        'description': 'Die-to-Die ULA errors (merged)',
        'register_path': 'sv.socket0.imhs.uncore.d2d'
    },
    16: {
        'name': 'MSE',
        'full_name': 'Memory Subsystem Error',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '16 per IMH',
        'description': 'Memory Subsystem errors (merged)',
        'register_path': 'sv.socket0.imhs.uncore.memss.mse'
    },
    17: {
        'name': 'IOCACHE',
        'full_name': 'IO Cache Agent',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '16 per IMH',
        'description': 'IO Cache Agent errors (merged)',
        'register_path': 'sv.socket0.imhs.uncore.iocache'
    },
    18: {
        'name': 'UXI',
        'full_name': 'Universal Interconnect',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '2 per IMH',
        'description': 'Universal Interconnect errors (merged)',
        'register_path': 'sv.socket0.imhs.uncore.uxi'
    },
    19: {
        'name': 'MCCHAN0',
        'full_name': 'DDR Memory Channel 0',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '2 per IMH (merged sub-channels)',
        'description': 'DDR Channel 0 errors (merged sub-channels)',
        'register_path': 'sv.socket0.imhs.uncore.memss.mcs.chs[0]',
        'sub_channel_info': 'MCi_MISC.extra_error_info[40]'
    },
    20: {
        'name': 'MCCHAN1',
        'full_name': 'DDR Memory Channel 1',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '2 per IMH (merged sub-channels)',
        'description': 'DDR Channel 1 errors (merged sub-channels)',
        'register_path': 'sv.socket0.imhs.uncore.memss.mcs.chs[1]',
        'sub_channel_info': 'MCi_MISC.extra_error_info[40]'
    },
    21: {
        'name': 'MCCHAN2',
        'full_name': 'DDR Memory Channel 2',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '2 per IMH (merged sub-channels)',
        'description': 'DDR Channel 2 errors (merged sub-channels)',
        'register_path': 'sv.socket0.imhs.uncore.memss.mcs.chs[2]',
        'sub_channel_info': 'MCi_MISC.extra_error_info[40]'
    },
    22: {
        'name': 'MCCHAN3',
        'full_name': 'DDR Memory Channel 3',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '2 per IMH (merged sub-channels)',
        'description': 'DDR Channel 3 errors (merged sub-channels)',
        'register_path': 'sv.socket0.imhs.uncore.memss.mcs.chs[3]',
        'sub_channel_info': 'MCi_MISC.extra_error_info[40]'
    },
    23: {
        'name': 'MCCHAN4',
        'full_name': 'DDR Memory Channel 4',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '2 per IMH (merged sub-channels)',
        'description': 'DDR Channel 4 errors (merged sub-channels)',
        'register_path': 'sv.socket0.imhs.uncore.memss.mcs.chs[4]',
        'sub_channel_info': 'MCi_MISC.extra_error_info[40]'
    },
    24: {
        'name': 'MCCHAN5',
        'full_name': 'DDR Memory Channel 5',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '2 per IMH (merged sub-channels)',
        'description': 'DDR Channel 5 errors (merged sub-channels)',
        'register_path': 'sv.socket0.imhs.uncore.memss.mcs.chs[5]',
        'sub_channel_info': 'MCi_MISC.extra_error_info[40]'
    },
    25: {
        'name': 'MCCHAN6',
        'full_name': 'DDR Memory Channel 6',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '2 per IMH (merged sub-channels)',
        'description': 'DDR Channel 6 errors (merged sub-channels)',
        'register_path': 'sv.socket0.imhs.uncore.memss.mcs.chs[6]',
        'sub_channel_info': 'MCi_MISC.extra_error_info[40]'
    },
    26: {
        'name': 'MCCHAN7',
        'full_name': 'DDR Memory Channel 7',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': True,
        'instances': '2 per IMH (merged sub-channels)',
        'description': 'DDR Channel 7 errors (merged sub-channels)',
        'register_path': 'sv.socket0.imhs.uncore.memss.mcs.chs[7]',
        'sub_channel_info': 'MCi_MISC.extra_error_info[40]'
    },
    27: {
        'name': 'SPARE_IMH_27',
        'full_name': 'Reserved (IMH)',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': False,
        'instances': 'Reserved',
        'description': 'Reserved for future use',
        'register_path': None
    },
    28: {
        'name': 'SPARE_IMH_28',
        'full_name': 'Reserved (IMH)',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': False,
        'instances': 'Reserved',
        'description': 'Reserved for future use',
        'register_path': None
    },
    29: {
        'name': 'SPARE_IMH_29',
        'full_name': 'Reserved (IMH)',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': False,
        'instances': 'Reserved',
        'description': 'Reserved for future use',
        'register_path': None
    },
    30: {
        'name': 'SPARE_IMH_30',
        'full_name': 'Reserved (IMH)',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': False,
        'instances': 'Reserved',
        'description': 'Reserved for future use',
        'register_path': None
    },
    31: {
        'name': 'SPARE_IMH_31',
        'full_name': 'Reserved (IMH)',
        'scope': 'IMH',
        'domain': 'IMH',
        'merged': False,
        'instances': 'Reserved',
        'description': 'Reserved for future use',
        'register_path': None
    }
}

# Domain mapping information
DMR_DOMAIN_INFO = {
    'CBB': {
        'name': 'Core Building Block',
        'bank_range': (0, 8),
        'description': 'Compute domain with cores, modules, and coherency fabric'
    },
    'IMH': {
        'name': 'Integrated Memory Hub',
        'bank_range': (9, 31),
        'description': 'Memory and IO domain with memory controllers and interconnects',
        'instances': {
            'IMH0': 'Domain 0 (even-numbered modules)',
            'IMH1': 'Domain 1 (odd-numbered modules)'
        }
    }
}

# Additional notes for DMR
DMR_NOTES = {
    'core_architecture': 'DMR uses BigCore (PNC cores), not Atom cores - one thread per core (no SMT/HT)',
    'module_concept': 'Modules contain BigCore pairs; DCMs (Dual-Core Modules) formed from pairs of PNC cores',
    'threading': 'No SMT/hyperthreading - one thread per core',
    'merged_banks': 'Merged banks aggregate multiple physical instances into one logical bank',
    'merge_registers': 'CR_BANKMERGE_x_ERRLOG and AGGR registers manage merge info',
    'mc_subchannel': 'DDR MC banks (19-26) merge two sub-channels; sub-channel index in MCi_MISC.extra_error_info[40]',
    'fullbank_msg': 'Some IPs (UBOX, UBR, SCMS) use FULLBANK_MCA_MSG without dedicated MCA bank',
    'domain_mapping': 'IMH0 → Domain 0, IMH1 → Domain 1; even modules → D0, odd modules → D1',
    'cbb_domain': 'CBB (Core Building Block) contains compute resources with BigCore modules',
    'imh_domain': 'IMH (Integrated Memory Hub) is separate domain for memory and IO'
}


def get_bank_info(bank_id):
    """
    Get detailed information about a specific MCA bank.
    
    Args:
        bank_id (int): MCA bank ID (0-31)
        
    Returns:
        dict: Bank information or None if bank not found
    """
    return DMR_MCA_BANKS.get(bank_id)


def get_bank_name(bank_id):
    """
    Get the short name of an MCA bank.
    
    Args:
        bank_id (int): MCA bank ID (0-31)
        
    Returns:
        str: Bank name or 'UNKNOWN'
    """
    bank = DMR_MCA_BANKS.get(bank_id)
    return bank['name'] if bank else f'UNKNOWN_BANK_{bank_id}'


def get_bank_full_name(bank_id):
    """
    Get the full descriptive name of an MCA bank.
    
    Args:
        bank_id (int): MCA bank ID (0-31)
        
    Returns:
        str: Full bank name
    """
    bank = DMR_MCA_BANKS.get(bank_id)
    return bank['full_name'] if bank else f'Unknown Bank {bank_id}'


def decode_bank_error(bank_id, status_value=None, misc_value=None):
    """
    Decode MCA bank error with additional context.
    
    Args:
        bank_id (int): MCA bank ID
        status_value (int, optional): MCi_STATUS register value
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
        'domain': bank['domain'],
        'merged': bank['merged'],
        'instances': bank['instances'],
        'description': bank['description']
    }
    
    # Add sub-channel information for memory channel banks
    if 19 <= bank_id <= 26 and misc_value is not None:
        sub_channel = (misc_value >> 40) & 0x1
        result['sub_channel'] = sub_channel
        result['sub_channel_note'] = f'Error in sub-channel {sub_channel}'
    
    return result


def format_bank_error(bank_id, register_path='', status_value=None):
    """
    Format a human-readable MCA bank error message.
    
    Args:
        bank_id (int): MCA bank ID
        register_path (str): Full register path
        status_value (int, optional): MCi_STATUS value
        
    Returns:
        str: Formatted error message
    """
    bank = get_bank_info(bank_id)
    if not bank:
        return f'MCA Bank {bank_id}: UNKNOWN'
    
    msg = f"MCA Bank {bank_id}: {bank['name']} ({bank['full_name']})\n"
    msg += f"  Scope: {bank['scope']} | Domain: {bank['domain']}"
    
    if bank['merged']:
        msg += f" | MERGED ({bank['instances']})"
    
    msg += f"\n  Description: {bank['description']}"
    
    if register_path:
        msg += f"\n  Register: {register_path}"
    
    if status_value is not None:
        msg += f"\n  STATUS: 0x{status_value:016x}"
    
    return msg


def get_banks_by_domain(domain):
    """
    Get all banks for a specific domain.
    
    Args:
        domain (str): 'CBB' or 'IMH'
        
    Returns:
        dict: Banks in the specified domain
    """
    return {k: v for k, v in DMR_MCA_BANKS.items() if v['domain'] == domain}


def get_banks_by_scope(scope):
    """
    Get all banks for a specific scope.
    
    Args:
        scope (str): 'Core', 'Module', 'CBB', or 'IMH'
        
    Returns:
        dict: Banks in the specified scope
    """
    return {k: v for k, v in DMR_MCA_BANKS.items() if v['scope'] == scope}


def get_merged_banks():
    """
    Get all merged MCA banks.
    
    Returns:
        dict: All merged banks
    """
    return {k: v for k, v in DMR_MCA_BANKS.items() if v['merged']}


def print_bank_table():
    """
    Print a formatted table of all MCA banks.
    """
    print("\n" + "="*100)
    print("DMR (Diamond Rapids) MCA Bank Table")
    print("="*100)
    print(f"{'Bank':<6}{'Name':<15}{'Scope':<10}{'Domain':<8}{'Merged':<8}{'Instances':<25}{'Description':<30}")
    print("-"*100)
    
    for bank_id in sorted(DMR_MCA_BANKS.keys()):
        bank = DMR_MCA_BANKS[bank_id]
        merged = 'Yes' if bank['merged'] else 'No'
        print(f"{bank_id:<6}{bank['name']:<15}{bank['scope']:<10}{bank['domain']:<8}{merged:<8}{bank['instances']:<25}{bank['description'][:30]:<30}")
    
    print("="*100)
    print("\nDomain Information:")
    for domain, info in DMR_DOMAIN_INFO.items():
        print(f"  {domain}: {info['name']} (Banks {info['bank_range'][0]}-{info['bank_range'][1]})")
        print(f"      {info['description']}")
    
    print("\nNotes:")
    for key, note in DMR_NOTES.items():
        print(f"  - {note}")
    print()


def compare_with_gnr():
    """
    Print comparison between DMR and GNR MCA bank architectures.
    """
    print("\n" + "="*100)
    print("DMR vs GNR MCA Bank Architecture Comparison")
    print("="*100)
    
    print("\n" + "-"*100)
    print("CORE-SCOPED BANKS (0-3)")
    print("-"*100)
    
    print("\nDMR (Diamond Rapids) - BigCore (PNC):")
    print("  Bank 0: IFU   (Instruction Fetch Unit)")
    print("  Bank 1: DCU   (Data Cache Unit)")
    print("  Bank 2: DTLB  (Data TLB)")
    print("  Bank 3: MLC   (Module Level Cache - L2)")
    print("  Scope: Per core, one thread per core (no SMT/HT)")
    print("  Note: DCMs (Dual-Core Modules) formed from pairs of PNC BigCores")
    
    print("\nGNR (Granite Rapids) - Big Core:")
    print("  Bank 0: IFU   (Instruction Fetch Unit)")
    print("  Bank 1: DCU   (Data Cache Unit)")
    print("  Bank 2: DTLB  (Data TLB)")
    print("  Bank 3: ML2   (Mid-Level L2 Cache)")
    print("  Bank 4: PMSB  (Power Management State Buffer)")
    print("  Scope: Per core, supports 2 threads (hyperthreading/SMT)")
    
    print("\n" + "-"*100)
    print("COMPUTE/CBB BANKS (4-8)")
    print("-"*100)
    
    print("\nDMR (CBB Domain):")
    print("  Bank 4: PUNIT_CBB (Power Management Unit - CBB)")
    print("  Bank 5: NCU       (Node Control Unit - merging agent)")
    print("  Bank 6: CCF       (Caching/Coherency Fabric) - MERGED: 32 instances")
    print("  Bank 7: D2D_CBB   (Die-to-Die Interconnect) - MERGED: 8 instances")
    print("  Bank 8: SPARE")
    print("  Architecture: CBB (Core Building Block) contains compute resources")
    
    print("\nGNR (Uncore):")
    print("  Bank 5: CHA   (Caching and Home Agent) - per LLC slice")
    print("  Bank 9: LLC   (Last Level Cache in SCF)")
    print("  Bank 12: PUNIT (Power Control Unit)")
    print("  Architecture: Traditional uncore with CHA per LLC slice")
    
    print("\n" + "-"*100)
    print("MEMORY SUBSYSTEM BANKS")
    print("-"*100)
    
    print("\nDMR (IMH Domain - Banks 10-26):")
    print("  Bank 10: RASIP    (RAS Infrastructure)")
    print("  Bank 11: PUNIT_IMH (Power Unit - IMH) - MERGED")
    print("  Bank 12: HA/MVF    (Home Agent/Memory VF) - MERGED: 16 instances")
    print("  Bank 13: HSF       (High Speed Fabric) - MERGED: 16 instances")
    print("  Bank 14: SCA       (System Cache Agent) - MERGED: 16 instances")
    print("  Bank 16: MSE       (Memory Subsystem Error) - MERGED: 16 instances")
    print("  Bank 18: UXI       (Universal Interconnect) - MERGED: 2 instances")
    print("  Banks 19-26: MCCHAN0-7 (DDR Channels) - MERGED: 2 sub-channels each")
    print("  Architecture: Separate IMH (Integrated Memory Hub) domain")
    print("  Domain Mapping: IMH0 → Domain 0, IMH1 → Domain 1")
    
    print("\nGNR (Integrated):")
    print("  Bank 6: IMC    (Integrated Memory Controller)")
    print("  Bank 7: B2CMI  (Box to Channel Memory Interface)")
    print("  Bank 8: MSE    (Memory Subsystem Error)")
    print("  Bank 13: M2MEM (Mesh to Memory)")
    print("  Architecture: Memory integrated in main uncore, no separate domain")
    
    print("\n" + "-"*100)
    print("INTERCONNECT BANKS")
    print("-"*100)
    
    print("\nDMR:")
    print("  Bank 7: D2D_CBB  (Die-to-Die in CBB)")
    print("  Bank 15: D2D_ULA (Die-to-Die ULA in IMH)")
    print("  Bank 18: UXI     (Universal Interconnect)")
    print("  Architecture: Multiple D2D instances for CBB-IMH and tile-tile")
    
    print("\nGNR:")
    print("  Bank 10: UPI (Ultra Path Interconnect)")
    print("  Architecture: UPI for socket-to-socket communication")
    
    print("\n" + "-"*100)
    print("IO/SYSTEM BANKS")
    print("-"*100)
    
    print("\nDMR:")
    print("  Bank 10: RASIP   (RAS Infrastructure, CXL/PCIe)")
    print("  Bank 17: IOCACHE (IO Cache Agent)")
    print("  UBOX: Uses FULLBANK_MCA_MSG (no dedicated bank)")
    
    print("\nGNR:")
    print("  Bank 11: UBOX (System Configuration Controller)")
    print("  Bank 15: IIO  (Integrated IO - PCIe)")
    
    print("\n" + "="*100)
    print("KEY ARCHITECTURAL DIFFERENCES")
    print("="*100)
    
    print("\n1. DOMAIN ARCHITECTURE:")
    print("   DMR: Dual-domain (CBB + IMH) with 32 total banks")
    print("   GNR: Single unified domain with 16+ banks")
    
    print("\n2. CORE TYPE:")
    print("   DMR: BigCore (PNC cores), one thread per core, no SMT/HT")
    print("   GNR: Big cores (P-cores) with hyperthreading (2 threads per core)")
    
    print("\n3. MODULE ARCHITECTURE:")
    print("   DMR: DCMs (Dual-Core Modules) formed from pairs of PNC BigCores")
    print("   GNR: No module concept, individual cores")
    
    print("\n4. MERGED BANKS:")
    print("   DMR: Extensive use of merged banks (CCF, HA, HSF, SCA, D2D, MSE, etc.)")
    print("   GNR: Minimal merging, mostly individual banks per instance")
    
    print("\n5. MEMORY ARCHITECTURE:")
    print("   DMR: Separate IMH domain with 8 DDR channels (banks 19-26)")
    print("   DMR: Each channel merges 2 sub-channels")
    print("   GNR: Integrated memory controllers in main uncore")
    
    print("\n6. POWER MANAGEMENT:")
    print("   DMR: Separate PUNIT banks for CBB (bank 4) and IMH (bank 11)")
    print("   DMR: No PMSB (BigCore PNC without SMT doesn't need PMSB)")
    print("   GNR: PMSB per core (bank 4), unified PUNIT (bank 12)")
    
    print("\n6. COHERENCY:")
    print("   DMR: CCF (Caching/Coherency Fabric) bank 6, merged 32 instances")
    print("   GNR: CHA (Caching and Home Agent) bank 5, per LLC slice")
    
    print("\n7. INTERCONNECT:")
    print("   DMR: D2D for die-to-die + UXI for universal interconnect")
    print("   GNR: UPI for socket-to-socket")
    
    print("\n8. BANK UTILIZATION:")
    print("   DMR: Uses banks 0-26, banks 27-31 reserved")
    print("   GNR: Uses banks 0-15+, more compact")
    
    print("\n9. INSTANCE TRACKING:")
    print("   DMR: CR_BANKMERGE_x_ERRLOG registers track merged instance info")
    print("   GNR: Direct per-instance reporting in most cases")
    
    print("\n10. THREADING:")
    print("   DMR: One thread per BigCore (PNC), no SMT/HT")
    print("   GNR: Two threads per core (SMT/HT enabled)")
    
    print("\n" + "="*100)
    print("MIGRATION CONSIDERATIONS (GNR → DMR)")
    print("="*100)
    
    print("\n- Bank 0-3 (Core banks): Similar naming but DMR has no SMT/HT")
    print("- Bank 4: PUNIT_CBB in DMR vs PMSB in GNR - DMR doesn't need PMSB")
    print("- Bank 5: NCU in DMR vs CHA in GNR - completely different")
    print("- Bank 6+: Completely different mapping")
    print("- Memory: Banks 19-26 in DMR vs Bank 6 in GNR")
    print("- Must account for merged banks in DMR")
    print("- Domain awareness required (CBB vs IMH)")
    print("- Different register paths and error reporting")
    
    print("\n" + "="*100 + "\n")


if __name__ == '__main__':
    # Example usage
    print_bank_table()
    
    print("\nExample: Decoding Bank 6 (CCF):")
    print(format_bank_error(6))
    
    print("\nExample: Decoding Bank 19 (MCCHAN0) with sub-channel info:")
    decoded = decode_bank_error(19, misc_value=0x1000000000)
    for key, value in decoded.items():
        print(f"  {key}: {value}")
    
    # Show comparison with GNR
    compare_with_gnr()
