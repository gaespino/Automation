"""
Script to fix F541 errors: f-strings without placeholders
Converts f-strings to regular strings when they don't contain any placeholders
"""

import re
import os
from pathlib import Path

# Files with F541 errors from the error list
FILES_TO_FIX = [
    "S2T/BASELINE_DMR/DebugFramework/Automation_Flow/AutomationDesigner.py",
    "S2T/BASELINE_DMR/DebugFramework/Automation_Flow/AutomationFlows.py",
    "S2T/BASELINE_DMR/DebugFramework/Automation_Flow/AutomationHandler.py",
    "S2T/BASELINE_DMR/DebugFramework/Automation_Flow/AutomationTracker.py",
    "S2T/BASELINE_DMR/DebugFramework/Automation_Flow/old_interface.py",
    "S2T/BASELINE_DMR/DebugFramework/Automation_Flow/reference_code_old.py",
    "S2T/BASELINE_DMR/DebugFramework/EFI/patternfinder.py",
    "S2T/BASELINE_DMR/DebugFramework/ExecutionHandler/utils/ThreadsHandler.py",
    "S2T/BASELINE_DMR/DebugFramework/FileHandler.py",
    "S2T/BASELINE_DMR/DebugFramework/PPV/Decoder/decoder.py",
    "S2T/BASELINE_DMR/DebugFramework/PPV/gui/AutomationDesigner.py",
    "S2T/BASELINE_DMR/DebugFramework/PPV/gui/ExperimentBuilder.py",
    "S2T/BASELINE_DMR/DebugFramework/PPV/gui/MCADecoder.py",
    "S2T/BASELINE_DMR/DebugFramework/PPV/gui/PPVDataChecks.py",
    "S2T/BASELINE_DMR/DebugFramework/PPV/gui/PPVFileHandler.py",
    "S2T/BASELINE_DMR/DebugFramework/PPV/gui/PPVLoopChecks.py",
    "S2T/BASELINE_DMR/DebugFramework/PPV/gui/PPVTools.py",
    "S2T/BASELINE_DMR/DebugFramework/PPV/parsers/MCAparser.py",
    "S2T/BASELINE_DMR/DebugFramework/PPV/parsers/PPVLoopsParser.py",
    "S2T/BASELINE_DMR/DebugFramework/PPV/utils/DeveloperEnvironment.py",
    "S2T/BASELINE_DMR/DebugFramework/SerialConnection.py",
    "S2T/BASELINE_DMR/DebugFramework/Storage_Handler/DBClient.py",
    "S2T/BASELINE_DMR/DebugFramework/SystemDebug.py",
    "S2T/BASELINE_DMR/DebugFramework/UI/ControlPanel.py",
    "S2T/BASELINE_DMR/DebugFramework/UI/ProcessPanel.py",
    "S2T/BASELINE_DMR/DebugFramework/UI/StatusHandler.py",
    "S2T/BASELINE_DMR/DebugFramework/UI/TestRunControlPanel.py",
    "S2T/BASELINE_DMR/S2T/CoreManipulation.py",
    "S2T/BASELINE_DMR/S2T/GetTesterCurves.py",
    "S2T/BASELINE_DMR/S2T/Logger/ErrorReport.py",
    "S2T/BASELINE_DMR/S2T/Logger/logger.py",
    "S2T/BASELINE_DMR/S2T/SetTesterRegs.py",
    "S2T/BASELINE_DMR/S2T/dpmChecks.py",
    "S2T/BASELINE_DMR/S2T/managers/frequency_manager.py",
    "S2T/BASELINE_DMR/S2T/managers/voltage_manager.py",
    "S2T/BASELINE_DMR/S2T/product_specific/cwf/configs.py",
    "S2T/BASELINE_DMR/S2T/product_specific/gnr/configs.py",
]

def fix_f541_in_file(filepath):
    """
    Fix F541 errors in a single file by converting f-strings without placeholders to regular strings.
    Returns the number of fixes made.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fixes = 0

        # Pattern to match f-strings without placeholders
        # Matches f"..." or f'...' where ... doesn't contain {
        patterns = [
            (r'f"([^"{}]*)"', r'"\1"'),  # f"text" -> "text"
            (r"f'([^'{}]*)'", r"'\1'"),  # f'text' -> 'text'
        ]

        for pattern, replacement in patterns:
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                content = new_content
                fixes += count

        if fixes > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ {filepath}: Fixed {fixes} f-strings")
            return fixes
        else:
            print(f"  {filepath}: No f-strings to fix")
            return 0

    except Exception as e:
        print(f"✗ {filepath}: Error - {e}")
        return 0

def main():
    base_path = Path(r"C:\Git\Automation")
    total_fixes = 0

    print("=" * 80)
    print("F541 Error Fixer - Converting f-strings without placeholders to regular strings")
    print("=" * 80)
    print()

    for relative_path in FILES_TO_FIX:
        full_path = base_path / relative_path
        if full_path.exists():
            fixes = fix_f541_in_file(full_path)
            total_fixes += fixes
        else:
            print(f"⚠ {relative_path}: File not found")

    print()
    print("=" * 80)
    print(f"Summary: Fixed {total_fixes} f-strings across {len(FILES_TO_FIX)} files")
    print("=" * 80)

if __name__ == "__main__":
    main()
