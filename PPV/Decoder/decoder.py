## MCA Decoder for MCA Checker
## Gaespino - Nov-2024

#import sys
#import os
import json
import re
import pandas as pd
from pathlib import Path
import os

# LLC MSCOD -- Taken from llc_mca_decoder in graniterapids repo
LLC = {'MSCOD_BY_VAL': {
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

class decoder():
	
	def __init__(self, data):
		self.data = data

	# Helper function to extract values based on a pattern
	def extract_value(self, df, dfcol, pattern):
		#filtered = pd.DataFrame()
		if isinstance(pattern, str):
			pat = [pattern]
		else:
			pat = pattern
		
		regex_pat = '|'.join(pat)

		filtered= df[(df[dfcol].str.contains(regex_pat, case=False, na=False))]

		if not filtered.empty:
			return filtered   			
		return None
	
	# Define the lookup pattern for each column
	def lookup_pattern(self, compute, location, operation, suffix, thread = '', ptype = 'cha'):
		
		if ptype == 'cha':
			pattern = f"SOCKET0__COMPUTE{compute}__UNCORE__CHA__CHA{location}__UTIL__MC_{suffix}"#_{operation}"
		elif ptype == 'llc':
			pattern = f"SOCKET0__COMPUTE{compute}__UNCORE__SCF__SCF_LLC__SCF_LLC{location}__MCI_{suffix}"#_{operation}"
		#DPMB_SOCKET0__COMPUTE0__CPU__CORE0__ML2_CR_MC3_ADDR_8749
		elif ptype == 'core_ml2':
				pattern = f"SOCKET0__COMPUTE{compute}__CPU__CORE{location}__ML2_CR_MC3_{suffix}"#_{operation}"		
		#DPMB_SOCKET0__COMPUTE1__CPU__CORE68__THREAD0__DCU_CR_MC1_STATUS_8749
		elif ptype == 'core_dcu':
				pattern = f"SOCKET0__COMPUTE{compute}__CPU__CORE{location}__THREAD{thread}__DCU_CR_MC1_{suffix}"#_{operation}"	
		#DPMB_SOCKET0__COMPUTE0__CPU__CORE0__DTLB_CR_MC2_STATUS_*
		elif ptype == 'core_dtlb':
				pattern = f"SOCKET0__COMPUTE{compute}__CPU__CORE{location}__DTLB_CR_MC2_{suffix}"#_{operation}"	
		#DPMB_SOCKET0__COMPUTE0__CPU__CORE0__THREAD*__IFU_CR_MC0_STATUS_*
		elif ptype == 'core_ifu':
				pattern = f"SOCKET0__COMPUTE{compute}__CPU__CORE{location}__THREAD{thread}__IFU_CR_MC0_{suffix}"#_{operation}"	
		elif ptype == 'ubox':
				pattern = f"SOCKET0__{compute}__UNCORE__{location}__NCEVENTS__{suffix}"#_{operation}"	

		return pattern

	# XLOOKUP equivalent in pandas
	def xlookup(self, lookup_array, testname, LotsSeqKey, UnitTestingSeqKey, if_not_found=""):
		try:
			result = lookup_array[(lookup_array['TestName'].str.contains(testname)) & (lookup_array['LotsSeqKey'] == LotsSeqKey) & (lookup_array['UnitTestingSeqKey'] == UnitTestingSeqKey)]
			lutvalue = result['TestValue'].iloc[0] if not result.empty else if_not_found
		except:
			print(f' -- Error looking for {testname}: Nothing found in MCA Data')
			lutvalue = if_not_found
		return  lutvalue

	def cha(self):
		mcdata = self.data
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
		
		mcdata = self.data
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

	def core(self):
			
		mcdata = self.data
		# Initialize the new dataframe
		columns = ['VisualID', 'Run', 'Operation', 'CORE_MC', 'Compute', 'CORE', 'ErrorType', 'MC_STATUS', 'MCACOD (ErrDecode)', 'MSCOD','MC_ADDR','MC_MISC']
		#new_df = pd.DataFrame(columns=columns)
		#decodelist = ['MC DECODE', 'Orig Req','Opcode','cachestate','TorID','TorFSM','SrcID','ISMQ','Attribute','Result','Local Port']
		
		# CHA List
		decodelistmc = ['MC DECODE']
		decodelistmisc = ['MiscV','RSF','LSF','LLC_misc']
		#decodelistmisc3 = ['SrcID','ISMQ','Attribute','Result','Local Port']
		
		data_dict = {k:[] for k in columns}
		
		for visual_id in mcdata['VisualId'].unique():

			# Split Data into required elements
			subset = mcdata[(mcdata['VisualId'] == visual_id) & (mcdata['TestName'].str.contains('CPU__CORE'))]

			# Further split into required lookup registers for each VID
			mc_filtered = self.extract_value(subset,'TestName', ['ML2_CR_MC3_STATUS','IFU_CR_MC0_STATUS','DTLB_CR_MC2_STATUS','DCU_CR_MC1_STATUS'])# subset[(subset['TestName'].str.contains('UTIL__MC_STATUS'))] #self.extract_value(subset, 'UTIL__MC_STATUS')
			addr_filtered = self.extract_value(subset,'TestName', ['ML2_CR_MC3_ADDR','IFU_CR_MC0_ADDR','DTLB_CR_MC2_ADDR','DCU_CR_MC1_ADDR'])# subset[subset['TestName'].str.contains('UTIL__MC_ADDR')]#self.extract_value(subset, 'UTIL__MC_ADDR')
			misc_filtered = self.extract_value(subset,'TestName', ['ML2_CR_MC3_MISC','IFU_CR_MC0_MISC','DTLB_CR_MC2_MISC','DCU_CR_MC1_MISC'])# subset[subset['TestName'].str.contains('UTIL__MC_MISC_')]#self.extract_value(subset, 'UTIL__MC_MISC_')
			#misc3_filtered = self.extract_value(subset,'TestName', 'UTIL__MC_MISC3_')# subset[subset['TestName'].str.contains('UTIL__MC_MISC3_')]#self.extract_value(subset, 'UTIL__MC_MISC3')
			
			# If no MCA is found move to the next VID
			try:
				if mc_filtered.empty:
					print(f' -- No MCA data found for COREs ML2 in VID: {visual_id}')
					continue
			except:
				print(f' -- No MCA data found for COREs ML2 in VID: {visual_id}')
				continue
			
			# This will iterate over all the MCAS to look for Address, Misc and MISC3 data for corresponding fail IP
			for i, data in mc_filtered.iterrows():
				
				# Build new
				data_dict['VisualID'] += [visual_id]
				LotsSeqKey = data['LotsSeqKey']
				UnitTestingSeqKey = data['UnitTestingSeqKey']
				compute =  re.search(r'COMPUTE(\d+)', data['TestName']).group(1) #data['TestName'].extract(r'COMPUTE(\d+)')
				core = re.search(r'CPU__CORE(\d+)', data['TestName']).group(1)  #data['TestName'].extract(r'CHA(\d+)')
				operation = data['Operation']
				thread =re.search(r'THREAD(\d+)', data['TestName']).group(1) if 'THREAD' in data['TestName'] else ''
				## Address lookup pattern
				
				ErroTypes = ['ML2', 'DCU', 'DTLB', 'IFU']
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
				data_dict['CORE_MC'] += [data['TestName'] ]
				data_dict['Compute'] += [compute]
				data_dict['CORE'] += [f'CORE{core}']
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
def dev_dict(filename, useroot = True):
		## Load Configuration json files
	configfilename = filename
	if useroot:
		#file_NAME = (__file__).split("\\")[-1].rstrip()
		parent_dir =Path(__file__).parent #split(file_NAME)[0]
		jsfile = os.path.join(parent_dir, configfilename)#"{}\\{}".format(parent_dir, configfilename)
	else:
		jsfile = configfilename

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

# Cha decoder file
cha_json = dev_dict('cha_params.json')
core_json = dev_dict('core_params.json')
#portids_json = dev_dict('GNRPortIDs.json')
portids_json = dev_dict('log_portid.json')
