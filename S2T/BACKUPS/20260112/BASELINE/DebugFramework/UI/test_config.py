# test_config.py
import os
import sys

# Test configuration
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
MOCK_EXPERIMENT_FILE = os.path.join(TEST_DATA_DIR, 'mock_experiments.xlsx')

# Sample test data
SAMPLE_EXPERIMENTS = {
    'Loop_Test': {
        'Experiment': 'Enabled',
        'Test Name': 'Loop Test Sample',
        'Test Mode': 'Normal',
        'Test Type': 'Loops',
        'Loops': 3,
        'External Mask': None
    },
    'Sweep_Test': {
        'Experiment': 'Enabled',
        'Test Name': 'Sweep Test Sample',
        'Test Mode': 'Debug',
        'Test Type': 'Sweep',
        'Type': 'frequency',
        'Domain': 'ia',
        'Start': 16,
        'End': 24,
        'Steps': 4,
        'External Mask': None
    },
    'Shmoo_Test': {
        'Experiment': 'Disabled',
        'Test Name': 'Shmoo Test Sample',
        'Test Mode': 'Normal',
        'Test Type': 'Shmoo',
        'ShmooFile': 'test_shmoo.json',
        'ShmooLabel': 'TEST_LABEL',
        'External Mask': None
    }
}

SAMPLE_S2T_CONFIG = {
    'AFTER_MRC_POST': 30,
    'EFI_POST': 60,
    'LINUX_POST': 120,
    'BOOTSCRIPT_RETRY_TIMES': 3,
    'BOOTSCRIPT_RETRY_DELAY': 10
}