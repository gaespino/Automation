"""
GNR (Granite Rapids) MCA Bank Definitions and Decoder
Author: gaespino
Last update: 12/11/25

Provides comprehensive MCA bank information for GNR product including:
- Bank ID to name mapping
- Scope information (Core, Socket, CHA, Memory)
- Physical instance counts
- Decoding utilities
"""

# ANSI Color codes for console output (Python 3.8+ compatible)
class Colors:
	"""ANSI color codes for terminal output."""
	GREEN = '\033[92m'
	RED = '\033[91m'
	BLUE = '\033[94m'
	CYAN = '\033[96m'
	YELLOW = '\033[93m'
	MAGENTA = '\033[95m'
	BOLD = '\033[1m'
	RESET = '\033[0m'
	
	@staticmethod
	def success(text):
		return f"{Colors.GREEN}{text}{Colors.RESET}"
	
	@staticmethod
	def error(text):
		return f"{Colors.RED}{text}{Colors.RESET}"
	
	@staticmethod
	def info(text):
		return f"{Colors.CYAN}{text}{Colors.RESET}"
	
	@staticmethod
	def warning(text):
		return f"{Colors.YELLOW}{text}{Colors.RESET}"

# GNR MCA Bank Definitions
# Based on GNR/SPR architecture with big cores

GNR_MCA_BANKS = {
	# Core-scoped banks (0-3)
	0: {
		'name': 'IFU',
		'full_name': 'Instruction Fetch Unit',
		'scope': 'Core',
		'merged': False,
		'instances': '1 per thread',
		'description': 'Instruction Fetch Unit errors',
		'register_path': 'sv.sockets.computes.cpu.cores.threads.ifu_cr_mc0_status'
	},
	1: {
		'name': 'DCU',
		'full_name': 'Data Cache Unit',
		'scope': 'Core',
		'merged': False,
		'instances': '1 per thread',
		'description': 'Data Cache Unit (L1 Data Cache) errors',
		'register_path': 'sv.sockets.computes.cpu.cores.threads.dcu_cr_mc1_status'
	},
	2: {
		'name': 'DTLB',
		'full_name': 'Data Translation Lookaside Buffer',
		'scope': 'Core',
		'merged': False,
		'instances': '1 per thread',
		'description': 'Data TLB errors',
		'register_path': 'sv.sockets.computes.cpu.cores.dtlb_cr_mc2_status'
	},
	3: {
		'name': 'ML2',
		'full_name': 'Mid-Level Cache L2',
		'scope': 'Core',
		'merged': False,
		'instances': '1 per core',
		'description': 'L2 Cache errors',
		'register_path': 'sv.sockets.computes.cpu.cores.ml2_cr_mc3_status'
	},
	
	# Uncore banks (4+)
	4: {
		'name': 'PMSB',
		'full_name': 'Power Management State Buffer',
		'scope': 'Core',
		'merged': False,
		'instances': '1 per core',
		'description': 'Power Management State Buffer errors',
		'register_path': 'sv.sockets.computes.uncore.core_pmsb.core_pmsbs.core_pmsb_instance.pmsb_top.pma_core.error_report'
	},
	5: {
		'name': 'CHA',
		'full_name': 'Caching and Home Agent',
		'scope': 'Uncore',
		'merged': False,
		'instances': 'Variable per socket',
		'description': 'LLC slice and home agent errors',
		'register_path': 'sv.sockets.computes.uncore.cha.chas.util.mc_status',
		'notes': 'One per LLC slice/CHA'
	},
	6: {
		'name': 'IMC',
		'full_name': 'Integrated Memory Controller',
		'scope': 'Uncore',
		'merged': False,
		'instances': 'Variable per socket',
		'description': 'Memory controller errors',
		'register_path': 'sv.sockets.computes.uncore.memss.mcs.chs.mcchan.imc0_mc_status',
		'notes': 'Includes channel and sub-channel errors'
	},
	7: {
		'name': 'B2CMI',
		'full_name': 'Box to Channel Memory Interface',
		'scope': 'Uncore',
		'merged': False,
		'instances': 'Variable per socket',
		'description': 'Box to Channel Memory Interface errors',
		'register_path': 'sv.sockets.computes.uncore.memss.b2cmis.mci_status'
	},
	8: {
		'name': 'MSE',
		'full_name': 'Memory Subsystem Error',
		'scope': 'Uncore',
		'merged': False,
		'instances': 'Variable per socket',
		'description': 'Memory subsystem errors',
		'register_path': 'sv.sockets.computes.uncore.memss.mcs.chs.mse.mse_mci_status'
	},
	9: {
		'name': 'LLC',
		'full_name': 'Last Level Cache',
		'scope': 'Uncore',
		'merged': False,
		'instances': 'Variable per socket',
		'description': 'LLC (L3) cache errors in SCF',
		'register_path': 'sv.sockets.computes.uncore.scf.scf_llc.scf_llcs.mci_status'
	},
	10: {
		'name': 'UPI',
		'full_name': 'Ultra Path Interconnect',
		'scope': 'IO',
		'merged': False,
		'instances': 'Variable per socket',
		'description': 'UPI (formerly QPI/KTI) link errors',
		'register_path': 'sv.sockets.ios.uncore.upi.upis.upi_regs.kti_mc_st',
		'notes': 'Socket-to-socket interconnect'
	},
	11: {
		'name': 'UBOX',
		'full_name': 'System Configuration Controller',
		'scope': 'IO',
		'merged': False,
		'instances': '1 per socket',
		'description': 'UBOX system configuration errors',
		'register_path': 'sv.sockets.io0.uncore.ubox.ncevents.ncevents_cr_ubox_mci_status',
		'notes': 'Includes IERR and MCERR logging'
	},
	12: {
		'name': 'PUNIT',
		'full_name': 'Power Control Unit',
		'scope': 'Socket',
		'merged': False,
		'instances': '2 per socket (compute + IO)',
		'description': 'Power management unit errors',
		'register_path': 'sv.sockets.computes.uncore.punit.ptpcfsms.ptpcfsms.mc_status',
		'notes': 'Separate instances for compute and IO tiles'
	},
	13: {
		'name': 'M2MEM',
		'full_name': 'Mesh to Memory',
		'scope': 'Uncore',
		'merged': False,
		'instances': 'Variable per socket',
		'description': 'Mesh to memory interface errors',
		'register_path': 'sv.sockets.computes.uncore.m2mem'
	},
	14: {
		'name': 'PCU',
		'full_name': 'Power Control Unit (Legacy)',
		'scope': 'Socket',
		'merged': False,
		'instances': '1 per socket',
		'description': 'Legacy PCU errors (use PUNIT for newer systems)',
		'register_path': None
	},
	15: {
		'name': 'IIO',
		'full_name': 'Integrated IO',
		'scope': 'IO',
		'merged': False,
		'instances': 'Variable per socket',
		'description': 'PCIe root complex and IIO stack errors',
		'register_path': 'sv.sockets.ios.uncore.iio'
	}
}

# Additional GNR-specific information
GNR_NOTES = {
	'core_architecture': 'GNR uses big core (Golden Cove/Raptor Cove) architecture',
	'threading': 'Each core supports 2 threads (hyperthreading)',
	'llc_distribution': 'LLC is distributed across CHA slices',
	'memory_channels': 'Variable memory channels depending on SKU (typically 8 or 12 channels)',
	'upi_links': 'Variable UPI links (typically 4-6) for multi-socket configurations',
	'cha_mapping': 'CHA count matches LLC slice count and varies by SKU'
}

# Common GNR configurations
GNR_CONFIGS = {
	'XCC': {
		'name': 'eXtreme Core Count',
		'cores': 'Up to 128',
		'cha_count': 'Up to 120',
		'memory_channels': 12,
		'upi_links': 6
	},
	'MCC': {
		'name': 'Medium Core Count',
		'cores': 'Up to 86',
		'cha_count': 'Up to 80',
		'memory_channels': 8,
		'upi_links': 4
	},
	'LCC': {
		'name': 'Low Core Count',
		'cores': 'Up to 64',
		'cha_count': 'Up to 60',
		'memory_channels': 8,
		'upi_links': 4
	}
}

# Tileview Locations (Spreadsheet)
SPREADSHEET_DATA = {    'name':'B2' ,
							'errors':'X8',
							'status':'X2' , 
							'pcbs':'B66' }

class MCADecoders:
	"""
	GNR-specific MCA decoder manager.
	Single source of truth for all decoder imports.
	
	This class uses direct imports and provides a clean interface to access
	product-specific decoders. If a decoder is not available, it returns None.
	"""
	
	def __init__(self):
		"""Load all available decoders using direct imports."""
		# MCA Decoders
		self.cha = self._import_decoder('pysvtools.server_ip_debug.cha', 'cha')
		self.llc = self._import_decoder('toolext.server_ip_debug.llc', 'llc')
		self.ubox = self._import_decoder('pysvtools.server_ip_debug.ubox', 'ubox')
		self.punit = self._import_decoder('toolext.server_ip_debug.punit', 'punit')
		self.pm = self._import_decoder('pysvtools.server_ip_debug.pm', 'pm')
		
		# Tools
		self.tileview = self._import_module('pysvtools.server_wave_4.tileview')
		self.dimm_info = self._import_module('mc.gnrDimmInfo')
		
		# Debug tools
		self.core_debug = self._import_module('core.debug')
		self.debug_mca = self._import_module('pysvtools.debug_mca')
		
		# Not available for GNR
		self.ccf = None
		self.ula = None
	
	def _import_decoder(self, module_path, class_name):
		"""
		Import a decoder class from a module.
		
		Args:
			module_path: Full module path (e.g., 'pysvtools.server_ip_debug.cha')
			class_name: Class name to extract (e.g., 'cha')
		
		Returns:
			Decoder class or None if import fails
		"""
		try:
			module = __import__(module_path, fromlist=[class_name])
			decoder = getattr(module, class_name)
			print(f"  {Colors.success('[+]')} Loaded {Colors.BOLD}{class_name}{Colors.RESET} for GNR")
			return decoder
		except ImportError:
			print(f"  {Colors.error('[X]')} {class_name} not available")
			return None
		except Exception as e:
			print(f"  {Colors.error('[X]')} Error loading {class_name}: {e}")
			return None
	
	def _import_module(self, module_path):
		"""
		Import a module directly.
		
		Args:
			module_path: Full module path
		
		Returns:
			Module or None if import fails
		"""
		try:
			module = __import__(module_path, fromlist=[''])
			module_name = module_path.split('.')[-1]
			print(f"  {Colors.success('[+]')} Loaded {Colors.BOLD}{module_name}{Colors.RESET} for GNR")
			return module
		except ImportError:
			module_name = module_path.split('.')[-1]
			print(f"  {Colors.error('[X]')} {module_name} not available")
			return None
		except Exception as e:
			module_name = module_path.split('.')[-1]
			print(f"  {Colors.error('[X]')} Error loading {module_name}: {e}")
			return None
	
	def get_decoder(self, decoder_name):
		"""
		Get a decoder by name.
		
		Args:
			decoder_name: Name of the decoder (e.g., 'cha', 'llc', 'tileview')
		
		Returns:
			Decoder module/class or None if not available
		"""
		return getattr(self, decoder_name.lower(), None)
	
	def list_decoders(self):
		"""List all available decoders and their status."""
		decoders = {
			'cha': self.cha,
			'ccf': self.ccf,
			'llc': self.llc,
			'ubox': self.ubox,
			'ula': self.ula,
			'punit': self.punit,
			'pm': self.pm,
			'core_debug': self.core_debug,
			'debug_mca': self.debug_mca,
		}
		
		tools = {
			'tileview': self.tileview,
			'dimm_info': self.dimm_info,
		}
		
		print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*50}{Colors.RESET}")
		print(f"{Colors.BOLD}{Colors.CYAN}  GNR MCA Decoders Status{Colors.RESET}")
		print(f"{Colors.BOLD}{Colors.CYAN}{'='*50}{Colors.RESET}")
		for name, decoder in sorted(decoders.items()):
			if decoder is not None:
				print(f"  {Colors.success('[+]')} {name:<15} {Colors.info('Available')}")
			else:
				print(f"  {Colors.error('[X]')} {name:<15} {Colors.warning('Not available')}")
		print(f"\n{Colors.BOLD}{Colors.MAGENTA}  Tools:{Colors.RESET}")
		for name, tool in sorted(tools.items()):
			if tool is not None:
				print(f"  {Colors.success('[+]')} {name:<15} {Colors.info('Available')}")
			else:
				print(f"  {Colors.error('[X]')} {name:<15} {Colors.warning('Not available')}")
		print(f"{Colors.CYAN}{'='*50}{Colors.RESET}\n")


# Alias for backward compatibility
mca_decoders = MCADecoders
	
def get_bank_info(bank_id):
	"""
	Get detailed information about a specific MCA bank.
	
	Args:
		bank_id (int): MCA bank ID
		
	Returns:
		dict: Bank information or None if bank not found
	"""
	return GNR_MCA_BANKS.get(bank_id)


def get_bank_name(bank_id):
	"""
	Get the short name of an MCA bank.
	
	Args:
		bank_id (int): MCA bank ID
		
	Returns:
		str: Bank name or 'UNKNOWN'
	"""
	bank = GNR_MCA_BANKS.get(bank_id)
	return bank['name'] if bank else f'UNKNOWN_BANK_{bank_id}'


def get_bank_full_name(bank_id):
	"""
	Get the full descriptive name of an MCA bank.
	
	Args:
		bank_id (int): MCA bank ID
		
	Returns:
		str: Full bank name
	"""
	bank = GNR_MCA_BANKS.get(bank_id)
	return bank['full_name'] if bank else f'Unknown Bank {bank_id}'


def decode_bank_error(bank_id, status_value=None, addr_value=None, misc_value=None):
	"""
	Decode MCA bank error with additional context.
	
	Args:
		bank_id (int): MCA bank ID
		status_value (int, optional): MCi_STATUS register value
		addr_value (int, optional): MCi_ADDR register value
		misc_value (int, optional): MCi_MISC register value
		
	Returns:
		dict: Decoded error information
	"""
	bank = get_bank_info(bank_id)
	if not bank:
		return {'error': f'Invalid bank ID: {bank_id}'}
	
	result = {
		'bank_id': bank_id,
		'bank_name': bank['name'],
		'full_name': bank['full_name'],
		'scope': bank['scope'],
		'merged': bank['merged'],
		'instances': bank['instances'],
		'description': bank['description']
	}
	
	if 'notes' in bank:
		result['notes'] = bank['notes']
	
	if status_value is not None:
		# Decode STATUS register fields
		result['valid'] = bool(status_value & (1 << 63))
		result['overflow'] = bool(status_value & (1 << 62))
		result['uc'] = bool(status_value & (1 << 61))  # Uncorrected
		result['en'] = bool(status_value & (1 << 60))  # Error enabled
		result['miscv'] = bool(status_value & (1 << 59))  # MISC valid
		result['addrv'] = bool(status_value & (1 << 58))  # ADDR valid
		result['pcc'] = bool(status_value & (1 << 57))  # Processor context corrupt
		result['mca_error_code'] = status_value & 0xFFFF
	
	return result


def format_bank_error(bank_id, register_path='', status_value=None):
	"""
	Format a human-readable MCA bank error message.
	
	Args:
		bank_id (int): MCA bank ID
		register_path (str): Full register path
		status_value (int, optional): MCi_STATUS value
		
	Returns:
		str: Formatted error message
	"""
	bank = get_bank_info(bank_id)
	if not bank:
		return f'MCA Bank {bank_id}: UNKNOWN'
	
	msg = f"MCA Bank {bank_id}: {bank['name']} ({bank['full_name']})\n"
	msg += f"  Scope: {bank['scope']} | Instances: {bank['instances']}"
	
	if bank['merged']:
		msg += " | MERGED"
	
	msg += f"\n  Description: {bank['description']}"
	
	if 'notes' in bank:
		msg += f"\n  Notes: {bank['notes']}"
	
	if register_path:
		msg += f"\n  Register: {register_path}"
	
	if status_value is not None:
		msg += f"\n  STATUS: 0x{status_value:016x}"
		if status_value & (1 << 63):
			msg += " [VALID]"
		if status_value & (1 << 61):
			msg += " [UNCORRECTED]"
	
	return msg


def get_banks_by_scope(scope):
	"""
	Get all banks for a specific scope.
	
	Args:
		scope (str): 'Core', 'Uncore', 'IO', or 'Socket'
		
	Returns:
		dict: Banks in the specified scope
	"""
	return {k: v for k, v in GNR_MCA_BANKS.items() if v['scope'] == scope}


def print_bank_table():
	"""
	Print a formatted table of all MCA banks.
	"""
	print("\n" + "="*100)
	print("GNR (Granite Rapids) MCA Bank Table")
	print("="*100)
	print(f"{'Bank':<6}{'Name':<12}{'Scope':<10}{'Merged':<8}{'Instances':<22}{'Description':<40}")
	print("-"*100)
	
	for bank_id in sorted(GNR_MCA_BANKS.keys()):
		bank = GNR_MCA_BANKS[bank_id]
		merged = 'Yes' if bank['merged'] else 'No'
		desc = bank['description'][:38]
		print(f"{bank_id:<6}{bank['name']:<12}{bank['scope']:<10}{merged:<8}{bank['instances']:<22}{desc:<40}")
	
	print("="*100)
	print("\nArchitecture Notes:")
	for key, note in GNR_NOTES.items():
		print(f"  - {note}")
	
	print("\nCommon SKU Configurations:")
	for sku, config in GNR_CONFIGS.items():
		print(f"  {sku} ({config['name']}):")
		print(f"    Cores: {config['cores']}, CHAs: {config['cha_count']}, "
			  f"Memory Channels: {config['memory_channels']}, UPI Links: {config['upi_links']}")
	print()


def decode_mca_bank(register_path, status_value=None):
	"""
	GNR-specific MCA bank decoder
	Decode MCA bank information from register path and status value.
	
	Args:
		register_path (str): Full register path from pysvtools
		status_value (int, optional): MCi_STATUS register value
		
	Returns:
		str: Formatted bank information or empty string if bank not identified
	"""
	try:
		bank_id = None
		
		# Core banks (0-3)
		if '_mc0_' in register_path.lower() or 'ifu_cr' in register_path.lower():
			bank_id = 0
		elif '_mc1_' in register_path.lower() or 'dcu_cr' in register_path.lower():
			bank_id = 1
		elif '_mc2_' in register_path.lower() or 'dtlb_cr' in register_path.lower():
			bank_id = 2
		elif '_mc3_' in register_path.lower() or 'ml2_cr' in register_path.lower():
			bank_id = 3
		elif 'pmsb' in register_path.lower() or 'pma_core' in register_path.lower():
			bank_id = 4
		elif 'cha' in register_path.lower() and 'util.mc_status' in register_path.lower():
			bank_id = 5
		elif 'mcchan' in register_path.lower() or 'imc0_mc' in register_path.lower():
			bank_id = 6
		elif 'b2cmi' in register_path.lower():
			bank_id = 7
		elif 'mse' in register_path.lower() and 'mci_status' in register_path.lower():
			bank_id = 8
		elif 'scf_llc' in register_path.lower():
			bank_id = 9
		elif 'upi' in register_path.lower() or 'kti_mc' in register_path.lower():
			bank_id = 10
		elif 'ubox' in register_path.lower():
			bank_id = 11
		elif 'punit' in register_path.lower() and 'ptpcfsm' in register_path.lower():
			bank_id = 12
		
		if bank_id is not None:
			bank_info = get_bank_info(bank_id)
			if bank_info:
				decoded = f" --> MCA Bank {bank_id}: {bank_info['name']} ({bank_info['full_name']})"
				decoded += f"\n     Scope: {bank_info['scope']} | {bank_info['description']}"
				if bank_info.get('notes'):
					decoded += f"\n     Note: {bank_info['notes']}"
				return decoded
		
	except Exception as e:
		# Silently fail if decoding fails
		pass
	
	return ""


def mca_dump(sv, itp, verbose=True):
	"""
	GNR-specific MCA dump function
	Dumps all Machine Check Architecture banks for GNR product
	
	Args:
		sv: pysvtools sv object (socket view)
		verbose (bool): If True, prints detailed register information
		
	Returns:
		tuple: (mcadata dict, pysvdecode dict) - mcadata contains TestName/TestValue lists,
			   pysvdecode contains flags for which banks have errors
			   
	Dumps the following banks:
	- Banks 0-3: Core banks (IFU, DCU, DTLB, MLC)
	- Bank 4: PMSB (Power Management)
	- Bank 5: CHA (Caching Home Agent)
	- Bank 6: iMC (Integrated Memory Controller)
	- Bank 7-9: B2CMI, MSE, LLC
	- UPI, UBOX, PUNIT
	"""

	def print_valid(i,a,mc,e,b=63,save=False):
		try:
			if verbose: 
				status_val = i.read()
				print("%s = 0x%x" %(i.path, status_val))
				# Add decoded bank information
				#decoded_info = decode_mca_bank(i.path, status_val)
				#if decoded_info:
				#    print(decoded_info)
			
			if i.bits(b,1): 
				a.append(i)
				mc.append(i)
				
				return True
			else:
				if save: mc.append(i)
				return False
		except:
			#print("Access failed to: {}".format(i.path))
			print("%s = <error reading>" %(i.path))
			e.append(i)
			return False

	a=[] #mcas
	e=[] #errors
	mc=[]
	mcadata = {'TestName':[],	'TestValue':[]}

	sv.sockets.cpu.cores.setaccess('crb') #no halt required

	with itp.device_locker():
		for i in sv.sockets.computes.cpu.cores.ml2_cr_mc3_status:
			if print_valid(i,a,mc,e):
				if i.bits(58,1): 
					a.append(i.parent.ml2_cr_mc3_addr)
					mc.append(i.parent.ml2_cr_mc3_addr)
				if i.bits(59,1): 
					mc.append(i.parent.ml2_cr_mc3_misc)
		for i in sv.sockets.computes.cpu.cores.dtlb_cr_mc2_status:
			if print_valid(i,a,mc,e):
				if i.bits(58,1): 
					a.append(i.parent.dtlb_cr_mc2_addr)
					mc.append(i.parent.dtlb_cr_mc2_addr)
				if i.bits(59,1):
					mc.append(i.parent.dtlb_cr_mc2_misc)
		for i in sv.sockets.computes.cpu.cores.threads.dcu_cr_mc1_status:
			if print_valid(i,a,mc,e):
				if i.bits(58,1): 
					a.append(i.parent.dcu_cr_mc1_addr)
					mc.append(i.parent.dcu_cr_mc1_addr)
				if i.bits(59,1):
					mc.append(i.parent.dcu_cr_mc1_misc)
		for i in sv.sockets.computes.cpu.cores.threads.ifu_cr_mc0_status:
			if print_valid(i,a,mc,e):
				if i.bits(58,1): 
					a.append(i.parent.ifu_cr_mc0_addr)
					mc.append(i.parent.ifu_cr_mc0_addr)
				if i.bits(59,1):
					mc.append(i.parent.ifu_cr_mc0_misc)

	for i in sv.sockets.computes.uncore.core_pmsb.core_pmsbs.core_pmsb_instance.pmsb_top.pma_core.error_report:
			if print_valid(i,a,mc,e,b=0):
				mc.append(i.parent.pma_debug)
				mc.append(i.parent.pma_debug2)
				mc.append(i.parent.pma_debug3)
	for i in sv.sockets.computes.uncore.cha.chas.util.mc_status:
		if print_valid(i,a,mc,e):
			if i.bits(58,1): 
				a.append(i.parent.mc_addr)
			mc.append(i.parent.mc_addr)
			if i.bits(59,1): 
				mc.append(i.parent.mc_misc)
				mc.append(i.parent.mc_misc2)
				mc.append(i.parent.mc_misc3)
	try:
		for i in sv.sockets.computes.uncore.memss.mcs.chs.mcchan.imc0_mc_status:
			if print_valid(i,a,mc,e):
				if i.bits(58,1): 
					a.append(i.parent.imc0_mc8_addr)
					mc.append(i.parent.imc0_mc8_addr)
				if i.bits(59,1): 
					mc.append(i.parent.imc0_mc_misc)
	except:
		for i in sv.sockets.soc.memss.mcs.chs.mcchan.imc0_mc_status:
			if print_valid(i,a,mc,e):
				if i.bits(58,1): 
					a.append(i.parent.imc0_mc8_addr)
					mc.append(i.parent.imc0_mc8_addr)
				if i.bits(59,1):
					mc.append(i.parent.imc0_mc_misc)
	try:
		for i in sv.sockets.computes.uncore.memss.b2cmis.mci_status:
			if print_valid(i,a,mc,e):
				if i.bits(58,1): 
					a.append(i.parent.mci_addr)
					mc.append(i.parent.mci_addr)
				if i.bits(59,1):
					mc.append(i.parent.mci_misc)
	except:
		for i in sv.sockets.soc.memss.b2cmis.mci_status:
			if print_valid(i,a,mc,e):
				if i.bits(58,1): 
					a.append(i.parent.mci_addr)
					mc.append(i.parent.mci_addr)
				if i.bits(59,1):
					mc.append(i.parent.mci_misc)
	try:
		for i in sv.sockets.computes.uncore.memss.mcs.chs.mse.mse_mci_status:
			if print_valid(i,a,mc,e):
				if i.bits(58,1): 
					a.append(i.parent.mse_mci_addr)
					mc.append(i.parent.mse_mci_addr)
				if i.bits(59,1):
					mc.append(i.parent.mci_misc)
	except:
		for i in sv.sockets.soc.memss.mcs.chs.mse.mse_mci_status:
			if print_valid(i,a,mc,e):
				if i.bits(58,1): 
					a.append(i.parent.mse_mci_addr)
					mc.append(i.parent.mse_mci_addr)
				if i.bits(59,1):
					mc.append(i.parent.mci_misc)
	for i in sv.sockets.computes.uncore.scf.scf_llc.scf_llcs.mci_status:
		if print_valid(i,a,mc,e):
			if i.bits(58,1): 
				a.append(i.parent.mci_addr)
				mc.append(i.parent.mci_addr)
			if i.bits(59,1):
				mc.append(i.parent.mci_misc)
	try:
		for i in sv.sockets.ios.uncore.upi.upis.upi_regs.kti_mc_st:
			if print_valid(i,a,mc,e):
				if i.bits(58,1): 
					a.append(i.parent.kti_mc_ad)
					mc.append(i.parent.kti_mc_ad)
	except:
		print('WARNING: skipping kti, not working - sv.sockets.ios.uncore.upi.upis.upi_regs.kti_mc_st')
	try:
		for i in sv.sockets.io0.uncore.ubox.ncevents.ncevents_cr_ubox_mci_status:
			print_valid(i,a,mc,e)
		for i in sv.sockets.io0.uncore.ubox.ncevents.ierrloggingreg:
			print_valid(i,a,mc,e,b=16)
		for i in sv.sockets.io0.uncore.ubox.ncevents.ncuevdbgsts:
			mc.append(i)
		for i in sv.sockets.io0.uncore.ubox.ncevents.ncevents_cr_ubox_mci_ctl:
			mc.append(i)
		for i in sv.sockets.io0.uncore.ubox.ncevents.mcerrloggingreg:
			mc.append(i)
		for i in sv.sockets.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg:
			mc.append(i)
	except:
		print('WARNING: skipping ubox, not working')
	try:
		for i in sv.sockets.computes.uncore.punit.ptpcfsms.ptpcfsms.mc_status:
			if print_valid(i,a,mc,e):
				if i.bits(59,1): 
					a.append(i.parent.mc_misc)
					mc.append(i.parent.mc_misc)
				a.append(i.parent.parent.parent.parent.pcodeio_map.io_firmware_mca_command)
				mc.append(i.parent.parent.parent.parent.pcodeio_map.io_firmware_mca_command)
		for i in sv.sockets.ios.uncore.punit.ptpcfsms.ptpcfsms.mc_status:
			if print_valid(i,a,mc,e):
				if i.bits(59,1): 
					a.append(i.parent.mc_misc)
					mc.append(i.parent.mc_misc)
				a.append(i.parent.parent.parent.parent.pcodeio_map.io_firmware_mca_command)
				mc.append(i.parent.parent.parent.parent.pcodeio_map.io_firmware_mca_command)
	except:
		print('WARNING: skipping punit, not working')
		
	pysvdecode = {'cha':False, 'llc':False, 'ubox':False, 'punit':False, 'pm':False, 'core':False  }
	if mc != []:
		for i in mc:
			mcadata['TestName'].append("%s" % i.path)
			mcadata['TestValue'].append("0x%x" % i.get_value())
			
	if a != []:
		print('\nFOUND VALID MCA')
		print('='*80)
		for i in a:
			status_val = i.get_value()
			print("%s = 0x%x" %(i.path, status_val))
			# Add decoded bank information for summary
			decoded_info = decode_mca_bank(i.path, status_val)
			if decoded_info:
				print(decoded_info)
			print('-'*80)
			if 'cha' in i.path: pysvdecode['cha'] = True
			if 'scf_llc' in i.path: pysvdecode['llc'] = True
			if 'ubox' in i.path: pysvdecode['ubox'] = True
			if 'punit' in i.path: pysvdecode['punit'] = True
			if 'punit' in i.path: pysvdecode['pm'] = True
			if 'cpu.core' in i.path: pysvdecode['core'] = True
			if verbose: print("%s \n"%i.show())
	else:
		print('did not find valid MCA')
	
	if e != []:
		print('errors found during mca_dump. see above')
	
	sv.sockets.cpu.cores.setaccess('default') #restore
	return mcadata, pysvdecode

def read_scratchpad(sv):
	"""Read scratchpad register value."""
	try:
		scratchpad = str(sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg)
		return scratchpad
	except Exception as e:
		print(f"[X] Error reading scratchpad: {e}")
		return "ERROR"    

if __name__ == '__main__':
	# Example usage
	print_bank_table()
	
	print("\nExample: Decoding Bank 0 (IFU):")
	print(format_bank_error(0))
	
	print("\nExample: Decoding Bank 5 (CHA) with STATUS:")
	status = 0xBE00000000800150  # Example valid uncorrected error
	print(format_bank_error(5, status_value=status))
	
	print("\nExample: Get all Core-scoped banks:")
	core_banks = get_banks_by_scope('Core')
	for bank_id, bank in core_banks.items():
		print(f"  Bank {bank_id}: {bank['name']} - {bank['description']}")
