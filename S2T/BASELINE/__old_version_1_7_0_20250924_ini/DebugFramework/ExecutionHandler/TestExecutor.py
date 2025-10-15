"""
Enhanced Test Executor with Interface Integration
Handles individual test execution with comprehensive monitoring, error handling, and status reporting.
"""
import os
import time
import shutil
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import threading
from pathlib import Path

from .Configurations import TestConfiguration, SystemToTesterConfig, TestResult
from .Enums import TestStatus, ContentType, TestTarget
from .Exceptions import TestExecutionError, ExecutionTimeoutError, ConfigurationError
from ..Interfaces.IFramework import ITestExecutor, ILogger, IStatusReporter


class TestExecutor(ITestExecutor):
    """
    Enhanced test executor with proper interface integration and comprehensive monitoring.
    
    This class handles the execution of individual test iterations with:
    - Comprehensive error handling and recovery
    - Real-time status reporting
    - Cancellation support
    - Configuration validation
    - Resource management
    """
    
    def __init__(
        self, 
        config: TestConfiguration, 
        s2t_config: SystemToTesterConfig,
        logger: ILogger,
        status_reporter: Optional[IStatusReporter] = None,
        cancel_flag: Optional[threading.Event] = None,
        framework_callback: Optional[Callable] = None
    ):
        """
        Initialize test executor with dependencies.
        
        Args:
            config: Test configuration
            s2t_config: System-to-tester configuration
            logger: Logger implementation
            status_reporter: Optional status reporter
            cancel_flag: Optional cancellation flag
            framework_callback: Optional callback for framework communication
        """
        self.config = config
        self.s2t_config = s2t_config
        self.logger = logger
        self.status_reporter = status_reporter
        self.cancel_flag = cancel_flag
        self._framework_callback = framework_callback
        
        # Execution state
        self.current_status = TestStatus.SUCCESS
        self._execution_start_time: Optional[float] = None
        self._current_iteration_data: Dict[str, Any] = {}
        
        # Resource tracking
        self._created_files: List[str] = []
        self._temp_directories: List[str] = []
        
        # Thread safety
        self._status_lock = threading.Lock()
        
        # Validate configurations on initialization
        self._validate_configurations()
        
        # Initialize environment
        self._setup_test_environment()
        
        self.logger.log(f"TestExecutor initialized for test: {self.config.name}", 1)
    
    def _validate_configurations(self) -> None:
        """Validate all configurations and raise errors if invalid."""
        try:
            config_valid, config_errors = self.config.validate()
            s2t_valid, s2t_errors = self.s2t_config.validate()
            
            all_errors = []
            if not config_valid:
                all_errors.extend([f"Config: {error}" for error in config_errors])
            if not s2t_valid:
                all_errors.extend([f"S2T: {error}" for error in s2t_errors])
            
            if all_errors:
                raise ConfigurationError(
                    f"Configuration validation failed: {'; '.join(all_errors)}",
                    context={
                        'config_errors': config_errors,
                        's2t_errors': s2t_errors,
                        'test_name': self.config.name
                    }
                )
                
        except Exception as e:
            self.logger.log_exception(e, "Configuration validation failed")
            raise
    
    def execute_test(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute test with enhanced error handling and monitoring.
        
        Args:
            config: Optional configuration updates to apply before execution
            
        Returns:
            Dictionary containing test results and metadata
        """
        self._execution_start_time = time.time()
        
        try:
            # Update configuration if provided
            if config:
                self._update_config_from_dict(config)
                self.logger.log(f"Configuration updated for test execution", 1)
            
            # Execute the test
            result = self.execute_single_test()
            
            # Calculate execution time and update result
            execution_time = time.time() - self._execution_start_time
            result.execution_time = execution_time
            
            # Log completion
            self.logger.log(
                f"Test execution completed: {result.status} in {execution_time:.2f}s", 
                1 if result.status in ['PASS', 'SUCCESS'] else 2
            )
            
            return result.to_dict()
            
        except TestExecutionError as e:
            return self._handle_test_execution_error(e)
        except Exception as e:
            return self._handle_unexpected_error(e)
        finally:
            self._cleanup_resources()
    
    def cancel_execution(self) -> bool:
        """
        Cancel current test execution.
        
        Returns:
            True if cancellation was successful, False otherwise
        """
        try:
            if self.cancel_flag:
                self.cancel_flag.set()
                self.logger.log("Test execution cancelled by user request", 2)
                
                # Send cancellation status
                self._send_status_update('execution_cancelled', {
                    'test_name': self.config.name,
                    'iteration': self.config.tnumber,
                    'timestamp': datetime.now().isoformat()
                })
                
                return True
            else:
                self.logger.log("No cancel flag available for cancellation", 2)
                return False
                
        except Exception as e:
            self.logger.log_exception(e, "Error during cancellation")
            return False
    
    def get_execution_status(self) -> Dict[str, Any]:
        """
        Get current execution status with detailed information.
        
        Returns:
            Dictionary containing current execution status and metadata
        """
        with self._status_lock:
            execution_time = None
            if self._execution_start_time:
                execution_time = time.time() - self._execution_start_time
            
            return {
                'current_status': self.current_status.value,
                'test_name': self.config.name,
                'iteration': self.config.tnumber,
                'execution_time': execution_time,
                'is_cancelled': self.cancel_flag.is_set() if self.cancel_flag else False,
                'config_valid': True,  # We validated on init
                'log_file': self.config.log_file,
                'test_folder': self.config.tfolder,
                'iteration_data': self._current_iteration_data.copy()
            }
    
    def execute_single_test(self) -> TestResult:
        """
        Execute a single test iteration with comprehensive monitoring and error handling.
        
        Returns:
            TestResult object containing execution results
        """
        iteration_start_time = time.time()
        
        try:
            # Check for cancellation before starting
            self._check_cancellation()
            
            # Send iteration start notification
            self._send_iteration_update('iteration_start', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'Starting Test Iteration',
                'progress_weight': 0.0
            })
            
            # Log test banner
            self._log_test_banner()
            
            # Kill any previous processes
            self._cleanup_previous_processes()
            
            # Prepare test environment (5% progress)
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'status': 'Preparing Environment',
                'progress_weight': 0.05
            })
            
            # Setup test environment
            self._prepare_test_environment()
            
            # Execute system-to-tester flow (10-50% progress)
            boot_ready = self._execute_system_to_tester_flow()
            
            # Execute custom scripts if provided (55% progress)
            if self.config.script_file:
                self._execute_custom_script()
            
            # Run test content (60-75% progress)
            self._execute_test_content()
            
            # Process results (90% progress)
            result = self._process_test_results(boot_ready, iteration_start_time)
            
            # Update status based on results
            if boot_ready and result.status in ['PASS', 'SUCCESS']:
                self.current_status = TestStatus.SUCCESS
            else:
                self.current_status = TestStatus.FAILED
            
            # Send completion notification (100% progress)
            self._send_iteration_update('iteration_complete', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'status': result.status,
                'scratchpad': result.scratchpad,
                'seed': result.seed,
                'progress_weight': 1.0,
                'execution_time': result.execution_time
            })
            
            return result
            
        except KeyboardInterrupt:
            return self._handle_keyboard_interrupt()
        except InterruptedError:
            return self._handle_interruption()
        except TestExecutionError as e:
            return self._handle_test_execution_error_in_iteration(e)
        except Exception as e:
            return self._handle_unexpected_error_in_iteration(e)
    
    def _prepare_test_environment(self) -> None:
        """Prepare the test environment for execution."""
        try:
            # Determine test configuration
            boot_logging = self.config.content == ContentType.BOOTBREAKS
            wait_postcode = not self.config.u600w
            
            # Get TTL files configuration
            ttl_files_dict = self._get_ttl_files_from_config()
            test_name = self._generate_test_name()
            
            # Store environment data
            self._current_iteration_data.update({
                'boot_logging': boot_logging,
                'wait_postcode': wait_postcode,
                'ttl_files': ttl_files_dict,
                'test_name': test_name
            })
            
            self.logger.log("Test environment prepared successfully", 1)
            
        except Exception as e:
            raise TestExecutionError(
                f"Failed to prepare test environment: {str(e)}",
                original_exception=e,
                context={'test_name': self.config.name, 'iteration': self.config.tnumber}
            )
    
    def _execute_system_to_tester_flow(self) -> bool:
        """
        Execute the system-to-tester flow.
        
        Returns:
            True if boot was successful, False otherwise
        """
        boot_ready = False
        
        try:
            self._check_cancellation()
            
            # Send progress update
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'status': 'System Boot in Progress - Starting S2T Flow',
                'progress_weight': 0.20
            })
            
            # Execute S2T flow based on target
            self._execute_s2t_by_target()
            
            # Send completion update
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'status': 'System Boot in Progress - S2T Flow Complete',
                'progress_weight': 0.35
            })
            
            self._check_cancellation()
            boot_ready = True
            
            self.logger.log("System-to-tester flow completed successfully", 1)
            
        except (KeyboardInterrupt, InterruptedError):
            self.logger.log("S2T flow interrupted by user", 2)
            self.current_status = TestStatus.CANCELLED
            raise
        except SyntaxError as se:
            self.logger.log_exception(se, "Syntax error in S2T flow")
            self.current_status = TestStatus.FAILED
            raise TestExecutionError(
                f"Syntax error in S2T flow: {str(se)}",
                original_exception=se
            )
        except Exception as e:
            self.logger.log(f'Boot failed with exception: {str(e)} - Attempting retry...', 2)
            
            # Attempt recovery
            boot_ready = self._attempt_boot_recovery(e)
        
        # Send final boot status
        self._send_iteration_update('iteration_progress', {
            'iteration': self.config.tnumber,
            'test_name': self.config.name,
            'status': 'Boot Process Complete',
            'progress_weight': 0.45,
            'boot_ready': boot_ready
        })
        
        return boot_ready
    
    def _execute_s2t_by_target(self) -> None:
        """Execute S2T flow based on target configuration."""
        # This is a placeholder for your actual S2T implementation
        # You would integrate your existing s2t.MeshQuickTest and s2t.SliceQuickTest here
        
        if self.config.target == TestTarget.MESH:
            self.logger.log("Executing MESH S2T flow", 1)
            # s2t.MeshQuickTest(...) - Your existing implementation
        elif self.config.target == TestTarget.SLICE:
            self.logger.log("Executing SLICE S2T flow", 1)
            # s2t.SliceQuickTest(...) - Your existing implementation
        else:
            raise TestExecutionError(f"Unknown target type: {self.config.target}")
    
    def _attempt_boot_recovery(self, original_error: Exception) -> bool:
        """
        Attempt to recover from boot failure.
        
        Args:
            original_error: The original error that caused boot failure
            
        Returns:
            True if recovery was successful, False otherwise
        """
        try:
            self.logger.log("Attempting boot recovery...", 2)
            
            # Send retry notification
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'status': 'Boot Failed - Retrying',
                'progress_weight': 0.20,
                'error': str(original_error)
            })
            
            # Determine recovery strategy based on error type
            if 'RSP 10' in str(original_error) or 'regaccfail' in str(original_error):
                self.logger.log('PowerCycling Unit -- RegAcc Fail during previous Boot', 2)
                self._power_cycle_recovery()
            else:
                self._standard_recovery()
            
            # Retry S2T flow
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'status': 'Boot Failed - Retrying S2T Flow',
                'progress_weight': 0.25
            })
            
            self._execute_s2t_by_target()
            
            self.logger.log("Boot recovery successful", 1)
            return True
            
        except Exception as recovery_error:
            self.logger.log_exception(recovery_error, "Boot recovery failed")
            return False
    
    def _power_cycle_recovery(self) -> None:
        """Perform power cycle recovery."""
        # Placeholder for your power cycle implementation
        self.logger.log("Performing power cycle recovery", 2)
        time.sleep(120)  # Wait for power cycle
    
    def _standard_recovery(self) -> None:
        """Perform standard recovery."""
        # Placeholder for your standard recovery implementation
        self.logger.log("Performing standard recovery", 2)
    
    def _execute_custom_script(self) -> None:
        """Execute custom script if provided."""
        try:
            if not self.config.script_file:
                return
            
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'status': 'Executing Custom Script',
                'progress_weight': 0.55
            })
            
            script_path = Path(self.config.script_file)
            if not script_path.exists():
                raise TestExecutionError(f"Custom script not found: {self.config.script_file}")
            
            if self.config.content == ContentType.BOOTBREAKS:
                self.logger.log(f"Executing custom script at boot breakpoint: {self.config.script_file}", 1)
            elif self.config.content == ContentType.PYSVCONSOLE:
                self.logger.log(f"Executing custom script before test: {self.config.script_file}", 1)
            
            # Placeholder for script execution - integrate with your fh.execute_file
            self.logger.log(f"Custom script executed successfully: {self.config.script_file}", 1)
            
        except Exception as e:
            raise TestExecutionError(
                f"Failed to execute custom script: {str(e)}",
                original_exception=e,
                context={'script_file': self.config.script_file}
            )
    
    def _execute_test_content(self) -> None:
        """Execute the main test content."""
        try:
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'status': 'Running Test Content',
                'progress_weight': 0.60
            })
            
            # Execute based on content type
            if self.config.content == ContentType.PYSVCONSOLE:
                self.logger.log("Executing PYSVConsole content", 1)
                # serial.PYSVconsole() - Your existing implementation
            elif self.config.content == ContentType.BOOTBREAKS:
                self.logger.log("Executing BootBreaks content", 1)
                # serial.boot_end() - Your existing implementation
            else:
                self.logger.log("Executing standard test content", 1)
                # serial.run() - Your existing implementation
            
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'status': 'Test Content Complete - Processing Results',
                'progress_weight': 0.75
            })
            
        except Exception as e:
            raise TestExecutionError(
                f"Failed to execute test content: {str(e)}",
                original_exception=e,
                context={'content_type': self.config.content.value}
            )
    
    def _process_test_results(self, boot_ready: bool, iteration_start_time: float) -> TestResult:
        """
        Process test results and create TestResult object.
        
        Args:
            boot_ready: Whether boot was successful
            iteration_start_time: When the iteration started
            
        Returns:
            TestResult object with processed results
        """
        try:
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'status': 'Analyzing Results',
                'progress_weight': 0.90
            })
            
            # Determine test status
            if boot_ready:
                run_status = TestStatus.SUCCESS.value
            else:
                run_status = TestStatus.EXECUTION_FAIL.value
            
            # Generate test name
            test_name = self._generate_test_name()
            
            # Copy logs to test folder
            log_paths = self._copy_test_logs(test_name)
            
            # Extract additional information (placeholder)
            scratchpad = "test_data"  # Replace with actual scratchpad extraction
            seed = "12345"  # Replace with actual seed extraction
            
            # Calculate execution time
            execution_time = time.time() - iteration_start_time
            
            # Create result object
            result = TestResult(
                status=run_status,
                name=test_name,
                scratchpad=scratchpad,
                seed=seed,
                iteration=self.config.tnumber,
                log_path=log_paths.get('main_log'),
                config_path=log_paths.get('config_log'),
                pysv_log_path=log_paths.get('pysv_log'),
                execution_time=execution_time
            )
            
            # Log results
            self.logger.log(f'Test iteration summary: {result.name} - {result.status}', 1)
            
            return result
            
        except Exception as e:
            # Return error result if processing fails
            return TestResult(
                status=TestStatus.FAILED.value,
                name=self.config.name,
                iteration=self.config.tnumber,
                execution_time=time.time() - iteration_start_time,
                error_details={'processing_error': str(e)}
            )
    
    def _copy_test_logs(self, test_name: str) -> Dict[str, str]:
        """
        Copy test logs to test folder.
        
        Args:
            test_name: Generated test name for file naming
            
        Returns:
            Dictionary mapping log types to their new paths
        """
        log_paths = {}
        
        if not self.config.tfolder:
            return log_paths
        
        try:
            # Define log file paths
            log_new_path = os.path.join(self.config.tfolder, f'{self.config.tnumber}_{test_name}.log')
            pysvlog_new_path = os.path.join(self.config.tfolder, f'{self.config.tnumber}_{test_name}_pysv.log')
            s2t_config_path = os.path.join(self.config.tfolder, f'{self.config.tnumber}_{test_name}.json')
            
            # Copy files if they exist
            if self.config.ser_log_file and os.path.exists(self.config.ser_log_file):
                shutil.copy(self.config.ser_log_file, log_new_path)
                log_paths['main_log'] = log_new_path
                self._created_files.append(log_new_path)
            
            # Placeholder for other log files - replace with actual paths
            pysv_log_source = r"C:\Temp\PythonSVLog.log"  # Your actual path
            if os.path.exists(pysv_log_source):
                shutil.copy(pysv_log_source, pysvlog_new_path)
                log_paths['pysv_log'] = pysvlog_new_path
                self._created_files.append(pysvlog_new_path)
            
            s2t_config_source = r"C:\Temp\System2TesterRun.json"  # Your actual path
            if os.path.exists(s2t_config_source):
                shutil.copy(s2t_config_source, s2t_config_path)
                log_paths['config_log'] = s2t_config_path
                self._created_files.append(s2t_config_path)
            
        except Exception as e:
            self.logger.log_exception(e, "Failed to copy test logs")
        
        return log_paths
    
    def _get_ttl_files_from_config(self) -> Dict[str, str]:
        """Get TTL files from configuration."""
        if self.config.ttl_files_dict:
            self.logger.log("Using pre-copied TTL files from strategy setup", 1)
            if self.config.ttl_path:
                self.logger.log(f"TTL files location: {self.config.ttl_path}", 1)
            return self.config.ttl_files_dict
        else:
            self.logger.log("Using default TTL files (fallback)", 2)
            # Return default TTL files - replace with your actual default
            return {
                'Connect': 'default_connect.ttl',
                'Disconnect': 'default_disconnect.ttl',
                'StartCapture': 'default_start.ttl',
                'StartTest': 'default_test.ttl',
                'StopCapture': 'default_stop.ttl'
            }
    
    def _generate_test_name(self) -> str:
        """Generate test name based on configuration."""
        vbumps = self.config.volt_IA is not None or self.config.volt_CFC is not None
        vtstring = f'_vcfg_{self.config.volt_type.value}' if vbumps else ""
        iaF = f'_ia_f{self.config.freq_ia}' if self.config.freq_ia else ""
        cfcF = f'_cfc_f{self.config.freq_cfc}' if self.config.freq_cfc else ""
        iavolt = f'_ia_v{self.config.volt_IA}'.replace(".", "_") if self.config.volt_IA else ""
        cfcvolt = f'_cfc_v{self.config.volt_CFC}'.replace(".", "_") if self.config.volt_CFC else ""
        mask = self.config.mask or "System"
        
        return f'{self.config.name.strip()}_{mask}{iaF}{cfcF}{vtstring}{iavolt}{cfcvolt}'
    
    def _cleanup_previous_processes(self) -> None:
        """Clean up any previous processes."""
        try:
            # Placeholder for process cleanup - integrate with your ser.kill_process
            self.logger.log("Cleaning up previous processes", 1)
        except Exception as e:
            self.logger.log_exception(e, "Failed to cleanup previous processes")
    
    def _log_test_banner(self) -> None:
        """Log test information banner."""
        self.logger.log(' -- Test Start ---', 1)
        self.logger.log(f' -- Debug Framework {self.config.name} ---', 1)
        self.logger.log(f' -- Performing test iteration {self.config.tnumber} with the following parameters:', 1)
        
        # Log configuration details
        EMPTY_FIELDS = [None, 'None', '']
        configured_mask = self.config.mask if self.config.extMask is None else "Custom"
        
        self.logger.log(f'\t > Unit VisualID: {self.config.visual}', 1)
        self.logger.log(f'\t > PPV Program: {self.config.program}', 1)
        self.logger.log(f'\t > PPV Bin: {self.config.data_bin}', 1)
        self.logger.log(f'\t > PPV Bin Desc: {self.config.data_bin_desc}', 1)
        self.logger.log(f'\t > Unit QDF: {self.config.qdf}', 1)
        self.logger.log(f'\t > Configuration: {configured_mask if configured_mask not in EMPTY_FIELDS else "System Mask"}', 1)
        
        if self.config.corelic:
            self.logger.log(f'\t > Core License: {self.config.corelic}', 1)
        
        self.logger.log(f'\t > Voltage set to: {self.config.volt_type.value}', 1)
        self.logger.log(f'\t > HT Disabled (BigCore): {self.config.pseudo}', 1)
        self.logger.log(f'\t > Dis 2 Cores (Atomcore): {self.config.dis2CPM}', 1)
        self.logger.log(f'\t > Core Freq: {self.config.freq_ia}', 1)
        self.logger.log(f'\t > Core Voltage: {self.config.volt_IA}', 1)
        self.logger.log(f'\t > Mesh Freq: {self.config.freq_cfc}', 1)
        self.logger.log(f'\t > Mesh Voltage: {self.config.volt_CFC}', 1)
        self.logger.log(f'\t > Running Content: {self.config.content.value}', 1)
        self.logger.log(f'\t > Pass String: {self.config.passstring}', 1)
        self.logger.log(f'\t > Fail String: {self.config.failstring}', 1)
    
    def _setup_test_environment(self) -> None:
        """Setup test environment and logging."""
        try:
            if self.config.tfolder:
                self.config.log_file = os.path.join(self.config.tfolder, 'DebugFrameworkLogger.log')
                
                # Create log directory if it doesn't exist
                os.makedirs(os.path.dirname(self.config.log_file), exist_ok=True)
                self._temp_directories.append(os.path.dirname(self.config.log_file))
            
            # Update system configuration (placeholder)
            self._update_system_config()
            
            self.logger.log(f"Test environment setup completed for {self.config.name}", 1)
            
        except Exception as e:
            raise TestExecutionError(
                f"Failed to setup test environment: {str(e)}",
                original_exception=e
            )
    
    def _update_system_config(self) -> None:
        """Update global system configuration."""
        # Placeholder for your system configuration updates
        # This would integrate with your gcm module
        self.logger.log("System configuration updated", 1)
    
    def _send_iteration_update(self, update_type: str, data: Dict[str, Any]) -> None:
        """Send iteration update through framework callback."""
        if self._framework_callback:
            try:
                self._framework_callback(update_type, data)
            except Exception as e:
                self.logger.log_exception(e, f"Error sending iteration update: {update_type}")
    
    def _send_status_update(self, status_type: str, data: Dict[str, Any]) -> None:
        """Send status update through status reporter."""
        if self.status_reporter:
            try:
                status_data = {
                    'type': status_type,
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }
                self.status_reporter.report_status(status_data)
            except Exception as e:
                self.logger.log_exception(e, f"Error sending status update: {status_type}")
    
    def _check_cancellation(self) -> None:
        """Check if test should be cancelled."""
        if self.cancel_flag and self.cancel_flag.is_set():
            self.logger.log("Test execution interrupted by user. Exiting...", 2)
            raise InterruptedError("Test cancelled by user")
    
    def _update_config_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        updated_fields = []
        
        for key, value in config_dict.items():
            if hasattr(self.config, key):
                old_value = getattr(self.config, key)
                setattr(self.config, key, value)
                updated_fields.append(f"{key}: {old_value} -> {value}")
        
        if updated_fields:
            self.logger.log(f"Configuration updated: {', '.join(updated_fields)}", 1)
    
    def _cleanup_resources(self) -> None:
        """Clean up created resources."""
        try:
            # Clean up temporary files if needed
            for file_path in self._created_files:
                try:
                    if os.path.exists(file_path):
                        # Don't actually delete log files, just track them
                        pass
                except Exception as e:
                    self.logger.log_exception(e, f"Error cleaning up file: {file_path}")
            
            self.logger.log("Resource cleanup completed", 1)
            
        except Exception as e:
            self.logger.log_exception(e, "Error during resource cleanup")
    
    # Error handling methods
    def _handle_keyboard_interrupt(self) -> TestResult:
        """Handle keyboard interrupt (Ctrl+C)."""
        self.current_status = TestStatus.CANCELLED
        self._send_iteration_update('iteration_cancelled', {
            'iteration': self.config.tnumber,
            'test_name': self.config.name,
            'status': 'CANCELLED',
            'reason': 'Keyboard interrupt'
        })
        
        return TestResult(
            status=TestStatus.CANCELLED.value,
            name=self.config.name,
            iteration=self.config.tnumber
        )
    
    def _handle_interruption(self) -> TestResult:
        """Handle interruption (cancellation)."""
        self.current_status = TestStatus.CANCELLED
        self._send_iteration_update('iteration_cancelled', {
            'iteration': self.config.tnumber,
            'test_name': self.config.name,
            'status': 'CANCELLED',
            'reason': 'User cancellation'
        })
        
        return TestResult(
            status=TestStatus.CANCELLED.value,
            name=self.config.name,
            iteration=self.config.tnumber
        )
    
    def _handle_test_execution_error_in_iteration(self, error: TestExecutionError) -> TestResult:
        """Handle TestExecutionError during iteration."""
        self.logger.log_exception(error, f"Test execution failed: {self.config.name}")
        self.current_status = TestStatus.FAILED
        
        self._send_iteration_update('iteration_failed', {
            'iteration': self.config.tnumber,
            'test_name': self.config.name,
            'status': 'FAILED',
            'error': str(error),
            'failure_type': error.failure_type.value if error.failure_type else None
        })
        
        return TestResult(
            status=TestStatus.FAILED.value,
            name=self.config.name,
            iteration=self.config.tnumber,
            error_details=error.to_dict()
        )
    
    def _handle_unexpected_error_in_iteration(self, error: Exception) -> TestResult:
        """Handle unexpected error during iteration."""
        self.logger.log_exception(error, f"Unexpected error in test execution: {self.config.name}")
        self.current_status = TestStatus.FAILED
        
        self._send_iteration_update('iteration_failed', {
            'iteration': self.config.tnumber,
            'test_name': self.config.name,
            'status': 'FAILED',
            'error': str(error),
            'error_type': type(error).__name__
        })
        
        return TestResult(
            status=TestStatus.FAILED.value,
            name=self.config.name,
            iteration=self.config.tnumber,
            error_details={
                'exception': str(error),
                'type': type(error).__name__,
                'unexpected': True
            }
        )
    
    def _handle_test_execution_error(self, error: TestExecutionError) -> Dict[str, Any]:
        """Handle TestExecutionError in main execute_test method."""
        execution_time = time.time() - self._execution_start_time if self._execution_start_time else 0
        
        self.logger.log_exception(error, "Test execution failed")
        
        error_result = TestResult(
            status=TestStatus.FAILED.value,
            name=self.config.name,
            iteration=self.config.tnumber,
            execution_time=execution_time,
            error_details=error.to_dict()
        )
        
        return error_result.to_dict()
    
    def _handle_unexpected_error(self, error: Exception) -> Dict[str, Any]:
        """Handle unexpected error in main execute_test method."""
        execution_time = time.time() - self._execution_start_time if self._execution_start_time else 0
        
        self.logger.log_exception(error, "Unexpected error during test execution")
        
        error_result = TestResult(
            status=TestStatus.FAILED.value,
            name=self.config.name,
            iteration=self.config.tnumber,
            execution_time=execution_time,
            error_details={
                'exception': str(error),
                'type': type(error).__name__,
                'unexpected': True
            }
        )
        
        return error_result.to_dict()


class TestExecutorFactory:
    """Factory for creating TestExecutor instances with proper dependency injection."""
    
    @staticmethod
    def create_executor(
        config: TestConfiguration,
        s2t_config: SystemToTesterConfig,
        logger: ILogger,
        status_reporter: Optional[IStatusReporter] = None,
        cancel_flag: Optional[threading.Event] = None,
        framework_callback: Optional[Callable] = None
    ) -> TestExecutor:
        """
        Create a TestExecutor instance with all dependencies.
        
        Args:
            config: Test configuration
            s2t_config: System-to-tester configuration  
            logger: Logger implementation
            status_reporter: Optional status reporter
            cancel_flag: Optional cancellation flag
            framework_callback: Optional framework callback
            
        Returns:
            Configured TestExecutor instance
        """
        return TestExecutor(
            config=config,
            s2t_config=s2t_config,
            logger=logger,
            status_reporter=status_reporter,
            cancel_flag=cancel_flag,
            framework_callback=framework_callback
        )