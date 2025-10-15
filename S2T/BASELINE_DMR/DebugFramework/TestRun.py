import TestMocks
import TestFramework
import os
import tempfile

# Now you can safely run tests with product specification
# Available products: "GNR", "CWF", "DMR"

TestFramework.run_control_panel_test("GNR")
#TestFramework.run_automation_panel_test("GNR")