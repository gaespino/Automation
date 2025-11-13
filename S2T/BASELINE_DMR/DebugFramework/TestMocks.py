# TestMocks.py - Comprehensive mocking system for S2T Framework

import sys
import tempfile
import os
import json
import pandas as pd
from datetime import datetime
import configparser
from pathlib import Path


def setup_all_mocks(product: str = "GNR"):
    """Setup all mocks before importing the main framework"""
    
    print(f"Setting up direct mocks for product: {product}...")
    
    # Import and setup hardware mocks first
    try:
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        from HardwareMocks import setup_hardware_mocks
        setup_hardware_mocks(product)
        print(f"[MOCK SETUP] Hardware mocks initialized for {product}")
    except ImportError as e:
        print(f"[MOCK SETUP] Hardware mocks not available: {e}")
        # Continue with basic mocks
    except Exception as e:
        print(f"[MOCK SETUP] Error setting up hardware mocks: {e}")
        # Continue with basic mocks

def setup_s2t_testing_mocks(product: str = "GNR"):
    """Setup mocks specifically for S2T function testing"""
    
    print(f"Setting up S2T testing mocks for product: {product}...")
    
    # First setup hardware mocks
    setup_all_mocks(product)
    
    # Import and setup S2T-specific mocks
    try:
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        from S2TMocks import setup_s2t_mocks
        setup_s2t_mocks(product)
        print(f"[MOCK SETUP] S2T testing mocks initialized for {product}")
        return True
    except ImportError as e:
        print(f"[MOCK SETUP] S2T mocks not available: {e}")
        return False
    except Exception as e:
        print(f"[MOCK SETUP] Error setting up S2T mocks: {e}")
        return False


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
        def create_ttl_config_ini(ttl_folder, experiment_data):
            """Generate configs.ini in TTL folder with Framework experiment data (simulates FileHandler behavior)"""
            import configparser
            import os
            
            print(f"[MOCK FH] Creating TTL configs.ini with Framework data")
            
            # Ensure TTL folder exists
            os.makedirs(ttl_folder, exist_ok=True)
            
            config = configparser.ConfigParser()
            
            # Framework experiment configuration section
            config['EXPERIMENT_CONFIG'] = {
                'visual_id': experiment_data.get('visual', 'MOCK_VID'),
                'test_name': experiment_data.get('test', 'Mock_Test'),
                'content_type': experiment_data.get('content', 'dragon'),
                'qdf': experiment_data.get('qdf', 'MOCK_QDF'),
                'bucket': experiment_data.get('bucket', 'MockBucket')
            }
            
            # TTL Macro Variables (VVARs 0-3) - what the TTL macro reads
            config['TTL_VARIABLES'] = {
                'vvar0': '0x4C4B40',  # Standard base address
                'vvar1': experiment_data.get('vvar1', '80064000'),    # Framework experiment data
                'vvar2': experiment_data.get('vvar2', '0x1000000'),  # Framework experiment data  
                'vvar3': experiment_data.get('vvar3', '0x4000000'),  # Framework experiment data
            }
            
            # Dragon test configuration
            config['DRAGON_CONFIG'] = {
                'content_path': f"FS1:\\content\\Dragon\\GNR50C_L_MOSBFT_HToff_pseudoSBFT_System",
                'merlinx_path': 'FS1:\\EFI\\Version8.15\\BinFiles\\Release\\MerlinX.efi',
                'test_mode': experiment_data.get('content', 'dragon'),
                'cores': str(experiment_data.get('cores', 32))
            }
            
            # Test execution parameters
            config['EXECUTION'] = {
                'pass_string': experiment_data.get('PassString', ['Test Passed'])[0] if experiment_data.get('PassString') else 'Test Passed',
                'fail_string': experiment_data.get('FailString', ['Test Failed'])[0] if experiment_data.get('FailString') else 'Test Failed',
                'timeout': '300',
                'retries': '3'
            }
            
            # Write configs.ini file
            config_path = os.path.join(ttl_folder, 'configs.ini')
            with open(config_path, 'w') as configfile:
                config.write(configfile)
            
            print(f"[MOCK FH] Created configs.ini: {config_path}")
            print(f"[MOCK FH] TTL VVARs: 0=0x4C4B40, 1={config['TTL_VARIABLES']['vvar1']}, 2={config['TTL_VARIABLES']['vvar2']}, 3={config['TTL_VARIABLES']['vvar3']}")
            
            return config_path
        
        @staticmethod
        def read_ttl_config_ini(ttl_folder):
            """Read configs.ini from TTL folder (simulates what TTL macro does)"""
            import configparser
            import os
            
            config_path = os.path.join(ttl_folder, 'configs.ini')
            
            if not os.path.exists(config_path):
                print(f"[MOCK FH] configs.ini not found at: {config_path}")
                return None
                
            config = configparser.ConfigParser()
            config.read(config_path)
            
            # Extract VVARs that TTL macro would use
            vvars = {}
            if 'TTL_VARIABLES' in config:
                vvars = {
                    'vvar0': config['TTL_VARIABLES'].get('vvar0', '0x4C4B40'),
                    'vvar1': config['TTL_VARIABLES'].get('vvar1', '80064000'),
                    'vvar2': config['TTL_VARIABLES'].get('vvar2', '0x1000000'),
                    'vvar3': config['TTL_VARIABLES'].get('vvar3', '0x4000000'),
                }
            
            experiment_config = {}
            if 'EXPERIMENT_CONFIG' in config:
                experiment_config = dict(config['EXPERIMENT_CONFIG'])
            
            print(f"[MOCK FH] Read TTL config - VVARs: {vvars}")
            
            return {
                'vvars': vvars,
                'experiment': experiment_config,
                'dragon_config': dict(config['DRAGON_CONFIG']) if 'DRAGON_CONFIG' in config else {},
                'execution': dict(config['EXECUTION']) if 'EXECUTION' in config else {}
            }
        
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
            """Extract fail seed - tries to use real FileHandler, falls back to mock if needed"""
            import os
            
            # First try to use the real FileHandler if available
            try:
                import sys
                import os as path_os
                current_dir = path_os.path.dirname(path_os.path.abspath(__file__))
                parent_dir = path_os.path.dirname(current_dir)
                sys.path.insert(0, parent_dir)
                
                # Import the real FileHandler
                from DebugFramework import FileHandler as RealFileHandler
                
                # If log file exists, use real FileHandler
                if os.path.exists(log_file_path):
                    print(f"[MOCK FH] Using REAL FileHandler to extract seed from: {log_file_path}")
                    return RealFileHandler.extract_fail_seed(log_file_path, PassString, FailString)
                else:
                    print(f"[MOCK FH] Log file not found, generating mock log: {log_file_path}")
                    # Create realistic mock log and then extract from it
                    MockFileHandler._create_realistic_mock_log(log_file_path)
                    if os.path.exists(log_file_path):
                        return RealFileHandler.extract_fail_seed(log_file_path, PassString, FailString)
                    
            except Exception as e:
                print(f"[MOCK FH] Could not use real FileHandler: {e}")
                print("[MOCK FH] Falling back to mock seed generation")
            
            # Fallback: generate mock seeds if real FileHandler unavailable
            return MockFileHandler._generate_mock_fail_seed()
        
        @staticmethod
        def _generate_mock_fail_seed():
            """Generate realistic mock fail seeds"""
            import random
            
            # Generate realistic Dragon test seeds based on the log format you provided
            dragon_seeds = [
                "DL32-Blender-Z1J-0F100050",
                "DL32-Blender-Z1J-0F100051", 
                "DL32-Blender-Z1J-0F100052",
                "DL32-Yakko-Z1J-0F100053",
                "DL32-Wakko-Z1J-0F100054", 
                "DL32-Dot-Z1J-0F100055",
                "DL64-Blender-Z2K-0F200050",
                "DL64-Yakko-Z2K-0F200051",
                "DL128-Blender-Z3L-0F300050"
            ]
            
            mesh_seeds = [
                "GNR128C_H_1UP_MESH_0001",
                "GNR128C_H_1UP_MESH_0002", 
                "GNR64C_M_2UP_MESH_0003",
                "GNR32C_L_4UP_MESH_0004"
            ]
            
            # Use mixed pool for mock generation
            seed_pool = dragon_seeds + mesh_seeds + ["PASS", "NA"]
            
            # Simulate realistic failure rate (70% pass, 25% fail with seed, 5% other)
            outcome = random.choices(
                ["PASS", "FAIL_SEED", "OTHER"],
                weights=[70, 25, 5]
            )[0]
            
            if outcome == "PASS":
                return "PASS"
            elif outcome == "FAIL_SEED":
                return random.choice(seed_pool)
            else:
                return random.choice(["NA", "TIMEOUT", "0xDEADBEEF"])
        
        @staticmethod
        def _create_mock_dragon_log(log_file_path):
            """Create a realistic mock Dragon test log file with both passing and failing scenarios"""
            import os
            import random
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            
            # Generate realistic seeds with different patterns
            cores = random.choice([32, 48, 64, 80])
            patterns = ["Blender", "Yakko", "Wakko", "Dot"]
            ids = ["Z1J", "WsZ", "X2K", "Y3L"]
            
            # 70% chance for passing test, 30% for failing
            test_will_pass = random.random() < 0.7
            
            log_lines = ["Echo is off."]
            
            if test_will_pass:
                # Generate passing Dragon test based on your format
                hex_suffix = f"{random.randint(0xF100000, 0xF199999):08X}"
                passing_seed = f"DL{cores}-{random.choice(patterns)}-{random.choice(ids)}-{hex_suffix}"
                
                log_lines.extend([
                    f"Running FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{passing_seed}.obj",
                    f"Running MerlinX.efi   -a FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{passing_seed}.obj -d 0 0x4C4B40 1 80064000 2 0x1000000 3 0x4000000",
                    "CAPID0_CFG_PCU_FUN0_REG = 0x41589129, MiniDPE = NOT enabled",
                    "MerlinX Version                             [8.15]",
                    "MerlinX [info] Is official version          [True]",
                    f"Image Handle = {random.randint(1600000000, 1699999999)} , {random.randint(0x5F000000, 0x5FFFFFFF):08X} Merlinx Version {random.randint(8000, 8999)}F Test Passed FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{passing_seed}.obj",
                    f"Deleting 'FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{passing_seed}.obj.hng'",
                    "Delete successful.",
                    "**************",
                    "",
                    "Echo is off.",
                    "",
                    "=======================================",
                    "=        TEST STATUS: PASSED          =",
                    "=         REGRESSION FINISHED         =",
                    "=======================================",
                    "Test Complete",
                    f"REGRESSION INFO: FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\\\log.txt",
                    f"FAILURE INFO: FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\\\fail.txt",
                    "CHANGING BACK TO DIR: FS1:\\EFI",
                    "FS1:\\EFI\\> #Test Complete",
                    "FS1:\\EFI\\>"
                ])
                
            else:
                # Generate failing Dragon test with passing tests first, then failure
                # First, a passing test
                hex_suffix_pass = f"{random.randint(0xF100000, 0xF199999):08X}"
                passing_seed = f"DL{cores}-{random.choice(patterns)}-{random.choice(ids)}-{hex_suffix_pass}"
                
                log_lines.extend([
                    f"Running FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{passing_seed}.obj",
                    f"Running MerlinX.efi   -a FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{passing_seed}.obj -d 0 0x4C4B40 1 80064000 2 0x1000000 3 0x4000000",
                    "CAPID0_CFG_PCU_FUN0_REG = 0x41589129, MiniDPE = NOT enabled",
                    "MerlinX Version                             [8.15]",
                    "MerlinX [info] Is official version          [True]",
                    f"Image Handle = {random.randint(1600000000, 1699999999)} , {random.randint(0x5F000000, 0x5FFFFFFF):08X} Merlinx Version {random.randint(8000, 8999)}F Test Passed FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{passing_seed}.obj",
                    f"Deleting 'FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{passing_seed}.obj.hng'",
                    "Delete successful.",
                    "**************",
                    "",
                    "Echo is off."
                ])
                
                # Then, the failing test
                hex_suffix_fail = f"{random.randint(0xF100000, 0xF199999):08X}"
                failing_seed = f"DL{cores}-{random.choice(patterns)}-{random.choice(ids)}-{hex_suffix_fail}"
                
                log_lines.extend([
                    f"Running FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{failing_seed}.obj",
                    f"Running MerlinX.efi   -a FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{failing_seed}.obj -d 0 0x4C4B40 1 80064000 2 0x1000000 3 0x4000000",
                    "CAPID0_CFG_PCU_FUN0_REG = 0x41589129, MiniDPE = NOT enabled",
                    "MerlinX Version                             [8.15]",
                    "MerlinX [info] Is official version          [True]",
                    f"Image Handle = {random.randint(1600000000, 1699999999)} , {random.randint(0x5F000000, 0x5FFFFFFF):08X} Buffer = {random.randint(0x5F000000, 0x5FFFFFFF):08X} and BufferStart = {random.randint(0x5F000000, 0x5FFFFFFF):08X}",
                    "<Configuration>",
                    "<Symbols />",
                    "<Vvars>",
                    f"<Vvar Number=\"0x0\" Value=\"0x4C4B40\" />",
                    f"<Vvar Number=\"0x1\" Value=\"0x{random.randint(0x80000000, 0x8FFFFFFF):08X}\" />",
                    f"<Vvar Number=\"0x2\" Value=\"0x{random.randint(0x1000000, 0x1FFFFFF):07X}\" />",
                    f"<Vvar Number=\"0x3\" Value=\"0x4000000\" />",
                    f"<Vvar Number=\"0x5\" Value=\"0x7FFFFFFF\" />",
                    f"<Vvar Number=\"0x8\" Value=\"0x1FFFAFF\" />",
                    f"<Vvar Number=\"0x9\" Value=\"0xFFFFFFFF\" />",
                    f"<Vvar Number=\"0xA\" Value=\"0x{random.randint(0x50, 0xFF):02X}\" />",
                    f"<Vvar Number=\"0xB\" Value=\"0x{random.randint(0x7000, 0x7FFF):04X}\" />",
                    "</Vvars>",
                    "</Configuration>",
                    f"MerlinX {random.randint(8000, 8999)}F Test Failed: FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{failing_seed}.obj",
                    f"Deleting 'FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{failing_seed}.obj.hng'",
                    "Delete successful.",
                    f"FAILED: FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{failing_seed}.obj",
                    "Stopping regression due to failure",
                    "",
                    "======================================",
                    "=        TEST STATUS: FAILED         =",
                    "=         REGRESSION STOPPED         =",
                    "======================================",
                    "Test Failed",
                    f"REGRESSION INFO: FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\\\log.txt",
                    f"FAILURE INFO: FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\\\fail.txt",
                    "CHANGING BACK TO DIR: FS1:\\EFI",
                    "FS1:\\EFI\\> #Test Failed",
                    "FS1:\\EFI\\>"
                ])
            
            log_content = "\n".join(log_lines)
            
            # Write the mock log file
            with open(log_file_path, 'w') as f:
                f.write(log_content)
            
            print(f"[MOCK FH] Created realistic Dragon log: {log_file_path}")
        
        @staticmethod
        def _create_realistic_mock_log(log_file_path):
            """Create realistic mock log based on file path/name"""
            if "dragon" in log_file_path.lower():
                MockFileHandler._create_mock_dragon_log(log_file_path)
            elif "mesh" in log_file_path.lower():
                MockFileHandler._create_mock_mesh_log(log_file_path)
            else:
                # Default to dragon log
                MockFileHandler._create_mock_dragon_log(log_file_path)
        
        @staticmethod
        def _create_mock_mesh_log(log_file_path):
            """Create a realistic mock Mesh test log file"""
            import os
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            
            failing_seed = "GNR128C_H_1UP_MESH_0002"
            passing_seed = "GNR128C_H_1UP_MESH_0001"
            
            log_content = f"""Starting Mesh test execution...
Loading content: FS1:\\content\\Dragon\\7410_0x0E_PPV_MegaMem\\GNR128C_H_1UP\\
Test seed: {passing_seed}
Mesh frequency: 1800MHz, Core frequency: 2400MHz
Test execution completed: PASS

Test seed: {failing_seed} 
Mesh frequency: 1800MHz, Core frequency: 2400MHz
ERROR: Mesh validation failed at cycle 12847
FAILED: {failing_seed}
Test execution completed: FAIL

======================================
=        TEST STATUS: FAILED         =
=       MESH TEST COMPLETED          =
======================================
"""
            
            with open(log_file_path, 'w') as f:
                f.write(log_content)
            
            print(f"[MOCK FH] Created realistic Mesh log: {log_file_path}")
        
        @staticmethod
        def create_mock_test_log(log_file_path, test_type="dragon"):
            """Create mock test logs based on test type"""
            if test_type.lower() in ["dragon", "slice"]:
                MockFileHandler._create_mock_dragon_log(log_file_path)
            elif test_type.lower() == "mesh":
                MockFileHandler._create_mock_mesh_log(log_file_path)
            else:
                # Generic log
                MockFileHandler._create_mock_dragon_log(log_file_path)
        
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
        
        class config:
            SELECTED_PRODUCT = "GNR"
            
        
        config.SELECTED_PRODUCT = SELECTED_PRODUCT
        
        @staticmethod
        def MeshQuickTest(core_freq=None, mesh_freq=None, vbump_core=None, vbump_mesh=None,
                          Reset=True, Mask=None, pseudo=False, dis_2CPM=0, GUI=False,
                          fastboot=False, corelic=None, volttype='nom', debug=False,
                          boot_postcode=False, extMask=None, u600w=None,execution_state=None):
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
                           fastboot=False, corelic=None, volttype='nom',u600w=None, debug=False,
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
                 FailString=None, execution_state=None, **kwargs):
        
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
        
        # TTL folder path (where configs.ini is located)
        self.ttl_folder = kwargs.get('ttl_folder', 'C:\\SystemDebug\\TTL')
        
        # Read VVARs from configs.ini (like real TTL macro does)
        self.vvars = self._read_ttl_config()
        
        # Experiment iteration tracking
        self.iteration_count = 0
        
        # Framework log naming pattern
        self.base_log_name = f"{visual}_{test}" if visual and test else "MockTest"
        
        self.testresult = "NA::NA"
        self.scratchpad = ""
        
        self.DebugLog(f"[MOCK TERATERM] Initialized with test: {test}", 1)
        self.DebugLog(f"[MOCK TERATERM] Content type: {content}", 1)
        self.DebugLog(f"[MOCK TERATERM] TTL Folder: {self.ttl_folder}", 1)
        self.DebugLog(f"[MOCK TERATERM] TTL VVARs from configs.ini: {self.vvars}", 1)
    
    def _read_ttl_config(self):
        """Read VVARs from configs.ini (simulates TTL macro behavior)"""
        try:
            config_data = MockFileHandler.read_ttl_config_ini(self.ttl_folder)
            if config_data and 'vvars' in config_data:
                return config_data['vvars']
            else:
                self.DebugLog("[MOCK TERATERM] No configs.ini found, using defaults", 2)
                return {
                    'vvar0': '0x4C4B40',
                    'vvar1': '80064000',
                    'vvar2': '0x1000000', 
                    'vvar3': '0x4000000'
                }
        except Exception as e:
            self.DebugLog(f"[MOCK TERATERM] Error reading configs.ini: {e}", 2)
            return {
                'vvar0': '0x4C4B40',
                'vvar1': '80064000',
                'vvar2': '0x1000000',
                'vvar3': '0x4000000'
            }
    
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
            
            # Generate realistic log content and save to file first
            # This determines if boot was successful and sets postcodes
            self._generate_realistic_log()
            
            # Check if boot reached the execution milestone
            boot_reached = getattr(self, '_boot_reached', False)
            
            if not boot_reached:
                # Boot failed - no test execution stages
                self.DebugLog("[MOCK TERATERM] Boot failed - no test execution performed", 2)
                self.testresult = f"FAIL::{self.test or 'MockTest'}"
                self.scratchpad = getattr(self, '_bios_postcode', "0xaf0000ff")
                self.DebugLog(f"[MOCK TERATERM] Boot failure: {self.testresult}", 1)
                self.DebugLog(f"[MOCK TERATERM] Scratchpad: {self.scratchpad}", 1)
                return
            
            # Boot successful - proceed with test execution stages
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
            
            # Determine test result based on generated log (boot was successful)
            if hasattr(self, '_test_failed') and self._test_failed:
                self.testresult = f"FAIL::{self.test or 'MockTest'}"
                # Use postcode already set in _generate_realistic_log()
                self.scratchpad = getattr(self, '_bios_postcode', "0xf0000001")
            else:
                self.testresult = f"PASS::{self.test or 'MockTest'}"
                # Use success postcode already set in _generate_realistic_log()  
                self.scratchpad = getattr(self, '_bios_postcode', "0xef0000ff")
            
            self.DebugLog(f"[MOCK TERATERM] Test completed: {self.testresult}", 1)
            self.DebugLog(f"[MOCK TERATERM] Scratchpad: {self.scratchpad}", 1)
    
    def _generate_realistic_log(self):
        """Generate realistic Dragon/Mesh/Slice test log content with Framework integration"""
        import random
        import os
        from datetime import datetime
        
        # Increment iteration count for Framework experiment tracking
        self.iteration_count += 1
        
        # Create capture.log in C:\Temp (as expected by real Framework)
        # This matches the real Teraterm behavior where TTL macros use: logopen 'C:\Temp\capture.log'
        capture_log_path = r'C:\Temp\capture.log'
        
        # Ensure C:\Temp directory exists
        os.makedirs(r'C:\Temp', exist_ok=True)
        
        # First determine if we reach the proper boot milestone
        content_type = (self.content or "dragon").lower()
        boot_success = self._determine_boot_success()
        
        if boot_success:
            # Generate full test content - we reached the boot milestone
            if "dragon" in content_type:
                log_content = self._generate_dragon_log()
            elif "linux" in content_type:
                log_content = self._generate_linux_log()
            elif "mesh" in content_type:
                log_content = self._generate_mesh_log()
            elif "slice" in content_type:
                log_content = self._generate_slice_log()
            else:
                log_content = self._generate_generic_log()
        else:
            # Generate boot failure log - no test content executed
            log_content = self._generate_boot_failure_log(content_type)
        
        # Write log content to capture.log (Framework will copy this file)
        with open(capture_log_path, 'w') as f:
            f.write(log_content)
        
        self.DebugLog(f"[MOCK TERATERM] Generated capture.log: {capture_log_path}", 1)
        self.DebugLog(f"[MOCK TERATERM] Framework will copy this file to experiment folder", 1)
        
        # Store log path for potential additional processing
        self._generated_log_path = capture_log_path
    
    def _determine_boot_success(self):
        """Determine if boot reaches the appropriate milestone for test execution"""
        import random
        
        # 70% chance of reaching boot milestone (realistic failure rate)
        reaches_boot = random.random() > 0.3
        
        content_type = (self.content or "dragon").lower()
        
        if reaches_boot:
            if "linux" in content_type:
                # Reached Linux boot (0x58000000)
                self._boot_reached = True
                return True
            else:
                # Reached EFI boot (0xef0000ff) for Dragon
                self._boot_reached = True  
                return True
        else:
            # Boot failed - didn't reach test execution milestone
            self._boot_reached = False
            return False
    
    def _generate_boot_failure_log(self, content_type):
        """Generate minimal log showing boot failure - no test content"""
        import random
        
        # Boot failure postcodes - didn't reach 0xef or 0x58
        if "linux" in content_type:
            failure_postcodes = ["0xaf0000ff", "0xb70000ff", "0x4f000000", "0x32000000"]
        else:
            failure_postcodes = ["0xaf0000ff", "0xb70000ff", "0x4f000000"] 
            
        failed_postcode = random.choice(failure_postcodes)
        self._bios_postcode = failed_postcode
        self._test_failed = True
        
        # Generate failure reason based on postcode
        if failed_postcode == "0xb70000ff":
            self._fail_reason = "Memory_Training_Failed"
            failure_description = "Memory training initialization failed"
        elif failed_postcode == "0xaf0000ff":
            self._fail_reason = "Boot_Sequence_Failed"  
            failure_description = "Boot sequence failure detected"
        elif failed_postcode == "0x4f000000":
            self._fail_reason = "Hardware_Init_Failed"
            failure_description = "Hardware initialization error"
        elif failed_postcode == "0x32000000":
            self._fail_reason = "Early_Boot_Failed"
            failure_description = "Early boot stage failure"
        else:
            self._fail_reason = "Boot_Failed"
            failure_description = "Unknown boot failure"
        
        # Minimal boot failure log - no test execution
        if "linux" in content_type:
            return f"""Echo is off.

System boot initialization...
POST Code: 0x01000000 - Power on self test
POST Code: 0x0e000000 - Microcode loading  
POST Code: 0x16000000 - Cache initialization
POST Code: 0x19000000 - Memory detection
POST Code: {failed_postcode} - {failure_description}

BOOT FAILED: System did not reach Linux boot milestone (0x58000000)
No test content executed.
"""
        else:
            return f"""Echo is off.

System boot initialization...
POST Code: 0x01000000 - Power on self test
POST Code: 0x0e000000 - Microcode loading
POST Code: 0x16000000 - Cache initialization  
POST Code: 0x19000000 - Memory detection
POST Code: {failed_postcode} - {failure_description}

BOOT FAILED: System did not reach EFI boot milestone (0xef0000ff)
No Dragon test content executed.
"""
    
    def _generate_dragon_log(self):
            """Generate realistic Dragon test log with Framework variables integration"""
            import random
            
            # Start with boot sequence
            log_lines = [
                "Echo is off.",
                "",
                "System boot initialization...",
                "POST Code: 0x01000000 - Power on self test", 
                "POST Code: 0x0e000000 - Microcode loading",
                "POST Code: 0x16000000 - Cache initialization",
                "POST Code: 0x19000000 - Memory detection"
            ]
            
            # Check if we reach Dragon EFI boot milestone  
            boot_reached = getattr(self, '_boot_reached', True)
            
            if not boot_reached:
                # Boot failed - return minimal log with no test content
                return "\n".join(log_lines + [
                    f"POST Code: {getattr(self, '_bios_postcode', '0xaf0000ff')} - Boot failure",
                    "",
                    "BOOT FAILED: System did not reach EFI boot milestone (0xef0000ff)",
                    "No Dragon test content executed."
                ])
            
            # Boot successful - continue with full test content
            log_lines.extend([
                "POST Code: 0xef0000ff - EFI Boot successful",
                "Entering Dragon test execution...",
                ""
            ])
            
            # Generate realistic seeds - Dragon format: DL{cores}-{pattern}-{id}-{hex}
            cores = random.choice([32, 48, 64, 80])
            patterns = ["Blender", "Ditto", "Yakko"]
            ids = ["Z1J", "X2K", "Y3L", "W4M"]
            
            # Generate 3-5 test iterations
            num_tests = random.randint(3, 5)
            failing_seed = None
            
            for i in range(num_tests):
                # Generate seed
                hex_suffix = f"{random.randint(0xF100000, 0xF199999):08X}"
                seed = f"DL{cores}-{random.choice(patterns)}-{random.choice(ids)}-{hex_suffix}.obj"
                
                # Add test execution
                log_lines.extend([
                    f"Running FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{seed}",
                    f"Running MerlinX.efi   -a FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{seed} -d 0 0x4C4B40 1 80064000 2 0x1000000 3 0x4000000",
                    "CAPID0_CFG_PCU_FUN0_REG = 0x41589129, MiniDPE = NOT enabled",
                    "MerlinX Version                             [8.15]",
                    "MerlinX [info] Is official version          [True]",
                    f"Image Handle = {random.randint(1600000000, 1699999999)} , {random.randint(0x5F000000, 0x5FFFFFFF):08X}"
                ])
                
                # Determine if this test passes or fails (70% pass rate)
                if random.random() < 0.3 and failing_seed is None:  # First failure
                    failing_seed = seed
                    self._test_failed = True
                    self._fail_reason = f"Test_Failed"
                    
                    # Add configuration block for failures
                    log_lines.extend([
                        "Buffer = 5FB29498 and BufferStart = 5FB29498",
                        "<Configuration>",
                        "<Symbols />",
                        "<Vvars>",
                        f"<Vvar Number=\"0x0\" Value=\"{self.vvars['vvar0']}\" />",
                        # Framework variables (from TTL configs.ini)
                        f"<Vvar Number=\"0x1\" Value=\"{self.vvars['vvar1']}\" />",
                        f"<Vvar Number=\"0x2\" Value=\"{self.vvars['vvar2']}\" />", 
                        f"<Vvar Number=\"0x3\" Value=\"{self.vvars['vvar3']}\" />",
                        f"<Vvar Number=\"0x5\" Value=\"0x7FFFFFFF\" />",
                        f"<Vvar Number=\"0x8\" Value=\"0x1FFFAFF\" />",
                        f"<Vvar Number=\"0x9\" Value=\"0xFFFFFFFF\" />",
                        f"<Vvar Number=\"0xA\" Value=\"0x{random.randint(0x50, 0xFF):02X}\" />",
                        f"<Vvar Number=\"0xB\" Value=\"0x{random.randint(0x7000, 0x7FFF):04X}\" />",
                        # VVAR 0xC-0x20 - These indicate failure points
                        f"<Vvar Number=\"0xC\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0xD\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0xE\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0xF\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x10\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x11\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x12\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x13\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x14\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x15\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x16\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x17\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x18\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x19\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x1A\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x1B\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x1C\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x1D\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x1E\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x1F\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x20\" Value=\"0x{random.randint(0xAC000000, 0xACFFFFFF):08X}\" />",
                        # Additional failure pattern VVARs
                        f"<Vvar Number=\"0x22\" Value=\"0xAC040D03\" />",  # Specific failure pattern
                        f"<Vvar Number=\"0x23\" Value=\"0xAC000000\" />",
                        # High-address VVARs from your example  
                        f"<Vvar Number=\"0x32C\" Value=\"0x{random.randint(0x20000000, 0x2FFFFFFF):08X}\" />",
                        f"<Vvar Number=\"0x32E\" Value=\"0x7FFFFFFF\" />",
                        "</Vvars>",
                        "</Configuration>",
                        f"MerlinX {random.randint(8000, 8999)}F Test Failed: FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{seed}",
                        f"Deleting 'FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{seed}.hng'",
                        "Delete successful.",
                        f"FAILED: FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{seed}",
                        "Stopping regression due to failure",
                        "",
                        "======================================",
                        "=        TEST STATUS: FAILED         =",
                        "=         REGRESSION STOPPED         =",
                        "======================================",
                        "Test Failed",
                        f"REGRESSION INFO: FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\\\log.txt",
                        f"FAILURE INFO: FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\\\fail.txt",
                        "CHANGING BACK TO DIR: FS1:\\EFI",
                        "FS1:\\EFI\\> #Test Failed",
                        "FS1:\\EFI\\>"
                    ])
                    break
                else:
                    # Passing test
                    log_lines.extend([
                        f"Merlinx Version {random.randint(8000, 8999)}F Test Passed FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{seed}",
                        f"Deleting 'FS1:\\content\\Dragon\\GNR{cores}C_L_MOSBFT_HToff_pseudoSBFT_System\\{seed}.hng'",
                        "Delete successful.",
                        "**************",
                        ""
                    ])
            
            # Set final postcode based on overall test result
            if not hasattr(self, '_test_failed') or not self._test_failed:
                self._bios_postcode = "0xef0000ff"  # Dragon success postcode
                self._test_failed = False
            # Failure postcode already set above in failure case
            
            return "\n".join(log_lines)
    
    def _generate_linux_log(self):
        """Generate realistic Linux test log (TSL, Sandstone, MLC, etc.)"""
        import random
        
        # Start with boot sequence  
        boot_lines = [
            "System boot initialization...",
            "POST Code: 0x01000000 - Power on self test",
            "POST Code: 0x0e000000 - Microcode loading", 
            "POST Code: 0x16000000 - Cache initialization",
            "POST Code: 0x19000000 - Memory detection"
        ]
        
        # Check if we reach Linux boot milestone
        boot_reached = getattr(self, '_boot_reached', True)
        
        if not boot_reached:
            # Boot failed - return minimal log with no test content
            return "\n".join(boot_lines + [
                f"POST Code: {getattr(self, '_bios_postcode', '0xaf0000ff')} - Boot failure",
                "",
                "BOOT FAILED: System did not reach Linux boot milestone (0x58000000)",
                "No Linux test content executed."
            ])
        
        # Boot successful - continue with Linux test content
        boot_lines.extend([
            "POST Code: 0x58000000 - Linux Boot successful", 
            "Entering Linux test execution...",
            ""
        ])
        
        # Detect Linux content type from commands/content
        linux_commands = getattr(self, 'linux_commands', [])
        content_type = "tsl"  # Default to TSL
        
        # Try to detect content type from command patterns
        if hasattr(self, 'vvars') and 'linux_content_line_0' in str(self.vvars):
            command_line = str(self.vvars)
            if 'tsl' in command_line.lower():
                content_type = "tsl"
            elif 'sandstone' in command_line.lower():
                content_type = "sandstone" 
            elif 'mlc' in command_line.lower():
                content_type = "mlc"
            elif 'ocelot' in command_line.lower():
                content_type = "ocelot"
        
        # Generate content-specific log
        if content_type == "tsl":
            test_content = self._generate_tsl_log()
        elif content_type == "sandstone":
            test_content = self._generate_sandstone_log()
        elif content_type == "mlc":
            test_content = self._generate_mlc_log()
        elif content_type == "ocelot":
            test_content = self._generate_ocelot_log()
        else:
            test_content = self._generate_generic_linux_log()
        
        # Combine boot sequence with test content
        return "\n".join(boot_lines) + "\n" + test_content
    
    def _generate_tsl_log(self):
        """Generate realistic TSL (Test Seed Loader) log based on user example"""
        import random
        
        # TSL Dragon seeds from user example
        tsl_seeds = [
            "DH02-BR-0550000A.obj algo (LN, YO)",
            "DH02-BR-05500071.obj algo (SA, YO)", 
            "DH02-BR-0550005C.obj algo (LN, FM)"
        ]
        
        # Generate realistic system info
        cores = random.choice([120, 128, 144, 160])
        threads = cores * 2
        seed_number = random.randint(1000000000, 1999999999)
        
        log_lines = [
            "VERIFYING FILES AND DIRECTORIES",
            "",
            "Determined current user directory        : /root/YAKKO/0072",
            "Determined dragon license file directory : /root/YAKKO/0072/.tsl/License", 
            "Determined dragon logs file directory    : /root/YAKKO/0072/.tsl/Logs",
            "",
            "Determined DRAGON log file name          : /root/YAKKO/0072/.tsl/Logs/TestLoad_7840_2023-08-22_00.27.57.log",
            "",
            "Verifying cfg file entries - please wait...",
            "",
            "",
            "System information retrieved...",
            "",
            "	General information         :",
            "	Test Seed Loader revision   : 3.9.1",
            f"	Random Seed Number          : {seed_number}",
            "	Operating system            : CentOS Stream 9",
            "	Kernel version              : Linux 6.2.0-gnr.bkc.6.2.9.3.33.x86_64",
            "	System under test name      : gnr-bkc",
            "	Processor model detected    : Intel(R) Xeon(R) 6985P-C",
            "	Processor packages detected : 1",
            f"	Processor cores detected    : {cores}",
            f"	Processor threads detected  : {threads}",
            "	Hyperthreading enabled      : Yes",
            "",
            "	# CPUID ISA",
            "	# EAX      ECX     =>   EAX      EBX      ECX      EDX",
            "	00000001 00000000  => 000a06d1 00ff0800 7ffefbff bfebfbff",
            "	00000007 00000000  => 00000002 f3bfbfff fb417ffe ffdd4432",
            "	00000007 00000001  => 40601d30 00000001 00000000 000e4000",
            "	80000001 00000000  => 00000000 00000000 00000121 2c100800",
            "	80000008 00000000  => 00003934 00000200 00000000 00000000",
            "",
            "	# XCR0",
            "	# ECX     =>   EDX      EAX",
            "	00000000  => 00000000 000602e7",
            "",
            "Initializing memory for dragon seed tests...",
            "",
            "	Required memory is initialized.",
            "",
            "Assigning signal handlers - please wait...",
            "",
            "	Signal handlers have been assigned.",
            "",
            "Creating test log - please wait...",
            "",
            "	Test log created.",
            "",
            f"Running DRAGON seed(s): PARALLEL EXECUTION, targeted cores are {','.join(map(str, range(0, cores, 2)))}, all sockets, executing failing_seeds.list configuration file  - please wait...",
            "",
            "	Directory: ./../../content/LOS/DragonOnLinux_2022REL_0x05/GNR1C_BR_HT"
        ]
        
        # Generate test execution with realistic failures  
        failing_core = None
        if random.random() < 0.3:  # 30% failure rate
            failing_core = random.randint(0, cores//8) * 2
            self._test_failed = True
            self._fail_reason = f"TSL_Core_{failing_core}_Fail"
            self._bios_postcode = random.choice(["0xaf0000ff", "0x4f000000", "0x32000000"])
        else:
            self._bios_postcode = "0x58000000"  # Linux success
            
        # Add test execution logs
        for i in range(20):  # Generate multiple test iterations
            seed = random.choice(tsl_seeds)
            log_lines.append(f"\t{seed}")
            
            # Add failure if this is the failing core
            if failing_core is not None and i % 8 == failing_core // 2:
                fail_mask = f"0x{random.randint(0xf0000240, 0xf0000447):08x}"
                fail_mask2 = "0x00000000"
                log_lines.append(f"\t Core {failing_core:03d} FailMask 0x2 ({fail_mask}, {fail_mask2}) {seed}")
                
        # Add execution summary
        if failing_core is not None:
            log_lines.extend([
                "",
                f"	Total test time    : 00:{random.randint(5, 15)}:{random.randint(10, 59):02d}",
                "",
                "TSL tool is aborted as per user request.",
                "Reclaiming topology resources - please wait...",
                "",
                "Application cleanup - please wait..."
            ])
        else:
            log_lines.extend([
                "",
                f"	Total test time    : 00:{random.randint(15, 30)}:{random.randint(10, 59):02d}",
                "",
                "All tests completed successfully.",
                "Reclaiming topology resources - please wait...",
                "",
                "Application cleanup - please wait..."
            ])
        
        # Set Linux postcode based on test result
        if not hasattr(self, '_test_failed') or not self._test_failed:
            self._bios_postcode = "0x58000000"  # Linux success postcode
            self._test_failed = False
        # Failure postcode already set above in failure case
            
        return "\n".join(log_lines)
    
    def _generate_sandstone_log(self):
        """Generate Sandstone test log"""
        import random
        
        if random.random() < 0.3:
            self._test_failed = True
            self._fail_reason = "Sandstone_Fail"
            self._bios_postcode = "0xaf0000ff"
            return """Sandstone Test Framework
Test execution started...
ERROR: Sandstone validation failed
Test Status: FAILED"""
        else:
            self._bios_postcode = "0x58000000"
            return """Sandstone Test Framework  
Test execution started...
All Sandstone tests passed
Test Status: PASSED"""
    
    def _generate_mlc_log(self):
        """Generate MLC (Memory Latency Checker) test log"""
        import random
        
        if random.random() < 0.3:
            self._test_failed = True
            self._fail_reason = "MLC_Memory_Fail" 
            self._bios_postcode = "0xb70000ff"  # Memory training failure
            return """Intel(R) Memory Latency Checker - v3.11
Memory latency test starting...
ERROR: Memory validation failed
Bandwidth test: FAILED
Latency test: FAILED"""
        else:
            self._bios_postcode = "0x58000000"
            return """Intel(R) Memory Latency Checker - v3.11
Memory latency test starting...
Bandwidth test: PASSED
Latency test: PASSED
All tests completed successfully"""
    
    def _generate_ocelot_log(self):
        """Generate Ocelot test log (from user example)"""
        import random
        
        if random.random() < 0.3:
            self._test_failed = True 
            self._fail_reason = "Ocelot_Flow_Fail"
            self._bios_postcode = "0xaf0000ff"
            return """/usr/local/bin/ocelot --flow /root/content/LOS/LOS-23WW24/Mlc/flows/Mlc_mp2.xml --write_log_file_to_stdout=on --ituff=on
Ocelot flow execution started...
ERROR: Flow execution failed
Result=FAILED"""
        else:
            self._bios_postcode = "0x58000000"
            return """/usr/local/bin/ocelot --flow /root/content/LOS/LOS-23WW24/Mlc/flows/Mlc_mp2.xml --write_log_file_to_stdout=on --ituff=on
Ocelot flow execution started...
Flow completed successfully
Result=SUCCESS"""
    
    def _generate_generic_linux_log(self):
        """Generate generic Linux test log"""
        import random
        
        if random.random() < 0.3:
            self._test_failed = True
            self._fail_reason = "Linux_Generic_Fail"
            self._bios_postcode = "0xaf0000ff"
            return """Linux test execution started...
ERROR: Generic Linux test failed
Test Status: FAILED"""
        else:
            self._bios_postcode = "0x58000000" 
            return """Linux test execution started...
Linux test completed successfully
Test Status: PASSED"""
    
    def _generate_mesh_log(self):
            """Generate realistic Mesh test log"""
            import random
            
            # Mesh tests typically have different patterns
            log_lines = [
                "Echo is off.",
                "Starting Mesh Test Execution",
                ""
            ]
            
            # Simulate mesh test with potential failure
            if random.random() < 0.4:  # 40% failure rate for mesh
                self._test_failed = True
                self._fail_reason = "Mesh_Timeout_Error"
                
                log_lines.extend([
                    "Running Mesh Content Test",
                    "Mesh initialization... OK",
                    "Starting traffic patterns...",
                    f"Pattern execution timeout at iteration {random.randint(50, 150)}",
                    "ERROR: Mesh traffic timeout detected",
                    "TEST STATUS: FAILED",
                    f"Failed seed: MESH_{random.randint(1000, 9999):04d}"
                ])
            else:
                log_lines.extend([
                    "Running Mesh Content Test", 
                    "Mesh initialization... OK",
                    "Traffic patterns completed successfully",
                    "All mesh nodes responding",
                    "TEST STATUS: PASSED"
                ])
                
            return "\n".join(log_lines)
    
    def _generate_slice_log(self):
            """Generate realistic Slice test log"""
            import random
            
            log_lines = [
                "Echo is off.",
                "Starting Slice Test Execution",
                ""
            ]
            
            if random.random() < 0.3:  # 30% failure rate for slice
                self._test_failed = True
                core_fail = random.randint(0, 15)
                self._fail_reason = f"Core{core_fail}_Slice_Fail"
                
                log_lines.extend([
                    "Initializing slice configuration",
                    f"Core {core_fail} slice test starting...",
                    f"ERROR: Core {core_fail} slice validation failed",
                    "Slice test aborted",
                    "TEST STATUS: FAILED",
                    f"Failing core: {core_fail}"
                ])
            else:
                log_lines.extend([
                    "Initializing slice configuration",
                    "All slice tests completed successfully", 
                    "TEST STATUS: PASSED"
                ])
                
            return "\n".join(log_lines)
    
    def _generate_generic_log(self):
            """Generate generic test log"""
            import random
            
            if random.random() < 0.25:  # 25% failure rate
                self._test_failed = True
                self._fail_reason = "Generic_Test_Fail"
                return f"""Test execution started
Generic test running...
ERROR: Test failed at step {random.randint(5, 20)}
TEST STATUS: FAILED"""
            else:
                return """Test execution started
Generic test running...
All steps completed successfully
TEST STATUS: PASSED"""


class MockSerialConnection:
    log_file_path = r"C:\Temp\capture.log"  # Match real Framework expectation
    
    @staticmethod
    def teraterm(*args, **kwargs):
        """Create MockTeraterm instance with proper Framework integration"""
        import shutil
        import os
        from datetime import datetime
        
        # Extract Framework experiment data
        experiment_data = {
            'visual': kwargs.get('visual', 'MOCK_VID'),
            'test': kwargs.get('test', 'Mock_Test'),
            'content': kwargs.get('content', 'dragon'),
            'qdf': kwargs.get('qdf', 'MOCK_QDF'),
            'bucket': kwargs.get('bucket', 'MockBucket'),
            'vvar1': kwargs.get('vvar1', '80064000'),
            'vvar2': kwargs.get('vvar2', '0x1000000'),
            'vvar3': kwargs.get('vvar3', '0x4000000'),
            'PassString': kwargs.get('PassString', ['Test Passed']),
            'FailString': kwargs.get('FailString', ['Test Failed'])
        }
        
        # Simulate Framework creating configs.ini in TTL folder
        ttl_folder = kwargs.get('ttl_folder', 'C:\\SystemDebug\\TTL')
        config_path = MockFileHandler.create_ttl_config_ini(ttl_folder, experiment_data)
        
        # Add ttl_folder to kwargs so MockTeraterm can read configs.ini
        kwargs['ttl_folder'] = ttl_folder
        
        # Create teraterm instance (will read from configs.ini)
        tt_instance = MockTeraterm(*args, **kwargs)
        
        # Framework experiment iteration tracking
        tt_instance.DebugLog(f"[MOCK SERIAL] Framework experiment starting", 1)
        tt_instance.DebugLog(f"[MOCK SERIAL] Created configs.ini: {config_path}", 1)
        tt_instance.DebugLog(f"[MOCK SERIAL] TTL macro will read VVARs from configs.ini", 1)
        
        return tt_instance
    
    @staticmethod
    def collect_teraterm_log(tt_instance, experiment_folder, iteration_num=None):
        """Simulate SerialConnection collecting Teraterm logs after each experiment iteration"""
        import shutil
        import os
        from datetime import datetime
        
        if not hasattr(tt_instance, '_generated_log_path') or not tt_instance._generated_log_path:
            if tt_instance.DebugLog:
                tt_instance.DebugLog("[MOCK SERIAL] No log generated to collect", 2)
            return None
            
        try:
            os.makedirs(experiment_folder, exist_ok=True)
            
            # Framework log naming: Include iteration and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            iter_suffix = f"_Iter{iteration_num}" if iteration_num else ""
            
            # Framework standard log naming
            log_filename = f"{tt_instance.visual}_{tt_instance.test}{iter_suffix}_{timestamp}.log"
            dst_log = os.path.join(experiment_folder, log_filename)
            
            # Copy Teraterm log to experiment folder
            shutil.copy2(tt_instance._generated_log_path, dst_log)
            
            if tt_instance.DebugLog:
                tt_instance.DebugLog(f"[MOCK SERIAL] Collected experiment log: {dst_log}", 1)
                tt_instance.DebugLog(f"[MOCK SERIAL] Log contains Framework VVARs 1-3 and failure indicators 0xC-0x20", 1)
            
            return dst_log
            
        except Exception as e:
            if tt_instance.DebugLog:
                tt_instance.DebugLog(f"[MOCK SERIAL] Error collecting log: {e}", 2)
            return None
    
    @staticmethod
    def copy_teraterm_log(source_log, destination_folder, logger=None):
        """Simulate copying Teraterm log to experiment folder"""
        import shutil
        import os
        
        try:
            os.makedirs(destination_folder, exist_ok=True)
            dst_path = os.path.join(destination_folder, "teraterm_log_copy.log")
            
            if os.path.exists(source_log):
                shutil.copy2(source_log, dst_path)
                if logger:
                    logger(f"[MOCK SERIAL] Copied Teraterm log to {dst_path}", 1)
                return dst_path
            else:
                if logger:
                    logger(f"[MOCK SERIAL] Source log not found: {source_log}", 2)
                return None
                
        except Exception as e:
            if logger:
                logger(f"[MOCK SERIAL] Error copying Teraterm log: {e}", 2)
            return None
    
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