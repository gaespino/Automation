"""
Mock module for dpmChecks.py logger function testing
This mock simulates the behavior of dpmChecks functions for DMR product
Created: December 2, 2025
"""

from unittest.mock import Mock, MagicMock
import datetime


class MockConfig:
    """Mock configuration object"""
    SELECTED_PRODUCT = 'DMR'
    PRODUCT_CONFIG = 'DMR'
    PRODUCT_VARIANT = 'AP'
    PRODUCT_CHOP = 'XCC'
    BASE_PATH = 'BASELINE_DMR'
    DEV_MODE = False
    MAXPHYSICAL = 64
    FUSE_INSTANCE = ['hwrs_top_ram']
    BOOTSCRIPT_DATA = {
        'DMR': {
            'compute_config': 'mock_compute_config',
            'segment': 'mock_segment'
        }
    }
    
    def reload(self):
        """Mock reload method"""
        pass
    
    def get_functions(self):
        """Mock get_functions method"""
        return Mock()


class MockGCM:
    """Mock for CoreManipulation module (gcm)"""
    EFI_POST = 0x80
    
    @staticmethod
    def svStatus(refresh=False):
        """Mock svStatus function"""
        print(f"[MOCK] gcm.svStatus called with refresh={refresh}")
        return True
    
    @staticmethod
    def coresEnabled():
        """Mock coresEnabled function"""
        print("[MOCK] gcm.coresEnabled called")
        return [0, 1, 2, 3]
    
    @staticmethod
    def _wait_for_post(post_code, sleeptime=60):
        """Mock wait_for_post function"""
        print(f"[MOCK] gcm._wait_for_post called with post_code={hex(post_code)}, sleeptime={sleeptime}")
        return True
    
    @staticmethod
    def mask_fuse_core_array(coremask):
        """Mock mask_fuse_core_array function"""
        print(f"[MOCK] gcm.mask_fuse_core_array called with coremask={coremask}")
        return []
    
    @staticmethod
    def fuse_cmd_override_reset(fuse_cmd_array, skip_init=False, boot=True, s2t=False):
        """Mock fuse_cmd_override_reset function"""
        print(f"[MOCK] gcm.fuse_cmd_override_reset called")
        return True
    
    @staticmethod
    def fuse_cmd_override_check(fuse_cmd_array, skip_init=True, bsFuses=None):
        """Mock fuse_cmd_override_check function"""
        print(f"[MOCK] gcm.fuse_cmd_override_check called with bsFuses={bsFuses}")
        return True


class MockDPMLog:
    """Mock for Logger module (dpmlog)"""
    
    @staticmethod
    def callUI(qdf='', ww='', product=''):
        """Mock callUI function"""
        print(f"[MOCK] dpmlog.callUI called with qdf={qdf}, ww={ww}, product={product}")
        return True


class MockDPMTileView:
    """Mock for ErrorReport module (dpmtileview)"""
    
    @staticmethod
    def run(visual, testnumber, testname, chkmem, debug_mca, dr_dump=True, 
            folder=None, WW='', Bucket='UNCORE', product='', QDF='', 
            logger=None, upload_to_disk=False, upload_to_danta=False):
        """Mock run function for error report generation"""
        print(f"[MOCK] dpmtileview.run called")
        print(f"  Visual ID: {visual}")
        print(f"  Test Number: {testnumber}")
        print(f"  Test Name: {testname}")
        print(f"  Check Memory: {chkmem}")
        print(f"  Debug MCA: {debug_mca}")
        print(f"  DR Dump: {dr_dump}")
        print(f"  Folder: {folder}")
        print(f"  WW: {WW}")
        print(f"  Bucket: {Bucket}")
        print(f"  Product: {product}")
        print(f"  QDF: {QDF}")
        print(f"  Upload to Disk: {upload_to_disk}")
        print(f"  Upload to Danta: {upload_to_danta}")
        
        # Simulate successful report generation
        return {
            'status': 'success',
            'report_path': f'{folder}\\{visual}_{testname}_WW{WW}.xlsx',
            'errors_found': 2,
            'mca_decoded': True
        }


class MockFuseUtils:
    """Mock for fuse utilities (fu)"""
    
    @staticmethod
    def get_visual_id(socket=None, tile='compute0'):
        """Mock get_visual_id function"""
        print(f"[MOCK] fu.get_visual_id called with socket={socket}, tile={tile}")
        return "QVRX12345678"
    
    @staticmethod
    def get_qdf_str(socket=None, die='cbb0.base'):
        """Mock get_qdf_str function"""
        print(f"[MOCK] fu.get_qdf_str called with socket={socket}, die={die}")
        return "L0_DMRAP_XCC"
    
    @staticmethod
    def get_ult(socket=None, tile='compute0', ult_in=None):
        """Mock get_ult function"""
        return {'textStr': 'mock_ult_string'}


class MockRequestInfo:
    """Mock for request_unit_info module (reqinfo)"""
    
    @staticmethod
    def get_unit_info(sv=None, ipc=None):
        """Mock get_unit_info function"""
        print(f"[MOCK] reqinfo.get_unit_info called")
        return {
            'visual_id': 'QVRX12345678',
            'qdf': 'L0_DMRAP_XCC',
            'product': 'DMR',
            'variant': 'AP',
            'chop': 'XCC',
            'socket_count': 1,
            'compute_count': 3
        }


class MockSV:
    """Mock for namednodes.sv"""
    
    class Socket:
        name = "socket0"
        target_info = {
            'device_name': 'DMR',
            'variant': 'AP',
            'chop': 'XCC'
        }
        
        class Computes:
            name = ['compute0', 'compute1', 'compute2']
            
            class Fuses:
                @staticmethod
                def load_fuse_ram():
                    print("[MOCK] sv.sockets.computes.fuses.load_fuse_ram called")
                    return True
            
            fuses = Fuses()
        
        computes = Computes()
    
    socket0 = Socket()
    sockets = Mock()
    
    @staticmethod
    def initialize():
        """Mock initialize function"""
        print("[MOCK] sv.initialize called")
        return True


class MockIPC:
    """Mock for IPC/baseaccess"""
    
    def __init__(self):
        self.connected = True
    
    def read(self, address):
        """Mock read function"""
        return 0x12345678
    
    def write(self, address, value):
        """Mock write function"""
        return True


# Module-level mock instances
config = MockConfig()
gcm = MockGCM()
dpmlog = MockDPMLog()
dpmtileview = MockDPMTileView()
fu = MockFuseUtils()
reqinfo = MockRequestInfo()
sv = MockSV()
ipc = MockIPC()
itp = ipc

# Mock log folder
log_folder = "C:\\temp\\mock_logs\\"


def getWW():
    """Mock getWW function - returns current work week"""
    currentdate = datetime.date.today()
    iso_calendar = currentdate.isocalendar()
    WW = iso_calendar[1]
    print(f"[MOCK] getWW called, returning WW{WW}")
    return WW


def visual_str(socket=None, die='compute0'):
    """Mock visual_str function"""
    print(f"[MOCK] visual_str called with socket={socket}, die={die}")
    return fu.get_visual_id(socket=socket, tile=die)


def qdf_str():
    """Mock qdf_str function"""
    print(f"[MOCK] qdf_str called")
    return fu.get_qdf_str(socket=sv.socket0, die='cbb0.base')


def product_str():
    """Mock product_str function"""
    return config.PRODUCT_CONFIG.upper()


def request_unit_info():
    """Mock request_unit_info function"""
    return reqinfo.get_unit_info(sv=sv, ipc=ipc)


def logger(visual='', qdf='', TestName='', Testnumber=0, dr_dump=True, 
           chkmem=0, debug_mca=0, folder=None, WW='', Bucket='UNCORE', 
           UI=False, refresh=False, logging=None, upload_to_disk=False, 
           upload_to_danta=False):
    """
    Mock logger function - simulates DPM Tileview for error logs
    
    This mock replicates the behavior of the actual logger function for testing purposes.
    """
    print("\n" + "="*80)
    print("[MOCK] logger function called")
    print("="*80)
    
    gcm.svStatus(refresh=refresh)
    
    if folder is None:
        folder = log_folder
        print(f"[MOCK] Using default folder: {folder}")
    
    if visual == '':
        visual = visual_str()
        if visual == '' and not UI:
            visual = "MOCK_VISUAL_ID"
            print(f"[MOCK] Using mock visual ID: {visual}")
    
    if qdf == '':
        qdf = qdf_str()
    
    product = config.SELECTED_PRODUCT
    
    if WW == '':
        WW = getWW()
    
    print(f"\n[MOCK] Logger Parameters:")
    print(f"  Visual ID: {visual}")
    print(f"  QDF: {qdf}")
    print(f"  Test Name: {TestName}")
    print(f"  Test Number: {Testnumber}")
    print(f"  Product: {product}")
    print(f"  WW: {WW}")
    print(f"  Bucket: {Bucket}")
    print(f"  UI Mode: {UI}")
    print(f"  Folder: {folder}")
    
    if UI:
        print("\n[MOCK] Running UI mode...")
        result = dpmlog.callUI(qdf=qdf, ww=WW, product=product)
    else:
        print("\n[MOCK] Running standard logger mode...")
        try:
            result = dpmtileview.run(
                visual, Testnumber, TestName, chkmem, debug_mca, 
                dr_dump=dr_dump, folder=folder, WW=WW, Bucket=Bucket, 
                product=product, QDF=qdf, logger=logging, 
                upload_to_disk=upload_to_disk, upload_to_danta=upload_to_danta
            )
            print(f"\n[MOCK] Logger execution successful!")
            print(f"[MOCK] Result: {result}")
            
        except Exception as e:
            print(f"\n[MOCK] Exception in logger (simulating retry)...")
            print(f"[MOCK] Exception: {e}")
            gcm.svStatus(refresh=True)
            result = dpmtileview.run(
                visual, Testnumber, TestName, chkmem, debug_mca, 
                dr_dump=dr_dump, folder=folder, WW=WW, Bucket=Bucket, 
                product=product, QDF=qdf, logger=logging, 
                upload_to_disk=upload_to_disk, upload_to_danta=upload_to_danta
            )
    
    print("\n" + "="*80)
    print("[MOCK] logger function completed")
    print("="*80 + "\n")
    
    return result


# Additional helper functions for testing
def powercycle(stime=10, ports=[1, 2]):
    """Mock powercycle function"""
    print(f"[MOCK] powercycle called with stime={stime}, ports={ports}")
    return True


def power_status():
    """Mock power_status function"""
    print("[MOCK] power_status called")
    return {'port1': 'ON', 'port2': 'ON'}


def fuses(rdFuses=True, sktnum=[0], printFuse=False):
    """Mock fuses function"""
    print(f"[MOCK] fuses called with rdFuses={rdFuses}, sktnum={sktnum}, printFuse={printFuse}")
    return {
        'ia_compute_0': 0xffffffffffffffff,
        'ia_compute_1': 0xffffffffffffffff,
        'ia_compute_2': 0xffffffffffffffff,
        'llc_compute_0': 0xffffffffffffffff,
        'llc_compute_1': 0xffffffffffffffff,
        'llc_compute_2': 0xffffffffffffffff
    }


if __name__ == "__main__":
    print("Mock dpmChecks module for DMR testing")
    print(f"Product: {config.SELECTED_PRODUCT}")
    print(f"Mock modules loaded successfully")
