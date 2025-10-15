# mock_setup.py - Simplified and direct mock setup

import sys
# Add this to your mock_setup.py file

import tempfile
import os
import json
import pandas as pd
from datetime import datetime
import configparser
from pathlib import Path

# Add the mock to your setup_all_mocks function in mock_setup.py:


def setup_all_mocks():
    """Setup all mocks before importing the main framework"""
    
    print("Setting up direct mocks...")


    class MockFrameworkLogger:
        """Mock Framework Logger"""
        
        def __init__(self, log_file='mock_app.log', logger_name='MockFrameworkLogger', 
                    console_output=False, pythonconsole=False, reset_handlers=True):
            self.log_file = log_file
            self.logger_name = logger_name
            self.console_output = console_output
            self.pythonconsole = pythonconsole
            print(f"[MOCK LOGGER] Created logger: {logger_name} -> {log_file}")
            
            # Create the log file directory if it doesn't exist
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            # Create empty log file
            with open(log_file, 'w') as f:
                f.write(f"[MOCK LOG] Framework Logger initialized: {datetime.now()}\n")
        
        def log(self, message, event_type=1):
            level_map = {0: "DEBUG", 1: "INFO", 2: "WARN", 3: "ERROR", 4: "CRITICAL"}
            level_str = level_map.get(event_type, "INFO")
            
            log_message = f"[MOCK {self.logger_name} {level_str}] {message}"
            
            if self.console_output:
                print(log_message)
            
            # Write to log file
            try:
                with open(self.log_file, 'a') as f:
                    f.write(f"{datetime.now()} - {level_str} - {message}\n")
            except:
                pass  # Ignore file write errors in mock
        
        def start_capture(self, mode='w'):
            print(f"[MOCK LOGGER] Starting capture mode: {mode}")
        
        def stop_capture(self):
            print(f"[MOCK LOGGER] Stopping capture")

    class MockTestUpload:
        """Mock Test Upload class"""
        
        def __init__(self, folder, vid, name, bucket, WW, product, logger=None, 
                    from_Framework=False, upload_to_disk=True, upload_to_danta=False):
            self.folder = folder
            self.vid = vid
            self.name = name
            self.bucket = bucket
            self.WW = WW
            self.product = product
            self.logger = logger or print
            self.from_Framework = from_Framework
            self.upload_to_disk = upload_to_disk
            self.upload_to_danta = upload_to_danta
            
            self.logger(f"[MOCK UPLOAD] TestUpload initialized for {name}", 1)
            self.logger(f"[MOCK UPLOAD] Upload to disk: {upload_to_disk}", 1)
            self.logger(f"[MOCK UPLOAD] Upload to database: {upload_to_danta}", 1)
        
        def generate_summary(self):
            self.logger("[MOCK UPLOAD] Generating test summary...", 1)
            # Simulate summary generation
            import time
            time.sleep(0.5)
            self.logger("[MOCK UPLOAD] Summary generation completed", 1)
        
        def upload_data(self):
            if self.upload_to_danta:
                self.logger("[MOCK UPLOAD] WARNING: Database upload disabled in test mode", 2)
            else:
                self.logger("[MOCK UPLOAD] Skipping database upload (test mode)", 1)
            
            if self.upload_to_disk:
                self.logger("[MOCK UPLOAD] Simulating disk upload...", 1)
                import time
                time.sleep(0.3)
                self.logger("[MOCK UPLOAD] Disk upload simulation completed", 1)

    class MockFrameworkConfigConverter:
        """Mock Framework Config Converter"""
        
        def __init__(self, ini_file_path="mock_framework_config.ini", logger=None):
            self.ini_file_path = ini_file_path
            self.logger = logger or print
            self.config = None
            self._mock_config_data = self._create_mock_config_data()
            
            # Create a mock INI file
            self._create_mock_ini_file()
        
        def _create_mock_config_data(self):
            """Create mock configuration data"""
            return {
                'LINUX': {
                    'STARTUP_LINUX': 'startup_linux.nsh',
                    'WAIT_STRING1': 'Press any key to continue...',
                    'WAIT_STRING2': 'GRUB version',
                    'WAIT_STRING3': 'Loading Linux',
                    'WAIT_STRING4': '--MORE--',
                    'LINUX_PATH': 'cd /root/content/LOS/TSL/bin',
                    'LINUX_CONTENT_WAIT': '20',
                    'LINUX_PASS_STRING': 'Test Completed',
                    'LINUX_FAIL_STRING': 'Test_Failed',
                    'LINUX_CONTENT_LINE_0': 'mock_linux_command_0',
                    'LINUX_CONTENT_LINE_1': 'mock_linux_command_1',
                    'LINUX_CONTENT_LINE_2': '',
                    'LINUX_CONTENT_LINE_3': '',
                    'LINUX_CONTENT_LINE_4': '',
                    'LINUX_CONTENT_LINE_5': '',
                    'LINUX_CONTENT_LINE_6': '',
                    'LINUX_CONTENT_LINE_7': '',
                    'LINUX_CONTENT_LINE_8': '',
                    'LINUX_CONTENT_LINE_9': '',
                    'LNX_PRE_EXEC_CMD': '',
                    'LNX_POST_EXEC_CMD': '',
                    'command_timeout': '30'
                },
                'SLICE': {
                    'STARTUP_EFI': 'startup_efi.nsh',
                    'ULX_PATH': 'FS1:\\EFI\\ulx',
                    'ULX_CPU': 'GNR_B0',
                    'PRODUCT_CHOP': 'GNR',
                    'VVAR0': '0x4C4B40',
                    'VVAR1': '80064000',
                    'VVAR2': '0x1000000',
                    'VVAR3': '0x10000',
                    'VVAR_EXTRA': ' ',
                    'SLICE_CONTENT': 'FS1:\\content\\Dragon\\GNR1C_Q_Slice_2M_pseudoSBFT_System',
                    'APIC_CDIE': '0',
                    'DRAGON_CONTENT_LINE': 'Ditto Blender Yakko',
                    'MERLIN': 'MerlinX',
                    'MERLIN_DRIVE': 'FS1:',
                    'MERLIN_DIR': 'FS1:\\EFI\\Version8.15\\BinFiles\\Release',
                    'STOP_ON_FAIL': '0',
                    'EFI_PRE_EXEC_CMD': '',
                    'EFI_POST_EXEC_CMD': '',
                    'command_timeout': '30'
                },
                'MESH': {
                    'STARTUP_EFI': 'startup_efi.nsh',
                    'ULX_PATH': 'FS1:\\EFI\\ulx',
                    'ULX_CPU': 'GNR_B0',
                    'PRODUCT_CHOP': 'GNR',
                    'VVAR0': '0x4C4B40',
                    'VVAR1': '80064000',
                    'VVAR2': '0x1000000',
                    'VVAR3': '0x10000',
                    'VVAR_EXTRA': ' ',
                    'MESH_CONTENT': 'FS1:\\content\\Dragon\\7410_0x0E_PPV_MegaMem\\GNR128C_H_1UP\\',
                    'DRAGON_CONTENT_LINE': 'Ditto Blender Yakko',
                    'MERLIN': 'MerlinX',
                    'MERLIN_DRIVE': 'FS1:',
                    'MERLIN_DIR': 'FS1:\\EFI\\Version8.15\\BinFiles\\Release',
                    'STOP_ON_FAIL': '0',
                    'EFI_PRE_EXEC_CMD': '',
                    'EFI_POST_EXEC_CMD': '',
                    'command_timeout': '30'
                },
                'CUSTOM': {
                    'CUSTOM_PATH': 'FS1:\\CUSTOM',
                    'CMD_LINE_0': 'custom.nsh',
                    'EFI_PRE_EXEC_CMD': '',
                    'EFI_POST_EXEC_CMD': '',
                    'command_timeout': '30'
                }
            }
        
        def _create_mock_ini_file(self):
            """Create a mock INI file"""
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.ini_file_path), exist_ok=True)
                
                config = configparser.ConfigParser()
                
                # Add execution control section
                config['EXECUTION_CONTROL'] = {
                    'flow_type': 'SLICE',
                    'command_timeout': '30'
                }
                
                # Add other sections based on mock data
                config['DRG_INIT'] = {
                    'STARTUP_EFI': 'startup_efi.nsh',
                    'ULX_PATH': 'FS1:\\EFI\\ulx',
                    'ULX_CPU': 'GNR_B0',
                    'PRODUCT_CHOP': 'GNR'
                }
                
                config['SETUP_SLICE'] = {
                    'SLICE_CONTENT': 'FS1:\\content\\Dragon\\GNR1C_Q_Slice_2M_pseudoSBFT_System',
                    'APIC_CDIE': '0'
                }
                
                # Write to file
                with open(self.ini_file_path, 'w') as configfile:
                    config.write(configfile)
                    
            except Exception as e:
                self.logger(f"[MOCK CONFIG] Error creating INI file: {e}", 2)
        
        def read_ini(self):
            """Mock read INI"""
            self.logger(f"[MOCK CONFIG] Reading INI file: {self.ini_file_path}", 1)
            
            try:
                self.config = configparser.ConfigParser()
                if os.path.exists(self.ini_file_path):
                    self.config.read(self.ini_file_path)
                    return True
                else:
                    self.logger(f"[MOCK CONFIG] INI file not found, using defaults", 2)
                    return False
            except Exception as e:
                self.logger(f"[MOCK CONFIG] Error reading INI: {e}", 2)
                return False
        
        def update_ini(self, dragon_config=None, linux_config=None, config_dict=None, 
                    flow_type=None, command_timeout=None, output_path=None):
            """Mock update INI"""
            self.logger("[MOCK CONFIG] Updating INI configuration", 1)
            
            if flow_type:
                self.logger(f"[MOCK CONFIG] Setting flow type to: {flow_type}", 1)
            
            if dragon_config:
                self.logger("[MOCK CONFIG] Applying Dragon configuration", 1)
            
            if linux_config:
                self.logger("[MOCK CONFIG] Applying Linux configuration", 1)
            
            return True
        
        def get_flow_config_data(self, flow_type=None, include_empty=True, use_cache=True):
            """Mock get flow config data"""
            if flow_type is None:
                flow_type = 'SLICE'
            
            flow_type = flow_type.upper()
            
            if flow_type in self._mock_config_data:
                config_data = self._mock_config_data[flow_type].copy()
                self.logger(f"[MOCK CONFIG] Returning {flow_type} configuration data", 1)
                return config_data
            else:
                self.logger(f"[MOCK CONFIG] Unknown flow type: {flow_type}", 2)
                return None
        
        def create_current_flow_csv(self, ttl_folder_path):
            """Mock create current flow CSV"""
            self.logger(f"[MOCK CONFIG] Creating CSV in: {ttl_folder_path}", 1)
            
            # Ensure directory exists
            os.makedirs(ttl_folder_path, exist_ok=True)
            
            # Create a mock CSV file
            csv_path = os.path.join(ttl_folder_path, 'mock_flow_params.csv')
            with open(csv_path, 'w') as f:
                f.write('startup_efi.nsh,FS1:\\EFI\\ulx,GNR_B0,GNR,0x4C4B40,80064000\n')
            
            self.logger(f"[MOCK CONFIG] CSV created: {csv_path}", 1)
            return csv_path
        
        def get_current_flow_type(self):
            """Mock get current flow type"""
            return 'SLICE'

    class MockFileHandler:
        """Mock File Handler module"""
        
        # Mock the main classes
        FrameworkLogger = MockFrameworkLogger
        TestUpload = MockTestUpload
        FrameworkConfigConverter = MockFrameworkConfigConverter
        
        @staticmethod
        def create_log_folder(logs_dest, description=None):
            """Mock create log folder"""
            current_datetime = datetime.now().strftime('%Y%m%d_%H%M%S')
            add_name = f'_{description}' if description else ''
            log_folder_path = os.path.join(logs_dest, f'{current_datetime}{add_name}')
            
            # Create the folder
            os.makedirs(log_folder_path, exist_ok=True)
            print(f"[MOCK FH] Created mock log folder: {log_folder_path}")
            return log_folder_path
        
        @staticmethod
        def create_folder_if_not_exists(folder):
            """Mock create folder if not exists"""
            if not os.path.exists(folder):
                os.makedirs(folder)
                print(f"[MOCK FH] Created folder: {folder}")
                return False
            else:
                print(f"[MOCK FH] Folder already exists: {folder}")
                return True
        
        @staticmethod
        def create_path(folder, file):
            """Mock create path"""
            return os.path.join(folder, file)
        
        @staticmethod
        def copy_files(src, dest, uinput="Y"):
            """Mock copy files"""
            print(f"[MOCK FH] Mock copying files from {src} to {dest}")
            # Create destination if it doesn't exist
            os.makedirs(dest, exist_ok=True)
            
            # Create some mock files in destination
            mock_files = ['connect.ttl', 'disconnect.ttl', 'boot.ttl', 'commands.ttl', 'stop_capture.ttl']
            for mock_file in mock_files:
                mock_file_path = os.path.join(dest, mock_file)
                with open(mock_file_path, 'w') as f:
                    f.write(f"# Mock TTL file: {mock_file}\n")
                    f.write("# This is a mock file for testing\n")
            
            print(f"[MOCK FH] Created mock TTL files in {dest}")
        
        @staticmethod
        def execute_file(file_path, logger=None):
            """Mock execute file"""
            if logger:
                logger(f"[MOCK FH] Mock executing file: {file_path}", 1)
            else:
                print(f"[MOCK FH] Mock executing file: {file_path}")
            
            # Simulate file execution
            import time
            time.sleep(0.5)
            
            if logger:
                logger("[MOCK FH] Mock file execution completed", 1)
            else:
                print("[MOCK FH] Mock file execution completed")
        
        @staticmethod
        def extract_fail_seed(log_file_path, PassString=["PASS"], FailString=["FAIL"]):
            """Mock extract fail seed"""
            # Return a mock seed based on random choice
            import random
            mock_seeds = ["0xDEADBEEF", "0xCAFEBABE", "0x12345678", "0xABCDEF00", "PASS", "NA"]
            return random.choice(mock_seeds)
        
        @staticmethod
        def process_excel_file(file_path):
            """Mock process excel file"""
            print(f"[MOCK FH] Mock processing Excel file: {file_path}")
            
            # Return mock recipe data
            return {
                'MockTest1': {
                    'Test Name': 'Mock_Test_1',
                    'Test Type': 'Loops',
                    'Loops': 3,
                    'Test Mode': 'mesh',
                    'Content': 'dragon',
                    'Visual ID': 'MOCK123',
                    'QDF': 'MockQDF',
                    'Bucket': 'MockBucket',
                    'Core Frequency': 2400,
                    'Mesh Frequency': 1800,
                    'Voltage Type': 'nom',
                    'Reset': True,
                    'Reset on Pass': False,
                    'Mask': 'System',
                    'Pass String': 'PASS,SUCCESS',
                    'Fail String': 'FAIL,ERROR,TIMEOUT',
                    'Experiment': 'Enabled'
                }
            }
        
        @staticmethod
        def load_json_file(file_path):
            """Mock load JSON file"""
            print(f"[MOCK FH] Mock loading JSON file: {file_path}")
            
            # Return mock JSON data
            return {
                "mock_config": {
                    "test_parameter": "mock_value",
                    "iterations": 5,
                    "enabled": True
                }
            }
        
        @staticmethod
        def save_excel_to_json(file_path, experiments):
            """Mock save excel to JSON"""
            print(f"[MOCK FH] Mock saving to JSON: {file_path}")
            
            # Create directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save mock JSON
            with open(file_path, 'w') as f:
                json.dump(experiments, f, indent=4)
            
            print(f"[MOCK FH] Mock JSON saved successfully")
        
        @staticmethod
        def teraterm_check(com_port, ip_address='192.168.0.2', teraterm_path=r"C:\teraterm", 
                        seteo_h_path=r"C:\SETEO_H", ini_file="TERATERM.INI", useparser=False, checkenv=True):
            """Mock teraterm check"""
            print(f"[MOCK FH] Mock Teraterm check - COM: {com_port}, IP: {ip_address}")
            print(f"[MOCK FH] Mock Teraterm configuration updated successfully")
        
        @staticmethod
        def manual_upload():
            """Mock manual upload"""
            print("[MOCK FH] Mock manual upload interface would open here")

    # Create simple mock classes that return actual values
    
    # Mock ipccli and stdiolog
    class MockStdioLog:
        @staticmethod
        def log(filename, mode='w'):
            print(f"[MOCK STDIOLOG] Starting log to {filename} in mode {mode}")
        
        @staticmethod
        def nolog():
            print("[MOCK STDIOLOG] Stopping log")
    
    class MockIPCCLI:
        stdiolog = MockStdioLog()
    
    # Mock CoreManipulation
    class MockCoreManipulation:
        AFTER_MRC_POST = "0x15"
        EFI_POST = "0x9A"
        LINUX_POST = "0xAA"
        BOOTSCRIPT_RETRY_TIMES = 3
        BOOTSCRIPT_RETRY_DELAY = 30
        MRC_POSTCODE_WT = 300
        EFI_POSTCODE_WT = 180
        MRC_POSTCODE_CHECK_COUNT = 5
        EFI_POSTCODE_CHECK_COUNT = 3
        BOOT_STOP_POSTCODE = "0x15"
        BOOT_POSTCODE_WT = 60
        BOOT_POSTCODE_CHECK_COUNT = 10
        cancel_flag = None
        
        @staticmethod
        def svStatus(checkipc=True, checksvcores=False, refresh=False, reconnect=False):
            print("[MOCK GCM] Checking SV status...")
            return True
    
    # Mock DPMChecks
    class MockDPMChecks:
        @staticmethod
        def qdf_str():
            return "MOCK_QDF_12345"
        
        @staticmethod
        def product_str():
            return "GNR"
        
        @staticmethod
        def getWW():
            return "2024_15"
        
        @staticmethod
        def request_unit_info():
            return {
                'VISUAL_ID': ['MOCK_VID_123'],
                'DATA_BIN': ['MOCK_BIN_A1'],
                'data_bin_desc': ['Mock Bin Description'],
                'PROGRAM': ['MOCK_PROGRAM_V1']
            }
        
        @staticmethod
        def fuses(rdFuses=True, sktnum=[0], printFuse=False):
            return {
                "ia_compute_0": "0xFFFFFFFF",
                "llc_compute_0": "0xFFFFFFFF", 
                "ia_compute_1": "0xFFFFFFFF",
                "llc_compute_1": "0xFFFFFFFF",
                "ia_compute_2": None,
                "llc_compute_2": None
            }
        
        @staticmethod
        def get_compute_index(core):
            compute_map = {
                0: 0, 1: 0, 2: 0, 3: 0,  # Compute 0
                4: 1, 5: 1, 6: 1, 7: 1,  # Compute 1
            }
            return compute_map.get(core, 0)
        
        @staticmethod
        def dev_dict(file_path, print_data=False):
            return {
                'COREFIX': {
                    'VoltageSettings': {
                        'Type': 'override',
                        'core': 1.0,
                        'cfc': 0.9
                    },
                    'FrequencySettings': {
                        'core': 2400,
                        'cfc': 1800
                    },
                    'Xaxis': {
                        'Type': 'frequency',
                        'Domain': 'ia',
                        'Start': 2000,
                        'End': 2800,
                        'Step': 200
                    },
                    'Yaxis': {
                        'Type': 'voltage',
                        'Domain': 'ia', 
                        'Start': 0.8,
                        'End': 1.2,
                        'Step': 0.1
                    }
                }
            }
    
    # Mock SetTesterRegs - THIS IS THE CRITICAL ONE
    class MockSetTesterRegs:
        # CRITICAL: This must be a simple string, not a mock object
        SELECTED_PRODUCT = "GNR"
        
        @staticmethod
        def MeshQuickTest(core_freq=None, mesh_freq=None, vbump_core=None, vbump_mesh=None,
                          Reset=True, Mask=None, pseudo=False, dis_2CPM=0, GUI=False,
                          fastboot=False, corelic=None, volttype='nom', debug=False,
                          boot_postcode=False, extMask=None, execution_state=None):
            print(f"[MOCK S2T] Starting MeshQuickTest with:")
            print(f"  Core Freq: {core_freq}, Mesh Freq: {mesh_freq}")
            print(f"  Core Voltage: {vbump_core}, Mesh Voltage: {vbump_mesh}")
            print(f"  Mask: {Mask}, Reset: {Reset}")
            
            # Simulate boot process with shorter delays for testing
            import time
            import random
            
            boot_stages = [
                ("Initializing system", 1),
                ("Setting frequencies", 1),
                ("Applying voltage settings", 1),
                ("Starting boot sequence", 2),
                ("MRC initialization", 2),
                ("EFI boot", 2),
                ("System ready", 1)
            ]
            
            for stage, duration in boot_stages:
                print(f"[MOCK S2T] {stage}...")
                
                if execution_state and hasattr(execution_state, 'is_cancelled') and execution_state.is_cancelled():
                    print("[MOCK S2T] Boot cancelled by user")
                    raise InterruptedError("Boot cancelled")
                
                for _ in range(duration):
                    time.sleep(0.5)  # Shorter delays for testing
                    if execution_state and hasattr(execution_state, 'is_cancelled') and execution_state.is_cancelled():
                        print("[MOCK S2T] Boot cancelled by user")
                        raise InterruptedError("Boot cancelled")
            
            # Simulate occasional boot failures (10% chance)
            SIMBOOTFAIL = False
            if random.random() < 0.1 and SIMBOOTFAIL:
                print("[MOCK S2T] Boot failed - simulated failure")
                raise Exception("Mock boot failure - RSP 10 regaccfail")
            
            print("[MOCK S2T] MeshQuickTest completed successfully")
        
        @staticmethod
        def SliceQuickTest(Target_core=None, core_freq=None, mesh_freq=None, vbump_core=None,
                           vbump_mesh=None, Reset=True, pseudo=False, dis_2CPM=0, GUI=False,
                           fastboot=False, corelic=None, volttype='nom', debug=False,
                           boot_postcode=False, execution_state=None):
            print(f"[MOCK S2T] Starting SliceQuickTest with:")
            print(f"  Target Core: {Target_core}")
            print(f"  Core Freq: {core_freq}, Mesh Freq: {mesh_freq}")
            print(f"  Core Voltage: {vbump_core}, Mesh Voltage: {vbump_mesh}")
            
            import time
            import random
            
            boot_stages = [
                ("Targeting specific core", 1),
                ("Initializing slice configuration", 1),
                ("Setting frequencies", 1),
                ("Starting boot sequence", 2),
                ("Core slice initialization", 2),
                ("EFI boot", 2),
                ("System ready", 1)
            ]
            
            for stage, duration in boot_stages:
                print(f"[MOCK S2T] {stage}...")
                
                if execution_state and hasattr(execution_state, 'is_cancelled') and execution_state.is_cancelled():
                    print("[MOCK S2T] Boot cancelled by user")
                    raise InterruptedError("Boot cancelled")
                
                for _ in range(duration):
                    time.sleep(0.5)
                    if execution_state and hasattr(execution_state, 'is_cancelled') and execution_state.is_cancelled():
                        print("[MOCK S2T] Boot cancelled by user")
                        raise InterruptedError("Boot cancelled")
            
            if random.random() < 0.1:
                print("[MOCK S2T] Boot failed - simulated failure")
                raise Exception("Mock boot failure - RSP 10 regaccfail")
            
            print("[MOCK S2T] SliceQuickTest completed successfully")
    
    # Mock SerialConnection
    class MockTeraterm:
        def __init__(self, visual=None, qdf=None, bucket=None, log=None, cmds=None,
                     tfolder=None, test=None, ttime=None, tnum=None, DebugLog=None,
                     chkcore=None, content=None, host=None, PassString=None,
                     FailString=None, execution_state=None):
            
            self.visual = visual
            self.qdf = qdf
            self.bucket = bucket
            self.log = log
            self.cmds = cmds
            self.tfolder = tfolder
            self.test = test
            self.ttime = ttime
            self.tnum = tnum
            self.DebugLog = DebugLog or print
            self.chkcore = chkcore
            self.content = content
            self.host = host
            self.PassString = PassString or "PASS"
            self.FailString = FailString or "FAIL"
            self.execution_state = execution_state
            
            self.testresult = "NA::NA"
            self.scratchpad = ""
            
            self.DebugLog(f"[MOCK TERATERM] Initialized with test: {test}", 1)
            self.DebugLog(f"[MOCK TERATERM] Content type: {content}", 1)
        
        def boot_start(self):
            self.DebugLog("[MOCK TERATERM] Starting boot logging...", 1)
        
        def boot_end(self):
            self.DebugLog("[MOCK TERATERM] Ending boot logging and running test...", 1)
            self._simulate_test_execution()
        
        def run(self):
            self.DebugLog("[MOCK TERATERM] Running test content...", 1)
            self._simulate_test_execution()
        
        def PYSVconsole(self):
            self.DebugLog("[MOCK TERATERM] Running Python SV console test...", 1)
            self._simulate_test_execution()
        
        def _simulate_test_execution(self):
            import time
            import random
            
            execution_stages = [
                "Connecting to target",
                "Loading test content",
                "Executing test",
                "Collecting results"
            ]
            
            for stage in execution_stages:
                self.DebugLog(f"[MOCK TERATERM] {stage}...", 1)
                time.sleep(random.uniform(0.2, 1.0))  # Shorter delays for testing
                
                if self.execution_state and hasattr(self.execution_state, 'is_cancelled') and self.execution_state.is_cancelled():
                    self.DebugLog("[MOCK TERATERM] Test execution cancelled", 2)
                    self.testresult = "CANCELLED::MockTest"
                    return
            
            # Simulate different test outcomes
            outcome = random.choices(
                ['PASS', 'FAIL', 'TIMEOUT', 'ERROR'],
                weights=[20, 40, 30, 20],
                k=1
            )[0]
            
            if outcome == 'PASS':
                self.testresult = f"PASS::{self.test or 'MockTest'}"
                self.scratchpad = "Test completed successfully"
            elif outcome == 'FAIL':
                fail_types = [
                    ("CORE_HANG", "Core0_Hang_Detected"),
                    ("MEMORY_ERROR", "DDR_Training_Fail"),
                    ("THERMAL", "Thermal_Shutdown"),
                    ("VOLTAGE", "VR_Fault_Detected"),
                    ("TIMEOUT", "Boot_Timeout_90s")
                ]
                fail_type, scratchpad = random.choice(fail_types)
                self.testresult = f"FAIL::{self.test or 'MockTest'}"
                self.scratchpad = scratchpad
            elif outcome == 'TIMEOUT':
                self.testresult = f"FAIL::{self.test or 'MockTest'}"
                self.scratchpad = "Test_Timeout_300s"
            else:
                self.testresult = f"FAIL::{self.test or 'MockTest'}"
                self.scratchpad = "Execution_Error"
            
            self.DebugLog(f"[MOCK TERATERM] Test completed: {self.testresult}", 1)
            self.DebugLog(f"[MOCK TERATERM] Scratchpad: {self.scratchpad}", 1)
    
    class MockSerialConnection:
        log_file_path = r"C:\Temp\MockTeratermLog.log"
        
        @staticmethod
        def teraterm(*args, **kwargs):
            return MockTeraterm(*args, **kwargs)
        
        @staticmethod
        def kill_process(process_name, logger=None):
            if logger:
                logger(f"[MOCK SERIAL] Killing process: {process_name}", 1)
            else:
                print(f"[MOCK SERIAL] Killing process: {process_name}")
    
    # Mock S2T Utils
    class MockS2TUtils:
        @staticmethod
        def formatException(e):
            return f"MockFormatted: {str(e)}"
    
    # Mock namednodes (simple mock)
    class MockNamedNodes:
        pass
    
    # Now apply all the mocks to sys.modules
    # We need to mock the entire hierarchy
    
    # Create the module hierarchy
    import types
    
    # Mock base modules
    sys.modules['ipccli'] = MockIPCCLI()
    sys.modules['ipccli.stdiolog'] = MockStdioLog()
    sys.modules['namednodes'] = MockNamedNodes()
    
    # Create users module hierarchy
    users = types.ModuleType('users')
    users.gaespino = types.ModuleType('users.gaespino')
    users.gaespino.dev = types.ModuleType('users.gaespino.dev')
    users.gaespino.dev.S2T = types.ModuleType('users.gaespino.dev.S2T')
    users.gaespino.dev.S2T.Tools = types.ModuleType('users.gaespino.dev.S2T.Tools')
    users.gaespino.dev.DebugFramework = types.ModuleType('users.gaespino.dev.DebugFramework')
    
    # Apply the mock classes
    users.gaespino.dev.S2T.CoreManipulation = MockCoreManipulation()
    users.gaespino.dev.S2T.dpmChecks = MockDPMChecks()
    users.gaespino.dev.S2T.SetTesterRegs = MockSetTesterRegs()  # This is the critical one
    users.gaespino.dev.S2T.Tools.utils = MockS2TUtils()
    users.gaespino.dev.DebugFramework.SerialConnection = MockSerialConnection()
    users.gaespino.dev.DebugFramework.FileHandler = MockFileHandler()

    # Register all modules in sys.modules
    sys.modules['users'] = users
    sys.modules['users.gaespino'] = users.gaespino
    sys.modules['users.gaespino.dev'] = users.gaespino.dev
    sys.modules['users.gaespino.dev.S2T'] = users.gaespino.dev.S2T
    sys.modules['users.gaespino.dev.S2T.CoreManipulation'] = users.gaespino.dev.S2T.CoreManipulation
    sys.modules['users.gaespino.dev.S2T.dpmChecks'] = users.gaespino.dev.S2T.dpmChecks
    sys.modules['users.gaespino.dev.S2T.SetTesterRegs'] = users.gaespino.dev.S2T.SetTesterRegs
    sys.modules['users.gaespino.dev.S2T.Tools'] = users.gaespino.dev.S2T.Tools
    sys.modules['users.gaespino.dev.S2T.Tools.utils'] = users.gaespino.dev.S2T.Tools.utils
    sys.modules['users.gaespino.dev.DebugFramework'] = users.gaespino.dev.DebugFramework
    sys.modules['users.gaespino.dev.DebugFramework.SerialConnection'] = users.gaespino.dev.DebugFramework.SerialConnection
    sys.modules['users.gaespino.dev.DebugFramework.FileHandler'] = users.gaespino.dev.DebugFramework.FileHandler
    
    print("All mocks setup completed successfully!")
    print(f"SELECTED_PRODUCT mock value: {MockSetTesterRegs.SELECTED_PRODUCT}")

# Call setup immediately when this module is imported
setup_all_mocks()