import os
import time
import shutil
from typing import Dict, Any, Optional
from ..configurations.test_configurations import TestConfiguration, SystemToTesterConfig, TestResult
from ..enums.framework_enums import TestStatus, ContentType, TestTarget

class TestExecutor:
    """Handles individual test execution"""
    
    def __init__(self, config: TestConfiguration, s2t_config: SystemToTesterConfig, cancel_flag=None):
        self.config = config
        self.s2t_config = s2t_config
        self.cancel_flag = cancel_flag
        self.current_status = TestStatus.SUCCESS
        self._framework_callback = None
        
        # Initialize logging and paths
        self._setup_test_environment()
        
    def _setup_test_environment(self):
        """Setup test environment and logging"""
        # Import here to avoid circular dependencies
        import users.gaespino.dev.DebugFramework.FileHandler as fh
        import users.gaespino.dev.DebugFramework.SerialConnection as ser
        import users.gaespino.dev.S2T.CoreManipulation as gcm
        
        self.config.log_file = os.path.join(self.config.tfolder, 'DebugFrameworkLogger.log')
        self.config.ser_log_file = ser.log_file_path
        
        # Initialize loggers
        self.gdflog = fh.FrameworkLogger(self.config.log_file, 'FrameworkLogger', console_output=True)
        
        PYTHONSV_CONSOLE_LOG = r"C:\Temp\PythonSVLog.log"
        self.pylog = fh.FrameworkLogger(PYTHONSV_CONSOLE_LOG, 'PythonSVLogger', pythonconsole=True)
        
        # Clear any previous cancellation flag
        from ..framework.main_framework import Framework
        Framework.clear_s2t_cancel_flag(self.gdflog.log)
        
        # Update system configuration
        self._update_system_config()
        
    def _update_system_config(self):
        """Update global system configuration"""
        import users.gaespino.dev.S2T.CoreManipulation as gcm
        
        gcm.AFTER_MRC_POST = self.s2t_config.AFTER_MRC_POST
        gcm.EFI_POST = self.s2t_config.EFI_POST
        gcm.LINUX_POST = self.s2t_config.LINUX_POST
        gcm.BOOTSCRIPT_RETRY_TIMES = self.s2t_config.BOOTSCRIPT_RETRY_TIMES
        gcm.BOOTSCRIPT_RETRY_DELAY = self.s2t_config.BOOTSCRIPT_RETRY_DELAY
        gcm.MRC_POSTCODE_WT = self.s2t_config.MRC_POSTCODE_WT
        gcm.EFI_POSTCODE_WT = self.s2t_config.EFI_POSTCODE_WT
        gcm.MRC_POSTCODE_CHECK_COUNT = self.s2t_config.MRC_POSTCODE_CHECK_COUNT
        gcm.EFI_POSTCODE_CHECK_COUNT = self.s2t_config.EFI_POSTCODE_CHECK_COUNT
        gcm.BOOT_STOP_POSTCODE = self.s2t_config.BOOT_STOP_POSTCODE
        gcm.BOOT_POSTCODE_WT = self.s2t_config.BOOT_POSTCODE_WT
        gcm.BOOT_POSTCODE_CHECK_COUNT = self.s2t_config.BOOT_POSTCODE_CHECK_COUNT
        
        if self.cancel_flag:
            gcm.cancel_flag = self.cancel_flag
    
    def execute_single_test(self) -> TestResult:
        """Execute a single test iteration"""
        try:
            # Check cancellation at start
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

            self._log_test_banner()
            
            # Import here to avoid circular dependencies
            import users.gaespino.dev.DebugFramework.SerialConnection as ser
            
            # Kill Any previous Teraterm Process
            ser.kill_process(process_name='ttermpro.exe', logger=self.gdflog.log)

            # Prepare test environment
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'Preparing Environment',
                'progress_weight': 0.05
            })
                
            # Prepare test environment
            boot_logging = self.config.content == ContentType.BOOTBREAKS
            
            # Setup serial configuration
            exp_ttl_files_dict = self._get_ttl_files_from_config()
            test_name = self._generate_test_name()

            # Send boot start notification
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'Starting Boot Process',
                'progress_weight': 0.10
            })
            
            serial = ser.teraterm(
                visual=self.config.visual,
                qdf=self.config.qdf,
                bucket=self.config.bucket,
                log=self.config.ser_log_file,
                cmds=exp_ttl_files_dict,
                tfolder=self.config.tfolder,
                test=test_name,
                ttime=self.config.ttime,
                tnum=self.config.tnumber,
                DebugLog=self.gdflog.log,
                chkcore=self.config.coreslice,
                content=self.config.content.value,
                host=self.config.host,
                PassString=self.config.passstring,
                FailString=self.config.failstring,
                cancel_flag=self.cancel_flag
            )
            
            # Start logging if needed
            if boot_logging:
                serial.boot_start()
            
            self._start_python_logging()

            # Execute test based on target
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'System Boot in Progress',
                'progress_weight': 0.15
            })				

            # Execute test based on target
            boot_ready = self._execute_test_by_target()

            # Send test execution notification
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'Boot Process Complete',
                'progress_weight': 0.50,
                'boot_ready': boot_ready
            })
                        
            # Execute custom script if provided
            if self.config.script_file:
                self._send_iteration_update('iteration_progress', {
                    'iteration': self.config.tnumber,
                    'test_name': self.config.name,
                    'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                    'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                    'status': 'Executing Custom Script',
                    'progress_weight': 0.55
                })
                self._execute_custom_script()
            
            self._stop_python_logging()

            # Send test execution notification
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'Running Test Content',
                'progress_weight': 0.60,
                'boot_ready': boot_ready
            })

            if self.config.content == ContentType.PYSVCONSOLE:
                serial.PYSVconsole()
            elif self.config.content == ContentType.BOOTBREAKS:
                serial.boot_end()
            else:
                serial.run()

            # Handle test completion
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'Test Content Complete - Processing Results',
                'progress_weight': 0.75
            })
            
            # Process results
            result = self._process_test_results(serial, test_name, boot_ready)

            # Process results
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'Analyzing Results',
                'progress_weight': 0.90
            })
                
            if boot_ready:
                self.current_status = TestStatus.SUCCESS
            else:
                self.current_status = TestStatus.FAILED

            # Send iteration complete notification
            self._send_iteration_update('iteration_complete', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': result.status,
                'scratchpad': result.scratchpad,
                'seed': result.seed,
                'progress_weight': 1.0
            })
    
            return result

        except KeyboardInterrupt:
            self.current_status = TestStatus.CANCELLED
            self._send_iteration_update('iteration_cancelled', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'CANCELLED'
            })
            return TestResult(status="CANCELLED", name=self.config.name, iteration=self.config.tnumber)
            
        except InterruptedError:
            self.current_status = TestStatus.CANCELLED
            self._send_iteration_update('iteration_cancelled', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'CANCELLED'
            })
            return TestResult(status="CANCELLED", name=self.config.name, iteration=self.config.tnumber)
            
        except Exception as e:
            # Import here to avoid circular dependencies
            import users.gaespino.dev.S2T.Tools.utils as s2tutils
            
            self.gdflog.log(f"Test execution failed: {s2tutils.formatException(e)}", 3)
            self.current_status = TestStatus.FAILED
            self._send_iteration_update('iteration_failed', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'FAILED',
                'error': str(e)
            })
            return TestResult(status="FAILED", name=self.config.name, iteration=self.config.tnumber)

    def _send_iteration_update(self, update_type: str, data: Dict[str, Any]):
        """Send iteration update through framework callback"""
        if self._framework_callback:
            try:
                self._framework_callback(update_type, data)
            except Exception as e:
                print(f"Error sending iteration update: {e}")
                
    def _check_cancellation(self):
        """Check if test should be cancelled"""
        if self.cancel_flag and self.cancel_flag.is_set():
            self.gdflog.log("FRAME: Framework Execution interrupted by user. Exiting...", 2)
            raise InterruptedError("Test cancelled by user")
    
    def _log_test_banner(self):
        """Log test information banner"""
        self.gdflog.log(f' -- Test Start --- ')
        self.gdflog.log(f' -- Debug Framework {self.config.name} --- ')
        self.gdflog.log(f' -- Performing test iteration {self.config.tnumber} with the following parameters: ')
        
        EMPTY_FIELDS = [None, 'None', '']
        Configured_Mask = self.config.mask if self.config.extMask is None else "Custom"
        self.gdflog.log(f'\t > Unit VisualID: {self.config.visual}')
        self.gdflog.log(f'\t > PPV Program: {self.config.program}')
        self.gdflog.log(f'\t > PPV Bin: {self.config.data_bin}')
        self.gdflog.log(f'\t > PPV Bin Desc: {self.config.data_bin_desc}')
        self.gdflog.log(f'\t > Unit QDF: {self.config.qdf}')
        self.gdflog.log(f'\t > Configuration: {Configured_Mask if Configured_Mask not in EMPTY_FIELDS else "System Mask"} ')
        if self.config.corelic: 
            self.gdflog.log(f'\t > Core License: {self.config.corelic} ')
        self.gdflog.log(f'\t > Voltage set to: {self.config.volt_type.value} ')
        self.gdflog.log(f'\t > HT Disabled (BigCore): {self.config.pseudo} ')
        self.gdflog.log(f'\t > Dis 2 Cores (Atomcore): {self.config.dis2CPM} ')
        self.gdflog.log(f'\t > Core Freq: {self.config.freq_ia} ')
        self.gdflog.log(f'\t > Core Voltage: {self.config.volt_IA} ')
        self.gdflog.log(f'\t > Mesh Freq: {self.config.freq_cfc} ')
        self.gdflog.log(f'\t > Mesh Voltage: {self.config.volt_CFC} ')
        self.gdflog.log(f'\t > Running Content: {self.config.content.value} ')
        self.gdflog.log(f'\t > Pass String: {self.config.passstring} ')
        self.gdflog.log(f'\t > Fail String: {self.config.failstring} ')

    def _get_ttl_files_from_config(self) -> Dict:
        """Get TTL files from configuration (already copied at strategy level)"""
        if self.config.ttl_files_dict:
            self.gdflog.log("Using pre-copied TTL files from strategy setup", 1)
            if self.config.ttl_path:
                self.gdflog.log(f"TTL files location: {self.config.ttl_path}", 1)
            return self.config.ttl_files_dict
        else:
            # Fallback to default if no pre-copied files available
            self.gdflog.log("Using default TTL files (fallback)", 2)
            # Import here to avoid circular dependencies
            from ..utils.misc_utils import macro_cmds
            return macro_cmds
        
    def _generate_test_name(self) -> str:
        """Generate test name based on configuration"""
        vbumps = self.config.volt_IA is not None or self.config.volt_CFC is not None
        vtstring = f'_vcfg_{self.config.volt_type.value}' if vbumps else ""
        iaF = f'_ia_f{self.config.freq_ia}' if self.config.freq_ia else ""
        cfcF = f'_cfc_f{self.config.freq_cfc}' if self.config.freq_cfc else ""
        iavolt = f'_ia_v{self.config.volt_IA}'.replace(".", "_") if self.config.volt_IA else ""
        cfcvolt = f'_cfc_v{self.config.volt_CFC}'.replace(".", "_") if self.config.volt_CFC else ""
        mask = self.config.mask or "System"
        
        return f'{self.config.name.strip()}_{mask}{iaF}{cfcF}{vtstring}{iavolt}{cfcvolt}'
    
    def _execute_test_by_target(self) -> bool:
        """Execute test based on target (mesh/slice)"""
        boot_ready = False
        wait_postcode = not self.config.u600w
        self._check_cancellation()
        print('Boot Status: ', 'READY' if boot_ready else 'NOT_READY')
        
        try:
            # Send detailed boot progress updates
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'System Boot in Progress - Starting S2T Flow',
                'progress_weight': 0.20
            })
            self._execute_system2tester_flow()			

            # Boot process progressing
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'System Boot in Progress - S2T Flow Complete',
                'progress_weight': 0.35
            })
        
            self._check_cancellation()
            boot_ready = True
            
        except KeyboardInterrupt:
            self.gdflog.log("Script interrupted by user. Exiting...", 2)
            self.current_status = TestStatus.CANCELLED
            return False			
        except InterruptedError:
            self.gdflog.log("Script interrupted by user. Exiting...", 2)
            self.current_status = TestStatus.CANCELLED
            return False
        except SyntaxError as se:
            print(f"Syntax error occurred: {se}")
            self.current_status = TestStatus.FAILED
            return False		
        except Exception as e:
            # Import here to avoid circular dependencies
            import users.gaespino.dev.S2T.Tools.utils as s2tutils
            import users.gaespino.dev.S2T.CoreManipulation as gcm
            
            self.gdflog.log(f'Boot Failed with Exception {s2tutils.formatException(e)} --- Retrying.....', 4)

            # Send boot retry notification
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'Boot Failed - Retrying',
                'progress_weight': 0.20
            })
                    
            if 'RSP 10' in str(e) or 'regaccfail' in str(e):
                self.gdflog.log('PowerCycling Unit -- RegAcc Fail during previous Boot', 4)
                from ..framework.main_framework import Framework
                Framework.reboot_unit(wait_postcode=wait_postcode)
                time.sleep(120)
                gcm.svStatus(checkipc=True, checksvcores=False, refresh=False, reconnect=False)
            else:
                from ..framework.main_framework import Framework
                Framework.reboot_unit(wait_postcode=wait_postcode)
            
            # Send boot retry notification
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'Boot Failed - Retrying S2T Flow',
                'progress_weight': 0.20
            })
            
            self._execute_system2tester_flow()

            # Boot process progressing
            self._send_iteration_update('iteration_progress', {
                'iteration': self.config.tnumber,
                'test_name': self.config.name,
                'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
                'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
                'status': 'System Boot in Progress - S2T Flow Complete',
                'progress_weight': 0.35
            })

            boot_ready = True

        print('Boot Status: ', 'READY' if boot_ready else 'NOT_READY')

        # Boot completion
        self._send_iteration_update('iteration_progress', {
            'iteration': self.config.tnumber,
            'test_name': self.config.name,
            'experiment_name': getattr(self.config, 'experiment_name', self.config.name),
            'strategy_type': getattr(self.config, 'strategy_type', 'Unknown'),
            'status': 'Boot Process Complete',
            'progress_weight': 0.45
        })

        return boot_ready

    def _execute_system2tester_flow(self):
        # Import here to avoid circular dependencies
        import users.gaespino.dev.S2T.SetTesterRegs as s2t
        
        if self.config.target == TestTarget.MESH:
            s2t.MeshQuickTest(
                core_freq=self.config.freq_ia,
                mesh_freq=self.config.freq_cfc,
                vbump_core=self.config.volt_IA,
                vbump_mesh=self.config.volt_CFC,
                Reset=self.config.reset,
                Mask=self.config.mask,
                pseudo=self.config.pseudo,
                dis_2CPM=self.config.dis2CPM,
                GUI=False,
                fastboot=self.config.fastboot,
                corelic=self.config.corelic,
                volttype=self.config.volt_type.value,
                debug=False,
                boot_postcode=(self.config.content == ContentType.BOOTBREAKS),
                extMask=self.config.extMask
            )
        elif self.config.target == TestTarget.SLICE:
            s2t.SliceQuickTest(
                Target_core=self.config.mask,
                core_freq=self.config.freq_ia,
                mesh_freq=self.config.freq_cfc,
                vbump_core=self.config.volt_IA,
                vbump_mesh=self.config.volt_CFC,
                Reset=self.config.reset,
                pseudo=False,
                dis_2CPM=self.config.dis2CPM,
                GUI=False,
                fastboot=self.config.fastboot,
                corelic=self.config.corelic,
                volttype=self.config.volt_type.value,
                debug=False,
                boot_postcode=(self.config.content == ContentType.BOOTBREAKS)
            )

    def _execute_custom_script(self):
        """Execute custom script if provided"""
        # Import here to avoid circular dependencies
        import users.gaespino.dev.DebugFramework.FileHandler as fh
        
        if self.config.content == ContentType.BOOTBREAKS:
            self.gdflog.log(f"Executing Custom script at reached boot Breakpoint: {self.config.script_file}", 1)
        elif self.config.content == ContentType.PYSVCONSOLE:
            self.gdflog.log(f"Executing Custom script before test: {self.config.script_file}", 1)
        
        fh.execute_file(file_path=self.config.script_file, logger=self.gdflog.log)
    
    def _start_python_logging(self):
        """Start Python SV console logging"""
        # Import here to avoid circular dependencies
        from ipccli.stdiolog import log
        
        PYTHONSV_CONSOLE_LOG = r"C:\Temp\PythonSVLog.log"
        
        if self.config.content in [ContentType.BOOTBREAKS, ContentType.PYSVCONSOLE]:
            log(PYTHONSV_CONSOLE_LOG, 'w')
        else:
            if self.pylog:
                self.pylog.start_capture('w')
    
    def _stop_python_logging(self):
        """Stop Python SV console logging"""
        # Import here to avoid circular dependencies
        from ipccli.stdiolog import nolog
        
        if self.config.content in [ContentType.BOOTBREAKS, ContentType.PYSVCONSOLE]:
            nolog()
        else:
            if self.pylog:
                self.pylog.stop_capture()
    
    def _process_test_results(self, serial, test_name: str, boot_ready: bool) -> TestResult:
        """Process test results and save logs"""
        # Import here to avoid circular dependencies
        import users.gaespino.dev.DebugFramework.FileHandler as fh
        
        # Get test results
        result_parts = serial.testresult.split("::") if serial.testresult else ['NA', 'NA']
        run_status = result_parts[0] if boot_ready else TestStatus.EXECUTION_FAIL.value
        run_name = result_parts[-1]
        
        # Copy logs to test folder
        log_new_path = os.path.join(self.config.tfolder, f'{self.config.tnumber}_{test_name}.log')
        pysvlog_new_path = os.path.join(self.config.tfolder, f'{self.config.tnumber}_{test_name}_pysv.log')
        s2t_config_path = os.path.join(self.config.tfolder, f'{self.config.tnumber}_{test_name}.json')
        
        PYTHONSV_CONSOLE_LOG = r"C:\Temp\PythonSVLog.log"
        
        # Copy files if they exist
        if os.path.exists(self.config.ser_log_file):
            shutil.copy(self.config.ser_log_file, log_new_path)
        
        if os.path.exists(PYTHONSV_CONSOLE_LOG):
            shutil.copy(PYTHONSV_CONSOLE_LOG, pysvlog_new_path)
        
        if os.path.exists(r"C:\Temp\System2TesterRun.json"):
            shutil.copy(r"C:\Temp\System2TesterRun.json", s2t_config_path)
        
        # Extract additional information
        pass_strings = [s.strip() for s in self.config.passstring.split(",")]
        fail_strings = [s.strip() for s in self.config.failstring.split(",")]
        seed = fh.extract_fail_seed(log_file_path=log_new_path, PassString=pass_strings, FailString=fail_strings) if os.path.exists(log_new_path) else "NA"
        scratchpad = getattr(serial, 'scratchpad', '')
        
        # Log results
        from ..utils.misc_utils import print_custom_separator
        
        self.gdflog.log(f'tdata_{self.config.tnumber}::{run_name}::{run_status}::{scratchpad}::{seed}')
        self.gdflog.log(print_custom_separator(f'Test iteration summary'))
        self.gdflog.log(f' -- Test Name: {run_name} --- ')
        self.gdflog.log(f' -- Test Result: {run_status} --- ')
        self.gdflog.log(f' -- Test End --- ')
        
        return TestResult(
            status=run_status,
            name=run_name,
            scratchpad=scratchpad,
            seed=seed,
            iteration=self.config.tnumber,
            log_path=log_new_path,
            config_path=s2t_config_path,
            pysv_log_path=pysvlog_new_path
        )