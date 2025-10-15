"""
Offline Test Unit for DebugFrameworkControlPanel
Tests all interface functionality without requiring actual Framework
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
import time
import threading
import queue
import json
from typing import Dict, Any, List
import random

# Add the parent directory to path to import ControlPanel
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

# Import your ControlPanel (adjust import path as needed)
try:
    from ControlPanel import DebugFrameworkControlPanel
    from StatusHandler import MainThreadHandler, ExecutionStateMachine
except ImportError as e:
    print(f"Import error: {e}")
    print("Please adjust the import paths in the test file")
    sys.exit(1)

class MockFramework:
    """Complete Mock Framework for offline testing"""
    
    def __init__(self, status_reporter=None):
        """Initialize with optional status reporter"""
        self.execution_state = MockExecutionState()
        self.upload_to_database = False
        self._status_reporter = status_reporter
        self._current_execution_state = {'end_requested': False}
        self._end_experiment_flag = threading.Event()
        
    def set_status_reporter(self, status_reporter):
        """Set the status reporter"""
        self._status_reporter = status_reporter
        
    @staticmethod
    def system_2_tester_default():
        """Mock S2T configuration"""
        return {
            'boot_timeout': 30,
            'test_timeout': 60,
            'retry_count': 3,
            'debug_mode': True
        }
    
    def Recipes(self, file_path):
        """Mock recipe loading"""
        return generate_mock_experiments()
    
    def RecipeExecutor(self, data, S2T_BOOT_CONFIG, extmask=None, summary=True, 
                      cancel_flag=None, experiment_name=""):
        """Mock recipe execution with realistic timing and status updates"""
        
        try:
            test_type = data.get('Test Type', 'Single')
            iterations = self._get_iterations_for_test_type(data)
            
            # Send experiment start notification
            if self._status_reporter:
                self._status_reporter.report_status({
                    'type': 'experiment_start',
                    'data': {
                        'experiment_name': experiment_name,
                        'strategy_type': test_type,
                        'test_name': data.get('Test Name', 'Mock Test'),
                        'total_iterations': iterations
                    }
                })
            
            results = []
            
            for i in range(1, iterations + 1):
                # Check for cancellation
                if self.execution_state.is_cancelled():
                    if self._status_reporter:
                        self._status_reporter.report_status({
                            'type': 'iteration_cancelled',
                            'data': {
                                'iteration': i,
                                'status': 'CANCELLED'
                            }
                        })
                    results.append('CANCELLED')
                    break
                
                # Check for END command
                if self.execution_state.is_ended():
                    results.append('ENDED')
                    break
                
                # Send iteration start
                if self._status_reporter:
                    self._status_reporter.report_status({
                        'type': 'iteration_start',
                        'data': {
                            'iteration': i,
                            'status': f'Starting iteration {i}/{iterations}',
                            'progress_weight': 0.0
                        }
                    })
                
                # Simulate iteration execution with progress updates
                self._simulate_iteration_execution(i, iterations, experiment_name)
                
                # Check for cancellation during execution
                if self.execution_state.is_cancelled():
                    results.append('CANCELLED')
                    break
                
                # Simulate result
                result = self._simulate_iteration_result(i, test_type)
                results.append(result)
                
                # Send iteration complete
                if self._status_reporter:
                    self._status_reporter.report_status({
                        'type': 'iteration_complete',
                        'data': {
                            'iteration': i,
                            'status': result,
                            'progress_weight': 1.0,
                            'scratchpad': f'Mock data for iteration {i}',
                            'seed': random.randint(1000, 9999)
                        }
                    })
                
                # Small delay between iterations
                time.sleep(0.5)
            
            # Send experiment complete
            if self._status_reporter and not self.execution_state.is_cancelled():
                self._status_reporter.report_status({
                    'type': 'experiment_complete',
                    'data': {
                        'test_name': experiment_name,
                        'total_tests': len(results),
                        'success_rate': (results.count('PASS') / len(results) * 100) if results else 0
                    }
                })
            
            return results
            
        except Exception as e:
            print(f"Mock execution error: {e}")
            return ['FAILED']
    
    def _get_iterations_for_test_type(self, data):
        """Get number of iterations based on test type"""
        test_type = data.get('Test Type', 'Single')
        
        if test_type == 'Loops':
            return data.get('Loops', 5)
        elif test_type == 'Sweep':
            start = data.get('Start', 0)
            end = data.get('End', 10)
            step = data.get('Steps', 1)
            return max(1, int((end - start) / step) + 1)
        elif test_type == 'Shmoo':
            return 25  # Simulate 5x5 shmoo
        else:
            return 3  # Single test with retries
    
    def _simulate_iteration_execution(self, iteration, total_iterations, experiment_name):
        """Simulate realistic iteration execution with progress updates"""
        
        phases = [
            ('Preparing environment', 0.1),
            ('Starting boot process', 0.3),
            ('System boot in progress', 0.5),
            ('Boot complete', 0.7),
            ('Running test content', 0.9),
            ('Test content complete', 1.0)
        ]
        
        for phase_name, progress_weight in phases:
            if self.execution_state.is_cancelled() or self.execution_state.is_ended():
                break
                
            # Send progress update
            if self._status_reporter:
                self._status_reporter.report_status({
                    'type': 'iteration_progress',
                    'data': {
                        'iteration': iteration,
                        'status': phase_name,
                        'progress_weight': progress_weight
                    }
                })
            
            # Send strategy progress update
            overall_progress = ((iteration - 1 + progress_weight) / total_iterations) * 100
            if self._status_reporter:
                self._status_reporter.report_status({
                    'type': 'strategy_progress',
                    'data': {
                        'progress_percent': overall_progress,
                        'current_iteration': iteration,
                        'total_iterations': total_iterations,
                        'strategy_type': 'Mock Strategy',
                        'test_name': experiment_name,
                        'current_value': f'Value_{iteration}'
                    }
                })
            
            # Simulate phase execution time
            time.sleep(random.uniform(0.2, 0.8))
    
    def _simulate_iteration_result(self, iteration, test_type):
        """Simulate iteration results with realistic distribution"""
        
        # Simulate different failure rates based on test type
        if test_type == 'Shmoo':
            # Shmoo tests have more varied results
            results = ['PASS', 'FAIL', 'MARGINAL']
            weights = [0.6, 0.3, 0.1]
        else:
            # Regular tests mostly pass
            results = ['PASS', 'FAIL']
            weights = [0.85, 0.15]
        
        return random.choices(results, weights=weights)[0]
    
    def halt_execution(self):
        """Mock halt execution"""
        self.execution_state.halt()
        if self._status_reporter:
            self._status_reporter.report_status({
                'type': 'execution_halted',
                'data': {
                    'message': 'Execution halted by user request',
                    'current_iteration': getattr(self, '_current_iteration', 0)
                }
            })
        return True
    
    def continue_execution(self):
        """Mock continue execution"""
        self.execution_state.resume()
        if self._status_reporter:
            self._status_reporter.report_status({
                'type': 'execution_resumed',
                'data': {
                    'message': 'Execution resumed by user request',
                    'current_iteration': getattr(self, '_current_iteration', 0)
                }
            })
        return True
    
    def end_experiment(self):
        """Mock end experiment"""
        self.execution_state.end()
        if self._status_reporter:
            self._status_reporter.report_status({
                'type': 'execution_ended',
                'data': {
                    'reason': 'END command issued by user',
                    'experiment_name': getattr(self, '_current_experiment', 'Unknown')
                }
            })
        return True
    
    def cancel_execution(self):
        """Mock cancel execution"""
        self.execution_state.cancel()
        if self._status_reporter:
            self._status_reporter.report_status({
                'type': 'execution_cancelled',
                'data': {
                    'reason': 'User requested cancellation',
                    'experiment_name': getattr(self, '_current_experiment', 'Unknown')
                }
            })
        return True
    
    def _prepare_for_new_execution(self):
        """Mock preparation for new execution"""
        self.execution_state.reset()
        return True
    
    def _finalize_execution(self, reason):
        """Mock execution finalization"""
        print(f"Mock Framework: Execution finalized - {reason}")
    
    def refresh_ipc(self):
        """Mock IPC refresh"""
        print("Mock Framework: IPC refreshed")
    
    def update_unit_data(self):
        """Mock unit data update"""
        print("Mock Framework: Unit data updated")

class MockExecutionState:
    """Mock execution state for testing"""
    
    def __init__(self):
        self._cancelled = False
        self._ended = False
        self._halted = False
        self._active = False
    
    def is_cancelled(self):
        return self._cancelled
    
    def is_ended(self):
        return self._ended
    
    def is_halted(self):
        return self._halted
    
    def is_active(self):
        return self._active
    
    def cancel(self, reason="Test cancellation"):
        self._cancelled = True
        self._active = False
    
    def end(self, reason="Test end"):
        self._ended = True
    
    def halt(self):
        self._halted = True
    
    def resume(self):
        self._halted = False
    
    def reset(self):
        self._cancelled = False
        self._ended = False
        self._halted = False
        self._active = True

def generate_mock_experiments():
    """Generate mock experiment data for testing"""
    
    experiments = {
        'Basic_Test_1': {
            'Experiment': 'Enabled',
            'Test Name': 'Basic Functionality Test',
            'Test Mode': 'Normal',
            'Test Type': 'Single',
            'Description': 'Basic test to verify core functionality',
            'Timeout': 30,
            'Retries': 3
        },
        'Loop_Test_2': {
            'Experiment': 'Enabled',
            'Test Name': 'Loop Stress Test',
            'Test Mode': 'Stress',
            'Test Type': 'Loops',
            'Loops': 8,
            'Description': 'Stress test with multiple iterations',
            'Timeout': 60
        },
        'Sweep_Test_3': {
            'Experiment': 'Disabled',
            'Test Name': 'Parameter Sweep Test',
            'Test Mode': 'Characterization',
            'Test Type': 'Sweep',
            'Start': 0,
            'End': 20,
            'Steps': 2,
            'Description': 'Sweep test across parameter range'
        },
        'Shmoo_Test_4': {
            'Experiment': 'Enabled',
            'Test Name': 'Shmoo Plot Test',
            'Test Mode': 'Characterization',
            'Test Type': 'Shmoo',
            'X_Axis': {'Type': 'Voltage', 'Start': 1.0, 'End': 1.5, 'Steps': 5},
            'Y_Axis': {'Type': 'Frequency', 'Start': 100, 'End': 200, 'Steps': 5},
            'Description': 'Two-dimensional parameter sweep'
        },
        'Debug_Test_5': {
            'Experiment': 'Enabled',
            'Test Name': 'Debug Mode Test',
            'Test Mode': 'Debug',
            'Test Type': 'Single',
            'Debug_Level': 'Verbose',
            'Description': 'Test with debug output enabled'
        },
        'Long_Test_6': {
            'Experiment': 'Disabled',
            'Test Name': 'Long Duration Test',
            'Test Mode': 'Endurance',
            'Test Type': 'Loops',
            'Loops': 15,
            'Description': 'Long-running endurance test',
            'Timeout': 120
        }
    }
    
    return experiments

class TestControlPanelOffline:
    """Main test class for offline ControlPanel testing"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ControlPanel Offline Test Unit")
        self.root.geometry("1600x900")
        
        # Create mock framework
        #self.mock_framework = MockFramework()
        
        # Create ControlPanel with mock framework
        self.control_panel = DebugFrameworkControlPanel(self.root, MockFramework)
        self.mock_framework = self.control_panel.Framework
        
        # Load mock experiments
        self.load_mock_experiments()
        
        # Add test controls
        self.create_test_controls()
        
        # Set up test scenarios
        self.test_scenarios = self.create_test_scenarios()
        
    def load_mock_experiments(self):
        """Load mock experiments into the control panel"""
        try:
            mock_experiments = generate_mock_experiments()
            self.control_panel.experiments = mock_experiments
            self.control_panel.create_experiment_rows()
            self.control_panel.log_status("[TEST] Mock experiments loaded successfully")
        except Exception as e:
            print(f"Error loading mock experiments: {e}")
    
    def create_test_controls(self):
        """Create additional test controls"""
        
        # Test control frame
        test_frame = ttk.LabelFrame(self.root, text="Test Controls", padding=10)
        test_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # Test scenario buttons
        ttk.Button(test_frame, text="Run Animation Test", 
                  command=self.control_panel.verify_animations).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(test_frame, text="Simulate Success Run", 
                  command=self.simulate_success_run).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(test_frame, text="Simulate Failure Run", 
                  command=self.simulate_failure_run).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(test_frame, text="Simulate Cancel", 
                  command=self.simulate_cancel).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(test_frame, text="Simulate Hold/Resume", 
                  command=self.simulate_hold_resume).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(test_frame, text="Test Progress Bars", 
                  command=self.test_progress_bars).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(test_frame, text="Test Status Animations", 
                  command=self.test_status_animations).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(test_frame, text="Reset All", 
                  command=self.reset_all_tests).pack(side=tk.RIGHT, padx=5)
    
    def create_test_scenarios(self):
        """Create predefined test scenarios"""
        
        scenarios = {
            'quick_success': {
                'name': 'Quick Success Test',
                'experiments': ['Basic_Test_1', 'Debug_Test_5'],
                'expected_result': 'success',
                'duration': 10
            },
            'mixed_results': {
                'name': 'Mixed Results Test',
                'experiments': ['Basic_Test_1', 'Loop_Test_2', 'Shmoo_Test_4'],
                'expected_result': 'mixed',
                'duration': 30
            },
            'long_endurance': {
                'name': 'Long Endurance Test',
                'experiments': ['Long_Test_6'],
                'expected_result': 'success',
                'duration': 60
            }
        }
        
        return scenarios
    
    def simulate_success_run(self):
        """Simulate a successful test run"""
        self.control_panel.log_status("[TEST] Starting simulated success run...")
        
        # Enable specific experiments for success scenario
        self.set_experiment_states(['Basic_Test_1', 'Debug_Test_5'], True)
        
        # Start the test
        self.root.after(1000, self.control_panel.start_tests_thread)
    
    def simulate_failure_run(self):
        """Simulate a test run with failures"""
        self.control_panel.log_status("[TEST] Starting simulated failure run...")
        
        # Enable experiments that might fail
        self.set_experiment_states(['Loop_Test_2', 'Shmoo_Test_4'], True)
        
        # Increase failure rate for this test
        original_method = self.mock_framework._simulate_iteration_result
        def high_failure_rate(iteration, test_type):
            results = ['PASS', 'FAIL']
            weights = [0.3, 0.7]  # High failure rate
            return random.choices(results, weights=weights)[0]
        
        self.mock_framework._simulate_iteration_result = high_failure_rate
        
        # Start the test
        self.root.after(1000, self.control_panel.start_tests_thread)
        
        # Restore original method after test
        self.root.after(30000, lambda: setattr(self.mock_framework, '_simulate_iteration_result', original_method))
    
    def simulate_cancel(self):
        """Simulate cancellation during execution"""
        self.control_panel.log_status("[TEST] Starting test with planned cancellation...")
        
        # Enable some experiments
        self.set_experiment_states(['Basic_Test_1', 'Loop_Test_2'], True)
        
        # Start the test
        self.control_panel.start_tests_thread()
        
        # Cancel after 5 seconds
        self.root.after(5000, self.control_panel.cancel_tests)
    
    def simulate_hold_resume(self):
        """Simulate hold and resume functionality"""
        self.control_panel.log_status("[TEST] Starting test with hold/resume simulation...")
        
        # Enable experiments
        self.set_experiment_states(['Loop_Test_2'], True)
        
        # Start the test
        self.control_panel.start_tests_thread()
        
        # Hold after 3 seconds
        self.root.after(3000, self.control_panel.toggle_framework_hold)
        
        # Resume after 5 more seconds
        self.root.after(8000, self.control_panel.toggle_framework_hold)
    
    def test_progress_bars(self):
        """Test dual progress bar functionality"""
        self.control_panel.log_status("[TEST] Testing dual progress bar system...")
        
        def progress_test_sequence():
            # Test overall progress
            for exp in range(1, 6):  # 5 experiments
                self.control_panel.current_experiment_index = exp - 1
                self.control_panel.total_experiments = 5
                
                # Test iteration progress within each experiment
                for iteration in range(1, 11):  # 10 iterations per experiment
                    progress_data = {
                        'progress_percent': (iteration / 10) * 100,
                        'current_iteration': iteration,
                        'total_iterations': 10
                    }
                    
                    self.root.after(
                        (exp - 1) * 10 * 200 + iteration * 200,
                        lambda pd=progress_data: self.control_panel._coordinate_progress_updates('strategy_progress', pd)
                    )
                
                # Complete experiment
                self.root.after(
                    (exp - 1) * 10 * 200 + 10 * 200 + 100,
                    lambda: self.control_panel._coordinate_progress_updates('experiment_complete', {})
                )
        
        progress_test_sequence()
    
    def test_status_animations(self):
        """Test all status animations"""
        self.control_panel.log_status("[TEST] Testing status animations...")
        
        if not self.control_panel.experiment_frames:
            self.control_panel.log_status("[WARN] No experiments available for animation testing")
            return
        
        # Test different status animations on different experiments
        animations = [
            ('In Progress', '#00008B', 'white', 0),
            ('Running', '#00008B', 'white', 2000),
            ('Done', '#006400', 'white', 4000),
            ('Fail', 'yellow', 'black', 6000),
            ('Cancelled', 'gray', 'white', 8000),
            ('Halted', 'orange', 'black', 10000),
            ('Idle', 'lightgray', 'black', 12000)
        ]
        
        for i, frame_data in enumerate(self.control_panel.experiment_frames[:3]):  # Test first 3
            exp_name = frame_data['experiment_name']
            
            for status, bg, fg, delay in animations:
                self.root.after(
                    delay + i * 500,  # Stagger animations
                    lambda n=exp_name, s=status, b=bg, f=fg: 
                    self.control_panel._update_experiment_status_safe(n, s, b, f)
                )
    
    def set_experiment_states(self, experiment_names: List[str], enabled: bool):
        """Set specific experiments to enabled/disabled state"""
        
        for frame_data in self.control_panel.experiment_frames:
            exp_name = frame_data['experiment_name']
            
            if exp_name in experiment_names:
                # Update the checkbox
                frame_data['enabled_var'].set(enabled)
                # Update the internal state
                self.control_panel._update_experiment_state(exp_name, enabled)
    
    def reset_all_tests(self):
        """Reset all test states"""
        self.control_panel.log_status("[TEST] Resetting all test states...")
        
        try:
            # Reset progress bars
            if hasattr(self.control_panel, 'overall_progress_var'):
                self.control_panel.overall_progress_var.set(0)
            if hasattr(self.control_panel, 'iteration_progress_var'):
                self.control_panel.iteration_progress_var.set(0)
            
            # Reset experiment statuses
            self.control_panel._cleanup_experiment_statuses()
            
            # Reset counters
            self.control_panel.reset_progress_tracking()
            
            # Reset framework state
            self.mock_framework.execution_state.reset()
            
            # Reset UI state
            self.control_panel._coordinate_status_updates({'text': ' Ready ', 'bg': 'white', 'fg': 'black'})
            
            self.control_panel.log_status("[TEST] All test states reset successfully")
            
        except Exception as e:
            self.control_panel.log_status(f"[ERROR] Reset failed: {e}")
    
    def run_comprehensive_test(self):
        """Run a comprehensive test of all functionality"""
        self.control_panel.log_status("[TEST] Starting comprehensive functionality test...")
        
        test_sequence = [
            (0, "Testing progress bar coordination..."),
            (2000, lambda: self.test_progress_bars()),
            (15000, "Testing status animations..."),
            (17000, lambda: self.test_status_animations()),
            (30000, "Testing simulated execution..."),
            (32000, lambda: self.simulate_success_run()),
            (45000, "Testing cancellation..."),
            (47000, lambda: self.simulate_cancel()),
            (55000, "Testing hold/resume..."),
            (57000, lambda: self.simulate_hold_resume()),
            (70000, "Comprehensive test completed!"),
            (72000, lambda: self.reset_all_tests())
        ]
        
        for delay, action in test_sequence:
            if callable(action):
                self.root.after(delay, action)
            else:
                self.root.after(delay, lambda msg=action: self.control_panel.log_status(f"[TEST] {msg}"))
    
    def run(self):
        """Run the test application"""
        
        # Add comprehensive test button
        test_frame = ttk.Frame(self.root)
        test_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        ttk.Button(test_frame, text="Run Comprehensive Test", 
                  command=self.run_comprehensive_test).pack(side=tk.LEFT, padx=5)
        
        # Log startup
        self.control_panel.log_status("[TEST] ControlPanel Offline Test Unit started")
        self.control_panel.log_status("[TEST] Use the test controls below to test different scenarios")
        
        # Start the GUI
        self.root.mainloop()

def main():
    """Main function to run the offline test"""
    
    print("Starting ControlPanel Offline Test Unit...")
    print("This test unit allows you to test all ControlPanel functionality without the actual Framework.")
    print("Use the test controls at the bottom to run different test scenarios.")
    
    try:
        test_app = TestControlPanelOffline()
        test_app.run()
    except Exception as e:
        print(f"Test application error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()