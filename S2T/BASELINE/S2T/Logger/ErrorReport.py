# ErrorReport.py - Multi-Product Error Report Generator
# Refactored to use ErrorReportGenerator class with MCADecoders support

import sys
import os

# Append the Main Scripts Path
FILE_PATH = os.path.abspath(os.path.dirname(__file__))
MAIN_PATH = os.path.join(FILE_PATH, '..')

sys.path.append(MAIN_PATH)

from importlib import import_module

import Logger.ErrorReportClass as erg
import ConfigsLoader as pe

# Import required modules for dependency injection
core_manipulation = None
file_handler = None
dpm_checks = None
ipccli = None
namednodes = None
sv = None

# Flag to change the import to the development path
dev_mode = pe.DEV_MODE
BASE_PATH = pe.BASE_PATH

try:
	import CoreManipulation as core_manipulation
except ImportError:
	print("[!] CoreManipulation module not available - some features will be disabled")

try:
	if dev_mode: 
		import users.gaespino.dev.DebugFramework.FileHandler as file_handler
	else:
		import users.gaespino.DebugFramework.FileHandler as file_handler
except ImportError:
	print("[!] FileHandler module not available - upload features will be disabled")

try:
	import dpmChecks as dpm_checks
except ImportError:
	print("[!] dpmChecks module not available - fuse/voltage operations will be disabled")

try:
	import ipccli
	import namednodes
	sv = namednodes.sv
	
except ImportError:
	print("[!] ipccli/namednodes not available - MCA dump features will be disabled")

ErrorReportGenerator = erg.ErrorReportGenerator

SELECTED_PRODUCT = pe.SELECTED_PRODUCT
SELECTED_VARIANT = pe.PRODUCT_VARIANT
LICENSE_DICT = pe.LICENSE_S2T_MENU
FRAMEWORK_CORELIC = [f"{k}:{v}" for k, v in LICENSE_DICT.items()]
FRAMEWORK_VTYPES = ["VBUMP", "FIXED", "PPVC"]
FRAMEWORK_RUNSTATUS = ["PASS", "FAIL"]
FRAMEWORK_CONTENT = ["Dragon", "Linux", "PYSVConsole"]

FRAMEWORK_VARS = {
	'qdf': '', 'tnum': '', 'mask': '', 'corelic': '', 'bumps': '',
	'htdis': '', 'dis2CPM': '', 'dis1CPM': '', 'freqIA': '', 'voltIA': '',
	'freqCFC': '', 'voltCFC': '', 'content': '', 'passstring': '',
	'failstring': '', 'runName': '', 'runStatus': '', 'scratchpad': '',
	'seed': '', 'ttlog': None
}

def run(visual='', Testnumber='', TestName='', chkmem=0, debug_mca=0,
		dr_dump=False, folder=None, WW='WW', Bucket='UNCORE',
		product=None, variant=None, QDF='', logger=None,
		upload_to_disk=False, upload_to_danta=False, framework_data=None):
	if product is None:
		product = SELECTED_PRODUCT
	if variant is None:
		variant = SELECTED_VARIANT
	if framework_data is None:
		framework_data = FRAMEWORK_VARS.copy()
	if folder is None:
		folder = "C:\\temp\\"
	
	print('='*80)
	print(f'ErrorReport - Product: {product}:{variant}')
	print(f'Test: {Testnumber}_{visual}_{TestName}')
	print('='*80)
	
	try:
		generator = ErrorReportGenerator(
			product=product, variant=variant,
			config_loader=pe, logger=logger,
			core_manipulation=core_manipulation,
			file_handler=file_handler,
			dpm_checks=dpm_checks
		)
		
		if generator.mca_decoders:
			print(f'\n{"-"*80}')
			print(f'MCA Decoders Status for {product}:')
			generator.mca_decoders.list_decoders()
			print(f'{"-"*80}\n')
		
		result = generator.run(
			visual=visual, Testnumber=Testnumber, TestName=TestName,
			chkmem=chkmem, debug_mca=debug_mca, dr_dump=dr_dump,
			folder=folder, WW=WW, Bucket=Bucket, QDF=QDF,
			logger=logger, upload_to_disk=upload_to_disk,
			upload_to_danta=upload_to_danta, framework_data=framework_data
		)
		
		print('\n' + '='*80)
		print(f'Error Report: {"SUCCESS" if result else "FAILED"}')
		print('='*80 + '\n')
		return result
	
	# Legacy fallback
	except Exception as e:
		print(f'ERROR: {e}')
		try:
			from Logger.ErrorReport_legacy import run_legacy
			return run_legacy(visual=visual, Testnumber=Testnumber, TestName=TestName,
							chkmem=chkmem, debug_mca=debug_mca, dr_dump=dr_dump,
							folder=folder, WW=WW, Bucket=Bucket, product=product,
							QDF=QDF, logger=logger, upload_to_disk=upload_to_disk,
							upload_to_danta=upload_to_danta, framework_data=framework_data)
		except:
			return False

def quick_run(visual='', Testnumber='', TestName='', product=None):
	return run(visual=visual, Testnumber=Testnumber, TestName=TestName, product=product)

def get_decoder(decoder_name, product=None):
	if product is None:
		product = SELECTED_PRODUCT
	try:
		generator = ErrorReportGenerator(
			product=product,
			core_manipulation=core_manipulation,
			file_handler=file_handler,
			dpm_checks=dpm_checks
		)
		return generator.get_decoder(decoder_name)
	except:
		return None

def list_decoders(product=None):
	if product is None:
		product = SELECTED_PRODUCT
	try:
		generator = ErrorReportGenerator(
			product=product,
			core_manipulation=core_manipulation,
			file_handler=file_handler,
			dpm_checks=dpm_checks
		)
		if generator.mca_decoders:
			generator.mca_decoders.list_decoders()
	except:
		pass

def get_generator(product=None, variant=None, logger=None):
	if product is None:
		product = SELECTED_PRODUCT
	if variant is None:
		variant = SELECTED_VARIANT
	
	return ErrorReportGenerator(
		product=product, variant=variant, config_loader=pe, logger=logger,
		core_manipulation=core_manipulation, file_handler=file_handler,
		dpm_checks=dpm_checks
	)

# ============================================================================
# MCA Dump Wrapper Functions - Product Specific
# ============================================================================

def mca_init():
	"""Initialize IPC connection for MCA operations"""
	import namednodes
	sv = namednodes.sv
	ErrorReportGenerator.mca_init(sv)

	return sv

def unlock():
	import ipccli
	itp = ipccli.baseaccess()
	ErrorReportGenerator.unlock(itp)

	return itp

def refresh_weakly_reference():
	ErrorReportGenerator.refresh_weakly_reference()

def mca_dump_gnr(verbose=True):
	"""
	GNR MCA dump wrapper - delegates to product-specific implementation
	Performs unlock in ErrorReport, then calls product-specific mca_dump

	Args:
		verbose (bool): If True, prints detailed register information

	Returns:
		tuple: (mcadata dict, pysvdecode dict) from product-specific mca_dump
	"""

	try:
		# Import and call product-specific mca_dump
		import product_specific.gnr.mca_banks as mca_banks

		if mca_banks is None:
			return {}, {}
		
		itp = unlock()
		sv = mca_init()
		refresh_weakly_reference()

		return mca_banks.mca_dump(sv, itp=itp, verbose=verbose)
	except Exception as e:
		print(f"[!] MCA dump failed: {e}")
		return {}, {}

def mca_dump_cwf(verbose=True):
	"""
	CWF MCA dump wrapper - delegates to product-specific implementation
	Performs unlock in ErrorReport, then calls product-specific mca_dump

	Args:
		verbose (bool): If True, prints detailed register information

	Returns:
		tuple: (mcadata dict, pysvdecode dict) from product-specific mca_dump
	"""

	try:
		
		# Import and call product-specific mca_dump
		import product_specific.cwf.mca_banks as mca_banks
		
		if mca_banks is None:
			return {}, {}
		
		itp = unlock()
		sv = mca_init()
		refresh_weakly_reference()

		return mca_banks.mca_dump(sv, itp=itp, verbose=verbose)
	except Exception as e:
		print(f"[!] MCA dump failed: {e}")
		return {}, {}

def mca_dump_dmr(verbose=True):
	"""
	DMR MCA dump wrapper - delegates to product-specific implementation
	Performs unlock in ErrorReport, then calls product-specific mca_dump

	Args:
		verbose (bool): If True, prints detailed register information

	Returns:
		tuple: (mcadata dict, pysvdecode dict) from product-specific mca_dump
	"""
	
	try:
		
		# Import and call product-specific mca_dump
		import product_specific.dmr.mca_banks as mca_banks

		if mca_banks is None:
			return {}, {}
		
		itp = unlock()
		sv = mca_init()
		refresh_weakly_reference()

		return mca_banks.mca_dump(sv, itp=itp, verbose=verbose)
	except Exception as e:
		print(f"[!] MCA dump failed: {e}")
		return {}, {}

def readscratchpad():
	"""Read scratchpad value"""
	dev_base_path = 'users.gaespino.dev'
	if pe.DEV_MODE:
		import_path = dev_base_path
	else:
		import_path = BASE_PATH
	return ErrorReportGenerator.readscratchpad(sv = sv, product=SELECTED_PRODUCT, base_path = import_path)

__all__ = ['run', 'quick_run', 'get_decoder', 'list_decoders', 'get_generator',
		   'mca_dump_gnr', 'mca_dump_cwf', 'mca_dump_dmr', 'mca_init',
		   'SELECTED_PRODUCT', 'SELECTED_VARIANT', 'FRAMEWORK_VARS']

if __name__ == '__main__':
	if len(sys.argv) >= 4:
		run(visual=sys.argv[1], Testnumber=sys.argv[2], TestName=sys.argv[3], product=sys.argv[4] if len(sys.argv) > 4 else None)
