## MCA Decoder for MCA Checker
## Gaespino - Nov-2024

#import sys
#import os
import json
import re
import pandas as pd
from pathlib import Path
import os
import sys

# Import DMR decoder

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from Decoder.decoder_dmr import decoder_dmr

validproducts = {'GNR':'bigcore', 'CWF':'atom', 'DMR':'bigcore'}

class mcadata():
	def __init__(self, product):
		self.product = product
		parent_dir =Path(__file__).parent
		self.jsfile_dir = os.path.join(parent_dir, product.upper())

		self.llc_data = self.llc()
		self.cha_data = self.cha()
		self.core_data = self.core()
		self.portid_data = self.portid()
		self.mse_data = self.mse()
		self.mcchnl_data = self.mcchnl()
		self.b2cmi_data = self.b2cmi()
		self.upi_data = self.upi()
		self.ubox_data = self.ubox()
		
		# DMR-specific JSON files
		if product.upper() == 'DMR':
			self.ula_data = self.ula()
			self.cache_data = self.cache()
			self.hamvf_data = self.hamvf()
			self.mc_subch_data = self.mc_subch()
			self.sca_data = self.sca_dmr()


	def llc(self):
		# Load product-specific LLC data from JSON if available (DMR, future products)
		# Otherwise use default GNR/CWF hardcoded data
		try:
			llc_json = dev_dict('llc_params.json', filedir = self.jsfile_dir)
			if llc_json:
				return llc_json
		except:
			pass
		
		# Default LLC data for GNR/CWF (fallback)
		llc_json = {'MSCOD_BY_VAL': {
		"0": "MSCOD_NONE",
		"2": "MSCOD_UNCORRECTABLE_TAG_ERROR",
		"36": "MSCOD_SF_STCV_UNCORR_ERR",
		"33": "MSCOD_UNCORRECTABLE_SF_TAG_ERROR",
		"19": "MSCOD_LLC_STCV_UNCORR_ERR",
		"58": "MSCOD_RSF_TAG_UNCORR_ERR",
		"59": "MSCOD_RSF_ST_UNCORR_ERR",
		"41": "MSCOD_LLC_TWOLM_UNCORR_ERR",
		"50": "MSCOD_SF_TWOLM_UNCORR_ERR",
		"10": "MSCOD_PARITY_DATA_ERROR",
		"1": "MSCOD_UNCORRECTABLE_DATA_ERROR",
		"8": "MSCOD_MEM_POISON_DATA_ERROR",
		"7": "MSCOD_CORRECTABLE_DATA_ERROR",
		"34": "MSCOD_SF_TAG_CORR_ERR",
		"35": "MSCOD_SF_STCV_CORR_ERR",
		"17": "MSCOD_LLC_TAG_CORR_ERR",
		"18": "MSCOD_LLC_STCV_CORR_ERR",
		"60": "MSCOD_RSF_TAG_CORR_ERR",
		"57": "MSCOD_RSF_ST_CORR_ERR",
		"40": "MSCOD_LLC_TWOLM_CORR_ERR",
		"49": "MSCOD_SF_TWOLM_CORR_ERR"
		}}

		return llc_json

	def cha(self):
		cha_json = dev_dict('cha_params.json', filedir = self.jsfile_dir)
		return cha_json

	def core(self):
		core_json = dev_dict('core_params.json', filedir = self.jsfile_dir)
		return core_json

	def portid(self):
		portids_json = dev_dict('log_portid.json', filedir = self.jsfile_dir)
		return portids_json
	
	def mse(self):
		"""Load MSE (Memory Security Engine) parameters JSON"""
		try:
			mse_json = dev_dict('mse_params.json', filedir = self.jsfile_dir)
			return mse_json
		except:
			return {}
	
	def mcchnl(self):
		"""Load Memory Controller Channel (MCCHAN/iMC) parameters JSON"""
		try:
			mcchnl_json = dev_dict('mcchnl_params.json', filedir = self.jsfile_dir)
			return mcchnl_json
		except:
			return {}
	
	def b2cmi(self):
		"""Load B2CMI (B2C Memory Interface) parameters JSON"""
		try:
			b2cmi_json = dev_dict('b2cmi_params.json', filedir = self.jsfile_dir)
			return b2cmi_json
		except:
			return {}
	
	def upi(self):
		"""Load UPI (Ultra Path Interconnect) parameters JSON"""
		try:
			upi_json = dev_dict('upi_params.json', filedir = self.jsfile_dir)
			return upi_json
		except:
			return {}
	
	def ubox(self):
		"""Load UBOX parameters JSON"""
		try:
			ubox_json = dev_dict('ubox_params.json', filedir = self.jsfile_dir)
			return ubox_json
		except:
			return {}
	
	def ula(self):
		"""Load ULA (UXI Link Agent) parameters JSON for DMR"""
		try:
			ula_json = dev_dict('ula_params.json', filedir = self.jsfile_dir)
			return ula_json
		except:
			return {}
	
	def cache(self):
		"""Load cache parameters JSON for DMR (IOCACHE, HSF)"""
		try:
			cache_json = dev_dict('cache_params.json', filedir = self.jsfile_dir)
			return cache_json
		except:
			return {}
	
	def hamvf(self):
		"""Load HAMVF (Home Agent Memory Virtual Function) parameters JSON for DMR"""
		try:
			hamvf_json = dev_dict('hamvf_params.json', filedir = self.jsfile_dir)
			return hamvf_json
		except:
			return {}
	
	def mc_subch(self):
		"""Load Memory Controller Subchannel parameters JSON for DMR"""
		try:
			mc_subch_json = dev_dict('mc_subch_params.json', filedir = self.jsfile_dir)
			return mc_subch_json
		except:
			return {}
	
	def sca_dmr(self):
		"""Load SCA parameters JSON for DMR"""
		try:
			sca_json = dev_dict('sca_params.json', filedir = self.jsfile_dir)
			return sca_json
		except:
			return {}


class decoder():
	
	def __init__(self, data, product = 'GNR'):
		self.data = data
		self.product = product

		if product in validproducts.keys():
			self.mcadata = mcadata(product)
			self.coretype = validproducts[product]
			
			# Instantiate DMR-specific decoder if product is DMR
			if product == 'DMR':
				self.dmr_decoder = decoder_dmr(data, self.mcadata)
		else:
			print(f' Not valid product selected use: {validproducts}')
			sys.exit()

	# Helper function to extract values based on a pattern
	def extract_value(self, df, dfcol, pattern):
		#filtered = pd.DataFrame()
		if isinstance(pattern, str):
			pat = [pattern]
		else:
			pat = pattern
		
		regex_pat = '|'.join(pat)

		filtered= df[(df[dfcol].str.contains(regex_pat, case=False, na=False))]

		#if not filtered.empty:
		return filtered   			
		#return None
	
	# Define the lookup pattern for each column
	def lookup_pattern(self, compute, location, operation, suffix, thread = '', ptype = 'cha'):
		
		if ptype == 'cha':
			pattern = f"COMPUTE{compute}__UNCORE__CHA__CHA{location}__UTIL__MC_{suffix}"#_{operation}"
		elif ptype == 'llc':
			pattern = f"COMPUTE{compute}__UNCORE__SCF__SCF_LLC__SCF_LLC{location}__MCI_{suffix}"#_{operation}"
		#DPMB_SOCKET0__COMPUTE0__CPU__CORE0__ML2_CR_MC3_ADDR_8749
		#elif ptype == 'ubox':
		#	pattern = f"(SOCKET0|SOCKET1)__{compute}__UNCORE__{location}__NCEVENTS__{suffix}"#_{operation}"	

		## Patterns for bigcore
		elif ptype == 'core_ml2':
				pattern = f"COMPUTE{compute}__CPU__CORE{location}__ML2_CR_MC3_{suffix}"#_{operation}"		
		#DPMB_SOCKET0__COMPUTE1__CPU__CORE68__THREAD0__DCU_CR_MC1_STATUS_8749
		elif ptype == 'core_dcu':
				pattern = f"COMPUTE{compute}__CPU__CORE{location}__THREAD{thread}__DCU_CR_MC1_{suffix}"#_{operation}"	
		#DPMB_SOCKET0__COMPUTE0__CPU__CORE0__DTLB_CR_MC2_STATUS_*
		elif ptype == 'core_dtlb':
				pattern = f"COMPUTE{compute}__CPU__CORE{location}__DTLB_CR_MC2_{suffix}"#_{operation}"	
		#DPMB_SOCKET0__COMPUTE0__CPU__CORE0__THREAD*__IFU_CR_MC0_STATUS_*
		elif ptype == 'core_ifu':
				pattern = f"COMPUTE{compute}__CPU__CORE{location}__THREAD{thread}__IFU_CR_MC0_{suffix}"#_{operation}"	


		## Patterns for atomcore
		elif ptype == 'core_l2':
			pattern = f"COMPUTE{compute}__CPU__MODULE{location}__L2_CR_MCI_{suffix}"#_{operation}"		
		
		elif ptype == 'core_bbl':
			pattern = f"COMPUTE{compute}__CPU__MODULE{location}__BBL_CR_MCI_{suffix}"#_{operation}"		

		elif ptype == 'core_bus':
			pattern = f"COMPUTE{compute}__CPU__MODULE{location}__BUS_CR_MCI_{suffix}"#_{operation}"	

		#DPMB_SOCKET0__COMPUTE1__CPU__CORE68__THREAD0__DCU_CR_MC1_STATUS_8749
		elif ptype == 'core_mec':
			pattern = f"COMPUTE{compute}__CPU__MODULE{location}__CORE{thread}__MEC_CR_MCI_{suffix}"#_{operation}"	
		#DPMB_SOCKET0__COMPUTE0__CPU__CORE0__DTLB_CR_MC2_STATUS_*
		elif ptype == 'core_agu':
			pattern = f"COMPUTE{compute}__CPU__MODULE{location}__CORE{thread}__AGU_CR_MCI_{suffix}"#_{operation}"	
		#DPMB_SOCKET0__COMPUTE0__CPU__CORE0__THREAD*__IFU_CR_MC0_STATUS_*
		elif ptype == 'core_ic':
			pattern = f"COMPUTE{compute}__CPU__MODULE{location}__CORE{thread}__IC_CR_MCI_{suffix}"#_{operation}"	
		else:
			pattern = ''

		return pattern

	def mem_lookup_pattern(self, mc='', ch='', b2cmi='', imc='', suffix='ADDR', ptype='b2cmi'):
		"""
		Generate lookup patterns for memory subsystem registers

		Args:
			mc: Memory Controller number
			ch: Channel number
			b2cmi: B2CMI instance number
			imc: iMC instance number
			suffix: Register suffix (ADDR, MISC, etc.)
			ptype: Pattern type (b2cmi, mse, mcchan)

		Returns:
			Lookup pattern string
		"""
		if ptype == 'b2cmi':
			# Pattern: SOCKET0__SOC__MEMSS__B2CMI{n}__MCI_{suffix}
			pattern = f"SOC__MEMSS__B2CMI{b2cmi}__MCI_{suffix}"
			
		elif ptype == 'mse':
			# Pattern: SOCKET0__SOC__MEMSS__MC{n}__CH{n}__MSE__MSE_MCI_{suffix}
			pattern = f"SOC__MEMSS__MC{mc}__CH{ch}__MSE__MSE_MCI_{suffix}"
			
		elif ptype == 'mcchan':
			# Pattern: SOCKET0__SOC__MEMSS__MC{n}__CH{ch}__MCCHAN__IMC{imc}_MC_{suffix}
			# Note: ADDR register is IMC0_MC8_ADDR (special case)
			if suffix == 'ADDR':
				pattern = f"SOC__MEMSS__MC{mc}__CH{ch}__MCCHAN__IMC{imc}_MC8_ADDR"
			else:
				pattern = f"SOC__MEMSS__MC{mc}__CH{ch}__MCCHAN__IMC{imc}_MC_{suffix}"
		else:
			pattern = ''
		
		return pattern

	# XLOOKUP equivalent in pandas
	def xlookup(self, lookup_array, testname, LotsSeqKey, UnitTestingSeqKey, if_not_found=""):
		if lookup_array.empty:# == None:
			return if_not_found
		try:
			result = lookup_array[(lookup_array['TestName'].str.contains(testname)) & (lookup_array['LotsSeqKey'] == LotsSeqKey) & (lookup_array['UnitTestingSeqKey'] == UnitTestingSeqKey)]
			lutvalue = result['TestValue'].iloc[0] if not result.empty else if_not_found
		except:
			print(f' -- Error looking for {testname}: Nothing found in MCA Data')
			lutvalue = if_not_found
		return  lutvalue

	def cha(self):
		# Delegate to DMR CCF decoder if product is DMR
		if self.product == 'DMR':
			return self.dmr_decoder.ccf()
		
		mcdata = self.data
		
		# Check if required columns exist
		required_columns = ['VisualId', 'TestName']
		missing_columns = [col for col in required_columns if col not in mcdata.columns]
		if missing_columns:
			print(f' !!! ERROR: Missing required columns in MCA data: {missing_columns}')
			print(f' !!! Available columns: {list(mcdata.columns)}')
			print(' !!! Returning empty DataFrame. Please check your input Excel file structure.')
			return pd.DataFrame()
		
		# Initialize the new dataframe
		columns = ['VisualID', 'Run', 'Operation', 'CHA_MC', 'Compute', 'CHA', 'MC_STATUS', 'MC DECODE','MC_ADDR', 'MC_MISC', 'MC_MISC3','Orig Req','Opcode','cachestate','TorID','TorFSM','SrcID','ISMQ','Attribute','Result','Local Port']
		#new_df = pd.DataFrame(columns=columns)
		#decodelist = ['MC DECODE', 'Orig Req','Opcode','cachestate','TorID','TorFSM','SrcID','ISMQ','Attribute','Result','Local Port']
		
		# CHA List
		decodelistmc = ['MC DECODE']
		decodelistmisc = ['Orig Req','Opcode','cachestate','TorID','TorFSM']
		decodelistmisc3 = ['SrcID','ISMQ','Attribute','Result','Local Port']

		data_dict = {k:[] for k in columns}
		

		for visual_id in mcdata['VisualId'].unique():

			# Split Data into required elements
			subset = mcdata[(mcdata['VisualId'] == visual_id) & (mcdata['TestName'].str.contains('CHA'))]

			# Further split into required lookup registers for each VID
			mc_filtered = self.extract_value(subset,'TestName', 'UTIL__MC_STATUS')# subset[(subset['TestName'].str.contains('UTIL__MC_STATUS'))] #self.extract_value(subset, 'UTIL__MC_STATUS')
			addr_filtered = self.extract_value(subset,'TestName', 'UTIL__MC_ADDR')# subset[subset['TestName'].str.contains('UTIL__MC_ADDR')]#self.extract_value(subset, 'UTIL__MC_ADDR')
			misc_filtered = self.extract_value(subset,'TestName', r'.*UTIL__MC_MISC(?![0-9]).*')# subset[subset['TestName'].str.contains('UTIL__MC_MISC_')]#self.extract_value(subset, 'UTIL__MC_MISC_')
			misc3_filtered = self.extract_value(subset,'TestName', r'.*UTIL__MC_MISC3.*')# subset[subset['TestName'].str.contains('UTIL__MC_MISC3_')]#self.extract_value(subset, 'UTIL__MC_MISC3')
			
			# If no MCA is found move to the next VID
			try:
				if mc_filtered.empty:
					print(f' -- No MCA data found for CHAs in VID: {visual_id}')
					continue
			except:
				print(f' -- No MCA data found for CHAs in VID: {visual_id}')
				continue
			
			# This will iterate over all the MCAS to look for Address, Misc and MISC3 data for corresponding fail IP
			for i, data in mc_filtered.iterrows():
				
				# Build new
				data_dict['VisualID'] += [visual_id]
				LotsSeqKey = data['LotsSeqKey']
				UnitTestingSeqKey = data['UnitTestingSeqKey']
				compute =  re.search(r'COMPUTE(\d+)', data['TestName']).group(1) #data['TestName'].extract(r'COMPUTE(\d+)')
				cha = re.search(r'CHA(\d+)', data['TestName']).group(1)  #data['TestName'].extract(r'CHA(\d+)')
				operation = data['Operation']

				## Address lookup pattern
				addr_lut = self.lookup_pattern(compute, cha, operation, suffix="ADDR")
				misc_lut = self.lookup_pattern(compute, cha, operation, suffix="MISC")
				misc3_lut = self.lookup_pattern(compute, cha, operation, suffix="MISC3")

				## MCA Lookup values
				mc_value = data['TestValue']
				addr_value = self.xlookup(lookup_array=addr_filtered, testname = addr_lut, LotsSeqKey = LotsSeqKey, UnitTestingSeqKey = UnitTestingSeqKey)
				misc_value = self.xlookup(lookup_array=misc_filtered, testname = misc_lut, LotsSeqKey = LotsSeqKey, UnitTestingSeqKey = UnitTestingSeqKey)
				misc_value3 = self.xlookup(lookup_array=misc3_filtered, testname = misc3_lut, LotsSeqKey = LotsSeqKey, UnitTestingSeqKey = UnitTestingSeqKey)
				
				## Get Run Info
				run = str(LotsSeqKey) + "-" + str(UnitTestingSeqKey)	
				data_dict['Run'] += [run]
				data_dict['Operation'] += [str(operation)]
				data_dict['CHA_MC'] += [data['TestName'] ]
				data_dict['Compute'] += [compute]
				data_dict['CHA'] += [f'CHA{cha}']
				data_dict['MC_STATUS'] += [mc_value]
				data_dict['MC_ADDR'] += [addr_value]
				data_dict['MC_MISC'] += [misc_value]
				data_dict['MC_MISC3'] += [misc_value3]
			
				### MCdecode Data
				### Cha decode Orig Req	Opcode	cachestate	TorID	TorFSM	SrcID	ISMQ	Attribute	Result	Local Port

				for dval in decodelistmc:
					data_dict[dval] += [self.cha_decoder(value=mc_value, type=dval)]
				
				for dval in decodelistmisc:
					data_dict[dval] += [self.cha_decoder(value=misc_value, type=dval)]
				
				for dval in decodelistmisc3:
					data_dict[dval] += [self.cha_decoder(value=misc_value3, type=dval)]
		
		new_df = pd.DataFrame(data_dict)
		
		return new_df

	## CHA MCA Decode data -- Not all the values are included, add if needed for debug purposes
	def cha_decoder(self, value, type):
		cha_json = self.mcadata.cha_data
		 
		data = { 	'MC DECODE': {'table': 'MSCOD_BY_VAL', 'min': 16,'max':31}, ## Status
					'Orig Req': {'table': 'TOR_OPCODES_BY_VAL', 'min': 39,'max':49}, ## Misc
					'Opcode': {'table': 'TOR_OPCODES_BY_VAL', 'min': 23,'max':33}, ## Misc
					'cachestate': {'table': 'CACHE_STATE_BY_VAL', 'min': 17,'max':20}, ## Misc
					'TorID': {'table': None, 'min': 34,'max':38}, ## Misc
					'TorFSM': {'table': None, 'min': 50,'max':55}, ## Misc
					'SrcID': {'table': None, 'min': 29,'max':36}, ## Misc3
					'Attribute': {'table': 'SAD_ATTR_BY_VAL', 'min': 20,'max':21}, ## Misc3
					'Result': {'table': 'SAD_RESULT_BY_VAL', 'min': 26,'max':28}, ## Misc3
					'Local Port': {'table': 'TARGET_LOC_PORT_BY_VAL', 'min': 41,'max':47}, ## Misc3
					'ISMQ': {'table': 'ISMQ_FSM_BY_VAL', 'min': 54,'max':58}, ## Misc3
			}
		
		table = data[type]['table']
		mcmin = data[type]['min']
		mcmax = data[type]['max']
		
		# If nothing is found return empty string
		if value == '':
			return value
		
		extractedvalue = extract_bits(hex_value=value, min_bit=mcmin, max_bit=mcmax)

		if table != None: 
			mclist = cha_json[table]
			keyvalue = str(extractedvalue)
			
			# Check if value is in decode keys, if not, show N/A
			mc_value = mclist[str(extractedvalue)] if keyvalue in mclist.keys() else "N/A"
				
		else:
			mc_value = extractedvalue
		#files = 		['MSCOD_BY_VAL', 'CACHE_STATE_BY_VAL','ISMQ_FSM_BY_VAL','SAD_ATTR_BY_VAL','SAD_RESULT_BY_VAL','TARGET_LOC_PORT_BY_VAL', 'TOR_OPCODES_BY_VAL']
		
		### Orig Req	Opcode	cachestate	TorID	TorFSM	SrcID	ISMQ	Attribute	Result	Local Port
		
		return mc_value

	def llc(self):
		# LLC is included in the same bank as CHA for DMR
		if self.product == 'DMR':
			return pd.DataFrame()  # Return empty DataFrame for DMR (LLC is in CCF)
		
		mcdata = self.data
		
		# Check if required columns exist
		required_columns = ['VisualId', 'TestName']
		missing_columns = [col for col in required_columns if col not in mcdata.columns]
		if missing_columns:
			print(f' !!! ERROR: Missing required columns in MCA data: {missing_columns}')
			print(f' !!! Available columns: {list(mcdata.columns)}')
			print(' !!! Returning empty DataFrame. Please check your input Excel file structure.')
			return pd.DataFrame()
		
		# Initialize the new dataframe
		columns = ['VisualID', 'Run', 'Operation', 'LLC_MC', 'Compute', 'LLC', 'MC_STATUS', 'MC DECODE','MC_ADDR','MC_MISC', 'MiscV','RSF','LSF','LLC_misc']
		#new_df = pd.DataFrame(columns=columns)
		#decodelist = ['MC DECODE', 'Orig Req','Opcode','cachestate','TorID','TorFSM','SrcID','ISMQ','Attribute','Result','Local Port']
		
		# CHA List
		decodelistmc = ['MC DECODE','MiscV']
		decodelistmisc = ['RSF','LSF','LLC_misc']
		#decodelistmisc3 = ['SrcID','ISMQ','Attribute','Result','Local Port']

		data_dict = {k:[] for k in columns}
		
		for visual_id in mcdata['VisualId'].unique():

			# Split Data into required elements
			subset = mcdata[(mcdata['VisualId'] == visual_id) & (mcdata['TestName'].str.contains('LLC'))]

			# Further split into required lookup registers for each VID
			mc_filtered = self.extract_value(subset,'TestName', '__MCI_STATUS')# subset[(subset['TestName'].str.contains('UTIL__MC_STATUS'))] #self.extract_value(subset, 'UTIL__MC_STATUS')
			addr_filtered = self.extract_value(subset,'TestName', '__MCI_ADDR')# subset[subset['TestName'].str.contains('UTIL__MC_ADDR')]#self.extract_value(subset, 'UTIL__MC_ADDR')
			misc_filtered = self.extract_value(subset,'TestName', '__MCI_MISC')# subset[subset['TestName'].str.contains('UTIL__MC_MISC_')]#self.extract_value(subset, 'UTIL__MC_MISC_')
			#misc3_filtered = self.extract_value(subset,'TestName', 'UTIL__MC_MISC3_')# subset[subset['TestName'].str.contains('UTIL__MC_MISC3_')]#self.extract_value(subset, 'UTIL__MC_MISC3')
			
			# If no MCA is found move to the next VID
			try:
				if mc_filtered.empty:
					print(f' -- No MCA data found for LLCs in VID: {visual_id}')
					continue
			except:
				print(f' -- No MCA data found for LLCs in VID: {visual_id}')
				continue
			
			# This will iterate over all the MCAS to look for Address, Misc and MISC3 data for corresponding fail IP
			for i, data in mc_filtered.iterrows():
				
				# Build new
				data_dict['VisualID'] += [visual_id]
				LotsSeqKey = data['LotsSeqKey']
				UnitTestingSeqKey = data['UnitTestingSeqKey']
				compute =  re.search(r'COMPUTE(\d+)', data['TestName']).group(1) #data['TestName'].extract(r'COMPUTE(\d+)')
				llc = re.search(r'LLC(\d+)', data['TestName']).group(1)  #data['TestName'].extract(r'CHA(\d+)')
				operation = data['Operation']

				## Address lookup pattern
				addr_lut = self.lookup_pattern(compute=compute, location=llc, operation=operation, suffix="ADDR", ptype='llc')
				misc_lut = self.lookup_pattern(compute=compute, location=llc, operation=operation, suffix="MISC", ptype='llc')
				#misc3_lut = self.lookup_pattern(compute, cha, operation, suffix="MISC3")

				## MCA Lookup values
				mc_value = data['TestValue']
				addr_value = self.xlookup(lookup_array=addr_filtered, testname = addr_lut, LotsSeqKey = LotsSeqKey, UnitTestingSeqKey = UnitTestingSeqKey)
				misc_value = self.xlookup(lookup_array=misc_filtered, testname = misc_lut, LotsSeqKey = LotsSeqKey, UnitTestingSeqKey = UnitTestingSeqKey)
				#misc_value3 = self.xlookup(lookup_array=misc3_filtered, testname = misc3_lut, LotsSeqKey = LotsSeqKey, UnitTestingSeqKey = UnitTestingSeqKey)
				
				## Get Run Info
				run = str(LotsSeqKey) + "-" + str(UnitTestingSeqKey)	
				data_dict['Run'] += [run]
				data_dict['Operation'] += [str(operation)]
				data_dict['LLC_MC'] += [data['TestName'] ]
				data_dict['Compute'] += [compute]
				data_dict['LLC'] += [f'LLC{llc}']
				data_dict['MC_STATUS'] += [mc_value]
				data_dict['MC_ADDR'] += [addr_value]
				data_dict['MC_MISC'] += [misc_value]
				#data_dict['MC_MISC3'] += [misc_value3]
			
				### MCdecode Data
				### Cha decode Orig Req	Opcode	cachestate	TorID	TorFSM	SrcID	ISMQ	Attribute	Result	Local Port

				for dval in decodelistmc:
					data_dict[dval] += [self.llc_decoder(value=mc_value, type=dval)]
				
				for dval in decodelistmisc:
					data_dict[dval] += [self.llc_decoder(value=misc_value, type=dval)]
				
				#for dval in decodelistmisc3:
				#	data_dict[dval] += [self.cha_decoder(value=misc_value3, type=dval)]
		new_df = pd.DataFrame(data_dict)
		return new_df

	def llc_decoder(self, value, type):
		LLC =self.mcadata.llc_data
		data = { 	'MC DECODE': {'table': 'MSCOD_BY_VAL', 'min': 16,'max':31}, ## Status
					#'Orig Req': {'table': 'TOR_OPCODES_BY_VAL', 'min': 39,'max':49}, ## Misc
					#'Opcode': {'table': 'TOR_OPCODES_BY_VAL', 'min': 23,'max':33}, ## Misc
					#'cachestate': {'table': 'TOR_OPCODES_BY_VAL', 'min': 17,'max':20}, ## Misc
					'MiscV': {'table': None, 'min': 59,'max':59}, ## Status
					'RSF': {'table': None, 'min': 19,'max':24}, ## Misc
					'LSF': {'table': None, 'min': 14,'max':18}, ## Misc
					'LLC_misc': {'table': None, 'min': 9,'max':13}, ## Misc
					#'Attribute': {'table': 'SAD_ATTR_BY_VAL', 'min': 20,'max':21}, ## Misc3
					#'Result': {'table': 'SAD_RESULT_BY_VAL', 'min': 26,'max':28}, ## Misc3
					#'Local Port': {'table': 'TARGET_LOC_PORT_BY_VAL', 'min': 41,'max':47}, ## Misc3
					#'ISMQ': {'table': 'ISMQ_FSM_BY_VAL', 'min': 54,'max':58}, ## Misc3
			}
		
		table = data[type]['table']
		mcmin = data[type]['min']
		mcmax = data[type]['max']
		
		# If nothing is found return empty string
		if value == '':
			return value
		
		extractedvalue = extract_bits(hex_value=value, min_bit=mcmin, max_bit=mcmax)

		if table != None: 
			mclist = LLC[table]
			keyvalue = str(extractedvalue)
			
			# Check if value is in decode keys, if not, show N/A
			mc_value = mclist[str(extractedvalue)] if keyvalue in mclist.keys() else "N/A"
				
		else:
			mc_value = extractedvalue
		#files = 		['MSCOD_BY_VAL', 'CACHE_STATE_BY_VAL','ISMQ_FSM_BY_VAL','SAD_ATTR_BY_VAL','SAD_RESULT_BY_VAL','TARGET_LOC_PORT_BY_VAL', 'TOR_OPCODES_BY_VAL']
		
		### Orig Req	Opcode	cachestate	TorID	TorFSM	SrcID	ISMQ	Attribute	Result	Local Port
		
		return mc_value

	def sca(self):
		"""
		SCA (Scalable Caching Agent) decoder - Deprecated
		SCA was moved to mem() decoder for DMR (Bank 14)
		This method now returns empty DataFrame for backward compatibility
		"""
		# SCA is now part of mem() decoder for DMR
		return pd.DataFrame()  # Return empty DataFrame for all products

	def core(self):
		# Delegate to DMR core decoder if product is DMR
		if self.product == 'DMR':
			return self.dmr_decoder.core()
		
		coretype = self.coretype
		mcdata = self.data
		
		# Core MC Data / Addr / misc strings

		coredata = {'bigcore':{
								'mc':['ML2_CR_MC3_STATUS','IFU_CR_MC0_STATUS','DTLB_CR_MC2_STATUS','DCU_CR_MC1_STATUS'],
						 		'addr':['ML2_CR_MC3_ADDR','IFU_CR_MC0_ADDR','DTLB_CR_MC2_ADDR','DCU_CR_MC1_ADDR'],
								'misc':['ML2_CR_MC3_MISC','IFU_CR_MC0_MISC','DTLB_CR_MC2_MISC','DCU_CR_MC1_MISC'],	
								'errtype':['ML2', 'DCU', 'DTLB', 'IFU'],	
								'strcontain':'CPU__CORE',
								'strthreads':'THREAD',
								'keyword':'CORE',
								'columns':['VisualID', 'Run', 'Operation', 'CORE_MC', 'Compute', 'CORE', 'ErrorType', 'MC_STATUS', 'MCACOD (ErrDecode)', 'MSCOD','MC_ADDR','MC_MISC']

								},
					'atom':{
								'mc':['CR_MCI_STATUS'],
						 		'addr':['CR_MCI_ADDR'],
								'misc':['CR_MCI_MISC'],	
								'errtype':['BBL', 'BUS', 'MEC', 'IC', 'L2', 'AGU'],	
								'strcontain':'MODULE',
								'strthreads':'CORE',
								'keyword':'MODULE',
								'columns':['VisualID', 'Run', 'Operation', 'MODULE_MC', 'Compute', 'MODULE', 'ErrorType', 'MC_STATUS', 'MCACOD (ErrDecode)', 'MSCOD','MC_ADDR','MC_MISC']
								},
								}

		selected_core = coredata[coretype]
		# Initialize the new dataframe
		columns = selected_core['columns']#['VisualID', 'Run', 'Operation', 'CORE_MC', 'Compute', 'CORE', 'ErrorType', 'MC_STATUS', 'MCACOD (ErrDecode)', 'MSCOD','MC_ADDR','MC_MISC']
		keyword = selected_core['keyword']
		#new_df = pd.DataFrame(columns=columns)
		#decodelist = ['MC DECODE', 'Orig Req','Opcode','cachestate','TorID','TorFSM','SrcID','ISMQ','Attribute','Result','Local Port']
		
		# CHA List
		#decodelistmc = ['MC DECODE']
		#decodelistmisc = ['MiscV','RSF','LSF','LLC_misc']
		#decodelistmisc3 = ['SrcID','ISMQ','Attribute','Result','Local Port']
		
		data_dict = {k:[] for k in columns}
		
		for visual_id in mcdata['VisualId'].unique():

			# Split Data into required elements
			subset = mcdata[(mcdata['VisualId'] == visual_id) & (mcdata['TestName'].str.contains(selected_core['strcontain']))]

			# Further split into required lookup registers for each VID
			mc_filtered = self.extract_value(subset,'TestName', selected_core['mc'])# subset[(subset['TestName'].str.contains('UTIL__MC_STATUS'))] #self.extract_value(subset, 'UTIL__MC_STATUS')
			addr_filtered = self.extract_value(subset,'TestName', selected_core['addr'])# subset[subset['TestName'].str.contains('UTIL__MC_ADDR')]#self.extract_value(subset, 'UTIL__MC_ADDR')
			misc_filtered = self.extract_value(subset,'TestName', selected_core['misc'])# subset[subset['TestName'].str.contains('UTIL__MC_MISC_')]#self.extract_value(subset, 'UTIL__MC_MISC_')
			#misc3_filtered = self.extract_value(subset,'TestName', 'UTIL__MC_MISC3_')# subset[subset['TestName'].str.contains('UTIL__MC_MISC3_')]#self.extract_value(subset, 'UTIL__MC_MISC3')
			
			# If no MCA is found move to the next VID
			try:
				if mc_filtered.empty:
					print(f' -- No MCA data found for {keyword}s ML2 in VID: {visual_id}')
					continue
			except:
				print(f' -- No MCA data found for {keyword}s ML2 in VID: {visual_id}')
				continue
			
			# This will iterate over all the MCAS to look for Address, Misc and MISC3 data for corresponding fail IP
			for i, data in mc_filtered.iterrows():
				
				# Build new
				data_dict['VisualID'] += [visual_id]
				LotsSeqKey = data['LotsSeqKey']
				UnitTestingSeqKey = data['UnitTestingSeqKey']
				compute =  re.search(r'COMPUTE(\d+)', data['TestName']).group(1) #data['TestName'].extract(r'COMPUTE(\d+)')
				core = re.search(rf'{selected_core["strcontain"]}(\d+)', data['TestName']).group(1)  #data['TestName'].extract(r'CHA(\d+)')
				operation = data['Operation']
				thread =re.search(rf'{selected_core["strthreads"]}(\d+)', data['TestName']).group(1) if f'{selected_core["strthreads"]}' in data['TestName'] else ''
				## Address lookup pattern
				
				ErroTypes = selected_core["errtype"]
				for err in ErroTypes:
					if err in data['TestName']:
						data_dict['ErrorType'] += [err]
						break
					#else: data_dict['ErrorType'] += ['']
				
				addr_lut = self.lookup_pattern(compute=compute, location=core, operation=operation, suffix="ADDR", thread=thread, ptype=f'core_{err.lower()}')
				misc_lut = self.lookup_pattern(compute=compute, location=core, operation=operation, suffix="MISC", thread=thread, ptype=f'core_{err.lower()}')
				#misc3_lut = self.lookup_pattern(compute, cha, operation, suffix="MISC3")

				## MCA Lookup values
				mc_value = data['TestValue']
				addr_value = self.xlookup(lookup_array=addr_filtered, testname = addr_lut, LotsSeqKey = LotsSeqKey, UnitTestingSeqKey = UnitTestingSeqKey)
				misc_value = self.xlookup(lookup_array=misc_filtered, testname = misc_lut, LotsSeqKey = LotsSeqKey, UnitTestingSeqKey = UnitTestingSeqKey)
				#misc_value3 = self.xlookup(lookup_array=misc3_filtered, testname = misc3_lut, LotsSeqKey = LotsSeqKey, UnitTestingSeqKey = UnitTestingSeqKey)
				
				## Get Run Info
				run = str(LotsSeqKey) + "-" + str(UnitTestingSeqKey)	
				data_dict['Run'] += [run]
				data_dict['Operation'] += [str(operation)]
				data_dict[f'{keyword}_MC'] += [data['TestName'] ]
				data_dict['Compute'] += [compute]
				data_dict[f'{keyword}'] += [f'{keyword}{core}']
				data_dict['MC_STATUS'] += [mc_value]
				data_dict['MC_ADDR'] += [addr_value]
				data_dict['MC_MISC'] += [misc_value]
				#data_dict['MC_MISC3'] += [misc_value3]
			
				### MCdecode Data
				### Cha decode Orig Req	Opcode	cachestate	TorID	TorFSM	SrcID	ISMQ	Attribute	Result	Local Port

				'''Decode List to be added later'''
				mcacod, mscod = self.core_decoder(value = mc_value, type= err)
				data_dict['MCACOD (ErrDecode)'] += [mcacod]
				data_dict['MSCOD'] += [mscod]
				#for dval in decodelistmc:

		new_df = pd.DataFrame(data_dict)
		return new_df

	def core_decoder(self, value, type):
		mcacod = ''
		mscod = ''
		mln = ['DCU', 'DTLB', 'IFU']
		if type == 'ML2':
			mcacod, mscod = self.core_ml2(value = value)
		elif type in mln:
			mcacod, mscod = self.core_mln(value = value, bank = type)		
		return mcacod, mscod

	def core_mln(self, value, bank = 'DCU'):
    
		core_json =self.mcadata.core_data
		data = { 	'MC DECODE': {'table': 'MCACOD', 'min': 0,'max':15}, ## Status
					'MSCOD': {'table': 'MSCOD', 'min': 16,'max':31},
					'PCC': {'table': 'PCC', 'min': 57,'max':57}, ## Misc

			}
		
		
		tablemc = data['MC DECODE']['table']
		mcminmc = data['MC DECODE']['min']
		mcmaxmc = data['MC DECODE']['max']

		tablems = data['MSCOD']['table']
		mcminms = data['MSCOD']['min']
		if bank == 'DCU': mcmaxms = data['MSCOD']['max']
		else: mcmaxms = 23 ## Only use first 8 bits

		#tablepcc = data['MSCOD']['table']
		pcccmin = data['PCC']['min']
		pccmax = data['PCC']['max']

		# If nothing is found return empty string
		if value == '':
			return value
		
		extractedvaluepcc = extract_bits(hex_value=value, min_bit=pcccmin, max_bit=pccmax)
		extractedvaluemc = extract_bits(hex_value=value, min_bit=mcminmc, max_bit=mcmaxmc)
		extractedvaluems = extract_bits(hex_value=value, min_bit=mcminms, max_bit=mcmaxms)
		
		DCUMSCodes = [k for k in core_json[bank][tablems].keys()]
		mclist = None
		if str(extractedvaluems) in DCUMSCodes:
			mclist = core_json[bank][tablems][str(extractedvaluems)][tablemc]
		else:
			mskey = find_matching_key(hex_value=extractedvaluems, dictionary=DCUMSCodes)
			if mskey != None:
				mclist = core_json[bank][tablems][mskey][tablemc]
		
		
		if mclist != None: 
			#mclist = core_json['DCU'][tablemc]
			keyvalue = str(extractedvaluemc)
			
			# Check if value is in decode keys, if not, show N/A
			mc_dict = mclist[str(extractedvaluemc)] if keyvalue in mclist.keys() else "N/A"
			if mc_dict != "N/A":
				usepcc = ''
				if "Name0" in mc_dict.keys():
					usepcc = extractedvaluepcc
				mc_name = mc_dict[f'Name{usepcc}']
				mc_desc = mc_dict[f'Description{usepcc}']
				mc_value = f'{mc_name}'
			else:
				mc_value = extractedvaluemc
				
		else:
			mc_value = extractedvaluemc
		
		ms_value = extractedvaluems

		return mc_value, ms_value
	
	def core_ml2(self, value):
		
		core_json =self.mcadata.core_data

		data = { 	'MC DECODE': {'table': 'MCACOD', 'min': 0,'max':11}, ## Status IS UP TO 12, but for decoding purposes we only check the first 12 bits
					'MSCOD': {'table': 'MSCOD', 'min': 16,'max':31}, ## Misc

			}
		
		
		tablemc = data['MC DECODE']['table']
		mcminmc = data['MC DECODE']['min']
		mcmaxmc = data['MC DECODE']['max']

		tablems = data['MSCOD']['table']
		mcminms = data['MSCOD']['min']
		mcmaxms = data['MSCOD']['max']

		# If nothing is found return empty string
		if value == '':
			return value
		
		extractedvaluemc = extract_bits(hex_value=value, min_bit=mcminmc, max_bit=mcmaxmc)
		extractedvaluems = hex(extract_bits(hex_value=value, min_bit=mcminms, max_bit=mcmaxms))

		if tablemc != None: 
			mclist = core_json['ML2'][tablemc]
			keyvalue = str(extractedvaluemc)
			
			# Check if value is in decode keys, if not, show N/A
			mc_dict = mclist[str(extractedvaluemc)] if keyvalue in mclist.keys() else "N/A"
			if mc_dict != "N/A":
				mc_name = mc_dict['Name']
				mc_desc = mc_dict['Description']
				mc_value = f'{mc_name}'
			else:
				mc_value = extractedvaluemc
				
		else:
			mc_value = extractedvaluemc
		
		if tablems != None: 
			mslist = core_json['ML2'][tablems]
			keyvalue = str(extractedvaluems)
			
			# Check if value is in decode keys, if not, show N/A
			ms_dict = mslist['type'] #mclist[str(extractedvaluems)] if keyvalue in mslist.keys() else "N/A"
			#ms_name = mc_dict['Name']
			#ms_desc = mc_dict['Description']
			#mc_value = f'P{mc_name}'
			ms_value = ''
			
			if extractedvaluemc == 1024:
				ms_wd = ms_dict['MLC']
				for k in ms_wd.keys():
					decdata = extract_bits(hex_value=extractedvaluems, min_bit=ms_wd[k]['min'], max_bit=ms_wd[k]['max'])
					ms_value += f'{k}:{decdata},'
			elif extractedvaluems == 1038:
				decdata = "Check Misc"
			
			else:
				ms_others = ms_dict['Others']
				for k in ms_others.keys():
					decdata = extract_bits(hex_value=extractedvaluems, min_bit=ms_others[k]['min'], max_bit=ms_others[k]['max'])
					ms_value += f'{k}:{ms_others[k]["decode"][str(decdata)], }'
				
		else:
			ms_value = extractedvaluems
		#files = 		['MSCOD_BY_VAL', 'CACHE_STATE_BY_VAL','ISMQ_FSM_BY_VAL','SAD_ATTR_BY_VAL','SAD_RESULT_BY_VAL','TARGET_LOC_PORT_BY_VAL', 'TOR_OPCODES_BY_VAL']
		
		### Orig Req	Opcode	cachestate	TorID	TorFSM	SrcID	ISMQ	Attribute	Result	Local Port
		
		return mc_value, ms_value

	def portids(self):
		
		mcdata = self.data
		# Initialize the new dataframe
		columns = ['VisualID', 'Run', 'Operation', 'NCEVENT', 'VALUE', 'FirstError - DIEID', 'FirstError - PortID', 'FirstError - Location', 'FirstError - FromCore', 'SecondError - DIEID', 'SecondError - PortID', 'SecondError - Location', 'SecondError - FromCore']

		# UBOX List
		portid_data = ['FirstError - DIEID', 'FirstError - PortID', 'FirstError - Location', 'FirstError - FromCore', 'SecondError - DIEID', 'SecondError - PortID', 'SecondError - Location', 'SecondError - FromCore']
		#decodelistmisc = ['RSF','LSF','LLC_misc']
		#decodelistmisc3 = ['SrcID','ISMQ','Attribute','Result','Local Port']

		data_dict = {k:[] for k in columns}
		
		for visual_id in mcdata['VisualId'].unique():

			# Split Data into required elements
			subset = mcdata[(mcdata['VisualId'] == visual_id) & (mcdata['TestName'].str.contains('UBOX'))]

			# Further split into required lookup registers for each VID
			mcerrorlog = self.extract_value(subset,'TestName', '__MCERRLOGGINGREG')# subset[(subset['TestName'].str.contains('UTIL__MC_STATUS'))] #self.extract_value(subset, 'UTIL__MC_STATUS')
			ierrorlog = self.extract_value(subset,'TestName', '__IERRLOGGINGREG')# subset[subset['TestName'].str.contains('UTIL__MC_ADDR')]#self.extract_value(subset, 'UTIL__MC_ADDR')
			#misc_filtered = self.extract_value(subset,'TestName', '__MCI_MISC')# subset[subset['TestName'].str.contains('UTIL__MC_MISC_')]#self.extract_value(subset, 'UTIL__MC_MISC_')
			#misc3_filtered = self.extract_value(subset,'TestName', 'UTIL__MC_MISC3_')# subset[subset['TestName'].str.contains('UTIL__MC_MISC3_')]#self.extract_value(subset, 'UTIL__MC_MISC3')
			
			# If no MCA is found move to the next VID
			try:
				portidData = pd.concat([mcerrorlog, ierrorlog])
				if portidData.empty:
					print(f' -- No NCEVENT data found in VID: {visual_id}')
					continue
			except:
				print(f' -- No NCEVENT data found in VID: {visual_id}')
				continue
			
			# This will iterate over all the MCAS to look for Address, Misc and MISC3 data for corresponding fail IP
			for i, data in portidData.iterrows():
				
				# Build new
				data_dict['VisualID'] += [visual_id]
				LotsSeqKey = data['LotsSeqKey']
				UnitTestingSeqKey = data['UnitTestingSeqKey']
				#compute =  re.search(r'IO(\d+)', data['TestName']).group(1) #data['TestName'].extract(r'COMPUTE(\d+)')
				#llc = re.search(r'LLC(\d+)', data['TestName']).group(1)  #data['TestName'].extract(r'CHA(\d+)')
				operation = data['Operation']

				## Address lookup pattern
				#mcelog = self.lookup_pattern(compute='IO0', location='UBOX', operation=operation, suffix="MCERRLOGGINGREG", ptype='ubox')
				#ierrlog = self.lookup_pattern(compute='IO0', location='UBOX', operation=operation, suffix="IERRLOGGINGREG", ptype='ubox')
				#misc3_lut = self.lookup_pattern(compute, cha, operation, suffix="MISC3")

				## MCA Lookup values
				value = data['TestValue']
				name = data['TestName']
				#mcelog_value = self.xlookup(lookup_array=mcerrorlog, testname = mcelog, LotsSeqKey = LotsSeqKey, UnitTestingSeqKey = UnitTestingSeqKey)
				#ierrlog_value = self.xlookup(lookup_array=ierrorlog, testname = ierrlog, LotsSeqKey = LotsSeqKey, UnitTestingSeqKey = UnitTestingSeqKey)
				#misc_value3 = self.xlookup(lookup_array=misc3_filtered, testname = misc3_lut, LotsSeqKey = LotsSeqKey, UnitTestingSeqKey = UnitTestingSeqKey)
				
				## Get Run Info
				run = str(LotsSeqKey) + "-" + str(UnitTestingSeqKey)	
				data_dict['Run'] += [run]
				data_dict['Operation'] += [str(operation)]
				data_dict['NCEVENT'] += [name]
				#data_dict['ORIGIN'] += 'UBOX'
				#data_dict['LLC'] += [f'LLC{llc}']
				data_dict['VALUE'] += [value]
				#data_dict['MC_ADDR'] += [addr_value]
				#data_dict['MC_MISC'] += [misc_value]
				#data_dict['MC_MISC3'] += [misc_value3]
			
				### MCdecode Data
				### Cha decode Orig Req	Opcode	cachestate	TorID	TorFSM	SrcID	ISMQ	Attribute	Result	Local Port

				
				if 'MCERRLOGGINGREG' in name: portids_values = self.portids_decoder(value=value, portid_data=portid_data, event='mcerr')
				if 'IERRLOGGINGREG' in name: portids_values = self.portids_decoder(value=value, portid_data=portid_data, event='ierr')
				
				for k,v in portids_values.items():
					data_dict[k] += [v]
				#for dval in decodelistmisc:
				#	data_dict[dval] += [self.llc_decoder(value=misc_value, type=dval)]
				
				#for dval in decodelistmisc3:
				#	data_dict[dval] += [self.cha_decoder(value=misc_value3, type=dval)]
		new_df = pd.DataFrame(data_dict)
		return new_df

	def portids_decoder(self, value, portid_data, event):
		#portid_data = ['DIE_TYPE', 'DIE SEGMENT', 'TYPE', 'DEVICE','PORT ID (11 bits LSB)','DIE ID(5 bits MSB)']	
		portids_json =self.mcadata.portid_data

		data = { 	'firstierrsrcid': {'table': None, 'min': 0,'max':15}, 
		  			'firstmcerrsrcid': {'table': None, 'min': 0,'max':15}, 
					'firstierrsrcvalid': {'table': None, 'min': 16,'max':16}, 
					'firstmcerrsrcvalid': {'table': None, 'min': 16,'max':16}, 
					'firstierrsrcfromcore': {'table': None, 'min': 17,'max':17}, 
					'firstmcerrsrcfromcore': {'table': None, 'min': 17,'max':17}, 
					'secondierrsrcid': {'table': None, 'min': 32,'max':47}, 
		  			'secondmcerrsrcid': {'table': None, 'min': 32,'max':47}, 
					'secondierrsrcvalid': {'table': None, 'min': 48,'max':48}, 
					'secondmcerrsrcvalid': {'table': None, 'min': 48,'max':48}, 
					'secondierrsrcfromcore': {'table': None, 'min': 49,'max':49}, 
					'secondmcerrsrcfromcore': {'table': None, 'min': 49,'max':49}, 

			}
		first = data[f'first{event}srcid']
		first_valid = data[f'first{event}srcvalid']
		first_core = data[f'first{event}srcfromcore']

		second = data[f'second{event}srcid']
		second_valid = data[f'second{event}srcvalid']
		second_core = data[f'second{event}srcfromcore']

		portids_value = {k:'' for k in portid_data}

		# If nothing is found return empty string
		if value == '':
			return value
		
		#firstvalue = hex(extract_bits(hex_value=value, min_bit=first['min'], max_bit=first['max'])).replace("0x","").upper()
		firstvalue = str(extract_bits(hex_value=value, min_bit=first['min'], max_bit=first['max']))
		firstvalid = extract_bits(hex_value=value, min_bit=first_valid['min'], max_bit=first_valid['max'])
		firstcore = extract_bits(hex_value=value, min_bit=first_core['min'], max_bit=first_core['max'])
		firstportid =  extract_bits(hex_value=value, min_bit=0, max_bit=10)
		firstdieid =  extract_bits(hex_value=value, min_bit=11, max_bit=15)

		#secondvalue =  hex(extract_bits(hex_value=value, min_bit=second['min'], max_bit=second['max'])).replace("0x","").upper()
		secondvalue =  str(extract_bits(hex_value=value, min_bit=second['min'], max_bit=second['max']))
		secondvalid = extract_bits(hex_value=value, min_bit=second_valid['min'], max_bit=second_valid['max'])
		secondcore = extract_bits(hex_value=value, min_bit=second_core['min'], max_bit=second_core['max'])
		secondportid =  extract_bits(hex_value=value, min_bit=32, max_bit=42)
		seconddieid =  extract_bits(hex_value=value, min_bit=43, max_bit=47)

		portids = portids_json

		
		for v in portids_value.keys():
			if firstvalid == 1:
				if v == 'FirstError - DIEID': portids_value[v] = firstdieid#portids[firstvalue][0]['DIE ID(5 bits MSB)']
				if v == 'FirstError - PortID': portids_value[v] = firstportid#portids[firstvalue][0]['PORT ID (11 bits LSB)']
				if v == 'FirstError - Location': portids_value[v] = portids[firstvalue]  		
				if v == 'FirstError - FromCore': portids_value[v] = firstcore   
			if secondvalid == 1:
				if v == 'SecondError - DIEID': portids_value[v] = seconddieid#portids[secondvalue][0]['DIE ID(5 bits MSB)']
				if v == 'SecondError - PortID': portids_value[v] = secondportid#portids[secondvalue][0]['PORT ID (11 bits LSB)']
				if v == 'SecondError - Location': portids_value[v] = portids[secondvalue]
				if v == 'SecondError - FromCore': portids_value[v] = secondcore

		return portids_value

	def mem(self):
		"""
		Memory Controller MCA decoder for MSE, MCCHAN (iMC), and B2CMI
		Extracts instance name, MCACOD (numeric), and MC_DECODE (MSCOD value from JSON)
		Similar structure to LLC decoder

		Register path patterns:
		- B2CMI: SOCKET0__SOC__MEMSS__B2CMI{n}__MCI_STATUS
		- MCCHAN: SOCKET0__SOC__MEMSS__MC{n}__CH{n}__MCCHAN__IMC0_MC_STATUS
		- MSE: SOCKET0__SOC__MEMSS__MC{n}__CH{n}__MSE__MSE_MCI_STATUS
		"""
		# Delegate to DMR memory decoder if product is DMR
		if self.product == 'DMR':
			return self.dmr_decoder.mem()
		
		mcdata = self.data
		
		# Check if required columns exist
		required_columns = ['VisualId', 'TestName']
		missing_columns = [col for col in required_columns if col not in mcdata.columns]
		if missing_columns:
			print(f' !!! ERROR: Missing required columns in MCA data: {missing_columns}')
			print(f' !!! Available columns: {list(mcdata.columns)}')
			print(' !!! Returning empty DataFrame. Please check your input Excel file structure.')
			return pd.DataFrame()
		
		# Initialize the new dataframe - Added Type column
		columns = ['VisualID', 'Run', 'Operation', 'Type', 'MEM_MC', 'Instance', 'MC_STATUS', 'MCACOD', 'MC_DECODE', 'MC_ADDR', 'MC_MISC']
		
		data_dict = {k:[] for k in columns}
		
		# Memory subsystem patterns - looking for MSE, MCCHAN (iMC), and B2CMI
		mem_patterns = ['MSE', 'MCCHAN', 'B2CMI', 'IMC']
		
		for visual_id in mcdata['VisualId'].unique():
			# Split Data into required elements
			subset = mcdata[(mcdata['VisualId'] == visual_id)]
			
			# Filter for memory-related MCAs
			mem_filtered = pd.DataFrame()
			for pattern in mem_patterns:
				#print(pattern)
				pattern_data = self.extract_value(subset, 'TestName', pattern)
				#print(pattern_data)
				if not pattern_data.empty:
					mem_filtered = pd.concat([mem_filtered, pattern_data], ignore_index=True)
			
			# Check if mem_filtered has data and required column before proceeding
			if mem_filtered.empty or 'TestName' not in mem_filtered.columns:
				print(f' -- No Memory MCA data found in VID: {visual_id}')
				continue
			
			# Further filter for STATUS registers
			mc_filtered = self.extract_value(mem_filtered, 'TestName', '_STATUS|_MC_STATUS|_MCI_STATUS')
			
			# If no MCA is found move to the next VID
			if mc_filtered.empty:
				print(f' -- No Memory MCA STATUS registers found in VID: {visual_id}')
				continue
			
			# This will iterate over all the Memory MCAs
			for i, data in mc_filtered.iterrows():
				# Build new entry
				data_dict['VisualID'] += [visual_id]
				LotsSeqKey = data['LotsSeqKey']
				UnitTestingSeqKey = data['UnitTestingSeqKey']
				operation = data['Operation']
				test_name = data['TestName']
				mc_value = data['TestValue']
				
				# Extract instance information and type from the register path
				# Patterns: SOCKET0__SOC__MEMSS__B2CMI8__MCI_STATUS
				#           SOCKET0__SOC__MEMSS__MC0__CH0__MCCHAN__IMC0_MC_STATUS
				#           SOCKET0__SOC__MEMSS__MC0__CH0__MSE__MSE_MCI_STATUS
				
				instance = ''
				mem_type = ''
				mc_num = ''
				ch_num = ''
				b2cmi_num = ''
				imc_num = ''
				
				# Extract MC and CH numbers
				mc_match = re.search(r'__MC(\d+)__', test_name)
				ch_match = re.search(r'__CH(\d+)__', test_name)
				
				if 'B2CMI' in test_name:
					mem_type = 'B2CMI'
					# Extract B2CMI instance number
					b2cmi_match = re.search(r'B2CMI(\d+)', test_name)
					if b2cmi_match:
						b2cmi_num = b2cmi_match.group(1)
						instance = f'B2CMI{b2cmi_num}'
					else:
						instance = 'B2CMI'
						
				elif 'MSE' in test_name:
					mem_type = 'MSE'
					# MSE: indicate MC#CH#
					if mc_match and ch_match:
						mc_num = mc_match.group(1)
						ch_num = ch_match.group(1)
						instance = f'MC{mc_num}CH{ch_num}'
					else:
						instance = 'MSE'
						
				elif 'MCCHAN' in test_name or 'IMC' in test_name:
					mem_type = 'MCCHAN'
					# MCCHAN: indicate MC#CH#IMC#
					imc_match = re.search(r'IMC(\d+)', test_name)
					if mc_match and ch_match:
						mc_num = mc_match.group(1)
						ch_num = ch_match.group(1)
						if imc_match:
							imc_num = imc_match.group(1)
							instance = f'MC{mc_num}CH{ch_num}IMC{imc_num}'
						else:
							instance = f'MC{mc_num}CH{ch_num}'
					elif imc_match:
						imc_num = imc_match.group(1)
						instance = f'IMC{imc_num}'
					else:
						instance = 'iMC'
				
				# Extract MCACOD (bits 15:0) from MC_STATUS
				mcacod = extract_bits(hex_value=mc_value, min_bit=0, max_bit=15)
				
				# Decode MSCOD based on memory type
				mc_decode = self.mem_decoder(value=mc_value, instance_type=mem_type)
				
				# Look up ADDR and MISC registers using lookup patterns
				addr_value = ''
				misc_value = ''
				
				# Build lookup patterns based on memory type
				if mem_type == 'B2CMI':
					# Pattern: SOCKET0__SOC__MEMSS__B2CMI{n}__MCI_ADDR
					addr_lut = self.mem_lookup_pattern(mc=mc_num, ch=ch_num, b2cmi=b2cmi_num, 
					                                   imc=imc_num, suffix='ADDR', ptype='b2cmi')
					misc_lut = self.mem_lookup_pattern(mc=mc_num, ch=ch_num, b2cmi=b2cmi_num, 
					                                   imc=imc_num, suffix='MISC', ptype='b2cmi')
				elif mem_type == 'MSE':
					# Pattern: SOCKET0__SOC__MEMSS__MC{n}__CH{n}__MSE__MSE_MCI_ADDR
					addr_lut = self.mem_lookup_pattern(mc=mc_num, ch=ch_num, b2cmi=b2cmi_num, 
					                                   imc=imc_num, suffix='ADDR', ptype='mse')
					misc_lut = self.mem_lookup_pattern(mc=mc_num, ch=ch_num, b2cmi=b2cmi_num, 
					                                   imc=imc_num, suffix='MISC', ptype='mse')
				elif mem_type == 'MCCHAN':
					# Pattern: SOCKET0__SOC__MEMSS__MC{n}__CH{n}__MCCHAN__IMC0_MC8_ADDR
					# Note: ADDR register for MCCHAN is IMC0_MC8_ADDR (different from STATUS)
					addr_lut = self.mem_lookup_pattern(mc=mc_num, ch=ch_num, b2cmi=b2cmi_num, 
					                                   imc=imc_num, suffix='ADDR', ptype='mcchan')
					misc_lut = self.mem_lookup_pattern(mc=mc_num, ch=ch_num, b2cmi=b2cmi_num, 
					                                   imc=imc_num, suffix='MISC', ptype='mcchan')
				else:
					addr_lut = ''
					misc_lut = ''
				
				# Use xlookup to find corresponding ADDR and MISC values
				if addr_lut:
					addr_value = self.xlookup(lookup_array=mem_filtered, testname=addr_lut, 
					                         LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)
				if misc_lut:
					misc_value = self.xlookup(lookup_array=mem_filtered, testname=misc_lut, 
					                         LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)
				
				# Get Run Info
				run = str(LotsSeqKey) + "-" + str(UnitTestingSeqKey)
				data_dict['Run'] += [run]
				data_dict['Operation'] += [str(operation)]
				data_dict['Type'] += [mem_type]
				data_dict['MEM_MC'] += [test_name]
				data_dict['Instance'] += [instance]
				data_dict['MCACOD'] += [hex(mcacod)]
				data_dict['MC_DECODE'] += [mc_decode]
				data_dict['MC_STATUS'] += [mc_value]
				data_dict['MC_ADDR'] += [addr_value]
				data_dict['MC_MISC'] += [misc_value]
		
		new_df = pd.DataFrame(data_dict)
		return new_df

	def mem_decoder(self, value, instance_type):
		"""
		Decode Memory MCA MSCOD based on instance type and JSON configuration
		Uses JSON data loaded from mcadata class

		Args:
			value: MC_STATUS register value (hex string)
			instance_type: Type of memory instance (MSE, MCCHAN, B2CMI)

		Returns:
			Decoded MSCOD string from JSON or raw value
		"""
		if value == '' or value is None:
			return ''
		
		try:
			# Extract MSCOD (bits 31:16) from MC_STATUS
			mscod = extract_bits(hex_value=value, min_bit=16, max_bit=31)
			
			# Select appropriate JSON data from mcadata based on instance type
			mem_json = None
			if 'MSE' in instance_type:
				mem_json = self.mcadata.mse_data
			elif 'MCCHAN' in instance_type:
				mem_json = self.mcadata.mcchnl_data
			elif 'B2CMI' in instance_type:
				mem_json = self.mcadata.b2cmi_data
			
			# Look up MSCOD in the JSON
			if mem_json and 'MSCOD' in mem_json:
				mscod_str = str(mscod)
				if mscod_str in mem_json['MSCOD']:
					return f"{mem_json['MSCOD'][mscod_str]} (MSCOD={mscod})"
				else:
					return f"Unknown MSCOD={mscod}"
			else:
				return f"MSCOD={mscod}"
		
		except Exception as e:
			return f"Decode error: {str(e)}"

	def io(self):
		"""
		IO MCA decoder for UBOX and UPI registers
		Extracts instance name, IO#, MCACOD (numeric), and MC_DECODE (MSCOD from JSON or raw value)

		Register path patterns:
		- UBOX: sv.sockets.io0.uncore.ubox.ncevents.ncevents_cr_ubox_mci_status
		- UPI: sv.sockets.io0.uncore.upi.upi0.upi_regs.kti_mc_st
		"""
		# Delegate to DMR IO decoder if product is DMR
		if self.product == 'DMR':
			return self.dmr_decoder.io()
		
		mcdata = self.data
		
		# Check if required columns exist
		required_columns = ['VisualId', 'TestName']
		missing_columns = [col for col in required_columns if col not in mcdata.columns]
		if missing_columns:
			print(f' !!! ERROR: Missing required columns in MCA data: {missing_columns}')
			print(f' !!! Available columns: {list(mcdata.columns)}')
			print(' !!! Returning empty DataFrame. Please check your input Excel file structure.')
			return pd.DataFrame()
		
		# Initialize the new dataframe - Added IO# column
		columns = ['VisualID', 'Run', 'Operation', 'Type', 'IO_MC', 'IO', 'MC_STATUS', 'Instance', 'MCACOD', 'MC_DECODE', 'MC_ADDR', 'MC_MISC']
		
		data_dict = {k:[] for k in columns}
		
		# IO subsystem patterns - looking for UBOX and UPI
		io_patterns = ['UBOX', 'UPI']
		
		for visual_id in mcdata['VisualId'].unique():
			# Split Data into required elements
			subset = mcdata[(mcdata['VisualId'] == visual_id)]
			
			# Filter for IO-related MCAs
			io_filtered = pd.DataFrame()
			for pattern in io_patterns:
				pattern_data = self.extract_value(subset, 'TestName', pattern)
				if not pattern_data.empty:
					io_filtered = pd.concat([io_filtered, pattern_data], ignore_index=True)
			
			# Check if io_filtered has data and required column before proceeding
			if io_filtered.empty or 'TestName' not in io_filtered.columns:
				print(f' -- No IO MCA data found in VID: {visual_id}')
				continue
			
			# Further filter for STATUS registers
			mc_filtered = self.extract_value(io_filtered, 'TestName', '_STATUS|_MC_STATUS|_MCI_STATUS|_MC_ST')
			
			# If no MCA is found move to the next VID
			if mc_filtered.empty:
				print(f' -- No IO MCA STATUS registers found in VID: {visual_id}')
				continue
			
			# This will iterate over all the IO MCAs
			for i, data in mc_filtered.iterrows():
				# Build new entry
				data_dict['VisualID'] += [visual_id]
				LotsSeqKey = data['LotsSeqKey']
				UnitTestingSeqKey = data['UnitTestingSeqKey']
				operation = data['Operation']
				test_name = data['TestName']
				mc_value = data['TestValue']
				
				# Extract instance information and type from the register path
				# Patterns: IO0__UNCORE__UBOX__NCEVENTS__NCEVENTS_CR_UBOX_MCI_STATUS
				#           IO0__UNCORE__UPI__UPI0__UPI_REGS__KTI_MC_ST
				
				instance = ''
				io_type = ''
				io_num = ''
				upi_num = ''
				
				# Extract IO number
				io_match = re.search(r'IO(\d+)', test_name, re.IGNORECASE)
				if io_match:
					io_num = io_match.group(1)
				
				if 'UBOX' in test_name:
					io_type = 'UBOX'
					instance = 'UBOX'
					
				elif 'UPI' in test_name:
					io_type = 'UPI'
					# Extract UPI instance number
					upi_match = re.search(r'UPI(\d+)', test_name, re.IGNORECASE)
					if upi_match:
						upi_num = upi_match.group(1)
						instance = f'UPI{upi_num}'
				else:
					instance = 'UPI'
				
				# Decode both MCACOD and MSCOD using io_decoder
				mcacod_decoded, mscod_decoded = self.io_decoder(value=mc_value, instance_type=io_type)
				
				# Look up ADDR and MISC registers using lookup patterns
				addr_value = ''
				misc_value = ''
				
				# Build lookup patterns based on IO type
				if io_type == 'UBOX':
					# Pattern: IO0__UNCORE__UBOX__NCEVENTS__NCEVENTS_CR_UBOX_MCI_ADDR
					addr_lut = self.io_lookup_pattern(io=io_num, upi=upi_num, suffix='ADDR', ptype='ubox')
					misc_lut = self.io_lookup_pattern(io=io_num, upi=upi_num, suffix='MISC', ptype='ubox')
				elif io_type == 'UPI':
					# Pattern: IO0__UNCORE__UPI__UPI0__UPI_REGS__KTI_MC_ADDR
					addr_lut = self.io_lookup_pattern(io=io_num, upi=upi_num, suffix='ADDR', ptype='upi')
					misc_lut = self.io_lookup_pattern(io=io_num, upi=upi_num, suffix='MISC', ptype='upi')
				else:
					addr_lut = ''
					misc_lut = ''
				
				# Use xlookup to find corresponding ADDR and MISC values
				if addr_lut:
					addr_value = self.xlookup(lookup_array=io_filtered, testname=addr_lut, 
					                         LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)
				if misc_lut:
					misc_value = self.xlookup(lookup_array=io_filtered, testname=misc_lut, 
					                         LotsSeqKey=LotsSeqKey, UnitTestingSeqKey=UnitTestingSeqKey)
				
				# Get Run Info
				run = str(LotsSeqKey) + "-" + str(UnitTestingSeqKey)
				data_dict['Run'] += [run]
				data_dict['Operation'] += [str(operation)]
				data_dict['Type'] += [io_type]
				data_dict['IO_MC'] += [test_name]
				data_dict['IO'] += [f'IO{io_num}' if io_num else '']
				data_dict['Instance'] += [instance]
				data_dict['MCACOD'] += [mcacod_decoded]
				data_dict['MC_DECODE'] += [mscod_decoded]
				data_dict['MC_STATUS'] += [mc_value]
				data_dict['MC_ADDR'] += [addr_value]
				data_dict['MC_MISC'] += [misc_value]
		
		new_df = pd.DataFrame(data_dict)
		return new_df

	def io_decoder(self, value, instance_type):
		"""
		Decode IO MCA MCACOD and MSCOD based on instance type and JSON configuration
		Uses JSON data loaded from mcadata class for UPI and UBOX

		Special handling for UBOX based on MCACOD:
		- MCACOD 1042 (SCF Bridge IP:CMS error): Use CMS_MSCOD table
		- MCACOD 1043 (SCF Bridge IP:SBO error): Use SBO_MSCOD table
		- MCACOD 1036 (Shutdown suppression): Use SHUTDOWN_ERR_MSCOD table

		Args:
			value: MC_STATUS register value (hex string)
			instance_type: Type of IO instance (UBOX, UPI)

		Returns:
			Tuple of (mcacod_decoded, mscod_decoded) strings
		"""
		if value == '' or value is None:
			return ('', '')
		
		try:
			# Extract MCACOD (bits 15:0) and MSCOD (bits 31:16) from MC_STATUS
			mcacod = extract_bits(hex_value=value, min_bit=0, max_bit=15)
			mscod = extract_bits(hex_value=value, min_bit=16, max_bit=31)
			
			mcacod_decoded = hex(mcacod)  # Default to hex
			mscod_decoded = f"MSCOD={mscod}"  # Default to raw MSCOD
			
			# UBOX: Use ubox_params.json with different MSCOD tables based on MCACOD
			if 'UBOX' in instance_type:
				ubox_json = self.mcadata.ubox_data
				if ubox_json:
					# Decode MCACOD
					if 'MCACOD' in ubox_json:
						mcacod_str = str(mcacod)
						if mcacod_str in ubox_json['MCACOD']:
							mcacod_decoded = f"{ubox_json['MCACOD'][mcacod_str]} ({hex(mcacod)})"
					
					# Decode MSCOD - select table based on MCACOD value
					mscod_str = str(mscod)
					mscod_table = 'MSCOD'  # Default table
					
					# Special handling based on MCACOD value
					if mcacod == 1042:  # SCF Bridge IP:CMS error
						mscod_table = 'CMS_MSCOD'
					elif mcacod == 1043:  # SCF Bridge IP:SBO error
						mscod_table = 'SBO_MSCOD'
					elif mcacod == 1036:  # Shutdown suppression
						mscod_table = 'SHUTDOWN_ERR_MSCOD'
					
					# Look up MSCOD in the appropriate table
					if mscod_table in ubox_json:
						if mscod_str in ubox_json[mscod_table]:
							mscod_decoded = f"{ubox_json[mscod_table][mscod_str]} (MSCOD={mscod})"
						else:
							mscod_decoded = f"Unknown {mscod_table} MSCOD={mscod}"
			
			# UPI: Use upi_params.json with UPI_MSCOD key
			elif 'UPI' in instance_type:
				upi_json = self.mcadata.upi_data
				if upi_json and 'UPI_MSCOD' in upi_json:
					mscod_str = str(mscod)
					if mscod_str in upi_json['UPI_MSCOD']:
						mscod_decoded = f"{upi_json['UPI_MSCOD'][mscod_str]} (MSCOD={mscod})"
					else:
						mscod_decoded = f"Unknown MSCOD={mscod}"
			
			return (mcacod_decoded, mscod_decoded)
		
		except Exception as e:
			return (hex(0), f"Decode error: {str(e)}")

	def io_lookup_pattern(self, io='', upi='', suffix='ADDR', ptype='upi'):
		"""
		Build register path patterns for IO MCA ADDR/MISC lookup

		Args:
			io: IO number (string)
			upi: UPI number (string)
			suffix: 'ADDR' or 'MISC'
			ptype: 'ubox' or 'upi'

		Returns:
			Register path pattern string
		"""
		if ptype == 'ubox':
			# UBOX pattern: IO0__UNCORE__UBOX__NCEVENTS__NCEVENTS_CR_UBOX_MCI_ADDR
			pattern = f'IO{io}__UNCORE__UBOX__NCEVENTS__NCEVENTS_CR_UBOX_MCI_{suffix}'
		elif ptype == 'upi':
			# UPI pattern: IO0__UNCORE__UPI__UPI0__UPI_REGS__KTI_MC_ADDR
			# Note: Some products might use KTI_MC_AD or KTI_MC_MS instead
			if suffix == 'ADDR':
				pattern = f'IO{io}__UNCORE__UPI__UPI{upi}__UPI_REGS__KTI_MC_ADDR'
			elif suffix == 'MISC':
				pattern = f'IO{io}__UNCORE__UPI__UPI{upi}__UPI_REGS__KTI_MC_MISC'
			else:
				pattern = f'IO{io}__UNCORE__UPI__UPI{upi}__UPI_REGS__KTI_MC_{suffix}'
		else:
			pattern = ''
		
		return pattern

  	
## Extract bits from hex values decoding purposes and data extraction
def extract_bits(hex_value, min_bit, max_bit):
	
	"""
	Extract bits from a given hexadecimal value between min_bit and max_bit (inclusive).

	:param hex_value: The hexadecimal value as a string.
	:param min_bit: The starting bit position (inclusive).
	:param max_bit: The ending bit position (inclusive).
	:return: The extracted bits as an integer.
	"""
	# Convert the hex value to an integer
	
	int_value = int(hex_value, 16)

	# Calculate the number of bits to extract
	num_bits = max_bit - min_bit + 1

	# Create a mask for the desired bits
	mask = (1 << num_bits) - 1

	# Shift right by min_bit and apply the mask
	extracted_bits = (int_value >> min_bit) & mask

	return extracted_bits

# Loads decoder dict
def dev_dict(filename, filedir = None):
	## Load Configuration json files
	
	if filedir:
		jsfile = os.path.join(filedir, filename)#"{}\\{}".format(parent_dir, configfilename)
	else:
		parent_dir =Path(__file__).parent
		jsfile = os.path.join(parent_dir, filename)#"{}\\{}".format(parent_dir, configfilename)
	# Change dbgfile to original
	with open (jsfile) as configfile:
		configdata = json.load(configfile)
		jsondata = configdata

	return jsondata

def find_matching_key(hex_value, dictionary):
    # Convert the hex value to a string
    hex_str = f"0x{hex_value:04X}"
    
    # Iterate through the keys in the dictionary
    for key in dictionary:
        # Replace '?' with '.' to match any character
        pattern = key.replace('?', '.')
        
        # Use regular expression to match the pattern
        if re.match(pattern, hex_str):
            return key
    
    return None

def load_jsons(product):
	parent_dir =Path(__file__).parent
	jsfile_dir = os.path.join(parent_dir, product.upper())
	# Cha decoder file
	cha_json = dev_dict('cha_params.json', filedir = jsfile_dir)
	core_json = dev_dict('core_params.json', filedir = jsfile_dir)
	#portids_json = dev_dict('GNRPortIDs.json')
	portids_json = dev_dict('log_portid.json', filedir = jsfile_dir)    	
