"""
Mock Data Generator for ControlPanel Testing
Generates realistic test data and configurations
"""

import json
import random
from typing import Dict, Any, List

def generate_mock_s2t_config():
    """Generate mock S2T configuration"""
    return {
        'boot_timeout': 30,
        'test_timeout': 60,
        'retry_count': 3,
        'debug_mode': True,
        'log_level': 'INFO',
        'hardware_config': {
            'voltage_range': [0.8, 1.2],
            'frequency_range': [100, 1000],
            'temperature_range': [-40, 85]
        }
    }

def generate_mock_experiment_file(filename: str = "mock_experiments.json"):
    """Generate a mock experiment file for testing"""
    
    experiments = {
        'Power_On_Test': {
            'Experiment': 'Enabled',
            'Test Name': 'Power On Self Test',
            'Test Mode': 'Functional',
            'Test Type': 'Single',
            'Description': 'Basic power-on functionality test',
            'Timeout': 30,
            'Expected_Result': 'PASS'
        },
        'Voltage_Sweep': {
            'Experiment': 'Enabled',
            'Test Name': 'Core Voltage Sweep',
            'Test Mode': 'Characterization',
            'Test Type': 'Sweep',
            'Start': 0.8,
            'End': 1.2,
            'Steps': 0.05,
            'Description': 'Sweep core voltage and measure functionality',
            'Parameter': 'Core_Voltage'
        },
        'Frequency_Loop': {
            'Experiment': 'Disabled',
            'Test Name': 'Frequency Stability Loop',
            'Test Mode': 'Stress',
            'Test Type': 'Loops',
            'Loops': 10,
            'Description': 'Run frequency stability test multiple times',
            'Frequency': 500
        },
        'Temperature_Shmoo': {
            'Experiment': 'Enabled',
            'Test Name': 'Temperature vs Voltage Shmoo',
            'Test Mode': 'Characterization',
            'Test Type': 'Shmoo',
            'X_Axis': {
                'Type': 'Temperature',
                'Start': -40,
                'End': 85,
                'Steps': 25
            },
            'Y_Axis': {
                'Type': 'Voltage',
                'Start': 0.8,
                'End': 1.2,
                'Steps': 0.1
            },
            'Description': 'Two-dimensional characterization'
        },
        'Memory_Test': {
            'Experiment': 'Enabled',
            'Test Name': 'Memory Pattern Test',
            'Test Mode': 'Functional',
            'Test Type': 'Loops',
            'Loops': 5,
            'Description': 'Test memory with various patterns',
            'Patterns': ['0x55', '0xAA', '0xFF', '0x00']
        },
        'IO_Stress': {
            'Experiment': 'Disabled',
            'Test Name': 'IO Pin Stress Test',
            'Test Mode': 'Stress',
            'Test Type': 'Loops',
            'Loops': 20,
            'Description': 'Stress test all IO pins',
            'Duration': 120
        },
        'Clock_Jitter': {
            'Experiment': 'Enabled',
            'Test Name': 'Clock Jitter Measurement',
            'Test Mode': 'Measurement',
            'Test Type': 'Single',
            'Description': 'Measure clock jitter characteristics',
            'Clock_Frequency': 1000,
            'Measurement_Time': 10
        },
        'Debug_Mode': {
            'Experiment': 'Enabled',
            'Test Name': 'Debug Interface Test',
            'Test Mode': 'Debug',
            'Test Type': 'Single',
            'Description': 'Test debug interface functionality',
            'Debug_Level': 'Verbose',
            'Trace_Enable': True
        }
    }
    
    # Save to file
    with open(filename, 'w') as f:
        json.dump(experiments, f, indent=4)
    
    print(f"Mock experiment file generated: {filename}")
    return experiments

def generate_realistic_test_results(test_type: str, iterations: int) -> List[str]:
    """Generate realistic test results based on test type"""
    
    results = []
    
    if test_type == 'Shmoo':
        # Shmoo tests have more varied results
        result_options = ['PASS', 'FAIL', 'MARGINAL', 'UNTESTED']
        weights = [0.5, 0.2, 0.2, 0.1]
    elif test_type == 'Stress':
        # Stress tests have higher failure rates
        result_options = ['PASS', 'FAIL']
        weights = [0.7, 0.3]
    else:
        # Regular tests mostly pass
        result_options = ['PASS', 'FAIL']
        weights = [0.9, 0.1]
    
    for _ in range(iterations):
        result = random.choices(result_options, weights=weights)[0]
        results.append(result)
    
    return results

def generate_mock_mask_data():
    """Generate mock mask data for testing"""
    
    masks = {
        'Default': None,
        'Production_Mask': {
            'disabled_tests': ['Debug_Mode', 'IO_Stress'],
            'modified_limits': {
                'voltage_min': 0.9,
                'voltage_max': 1.1,
                'frequency_max': 800
            }
        },
        'Engineering_Mask': {
            'disabled_tests': [],
            'modified_limits': {
                'voltage_min': 0.7,
                'voltage_max': 1.3,
                'frequency_max': 1200
            },
            'debug_enabled': True
        },
        'Characterization_Mask': {
            'disabled_tests': ['Memory_Test'],
            'extended_ranges': True,
            'measurement_mode': True
        }
    }
    
    return masks

if __name__ == "__main__":
    # Generate mock data files
    generate_mock_experiment_file("test_experiments.json")
    
    # Generate and save mock configuration
    config = generate_mock_s2t_config()
    with open("mock_s2t_config.json", 'w') as f:
        json.dump(config, f, indent=4)
    
    # Generate and save mock masks
    masks = generate_mock_mask_data()
    with open("mock_masks.json", 'w') as f:
        json.dump(masks, f, indent=4)
    
    print("All mock data files generated successfully!")