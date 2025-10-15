import os
import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
from colorama import Fore

from core.interfaces import IStatusReporter
from core.factory import StrategyFactory, ContentBuilderFactory, ExecutorFactory
from configurations.test_configurations import TestConfiguration, SystemToTesterConfig
from content.configurations import DragonConfiguration, LinuxConfiguration, ConfigurationMapping
from enums.framework_enums import ContentType, TestTarget, VoltageType, TestType, ExecutionMode
from execution.result_processor import TestResultProcessor
from utils.misc_utils import print_custom_separator

class Framework:
    """Main framework class with static methods for interface compatibility"""
    
    def __init__(self, upload_to_database: bool = True, status_reporter: Optional[IStatusReporter] = None):
        self.upload_to_database = upload_to_database
        self.config = TestConfiguration()
        self.s2t_config = SystemToTesterConfig()
        self.dragon_content = DragonConfiguration()
        self.linux_content = LinuxConfiguration()
        self.content_config = None
        self.unit_data = None
        self.cancel_flag = None
        self._current_strategy = None
        self._current_executor = None

        # Status reporting
        self._status_reporter = status_reporter
        self._status_enabled = True

        # Control flags
        self._halt_flag = threading.Event()
        self._continue_flag = threading.Event()
        self._command_lock = threading.Lock()
        self._is_halted = False

        # Progress tracking
        self.current_experiment_name = None
        self.current_experiment_total = 0
        self.current_experiment_completed = 0

        # Unified END command control
        self._end_experiment_flag = threading.Event()
        self._end_command_lock = threading.Lock()
        
        # Step-by-step execution control
        self._step_mode_enabled = False
        self._step_continue_flag = threading.Event()
        self._iteration_complete_flag = threading.Event()
        self._step_command_lock = threading.Lock()

        # Current execution state for external monitoring
        self._current_execution_state = {
            'is_running': False,
            'current_iteration': 0,
            'total_iterations': 0,
            'iteration_results': [],
            'current_stats': {},
            'waiting_for_command': False,
            'experiment_name': None,
            'end_requested': False
        }

    def end_experiment(self):
        """End current experiment after current iteration completes"""
        with self._end_command_lock:
            if not self._current_execution_state['is_running']:
                self.FrameworkPrint("No experiment currently running", 2)
                return False
            
            self._end_experiment_flag.set()
            self._current_execution_state['end_requested'] = True
                
            # If in step-by-step mode and waiting, also release the wait
            if self._step_mode_enabled and self._current_execution_state['waiting_for_command']:
                self._step_continue_flag.set()
                self._current_execution_state['waiting_for_command'] = False
                
            # Log to console/file only
            if self._current_executor and hasattr(self._current_executor, 'gdflog'):
                self._current_executor.gdflog.log("END EXPERIMENT command received - will finish current iteration and stop", 2)
            else:
                self.FrameworkPrint("END EXPERIMENT command received - will finish current iteration and stop", 2)
                
            return True

    def _send_status_update(self, status_type: str, data: Dict[str, Any]):
        """Send status update through reporter"""
        if not self._status_enabled or not self._status_reporter:
            return
              
        try:
            status_data = {
                'type': status_type,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            self._status_reporter.report_status(status_data)

        except Exception as e:
            # Don't let status updates break execution
            print(f"Status update error: {e}")

    def enable_step_by_step_mode(self):
        """Enable step-by-step execution mode"""
        with self._step_command_lock:
            self._step_mode_enabled = True
            self.config.execution_mode = ExecutionMode.STEP_BY_STEP
            self._reset_step_flags()
                
            self._send_status_update('step_mode_enabled', {
                'message': 'Step-by-step execution mode enabled',
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name)
            })
            
            if self._current_executor and hasattr(self._current_executor, 'gdflog'):
                self._current_executor.gdflog.log("Step-by-step execution mode enabled", 1)

    def _reset_step_flags(self):
        """Reset step-by-step execution flags"""
        self._step_continue_flag.clear()
        self._iteration_complete_flag.clear()
        self._current_execution_state['waiting_for_command'] = False

    def disable_step_by_step_mode(self):
        """Disable step-by-step execution mode"""
        with self._step_command_lock:
            self._step_mode_enabled = False
            self.config.execution_mode = ExecutionMode.CONTINUOUS
            self._step_continue_flag.set()  # Release any waiting
            
            self._send_status_update('step_mode_disabled', {
                'message': 'Step-by-step execution mode disabled - switching to continuous mode',
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name)
            })

    def step_continue(self):
        """Continue to next iteration in step-by-step mode"""
        with self._step_command_lock:
            if not self._step_mode_enabled:
                self.FrameworkPrint("Step-by-step mode is not enabled", 2)
                return False
                
            if not self._current_execution_state['waiting_for_command']:
                self.FrameworkPrint("No iteration waiting for continue command", 2)
                return False
            
            # Check if end was already requested
            if self._current_execution_state['end_requested']:
                self.FrameworkPrint("Experiment end already requested - cannot continue", 2)
                return False
            
            self._step_continue_flag.set()
            self._current_execution_state['waiting_for_command'] = False
                
            self._send_status_update('step_continue_issued', {
                'current_iteration': self._current_execution_state['current_iteration'],
                'total_iterations': self._current_execution_state['total_iterations'],
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name)
            })
            
            if self._current_executor and hasattr(self._current_executor, 'gdflog'):
                self._current_executor.gdflog.log("CONTINUE command received - proceeding to next iteration", 1)
            
            return True

    def halt_execution(self):
        """Halt test execution after current iteration completes"""
        with self._command_lock:
            self._halt_flag.set()
            self._continue_flag.clear()
            self._is_halted = True

            # Send halt notification
            self._send_status_update('execution_halted', {
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'current_iteration': self.config.tnumber if self._current_executor else 0
            })
                
            # Use executor logger if available, fallback to FrameworkPrint
            if self._current_executor and hasattr(self._current_executor, 'gdflog'):
                self._current_executor.gdflog.log("HALT command issued - execution will pause after current iteration", 1)
            else:
                self.FrameworkPrint("HALT command issued - execution will pause after current iteration", 1)

    def continue_execution(self):
        """Continue halted test execution"""
        with self._command_lock:
            if self._is_halted:
                self._continue_flag.set()
                self._halt_flag.clear()
                self._is_halted = False

                # Send continue notification
                self._send_status_update('execution_resumed', {
                    'test_name': self.config.name,
                    'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                    'current_iteration': self.config.tnumber if self._current_executor else 0
                })
                    
                # Use executor logger if available
                if self._current_executor and hasattr(self._current_executor, 'gdflog'):
                    self._current_executor.gdflog.log("CONTINUE command issued - execution will resume", 1)
                else:
                    self.FrameworkPrint("CONTINUE command issued - execution will resume", 1)
            else:
                # Use executor logger if available
                if self._current_executor and hasattr(self._current_executor, 'gdflog'):
                    self._current_executor.gdflog.log("No halted execution to continue", 2)
                else:
                    self.FrameworkPrint("No halted execution to continue", 2)

    def cancel_execution(self):
        """Cancel test execution"""
        with self._command_lock:
            if self.cancel_flag:
                self.cancel_flag.set()

            # Also set end flag to ensure clean shutdown
            self._end_experiment_flag.set()
            self._current_execution_state['end_requested'] = True

            self._continue_flag.set()  # Release any waiting halt
            self._step_continue_flag.set()  # Release step wait
            self._halt_flag.clear()
            self._is_halted = False

            if self._current_execution_state['waiting_for_command']:
                self._current_execution_state['waiting_for_command'] = False

            # Log to console/file only
            if self._current_executor and hasattr(self._current_executor, 'gdflog'):
                self._current_executor.gdflog.log("CANCEL command issued - execution will stop", 2)
            else:
                self.FrameworkPrint("CANCEL command issued - execution will stop", 2)

    def _wait_for_step_command(self, current_iteration: int, total_iterations: int, 
                              latest_result, logger=None) -> bool:
        """Wait for step command after iteration completion"""
        if not self._step_mode_enabled:
            return True  # Continue normally if step mode disabled
        
        # Check if end was requested before waiting
        if self._check_end_experiment_request():
            return False
        
        log_func = logger.log if logger else self.FrameworkPrint
        
        # Update execution state
        with self._step_command_lock:
            self._current_execution_state['waiting_for_command'] = True
            self._current_execution_state['current_iteration'] = current_iteration
            
            # Add latest result to history
            if latest_result:
                self._current_execution_state['iteration_results'].append(latest_result)
        
        # Calculate and send current statistics
        current_stats = self._calculate_current_stats(self._current_execution_state['iteration_results'])
        
        # Send iteration complete notification with stats
        self._send_status_update('step_iteration_complete', {
            'current_iteration': current_iteration,
            'total_iterations': total_iterations,
            'latest_result': {
                'iteration': latest_result.iteration,
                'status': latest_result.status,
                'scratchpad': latest_result.scratchpad,
                'seed': latest_result.seed
            } if latest_result else None,
            'current_stats': current_stats,
            'waiting_for_command': True
        })
        
        log_func(f"=== STEP-BY-STEP: Iteration {current_iteration}/{total_iterations} COMPLETED ===", 1)
        log_func(f"Latest Result: {latest_result.status} - {latest_result.scratchpad}" if latest_result else "No result", 1)
        log_func(f"Current Stats: {current_stats['pass_count']} PASS, {current_stats['fail_count']} FAIL, {current_stats['pass_rate']}% pass rate", 1)
        log_func("Waiting for external command:", 1)
        log_func("  - framework.step_continue()     # Continue to next iteration", 1)
        log_func("  - framework.end_experiment()    # End experiment after current iteration", 1)
        log_func("  - framework.cancel_execution()  # Cancel immediately", 1)
        log_func("  - framework.get_execution_state() # Get current state", 1)
        
        # Wait for command
        while True:
            # Check for end experiment command (highest priority)
            if self._check_end_experiment_request():
                log_func("=== EXPERIMENT ENDED BY END COMMAND ===", 2)
                return False
            
            # Check for continue command
            if self._step_continue_flag.wait(timeout=1.0):
                self._step_continue_flag.clear()  # Reset for next iteration
                log_func("=== CONTINUING TO NEXT ITERATION ===", 1)
                return True
            
            # Check for cancellation (existing functionality)
            if self.cancel_flag and self.cancel_flag.is_set():
                log_func("Execution cancelled by user", 2)
                return False

    def _wait_for_continue_or_cancel(self, current_iteration: int, total_iterations: int = None, logger=None):
        """Wait for continue or cancel command when halted"""
        if not self._halt_flag.is_set():
            return True  # Not halted, continue normally
        
        # Use provided logger or fallback to FrameworkPrint
        log_func = logger.log if logger else self.FrameworkPrint
        
        total_str = f"/{total_iterations}" if total_iterations else ""
        log_func(f"=== EXECUTION HALTED after iteration {current_iteration}{total_str} ===", 1)
        log_func("Waiting for command: use continue_execution() or cancel_execution()", 1)
        log_func("Commands available:", 1)
        log_func("  - framework.continue_execution()  # Resume execution", 1)
        log_func("  - framework.cancel_execution()    # Cancel execution", 1)
        
        # Wait for either continue or cancel
        while True:
            # Check if cancel was requested
            if self.cancel_flag and self.cancel_flag.is_set():
                log_func("Execution cancelled by user", 2)
                return False
            
            # Wait for continue flag with timeout to check cancel periodically
            if self._continue_flag.wait(timeout=1.0):
                log_func("=== EXECUTION RESUMED ===", 1)
                return True

    def _calculate_current_stats(self, results: List) -> Dict[str, Any]:
        """Calculate current statistics from test results"""
        if not results:
            return {
                'total_completed': 0,
                'pass_count': 0,
                'fail_count': 0,
                'cancelled_count': 0,
                'execution_fail_count': 0,
                'other_count': 0,
                'pass_rate': 0.0,
                'fail_rate': 0.0,
                'valid_tests': 0,
                'latest_status': 'None',
                'latest_iteration': 0
            }
        
        # Count different result types
        status_counts = {}
        for result in results:
            status = result.status.upper() if result.status else 'UNKNOWN'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate specific counts
        pass_count = (status_counts.get('PASS', 0) + 
                    status_counts.get('SUCCESS', 0) + 
                    status_counts.get('*', 0))
        
        fail_count = (status_counts.get('FAIL', 0) + 
                    status_counts.get('FAILED', 0) + 
                    status_counts.get('ERROR', 0))
        
        cancelled_count = status_counts.get('CANCELLED', 0)
        execution_fail_count = status_counts.get('EXECUTIONFAIL', 0)
        
        total_completed = len(results)
        
        # Calculate valid tests (excluding cancelled and execution failures)
        valid_tests = total_completed - cancelled_count - execution_fail_count
        
        # Calculate other/unknown status count
        other_count = total_completed - pass_count - fail_count - cancelled_count - execution_fail_count
        
        # Calculate rates
        if valid_tests > 0:
            pass_rate = (pass_count / valid_tests) * 100
            fail_rate = (fail_count / valid_tests) * 100
        else:
            pass_rate = 0.0
            fail_rate = 0.0
        
        # Get latest result info
        latest_result = results[-1] if results else None
        latest_status = latest_result.status if latest_result else 'None'
        latest_iteration = latest_result.iteration if latest_result else 0
        
        return {
            'total_completed': total_completed,
            'pass_count': pass_count,
            'fail_count': fail_count,
            'cancelled_count': cancelled_count,
            'execution_fail_count': execution_fail_count,
            'other_count': other_count,
            'pass_rate': round(pass_rate, 1),
            'fail_rate': round(fail_rate, 1),
            'valid_tests': valid_tests,
            'latest_status': latest_status,
            'latest_iteration': latest_iteration,
            'status_breakdown': status_counts,
            'success_rate': round(pass_rate, 1)  # Alias for pass_rate for compatibility
        }

    def _get_strategy_total_iterations(self, strategy) -> int:
        """Get total number of iterations for a strategy"""
        if hasattr(strategy, 'loops'):
            return strategy.loops
        elif hasattr(strategy, 'values'):
            return len(strategy.values)
        elif hasattr(strategy, 'x_values') and hasattr(strategy, 'y_values'):
            return len(strategy.x_values) * len(strategy.y_values)
        return 0

    def _reset_halt_flags(self):
        """Reset halt flags for new test execution"""
        with self._command_lock:
            self._halt_flag.clear()
            self._continue_flag.clear()
            self._is_halted = False

    def _check_end_experiment_request(self) -> bool:
        """Check if experiment end was requested"""
        return self._end_experiment_flag.is_set()

    def _reset_experiment_flags(self):
        """Reset all experiment control flags for new execution"""
        with self._end_command_lock:
            self._end_experiment_flag.clear()
            self._current_execution_state['end_requested'] = False
            self._current_execution_state['is_running'] = False
            self._current_execution_state['waiting_for_command'] = False
        
        with self._step_command_lock:
            self._reset_step_flags()
        
        with self._command_lock:
            self._halt_flag.clear()
            self._continue_flag.clear()
            self._is_halted = False
        
        # Clear cancel flag if it exists
        if self.cancel_flag:
            self.cancel_flag.clear()
        
        self.FrameworkPrint("Framework ready for new execution", 1)

    def _setup_strategy_environment(self) -> Dict:
        """Setup environment once per strategy execution"""
        # Import here to avoid circular dependencies
        import users.gaespino.dev.DebugFramework.FileHandler as fh
        from ..utils.misc_utils import logs_dest
        
        # Create test folder for the entire strategy
        description = f'T{self.config.tnumber}_{self.config.name}'
        self.config.tfolder = fh.create_log_folder(logs_dest, description)
        
        # Copy TTL files once for the entire strategy and store them in config
        self._copy_ttl_files_to_config()
        Framework.FrameworkPrint(f"Strategy environment setup complete. Test folder: {self.config.tfolder}", 1)

    def _copy_ttl_files_to_config(self) -> Dict:
        """Copy TTL files once for the entire test strategy"""
        # Import here to avoid circular dependencies
        import users.gaespino.dev.DebugFramework.FileHandler as fh
        from ..utils.misc_utils import macro_cmds, ttl_dest, macros_path
        
        if not self.config.macro_folder:
            Framework.FrameworkPrint("Using default TTL files (no macro folder specified)", 1)
            self.config.ttl_files_dict = macro_cmds
            self.config.ttl_path = ttl_dest # Default Value
            return   # Default TTL files
        
        Framework.FrameworkPrint(f"Copying TTL files from: {self.config.macro_folder}", 1)
        
        replace = 'Y'
        self.config.ttl_path = fh.create_path(folder=self.config.tfolder, file='TTL')
        fh.create_folder_if_not_exists(self.config.ttl_path)
        fh.copy_files(self.config.macro_folder, self.config.ttl_path, uinput=replace)
        
        self.config.ttl_files_dict = macros_path(self.config.ttl_path)
        Framework.FrameworkPrint(f"TTL files copied to: {self.config.ttl_path}", 1)

    def _create_executor(self):
        """Create test executor with current configuration"""
        return ExecutorFactory.create_executor(
            config=self.config, 
            s2t_config=self.s2t_config, 
            cancel_flag=self.cancel_flag
        )
    
    def _execute_strategy_and_process_results(self, strategy, test_type: str) -> List[str]:
        """Execute strategy and process results"""
        self._current_strategy = strategy

        # IMPORTANT: Reset all flags at the start of new execution
        self._reset_experiment_flags()

        # Get total iterations for this experiment
        total_iterations = self._get_strategy_total_iterations(strategy)
            
        # Send experiment start notification
        self._send_status_update('experiment_start', {
            'experiment_name': self.current_experiment_name or self.config.name,
            'strategy_type': test_type,
            'test_name': self.config.name,
            'total_iterations': total_iterations
        })

        # Reset halt flags for new execution
        self._reset_halt_flags()
        
        # Setup TTL files and test environment once per strategy
        Framework.FrameworkPrint(f"Setting up {test_type} test environment...", 1)
        self._setup_strategy_environment()

        # Create executor
        executor = self._create_executor()
        self._current_executor = executor

        # Define logging
        executor.gdflog.log(f"Starting {test_type} test execution...", 1)
                
        Framework.FrameworkPrint(f"Starting {test_type} test execution...", 1)
        results = strategy.execute(executor, halt_controller=self)
        
        BAD_RESULTS = ["CANCELLED", "ExecutionFAIL"]

        # Generate summary and send to UI
        if results and results[-1].status not in BAD_RESULTS:
            summary_data = self._generate_summary_data(results, test_type)
            self._send_status_update('strategy_complete', summary_data)
            self._generate_summary(results, test_type, self.config.tfolder, executor)
        else:
            # Send failure summary
            self._send_status_update('experiment_failed', {
                'experiment_name': self.current_experiment_name or self.config.name,
                'strategy_type': test_type,
                'test_name': self.config.name,
                'reason': results[-1].status if results else 'Unknown',
                'completed_iterations': len(results)
            })
            
        return [result.status for result in results]

    def _generate_summary_data(self, results: List, test_type: str) -> Dict[str, Any]:
        """Generate summary data for UI"""
        total_tests = len(results)
        if total_tests == 0:
            return {}
        
        # Count different result types
        status_counts = {}
        for result in results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        # Calculate success rate
        valid_tests = total_tests - status_counts.get('CANCELLED', 0) - status_counts.get('ExecutionFAIL', 0)
        passed_tests = status_counts.get('PASS', 0) + status_counts.get('*', 0)
        success_rate = (passed_tests / valid_tests * 100) if valid_tests > 0 else 0
        
        # Get failure patterns
        failure_patterns = {}
        for result in results:
            if result.status == "FAIL" and result.scratchpad:
                pattern = result.scratchpad
                failure_patterns[pattern] = failure_patterns.get(pattern, 0) + 1
        
        return {
            'strategy_type': test_type,
            'test_name': self.config.name,
            'total_tests': total_tests,
            'status_counts': status_counts,
            'success_rate': round(success_rate, 1),
            'valid_tests': valid_tests,
            'failure_patterns': dict(sorted(failure_patterns.items(), key=lambda x: x[1], reverse=True)),
            'first_fail_iteration': next((r.iteration for r in results if r.status == "FAIL"), None),
            'execution_time': results[-1].timestamp - results[0].timestamp if results else 0
        }

    def _generate_summary(self, results: List, test_type: str, tfolder: str, executor):
        """Generate test summary and upload data"""
        logger = executor.gdflog

        # Log test series completion
        logger.log(print_custom_separator(f'{test_type} Test Series Completed'), 1)
        
        # Log individual test results first
        logger.log('Individual Test Results:', 1)
        logger.log('-' * 80, 1)
        logger.log(f"{'Iteration':<10} {'Status':<15} {'Name':<30} {'Scratchpad':<15} {'Seed':<10}", 1)
        logger.log('-' * 80, 1)

        for result in results:
            logger.log(
                f"{result.iteration:<10} {result.status:<15} {result.name[:29]:<30} "
                f"{result.scratchpad[:14]:<15} {result.seed[:9]:<10}", 1
            )
            
        # Check if we should skip upload based on test results
        should_upload = self._should_upload_data(results, logger)

        logger.log('-' * 80, 1)

        if test_type == "Shmoo" and isinstance(self._current_strategy, type(self._current_strategy)):
            # For 2D shmoo, get the axis values from the strategy
            if hasattr(self._current_strategy, 'get_axis_values'):
                x_values, y_values = self._current_strategy.get_axis_values()
                shmoo_df, legends_df = TestResultProcessor.create_2d_shmoo_data(
                    results, x_values, y_values
                )
                    
                logger.log(f'\n2D Shmoo Plot Configuration:', 1)
                logger.log(f'X-axis: {x_values}', 1)
                logger.log(f'Y-axis: {y_values}', 1)
                logger.log(f'Matrix Dimensions: {shmoo_df.shape[0]} rows x {shmoo_df.shape[1]} columns', 1)
            else:
                shmoo_df, legends_df = TestResultProcessor.create_shmoo_data(results, test_type)
        else:
            # For 1D tests (loops, sweeps), use the regular method
            shmoo_df, legends_df = TestResultProcessor.create_shmoo_data(results, test_type)
        
        # Log the shmoo matrix
        logger.log(f'\n{test_type} Results Matrix:', 1)
        logger.log('=' * 50, 1)
        
        # For better formatting in logs, convert to string with proper spacing
        shmoo_str = shmoo_df.to_string(max_cols=None, max_rows=None)
        for line in shmoo_str.split('\n'):
            if line.strip():  # Only log non-empty lines
                logger.log(line, 1)
        
        # Log legends
        logger.log('\nFailure Legends:', 1)
        logger.log('=' * 30, 1)
        if not legends_df.empty:
            for idx, row in legends_df.iterrows():
                logger.log(f"{row['Legends']}", 1)
        else:
            logger.log('No failures recorded - All tests passed!', 1)		

        self._log_test_statistics(results, logger)

        # Upload data Definition
        if should_upload:
            logger.log('\nData Upload Process:', 1)
            logger.log('=' * 30, 1)
            
            # Import here to avoid circular dependencies
            import users.gaespino.dev.S2T.dpmChecks as dpm
            import users.gaespino.dev.S2T.SetTesterRegs as s2t
            import users.gaespino.dev.DebugFramework.FileHandler as fh
            
            WW = str(dpm.getWW())
            product = s2t.SELECTED_PRODUCT
            
            datahandler = fh.TestUpload(
                folder=tfolder,
                vid=self.config.visual,
                name=self.config.name,
                bucket=self.config.bucket,
                WW=WW,
                product=product,
                logger=logger.log,
                from_Framework=True,
                upload_to_disk=True,
                upload_to_danta=self.upload_to_database
            )
            
            datahandler.generate_summary()
            datahandler.upload_data()
            logger.log('Database upload completed successfully', 1)

        else:
            self._log_upload_skipped_reason(results, logger)
        
        # Final completion message
        logger.log(print_custom_separator(f'{test_type} Summary Generation Completed'), 1)

    def _should_upload_data(self, results: List, logger) -> bool:
        """Determine if data should be uploaded based on test results"""
        if not results:
            logger.log('No results to evaluate for upload decision', 2)
            return False
        
        # Check for critical failure conditions
        critical_statuses = {'CANCELLED', 'ExecutionFAIL', 'FAILED'}
        
        # Count critical failures
        critical_failures = sum(1 for result in results if result.status in critical_statuses)
        total_tests = len(results)
        
        # If more than 50% of tests have critical failures, skip upload
        critical_failure_rate = critical_failures / total_tests if total_tests > 0 else 0
        
        # Check if the last test (most recent) had a critical failure
        last_test_critical = results[-1].status in critical_statuses
        
        # Check if ALL tests failed critically
        all_critical = all(result.status in critical_statuses for result in results)
        
        # Decision logic
        if all_critical:
            logger.log('Upload skipped: All tests had critical failures', 2)
            return False
        elif last_test_critical and critical_failure_rate > 0.5:
            logger.log(f'Upload skipped: Last test failed critically and {critical_failure_rate:.1%} of tests had critical failures', 2)
            return False
        elif critical_failure_rate >= 0.8:  # 80% or more critical failures
            logger.log(f'Upload skipped: {critical_failure_rate:.1%} of tests had critical failures', 2)
            return False
        else:
            # Check if we have any successful tests
            successful_tests = sum(1 for result in results if result.status not in {'FAILED', 'CANCELLED', 'ExecutionFAIL'})
            if successful_tests == 0:
                logger.log('Upload skipped: No successful tests found', 2)
                return False
            
            logger.log(f'Upload approved: {successful_tests}/{total_tests} tests successful, {critical_failure_rate:.1%} critical failure rate', 1)
            return True

    def _log_upload_skipped_reason(self, results: List, logger):
        """Log detailed reason why upload was skipped"""
        logger.log('\nData Upload Status:', 1)
        logger.log('=' * 30, 1)
        logger.log('Upload SKIPPED due to test execution issues', 2)
        
        # Analyze and report the reasons
        status_counts = {}
        for result in results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        total_tests = len(results)
        
        logger.log('Reason Analysis:', 2)
        if 'CANCELLED' in status_counts:
            cancelled_count = status_counts['CANCELLED']
            logger.log(f'- {cancelled_count}/{total_tests} tests were cancelled by user', 2)
        
        if 'ExecutionFAIL' in status_counts:
            exec_fail_count = status_counts['ExecutionFAIL']
            logger.log(f'- {exec_fail_count}/{total_tests} tests had execution failures', 2)
        
        # Check if series was incomplete
        if results and results[-1].status in {'CANCELLED', 'ExecutionFAIL'}:
            logger.log('- Test series ended prematurely due to critical failure', 2)
        
        logger.log('Data saved locally for debugging purposes only', 1)
        logger.log('No database upload performed', 1)

    def _log_test_statistics(self, results: List, logger):
        """Log detailed test statistics"""
        total_tests = len(results)
        if total_tests == 0:
            logger.log('No test results to analyze', 2)
            return
        
        # Count different result types
        status_counts = {}
        for result in results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        logger.log('\nTest Execution Statistics:', 1)
        logger.log('=' * 40, 1)
        logger.log(f'Total Tests Executed: {total_tests}', 1)
        
        for status, count in status_counts.items():
            percentage = (count / total_tests) * 100
            logger.log(f'{status}: {count} ({percentage:.1f}%)', 1)
        
        # Calculate success rate (excluding cancelled and execution failures)
        valid_tests = total_tests - status_counts.get('CANCELLED', 0) - status_counts.get('ExecutionFAIL', 0)
        if valid_tests > 0:
            passed_tests = status_counts.get('PASS', 0) + status_counts.get('*', 0)  # Handle both PASS and * statuses
            success_rate = (passed_tests / valid_tests) * 100
            logger.log(f'Success Rate (valid tests): {success_rate:.1f}%', 1)

    def update_configuration(self, **kwargs):
        """Update test configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                # Handle enum conversions
                print(key, ' : ', value)
                if key == 'content' and isinstance(value, str):
                    value = ContentType(value)
                elif key == 'target' and isinstance(value, str):
                    value = TestTarget(value)
                elif key == 'volt_type' and isinstance(value, str):
                    value = VoltageType(value)
                
                setattr(self.config, key, value)

    def update_ttl_configuration(self, config_updates, flow):
        content_builder = ContentBuilderFactory.create_builder(
            data=config_updates, 
            dragon_config=self.dragon_content, 
            linux_config=self.linux_content, 
            custom_config=None, 
            logger=Framework.FrameworkPrint, 
            flow=flow, 
            core=self.config.mask
        )

        return content_builder.generate_ttl_configuration(self.config.content.value)

    def Loops(self, loops: int = 5, **config_updates) -> List[str]:
        """Run loop test"""
        self.update_configuration(**config_updates)
        strategy = StrategyFactory.create_strategy('loops', loops=loops)
        return self._execute_strategy_and_process_results(strategy, "Loops")
    
    def Sweep(self, ttype: str = 'frequency', domain: str = 'ia', start: float = 16, 
              end: float = 39, step: float = 4, **config_updates) -> List[str]:
        """Run sweep test"""
        self.update_configuration(**config_updates)
        strategy = StrategyFactory.create_strategy('sweep', ttype=ttype, domain=domain, 
                                                 start=start, end=end, step=step)
        return self._execute_strategy_and_process_results(strategy, "Sweep")
    
    def Shmoo(self, file: str = r'C:\Temp\ShmooData.json', label: str = 'COREFIX', 
              **config_updates) -> List[str]:
        """Run shmoo test"""
        self.update_configuration(**config_updates)
        
        # Import here to avoid circular dependencies
        import users.gaespino.dev.S2T.dpmChecks as dpm
        
        # Load shmoo configuration
        shmoo_data = dpm.dev_dict(file, False)[label]
        
        # Update configuration from shmoo file
        volt_settings = shmoo_data['VoltageSettings']
        freq_settings = shmoo_data['FrequencySettings']
        
        self.update_configuration(
            volt_type=volt_settings['Type'],
            volt_IA=volt_settings['core'],
            volt_CFC=volt_settings['cfc'],
            freq_ia=freq_settings['core'],
            freq_cfc=freq_settings['cfc']
        )
        
        strategy = StrategyFactory.create_strategy('shmoo', x_config=shmoo_data['Xaxis'], 
                                                 y_config=shmoo_data['Yaxis'])
        return self._execute_strategy_and_process_results(strategy, "Shmoo")

    def get_execution_state(self) -> Dict[str, Any]:
        """Get current execution state for external monitoring"""
        with self._step_command_lock:
            # Calculate current statistics
            results = self._current_execution_state['iteration_results']
            stats = self._calculate_current_stats(results)
            
            return {
                'execution_mode': self.config.execution_mode.value if hasattr(self.config, 'execution_mode') else 'continuous',
                'step_mode_enabled': self._step_mode_enabled,
                'is_running': self._current_execution_state['is_running'],
                'waiting_for_command': self._current_execution_state['waiting_for_command'],
                'end_requested': self._current_execution_state['end_requested'],
                'current_iteration': self._current_execution_state['current_iteration'],
                'total_iterations': self._current_execution_state['total_iterations'],
                'experiment_name': self._current_execution_state['experiment_name'],
                'current_stats': stats,
                'latest_results': results[-5:] if results else [],  # Last 5 results
                'available_commands': self._get_available_commands()
            }

    def _get_available_commands(self) -> List[str]:
        """Get list of available commands based on current state"""
        commands = []
        
        if self._current_execution_state['is_running']:
            commands.extend(['end_experiment', 'cancel_execution', 'get_execution_state'])
            
            if self._step_mode_enabled:
                if self._current_execution_state['waiting_for_command'] and not self._current_execution_state['end_requested']:
                    commands.append('step_continue')
                
                if not self._current_execution_state['is_running']:
                    commands.append('disable_step_by_step_mode')
            else:
                commands.extend(['halt_execution'])
                if self._is_halted:
                    commands.append('continue_execution')
        else:
            commands.extend(['enable_step_by_step_mode'])
            
        return commands

    def RecipeExecutor(self, data: Dict, S2T_BOOT_CONFIG: Dict = None, 
                      extmask: Dict = None, summary: bool = True, cancel_flag=None,
                      experiment_name: str = None) -> List[str]:
        """Execute test from recipe data with proper dependency injection"""

        # IMPORTANT: Clear any previous END command state at the start
        self._reset_experiment_flags()

        # Clear any previous cancel flag set to S2T
        self.cancel_flag = cancel_flag
        
        # Store experiment name in config for status updates
        if experiment_name:
            self.config.experiment_name = experiment_name	

        if S2T_BOOT_CONFIG:
            # Update S2T configuration
            for key, value in S2T_BOOT_CONFIG.items():
                if hasattr(self.s2t_config, key):
                    setattr(self.s2t_config, key, value)

        # Update configuration from recipe
        config_mapping = ConfigurationMapping.CONFIG_MAPPING
        dragon_mapping = ConfigurationMapping.DRAGON_MAPPING
        linux_mapping = ConfigurationMapping.LINUX_MAPPING
        custom_mapping = ConfigurationMapping.CUSTOM_MAPPING

        config_updates = self.get_config_updates(data, config_mapping)
        dragon_updates = self.get_content_updates(data, dragon_mapping)
        linux_updates = self.get_content_updates(data, linux_mapping)
        custom_updates = self.get_content_updates(data, custom_mapping)

        if extmask:
            config_updates['extMask'] = extmask
    
        self.update_configuration(**config_updates)
        flow_type = self._get_current_flow_type()
        
        if self.config.content == ContentType.DRAGON:
            self.content_config = self.update_ttl_configuration(config_updates=dragon_updates, flow=flow_type)
        elif self.config.content == ContentType.LINUX:
            self.content_config = self.update_ttl_configuration(config_updates=linux_updates, flow=flow_type)
        elif self.config.content == ContentType.CUSTOM:
            self.content_config = self.update_ttl_configuration(config_updates=custom_updates, flow=flow_type)
        else:
            self.content_config = None

        # Parse TTL and create INI file if config is available
        if 'macro_folder' in config_updates and config_updates['macro_folder']:
            Framework.TTL_parse(
                folder=config_updates['macro_folder'], 
                config=self.content_config,
                flow_type=flow_type
            )
        else:
            Framework.FrameworkPrint("No macro folder specified, skipping TTL configuration", 2)

        # Execute based on test type
        test_type = data['Test Type']
        
        if test_type == 'Loops':
            return self.Loops(loops=data['Loops'])
        elif test_type == 'Sweep':
            return self.Sweep(
                ttype=data['Type'].lower(),
                domain=data['Domain'].lower(),
                start=data['Start'],
                end=data['End'],
                step=data['Steps']
            )
        elif test_type == 'Shmoo':
            return self.Shmoo(
                file=data['ShmooFile'],
                label=data['ShmooLabel']
            )
        else:
            raise ValueError(f"Unknown test type: {test_type}")

    def get_config_updates(self, data, config_mapping):
        config_updates = {}
        for recipe_key, config_key in config_mapping.items():
            if recipe_key in data and data[recipe_key] is not None:
                value = data[recipe_key]
                
                # Handle special conversions
                if recipe_key == 'Disable 2 Cores' and value:
                    config_updates['dis2CPM'] = int(value, 16)
                elif recipe_key == 'Core License' and value:
                    config_updates['corelic'] = int(value.split(":")[0])
                elif recipe_key == 'Test Mode' and value:
                    config_updates['target'] = value.lower()
                else:
                    config_updates[config_key] = value

        return config_updates

    def get_content_updates(self, data, config_mapping):
        config_updates = {}
        for recipe_key, config_key in config_mapping.items():
            if recipe_key in data and data[recipe_key] is not None:
                value = data[recipe_key]
                if recipe_key == 'Dragon Content Line' and value:
                    config_updates['dragon_content_line'] = " ".join(s.strip() for s in value.split(","))
                else:
                    config_updates[config_key] = value

        return config_updates

    def _get_current_flow_type(self):
        """Get current flow type based on framework configuration"""
        if hasattr(self.config, 'content') and self.config.content == ContentType.LINUX:
            return "LINUX"
        elif hasattr(self.config, 'content') and self.config.content == ContentType.CUSTOM:
            return "CUSTOM"
        elif hasattr(self.config, 'target') and self.config.content == ContentType.DRAGON:
            if self.config.target == TestTarget.MESH:
                return "MESH"
            elif self.config.target == TestTarget.SLICE:
                return "SLICE"
        
        # Default fallback
        return None

    # Static methods for interface compatibility
    @staticmethod
    def FrameworkPrint(text: str, level: int = None):
        """Print framework messages with color coding"""
        RESET_COLOR = Fore.WHITE
        
        if level == 0:
            COLOR = Fore.YELLOW
        elif level == 1:
            COLOR = Fore.GREEN
        elif level == 2:
            COLOR = Fore.RED
        else:
            COLOR = Fore.WHITE
        
        print(COLOR + text + RESET_COLOR)

    @staticmethod
    def TTL_parse(folder: str, config=None, flow_type=None):
        """Parse TTL configuration and create/update INI file if config provided"""
        # Import here to avoid circular dependencies
        import users.gaespino.dev.DebugFramework.FileHandler as fh
        from tabulate import tabulate
        from ..content.configurations import DragonConfiguration, LinuxConfiguration
        
        config_file = fh.create_path(folder, 'config.ini')
        converter = fh.FrameworkConfigConverter(config_file, logger=Framework.FrameworkPrint)
        
        if config is not None and flow_type is not None:
            Framework.FrameworkPrint(' -- Creating/Updating TTL Configuration File -- ', 1)

            dragon_config = None
            linux_config = None
            custom_config = None

            if isinstance(config, DragonConfiguration):
                dragon_config = config
            elif isinstance(config, LinuxConfiguration):
                linux_config = config
            else:
                Framework.FrameworkPrint(f' -- Unknown configuration type: {type(config)} -- ', 2)
            
            # Update/create the INI file
            success = converter.update_ini(
                dragon_config=dragon_config,
                linux_config=linux_config,
                flow_type=flow_type,
                command_timeout=9999999  # Default timeout
            )
            
            if success:
                Framework.FrameworkPrint(f' -- INI Configuration file updated: {config_file} -- ', 1)
            else:
                Framework.FrameworkPrint(' -- Failed to update INI configuration file -- ', 2)

        if converter.read_ini():
            converter.create_current_flow_csv(folder)
            config_data = converter.get_flow_config_data()
            Framework.FrameworkPrint(' -- TTL Test Configuration -- ')
            if config_data:
                table_data = [[key, value] for key, value in config_data.items()]
                data_table = tabulate(table_data, headers=["Parameter", "Value"], tablefmt="grid")
                Framework.FrameworkPrint(data_table)	
            else:
                Framework.FrameworkPrint(' -- Failed to read TTL configuration -- ', 2)

    @staticmethod
    def clear_s2t_cancel_flag(logger):
        # Import here to avoid circular dependencies
        import users.gaespino.dev.S2T.CoreManipulation as gcm
        gcm.clear_cancel_flag(logger)

    # Add other static methods as needed...