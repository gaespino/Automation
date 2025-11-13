"""
GNR (Granite Rapids) MCA Bank Definitions and Decoder
Author: gaespino
Last update: 12/11/25

Provides comprehensive MCA bank information for GNR product including:
- Bank ID to name mapping
- Scope information (Core, Socket, CHA, Memory)
- Physical instance counts
- Decoding utilities
"""

# GNR MCA Bank Definitions
# Based on GNR/SPR architecture with big cores

GNR_MCA_BANKS = {
    # Core-scoped banks (0-3)
    0: {
        'name': 'IFU',
        'full_name': 'Instruction Fetch Unit',
        'scope': 'Core',
        'merged': False,
        'instances': '1 per thread',
        'description': 'Instruction Fetch Unit errors',
        'register_path': 'sv.sockets.computes.cpu.cores.threads.ifu_cr_mc0_status'
    },
    1: {
        'name': 'DCU',
        'full_name': 'Data Cache Unit',
        'scope': 'Core',
        'merged': False,
        'instances': '1 per thread',
        'description': 'Data Cache Unit (L1 Data Cache) errors',
        'register_path': 'sv.sockets.computes.cpu.cores.threads.dcu_cr_mc1_status'
    },
    2: {
        'name': 'DTLB',
        'full_name': 'Data Translation Lookaside Buffer',
        'scope': 'Core',
        'merged': False,
        'instances': '1 per thread',
        'description': 'Data TLB errors',
        'register_path': 'sv.sockets.computes.cpu.cores.dtlb_cr_mc2_status'
    },
    3: {
        'name': 'ML2',
        'full_name': 'Mid-Level Cache L2',
        'scope': 'Core',
        'merged': False,
        'instances': '1 per core',
        'description': 'L2 Cache errors',
        'register_path': 'sv.sockets.computes.cpu.cores.ml2_cr_mc3_status'
    },
    
    # Uncore banks (4+)
    4: {
        'name': 'PMSB',
        'full_name': 'Power Management State Buffer',
        'scope': 'Core',
        'merged': False,
        'instances': '1 per core',
        'description': 'Power Management State Buffer errors',
        'register_path': 'sv.sockets.computes.uncore.core_pmsb.core_pmsbs.core_pmsb_instance.pmsb_top.pma_core.error_report'
    },
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
        'description': 'UPI (formerly QPI/KTI) link errors',
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
        'name': 'PCU',
        'full_name': 'Power Control Unit (Legacy)',
        'scope': 'Socket',
        'merged': False,
        'instances': '1 per socket',
        'description': 'Legacy PCU errors (use PUNIT for newer systems)',
        'register_path': None
    },
    15: {
        'name': 'IIO',
        'full_name': 'Integrated IO',
        'scope': 'IO',
        'merged': False,
        'instances': 'Variable per socket',
        'description': 'PCIe root complex and IIO stack errors',
        'register_path': 'sv.sockets.ios.uncore.iio'
    }
}

# Additional GNR-specific information
GNR_NOTES = {
    'core_architecture': 'GNR uses big core (Golden Cove/Raptor Cove) architecture',
    'threading': 'Each core supports 2 threads (hyperthreading)',
    'llc_distribution': 'LLC is distributed across CHA slices',
    'memory_channels': 'Variable memory channels depending on SKU (typically 8 or 12 channels)',
    'upi_links': 'Variable UPI links (typically 4-6) for multi-socket configurations',
    'cha_mapping': 'CHA count matches LLC slice count and varies by SKU'
}

# Common GNR configurations
GNR_CONFIGS = {
    'XCC': {
        'name': 'eXtreme Core Count',
        'cores': 'Up to 128',
        'cha_count': 'Up to 120',
        'memory_channels': 12,
        'upi_links': 6
    },
    'MCC': {
        'name': 'Medium Core Count',
        'cores': 'Up to 86',
        'cha_count': 'Up to 80',
        'memory_channels': 8,
        'upi_links': 4
    },
    'LCC': {
        'name': 'Low Core Count',
        'cores': 'Up to 64',
        'cha_count': 'Up to 60',
        'memory_channels': 8,
        'upi_links': 4
    }
}


def get_bank_info(bank_id):
    """
    Get detailed information about a specific MCA bank.
    
    Args:
        bank_id (int): MCA bank ID
        
    Returns:
        dict: Bank information or None if bank not found
    """
    return GNR_MCA_BANKS.get(bank_id)


def get_bank_name(bank_id):
    """
    Get the short name of an MCA bank.
    
    Args:
        bank_id (int): MCA bank ID
        
    Returns:
        str: Bank name or 'UNKNOWN'
    """
    bank = GNR_MCA_BANKS.get(bank_id)
    return bank['name'] if bank else f'UNKNOWN_BANK_{bank_id}'


def get_bank_full_name(bank_id):
    """
    Get the full descriptive name of an MCA bank.
    
    Args:
        bank_id (int): MCA bank ID
        
    Returns:
        str: Full bank name
    """
    bank = GNR_MCA_BANKS.get(bank_id)
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
    msg += f"  Scope: {bank['scope']} | Instances: {bank['instances']}"
    
    if bank['merged']:
        msg += " | MERGED"
    
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
        scope (str): 'Core', 'Uncore', 'IO', or 'Socket'
        
    Returns:
        dict: Banks in the specified scope
    """
    return {k: v for k, v in GNR_MCA_BANKS.items() if v['scope'] == scope}


def print_bank_table():
    """
    Print a formatted table of all MCA banks.
    """
    print("\n" + "="*100)
    print("GNR (Granite Rapids) MCA Bank Table")
    print("="*100)
    print(f"{'Bank':<6}{'Name':<12}{'Scope':<10}{'Merged':<8}{'Instances':<22}{'Description':<40}")
    print("-"*100)
    
    for bank_id in sorted(GNR_MCA_BANKS.keys()):
        bank = GNR_MCA_BANKS[bank_id]
        merged = 'Yes' if bank['merged'] else 'No'
        desc = bank['description'][:38]
        print(f"{bank_id:<6}{bank['name']:<12}{bank['scope']:<10}{merged:<8}{bank['instances']:<22}{desc:<40}")
    
    print("="*100)
    print("\nArchitecture Notes:")
    for key, note in GNR_NOTES.items():
        print(f"  - {note}")
    
    print("\nCommon SKU Configurations:")
    for sku, config in GNR_CONFIGS.items():
        print(f"  {sku} ({config['name']}):")
        print(f"    Cores: {config['cores']}, CHAs: {config['cha_count']}, "
              f"Memory Channels: {config['memory_channels']}, UPI Links: {config['upi_links']}")
    print()


if __name__ == '__main__':
    # Example usage
    print_bank_table()
    
    print("\nExample: Decoding Bank 0 (IFU):")
    print(format_bank_error(0))
    
    print("\nExample: Decoding Bank 5 (CHA) with STATUS:")
    status = 0xBE00000000800150  # Example valid uncorrected error
    print(format_bank_error(5, status_value=status))
    
    print("\nExample: Get all Core-scoped banks:")
    core_banks = get_banks_by_scope('Core')
    for bank_id, bank in core_banks.items():
        print(f"  Bank {bank_id}: {bank['name']} - {bank['description']}")
