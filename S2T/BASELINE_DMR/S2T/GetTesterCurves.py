## GNR Get Tester Curves
## Update: 10/3/2025
#
# Update: 3/6/2025
# Version: 1.5
# Last Update notes: Added the following features:
# - Code Modularity to include BASELINE of multiproducts
#
## Version: 1.40
## Last Update notes: Added the following features:
## - Updated CORE values based on TP S507
##
## Version: 1.30
## Last Update notes: Added the following features:
## - Changed endpoint url as the previous one stopped working
## - Added additional scripts to allow the usage of DFF voltages into S2T flow.
##
## Version: 1.30
## Last Update notes: Added the following features:
## - Changed Value of CORE Frequency for MESH F4 to 16 to be more in line with CLASS testing
## - Changed Value of CFC IO Frequency for MESH F4 to 22 to be more in line with CLASS testing
##
## Revision: 1.2
## Date: 20/06/2024
## Edit: gabriel.espinoza.ballestero@intel.com
## update Notes: updated ATE frequency values to match latest TP configuration.
##
## Revision: 1.1
## Date: 16/04/2024
## Edit: gabriel.espinoza.ballestero@intel.com
##
## Scripts with units default tester data, DFF data can be imported using zeep library
## To print / save your DFF use the GNR DFF Data Collector script.

import sys
import os

from tabulate import tabulate
try:
	from zeep import Client
	#from suds.client import Client
	print("Using zeep library to collect xml data...")
	#print("Using suds library to collect xml data...")
except ImportError:
	print ("!!!!!!!!!!!!!!!!!!")
	print ("zeep is not installed.")
	print ("install via windows shell:  command line == \"pip install zeep --proxy http://proxy-dmz.intel.com:911/\"")
	print ("!!!!!!!!!!!!!!!!!!")
	#sys.exit()

import re
from lxml import etree
import importlib
MAIN_PATH = os.path.abspath(os.path.dirname(__file__))

# iMPORT OF SELECTED PRODUCT CONFIGURATION
try:
	sys.path.append(MAIN_PATH)
	import ConfigsLoader as LoadConfig
	SELECTED_PRODUCT = LoadConfig.SELECTED_PRODUCT
	PRODUCT_CONFIG = LoadConfig.PRODUCT_CONFIG
except:
	SELECTED_PRODUCT = None
	PRODUCT_CONFIG = None
	print('Error while getting Product, if using UI discard this message.')

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== CONSTANTS AND GLOBAL VARIABLES =========================================================#
#========================================================================================================#

CORE_FREQ = None
CORE_CFC_FREQ = None
CORE_CFCIO_FREQ = None
CFC_FREQ = None
HDC_FREQ = None
IO_FREQ = None
MEM_FREQ = None
HDC_CORE_FREQ = None
CFC_CORE_FREQ = None
CFCIO_CORE_FREQ = None
MEM_CORE_FREQ = None
IO_HDC_FREQ = None
CFC_IO_FREQ = None
CORE_HDC_CFC_FREQ = None

CFC_MAX = None
HDC_MAX = None
CORE_MAX = None
IO_MAX = None
MEM_MAX = None
max_mlc_volt_per_cbb = None

All_Safe_RST_PKG = None
All_Safe_RST_CDIE = None
All_Safe_CBB = None

CORESTRING = None
CORETYPES = None
MAXLOGICAL = None
MAXPHYSICAL = None

classLogical2Physical = None
physical2ClassLogical = None

wsdl_url = None

def set_variables(product, config):

	ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
	PRODUCT_PATH = os.path.join(ROOT_PATH, 'product_specific', product.lower())
	sys.path.append(PRODUCT_PATH)

	# Loads Configuration directly based on SELECTED_PRODUCT done this way so it can be used offline
	# Performed this way to avoid using IPC and SV, to be able to use this offline
	import configs as pe
	#importlib.reload(pe)

	global SELECTED_PRODUCT
	global PRODUCT_CONFIG

	global CORE_FREQ
	global CORE_CFC_FREQ
	global CORE_CFCIO_FREQ
	global CFC_FREQ
	global HDC_FREQ
	global IO_FREQ
	global MEM_FREQ
	global MEM_CORE_FREQ
	global HDC_CORE_FREQ
	global CFC_CORE_FREQ
	global CFCIO_CORE_FREQ
	global IO_HDC_FREQ
	global CFC_IO_FREQ
	global CORE_HDC_CFC_FREQ
	global CFC_MAX
	global HDC_MAX
	global CORE_MAX
	global IO_MAX
	global MEM_MAX
	global max_mlc_volt_per_cbb
	global All_Safe_RST_PKG
	global All_Safe_RST_CDIE
	global All_Safe_CBB
	global CORESTRING
	global CORETYPES
	global MAXLOGICAL
	global MAXPHYSICAL
	global classLogical2Physical
	global physical2ClassLogical
	global wsdl_url

	SELECTED_PRODUCT = product
	PRODUCT_CONFIG = config

	configs = pe.configurations(product)

	DFF_VARS = configs.init_dff_data()

	CORE_FREQ = DFF_VARS['CORE_FREQ']
	CORE_CFC_FREQ = DFF_VARS['CORE_CFC_FREQ']
	CORE_CFCIO_FREQ = DFF_VARS['CORE_CFCIO_FREQ']
	CFC_FREQ = DFF_VARS['CFC_FREQ']
	HDC_FREQ = DFF_VARS['HDC_FREQ']
	IO_FREQ = DFF_VARS['IO_FREQ']
	HDC_CORE_FREQ = DFF_VARS['HDC_CORE_FREQ']
	CFC_CORE_FREQ = DFF_VARS['CFC_CORE_FREQ']
	CFCIO_CORE_FREQ = DFF_VARS['CFCIO_CORE_FREQ']
	IO_HDC_FREQ = DFF_VARS['IO_HDC_FREQ']
	CFC_IO_FREQ = DFF_VARS['CFC_IO_FREQ']
	CORE_HDC_CFC_FREQ = DFF_VARS['CORE_HDC_CFC_FREQ']
	MEM_FREQ = DFF_VARS['MEM_FREQ']
	MEM_CORE_FREQ = DFF_VARS['MEM_CORE_FREQ']
	max_mlc_volt_per_cbb = DFF_VARS['max_mlc_volt_per_cbb']

	CFC_MAX = DFF_VARS['cfc_max']
	HDC_MAX = DFF_VARS['hdc_max']
	CORE_MAX = DFF_VARS['core_max']
	IO_MAX = DFF_VARS['io_max']
	MEM_MAX = DFF_VARS['mem_max']

	#FivrCondition	All_Safe_RST_PKG
	All_Safe_RST_PKG = DFF_VARS['All_Safe_RST_PKG']
	'''{# Safe Voltages
		'VCORE_RST':0.85,
		'VHDC_RST':0.90,
		'VCFC_CDIE_RST':0.85,
		'VDDRA_RST':0.90,
		'VDDRD_RST':0.85,
		'VCFN_PCIE_RST':0.90,
		'VCFN_FLEX_RST':0.90,
		'VCFN_HCA_RST':0.90,
		'VIO_RST':1,
		'VCFC_IO_RST':0.85,
	}
	'''
	#FivrCondition	All_Safe_RST_CDie
	All_Safe_RST_CDIE = DFF_VARS['All_Safe_CBB'] # Legacy
	All_Safe_CBB = DFF_VARS['All_Safe_CBB']
	'''{# Safe Voltages
		'VCORE_RST':0.85,
		'VHDC_RST':0.90,
		'VCFC_CDIE_RST':0.85,
		'VDDRA_RST':0.90,
		'VDDRD_RST':0.85,
	}
	'''

	CONFIG = configs.init_product_specific()

	# Configuration Variables Init
	CORESTRING = CONFIG['CORESTRING']
	CORETYPES = CONFIG['CORETYPES']
	MAXLOGICAL = CONFIG['MAXLOGICAL']
	MAXPHYSICAL = CONFIG['MAXPHYSICAL']

	classLogical2Physical = CONFIG['LOG2PHY']
	physical2ClassLogical = CONFIG['PHY2LOG']

	#log2Phys10x5 = {0:0, 1:1, 2:2, 3:3, 4:6, 5:7, 6:8, 7:9, 8:10, 9:13, 10:14, 11:15, 12:16, 13:17, 14:20, 15:21, 16:22, 17:23, 18:24, 19:27, 20:28, 21:29, 22:30, 23:31, 24:34, 25:35, 26:36, 27:37, 28:38, 29:41, 30:42, 31:43, 32:44, 33:45, 34:48, 35:49, 36:50, 37:51, 38:52, 39:55, 40:56, 41:57, 42:58, 43:59}
	#Phys2log10x5 = {v:k for k, v in log2Phys10x5.items()}

	## EndPoint
	wsdl_url = DFF_VARS['wsdl_url'] # "http://mfglabdffsvc.intel.com/MDODFFWcf/DFFSVC.svc?wsdl"
	#wsdl_url = 'http://jfgwww1235.amr.corp.intel.com/MDODFFWcf/DFFSVC.svc?wsdl'

if SELECTED_PRODUCT != None:
	set_variables(SELECTED_PRODUCT, PRODUCT_CONFIG)
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== MAIN CODE STARTS HERE  =================================================================#
#========================================================================================================#

# Cache directory for XML files
CACHE_DIR = r'C:\Temp\DFF_Cache'

def ensure_cache_dir():
	"""Ensure the cache directory exists"""
	if not os.path.exists(CACHE_DIR):
		os.makedirs(CACHE_DIR)
		print(f"Created cache directory: {CACHE_DIR}")

def get_xml_data(visual, force=False):
	"""
	Get XML data for a visual ID, using cache if available.

	Args:
		visual: Visual ID string
		force: If True, force refresh from DFF service even if cached

	Returns:
		XML result string or None if error
	"""
	ensure_cache_dir()
	cache_file = os.path.join(CACHE_DIR, f"{visual}.xml")

	# Check if cached file exists and force is False
	if not force and os.path.exists(cache_file):
		#print(f"Using cached data for VID: {visual}")
		try:
			with open(cache_file, 'r', encoding='utf-8') as f:
				return f.read()
		except Exception as e:
			print(f"Error reading cache file: {e}. Fetching from service...")

	# Fetch from DFF service
	print(f"Fetching DFF data for VID: {visual}")
	try:
		client = call_client()
		xml = client.service.GetDataByVisualIdAsXml('visualIDs', visual)
		xml_result = xml.GetDataByVisualIdAsXmlResult

		# Save to cache
		try:
			with open(cache_file, 'w', encoding='utf-8') as f:
				f.write(xml_result)
			print(f"Cached data saved to: {cache_file}")
		except Exception as e:
			print(f"Warning: Could not save cache file: {e}")

		return xml_result
	except Exception as e:
		print(f"Error fetching data from DFF service: {e}")
		return None

def call_client():
	#wsdl_url = 'http://jfgwww1235.amr.corp.intel.com/MDODFFWcf/DFFSVC.svc?wsdl'
	client = Client(wsdl_url)
	return client
	# pip install zeep

def get_voltages_core(visual, core = 0, ate_freq='F1',  hot=True, force=False):
	phy2log = physical2ClassLogical
	compute = int(core/MAXPHYSICAL)
	coreLOG = phy2log[core%MAXPHYSICAL] + MAXLOGICAL*compute
	print(f' -- DFF data for physical {CORESTRING}{core} -- ATE {CORESTRING} {coreLOG} (This one is the number shown in below table)')
	data, printdata = dump_core_curves(visual=visual, core = coreLOG, hot=hot, s2tcollect = True, force=force)
	filtered_data = [row for row in printdata if (row[1] == ate_freq or row[1] == "CRVE") and row[2] != "MLC"]
	print(tabulate(filtered_data, headers="firstrow", tablefmt="grid"))
	return data

def get_voltages_uncore(visual, ate_freq='F1',  hot=True, force=False):
		#compute = int(core/60)
		#coreLOG = Phys2log10x5[core%60] + 44*compute


		print(' -- DFF data for UNCORE -- ATE DFF Data')
		data, printdata = dump_uncore_curves(visual=visual, hot=hot, s2tcollect = True, force=force)
		filtered_data = [row for row in printdata if row[2] == ate_freq or row[2] == "CRVE"]
		print(tabulate(filtered_data, headers="firstrow", tablefmt="grid"))
		return data

def get_voltages_l2(visual, ate_freq='F1',  hot=True, force=False):
    		#compute = int(core/60)
		#coreLOG = Phys2log10x5[core%60] + 44*compute


		print(' -- DFF data for L2 -- ATE DFF Data')
		data, printdata = dump_uncore_curves(visual=visual, hot=hot, s2tcollect = True, force=force)
		filtered_data = [row for row in printdata if row[2] == ate_freq or row[2] == "CRVE"]
		print(tabulate(filtered_data, headers="firstrow", tablefmt="grid"))
		return data


def get_voltages_mlc(visual, core = 0, ate_freq='F1',  hot=True, force=False):
	phy2log = physical2ClassLogical
	compute = int(core/MAXPHYSICAL)
	coreLOG = phy2log[core%MAXPHYSICAL] + MAXLOGICAL*compute
	CBB = int((core) / MAXPHYSICAL)
	print(f' -- DFF data for physical {CORESTRING}{core} -- ATE CBB {CBB}::{CORESTRING}::{coreLOG} (This one is the number shown in below table)')
	data, printdata = dump_core_curves(visual=visual, core = coreLOG, hot=hot, s2tcollect = True, force=force)
	header = [H.replace(CORESTRING, 'CBB').replace('LIC', 'IP') for H in printdata[0]]
	filtered_data = [row for row in printdata if (row[1] == ate_freq) and row[2] == "MLC"]
	print(tabulate(filtered_data, headers=header, tablefmt="grid"))
	return data


def filter_core_voltage(data, lic, core, ate_freq):

	for key, value in data.items():
		V_string = key.split('-')
		freq = V_string[2]
		corelog = V_string[0]
		ip = V_string[1]
		if freq == ate_freq and ip == lic:
			fvalue = float(value)
			print(f'{">"*3} Using {ip} Voltage DFF value of {fvalue}V for {CORESTRING} --> PHY:{core}-- LOG:{corelog}')
			return fvalue
		else:
			continue

def filter_uncore_voltage(data, ip, die, ate_freq):

	for key, value in data.items():
		key_string = key.split('-')
		freq = key_string[2]
		_compute = key_string[0]
		_ip = key_string[1]
		#fvalue = float(value)

		if _ip == ip and _compute == die and freq == ate_freq:
			fvalue = float(value)
			print(f'{">"*3} Using {die}:{ip} Voltage DFF value of {fvalue}V -- {ate_freq}')
			return fvalue
		else:
			continue

def get_ratios_core(ate_freq, flowid=1):
	index = flowid-1
	if ate_freq not in CORE_FREQ.keys() or ate_freq not in CORE_CFC_FREQ.keys():
		print ("ATE FREQ: F%d is not in %s_FREQ list" % (ate_freq, CORESTRING))
		return False
	if (flowid > len(CORE_FREQ[ate_freq]) ):
		print ("FLOWID is not correct: %d" % flowid)
		return False
	core_freq =  CORE_FREQ[ate_freq][index]
	mesh_freq =  CORE_CFC_FREQ[ate_freq]
	io_freq =  CORE_CFCIO_FREQ[ate_freq]
	return core_freq, mesh_freq, io_freq

def get_ratios_uncore(ate_freq, flowid=1):
	index = flowid-1
	if ate_freq not in CFC_FREQ.keys():
		print ("ATE FREQ: F%d is not in %d_FREQ list" % (ate_freq, CORESTRING))
		return False
	if (flowid > len(CFC_FREQ[ate_freq]) ):
		print ("FLOWID is not correct: %d" % flowid)
		return False
	core_freq =  CFC_CORE_FREQ[ate_freq]
	mesh_freq =  CFC_FREQ[ate_freq][index]
	io_freq =  CFC_IO_FREQ[ate_freq]
	return core_freq, mesh_freq, io_freq

def dump_core_curves(visual, core = [0,128], product = None, hot=True, usedata = False, custom=False, temp = "FAST_STC_V", s2tcollect = False, force=False):
	'''
	Dumps core voltage and frequency VMIN
	visual: visual ID
	core: Physical Core/Module to dump
	Hot: True == Hot,  False == Cold
	force: If True, force refresh from DFF service (ignore cache)
	'''
	if product == None: product = PRODUCT_CONFIG

	data_header = [f"{CORESTRING}","CRVE", "LIC", "COREF", "COREV", "CFCF", "CFCV"]
	CFC_VOLTAGE = All_Safe_RST_PKG['VCCRING_RST']
	core_license_levels = ['MLC','SSE','AVX2','AVX3', 'AMX']

	pattern = r'(MLC|SSE|AVX2|AVX3|AMX):((?:\d+(?:\.\d+)?\^.*?)+)(?=_|$)'
	CORE_FREQ_LIC = get_freq_array(visual, pattern=pattern, force=force)
	#print(CORE_FREQ_LIC)
	Available_license = [k for k in CORE_FREQ_LIC.keys()]
	corner="SSE@F1"
	data = {}

	printdata = []
	core_max = CORE_MAX
	MLC_per_CBB = max_mlc_volt_per_cbb # goes for CBB
	variant = CORETYPES[product]['config']
	maxlogcore =  CORETYPES[product]['maxlogcores']

	if type(core) == int:
		if core > maxlogcore:
			core = maxlogcore
		cores = [core,core+1]
	else:
		for i, v in enumerate(core):
			if v > maxlogcore:
				core[i] = maxlogcore
		cores = core

	print(f"Collecting data for VID:{visual} - {CORESTRING}s: {cores[1]-cores[0]}")
	#print(format_row.format("", *dota_teams))
	printdata = [data_header]
		#print ("{:<6} {:<4} {:<3} {:<5} {:<6} {:<6} {:<5} ".format(*data_header))

	for lic in Available_license:

		## Array is sorted this will fill any gaps in the sorted license dictionary array
		freq_index = 0
		for freq in range(1,core_max+1):

			corner = lic + "@F%d" % freq
			(flowid,v_array) = get_gv_array(visual, corner, hot, custom, temp, force=force)
			#if (freq > 4):
			#	freq_index = int(flowid)-1

			if v_array != None:
				if 'MLC'in lic:
					data_range = range(0,MLC_per_CBB)
					instance = 'CBB'
				else:
					data_range = range(cores[0],cores[1])
					cores_up = 0
					instance = f'{CORESTRING}'

				for c in data_range:
					try:
						if float(v_array[c]) < 0:
							continue
					except:
						print(f'Warning: No data for core {c} at corner {corner}')
						continue
					cores_up += 1 if not 'MLC'in lic else 0

					data[f'{instance}{c}-{lic}-F{freq}-Voltage'] = v_array[c]
					#print(lic,"-" , freq_index,"-" , corner)
					#print(CORE_FREQ_LIC[lic][freq_index])
					printdata.append([c, f'F{freq}', lic, CORE_FREQ_LIC[lic][freq_index], v_array[c], CORE_CFC_FREQ[freq], CFC_VOLTAGE])
					#print ("CORE{:<3} F{:<3} {:<4} {:<5} {:<6} {:<6} {:<5} ".format(c, freq, lic, CORE_FREQ[freq][freq_index], v_array[c], CORE_CFC_FREQ[freq], CFC_VOLTAGE))

				freq_index += 1

	if usedata:
		return data
	elif s2tcollect:
		return data, printdata
	else:
		print(tabulate(printdata, headers="firstrow", tablefmt="grid"))
		print(f'Total number of available cores = {cores_up}')

def dump_uncore_curves(visual, check = 'all', hot = True, custom=False, temp = "FAST_STC_V", usedata = False, s2tcollect = False, force=False):

	CORE_VOLTAGE = All_Safe_RST_PKG['VCORE_RST']
	CFC_VOLTAGE = All_Safe_RST_PKG['VCCRING_RST']
	data = {}
	printdata = []

	domains = {	'CFC':	{'freq':CFC_FREQ , 'string': "RING@F", 'corecfc':CFC_CORE_FREQ, 'inst':range(0,128), 'max':CFC_MAX},
				'IO':	{'freq':IO_FREQ , 'string': "CFCIO@F", 'corecfc':CFCIO_CORE_FREQ, 'inst':[0,1], 'max':IO_MAX},
				'MEM':	{'freq':MEM_FREQ , 'string': "CFCMEM@F", 'corecfc':MEM_CORE_FREQ, 'inst':[0,1], 'max':MEM_MAX},

    			}

	data_header = ["IP","INSTANCE","CRVE", "FREQ", "VOLT", "COREF", "COREV"]
	if check not in domains.keys() and check != 'all':
		print ('Not a valid key use: CFC, IO, HDC or all')
		sys.exit()

	IP = [check]

	if 'all' in IP:
		IP = domains.keys()

	#Use data key is to instead of printing the data on screen save it on a file
	print(f"Collecting data for VID:{visual} - Uncore")
	printdata = [data_header]
	#print ("{:<4} {:<8} {:<4} {:<5} {:<6} {:<6} {:<5} ".format(*data_header))
	for _IP in IP:

		domain_array = domains[_IP]['freq']
		domain_corecfc = domains[_IP]['corecfc']
		domain_string = domains[_IP]['string']
		domain_inst = domains[_IP]['inst']
		domain_max = domains[_IP]['max']
		if _IP == 'IO':
			instance = 'IMH'
		elif _IP == 'MEM':
			instance = 'MEM'
		elif _IP == 'MLC':
			instance = 'CBB'
		else:
			instance = "CBO"
		for _inst in domain_inst:
			for freq in range(1,domain_max+1):
				corner = f"{domain_string}{freq}"
				#for domain in domains:
				(flowid,v_array) = get_gv_array(visual, corner, hot, custom, temp, force=force)
				freq_index = 0
				if (freq == 4):
					freq_index = int(flowid)-1


				if v_array != None:
					if float(v_array[_inst]) < 0:
						continue
					#print(domain_array[freq][freq_index])
					#print(domain_corecfc[freq])

					data[f'{instance}{_inst}-{_IP}-F{freq}-Voltage'] = v_array[_inst]
					printdata.append([_IP,f'{instance}{_inst}', f'F{freq}', domain_array[freq][freq_index], v_array[_inst], domain_corecfc[freq], CORE_VOLTAGE])
					#print ("{:<4} {:<8} F{:<4} {:<5} {:<6} {:<6} {:<5} ".format(_IP,f'{instance}{_inst}', freq, domain_array[freq][freq_index], v_array[_inst], domain_corecfc[freq], CORE_VOLTAGE))


	if usedata:
		return data
	elif s2tcollect:
		return data, printdata
	else:
		print(tabulate(printdata, headers="firstrow", tablefmt="grid"))

def get_gv_array(visual, corner, hot=True, custom=False, temp = "FAST_STC_V", force=False):
	flowid = None
	if not custom:

		if hot:
			temp = "HSTC_V"
		else:
			temp = "CSTC_V"

	# Get XML data from cache or service
	xml_result = get_xml_data(visual, force=force)
	if xml_result is None:
		return None, None

	regex = r'FLOWID=(\d)'
	m = re.search(r"FLOWID=(\d)", xml_result)
	if m != None:
		flowid = m.group(1)
	else:
		flowid = '1'
	regex = ','+ temp + r'(.*)(,|FFDATA)'
	regex1 = f',{temp}='+ r'.*,'
	regex2 = f',{temp}='+ r'.*\<'
	#print(f'looking for{regex}')
	text = re.findall(regex1, xml_result)

	if not text:
		text = re.findall(regex2, xml_result)

	#print(f'found{text}')
	#print(f'looking for{regex}')
	#text = re.findall(regex, xml.GetDataByVisualIdAsXmlResult)
	#print(f'found{text}')
	if text:
		regex = corner + r'\:.*\_'
		#print(text[0])
		#print('----')
		#print(text[1])
		text = re.findall(regex, text[1])
		#print(f'found{text}')
		if text:
			text = text[0].split('_')[0]
			if text:
				text = text.lower()
				values = text.split(":")[-1].split("v")[::-1]
				return flowid, values
	return flowid, None

def get_vmins_by_corner_identifier(visual, corner, force=False):
	xml_result = get_xml_data(visual, force=force)
	if xml_result is None:
		return corner, None

	regex = corner + r'\:.*\_'
	text = re.findall(regex, xml_result)
	if text:
		text = text[0].split('_')[0]
		if text:
			text = text.lower()
			values = text.split(":")[-1].split("v")[::-1]
			return corner, values
	return corner, None

def get_vmins_by_corner_identifier_file(file, corner):
	regex = corner + r'\:.*\_'
	f = open(file,"r")
	text = re.findall(regex, f.read())
	f. close()
	if text:
		text = text[0].split('_')[0]
		if text:
			text = text.lower()
			values = text.split(":")[-1].split("v")[::-1]
			return corner, values
	return corner, None

def get_freq_array(visual, pattern = None, force=False):
	xml_result = get_xml_data(visual, force=force)
	if xml_result is None:
		return {}


	matches = re.findall(pattern, xml_result,  re.DOTALL)
	frequencies = {}
	for license_name, license_data in matches:
		# Extract frequencies from the license data
		freq_pattern = r'(\d+(?:\.\d+)?)\^'
		freqs = re.findall(freq_pattern, license_data)
		frequencies[license_name] = freqs

	for core_license_levels in frequencies:
		frequencies[core_license_levels] = sorted((int(float(freq) *10) for freq in frequencies[core_license_levels]), key=float)

	return frequencies

def parse_xml(xml_result, corner):
	regex = corner + r'\:.*\_'
	text = re.findall(regex, xml_result)
	if text:
		text = text[0].split('_')[0]
		if text:
			values = text.split(":")[-1].split("v")[::-1]
			return corner, values
	return corner, None

def print_vmins(corner, values, label):
	print(f"{corner}:")
	for i, vmin in enumerate(values):
		print(f"{label}{i}: {vmin}")

def save_gv_array(visual, corner, hot=True):
	"""
	Deprecated: Use get_xml_data with force=True instead.
	This function now just calls get_xml_data to maintain compatibility.
	"""
	xml_result = get_xml_data(visual, force=True)
	if xml_result:
		print(f"XML data saved for VID: {visual}")
		return xml_result
	else:
		print(f"Failed to save XML data for VID: {visual}")
		return None
