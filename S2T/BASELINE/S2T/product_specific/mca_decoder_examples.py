"""
MCA Bank Decoder - Usage Examples
Author: gaespino
Last update: 12/11/25

This script demonstrates how to use the MCA bank decoders for DMR, GNR, and CWF products.
"""

import sys
import os

# Add the S2T path to import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def example_dmr():
    """Example usage for DMR product"""
    print("\n" + "="*100)
    print("DMR (Diamond Rapids) MCA Bank Decoder Examples")
    print("="*100 + "\n")
    
    from product_specific.dmr import mca_banks
    
    # Print full bank table
    mca_banks.print_bank_table()
    
    # Example 1: Get bank information
    print("\n" + "-"*80)
    print("Example 1: Get Bank 6 (CCF) Information")
    print("-"*80)
    bank_info = mca_banks.get_bank_info(6)
    for key, value in bank_info.items():
        print(f"  {key}: {value}")
    
    # Example 2: Decode a bank error
    print("\n" + "-"*80)
    print("Example 2: Decode Bank 19 (MCCHAN0) with STATUS and MISC")
    print("-"*80)
    status = 0xBE00000000800150  # Example valid uncorrected error
    misc = 0x1000000000  # Sub-channel bit set
    decoded = mca_banks.decode_bank_error(19, status_value=status, misc_value=misc)
    for key, value in decoded.items():
        print(f"  {key}: {value}")
    
    # Example 3: Format error message
    print("\n" + "-"*80)
    print("Example 3: Format Bank 12 (HA_MVF) Error Message")
    print("-"*80)
    print(mca_banks.format_bank_error(12, register_path='sv.socket0.imhs.uncore.ha', status_value=0xBE00000000800150))
    
    # Example 4: Get banks by domain
    print("\n" + "-"*80)
    print("Example 4: Get all CBB domain banks")
    print("-"*80)
    cbb_banks = mca_banks.get_banks_by_domain('CBB')
    for bank_id, bank in cbb_banks.items():
        print(f"  Bank {bank_id}: {bank['name']} - {bank['description']}")
    
    print("\n")


def example_gnr():
    """Example usage for GNR product"""
    print("\n" + "="*100)
    print("GNR (Granite Rapids) MCA Bank Decoder Examples")
    print("="*100 + "\n")
    
    from product_specific.gnr import mca_banks
    
    # Print full bank table
    mca_banks.print_bank_table()
    
    # Example 1: Get bank information
    print("\n" + "-"*80)
    print("Example 1: Get Bank 5 (CHA) Information")
    print("-"*80)
    bank_info = mca_banks.get_bank_info(5)
    for key, value in bank_info.items():
        print(f"  {key}: {value}")
    
    # Example 2: Decode a core bank error
    print("\n" + "-"*80)
    print("Example 2: Decode Bank 0 (IFU) with STATUS")
    print("-"*80)
    status = 0x9E00000000800150  # Example valid corrected error
    decoded = mca_banks.decode_bank_error(0, status_value=status)
    for key, value in decoded.items():
        print(f"  {key}: {value}")
    
    # Example 3: Format error message
    print("\n" + "-"*80)
    print("Example 3: Format Bank 6 (IMC) Error Message")
    print("-"*80)
    print(mca_banks.format_bank_error(6, register_path='sv.sockets.computes.uncore.memss.mcs.chs.mcchan.imc0_mc_status'))
    
    # Example 4: Get banks by scope
    print("\n" + "-"*80)
    print("Example 4: Get all Core-scoped banks")
    print("-"*80)
    core_banks = mca_banks.get_banks_by_scope('Core')
    for bank_id, bank in core_banks.items():
        print(f"  Bank {bank_id}: {bank['name']} - {bank['description']}")
    
    print("\n")


def example_cwf():
    """Example usage for CWF product"""
    print("\n" + "="*100)
    print("CWF (Clearwater Forest) MCA Bank Decoder Examples")
    print("="*100 + "\n")
    
    from product_specific.cwf import mca_banks
    
    # Print full bank table
    mca_banks.print_bank_table()
    
    # Example 1: Get bank information
    print("\n" + "-"*80)
    print("Example 1: Get Bank 1 (MEC) Information")
    print("-"*80)
    bank_info = mca_banks.get_bank_info(1)
    for key, value in bank_info.items():
        print(f"  {key}: {value}")
    
    # Example 2: Decode a module bank error
    print("\n" + "-"*80)
    print("Example 2: Decode Bank 4 (L2) with STATUS")
    print("-"*80)
    status = 0xBE00000000800150  # Example valid uncorrected error
    decoded = mca_banks.decode_bank_error(4, status_value=status)
    for key, value in decoded.items():
        print(f"  {key}: {value}")
    
    # Example 3: Format error message with module context
    print("\n" + "-"*80)
    print("Example 3: Format Bank 0 (IC) Error with Module/Core Context")
    print("-"*80)
    print(mca_banks.format_bank_error(0, 
                                      register_path='sv.sockets.computes.cpu.modules.cores.ic_cr_mci_status',
                                      status_value=0xBE00000000800150,
                                      module_id=5,
                                      core_id=2))
    
    # Example 4: Get core and module banks
    print("\n" + "-"*80)
    print("Example 4: Get Core-scoped banks")
    print("-"*80)
    core_banks = mca_banks.get_core_banks()
    for bank_id, bank in core_banks.items():
        print(f"  Bank {bank_id}: {bank['name']} - {bank['description']}")
    
    print("\n" + "-"*80)
    print("Example 5: Get Module-scoped banks")
    print("-"*80)
    module_banks = mca_banks.get_module_banks()
    for bank_id, bank in module_banks.items():
        print(f"  Bank {bank_id}: {bank['name']} - {bank['description']}")
    
    # Show comparison with GNR
    print("\n")
    mca_banks.compare_with_gnr()


def example_integration_with_error_report():
    """Example showing how ErrorReport.py uses the decoder"""
    print("\n" + "="*100)
    print("Integration with ErrorReport.py")
    print("="*100 + "\n")
    
    print("""
The ErrorReport.py module now automatically imports the correct MCA bank decoder
based on the SELECTED_PRODUCT (DMR, GNR, or CWF).

When MCA errors are detected and printed, the decoder provides:

1. During MCA dump (for each register read):
   - Register path and STATUS value
   - --> MCA Bank X: NAME (Full Name)
   - Scope and description
   - Additional notes if available

2. In the final summary (when valid MCAs are found):
   - Each MCA error is printed with full decoding
   - Separated by lines for readability
   - Bank information helps identify the source of the error

Example output:
================================================================================
socket0.cbbs.computes.modules.cores[0].ifu_cr_mc0_status = 0xbe00000000800150
 --> MCA Bank 0: IFU (Instruction Fetch Unit)
     Scope: Core | Instruction Fetch Unit errors
--------------------------------------------------------------------------------
socket0.imhs.uncore.ha.mc_status = 0xbe00000000800150
 --> MCA Bank 12: HA_MVF (Home Agent/Memory VF)
     Scope: IMH | Home Agent/Memory Virtual Function errors (merged)
     Note: Merged instance handling 16 physical agents
================================================================================

This makes debugging MCA errors much faster by immediately knowing:
- What bank triggered the error
- What component/scope it belongs to
- Whether it's a merged bank (multiple instances)
- Additional context specific to the bank
    """)


def main():
    """Run all examples"""
    print("\n" + "="*100)
    print("MCA Bank Decoder Usage Examples")
    print("Product-specific MCA bank information and decoding utilities")
    print("="*100)
    
    while True:
        print("\nSelect an example:")
        print("1. DMR (Diamond Rapids) Examples")
        print("2. GNR (Granite Rapids) Examples")
        print("3. CWF (Clearwater Forest) Examples")
        print("4. Integration with ErrorReport.py")
        print("5. Run all examples")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-5): ").strip()
        
        if choice == '1':
            example_dmr()
        elif choice == '2':
            example_gnr()
        elif choice == '3':
            example_cwf()
        elif choice == '4':
            example_integration_with_error_report()
        elif choice == '5':
            example_dmr()
            example_gnr()
            example_cwf()
            example_integration_with_error_report()
        elif choice == '0':
            print("\nExiting...")
            break
        else:
            print("\nInvalid choice. Please try again.")


if __name__ == '__main__':
    main()
