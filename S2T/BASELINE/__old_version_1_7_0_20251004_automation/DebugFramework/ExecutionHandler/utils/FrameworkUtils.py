import time
from tabulate import tabulate
import os
import sys
from typing import Dict, List, Any, Optional, Callable
import importlib
from colorama import Fore, Style, Back

# S2T scripts

try:
	import users.gaespino.dev.S2T.CoreManipulation as gcm
except:
	print( '[WARNING] CoreManipulation Module not imported, ignore if testing. ')
	gcm = None

try:	
    import users.gaespino.dev.S2T.dpmChecks as dpm
except:
	print( '[WARNING] DPM Checks Module not imported, ignore if testing. ')
	dpm = None

try:
    import users.gaespino.dev.S2T.SetTesterRegs as s2t
except:
	print( '[WARNING] System to Tester Module not imported, ignore if testing. ')
	s2t = None
try:
    import users.gaespino.dev.S2T.Tools.utils as s2tutils
except:
	print( '[WARNING] System to Tester Utils Module not imported, ignore if testing. ')
	s2tutils = None
	
current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

sys.path.append(parent_dir)


''' -- Framework Utils -- rev 1.7'''

try:
    import SerialConnection as ser
except:
	print( '[WARNING] SerialConnection Module not imported, ignore if testing. ')
	ser = None

try:
    import FileHandler as fh
except:
	print( '[WARNING] File Hanlder Module not imported, ignore if testing. ')
	fh = None


try:
    import MaskEditor as gme
except:
	print( '[WARNING] File Hanlder Module not imported, ignore if testing. ')
	gme = None


class FrameworkUtils:

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
	def platform_check(com_port: str, ip_address: str):
		"""Check platform configuration"""
		TERATERM_PATH = ser.TERATERM_PATH
		TERATERM_RVP_PATH = ser.TERATERM_RVP_PATH
		TERATERM_INI_FILE = ser.TERATERM_INI_FILE
		
		fh.teraterm_check(
			com_port=com_port,
			ip_address=ip_address,
			teraterm_path=TERATERM_PATH,
			seteo_h_path=TERATERM_RVP_PATH,
			ini_file=TERATERM_INI_FILE,
			useparser=False,
			checkenv=True
		)
	
	@staticmethod
	def system_2_tester_default() -> Dict:
		"""Get default system to tester configuration"""
		return {
			'AFTER_MRC_POST': 0xbf000000,
			'EFI_POST': 0xef0000ff,
			'LINUX_POST': 0x58000000,
			'BOOTSCRIPT_RETRY_TIMES': 3,
			'BOOTSCRIPT_RETRY_DELAY': 60,
			'MRC_POSTCODE_WT': 30,
			'EFI_POSTCODE_WT': 60,
			'MRC_POSTCODE_CHECK_COUNT': 5,
			'EFI_POSTCODE_CHECK_COUNT': 10,
			'BOOT_STOP_POSTCODE': 0x0,
			'BOOT_POSTCODE_WT': 30,
			'BOOT_POSTCODE_CHECK_COUNT': 10
		}

	@staticmethod
	def Test_Macros_UI(root=None, data=None):
		"""Run TTL macro UI"""
		ser.run_ttl(root, data)
	
	@staticmethod
	def TTL_Test(visual: str, cmds: Dict, bucket: str = 'Dummy', 
				test: str = 'TTL Macro Validation', chkcore: int = None, 
				ttime: int = 30, tnum: int = 1, content: str = 'Dragon', 
				host: str = '192.168.0.2', PassString: str = 'Test Complete', 
				FailString: str = 'Test Failed', cancel_flag=False):
		"""Run TTL test"""
		qdf = dpm.qdf_str()
		
		ser.start(
			visual=visual,
			qdf=qdf,
			bucket=bucket,
			content=content,
			chkcore=chkcore,
			host=host,
			cmds=cmds,
			test=test,
			ttime=ttime,
			tnum=tnum,
			PassString=PassString,
			FailString=FailString,
			cancel_flag=cancel_flag
		)

	@staticmethod
	def get_unit_info() -> Dict:
		"""Get unit information"""
		return dpm.request_unit_info()
	
	@staticmethod
	def reboot_unit(waittime: int = 60, u600w: bool = False, wait_postcode: bool = False):
		"""Reboot unit"""
		if not u600w:
			dpm.powercycle(ports=[1])
		else:
			dpm.reset_600w()
			time.sleep(waittime)
		
		if wait_postcode:
			time.sleep(waittime)
			gcm._wait_for_post(gcm.EFI_POST, sleeptime=waittime)
			gcm.svStatus(refresh=True)
	
	@staticmethod
	def power_control(state: str = 'on', stime: int = 10):
		"""Control unit power"""
		if state == 'on':
			dpm.power_on(ports=[1])
		elif state == 'off':
			dpm.power_off(ports=[1])
		elif state == 'cycle':
			dpm.powercycle(stime=stime, ports=[1])
		else:
			FrameworkUtils.FrameworkPrint('-- No valid power configuration selected use: on, off or cycle', 2)
	
	@staticmethod
	def power_status() -> bool:
		"""Get power status"""
		try:
			return dpm.power_status()
		except:
			FrameworkUtils.FrameworkPrint('Not able to determine power status, setting it as off by default.', 2)
			return False
	
	@staticmethod
	def refresh_ipc():
		"""Refresh IPC connection"""
		try:
			gcm.svStatus(refresh=True)
		except:
			FrameworkUtils.FrameworkPrint('!!! Unable to refresh SV and Unlock IPC. Issues with your system..', 2)
	
	@staticmethod
	def reconnect_ipc():
		"""Reconnect IPC"""
		try:
			gcm.svStatus(checkipc=True, checksvcores=False, refresh=False, reconnect=True)
		except:
			FrameworkUtils.FrameworkPrint('!!! Unable to execute ipc reconnect operation, check your system ipc connection status...', 2)
	
	@staticmethod
	def warm_reset(waittime: int = 60, wait_postcode: bool = False):
		"""Perform warm reset"""
		try:
			dpm.warm_reset()
		except:
			FrameworkUtils.FrameworkPrint('Failed while performing a warm reset...', 2)
		
		if wait_postcode:
			time.sleep(waittime)
			gcm._wait_for_post(gcm.EFI_POST, sleeptime=waittime)
			gcm.svStatus(refresh=True)
	
	@staticmethod
	def read_current_mask() -> Dict:
		"""Read current mask configuration"""
		return dpm.fuses(rdFuses=True, sktnum=[0], printFuse=False)

	@staticmethod
	def Recipes(path: str = r'C:\Temp\DebugFrameworkTemplate.xlsx') -> Dict:
		"""Load recipes from file"""
		if path.endswith('.json'):
			data_from_sheets = fh.load_json_file(path)
		elif path.endswith('.xlsx'):
			data_from_sheets = fh.process_excel_file(path)
		else:
			return None
		
		tabulated_df = fh.create_tabulated_format(data_from_sheets)
		data_table = tabulate(tabulated_df, headers='keys', tablefmt='grid', showindex=False)
		print(data_table)
		
		return data_from_sheets

	@staticmethod
	def Masks(basemask=None, root=None, callback=None):
		"""Create debug mask"""
		return DebugMask(basemask, root, callback)



#######################################################
########## 		Masking Script 
#######################################################

def DebugMask(basemask=None, root=None, callback = None):

	#masks, array = gcm.CheckMasks(readfuse = True, extMasks=None)
	die = dpm.product_str()
	masks = dpm.fuses(rdFuses = True, sktnum =[0], printFuse=False) if basemask == None else basemask

	# Checks for all configurations, the dpm fuses will return None if that die is non existing on the system product

	compute0_core_hex = str(masks["ia_compute_0"]) if masks["ia_compute_0"] != None else None
	compute0_cha_hex = str(masks["llc_compute_0"]) if masks["llc_compute_0"] != None else None
	compute1_core_hex = str(masks["ia_compute_1"]) if masks["ia_compute_1"] != None else None
	compute1_cha_hex = str(masks["llc_compute_1"]) if masks["llc_compute_1"] != None else None
	compute2_core_hex = str(masks["ia_compute_2"]) if masks["ia_compute_2"] != None else None
	compute2_cha_hex = str(masks["llc_compute_2"]) if masks["llc_compute_2"] != None else None

	newmask = gme.Masking(root, compute0_core_hex, compute0_cha_hex, compute1_core_hex, compute1_cha_hex, compute2_core_hex, compute2_cha_hex, product = die.upper(), callback=callback)
	#editor = gme.SystemMaskEditor(compute0_core_hex, compute0_cha_hex, compute1_core_hex, compute1_cha_hex, compute2_core_hex, compute2_cha_hex, product = die.upper())
	#newmask = editor.start()

	return newmask

	#@staticmethod
	#def clear_s2t_cancel_flag(logger=FrameworkPrint):
	#	gcm.clear_cancel_flag(logger)	
