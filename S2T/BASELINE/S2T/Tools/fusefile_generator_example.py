"""
Example usage of FuseFileGenerator class

This script demonstrates how to use the FuseFileGenerator class to convert
register arrays into fuse configuration files compatible with fusefilegen.py

The class supports multiple products (GNR, DMR, CWF) by accepting their
respective fusefilegen modules as parameters.
"""

from registerdump import FuseFileGenerator
import sys
import os

# Append the Main Scripts Path
FILE_PATH = os.path.abspath(os.path.dirname(__file__))
MAIN_PATH = os.path.join(FILE_PATH, '..')

sys.path.append(MAIN_PATH)
# Import product-specific fusefilegen modules
from product_specific.gnr import fusefilegen as gnr_fusefilegen
from product_specific.dmr import fusefilegen as dmr_fusefilegen
from product_specific.cwf import fusefilegen as cwf_fusefilegen

# Example GNR register array
gnr_ddrd_array = [
    'sv.socket0.compute0.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point0= 0xaa',
    'sv.socket0.compute1.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point0= 0xaa',
    'sv.socket0.compute2.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point0= 0xaa',
    'sv.socket0.compute0.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point1= 0xb1',
    'sv.socket0.compute1.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point1= 0xb3',
    'sv.socket0.compute2.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point1= 0xb1',
    'sv.socket0.compute0.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point2= 0xbe',
    'sv.socket0.compute1.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point2= 0xbe',
    'sv.socket0.compute2.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point2= 0xc1',
    'sv.socket0.compute0.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point3= 0xbe',
    'sv.socket0.compute1.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point3= 0xbe',
    'sv.socket0.compute2.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point3= 0xc1'
]

# Example DMR register array
dmr_array = [
    'sv.socket0.cbb0.base.fuses.pcu.config_register1= 0x10',
    'sv.socket0.cbb1.base.fuses.pcu.config_register1= 0x10',
    'sv.socket0.cbb0.compute0.fuses.pcu.compute_config= 0x20',
    'sv.socket0.imh0.fuses.memory.timing_register= 0x30',
    'sv.sockets.cbbs.base.fuses.pcu.global_setting= 0xFF',
]

# Example CWF register array (same hierarchy as GNR)
cwf_array = [
    'sv.socket0.compute0.fuses.pcie.config_lane0= 0xA1',
    'sv.socket0.compute1.fuses.pcie.config_lane0= 0xA1',
    'sv.socket0.io0.fuses.pcie.link_config= 0xB2',
    'sv.sockets.ios.fuses.pcie.global_enable= 0xC3',
]

def example_auto_generated_file():
    """Example 1: Auto-generate fuse file with default naming (GNR)"""
    print("=" * 70)
    print("Example 1: Auto-generate fuse file for GNR")
    print("=" * 70)

    generator = FuseFileGenerator(gnr_fusefilegen, gnr_ddrd_array, product='gnr')

    if generator.create_fuse_file():
        report = generator.get_report()
        print(f"\nGeneration Report:")
        print(f"  Product: GNR")
        print(f"  Output file: {report['output_file']}")
        print(f"  Sections: {report['section_count']}")
        print(f"  Total registers: {report['register_count']}")
        print(f"  Errors: {len(report['errors'])}")
        print(f"  Warnings: {len(report['warnings'])}")
    else:
        print("Failed to generate fuse file")


def example_dmr_product():
    """Example 2: Generate fuse file for DMR product"""
    print("\n" + "=" * 70)
    print("Example 2: DMR product with different hierarchy")
    print("=" * 70)

    generator = FuseFileGenerator(dmr_fusefilegen, dmr_array, product='dmr')

    if generator.create_fuse_file():
        report = generator.get_report()
        print(f"\nDMR Generation Report:")
        print(f"  Product: DMR")
        print(f"  Output file: {report['output_file']}")
        print(f"  Sections: {report['sections']}")
        print(f"  Total registers: {report['register_count']}")
    else:
        print("Failed to generate DMR fuse file")


def example_cwf_product():
    """Example 3: Generate fuse file for CWF product"""
    print("\n" + "=" * 70)
    print("Example 3: CWF product")
    print("=" * 70)

    output_path = r"C:\Temp\RegisterDumpLogs\cwf_custom_fuses.fuse"
    generator = FuseFileGenerator(cwf_fusefilegen, cwf_array, product='cwf', output_file=output_path)

    if generator.create_fuse_file():
        print(f"CWF fuse file created at: {generator.fuse_file_path}")


def example_step_by_step():
    """Example 4: Step-by-step parsing and generation"""
    print("\n" + "=" * 70)
    print("Example 4: Step-by-step process (GNR)")
    print("=" * 70)

    generator = FuseFileGenerator(gnr_fusefilegen, gnr_ddrd_array, product='gnr')

    # Step 1: Parse the array
    print("\nStep 1: Parsing array...")
    if generator.parse_array():
        print(f"Parsed {len(generator.parsed_data)} sections")

        # Display parsed data structure
        for section, registers in generator.parsed_data.items():
            print(f"\n  Section: {section}")
            print(f"  Registers: {len(registers)}")
            for reg in list(registers.keys())[:2]:  # Show first 2 registers
                print(f"    - {reg} = {registers[reg]}")
            if len(registers) > 2:
                print(f"    ... and {len(registers) - 2} more")

    # Step 2: Generate the fuse file
    print("\nStep 2: Generating fuse file...")
    if generator.generate_fuse_file():
        print("Success!")


def example_with_io_fuses():
    """Example 5: Working with IO fuses (GNR/CWF pattern)"""
    print("\n" + "=" * 70)
    print("Example 5: IO fuses example (GNR)")
    print("=" * 70)

    io_array = [
        'sv.socket0.io0.fuses.pcie.config_register1= 0x10',
        'sv.socket0.io1.fuses.pcie.config_register1= 0x10',
        'sv.socket0.io0.fuses.pcie.config_register2= 0x20',
        'sv.socket0.io1.fuses.pcie.config_register2= 0x20',
    ]

    generator = FuseFileGenerator(gnr_fusefilegen, io_array, product='gnr')
    if generator.create_fuse_file():
        print(f"IO fuses file created: {generator.fuse_file_path}")


def example_with_plural_sections():
    """Example 6: Using plural sections (sockets/computes)"""
    print("\n" + "=" * 70)
    print("Example 6: Plural sections - applies to all units (GNR)")
    print("=" * 70)

    plural_array = [
        'sv.sockets.computes.fuses.pcu.global_config= 0xFF',
        'sv.sockets.computes.fuses.pcu.common_register= 0xAB',
        'sv.socket0.compute0.fuses.pcu.specific_override= 0x01',
    ]

    generator = FuseFileGenerator(gnr_fusefilegen, plural_array, product='gnr')
    if generator.create_fuse_file():
        print(f"Plural sections fuse file created: {generator.fuse_file_path}")
        report = generator.get_report()
        print(f"Sections generated: {report['sections']}")


if __name__ == "__main__":
    # Run all examples
    #example_auto_generated_file()  # GNR
    example_dmr_product()           # DMR
    #example_cwf_product()           # CWF
    #example_step_by_step()          # GNR step-by-step
    #example_with_io_fuses()         # GNR IO
    #example_with_plural_sections()  # GNR plural

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)
