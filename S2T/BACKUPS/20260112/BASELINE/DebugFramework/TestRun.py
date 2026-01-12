import TestMocks
import TestFramework
import os
import tempfile

# ==================== TEST CONFIGURATION ====================
# Available products: "GNR", "CWF", "DMR"
# Select which panel to test by uncommenting the appropriate line

PRODUCT = "CWF"  # Change this to test different products

print("\n" + "="*70)
print("DEBUG FRAMEWORK TEST LAUNCHER")
print("="*70)
print(f"Product: {PRODUCT}")
print("\nAvailable Test Options:")
print("  1. Control Panel   - Main experiment execution interface")
print("  2. Automation Panel - Flow-based automation execution interface")
print("="*70)

# Uncomment ONE of the following to run:

# Option 1: Test Control Panel (Main Framework UI)
#TestFramework.run_control_panel_test(PRODUCT)

# Option 2: Test Automation Panel (Flow Execution UI)
TestFramework.run_automation_panel_test(PRODUCT)

# Option 3: Interactive Test Menu (runs both and more)
#TestFramework.main()

print("\n" + "="*70)
print("Test session ended")
print("="*70 + "\n")
