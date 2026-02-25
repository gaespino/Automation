## DMR MCA Decoder for MCA Checker
## Created for DMR BigCore (PNC) architecture with dual-domain support
## Based on decoder.py structure

import json
import re
import pandas as pd
from pathlib import Path
import os
import sys

class decoder_dmr():
	"""
	DMR-specific MCA decoder class
	Architecture: BigCore (PNC), one thread per core, no SMT/HT
	Domains: CBB (banks 0-8) and IMH (banks 9-31)

	Important:
	- CCF (Bank 6): Contains LLC + CHA functionality (merged 32 CBO instances)
	- SCA (Bank 14): IO Caching Agent for UIO devices, NOT system LLC
	"""

	def __init__(self, data, mcadata):
		self.data = data
		self.mcadata = mcadata
		self.coretype = 'bigcore'

	# Helper function to extract values based on a pattern
	def extract_value(self, df, dfcol, pattern):
		if isinstance(pattern, str):
			pat = [pattern]
		else:
			pat = pattern

		regex_pat = '|'.join(pat)

		filtered = df[(df[dfcol].str.contains(regex_pat, case=False, na=False))]
		return filtered

	def check_fail_flow_prefix(self, test_name):

		# Detect FailFlow (FF) type from test name to differentiate FF vs non-FF cases
		# Example: DPMB_FF_VBUMP_100_SOCKET0__... -> ff_type = 'VBUMP_100'
		ff_match = re.search(r'_FF_(.+?)_SOCKET\d+', test_name)
		ff_type = ff_match.group(1) if ff_match else ''
		# Build prefix to scope lookup patterns: FF prefix for FF cases,
		# or the test name's own prefix for non-FF to avoid cross-matching
		if ff_type:
			ff_prefix = f'FF_{ff_type}_'
		else:
			prefix_match = re.search(r'^(.+?)SOCKET\d+', test_name)
			ff_prefix = prefix_match.group(1) if prefix_match else ''
		return ff_type, ff_prefix

	# Define the lookup pattern for each column - DMR specific patterns
	def lookup_pattern(self, cbb, compute, module, location, operation, suffix, env='', inst='', ptype='ccf', ff_prefix=''):
		"""
		DMR-specific register path patterns based on actual ErrorReport.py structure

		Args:
			cbb: CBB number (exact number, no wildcards)
			compute: COMPUTE number (exact number, no wildcards)
			module: MODULE number (exact number, no wildcards)
			location: Core/Instance number (exact number, no wildcards)
			operation: Operation type
			suffix: Register suffix (STATUS, ADDR, MISC, etc.)
			env: ENV number for CCF (0-3)
			inst: CBREGS_ALL instance number for CCF (00-77)
			ptype: Pattern type

		ptype options: ccf, core_ifu, core_dcu, core_dtlb, core_ml2, punit_cbb, punit_imh, ncu, rasip

		Note: IO patterns (ULA, IOCACHE, D2D) are handled by io_lookup_pattern()
		      Memory patterns (HA, HSF, SCA, SUBCHN, MSE) are handled by mem_lookup_pattern()
		"""

		# CBB Domain Patterns
		if ptype == 'ccf':
			# CCF (Caching/Coherency Fabric) - Bank 6
			# Pattern: SOCKET0__CBB{x}__BASE__I_CCF_ENV{env}__CBREGS_ALL{instance}__MC_STATUS
			# Must match exact ENV and CBREGS_ALL pair
			# Note: CCF contains LLC + CHA functionality (32 merged CBO instances)
			pattern = f"{ff_prefix}SOCKET0__CBB{cbb}__BASE__I_CCF_ENV{env}__CBREGS_ALL{inst}__MC_{suffix}"

		elif ptype == 'ncu':
			# NCU (Node Control Unit) - Bank 5
			# Pattern: SOCKET0__CBB{x}__BASE__SNCU_TOP__SNCEVENTS__MC5_STATUS
			pattern = f"{ff_prefix}SOCKET0__CBB{cbb}__BASE__SNCU_TOP__SNCEVENTS__MC5_{suffix}"

		elif ptype == 'punit_cbb':
			# Power Unit CBB - Bank 4
			# Pattern: SOCKET0__CBB{x}__BASE__PUNIT_REGS__PUNIT_GPSB__GPSB_INFVNN_CRS__MC_STATUS
			pattern = f"{ff_prefix}SOCKET0__CBB{cbb}__BASE__PUNIT_REGS__PUNIT_GPSB__GPSB_INFVNN_CRS__MC_{suffix}"

		# Core Patterns (Banks 0-3) - Need CBB, COMPUTE, MODULE, and CORE numbers
		elif ptype == 'core_ifu':
			# IFU - Bank 0 (Instruction Fetch Unit)
			# Pattern: SOCKET0__CBB{x}__COMPUTE{y}__MODULE{z}__CORE{w}__IFU_CR_MC0_STATUS
			# Note: DMR has one thread per core (no SMT/HT)
			pattern = f"{ff_prefix}SOCKET0__CBB{cbb}__COMPUTE{compute}__MODULE{module}__CORE{location}__IFU_CR_MC0_{suffix}"

		elif ptype == 'core_dcu':
			# DCU - Bank 1 (Data Cache Unit)
			pattern = f"{ff_prefix}SOCKET0__CBB{cbb}__COMPUTE{compute}__MODULE{module}__CORE{location}__DCU_CR_MC1_{suffix}"

		elif ptype == 'core_dtlb':
			# DTLB - Bank 2 (Data TLB)
			pattern = f"{ff_prefix}SOCKET0__CBB{cbb}__COMPUTE{compute}__MODULE{module}__CORE{location}__DTLB_CR_MC2_{suffix}"

		elif ptype == 'core_ml2':
			# MLC - Bank 3 (Module Level Cache / L2)
			# Pattern: SOCKET0__CBB{x}__COMPUTE{y}__MODULE{z}__ML2_CR_MC3_STATUS
			pattern = f"{ff_prefix}SOCKET0__CBB{cbb}__COMPUTE{compute}__MODULE{module}__ML2_CR_MC3_{suffix}"

		# IMH Domain Patterns
		elif ptype == 'punit_imh':
			# Power Unit IMH - Bank 11
			# Pattern: SOCKET0__IMH{imh}__PUNIT__RAS__GPSB__MC_STATUS
			pattern = f"{ff_prefix}SOCKET0__IMH{location}__PUNIT__RAS__GPSB__MC_{suffix}"

		elif ptype == 'rasip':
			# RASIP - Bank 10
			# Pattern: SOCKET0__IMH{imh}__RASIP__ROOT_RAS__RASIP_REGS_BLOCK__RASIP_REG_MSG_CR_RASIP_ERROR_HANDLER_CR__REG_CR_MCI_STATUS
			pattern = f"{ff_prefix}SOCKET0__IMH{location}__RASIP__ROOT_RAS__RASIP_REGS_BLOCK__RASIP_REG_MSG_CR_RASIP_ERROR_HANDLER_CR__REG_CR_MCI_{suffix}"

		else:
			# Default pattern if ptype is not recognized
			pattern = ""

		return pattern

	def io_lookup_pattern(self, imh='', cbb='', stack='', ula='', uxi='', uio='', iocache='', suffix='ADDR', ptype='ula_uios', ff_prefix=''):
		"""
		Build register path patterns for DMR IO MCA ADDR/MISC lookup

		Args:
			imh: IMH number (string)
			cbb: CBB number (string)
			stack: Stack number (string)
			ula: ULA number (string)
			uxi: UXI number (string)
			uio: UIO number (string)
			iocache: IOCACHE number (string)
			suffix: 'ADDR' or 'MISC' or 'AD' or 'MS'
			ptype: Pattern type

		Pattern types:
			- ula_uios: SOCKET0__IMH{n}__ULA__ULA_UIO{n}__ULA_MC_{AD/MS}
			- ula_d2dio: SOCKET0__IMH{n}__D2D_STACK__D2D_STACK_{n}__UXI_{n}__ULA_MC_{AD/MS}
			- ula_d2dcbb: SOCKET0__CBB{n}__BASE__D2D_STACK_{n}__ULA_{n}__ULA__ULA_MC_{AD/MS}
			- iocache: SOCKET0__IMH{n}__SCF__SCA__IOCACHE{n}__UTIL__MCI_{ADDR/MISC}
		"""
		if ptype == 'ula_uios':
			# ULA_UIOS pattern: SOCKET0__IMH{n}__ULA__ULA_UIO{n}__ULA_MC_AD/MS
			if suffix in ['ADDR', 'AD']:
				pattern = f'{ff_prefix}SOCKET0__IMH{imh}__ULA__ULA_UIO{uio}__ULA_MC_AD'
			elif suffix in ['MISC', 'MS']:
				pattern = f'{ff_prefix}SOCKET0__IMH{imh}__ULA__ULA_UIO{uio}__ULA_MC_MS'
			else:
				pattern = f'{ff_prefix}SOCKET0__IMH{imh}__ULA__ULA_UIO{uio}__ULA_MC_{suffix}'

		elif ptype == 'ula_d2dio':
			# ULA D2D IMH pattern: SOCKET0__IMH{n}__D2D_STACK__D2D_STACK_{n}__UXI_{n}__ULA_MC_AD/MS
			if suffix in ['ADDR', 'AD']:
				pattern = f'{ff_prefix}SOCKET0__IMH{imh}__D2D_STACK__D2D_STACK_{stack}__UXI_{uxi}__ULA_MC_AD'
			elif suffix in ['MISC', 'MS']:
				pattern = f'{ff_prefix}SOCKET0__IMH{imh}__D2D_STACK__D2D_STACK_{stack}__UXI_{uxi}__ULA_MC_MISC'
			else:
				pattern = f'{ff_prefix}SOCKET0__IMH{imh}__D2D_STACK__D2D_STACK_{stack}__UXI_{uxi}__ULA_MC_{suffix}'

		elif ptype == 'ula_d2dcbb':
			# ULA D2D CBB pattern: SOCKET0__CBB{n}__BASE__D2D_STACK_{n}__ULA_{n}__ULA__ULA_MC_AD/MS
			if suffix in ['ADDR', 'AD']:
				pattern = f'{ff_prefix}SOCKET0__CBB{cbb}__BASE__D2D_STACK_{stack}__ULA_{ula}__ULA__ULA_MC_AD'
			elif suffix in ['MISC', 'MS']:
				pattern = f'{ff_prefix}SOCKET0__CBB{cbb}__BASE__D2D_STACK_{stack}__ULA_{ula}__ULA__ULA_MC_MISC'
			else:
				pattern = f'{ff_prefix}SOCKET0__CBB{cbb}__BASE__D2D_STACK_{stack}__ULA_{ula}__ULA__ULA_MC_{suffix}'

		elif ptype == 'iocache':
			# IOCACHE pattern: SOCKET0__IMH{n}__SCF__SCA__IOCACHE{n}__UTIL__MCI_ADDR/MISC
			pattern = f'{ff_prefix}SOCKET0__IMH{imh}__SCF__SCA__IOCACHE{iocache}__UTIL__MCI_{suffix}'

		else:
			pattern = ''

		return pattern

	def mem_lookup_pattern(self, imh='', ha='', hsf='', mc='', subch='', sca='', suffix='ADDR', ptype='ha', ff_prefix=''):
		"""
		Build register path patterns for DMR Memory MCA ADDR/MISC lookup

		Args:
			imh: IMH number (string)
			ha: HA number (string)
			hsf: HSF number (string)
			mc: MC number (string)
			subch: Subchannel number (string)
			sca: SCA number (string)
			suffix: 'ADDR' or 'MISC'
			ptype: Pattern type
			ff_prefix: FailFlow prefix to prepend to pattern (e.g. 'FF_VBUMP_100_' or 'DPMB_')

		Pattern types:
			- ha: SOCKET0__IMH{n}__SCF__HAMVF__HA_{n}__MCI_{ADDR/MISC}
			- hsf: SOCKET0__IMH{n}__SCF__HAMVF__HSF_{n}__UTIL__MCI_{ADDR/MISC}
			- subchn: SOCKET0__IMH{n}__MEMSS__MC{n}__SUBCH{n}__MCDATA__IMC0_MC{8_ADDR or _MISC}
			- mse: SOCKET0__IMH{n}__MEMSS__MC{n}__SUBCH{n}__MSE__MSE_MCI_{ADDR/MISC}
			- sca: SOCKET0__IMH{n}__SCF__SCA__SCA{n}__UTIL__MC_{ADDR/MISC}
		"""
		if ptype == 'ha':
			# HA pattern: SOCKET0__IMH{n}__SCF__HAMVF__HA_{n}__MCI_ADDR/MISC
			pattern = f'{ff_prefix}SOCKET0__IMH{imh}__SCF__HAMVF__HA_{ha}__MCI_{suffix}'

		elif ptype == 'hsf':
			# HSF pattern: SOCKET0__IMH{n}__SCF__HAMVF__HSF_{n}__UTIL__MCI_ADDR/MISC
			pattern = f'{ff_prefix}SOCKET0__IMH{imh}__SCF__HAMVF__HSF_{hsf}__UTIL__MCI_{suffix}'

		elif ptype == 'subchn':
			# SUBCHN pattern: SOCKET0__IMH{n}__MEMSS__MC{n}__SUBCH{n}__MCDATA__IMC0_MC{8_ADDR or _MISC}
			# Special case: ADDR uses IMC0_MC8_ADDR, MISC uses IMC0_MC_MISC
			if suffix == 'ADDR':
				pattern = f'{ff_prefix}SOCKET0__IMH{imh}__MEMSS__MC{mc}__SUBCH{subch}__MCDATA__IMC0_MC8_ADDR'
			else:
				pattern = f'{ff_prefix}SOCKET0__IMH{imh}__MEMSS__MC{mc}__SUBCH{subch}__MCDATA__IMC0_MC_{suffix}'

		elif ptype == 'mse':
			# MSE pattern: SOCKET0__IMH{n}__MEMSS__MC{n}__SUBCH{n}__MSE__MSE_MCI_ADDR/MISC
			pattern = f'{ff_prefix}SOCKET0__IMH{imh}__MEMSS__MC{mc}__SUBCH{subch}__MSE__MSE_MCI_{suffix}'

		elif ptype == 'sca':
			# SCA pattern: SOCKET0__IMH{n}__SCF__SCA__SCA{n}__UTIL__MC_ADDR/MISC
			pattern = f'{ff_prefix}SOCKET0__IMH{imh}__SCF__SCA__SCA{sca}__UTIL__MC_{suffix}'

		else:
			pattern = ''

		return pattern

	# XLOOKUP equivalent in pandas
	def xlookup(self, lookup_array, testname, LotsSeqKey, UnitTestingSeqKey, if_not_found=""):
		if lookup_array.empty:
			return if_not_found
		try:
			result = lookup_array[(lookup_array['TestName'].str.contains(testname)) &
			                       (lookup_array['LotsSeqKey'] == LotsSeqKey) &
			                       (lookup_array['UnitTestingSeqKey'] == UnitTestingSeqKey)]
			lutvalue = result['TestValue'].iloc[0] if not result.empty else if_not_found
		except:
			print(f' -- Error looking for {testname}: Nothing found in MCA Data')
			lutvalue = if_not_found
		return lutvalue

	def ccf(self):
		"""
		CCF (Caching/Coherency Fabric) MCA decoder - Bank 6
		DMR uses CCF which contains LLC + CHA functionality (32 merged CBO instances across 4 ENVs)
		Pattern: SOCKET0__CBB0__BASE__I_CCF_ENV{0-3}__CBREGS_ALL{00-77}__MC_STATUS

		Note: In DMR, LLC is part of CCF (Bank 6), not SCA (Bank 14)
		SCA is a separate IO-specific caching agent for UIO devices

		Output columns match GNR CHA decoder format (only available fields):
		Opcode, TorID (from MC_MISC)
		Way, DataWay, AddrMode, LPID, ModuleID (DMR-specific from MC_MISC)

		Note: Unavailable fields NOT included in output:
		      - Orig Req (not separate from Opcode in DMR)
		      - cachestate, TorFSM (not in DMR MC_MISC register)
		      - SrcID, ISMQ, Attribute, Result, Local Port (no MC_MISC3 register)
		"""
		mcdata = self.data
		# Only include columns for fields that are available in DMR CCF
		columns = ['VisualID', 'Run', 'Operation', 'CCF_MC', 'CBB', 'ENV', 'Instance',
		           'MC_STATUS', 'MC DECODE', 'MC_ADDR', 'MC_MISC', 'MC_MISC3',
		           'Opcode', 'TorID',
		           'Way', 'DataWay', 'AddrMode', 'LPID', 'ModuleID']

		decodelistmc = ['MC DECODE']
		# Map DMR CCF fields to GNR CHA equivalents (only available fields from MC_MISC register)
		decodelistmisc = ['Opcode', 'TorID',
		                  'Way', 'DataWay', 'AddrMode', 'LPID', 'ModuleID']
		# DMR doesn't have MC_MISC3, so no fields from this list
		decodelistmisc3 = []

		data_dict = {k:[] for k in columns}

		total_processed = 0

		for visual_id in mcdata['VisualId'].unique():
			# Split Data into required elements - look for I_CCF_ENV pattern
			subset = mcdata[(mcdata['VisualId'] == visual_id) &
			                (mcdata['TestName'].str.contains('I_CCF_ENV'))]

			# Further split into required lookup registers for each VID
			mc_filtered = self.extract_value(subset, 'TestName', 'MC_STATUS')
			addr_filtered = self.extract_value(subset, 'TestName', 'MC_ADDR')
			misc_filtered = self.extract_value(subset, 'TestName', r'MC_MISC(?![0-9])')
			misc3_filtered = self.extract_value(subset, 'TestName', r'MC_MISC3')

			# If no MCA is found move to the next VID
			try:
				if mc_filtered.empty:
					print(f' -- No MCA data found for CCF in VID: {visual_id}')
					continue
			except:
				print(f' -- No MCA data found for CCF in VID: {visual_id}')
				continue

			print(f' -- CCF VID {visual_id}: Processing {len(mc_filtered)} STATUS rows')
			total_processed += len(mc_filtered)

			# This will iterate over all the MCAS
			for i, data in mc_filtered.iterrows():
				data_dict['VisualID'] += [visual_id]
				LotsSeqKey = data['LotsSeqKey']
				UnitTestingSeqKey = data['UnitTestingSeqKey']

				# Extract CBB, ENV, and Instance from pattern:
				# SOCKET0__CBB{x}__BASE__I_CCF_ENV{0-3}__CBREGS_ALL{00-77}__MC_STATUS
				cbb_match = re.search(r'CBB(\d+)', data['TestName'])
				env_match = re.search(r'ENV(\d+)', data['TestName'])
				inst_match = re.search(r'CBREGS_ALL(\d+)', data['TestName'])

				cbb = cbb_match.group(1) if cbb_match else '0'
				env = env_match.group(1) if env_match else '0'
				instance = inst_match.group(1) if inst_match else '00'

				operation = data['Operation']

				# Checks for new DMR fail flow prefix in test names (e.g., "FF_", "DMRFF_") to determine if special handling is needed
				test_name = data['TestName']
				ff_type, ff_prefix = self.check_fail_flow_prefix(test_name)

				## Address lookup pattern - use exact CBB, ENV and instance for precise matching
				addr_lut = self.lookup_pattern(cbb=cbb, compute='', module='', location='', operation=operation,
				                                suffix="ADDR", env=env, inst=instance, ptype='ccf', ff_prefix=ff_prefix)
				misc_lut = self.lookup_pattern(cbb=cbb, compute='', module='', location='', operation=operation,
				                                suffix="MISC", env=env, inst=instance, ptype='ccf', ff_prefix=ff_prefix)
				misc3_lut = self.lookup_pattern(cbb=cbb, compute='', module='', location='', operation=operation,
				                                 suffix="MISC3", env=env, inst=instance, ptype='ccf', ff_prefix=ff_prefix)

				## MCA Lookup values
				mc_value = data['TestValue']
				addr_value = self.xlookup(lookup_array=addr_filtered, testname=addr_lut,
				                          LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)
				misc_value = self.xlookup(lookup_array=misc_filtered, testname=misc_lut,
				                          LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)
				misc_value3 = self.xlookup(lookup_array=misc3_filtered, testname=misc3_lut,
				                           LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)

				## Get Run Info
				run = str(LotsSeqKey) + "-" + str(UnitTestingSeqKey)
				data_dict['Run'] += [run]
				data_dict['Operation'] += [f'{operation}_{ff_type}' if ff_type else str(operation)]
				data_dict['CCF_MC'] += [data['TestName']]
				data_dict['CBB'] += [f'CBB{cbb}']
				data_dict['ENV'] += [f'ENV{env}']
				data_dict['Instance'] += [f'INST{instance}']
				data_dict['MC_STATUS'] += [mc_value]
				data_dict['MC_ADDR'] += [addr_value]
				data_dict['MC_MISC'] += [misc_value]
				data_dict['MC_MISC3'] += [misc_value3]

				### MCdecode Data from STATUS register
				for dval in decodelistmc:
					data_dict[dval] += [self.ccf_decoder(value=mc_value, type=dval)]

				### MCdecode Data from MISC register (only available fields)
				for dval in decodelistmisc:
					data_dict[dval] += [self.ccf_decoder(value=misc_value, type=dval)]

		new_df = pd.DataFrame(data_dict)
		print(f' -- CCF Decoder: Total rows processed: {total_processed}, Final DataFrame rows: {len(new_df)}')
		return new_df

	def ccf_decoder(self, value, type):
		"""
		CCF MCA Decode - DMR specific
		Uses GNR cha_params.json as baseline (both are bigcore architectures)

		Output includes only fields available in DMR CCF hardware:
		- Opcode, TorID (from MC_MISC) ✅ Available
		- Way, DataWay, AddrMode, LPID, ModuleID (DMR-specific from MC_MISC) ✅ Available

		Fields NOT included (not available in DMR CCF):
		- Orig Req (DMR doesn't separate Orig Req from Opcode)
		- cachestate, TorFSM (not in DMR MC_MISC register)
		- SrcID, ISMQ, Attribute, Result, Local Port (no MC_MISC3 register in DMR)

		Bit field mapping based on live DMR system (sv.socket0.cbb0.base.i_ccf_env0.cbregs_all77):

		MC_STATUS (bits 63:0):
		  - Bit  63     = val (Valid flag)
		  - Bit  62     = over (Machine check overflow)
		  - Bit  61     = uc (Error uncorrected)
		  - Bit  60     = en (Error enabled)
		  - Bit  59     = miscv (MC_MISC valid)
		  - Bit  58     = addrv (MC_ADDR valid)
		  - Bit  57     = pcc (Processor context corrupt)
		  - Bit  56     = s (Signaling UCR error)
		  - Bit  55     = ar (Action required)
		  - Bits 54:53  = correrrorstatusind (Corrected error status indicator)
		  - Bits 52:38  = corr_err_count (15 bits correctable error count)
		  - Bit  37     = fw_upd (BIOS updated MC Bank)
		  - Bits 36:32  = enh_mca_avail0 (Enhanced MCA available)
		  - Bits 31:16  = model_specific_error_code (MSCOD)
		  - Bits 15:0   = mca_error_code (MCACOD)

		MC_MISC (bits 47:0 - only lower 48 bits used):
		  - Bits 47:40  = torid (TOR entry ID) ✅
		  - Bits 39:31  = opcode (Pipe command / IDI opcode - 9 bits) ✅
		  - Bits 30:26  = moduleid (Core ID / Instance) ✅
		  - Bits 25:23  = lpid (Thread ID/Logical Processor ID) ✅
		  - Bits 22:20  = enh_mca_avail1 (Enhanced MCA - not used for decoding)
		  - Bits 19:15  = dataway (Data way) ✅
		  - Bits 14:9   = way (Tag way) ✅
		  - Bits 8:6    = addrmode (Address mode) ✅
		  - Bits 5:0    = lsb_addr (LSB of address) ✅
		  - Bits 63:48  = enh_mca_avail2 (Enhanced MCA - not used for decoding)

		MC_MISC3: ❌ NOT AVAILABLE in DMR CCF
		  - DMR CCF doesn't have MC_MISC3 register
		  - Fields like SrcID, ISMQ, Attribute, Result, Local Port not available

		Fields NOT in DMR MC_MISC (compared to GNR CHA):
		  - cachestate: ❌ Not present in DMR CCF MC_MISC register
		  - TorFSM: ❌ Not present in DMR CCF MC_MISC register
		"""
		#ccf_json = self.mcadata.cha_data  # Using cha_params.json from GNR for CCF
		ccf_json = self.mcadata.ccf_data if hasattr(self.mcadata, 'ccf_data') else {}
		# Decode configuration for CCF/CHA fields - Based on live DMR system registers
		# Map to GNR CHA equivalent column names where possible
		#
		# DMR MC_MISC available fields (verified from live system):
		#   - torid (47:40), opcode (39:31), moduleid (30:26), lpid (25:23)
		#   - dataway (19:15), way (14:9), addrmode (8:6), lsb_addr (5:0)
		#
		# DMR MC_MISC NOT available (compared to GNR CHA):
		#   - Orig Req (DMR doesn't separate this from Opcode)
		#   - cachestate, TorFSM (these fields don't exist in DMR CCF MC_MISC register)
		# DMR has no MC_MISC3 register, so SrcID, ISMQ, Attribute, Result, Local Port not available
		#
		data = {
			'MC DECODE': {'table': 'MSCOD', 'min': 16, 'max': 31},          # Status - MSCOD field

			# GNR CHA equivalent fields AVAILABLE in DMR MC_MISC:
			'Opcode': {'table': 'TOR_OPCODES_BY_VAL', 'min': 31, 'max': 39},       # Misc - IDI opcode (9 bits) - combines Orig Req + Opcode
			'TorID': {'table': None, 'min': 40, 'max': 47},                        # Misc - TOR entry ID

			# DMR CCF-specific fields available in MC_MISC:
			'ModuleID': {'table': None, 'min': 26, 'max': 30},                     # Misc - moduleid (Core ID)
			'Way': {'table': None, 'min': 9, 'max': 14},                           # Misc - Tag way
			'DataWay': {'table': None, 'min': 15, 'max': 19},                      # Misc - Data way
			'AddrMode': {'table': None, 'min': 6, 'max': 8},                       # Misc - Address mode
			'LPID': {'table': None, 'min': 23, 'max': 25},                         # Misc - Thread/LP ID
		}

		table = data[type]['table']
		mcmin = data[type]['min']
		mcmax = data[type]['max']

		# If nothing is found return empty string
		if value == '':
			return value

		extractedvalue = extract_bits(hex_value=value, min_bit=mcmin, max_bit=mcmax)

		if table is not None:
			mclist = ccf_json.get(table, {})
			keyvalue = str(extractedvalue)
			mc_value = mclist.get(keyvalue, None)  # Get decoded value or None if not found

			# If not found in table, return the raw extracted value
			if mc_value is None:
				if type == 'MC DECODE':

					# For MC DECODE, show both MSCOD and MCACOD when not in table
					mcacod = extract_bits(hex_value=value, min_bit=0, max_bit=15)
					mscod = extract_bits(hex_value=value, min_bit=16, max_bit=31)
					mc_value = f"MSCOD={mscod}, MCACOD={mcacod}"
				else:
					# For other fields, show the raw extracted value
					mc_value = extractedvalue
			else:
				mc_value = f"MSCOD={mc_value}, MCACOD={mcacod}"
		else:
			mc_value = extractedvalue

		return mc_value

	def core(self):
		"""
		Core MCA decoder - Banks 0-2 (IFU, DCU, DTLB)
		BigCore (PNC) with one thread per core
		"""
		mcdata = self.data
		columns = ['VisualID', 'Run', 'Operation', 'Core_MC', 'CBB', 'Compute', 'Module', 'Core',
		           'Bank', 'MC_STATUS', 'MC DECODE', 'MC_ADDR', 'MC_MISC']

		data_dict = {k:[] for k in columns}

		# Core banks: IFU (0), DCU (1), DTLB (2), ML2 (3)
		core_banks = {'IFU': ('MC0', 'core_ifu', 0),
		              'DCU': ('MC1', 'core_dcu', 1),
		              'DTLB': ('MC2', 'core_dtlb', 2),
		              'ML2': ('MC3', 'core_ml2', 3)}

		for visual_id in mcdata['VisualId'].unique():
			for bank_name, (mc_num, ptype, bank_id) in core_banks.items():
				subset = mcdata[(mcdata['VisualId'] == visual_id) &
				                (mcdata['TestName'].str.contains(f'{bank_name}_CR_{mc_num}'))]

				mc_filtered = self.extract_value(subset, 'TestName', f'{mc_num}_STATUS')
				addr_filtered = self.extract_value(subset, 'TestName', f'{mc_num}_ADDR')
				misc_filtered = self.extract_value(subset, 'TestName', f'{mc_num}_MISC')

				if mc_filtered.empty:
					continue

				for i, data in mc_filtered.iterrows():
					data_dict['VisualID'] += [visual_id]
					LotsSeqKey = data['LotsSeqKey']
					UnitTestingSeqKey = data['UnitTestingSeqKey']

					# Extract CBB, COMPUTE, MODULE, and CORE numbers
					# Pattern: SOCKET0__CBB{x}__COMPUTE{y}__MODULE{z}__CORE{w}__{BANK}_CR_MC{n}_STATUS
					cbb_match = re.search(r'CBB(\d+)', data['TestName'])
					compute_match = re.search(r'COMPUTE(\d+)', data['TestName'])
					module_match = re.search(r'MODULE(\d+)', data['TestName'])
					core_match = re.search(r'CORE(\d+)', data['TestName'])

					cbb = cbb_match.group(1) if cbb_match else '0'
					compute = compute_match.group(1) if compute_match else '0'
					module = module_match.group(1) if module_match else '0'
					core = core_match.group(1) if core_match else '0'

					operation = data['Operation']
					test_name = data['TestName']

					# Checks for new DMR fail flow prefix in test names (e.g., "FF_", "DMRFF_") to determine if special handling is needed
					ff_type, ff_prefix = self.check_fail_flow_prefix(test_name)

					# Use exact CBB, COMPUTE, MODULE, and CORE for precise matching
					addr_lut = self.lookup_pattern(cbb=cbb, compute=compute, module=module, location=core,
					                                operation=operation, suffix="ADDR", ptype=ptype, ff_prefix=ff_prefix)
					misc_lut = self.lookup_pattern(cbb=cbb, compute=compute, module=module, location=core,
					                                operation=operation, suffix="MISC", ptype=ptype, ff_prefix=ff_prefix)

					mc_value = data['TestValue']
					addr_value = self.xlookup(lookup_array=addr_filtered, testname=addr_lut,
					                          LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)
					misc_value = self.xlookup(lookup_array=misc_filtered, testname=misc_lut,
					                          LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)

					run = str(LotsSeqKey) + "-" + str(UnitTestingSeqKey)
					data_dict['Run'] += [run]
					data_dict['Operation'] += [f'{operation}_{ff_type}' if ff_type else str(operation)]
					data_dict['Core_MC'] += [data['TestName']]
					data_dict['CBB'] += [f'CBB{cbb}']
					data_dict['Compute'] += [f'COMPUTE{compute}']
					data_dict['Core'] += [f'CORE{core}']
					data_dict['Module'] += [f'MODULE{module}']
					data_dict['Bank'] += [f'{bank_name} (Bank {bank_id})']
					data_dict['MC_STATUS'] += [mc_value]
					data_dict['MC_ADDR'] += [addr_value]
					data_dict['MC_MISC'] += [misc_value]

					data_dict['MC DECODE'] += [self.core_decoder(value=mc_value, bank=bank_name)]

		new_df = pd.DataFrame(data_dict)
		return new_df

	def core_decoder(self, value, bank):
		"""
		Core bank MCA decoder
		Uses GNR core_params.json as baseline (both are bigcore architectures)

		Bit field mapping based on live DMR system:

		IFU (Bank 0):
		  - Bits 15:0  = mcacod
		  - Bits 31:16 = mscod (16 bits)
		  - Bits 51:38 = corrected_err_cnt (14 bits)

		DCU (Bank 1): ⚠️ SPECIAL CASE - Extended MSCOD!
		  - Bits 15:0  = mcacod
		  - Bits 37:16 = mscod (22 bits!) ← Non-standard!
		  - Bits 52:38 = cecnt (15 bits)

		DTLB (Bank 2):
		  - Bits 15:0  = mcacod
		  - Bits 31:16 = mscod (16 bits)
		  - Bits 52:38 = cor_err_cnt (15 bits)

		ML2 (Bank 3):
		  - Bits 15:0  = mcacod
		  - Bits 31:16 = mscod (16 bits)
		  - Bits 52:38 = cec (15 bits)
		"""
		core_json = self.mcadata.core_data  # Using core_params.json from GNR

		if value == '':
			return value

		# Extract MCACOD from bits 15:0 (standard across all banks)
		mcacod = extract_bits(hex_value=value, min_bit=0, max_bit=15)

		# Extract MSCOD - DCU has extended 22-bit MSCOD field!
		if bank == 'DCU':
			mscod = extract_bits(hex_value=value, min_bit=16, max_bit=37)  # 22 bits for DCU
		else:
			mscod = extract_bits(hex_value=value, min_bit=16, max_bit=31)  # 16 bits for IFU, DTLB, ML2

		# Look up in core_params.json (GNR structure)
		bank_data = core_json.get(bank, {})
		mscod_data = bank_data.get('MSCOD', {})

		# Try direct lookup first (for simple MSCOD values)
		if str(mscod) in mscod_data:
			mscod_entry = mscod_data[str(mscod)]
			mcacod_data = mscod_entry.get('MCACOD', {})

			if str(mcacod) in mcacod_data:
				mcacod_entry = mcacod_data[str(mcacod)]
				name = mcacod_entry.get('Name', mcacod_entry.get('Name0', 'N/A'))
				desc = mcacod_entry.get('Description', mcacod_entry.get('Description0', ''))
				return f"{name}: {desc}" if desc else name

		# Try hex pattern matching for MSCOD (e.g., "0x1?10", "0x1?00")
		for mscod_key in mscod_data.keys():
			if 'x' in mscod_key.lower() and '?' in mscod_key:
				# Convert pattern to regex (e.g., "0x1?10" -> match 0x1010, 0x1110, etc.)
				pattern = mscod_key.replace('0x', '').replace('0X', '').replace('?', '.')
				mscod_hex = hex(mscod)[2:].upper().zfill(4)
				if re.match(pattern.upper(), mscod_hex):
					mscod_entry = mscod_data[mscod_key]
					mcacod_data = mscod_entry.get('MCACOD', {})
					if str(mcacod) in mcacod_data:
						mcacod_entry = mcacod_data[str(mcacod)]
						name = mcacod_entry.get('Name', mcacod_entry.get('Name0', 'N/A'))
						desc = mcacod_entry.get('Description', mcacod_entry.get('Description0', ''))
						return f"{name}: {desc}" if desc else name

		# If not found, return raw values
		return f"MSCOD={mscod}, MCACOD={mcacod}"

	def io(self):
		"""
		IO MCA decoder for DMR - Includes ULA instances and IO caches

		IO Components:
		- ula_uios: ULA for UIO devices (Bank 18)
		  Pattern: SOCKET0__IMH{0-1}__ULA__ULA_UIO{0-n}__ULA_MC_ST
		  Instance: ULA_UIO{n}

		- ula_d2dio: ULA for D2D IMH side (Bank 15)
		  Pattern: SOCKET0__IMH{0-1}__D2D_STACK__D2D_STACK_{0-5}__UXI_{0-1}__ULA_MC_ST
		  Instance: IMH{n}_UXI{n}_STACK{n}

		- ula_d2dcbb: ULA for D2D CBB side (Bank 7)
		  Pattern: SOCKET0__CBB{0-n}__BASE__D2D_STACK_{0-1}__ULA_{0-1}__ULA__ULA_MC_ST
		  Instance: CBB{n}_STACK{n}_ULA{n}

		- iocaches: IO Cache instances (Bank 17)
		  Pattern: SOCKET0__IMH{0-1}__SCF__SCA__IOCACHE{0-n}__UTIL__MCI_STATUS
		  Instance: IOCACHE{n}
		"""
		mcdata = self.data
		columns = ['VisualID', 'Run', 'Operation', 'Type', 'IO_MC', 'IMH_CBB', 'Instance',
		           'MC_STATUS', 'MCACOD', 'MC_DECODE', 'MC_ADDR', 'MC_MISC']

		data_dict = {k:[] for k in columns}

		# IO subsystem patterns
		io_patterns = ['ULA__ULA_UIO', 'D2D_STACK__D2D_STACK', 'D2D_STACK_', 'IOCACHE']

		for visual_id in mcdata['VisualId'].unique():
			# Filter for IO-related MCAs
			io_filtered = pd.DataFrame()
			for pattern in io_patterns:
				pattern_data = self.extract_value(mcdata[mcdata['VisualId'] == visual_id], 'TestName', pattern)
				if not pattern_data.empty:
					io_filtered = pd.concat([io_filtered, pattern_data], ignore_index=True)

			# Check if io_filtered has data and required column before proceeding
			if io_filtered.empty or 'TestName' not in io_filtered.columns:
				print(f' -- No IO MCA data found in VID: {visual_id}')
				continue

			# Further filter for STATUS registers
			mc_filtered = self.extract_value(io_filtered, 'TestName', '_STATUS|_MC_STATUS|_MCI_STATUS|_MC_ST')

			if mc_filtered.empty:
				print(f' -- No IO MCA STATUS registers found in VID: {visual_id}')
				continue

			# Iterate over all IO MCAs
			for i, data in mc_filtered.iterrows():
				data_dict['VisualID'] += [visual_id]
				LotsSeqKey = data['LotsSeqKey']
				UnitTestingSeqKey = data['UnitTestingSeqKey']
				operation = data['Operation']
				test_name = data['TestName']
				mc_value = data['TestValue']

				# Checks for new DMR fail flow prefix in test names (e.g., "FF_", "DMRFF_") to determine if special handling is needed
				ff_type, ff_prefix = self.check_fail_flow_prefix(test_name)

				# Determine IO type and extract instance information
				io_type = ''
				instance = ''
				imh_cbb = ''

				if 'ULA__ULA_UIO' in test_name:
					# ula_uios: SOCKET0__IMH{n}__ULA__ULA_UIO{n}__ULA_MC_ST
					io_type = 'ULA_UIOS'
					imh_match = re.search(r'IMH(\d+)', test_name)
					uio_match = re.search(r'ULA_UIO(\d+)', test_name)
					if imh_match and uio_match:
						imh_cbb = f'IMH{imh_match.group(1)}'
						instance = f'ULA_UIO{uio_match.group(1)}'

				elif 'IMH' in test_name and 'D2D_STACK__D2D_STACK' in test_name:
					# ula_d2dio: SOCKET0__IMH{n}__D2D_STACK__D2D_STACK_{n}__UXI_{n}__ULA_MC_ST
					io_type = 'ULA_D2DIO'
					imh_match = re.search(r'IMH(\d+)', test_name)
					stack_match = re.search(r'D2D_STACK__D2D_STACK_(\d+)', test_name)
					uxi_match = re.search(r'UXI_(\d+)', test_name)
					if imh_match:
						imh_num = imh_match.group(1)
						imh_cbb = f'IMH{imh_num}'
						stack_num = stack_match.group(1) if stack_match else '0'
						uxi_num = uxi_match.group(1) if uxi_match else '0'
						instance = f'IMH{imh_num}_UXI{uxi_num}_STACK{stack_num}'

				elif 'CBB' in test_name and 'D2D_STACK_' in test_name:
					# ula_d2dcbb: SOCKET0__CBB{n}__BASE__D2D_STACK_{n}__ULA_{n}__ULA__ULA_MC_ST
					io_type = 'ULA_D2DCBB'
					cbb_match = re.search(r'CBB(\d+)', test_name)
					stack_match = re.search(r'D2D_STACK_(\d+)', test_name)
					ula_match = re.search(r'__ULA_(\d+)__ULA', test_name)
					if cbb_match:
						cbb_num = cbb_match.group(1)
						imh_cbb = f'CBB{cbb_num}'
						stack_num = stack_match.group(1) if stack_match else '0'
						ula_num = ula_match.group(1) if ula_match else '0'
						instance = f'CBB{cbb_num}_STACK{stack_num}_ULA{ula_num}'

				elif 'IOCACHE' in test_name:
					# iocaches: SOCKET0__IMH{n}__SCF__SCA__IOCACHE{n}__UTIL__MCI_STATUS
					io_type = 'IOCACHE'
					imh_match = re.search(r'IMH(\d+)', test_name)
					cache_match = re.search(r'IOCACHE(\d+)', test_name)
					if imh_match and cache_match:
						imh_cbb = f'IMH{imh_match.group(1)}'
						instance = f'IOCACHE{cache_match.group(1)}'

				# Extract MCACOD (bits 15:0) from MC_STATUS
				mcacod = extract_bits(hex_value=mc_value, min_bit=0, max_bit=15)

				# Decode MSCOD based on IO type
				if io_type in ['ULA_UIOS', 'ULA_D2DIO', 'ULA_D2DCBB']:
					mc_decode = self.io_ula_decoder(value=mc_value)
				elif io_type == 'IOCACHE':
					mc_decode = self.io_cache_decoder(value=mc_value)
				else:
					mscod = extract_bits(hex_value=mc_value, min_bit=16, max_bit=31)
					mc_decode = f"MSCOD={mscod}"

				# Look up ADDR and MISC registers using proper lookup patterns
				addr_value = ''
				misc_value = ''
				addr_pattern = ''
				misc_pattern = ''

				# Build lookup patterns based on IO type using io_lookup_pattern method
				if io_type == 'ULA_UIOS':
					imh_match = re.search(r'IMH(\d+)', test_name)
					uio_match = re.search(r'ULA_UIO(\d+)', test_name)
					if imh_match and uio_match:
						imh_num = imh_match.group(1)
						uio_num = uio_match.group(1)
						addr_pattern = self.io_lookup_pattern(imh=imh_num, uio=uio_num, suffix='AD', ptype='ula_uios', ff_prefix=ff_prefix)
						misc_pattern = self.io_lookup_pattern(imh=imh_num, uio=uio_num, suffix='MS', ptype='ula_uios', ff_prefix=ff_prefix)

				elif io_type == 'ULA_D2DIO':
					imh_match = re.search(r'IMH(\d+)', test_name)
					stack_match = re.search(r'D2D_STACK__D2D_STACK_(\d+)', test_name)
					uxi_match = re.search(r'UXI_(\d+)', test_name)
					if imh_match and stack_match and uxi_match:
						imh_num = imh_match.group(1)
						stack_num = stack_match.group(1)
						uxi_num = uxi_match.group(1)
						addr_pattern = self.io_lookup_pattern(imh=imh_num, stack=stack_num, uxi=uxi_num, suffix='AD', ptype='ula_d2dio', ff_prefix=ff_prefix)
						misc_pattern = self.io_lookup_pattern(imh=imh_num, stack=stack_num, uxi=uxi_num, suffix='MS', ptype='ula_d2dio', ff_prefix=ff_prefix)

				elif io_type == 'ULA_D2DCBB':
					cbb_match = re.search(r'CBB(\d+)', test_name)
					stack_match = re.search(r'D2D_STACK_(\d+)', test_name)
					ula_match = re.search(r'__ULA_(\d+)__ULA', test_name)
					if cbb_match and stack_match and ula_match:
						cbb_num = cbb_match.group(1)
						stack_num = stack_match.group(1)
						ula_num = ula_match.group(1)
						addr_pattern = self.io_lookup_pattern(cbb=cbb_num, stack=stack_num, ula=ula_num, suffix='AD', ptype='ula_d2dcbb', ff_prefix=ff_prefix)
						misc_pattern = self.io_lookup_pattern(cbb=cbb_num, stack=stack_num, ula=ula_num, suffix='MS', ptype='ula_d2dcbb', ff_prefix=ff_prefix)

				elif io_type == 'IOCACHE':
					imh_match = re.search(r'IMH(\d+)', test_name)
					cache_match = re.search(r'IOCACHE(\d+)', test_name)
					if imh_match and cache_match:
						imh_num = imh_match.group(1)
						cache_num = cache_match.group(1)
						addr_pattern = self.io_lookup_pattern(imh=imh_num, iocache=cache_num, suffix='ADDR', ptype='iocache', ff_prefix=ff_prefix)
						misc_pattern = self.io_lookup_pattern(imh=imh_num, iocache=cache_num, suffix='MISC', ptype='iocache', ff_prefix=ff_prefix)

				else:
					# Fallback to simple replacement
					addr_pattern = test_name.replace('_MC_ST', '_MC_AD').replace('_MCI_STATUS', '_MCI_ADDR').replace('_MC_STATUS', '_MC_ADDR')
					misc_pattern = test_name.replace('_MC_ST', '_MC_MS').replace('_MCI_STATUS', '_MCI_MISC').replace('_MC_STATUS', '_MC_MISC')

				addr_value = self.xlookup(lookup_array=io_filtered, testname=addr_pattern,
				                         LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)
				misc_value = self.xlookup(lookup_array=io_filtered, testname=misc_pattern,
				                         LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)

				# Get Run Info
				run = str(LotsSeqKey) + "-" + str(UnitTestingSeqKey)
				data_dict['Run'] += [run]
				data_dict['Operation'] += [f'{operation}_{ff_type}' if ff_type else str(operation)]
				data_dict['Type'] += [io_type]
				data_dict['IO_MC'] += [test_name]
				data_dict['IMH_CBB'] += [imh_cbb]
				data_dict['Instance'] += [instance]
				data_dict['MCACOD'] += [hex(mcacod)]
				data_dict['MC_DECODE'] += [mc_decode]
				data_dict['MC_STATUS'] += [mc_value]
				data_dict['MC_ADDR'] += [addr_value]
				data_dict['MC_MISC'] += [misc_value]

		new_df = pd.DataFrame(data_dict)
		return new_df

	def io_ula_decoder(self, value):
		"""
		ULA (UXI Link Agent) MCA decoder for DMR
		Uses ula_params.json for MSCOD decoding
		"""
		if value == '' or value is None:
			return ''

		try:
			mscod = extract_bits(hex_value=value, min_bit=16, max_bit=31)

			# Use ULA parameters from JSON
			ula_json = self.mcadata.ula_data if hasattr(self.mcadata, 'ula_data') else {}

			if 'ULA_MSCOD' in ula_json:
				mscod_str = str(mscod)
				if mscod_str in ula_json['ULA_MSCOD']:
					return f"{ula_json['ULA_MSCOD'][mscod_str]} (MSCOD={mscod})"

			return f"MSCOD={mscod}"

		except Exception as e:
			return f"Decode error: {str(e)}"

	def io_cache_decoder(self, value):
		"""
		IO Cache MCA decoder for DMR
		Uses cache_params.json for MSCOD decoding
		"""
		if value == '' or value is None:
			return ''

		try:
			mscod = extract_bits(hex_value=value, min_bit=16, max_bit=31)

			# Use cache parameters from JSON
			cache_json = self.mcadata.cache_data if hasattr(self.mcadata, 'cache_data') else {}

			if 'MSCOD_BY_VAL' in cache_json:
				mscod_str = str(mscod)
				if mscod_str in cache_json['MSCOD_BY_VAL']:
					return f"{cache_json['MSCOD_BY_VAL'][mscod_str]} (MSCOD={mscod})"

			# Fallback to LLC data if cache_params.json not available
			llc_json = self.mcadata.llc_data
			mscod_table = llc_json.get('MSCOD_BY_VAL', {})

			if str(mscod) in mscod_table:
				return f"{mscod_table[str(mscod)]} (MSCOD={mscod})"
			else:
				return f"MSCOD={mscod}"

		except Exception as e:
			return f"Decode error: {str(e)}"

	def mem(self):
		"""
		Memory MCA decoder for DMR - Includes HA, HSF, SUBCHN, MSE, SCA

		Memory Components:
		- ha: Home Agent (Bank 12)
		  Pattern: SOCKET0__IMH{0-1}__SCF__HAMVF__HA_{0-15}__MCI_STATUS
		  Instance: HAMVF_HA{n}

		- hsf: Home Snoop Filter (Bank 13)
		  Pattern: SOCKET0__IMH{0-1}__SCF__HAMVF__HSF_{0-15}__UTIL__MCI_STATUS
		  Instance: HSF{n}

		- subchn: Memory Controller Subchannels (Banks 19-26)
		  Pattern: SOCKET0__IMH{0-1}__MEMSS__MC{0-7}__SUBCH{0-1}__MCDATA__IMC0_MC_STATUS
		  Instance: HA{n}

		- mse: Memory Security Engine (Bank 16)
		  Pattern: SOCKET0__IMH{0-1}__MEMSS__MC{0-7}__SUBCH{0-1}__MSE__MSE_MCI_STATUS
		  Instance: MSE

		- sca: Scalable Caching Agent (Bank 14)
		  Pattern: SOCKET0__IMH{0-1}__SCF__SCA__SCA{0-n}__UTIL__MC_STATUS
		  Instance: SCA{n}
		"""
		mcdata = self.data
		columns = ['VisualID', 'Run', 'Operation', 'Type', 'MEM_MC', 'IMH', 'Instance',
		           'MC_STATUS', 'MCACOD', 'MC_DECODE', 'MC_ADDR', 'MC_MISC']

		data_dict = {k:[] for k in columns}

		# Memory subsystem patterns
		mem_patterns = ['HAMVF__HA_', 'HAMVF__HSF_', 'MEMSS__MC', 'MSE__MSE_MCI', 'SCF__SCA__SCA']

		for visual_id in mcdata['VisualId'].unique():
			# Filter for memory-related MCAs
			mem_filtered = pd.DataFrame()
			for pattern in mem_patterns:
				pattern_data = self.extract_value(mcdata[mcdata['VisualId'] == visual_id], 'TestName', pattern)
				if not pattern_data.empty:
					mem_filtered = pd.concat([mem_filtered, pattern_data], ignore_index=True)

			# Check if mem_filtered has data and required column before proceeding
			if mem_filtered.empty or 'TestName' not in mem_filtered.columns:
				print(f' -- No Memory MCA data found in VID: {visual_id}')
				continue

			# Further filter for STATUS registers
			mc_filtered = self.extract_value(mem_filtered, 'TestName', '_STATUS|_MC_STATUS|_MCI_STATUS')

			if mc_filtered.empty:
				print(f' -- No Memory MCA STATUS registers found in VID: {visual_id}')
				continue

			# Iterate over all Memory MCAs
			for i, data in mc_filtered.iterrows():
				data_dict['VisualID'] += [visual_id]
				LotsSeqKey = data['LotsSeqKey']
				UnitTestingSeqKey = data['UnitTestingSeqKey']
				operation = data['Operation']
				test_name = data['TestName']
				mc_value = data['TestValue']

				# Checks for new DMR fail flow prefix in test names (e.g., "FF_", "DMRFF_") to determine if special handling is needed
				ff_type, ff_prefix = self.check_fail_flow_prefix(test_name)

				# Determine memory type and extract instance information
				mem_type = ''
				instance = ''
				imh = ''

				if 'HAMVF__HA_' in test_name and 'HSF' not in test_name:
					# ha: SOCKET0__IMH{n}__SCF__HAMVF__HA_{n}__MCI_STATUS
					mem_type = 'HA'
					imh_match = re.search(r'IMH(\d+)', test_name)
					ha_match = re.search(r'HAMVF__HA_(\d+)', test_name)
					if imh_match and ha_match:
						imh = f'IMH{imh_match.group(1)}'
						instance = f'HAMVF_HA{ha_match.group(1)}'

				elif 'HAMVF__HSF_' in test_name:
					# hsf: SOCKET0__IMH{n}__SCF__HAMVF__HSF_{n}__UTIL__MCI_STATUS
					mem_type = 'HSF'
					imh_match = re.search(r'IMH(\d+)', test_name)
					hsf_match = re.search(r'HAMVF__HSF_(\d+)', test_name)
					if imh_match and hsf_match:
						imh = f'IMH{imh_match.group(1)}'
						instance = f'HSF{hsf_match.group(1)}'

				elif 'MEMSS__MC' in test_name and 'MSE' not in test_name:
					# subchn: SOCKET0__IMH{n}__MEMSS__MC{n}__SUBCH{n}__MCDATA__IMC0_MC_STATUS
					mem_type = 'SUBCHN'
					imh_match = re.search(r'IMH(\d+)', test_name)
					mc_match = re.search(r'MEMSS__MC(\d+)', test_name)
					subch_match = re.search(r'SUBCH(\d+)', test_name)
					if imh_match and mc_match:
						imh = f'IMH{imh_match.group(1)}'
						mc_num = mc_match.group(1)
						subch_num = subch_match.group(1) if subch_match else '0'
						instance = f'HA{mc_num}'  # Using HA{n} as instance per spec

				elif 'MSE__MSE_MCI' in test_name:
					# mse: SOCKET0__IMH{n}__MEMSS__MC{n}__SUBCH{n}__MSE__MSE_MCI_STATUS
					mem_type = 'MSE'
					imh_match = re.search(r'IMH(\d+)', test_name)
					if imh_match:
						imh = f'IMH{imh_match.group(1)}'
						instance = 'MSE'

				elif 'SCF__SCA__SCA' in test_name:
					# sca: SOCKET0__IMH{n}__SCF__SCA__SCA{n}__UTIL__MC_STATUS
					mem_type = 'SCA'
					imh_match = re.search(r'IMH(\d+)', test_name)
					sca_match = re.search(r'__SCA__SCA(\d+)__', test_name)
					if imh_match and sca_match:
						imh = f'IMH{imh_match.group(1)}'
						instance = f'SCA{sca_match.group(1)}'

				# Extract MCACOD (bits 15:0) from MC_STATUS
				mcacod = extract_bits(hex_value=mc_value, min_bit=0, max_bit=15)

				# Decode MSCOD based on memory type
				mc_decode = self.mem_decoder(value=mc_value, mem_type=mem_type)

				# Look up ADDR and MISC registers using proper lookup patterns
				addr_value = ''
				misc_value = ''
				addr_pattern = ''
				misc_pattern = ''

				# Build lookup patterns based on memory type using mem_lookup_pattern method
				if mem_type == 'HA':
					imh_match = re.search(r'IMH(\d+)', test_name)
					ha_match = re.search(r'HAMVF__HA_(\d+)', test_name)
					if imh_match and ha_match:
						imh_num = imh_match.group(1)
						ha_num = ha_match.group(1)
						addr_pattern = self.mem_lookup_pattern(imh=imh_num, ha=ha_num, suffix='ADDR', ptype='ha', ff_prefix=ff_prefix)
						misc_pattern = self.mem_lookup_pattern(imh=imh_num, ha=ha_num, suffix='MISC', ptype='ha', ff_prefix=ff_prefix)

				elif mem_type == 'HSF':
					imh_match = re.search(r'IMH(\d+)', test_name)
					hsf_match = re.search(r'HAMVF__HSF_(\d+)', test_name)
					if imh_match and hsf_match:
						imh_num = imh_match.group(1)
						hsf_num = hsf_match.group(1)
						addr_pattern = self.mem_lookup_pattern(imh=imh_num, hsf=hsf_num, suffix='ADDR', ptype='hsf', ff_prefix=ff_prefix)
						misc_pattern = self.mem_lookup_pattern(imh=imh_num, hsf=hsf_num, suffix='MISC', ptype='hsf', ff_prefix=ff_prefix)

				elif mem_type == 'SUBCHN':
					imh_match = re.search(r'IMH(\d+)', test_name)
					mc_match = re.search(r'MEMSS__MC(\d+)', test_name)
					subch_match = re.search(r'SUBCH(\d+)', test_name)
					if imh_match and mc_match:
						imh_num = imh_match.group(1)
						mc_num = mc_match.group(1)
						subch_num = subch_match.group(1) if subch_match else '0'
						addr_pattern = self.mem_lookup_pattern(imh=imh_num, mc=mc_num, subch=subch_num, suffix='ADDR', ptype='subchn', ff_prefix=ff_prefix)
						misc_pattern = self.mem_lookup_pattern(imh=imh_num, mc=mc_num, subch=subch_num, suffix='MISC', ptype='subchn', ff_prefix=ff_prefix)

				elif mem_type == 'MSE':
					imh_match = re.search(r'IMH(\d+)', test_name)
					mc_match = re.search(r'MEMSS__MC(\d+)', test_name)
					subch_match = re.search(r'SUBCH(\d+)', test_name)
					if imh_match and mc_match:
						imh_num = imh_match.group(1)
						mc_num = mc_match.group(1)
						subch_num = subch_match.group(1) if subch_match else '0'
						addr_pattern = self.mem_lookup_pattern(imh=imh_num, mc=mc_num, subch=subch_num, suffix='ADDR', ptype='mse', ff_prefix=ff_prefix)
						misc_pattern = self.mem_lookup_pattern(imh=imh_num, mc=mc_num, subch=subch_num, suffix='MISC', ptype='mse', ff_prefix=ff_prefix)

				elif mem_type == 'SCA':
					imh_match = re.search(r'IMH(\d+)', test_name)
					sca_match = re.search(r'__SCA__SCA(\d+)__', test_name)
					if imh_match and sca_match:
						imh_num = imh_match.group(1)
						sca_num = sca_match.group(1)
						addr_pattern = self.mem_lookup_pattern(imh=imh_num, sca=sca_num, suffix='ADDR', ptype='sca', ff_prefix=ff_prefix)
						misc_pattern = self.mem_lookup_pattern(imh=imh_num, sca=sca_num, suffix='MISC', ptype='sca', ff_prefix=ff_prefix)

				else:
					# Fallback to simple replacement (test_name already contains FF prefix if applicable)
					if 'MCI_STATUS' in test_name:
						addr_pattern = test_name.replace('_MCI_STATUS', '_MCI_ADDR')
						misc_pattern = test_name.replace('_MCI_STATUS', '_MCI_MISC')
					elif 'MC_STATUS' in test_name:
						addr_pattern = test_name.replace('_MC_STATUS', '_MC_ADDR').replace('IMC0_MC_STATUS', 'IMC0_MC8_ADDR')
						misc_pattern = test_name.replace('_MC_STATUS', '_MC_MISC')

				addr_value = self.xlookup(lookup_array=mem_filtered, testname=addr_pattern,
				                         LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)
				misc_value = self.xlookup(lookup_array=mem_filtered, testname=misc_pattern,
				                         LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)

				# Get Run Info
				run = str(LotsSeqKey) + "-" + str(UnitTestingSeqKey)
				data_dict['Run'] += [run]
				# Append FF type to operation to differentiate FF vs non-FF cases (e.g. 8749_VBUMP_100)
				data_dict['Operation'] += [f'{operation}_{ff_type}' if ff_type else str(operation)]
				data_dict['Type'] += [mem_type]
				data_dict['MEM_MC'] += [test_name]
				data_dict['IMH'] += [imh]
				data_dict['Instance'] += [instance]
				data_dict['MCACOD'] += [hex(mcacod)]
				data_dict['MC_DECODE'] += [mc_decode]
				data_dict['MC_STATUS'] += [mc_value]
				data_dict['MC_ADDR'] += [addr_value]
				data_dict['MC_MISC'] += [misc_value]

		new_df = pd.DataFrame(data_dict)
		return new_df

	def mem_decoder(self, value, mem_type):
		"""
		Memory MCA decoder for DMR
		Routes to appropriate decoder based on memory component type

		Args:
			value: MC_STATUS register value
			mem_type: Type of memory component (HA, HSF, SUBCHN, MSE, SCA)
		"""
		if value == '' or value is None:
			return ''

		try:
			mscod = extract_bits(hex_value=value, min_bit=16, max_bit=31)

			# Route to appropriate JSON decoder
			if mem_type == 'HA':
				# Use hamvf_params.json
				hamvf_json = self.mcadata.hamvf_data if hasattr(self.mcadata, 'hamvf_data') else {}
				if 'MSCOD' in hamvf_json and str(mscod) in hamvf_json['MSCOD']:
					return f"{hamvf_json['MSCOD'][str(mscod)]} (MSCOD={mscod})"
				return f"MSCOD={mscod}"

			elif mem_type == 'HSF':
				# Use cache_params.json for HSF (snoop filter cache)
				cache_json = self.mcadata.cache_data if hasattr(self.mcadata, 'cache_data') else {}
				if 'MSCOD_BY_VAL' in cache_json and str(mscod) in cache_json['MSCOD_BY_VAL']:
					return f"{cache_json['MSCOD_BY_VAL'][str(mscod)]} (MSCOD={mscod})"

				# Fallback to LLC data
				llc_json = self.mcadata.llc_data
				mscod_table = llc_json.get('MSCOD_BY_VAL', {})
				if str(mscod) in mscod_table:
					return f"{mscod_table[str(mscod)]} (MSCOD={mscod})"
				return f"MSCOD={mscod}"

			elif mem_type == 'SUBCHN':
				# Use mc_subch_params.json
				mc_subch_json = self.mcadata.mc_subch_data if hasattr(self.mcadata, 'mc_subch_data') else {}
				if 'MSCOD' in mc_subch_json and str(mscod) in mc_subch_json['MSCOD']:
					return f"{mc_subch_json['MSCOD'][str(mscod)]} (MSCOD={mscod})"
				return f"MSCOD={mscod}"

			elif mem_type == 'MSE':
				# Use mse_params.json (already exists in GNR structure)
				mse_json = self.mcadata.mse_data if hasattr(self.mcadata, 'mse_data') else {}
				if 'MSCOD' in mse_json and str(mscod) in mse_json['MSCOD']:
					return f"{mse_json['MSCOD'][str(mscod)]} (MSCOD={mscod})"
				return f"MSCOD={mscod}"

			elif mem_type == 'SCA':
				# Use sca_params.json
				sca_json = self.mcadata.sca_data if hasattr(self.mcadata, 'sca_data') else {}
				if 'MSCOD_BY_VAL' in sca_json and str(mscod) in sca_json['MSCOD_BY_VAL']:
					return f"{sca_json['MSCOD_BY_VAL'][str(mscod)]} (MSCOD={mscod})"

				# Fallback to LLC data
				llc_json = self.mcadata.llc_data
				mscod_table = llc_json.get('MSCOD_BY_VAL', {})
				if str(mscod) in mscod_table:
					return f"{mscod_table[str(mscod)]} (MSCOD={mscod})"
				return f"MSCOD={mscod}"

			else:
				return f"MSCOD={mscod}"

		except Exception as e:
			return f"Decode error: {str(e)}"

	def memory_decoder(self, value):
		"""
		Memory MCA decoder
		"""
		if value == '':
			return value

		# Extract MCACOD from bits 15:0
		mcacod = extract_bits(hex_value=value, min_bit=0, max_bit=15)

		# Memory error types
		mem_errors = {
			0x90: "MEM_RD_ERR: Memory read error - uncorrectable",
			0x91: "MEM_RD_CORR_ERR: Memory read error - correctable",
			0xA0: "MEM_WR_ERR: Memory write error",
			0x92: "MEM_SCRUB_ERR: Memory scrub error"
		}

		return mem_errors.get(mcacod, f"Unknown memory error: MCACOD={mcacod}")

	def memory_error_type(self, value):
		"""
		Determine if memory error is correctable or uncorrectable
		"""
		if value == '':
			return 'N/A'

		mcacod = extract_bits(hex_value=value, min_bit=0, max_bit=15)

		if mcacod == 0x91 or mcacod == 0x92:
			return 'Correctable'
		elif mcacod == 0x90 or mcacod == 0xA0:
			return 'Uncorrectable'
		else:
			return 'Unknown'


# Utility function to extract bits from hex value
def extract_bits(hex_value, min_bit, max_bit):
	"""
	Extract bits from hex value
	"""
	if hex_value == '' or hex_value is None:
		return 0

	try:
		# Convert hex string to integer
		if isinstance(hex_value, str):
			int_value = int(hex_value, 16) if hex_value.startswith('0x') else int(hex_value, 16)
		else:
			int_value = int(hex_value)

		# Create mask for the bit range
		num_bits = max_bit - min_bit + 1
		mask = (1 << num_bits) - 1

		# Extract the bits
		extracted = (int_value >> min_bit) & mask

		return extracted
	except:
		return 0


# Helper function to load JSON files
def dev_dict(filename, filedir):
	"""
	Load JSON configuration file
	"""
	filepath = os.path.join(filedir, filename)

	if not os.path.exists(filepath):
		print(f"Warning: {filepath} not found")
		return {}

	with open(filepath, 'r') as f:
		data = json.load(f)

	return data
