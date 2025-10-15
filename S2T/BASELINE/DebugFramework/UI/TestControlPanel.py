import unittest
from unittest.mock import Mock, MagicMock, patch, call
import tkinter as tk
import threading
import queue
import time
import sys
import os
from datetime import datetime

# Mock the problematic imports BEFORE importing the actual modules
sys.modules['users'] = Mock()
sys.modules['users.framework'] = Mock()
sys.modules['users.framework.s2t'] = Mock()
sys.modules['users.framework.dpm'] = Mock()
sys.modules['users.framework.ser'] = Mock()
sys.modules['users.framework.fh'] = Mock()
sys.modules['users.framework.gcm'] = Mock()

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

sys.path.append(parent_dir)

# Import our mock framework
from UI.MockControlPanel import (
    MockFramework, MockFrameworkInstanceManager, MockFrameworkExternalAPI,
    MockExecutionState, MockFrameworkUtils, ContentType, TestTarget, VoltageType, TestStatus,
    ExecutionCommand, StatusEventType, mock_execution_state,
    OpenExperiment, Convert_xlsx_to_json, S2T_CONFIGURATION
)

# Now we can safely import the actual modules with mocked dependencies
class TestControlPanelSafe(unittest.TestCase):
    """Safe test suite for DebugFrameworkControlPanel with mocked dependencies"""
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level mocks"""
        # Mock all the problematic modules
        cls.framework_patcher = patch.dict('sys.modules', {
            'users.framework.Framework': Mock(),
            'users.framework.s2t': Mock(),
            'users.framework.dpm': Mock(),
            'users.framework.ser': Mock(),
            'users.framework.fh': Mock(),
            'users.framework.gcm': Mock(),
            'users.framework.FrameworkUtils': Mock(),
        })
        cls.framework_patcher.start()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up class-level mocks"""
        cls.framework_patcher.stop()
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create root window for testing
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        
        # Create mock dependencies
        self.mock_framework = MockFramework
        self.mock_utils = MockFrameworkUtils
        self.mock_manager = MockFrameworkInstanceManager
        self.mock_execution_state = MockExecutionState
        
        # Patch the imports in the control panel module
        with patch.dict('sys.modules', {
            'SystemDebug.Framework': Mock(return_value=self.mock_framework),
            'SystemDebug.FrameworkInstanceManager': Mock(return_value=self.mock_manager),
            'ExecutionHandler.utils.TreadHandler.execution_state': self.mock_execution_state,
            'UI.ControlPanel.OpenExperiment': Mock(side_effect=OpenExperiment),
            'UI.ControlPanel.Convert_xlsx_to_json': Mock(side_effect=Convert_xlsx_to_json),
            'UI.ControlPanel.S2T_CONFIGURATION': S2T_CONFIGURATION,
        }):
            # Import and create control panel
            from UI.ControlPanel import DebugFrameworkControlPanel
            
            self.control_panel = DebugFrameworkControlPanel(
                root=self.root,
                Framework=self.mock_framework,
                utils=self.mock_utils,
                manager=self.mock_manager
            )
        
        # Sample experiment data for testing
        self.sample_experiments = {
            'Test_Experiment_1': {
                'Experiment': 'Enabled',
                'Test Name': 'Sample Test 1',
                'Test Mode': 'Normal',
                'Test Type': 'Loops',
                'Loops': 5,
                'External Mask': None
            },
            'Test_Experiment_2': {
                'Experiment': 'Disabled',
                'Test Name': 'Sample Test 2',
                'Test Mode': 'Debug',
                'Test Type': 'Sweep',
                'Type': 'frequency',
                'Domain': 'ia',
                'Start': 16,
                'End': 32,
                'Steps': 4,
                'External Mask': None
            }
        }
    
    def tearDown(self):
        """Clean up after each test"""
        try:
            if hasattr(self.control_panel, 'main_thread_handler'):
                self.control_panel.main_thread_handler.cleanup()
            
            # Destroy the root window
            if self.root:
                self.root.destroy()
        except Exception as e:
            print(f"Teardown error: {e}")
    
    # ==================== INITIALIZATION TESTS ====================
    
    def test_control_panel_initialization(self):
        """Test that control panel initializes correctly"""
        self.assertIsNotNone(self.control_panel.root)
        self.assertIsNotNone(self.control_panel.main_thread_handler)
        self.assertIsNotNone(self.control_panel.framework_manager)
        self.assertEqual(self.control_panel.thread_active, False)
        self.assertIsInstance(self.control_panel.experiments_data, dict)
        self.assertIsInstance(self.control_panel.experiment_states, dict)
    
    def test_framework_manager_initialization(self):
        """Test framework manager is properly initialized"""
        self.assertIsNotNone(self.control_panel.framework_api)
    
    def test_ui_components_creation(self):
        """Test that UI components are created"""
        # Check main panels exist
        self.assertTrue(hasattr(self.control_panel, 'left_frame'))
        self.assertTrue(hasattr(self.control_panel, 'right_frame'))
        
        # Check key buttons exist
        self.assertTrue(hasattr(self.control_panel, 'run_button'))
        self.assertTrue(hasattr(self.control_panel, 'cancel_button'))
        self.assertTrue(hasattr(self.control_panel, 'hold_button'))
        self.assertTrue(hasattr(self.control_panel, 'end_button'))
        
        # Check progress bars exist
        self.assertTrue(hasattr(self.control_panel, 'overall_progress_bar'))
        self.assertTrue(hasattr(self.control_panel, 'iteration_progress_bar'))
        
        # Check status log exists
        self.assertTrue(hasattr(self.control_panel, 'status_log'))
    
    # ==================== EXPERIMENT MANAGEMENT TESTS ====================
    
    def test_load_experiments(self):
        """Test loading experiments"""
        with patch('UI.ControlPanel.OpenExperiment', return_value=self.sample_experiments):
            self.control_panel.load_experiments('dummy_path.xlsx')
        
        self.assertEqual(self.control_panel.experiments, self.sample_experiments)
        self.assertIn('Test_Experiment_1', self.control_panel.experiment_states)
        self.assertTrue(self.control_panel.experiment_states['Test_Experiment_1'])
        self.assertFalse(self.control_panel.experiment_states['Test_Experiment_2'])
    
    def test_experiment_state_update(self):
        """Test updating experiment state"""
        self.control_panel.experiments = self.sample_experiments.copy()
        
        # Test enabling experiment
        self.control_panel._update_experiment_state('Test_Experiment_1', True)
        self.assertTrue(self.control_panel.experiment_states['Test_Experiment_1'])
        
        # Test disabling experiment
        self.control_panel._update_experiment_state('Test_Experiment_1', False)
        self.assertFalse(self.control_panel.experiment_states['Test_Experiment_1'])
    
    def test_create_primitive_experiment_data(self):
        """Test creating thread-safe primitive data"""
        self.control_panel.experiments = self.sample_experiments.copy()
        
        primitive_data = self.control_panel._create_primitive_experiment_data('Test_Experiment_1')
        
        self.assertIsInstance(primitive_data, dict)
        self.assertEqual(primitive_data['experiment_name'], 'Test_Experiment_1')
        self.assertEqual(primitive_data['Test Name'], 'Sample Test 1')
        self.assertEqual(primitive_data['Test Type'], 'Loops')
        self.assertEqual(primitive_data['Loops'], 5)
    
    # ==================== EXECUTION TESTS ====================
    
    def test_start_tests_thread_no_experiments(self):
        """Test starting tests with no experiments enabled"""
        self.control_panel.experiment_states = {'Test_1': False, 'Test_2': False}
        
        with patch.object(self.control_panel, 'log_status') as mock_log:
            self.control_panel.start_tests_thread()
            mock_log.assert_called_with("No experiments enabled")
    
    def test_start_tests_thread_with_experiments(self):
        """Test starting tests with enabled experiments"""
        self.control_panel.experiments = self.sample_experiments.copy()
        self.control_panel.experiment_states = {'Test_Experiment_1': True, 'Test_Experiment_2': False}
        
        with patch.object(self.control_panel, '_prepare_framework_for_execution', return_value=True):
            with patch('threading.Thread') as mock_thread:
                mock_thread_instance = Mock()
                mock_thread.return_value = mock_thread_instance
                
                self.control_panel.start_tests_thread()
                
                # Verify thread was created and started
                mock_thread.assert_called_once()
                mock_thread_instance.start.assert_called_once()
                self.assertTrue(self.control_panel.thread_active)
    
    def test_framework_preparation(self):
        """Test framework preparation for execution"""
        # Mock the framework API
        mock_api = Mock()
        mock_api.get_current_state.return_value = {'ready': True}
        self.control_panel.framework_api = mock_api
        
        result = self.control_panel._prepare_framework_for_execution()
        self.assertTrue(result)
        mock_api.get_current_state.assert_called_once()
    
    # ==================== COMMAND SYSTEM TESTS ====================
    
    def test_toggle_framework_hold_no_api(self):
        """Test hold toggle when no API is available"""
        self.control_panel.framework_api = None
        
        with patch.object(self.control_panel, 'log_status') as mock_log:
            self.control_panel.toggle_framework_hold()
            mock_log.assert_called_with("No Framework API available")
    
    def test_toggle_framework_hold_not_running(self):
        """Test hold toggle when not running"""
        mock_api = Mock()
        mock_api.get_current_state.return_value = {'is_running': False}
        self.control_panel.framework_api = mock_api
        
        with patch.object(self.control_panel, 'log_status') as mock_log:
            self.control_panel.toggle_framework_hold()
            mock_log.assert_called_with("No active execution to control")
    
    def test_end_current_experiment(self):
        """Test ending current experiment"""
        mock_api = Mock()
        mock_api.end_experiment.return_value = {
            'success': True,
            'message': 'End command sent'
        }
        self.control_panel.framework_api = mock_api
        
        with patch.object(self.control_panel, 'log_status') as mock_log:
            self.control_panel.end_current_experiment()
            
            mock_api.end_experiment.assert_called_once()
            mock_log.assert_called_with('End command sent')
    
    def test_cancel_tests(self):
        """Test cancelling tests"""
        mock_api = Mock()
        mock_api.cancel_experiment.return_value = {
            'success': True,
            'message': 'Cancel command sent'
        }
        self.control_panel.framework_api = mock_api
        
        with patch.object(self.control_panel, 'log_status') as mock_log:
            with patch.object(self.control_panel.root, 'after') as mock_after:
                self.control_panel.cancel_tests()
                
                mock_api.cancel_experiment.assert_called_once()
                mock_log.assert_called_with('Cancel command sent')
                self.assertFalse(self.control_panel.thread_active)
                mock_after.assert_called_once()
    
    # ==================== PROGRESS TRACKING TESTS ====================
    
    def test_update_overall_progress_no_experiments(self):
        """Test overall progress update with no experiments"""
        self.control_panel.total_experiments = 0
        
        self.control_panel._update_overall_progress()
        
        if hasattr(self.control_panel, 'overall_progress_var'):
            self.assertEqual(self.control_panel.overall_progress_var.get(), 0)
    
    def test_update_overall_progress_with_experiments(self):
        """Test overall progress update with experiments"""
        self.control_panel.total_experiments = 5
        self.control_panel.current_experiment_index = 2
        self.control_panel.total_iterations_in_experiment = 10
        self.control_panel.current_iteration = 5
        self.control_panel.current_iteration_progress = 0.5
        
        self.control_panel._update_overall_progress()
        
        # Progress should be calculated correctly
        if hasattr(self.control_panel, 'overall_progress_var'):
            progress = self.control_panel.overall_progress_var.get()
            self.assertGreater(progress, 0)
            self.assertLessEqual(progress, 100)
    
    # ==================== STATUS MANAGEMENT TESTS ====================
    
    def test_log_status(self):
        """Test status logging functionality"""
        test_message = "Test status message"
        
        # Mock the status log widget
        with patch.object(self.control_panel.status_log, 'configure'):
            with patch.object(self.control_panel.status_log, 'insert') as mock_insert:
                with patch.object(self.control_panel.status_log, 'see'):
                    self.control_panel.log_status(test_message)
                    
                    # Verify message was inserted
                    mock_insert.assert_called()
                    call_args = mock_insert.call_args[0]
                    self.assertIn(test_message, call_args[1])
    
    def test_update_experiment_status_safe(self):
        """Test safe experiment status update"""
        # Create mock experiment frames
        mock_label = Mock()
        mock_label.winfo_exists.return_value = True
        
        self.control_panel.experiment_frames = [{
            'experiment_name': 'Test_Experiment_1',
            'run_label': mock_label
        }]
        
        self.control_panel._update_experiment_status_safe(
            'Test_Experiment_1', 'Running', '#00008B', 'white'
        )
        
        mock_label.configure.assert_called_with(text='Running', bg='#00008B', fg='white')
    
    def test_cleanup_experiment_statuses(self):
        """Test experiment status cleanup"""
        # Create mock experiment frames
        mock_label = Mock()
        mock_label.winfo_exists.return_value = True
        
        self.control_panel.experiment_frames = [{
            'experiment_name': 'Test_Experiment_1',
            'run_label': mock_label,
            'current_status': 'Running',
            'status_timestamp': time.time()
        }]
        
        self.control_panel._cleanup_experiment_statuses()
        
        mock_label.configure.assert_called_with(text='Idle', bg='lightgray', fg='black')
    
    # ==================== ERROR HANDLING TESTS ====================
    
    def test_error_handling_in_status_update(self):
        """Test error handling in status updates"""
        # Create a scenario that would cause an error
        self.control_panel.experiment_frames = [{
            'experiment_name': 'Test_Experiment_1',
            'run_label': None  # This will cause an error
        }]
        
        # Should not raise an exception
        with patch.object(self.control_panel, 'log_status') as mock_log:
            self.control_panel._update_experiment_status_safe(
                'Test_Experiment_1', 'Running', '#00008B', 'white'
            )
            # Should log an error
            mock_log.assert_called()
    
    def test_error_handling_in_progress_update(self):
        """Test error handling in progress updates"""
        # Should not raise an exception even with invalid data
        invalid_data = {'invalid_key': 'invalid_value'}
        
        try:
            self.control_panel._coordinate_progress_updates('strategy_progress', invalid_data)
        except Exception as e:
            self.fail(f"Progress update should handle errors gracefully: {e}")
    
    # ==================== CLEANUP TESTS ====================
    
    def test_on_closing_cleanup(self):
        """Test proper cleanup on window closing"""
        with patch.object(self.control_panel.main_thread_handler, 'cleanup') as mock_cleanup:
            with patch.object(self.control_panel.framework_manager, 'cleanup_current_instance') as mock_framework_cleanup:
                with patch.object(self.control_panel.root, 'after_idle') as mock_after_idle:
                    
                    self.control_panel.on_closing()
                    
                    mock_cleanup.assert_called_once()
                    mock_framework_cleanup.assert_called_once()
                    mock_after_idle.assert_called()


class TestMockFramework(unittest.TestCase):
    """Test the mock framework itself"""
    
    def setUp(self):
        self.framework = MockFramework()
    
    def test_mock_framework_initialization(self):
        """Test mock framework initializes correctly"""
        self.assertIsNotNone(self.framework.config)
        self.assertIsNotNone(self.framework.s2t_config)
        self.assertIsNotNone(self.framework.status_manager)
        self.assertIsNotNone(self.framework.execution_state)
    
    def test_mock_recipe_executor_loops(self):
        """Test mock recipe executor with loops"""
        data = {'Test Type': 'Loops', 'Loops': 3}
        result = self.framework.RecipeExecutor(data)
        self.assertEqual(len(result), 3)
        self.assertTrue(all(status == 'PASS' for status in result))
    
    def test_mock_recipe_executor_sweep(self):
        """Test mock recipe executor with sweep"""
        data = {'Test Type': 'Sweep', 'Start': 10, 'End': 20, 'Steps': 5}
        result = self.framework.RecipeExecutor(data)
        self.assertEqual(len(result), 3)  # (20-10)/5 + 1 = 3
        self.assertTrue(all(status == 'PASS' for status in result))
    
    def test_mock_execution_commands(self):
        """Test mock execution commands"""
        # Test end experiment
        success = self.framework.end_experiment()
        self.assertTrue(success)
        self.assertTrue(self.framework.execution_state.is_ended())
        
        # Test cancel
        success = self.framework.cancel_execution()
        self.assertTrue(success)
        self.assertTrue(self.framework.execution_state.is_cancelled())


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestControlPanelSafe,
        TestMockFramework
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        print(f"Success rate: {success_rate:.1f}%")
    print(f"{'='*50}")