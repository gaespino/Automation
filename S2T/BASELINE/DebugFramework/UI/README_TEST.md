# ControlPanel Offline Test Unit

## Overview
This test unit allows you to test all ControlPanel functionality without requiring the actual Framework or hardware.

## Files
- `TestControlPanel.py` - Main test application
- `MockCOntrolPanel.py` - Generates mock test data
- `TestRunControlPanel.py` - Test runner with different modes

## Setup
1. Ensure your ControlPanel and StatusHandler modules are importable
2. Run the mock data generator: `python mock_data_generator.py`
3. Run the test: `python test_control_panel_offline.py`

## Test Modes

### Interactive Mode (Default)
```bash
python TestControlPanel.py