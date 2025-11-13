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
	
	# Define the lookup pattern for each column - DMR specific patterns
	def lookup_pattern(self, cbb, compute, module, location, operation, suffix, env='', inst='', ptype='ccf'):
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
		
		ptype options: ccf, core_ifu, core_dcu, core_dtlb, core_ml2, sca, ha, hsf, punit_cbb, punit_imh, ncu, d2d_cbb, d2d_imh
		"""
		
		# CBB Domain Patterns
		if ptype == 'ccf':
			# CCF (Caching/Coherency Fabric) - Bank 6
			# Pattern: SOCKET0__CBB{x}__BASE__I_CCF_ENV{env}__CBREGS_ALL{instance}__MC_STATUS
			# Must match exact ENV and CBREGS_ALL pair
			# Note: CCF contains LLC + CHA functionality (32 merged CBO instances)
			pattern = f"SOCKET0__CBB{cbb}__BASE__I_CCF_ENV{env}__CBREGS_ALL{inst}__MC_{suffix}"
		
		elif ptype == 'ncu':
			# NCU (Node Control Unit) - Bank 5
			# Pattern: SOCKET0__CBB{x}__BASE__SNCU_TOP__SNCEVENTS__MC5_STATUS
			pattern = f"SOCKET0__CBB{cbb}__BASE__SNCU_TOP__SNCEVENTS__MC5_{suffix}"
		
		elif ptype == 'd2d_cbb':
			# D2D CBB side - Bank 7
			# Pattern: SOCKET0__CBB{x}__BASE__D2D_STACK_{stack}__ULA_{ula}__ULA__ULA_MC_ST
			# location = stack number, compute = ula number
			pattern = f"SOCKET0__CBB{cbb}__BASE__D2D_STACK_{location}__ULA_{compute}__ULA__ULA_MC_{suffix}"
		
		elif ptype == 'punit_cbb':
			# Power Unit CBB - Bank 4
			# Pattern: SOCKET0__CBB{x}__BASE__PUNIT_REGS__PUNIT_GPSB__GPSB_INFVNN_CRS__MC_STATUS
			pattern = f"SOCKET0__CBB{cbb}__BASE__PUNIT_REGS__PUNIT_GPSB__GPSB_INFVNN_CRS__MC_{suffix}"
		
		# Core Patterns (Banks 0-3) - Need CBB, COMPUTE, MODULE, and CORE numbers
		elif ptype == 'core_ifu':
			# IFU - Bank 0 (Instruction Fetch Unit)
			# Pattern: SOCKET0__CBB{x}__COMPUTE{y}__MODULE{z}__CORE{w}__IFU_CR_MC0_STATUS
			# Note: DMR has one thread per core (no SMT/HT)
			pattern = f"SOCKET0__CBB{cbb}__COMPUTE{compute}__MODULE{module}__CORE{location}__IFU_CR_MC0_{suffix}"
		
		elif ptype == 'core_dcu':
			# DCU - Bank 1 (Data Cache Unit)
			pattern = f"SOCKET0__CBB{cbb}__COMPUTE{compute}__MODULE{module}__CORE{location}__DCU_CR_MC1_{suffix}"
		
		elif ptype == 'core_dtlb':
			# DTLB - Bank 2 (Data TLB)
			pattern = f"SOCKET0__CBB{cbb}__COMPUTE{compute}__MODULE{module}__CORE{location}__DTLB_CR_MC2_{suffix}"
		
		elif ptype == 'core_ml2':
			# MLC - Bank 3 (Module Level Cache / L2)
			# Pattern: SOCKET0__CBB{x}__COMPUTE{y}__MODULE{z}__ML2_CR_MC3_STATUS
			pattern = f"SOCKET0__CBB{cbb}__COMPUTE{compute}__MODULE{module}__ML2_CR_MC3_{suffix}"
		
		# IMH Domain Patterns
		elif ptype == 'sca':
			# SCA (Scalable Caching Agent / IO Caching Agent) - Bank 14
			# Pattern: SOCKET0__IMH{imh}__SCF__SCA__SCA{instance}__UTIL__MC_STATUS
			# Note: SCA is for UIO device caching, NOT system LLC
			# SCA = IOCA (IO Caching Agent) - provides IO-specific cache for multiple UIO devices
			# location = IMH number, compute = SCA instance
			pattern = f"SOCKET0__IMH{location}__SCF__SCA__SCA{compute}__UTIL__MC_{suffix}"
		
		elif ptype == 'ha':
			# Home Agent - Bank 12 (merged 16 instances)
			# Pattern: SOCKET0__IMH{imh}__SCF__HAMVF__HA_{instance}__MCI_STATUS
			pattern = f"SOCKET0__IMH{location}__SCF__HAMVF__HA_{compute}__MCI_{suffix}"
		
		elif ptype == 'hsf':
			# HSF (Home Snoop Filter) - Bank 13
			# Pattern: SOCKET0__IMH{imh}__SCF__HAMVF__HSF_{instance}__UTIL__MCI_STATUS
			pattern = f"SOCKET0__IMH{location}__SCF__HAMVF__HSF_{compute}__UTIL__MCI_{suffix}"
		
		elif ptype == 'punit_imh':
			# Power Unit IMH - Bank 11
			# Pattern: SOCKET0__IMH{imh}__PUNIT__RAS__GPSB__MC_STATUS
			pattern = f"SOCKET0__IMH{location}__PUNIT__RAS__GPSB__MC_{suffix}"
		
		elif ptype == 'd2d_imh':
			# D2D IMH side - Bank 15
			# Pattern: SOCKET0__IMH{imh}__D2D_STACK__D2D_STACK_{stack}__UXI_{uxi}__ULA_MC_ST
			# location = IMH number, module = stack number, compute = uxi number
			pattern = f"SOCKET0__IMH{location}__D2D_STACK__D2D_STACK_{module}__UXI_{compute}__ULA_MC_{suffix}"
		
		elif ptype == 'rasip':
			# RASIP - Bank 10
			# Pattern: SOCKET0__IMH{imh}__RASIP__ROOT_RAS__RASIP_REGS_BLOCK__RASIP_REG_MSG_CR_RASIP_ERROR_HANDLER_CR__REG_CR_MCI_STATUS
			pattern = f"SOCKET0__IMH{location}__RASIP__ROOT_RAS__RASIP_REGS_BLOCK__RASIP_REG_MSG_CR_RASIP_ERROR_HANDLER_CR__REG_CR_MCI_{suffix}"
		
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
				
				## Address lookup pattern - use exact CBB, ENV and instance for precise matching
				addr_lut = self.lookup_pattern(cbb=cbb, compute='', module='', location='', operation=operation, 
				                                suffix="ADDR", env=env, inst=instance, ptype='ccf')
				misc_lut = self.lookup_pattern(cbb=cbb, compute='', module='', location='', operation=operation, 
				                                suffix="MISC", env=env, inst=instance, ptype='ccf')
				misc3_lut = self.lookup_pattern(cbb=cbb, compute='', module='', location='', operation=operation, 
				                                 suffix="MISC3", env=env, inst=instance, ptype='ccf')
				
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
				data_dict['Operation'] += [str(operation)]
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
		ccf_json = self.mcadata.cha_data  # Using cha_params.json from GNR for CCF
		
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
			'MC DECODE': {'table': 'MSCOD_BY_VAL', 'min': 16, 'max': 31},          # Status - MSCOD field
			
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
			mc_value = extractedvalue
		
		return mc_value

	def core(self):
		"""
		Core MCA decoder - Banks 0-2 (IFU, DCU, DTLB)
		BigCore (PNC) with one thread per core
		"""
		mcdata = self.data
		columns = ['VisualID', 'Run', 'Operation', 'Core_MC', 'Compute', 'Core', 
		           'Bank', 'MC_STATUS', 'MC DECODE', 'MC_ADDR', 'MC_MISC']
		
		data_dict = {k:[] for k in columns}
		
		# Core banks: IFU (0), DCU (1), DTLB (2)
		core_banks = {'IFU': ('MC0', 'core_ifu', 0), 
		              'DCU': ('MC1', 'core_dcu', 1), 
		              'DTLB': ('MC2', 'core_dtlb', 2)}
		
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
					
					# Use exact CBB, COMPUTE, MODULE, and CORE for precise matching
					addr_lut = self.lookup_pattern(cbb=cbb, compute=compute, module=module, location=core, 
					                                operation=operation, suffix="ADDR", ptype=ptype)
					misc_lut = self.lookup_pattern(cbb=cbb, compute=compute, module=module, location=core, 
					                                operation=operation, suffix="MISC", ptype=ptype)
					
					mc_value = data['TestValue']
					addr_value = self.xlookup(lookup_array=addr_filtered, testname=addr_lut,
					                          LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)
					misc_value = self.xlookup(lookup_array=misc_filtered, testname=misc_lut,
					                          LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)
					
					run = str(LotsSeqKey) + "-" + str(UnitTestingSeqKey)
					data_dict['Run'] += [run]
					data_dict['Operation'] += [str(operation)]
					data_dict['Core_MC'] += [data['TestName']]
					data_dict['Compute'] += [f'CBB{cbb}_COMPUTE{compute}']
					data_dict['Core'] += [f'CORE{core}']
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

	def sca(self):
		"""
		SCA (Scalable Caching Agent / IO Caching Agent) MCA decoder - Bank 14
		Pattern: SOCKET0__IMH{0-1}__SCF__SCA__SCA{0-15}__UTIL__MC_STATUS
		
		Important: SCA is NOT the system LLC. SCA is an IO-specific caching agent
		that supports multiple UIO devices. System LLC is part of CCF (Bank 6).
		
		SCA Features:
		- Provides caching for UIO devices (Gen6, CXL, etc.)
		- Reduces NodeID pressure by allowing UIO devices to share same NID
		- Independent tag and data pipelines for higher throughput (32B/c vs 11B/c)
		- 8 SCA instances in DMR iMH sustain 2 concurrent Gen6 read+write BW streams
		"""
		mcdata = self.data
		columns = ['VisualID', 'Run', 'Operation', 'SCA_MC', 'IMH', 'SCA_Instance',
		           'MC_STATUS', 'MC DECODE', 'MC_ADDR', 'MC_MISC', 'Error_Type']
		
		data_dict = {k:[] for k in columns}
		
		for visual_id in mcdata['VisualId'].unique():
			# Split Data into required elements - look for SCF__SCA pattern
			subset = mcdata[(mcdata['VisualId'] == visual_id) & 
			                (mcdata['TestName'].str.contains('SCF__SCA'))]
			
			mc_filtered = self.extract_value(subset, 'TestName', 'MC_STATUS')
			addr_filtered = self.extract_value(subset, 'TestName', 'MC_ADDR')
			misc_filtered = self.extract_value(subset, 'TestName', 'MC_MISC')
			
			if mc_filtered.empty:
				continue
			
			for i, data in mc_filtered.iterrows():
				data_dict['VisualID'] += [visual_id]
				LotsSeqKey = data['LotsSeqKey']
				UnitTestingSeqKey = data['UnitTestingSeqKey']
				
				# Extract IMH and SCA instance
				# Pattern: SOCKET0__IMH{0-1}__SCF__SCA__SCA{0-15}__UTIL__MC_STATUS
				imh_match = re.search(r'IMH(\d+)', data['TestName'])
				sca_match = re.search(r'__SCA__SCA(\d+)__', data['TestName'])
				
				imh = imh_match.group(1) if imh_match else '0'
				sca_inst = sca_match.group(1) if sca_match else '0'
				
				operation = data['Operation']
				
				# Use exact IMH and SCA instance for precise matching
				addr_lut = self.lookup_pattern(cbb='', compute=sca_inst, module='', location=imh, 
				                                operation=operation, suffix="ADDR", ptype='sca')
				misc_lut = self.lookup_pattern(cbb='', compute=sca_inst, module='', location=imh, 
				                                operation=operation, suffix="MISC", ptype='sca')
				
				mc_value = data['TestValue']
				addr_value = self.xlookup(lookup_array=addr_filtered, testname=addr_lut,
				                          LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)
				misc_value = self.xlookup(lookup_array=misc_filtered, testname=misc_lut,
				                          LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)
				
				run = str(LotsSeqKey) + "-" + str(UnitTestingSeqKey)
				data_dict['Run'] += [run]
				data_dict['Operation'] += [str(operation)]
				data_dict['SCA_MC'] += [data['TestName']]
				data_dict['IMH'] += [f'IMH{imh}']
				data_dict['SCA_Instance'] += [f'SCA{sca_inst}']
				data_dict['MC_STATUS'] += [mc_value]
				data_dict['MC_ADDR'] += [addr_value]
				data_dict['MC_MISC'] += [misc_value]
				
				# Decode using SCA decoder logic (IO caching agent, not LLC)
				data_dict['MC DECODE'] += [self.sca_decoder(value=mc_value)]
				data_dict['Error_Type'] += [self.sca_error_type(value=mc_value)]
		
		new_df = pd.DataFrame(data_dict)
		return new_df

	def sca_decoder(self, value):
		"""
		SCA (IO Caching Agent) MCA decoder for DMR
		Note: SCA uses similar MSCOD encoding as LLC but is for IO device caching
		"""
		if value == '':
			return value
		
		# Use the LLC data from mcadata (SCA uses similar error codes)
		llc_json = self.mcadata.llc_data
		
		# Extract MSCOD from bits 31:16
		mscod = extract_bits(hex_value=value, min_bit=16, max_bit=31)
		
		# Look up in MSCOD_BY_VAL table
		mscod_table = llc_json.get('MSCOD_BY_VAL', {})
		mscod_str = str(mscod)
		
		if mscod_str in mscod_table:
			return mscod_table[mscod_str]
		else:
			return f"MSCOD={mscod}"

	def sca_error_type(self, value):
		"""
		Determine SCA error severity using JSON configuration
		Note: SCA is IO caching agent, not system LLC
		"""
		if value == '':
			return 'N/A'
		
		mscod = extract_bits(hex_value=value, min_bit=16, max_bit=31)
		
		# Use error type lists from JSON if available
		llc_json = self.mcadata.llc_data
		error_types = llc_json.get('ERROR_TYPES', {})
		
		correctable = error_types.get('CORRECTABLE', [7, 17, 18, 34, 35, 40, 49, 57, 60])
		uncorrectable = error_types.get('UNCORRECTABLE', [1, 2, 8, 10, 19, 33, 36, 41, 50, 58, 59])
		
		if mscod in correctable:
			return 'Correctable'
		elif mscod in uncorrectable:
			return 'Uncorrectable'
		else:
			return 'Unknown'

	def memory(self):
		"""
		Memory Controller MCA decoder - Banks 19-26 (8 channels, 2 sub-channels each)
		NOTE: This pattern not observed in current DMR register paths
		Keeping for future use if memory controller paths are identified
		"""
		mcdata = self.data
		columns = ['VisualID', 'Run', 'Operation', 'MC', 'IMH', 'Channel', 'SubChannel',
		           'MC_STATUS', 'MC DECODE', 'MC_ADDR', 'MC_MISC', 'Error_Type']
		
		data_dict = {k:[] for k in columns}
		
		# Memory controller pattern not yet identified in DMR
		# Placeholder for future implementation
		print("Memory controller decoder not yet implemented for DMR")
		
		new_df = pd.DataFrame(data_dict)
		return new_df

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
