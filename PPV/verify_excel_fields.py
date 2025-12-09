"""
Verify that all fields from the Excel sheet specification are present in ExperimentBuilder
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.ExperimentBuilder import ExperimentBuilderGUI

# Expected fields from Excel sheet
EXCEL_FIELDS = [
    "Experiment",
    "Test Name",
    "Test Mode",
    "Test Type",
    "Visual ID",
    "Bucket",
    "COM Port",
    "IP Address",
    "TTL Folder",
    "Scripts File",
    "Post Process",
    "Pass String",
    "Fail String",
    "Content",
    "Test Number",
    "Test Time",
    "Reset",
    "Reset on PASS",
    "FastBoot",
    "Core License",
    "600W Unit",
    "Pseudo Config",
    "Configuration (Mask)",
    "Boot Breakpoint",
    "Disable 2 Cores",
    "Check Core",
    "Voltage Type",
    "Voltage IA",
    "Voltage CFC",
    "Frequency IA",
    "Frequency CFC",
    "Loops",
    "Type",
    "Domain",
    "Start",
    "End",
    "Steps",
    "ShmooFile",
    "ShmooLabel",
    "Linux Pre Command",
    "Linux Post Command",
    "Linux Pass String",
    "Linux Fail String",
    "Startup Linux",
    "Linux Path",
    "Linux Content Wait Time",
    "Linux Content Line 0",
    "Linux Content Line 1",
    "Dragon Pre Command",
    "Dragon Post Command",
    "Startup Dragon",
    "ULX Path",
    "ULX CPU",
    "Product Chop",
    "VVAR0",
    "VVAR1",
    "VVAR2",
    "VVAR3",
    "VVAR_EXTRA",
    "Dragon Content Path",
    "Dragon Content Line",
    "Stop on Fail",
    "Merlin Name",
    "Merlin Drive",
    "Merlin Path"
]

def verify_fields():
    """Verify all Excel fields are present in ExperimentBuilder"""
    print("=" * 70)
    print("ExperimentBuilder Field Verification")
    print("=" * 70)
    print()
    
    # Create instance to get template
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    app = ExperimentBuilderGUI(root)
    template = app.config_template
    data_types = template.get('data_types', {})
    
    print(f"Total fields in Excel specification: {len(EXCEL_FIELDS)}")
    print(f"Total fields in ExperimentBuilder: {len(data_types)}")
    print()
    
    # Check for missing fields
    missing_fields = []
    for field in EXCEL_FIELDS:
        if field not in data_types:
            missing_fields.append(field)
    
    # Check for extra fields
    extra_fields = []
    for field in data_types.keys():
        if field not in EXCEL_FIELDS:
            extra_fields.append(field)
    
    # Report results
    if not missing_fields and not extra_fields:
        print("✓ PERFECT MATCH!")
        print("✓ All Excel fields are present in ExperimentBuilder")
        print("✓ No extra fields found")
        result = True
    else:
        if missing_fields:
            print("⚠ MISSING FIELDS:")
            for field in missing_fields:
                print(f"  - {field}")
            print()
        
        if extra_fields:
            print("ℹ EXTRA FIELDS (not in Excel spec):")
            for field in extra_fields:
                print(f"  + {field}")
            print()
        
        result = not missing_fields  # Only fail if fields are missing
    
    print("=" * 70)
    print()
    
    # Print field list comparison
    print("Field Mapping:")
    print("-" * 70)
    for field in sorted(EXCEL_FIELDS):
        status = "✓" if field in data_types else "✗"
        field_type = data_types.get(field, ["N/A"])[0]
        print(f"{status} {field:40} [{field_type}]")
    
    print("=" * 70)
    
    root.destroy()
    
    return result

if __name__ == "__main__":
    try:
        success = verify_fields()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
