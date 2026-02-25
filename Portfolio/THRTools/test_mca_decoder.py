"""
Quick Launch Script for MCA Decoder
Run this file to test the MCA Decoder standalone
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.MCADecoder import start_mca_decoder

if __name__ == "__main__":
    print("=" * 60)
    print("MCA Single Line Decoder - Standalone Launch")
    print("=" * 60)
    print("\nLaunching MCA Decoder GUI...")
    print("\nQuick Test Instructions:")
    print("1. Select Product: GNR")
    print("2. Select Decoder: CHA/CCF")
    print("3. Enter MC_STATUS: 0x9C00000040000000")
    print("4. Enter MC_MISC: 0x0000000000000080")
    print("5. Click 'Decode MCA'")
    print("\nExpected Result:")
    print("  - MSCOD: MSCOD_UNCORRECTABLE_TAG_ERROR")
    print("  - VAL: 1 (Valid)")
    print("  - UC: 1 (Uncorrected)")
    print("  - Cache State: I")
    print("=" * 60)
    print()

    start_mca_decoder()
