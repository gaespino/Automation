"""
Script to fix F541 errors (f-strings without any placeholders)
This script will convert f-strings without placeholders to regular strings.
"""

import re
import os
from pathlib import Path

# Files to fix based on the error list
FILES_TO_FIX = {
    "BASELINE_DMR/DebugFramework/Automation_Flow/AutomationDesigner.py": [581],
    "BASELINE_DMR/DebugFramework/Automation_Flow/AutomationFlows.py": [169, 235, 274, 283, 287, 296, 310, 404, 414, 423, 424, 439, 441, 444, 447, 458, 478, 532, 620, 650, 654, 656, 658, 660, 739, 759, 778, 779, 791, 793, 908, 911, 914, 1003, 1006, 1009, 1014, 1017, 1038, 1041, 1098, 1263, 1423, 1462, 2292, 2294, 2301, 2942, 3025, 3064, 3074, 3084, 3098, 3105, 3130, 3148, 3162, 3273, 3330, 3349, 3359, 3380, 3400, 3416, 3425, 3432, 3440, 3451, 3470, 3483, 3792, 4147, 4150, 4155, 4158],
    "BASELINE_DMR/DebugFramework/Automation_Flow/AutomationHandler.py": [1307],
    "BASELINE_DMR/DebugFramework/Automation_Flow/AutomationTracker.py": [41, 557, 1208, 1447, 1507, 1510, 1514, 1538, 1570, 1582, 1584, 1588, 1590, 1638, 1650, 1652, 1656, 1658, 2338],
    "BASELINE_DMR/DebugFramework/Automation_Flow/old_interface.py": [450, 456, 467, 1050],
    "BASELINE_DMR/DebugFramework/Automation_Flow/reference_code_old.py": [1005],
    "BASELINE_DMR/DebugFramework/EFI/patternfinder.py": [314],
    "BASELINE_DMR/DebugFramework/ExecutionHandler/utils/ThreadsHandler.py": [140, 153, 611, 619, 641, 645, 647, 702, 955],
    "BASELINE_DMR/DebugFramework/FileHandler.py": [329, 355, 365, 1012],
    "BASELINE_DMR/DebugFramework/PPV/Decoder/decoder.py": [317, 458, 1032, 1253],
    "BASELINE_DMR/DebugFramework/PPV/gui/AutomationDesigner.py": [582],
    "BASELINE_DMR/DebugFramework/PPV/gui/ExperimentBuilder.py": [3615],
    "BASELINE_DMR/DebugFramework/PPV/gui/MCADecoder.py": [791, 797, 815, 821, 879],
    "BASELINE_DMR/DebugFramework/PPV/gui/PPVDataChecks.py": [243],
    "BASELINE_DMR/DebugFramework/PPV/gui/PPVFileHandler.py": [208],
    "BASELINE_DMR/DebugFramework/PPV/gui/PPVLoopChecks.py": [195],
    "BASELINE_DMR/DebugFramework/PPV/gui/PPVTools.py": [33],
    "BASELINE_DMR/DebugFramework/PPV/parsers/MCAparser.py": [304, 439],
    "BASELINE_DMR/DebugFramework/PPV/parsers/PPVLoopsParser.py": [118],
    "BASELINE_DMR/DebugFramework/PPV/utils/DeveloperEnvironment.py": [660],
    "BASELINE_DMR/DebugFramework/SerialConnection.py": [111, 129, 132, 223, 226, 367],
    "BASELINE_DMR/DebugFramework/Storage_Handler/DBClient.py": [65],
    "BASELINE_DMR/DebugFramework/SystemDebug.py": [509, 547, 805, 808, 1113, 1154, 1158, 1171, 1175, 1349, 1381, 1390, 1394, 1408, 1412, 1635, 1642, 1658, 2183, 2599, 2817, 3476],
    "BASELINE_DMR/DebugFramework/UI/ControlPanel.py": [1559, 1568, 1577, 3032, 3063, 3308, 3799, 5636, 5657],
    "BASELINE_DMR/DebugFramework/UI/ProcessPanel.py": [2377, 2398],
    "BASELINE_DMR/DebugFramework/UI/StatusHandler.py": [1645, 1651, 2207, 2213],
    "BASELINE_DMR/DebugFramework/UI/TestRunControlPanel.py": [75],
    "BASELINE_DMR/S2T/CoreManipulation.py": [453, 466, 482, 1131, 1795, 2050, 2324, 2787],
    "BASELINE_DMR/S2T/GetTesterCurves.py": [243, 254, 294],
    "BASELINE_DMR/S2T/Logger/ErrorReport.py": [33, 41, 46, 54],
    "BASELINE_DMR/S2T/Logger/logger.py": [336],
    "BASELINE_DMR/S2T/SetTesterRegs.py": [1765, 2091, 2092, 2093, 2094, 2095, 2096, 2097, 2098, 2099, 2100, 2102, 2104, 2106, 2108, 2110, 2111, 2113, 2114, 2116, 2117, 2118, 2139, 2149, 2150, 2151, 2152, 2153, 2154, 2155, 2156, 2157, 2158, 2160, 2162, 2164, 2166, 2172, 2173, 2174, 2175, 2394],
    "BASELINE_DMR/S2T/dpmChecks.py": [348, 446, 643, 791, 902, 918, 936, 1079, 1332, 1338, 1429, 1430, 1435, 1441, 1539, 1548, 1576, 1578, 1587, 1598, 1602, 1719, 1720, 1721, 1722, 1730, 1752, 1784, 1907, 2424, 2428],
    "BASELINE_DMR/S2T/managers/frequency_manager.py": [70, 82, 107, 143],
    "BASELINE_DMR/S2T/managers/voltage_manager.py": [189, 237, 238, 310, 506, 522],
    "BASELINE_DMR/S2T/product_specific/cwf/configs.py": [119, 120],
    "BASELINE_DMR/S2T/product_specific/gnr/configs.py": [120, 121],
}

def fix_fstring_in_line(line):
    """
    Convert f-strings without placeholders to regular strings.
    Matches f"..." or f'...' patterns that don't contain {}.
    """
    # Pattern to match f-strings (both single and double quotes)
    # That don't contain any curly braces
    patterns = [
        (r'f"([^"{]*)"', r'"\1"'),  # f"string" -> "string"
        (r"f'([^'{]*)'", r"'\1'"),  # f'string' -> 'string'
    ]

    modified = line
    for pattern, replacement in patterns:
        # Only replace if there are no curly braces in the matched string
        matches = re.finditer(pattern, line)
        for match in matches:
            content = match.group(1)
            if '{' not in content and '}' not in content:
                modified = modified.replace(match.group(0), replacement.replace('\\1', content))

    return modified

def fix_file(file_path, line_numbers):
    """Fix f-strings in specific lines of a file."""
    full_path = Path("C:/Git/Automation/S2T") / file_path

    if not full_path.exists():
        print(f"⚠️  File not found: {full_path}")
        return False

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        modified = False
        for line_num in line_numbers:
            if line_num <= len(lines):
                idx = line_num - 1
                original = lines[idx]
                fixed = fix_fstring_in_line(original)

                if original != fixed:
                    lines[idx] = fixed
                    modified = True
                    print(f"  Line {line_num}: Fixed")

        if modified:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"✅ Fixed: {file_path}")
            return True
        else:
            print(f"ℹ️  No changes needed: {file_path}")
            return False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all files."""
    print("=" * 60)
    print("F541 F-String Fixer")
    print("=" * 60)
    print()

    total_files = len(FILES_TO_FIX)
    fixed_count = 0

    for file_path, line_numbers in FILES_TO_FIX.items():
        print(f"\n📄 Processing: {file_path}")
        print(f"   Lines to check: {len(line_numbers)}")

        if fix_file(file_path, line_numbers):
            fixed_count += 1

    print()
    print("=" * 60)
    print(f"Summary: Fixed {fixed_count} out of {total_files} files")
    print("=" * 60)

if __name__ == "__main__":
    main()
