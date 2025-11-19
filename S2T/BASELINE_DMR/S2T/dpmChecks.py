# DPM Team Uncore Teams debug tools
# Developer: gaespino
#
# Update: 3/6/2025
# Version: 1.5
# Last Update notes: Added the following features:
# - Code Modularity to include BASELINE of multiproducts
#
# Update: 5/2/2025
# Version: 1.4
# Last Update notes: Added the following features:
# - Improved Logger with extended capabilities
# - qdf, visual and product strings added -- Visual Needs an open port80 for CATTS Tool to work properly
# - Added a new Logger folder with logger corresponding scripts
# 	>> ErrorReport.py - Script to build all the required files for Test logging, this version decodes MCA if there is any present for
#		CHA, LLC, UBOX, PM and PUNIT, more IPs can added in the future, depending on requirements.
#		MCA Dump code extracted from the core debug library, modified to save data into the MCA Data file, this file is in the format of
#		PPV Bucketer reports, which can be used for data analysis and report generation.
#	>> Logger.py - User Interface
#
# Update: 30/10/2024
# Version: 1.30 
# Last Update notes: Added the following features:
# - Bios Knobs Checks
# - PPVC option for pseudo Bootscript
# - Fuse self-check
# - Flow execution time reduction by code optimization
#
# Update: 20/06/2024
# Version: 1.20 
# Last Update notes: Added the following features
# - vbump option for pseudo_bs
# - Burn test logics
# - More vbump options DDRD, DDRA, VCCIN, VCCINF
# - Code cleanup
#
# Update: 12/2/2024
# Versiun: 1.00 
# Last Update notes: Added the pseudo bs capabilities to use Custom Masks, set htdis = False if none pseudo content is being used.
# Any issues please contact gabriel.espinoza.ballestero@intel.com
#

import time
import csv
import os, sys
import ipccli
import namednodes
import pandas as pd
import getpass
import subprocess
from tabulate import tabulate
from openpyxl import load_workbook
import re
import datetime
import json
import importlib
from importlib import import_module

# Tools and libraries from pythonsv
import toolext.bootscript.boot as b
import toolext.bootscript.toolbox.fuse_utility as fu
import pm.pmutils.tools as cvt



#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#========================================================================================================#
#=============== DIRECT CONFIG ACCESS (No redundant declarations) =======================================#
#========================================================================================================#

# All configuration accessed directly via config.ATTRIBUTE
# No legacy shortcuts - single source of truth pattern


# Append the Main Scripts Path
MAIN_PATH = os.path.abspath(os.path.dirname(__file__))

## Imports from S2T Folder  -- ADD Product on Module Name for Production
sys.path.append(MAIN_PATH)
import ConfigsLoader as cfl
config = cfl.config
config.reload()

# Product Functions
pf = config.get_functions()

# Set Used product Variable -- Called by Framework
SELECTED_PRODUCT = config.SELECTED_PRODUCT
BASE_PATH = config.BASE_PATH
LEGACY_NAMING = SELECTED_PRODUCT.upper() if SELECTED_PRODUCT.upper() in ['GNR', 'CWF'] else ''
THR_NAMING = SELECTED_PRODUCT.upper() if SELECTED_PRODUCT.upper() in ['GNR', 'CWF', 'DMR'] else ''

if cfl.DEV_MODE:
	import CoreManipulation as gcm
	import Logger.ErrorReport as dpmtileview
	import Logger.logger as dpmlog
	import Tools.portid2ip as p2ip
	import Tools.requests_unit_info as reqinfo
	import ConfigsLoader as LoadConfig
else:
	gcm = import_module(f'{BASE_PATH}.S2T.{LEGACY_NAMING}CoreManipulation')
	dpmtileview = import_module(f'{BASE_PATH}.S2T.Logger.ErrorReport')
	dpmlog = import_module(f'{BASE_PATH}.S2T.Logger.logger')
	p2ip = import_module(f'{BASE_PATH}.S2T.Tools.portid2ip')
	reqinfo = import_module(f'{BASE_PATH}.S2T.Tools.requests_unit_info')
	LoadConfig = import_module(f'{BASE_PATH}.S2T.ConfigsLoader')

## Imports from THR folder - These are external scripts, always use same path
f = None
try:
	f = import_module(f'{BASE_PATH}.{THR_NAMING}FuseOverride')
	print(' [+] FuseOverride imported successfully')
except Exception as e:
	print(f' [x] Could not import FuseOverride, some features may be limited: {e}')

## Reload of all imported scripts
if cfl.DEV_MODE:
	importlib.reload(gcm)
	importlib.reload(dpmlog)
	importlib.reload(dpmtileview)
	importlib.reload(LoadConfig)
	if f is not None:
		importlib.reload(f)
	config.reload()

verbose = False

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

ipc = ipccli.baseaccess()
itp = ipc
sv = namednodes.sv #shortcut
sv.initialize()

debug= False
log_folder = "C:\\temp\\"

## WIP
def retry_on_exception(func, *args, **kwargs):
	"""
	Executes a function and retries if an exception occurs.
	
	Parameters:
	- func: The function to execute.
	- *args: Positional arguments for the function.
	- **kwargs: Keyword arguments for the function.
	
	Returns:
	- The result of the function if successful.
	- None if all retries fail.
	"""
	try:
		return func(*args, **kwargs)
	except Exception as e:
		print(f"!!! Error occurred: {e}. Retrying...")
		try:
			return func(*args, **kwargs)
		except Exception as e:
			print(f"!!! Retry failed: {e}. Please check the function and inputs.")
			return None

## Instance Initiator - Can be optimized but it works for now, used to simplify code a bit
class PySV():
	from namednodes import sv
	
	"""
	Class constructor for PythonSV path creation.
	"""
	def __init__(self, tiles=[0], PathTemplates = ['uncore.ra'],instances=['ra22','ra18'], preTilePath='socket',die='compute0', checktype = 'current_vcri'):

		self._instances = []
		self.readcheck = checktype
		# All tiles
		for tile in tiles:
			self._socket = sv.get_by_path('{0}{1}.{2}'.format(preTilePath,tile,die))
			for template in PathTemplates:
				for i in instances:
					try:
						self._instances.append(self._socket.get_by_path('{0}.{1}'.format(template,i)))
					except:
						print(f'PythonSV instance {i} cannot be read, skipping')
		
		# Perform a check on all the instances, if there is a non readable one, remove it 
		if checktype != '': 
			self.instancechk()

	def instancechk(self):
		
		for _instance in self._instances:
			try:
				read_check = _instance.get_by_path('{}'.format(self.readcheck))
				#print(read_check.path)
				read_check.read()
			except:
				print(f'instance {_instance.path} cannot be read, removing it')
				self._instances.remove(_instance)

## Cstates review: type help for a nice table with all cstates values (WIP)
class cstates():
	def __init__(self, sktnum = [0]):
		self.sv = _get_global_sv()			
		self.ipc = ipccli.baseaccess()
		self.sktnum = sktnum
		self.instance = ['ptpcfsms.ptpcfsms']
	
	def core(self, corecstates = 0x7, computes = ['compute0', 'compute1', 'compute2']):
		#instance = ['ptpcfsms.ptpcfsms']
		for die in computes:	
			cores = PySV(tiles=self.sktnum, PathTemplates = ['uncore.punit'],instances=self.instance, preTilePath='socket',die=die, checktype = 'dfx_ctrl_unprotected')
			for core in cores._instances:
				cstate_cv = core.dfx_ctrl_unprotected.core_cstate_limit.read()
				core.dfx_ctrl_unprotected.core_cstate_limit = corecstates
				print(f'{die.upper()} core cstate value changed from {cstate_cv} --> {corecstates}')

	def pkgc(self, pkg = 0x5, computes = ['compute0', 'compute1', 'compute2']):
		#instance = ['ptpcfsms.ptpcfsms']
		for die in computes:	
			pc6s = PySV(tiles=self.sktnum, PathTemplates = ['uncore.punit'],instances=self.instance, preTilePath='socket',die=die, checktype = 'dfx_ctrl_unprotected')
			for pc6 in pc6s._instances:
				pc6_cv = pc6.dfx_ctrl_unprotected.pkg_cstate_limit.read()
				pc6.dfx_ctrl_unprotected.pkg_cstate_limit = pkg
				print(f'{die.upper()} pkg cstate value changed from {pc6_cv} --> {pkg}')
				
	def read(self):
		#instance = ['ptpcfsms.ptpcfsms']
		die = 'computes'
		_cstates = PySV(tiles=self.sktnum, PathTemplates = ['uncore.punit'],instances=self.instance, preTilePath='socket',die=die, checktype = 'dfx_ctrl_unprotected')
		for cstate in _cstates._instances:
			cstate.dfx_ctrl_unprotected.core_cstate_limit.show()
			cstate.dfx_ctrl_unprotected.pkg_cstate_limit.show()

	def counters(self):
		sv = self.sv		
		ipc = self.ipc
		halted = False
		message = 'Running C6 counters check, to check cpu counters a halt needs to be done, do you want to continue?'
		response = prompt_msg(message, timeout = 30)
		if (response == 'no') or (response == None):
			sys.exit()
		
		try: 
			ipc.halt()
			halted = True
		except: print('Halt cannot be executed, probably unit already hanged or halted. Skipping....')
		# Not considering multi socket on this version yet
		print ("Core C6 counters : \n")
		
		sv.socket0.computes.cpu.cores.fscp_cr_core_c6_residency_counter.show()
		
		print ("\nPackage C6 counters : \n")
		sv.socket0.computes.uncore.punit.ptpcioregs.ptpcioregs.pc6_rcntr.show()

		if halted: ipc.go()

## CFC Voltage/Ratio values and VF Curve data
class cfc():
	def __init__(self, dies = ['all'], regs = 'all', sktnum = [0], fuse_ram = True):
		self.sv = _get_global_sv()			
		self.ipc = ipccli.baseaccess()
		
		self.regs = regs
		self.sktnum = sktnum
		self.fuse_ram = fuse_ram
		
		if 'all' in dies:
			dies = []
			dies.extend(sv.socket0.ios.name)
			dies.extend(sv.socket0.computes.name)
		self.dies = dies

	def voltage(self):
		
		#Self Class values
		regs = self.regs
		fuse_ram = self.fuse_ram
		dies = self.dies
		sktnum = self.sktnum

		# Data inits
		data_cfc = {}
		data_hdc = {}
		#data_pstates = {}	
		data_read = {}
		update_data = {}
		instance = []
		mesh_inst = ['pcodeio_map']
		meshcv = 'io_wp_rc_cv_ps_0'

		# Check for arguments in reg key
		valid_regs = {	'fuses':{'fuses': True, 	'cv':False}, 
						'cv': 	{'fuses': False, 	'cv':True}, 
						'all':	{'fuses': True, 	'cv':True}}
		
		if regs not in valid_regs.keys():
			print (f'No valid register selection to be read, valid options are: \n' +
					'fuses:	Reads all fused data configured for CFC Ratios. \n' + 
					'cv: 	Reads current mesh value for CFC ratios. \n' +
					'all: 	Reads fuses and current values for CFC ratios. (default) '  )
			sys.exit()
		
		regfuse = valid_regs[regs]['fuses']
		regcv = valid_regs[regs]['cv']

		# Read all fuses first
		if fuse_ram and regfuse:
			fuseRAM()
			#sv.sockets.computes.fuses.load_fuse_ram()
			#sv.sockets.ios.fuses.load_fuse_ram()
		
		curves = config.CFC_VOLTAGE_CURVES
				#{	'cfc_curve': ['pcode_cfc_vf_voltage_point0','pcode_cfc_vf_voltage_point1','pcode_cfc_vf_voltage_point2','pcode_cfc_vf_voltage_point3','pcode_cfc_vf_voltage_point4','pcode_cfc_vf_voltage_point5'],
				#	#'hdc_curve': ['pcode_hdc_vf_voltage_point0','pcode_hdc_vf_voltage_point1','pcode_hdc_vf_voltage_point2','pcode_hdc_vf_voltage_point3','pcode_hdc_vf_voltage_point4','pcode_hdc_vf_voltage_point5'],
				#	'hdc_curve': ['pcode_l2_vf_voltage_point0','pcode_l2_vf_voltage_point1','pcode_l2_vf_voltage_point2','pcode_l2_vf_voltage_point3','pcode_l2_vf_voltage_point4','pcode_l2_vf_voltage_point5'],
				#}

		for die in dies:
			
			if re.search(r'io*', die): 
				instance = ['punit_iosf_sb']
				
			elif re.search(r'compute*', die): 
				instance = ['pcu']
			else:
				print(f'Not valid die selected {die}: Skipping...')
				continue
			#print (f'\n### {str(die).upper()}  - CFC Voltages fused values ###')
			die_inst = PySV(tiles=sktnum, PathTemplates = ['fuses'],instances=instance, preTilePath='socket',die=die, checktype = 'pcode_cfc_min_ratio')
			mesh_val = PySV(tiles=sktnum, PathTemplates = ['uncore'],instances=mesh_inst, preTilePath='socket',die=die, checktype = meshcv)
			
			if regfuse:
				for fuse in die_inst._instances:
					# CFC VF fuses (VOLTAGE)

					for curve in curves['cfc_curve']:
						pointvalue = fuse.readregister(curve)
						printData(data_cfc, curve, die, hex(pointvalue))

					if re.search(r'compute*', die):
						# HDC VF fuses (VOLTAGE)

						for curve in curves['hdc_curve']:
							pointvalue = fuse.readregister(curve)
							printData(data_hdc, curve, die, hex(pointvalue))

			if regcv:
				# Mesh current value / Add some extra code for the hdc read, this one can be checked directly from the RA
				for mesh in mesh_val._instances:

					meshvalue = mesh.io_wp_rc_cv_ps_0.readfield('voltage')
					printData(data_read, 'io_wp_rc_cv_ps_0.voltage', die, hex(meshvalue))

		if regfuse:
			printTable(data_cfc, "CFC VF fuses (VOLTAGE)")
			printTable(data_hdc, "HDC VF fuses (VOLTAGE)")
			
		if regcv:
			printTable(data_read, "Voltage Current Values (MESH)")

	def ratios(self):
		
		#Self Class values
		regs = self.regs
		fuse_ram = self.fuse_ram
		dies = self.dies
		sktnum = self.sktnum
		
		# Data inits
		data_cfc = {}
		data_hdc = {}
		data_pstates = {}	
		data_read = {}
		update_data = {}
		instance = []
		mesh_inst = ['pcodeio_map']
		meshcv = 'io_wp_rc_cv_ps_0'

		#Check for arguemnts in reg key
		valid_regs = {	'fuses':{'fuses': True, 	'cv':False}, 
						'cv': 	{'fuses': False, 	'cv':True}, 
						'all':	{'fuses': True, 	'cv':True}}
		
		if regs not in valid_regs.keys():
			print (f'No valid register selection to be read, valid options are: \n' +
					'fuses:	Reads all fused data configured for CFC Ratios. \n' + 
					'cv: 	Reads current mesh value for CFC ratios. \n' +
					'all: 	Reads fuses and current values for CFC ratios. (default) '  )
			sys.exit()
		
		regfuse = valid_regs[regs]['fuses']
		regcv = valid_regs[regs]['cv']
		
		# Read all fuses first
		if fuse_ram and regfuse:
			fuseRAM()
			#sv.sockets.computes.fuses.load_fuse_ram()
			#sv.sockets.ios.fuses.load_fuse_ram()
		
		curves = config.CFC_RATIO_CURVES
		#{	'cfc_curve': ['pcode_cfc_vf_ratio_point0','pcode_cfc_vf_ratio_point1','pcode_cfc_vf_ratio_point2','pcode_cfc_vf_ratio_point3','pcode_cfc_vf_ratio_point4','pcode_cfc_vf_ratio_point5'],
		#			'hdc_curve': ['pcode_l2_vf_ratio_point0','pcode_l2_vf_ratio_point1','pcode_l2_vf_ratio_point2','pcode_l2_vf_ratio_point3','pcode_l2_vf_ratio_point4','pcode_l2_vf_ratio_point5'],
		#			'pstates' : {	'p0':'pcode_sst_pp_0_cfc_p0_ratio', 
		#							'p1':'pcode_sst_pp_0_cfc_p1_ratio', 
		#							'pn':'pcode_cfc_pn_ratio', 
		#							'min':'pcode_cfc_min_ratio'}
		#		}

		for die in dies:
			
			if re.search(r'io*', die): 
				instance = ['punit_iosf_sb']
				
			elif re.search(r'compute*', die): 
				instance = ['pcu']
			else:
				print(f'Not valid die selected {die}: Skipping...')
				continue
			#print (f'\n### {str(die).upper()}  - CFC Ratios fused values ###')
			die_inst = PySV(tiles=sktnum, PathTemplates = ['fuses'],instances=instance, preTilePath='socket',die=die, checktype = 'pcode_cfc_min_ratio')
			mesh_val = PySV(tiles=sktnum, PathTemplates = ['uncore'],instances=mesh_inst, preTilePath='socket',die=die, checktype = meshcv)
			
			if regfuse:
				for fuse in die_inst._instances:
					# CFC VF fuses (RATIO)

					for curve in curves['cfc_curve']:
						pointvalue = fuse.readregister(curve)
						printData(data_cfc, curve, die, hex(pointvalue))

					if re.search(r'compute*', die):
						# HDC VF fuses (RATIO)

						for curve in curves['hdc_curve']:
							pointvalue = fuse.readregister(curve)
							printData(data_hdc, curve, die, hex(pointvalue))

					# CFC Pstate fuses (RATIO)
					for pstate in curves['pstates'].keys():
						pstatevalue = fuse.readregister(curves['pstates'][pstate])
						printData(data_pstates, pstate, die, hex(pstatevalue))
			
			if regcv:
				# Mesh current value
				for mesh in mesh_val._instances:

					meshvalue = mesh.io_wp_rc_cv_ps_0.readfield('ratio')
					printData(data_read, 'io_wp_rc_cv_ps_0.ratio', die, hex(meshvalue))

		if regfuse:
			printTable(data_cfc, "CFC VF fuses (RATIO)")
			printTable(data_hdc, "HDC VF fuses (RATIO)")
			printTable(data_pstates, "Pstates Values (RATIO)")
		if regcv:
			printTable(data_read, "Ratios Current Values (MESH)")

	#def curves(self)

## IA Voltage/Ratio values and VF Curve data
class ia():
	
	def __init__(self, dies = ['all'], regs = 'all', sktnum = [0], fuse_ram = True):
		self.sv = _get_global_sv()			
		self.ipc = ipccli.baseaccess()
		
		self.regs = regs
		self.sktnum = sktnum
		self.fuse_ram = fuse_ram
		
		if 'all' in dies:
			_die = sv.socket0.target_info["segment"].lower()
			dies = sv.socket0.computes.name
			#if _die == 'gnrap':
			#	dies = ['compute0', 'compute1', 'compute2']
			#elif _die == 'gnrsp':
			#	dies = ['compute0', 'compute1']
		
		self.dies = dies

	## Ratios information for IA/CORES
	def ratios(self, vf = True):
		#Self Class values
		regs = self.regs
		fuse_ram = self.fuse_ram
		dies = self.dies
		sktnum = self.sktnum
		
		## Init Values
		instance = {}
		data_limits ={}
		data_p1 = {}
		data_pstates = {}
		data_read = {}
		data_vf = {}
		mesh_inst = ['pcodeio_map']
		meshcv = 'io_wp_ia_cv_ps_0'
		
		# Curves defaults
		pp = 0
		idx = 0
		ratio = 0
		
		# Enumerate all the variables needed for power curves	
		ppfs = [0,1,2,3,4]
		idxs = [0,1,2,3,4,5]
		vfidxs = [0,1,2,3]
		ratios = [0,1,2,3,4,5,6,7]
		search_string = ['profile', 'idx', 'ratio'] # Not used


		valid_regs = {	'fuses':{'fuses': True, 	'cv':False}, 
						'cv': 	{'fuses': False, 	'cv':True}, 
						'all':	{'fuses': True, 	'cv':True}}

		if regs not in valid_regs.keys():
			print (f'No valid register selection to be read, valid options are: \n' +
					'fuses:	Reads all fused data configured for IA Ratios. \n' + 
					'cv: 	Reads current mesh value for IA ratios. \n' +
					'all: 	Reads fuses and current values for IA ratios. (default) '  )
			sys.exit()
		
		regfuse = valid_regs[regs]['fuses']
		regcv = valid_regs[regs]['cv']	
		
		# Read all fuses first
		if fuse_ram and regfuse:
			fuseRAM()

		#David - solo SSE license se usa, AVX no
		curves = config.IA_RATIO_CURVES
		
		#{	'limits': [f'pcode_sst_pp_##profile##_turbo_ratio_limit_ratios_cdyn_index##idx##_ratio##ratio##'],
		#			'p1': [f'pcode_sst_pp_##profile##_sse_p1_ratio'],
		#			'vf_curve': ['pcode_ia_vf_ratio_voltage_index##idx##_ratio_point0','pcode_ia_vf_ratio_voltage_index##idx##_ratio_point1','pcode_ia_vf_ratio_voltage_index##idx##_ratio_point2','pcode_ia_vf_ratio_voltage_index##idx##_ratio_point3','pcode_ia_vf_ratio_voltage_index##idx##_ratio_point4','pcode_ia_vf_ratio_voltage_index##idx##_ratio_point5'],
		#			'pstates' : {	'p0':'pcode_ia_p0_ratio', 
		#							'pn':'pcode_ia_pn_ratio', 
		#							'min':'pcode_ia_min_ratio',
		#						}
		#		}

		#if 'all' in dies:
		#	dies = ['compute0', 'compute1', 'compute2']

		for die in dies:

			if re.search(r'compute*', die): 
				instance = ['pcu']
			else:
				print(f'Not valid die selected {die}: Skipping...')
				continue
			#print (f'\n### {str(die).upper()}  - IA Ratios fused values ###')
			die_inst = PySV(tiles=sktnum, PathTemplates = ['fuses'],instances=instance, preTilePath='socket',die=die, checktype = 'pcode_ia_min_ratio')
			mesh_val = PySV(tiles=sktnum, PathTemplates = ['uncore'],instances=mesh_inst, preTilePath='socket',die=die, checktype = meshcv)
			
			## Dumps all fuse data if option is selected
			if regfuse:
				for fuse in die_inst._instances:
					
					# Limit fuses (RATIO)
					for curve in curves['limits']:
						for pp in ppfs:
							for idx in idxs:
								for ratio in ratios:
									new_curve = curve
									
									#for _search in search_string:
									new_curve = new_curve.replace(f'##profile##',str(pp))
									new_curve = new_curve.replace(f'##idx##',str(idx))
									new_curve = new_curve.replace(f'##ratio##',str(ratio))
									
									pointvalue = fuse.readregister(new_curve)
									printData(data_limits, new_curve, die, hex(pointvalue))
									#print(f'{new_curve} = {pointvalue}')
					
					# VF curve ratio values
					for idx in vfidxs:
						for curve in curves['vf_curve']:

							new_curve = curve
							new_curve = new_curve.replace(f'##idx##',str(idx))
							pointvalue = fuse.readregister(new_curve)
							printData(data_vf, new_curve, die, hex(pointvalue))

					# P1 fuses (RATIO)
					for curve in curves['p1']:
						for pp in ppfs:
							new_curve = curve
							new_curve = new_curve.replace(f'##profile##',str(pp))
							pointvalue = fuse.readregister(new_curve)
							#print(f'{new_curve} = {pointvalue}')
							printData(data_p1, new_curve, die, hex(pointvalue))

					# CFC Pstate fuses (RATIO)
					for pstate in curves['pstates'].keys():
						pstatevalue = fuse.readregister(curves['pstates'][pstate])
						#print(f'{pstate} = {pstatevalue}')
						printData(data_pstates, pstate, die, hex(pstatevalue))

			
			# Dumps current core ratio valus if option is selected
			if regcv:
				for mesh in mesh_val._instances:

					for core in range(64):
						svregister = f'io_wp_ia_cv_ps_{core}'
						meshvalue = mesh.readregister(svregister).readfield('ratio')
						printData(data_read, f'{svregister}.ratio', die, hex(meshvalue))
					#print(f'{meshcv}.ratio = {hex(meshvalue)}')
		if regfuse:
			printTable(data_limits, "IA VF limit fuses (RATIO)")
			printTable(data_p1, "IA P1 power profiles fuses (RATIO)")
			printTable(data_pstates, "IA Pstates Values (RATIO)")
			printTable(data_vf, "IA VF Curve Values (RATIO)")
		if regcv:
			printTable(data_read, "IA Ratios Current Values")

	## Ratios information for IA/CORES
	def voltage(self):
		#Self Class values
		regs = self.regs
		fuse_ram = self.fuse_ram
		dies = self.dies
		sktnum = self.sktnum
		
		## Init Values
		instance = {}
		data_read = {}
		data_vf = {}
		mesh_inst = ['pcodeio_map']
		meshcv = 'io_wp_ia_cv_ps_0'
		
		# Curves defaults
		pp = 0
		idx = 0
		ratio = 0
		
		# Enumerate all the variables needed for power curves	
		
		idxs = [0,1,2,3]
		vcurves = [0,1,2,3,4,5,6,7,8,9,10,11]
		search_string = ['profile', 'idx', 'ratio'] # Not used


		valid_regs = {	'fuses':{'fuses': True, 	'cv':False}, 
						'cv': 	{'fuses': False, 	'cv':True}, 
						'all':	{'fuses': True, 	'cv':True}}

		if regs not in valid_regs.keys():
			print (f'No valid register selection to be read, valid options are: \n' +
					'fuses:	Reads all fused data configured for IA Ratios. \n' + 
					'cv: 	Reads current mesh value for IA ratios. \n' +
					'all: 	Reads fuses and current values for IA ratios. (default) '  )
			sys.exit()
		
		regfuse = valid_regs[regs]['fuses']
		regcv = valid_regs[regs]['cv']	
		
		# Read all fuses first
		if fuse_ram and regfuse:
			fuseRAM()
			#sv.sockets.computes.fuses.load_fuse_ram()
			#sv.sockets.ios.fuses.load_fuse_ram()

		curves = config.IA_VOLTAGE_CURVES
		#{	'vf_curve': ['pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point0','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point1','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point2','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point3','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point4','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point5'],
		#		}

		#if 'all' in dies:
		#	dies = ['compute0', 'compute1', 'compute2']

		for die in dies:

			if re.search(r'compute*', die): 
				instance = ['pcu']
			else:
				print(f'Not valid die selected {die}: Skipping...')
				continue
			#print (f'\n### {str(die).upper()}  - IA Ratios fused values ###')
			die_inst = PySV(tiles=sktnum, PathTemplates = ['fuses'],instances=instance, preTilePath='socket',die=die, checktype = 'pcode_ia_min_ratio')
			mesh_val = PySV(tiles=sktnum, PathTemplates = ['uncore'],instances=mesh_inst, preTilePath='socket',die=die, checktype = meshcv)
			
			## Dumps all fuse data if option is selected
			if regfuse:
				for fuse in die_inst._instances:

					# VF curve voltage values
					for vcurve in vcurves:
						for idx in idxs:
							for curve in curves['vf_curve']:
								new_curve = curve
								new_curve = new_curve.replace(f'##curve##',str(vcurve))
								new_curve = new_curve.replace(f'##idx##',str(idx))								
								pointvalue = fuse.readregister(new_curve)
								printData(data_vf, new_curve, die, hex(pointvalue))
			
			# Dumps current core voltage valus if option is selected
			if regcv:
				for mesh in mesh_val._instances:

					for core in range(64):
						svregister = f'io_wp_ia_cv_ps_{core}'
						meshvalue = mesh.readregister(svregister).readfield('voltage')
						printData(data_read, f'{svregister}.voltage', die, hex(meshvalue))
					#print(f'{meshcv}.ratio = {hex(meshvalue)}')
		if regfuse:

			printTable(data_vf, "IA VF Curve Values (VOLTAGE)")
		if regcv:
			printTable(data_read, "IA Voltage Current Values")

## DPM Tileview for error logs
def logger(visual = '', qdf = '', TestName='', Testnumber = 0, dr_dump = True, chkmem = 0, debug_mca = 0, folder=None, WW = '', Bucket = 'UNCORE', UI=False, refresh = False, logging = None, upload_to_disk = False, upload_to_danta = False):
	gcm.svStatus(refresh=refresh)
	
	if folder == None:
		folder = log_folder
	if visual == '':
		visual = visual_str()
	
		if visual == '' and not UI:
			visual = input(" Enter Unit Visual ID: ")
	
	if qdf == '':
		qdf = qdf_str()

	product = config.SELECTED_PRODUCT #product_str()
	
	if WW == '':
		#currentdate = datetime.date.today()
		#iso_calendar = currentdate.isocalendar()
		WW = getWW()
	#test = f'{loop}_{visual}_{testname}'
	
	if UI: dpmlog.callUI(qdf = qdf, ww = WW, product = product)   		
	else: 
		try:
			dpmtileview.run(visual, Testnumber, TestName, chkmem, debug_mca, dr_dump = dr_dump, folder = folder, WW = WW, Bucket = Bucket, product = product, QDF = qdf, logger = logging, upload_to_disk = upload_to_disk, upload_to_danta = upload_to_danta)
			
		except Exception as e:
			print(f"!!! Something went wrong with the script: {e}. Retrying with a forced sv and ipc refresh...")
			gcm.svStatus(refresh=True)
			dpmtileview.run(visual, Testnumber, TestName, chkmem, debug_mca, dr_dump = dr_dump, folder = folder, WW = WW, Bucket = Bucket, product = product, QDF = qdf, logger = logging, upload_to_disk = upload_to_disk, upload_to_danta = upload_to_danta)

def u600w(check=True):
	u600f = {'compute':[],'io':[]}

	u600f['computes'] = ['pcu.pcode_sst_pp_0_power=0x226','pcu.punit_ptpcioregs_package_power_sku_pkg_min_pwr_fuse=0xa50','pcu.pcode_non_vccin_power=0x300','pcu.pcode_pkg_icc_max_app=0x23f','pcu.pcode_loadline_res=0x4','pcu.pcode_loadline_res_rev2=0x190','pcu.pcode_pkg_icc_max=0x2ee','pcu.pcode_pkg_icc_p1_max=0x2ee']
	u600f['ios'] = ['punit_iosf_sb.pcode_sst_pp_0_power=0x266','punit_iosf_sb.pmsrvr_ptpcioregs_package_power_sku_pkg_min_pwr_fuse=0xa50','punit_iosf_sb.pcode_non_vccin_power=0x300','punit_iosf_sb.pcode_pkg_icc_max_app=0x23f','punit_iosf_sb.pcode_loadline_res=0x4','punit_iosf_sb.pcode_loadline_res_rev2=0x190','punit_iosf_sb.pcode_pkg_icc_max=0x2ee','punit_iosf_sb.pcode_pkg_icc_p1_max=0x2ee']

	if check: pseudo_efi_check(u600f)

	return u600f

def reset_600w():
	u600f = u600w(check = False)
	print(f'>>> Using Bootscript to start the unit <<< ')
	print(f'>>> Compute fuses: {u600f["computes"]}')
	print(f'>>> IO fuses: {u600f["ios"]}')
	b.go(pwrgoodmethod='usb', pwrgoodport=1, pwrgooddelay=30, fused_unit=True, enable_strap_checks=False,compute_config=COMPUTE_CONFIG,enable_pm=True,segment=SEGMENT, fuse_str_compute = u600f['computes'], fuse_str_io = u600f['ios'])

## Calls the PortID tool
def find_portid(id=0x5808):
	p2ip.find_ip(portid=id)

## HWLS Check -- CWF
def hwls_miscompare(logger=None):
	if config.SELECTED_PRODUCT == 'CWF':
		logger = print if logger == None else print
		gcm.svStatus()
		modules = sv.sockets.computes.cpu.modules
		try:
			logger(f'Collecting HWLS Data')
			for module in modules:
				pair_0 = module.bus_cr_lockstep_miscompare_status_core_pair_0
				pair_1 = module.bus_cr_lockstep_miscompare_status_core_pair_1
				logger(f'HWLS_INFO_{module.name.upper()}_P0:{pair_0:#x}_P1:{pair_1:#x}')
		except Exception as e:
			logger(f'Error reading bus_cr_lockstep_miscompare_status_core_pair for module: {e}')
	
	else:
		logger(f'Function not available for this product: {config.SELECTED_PRODUCT}')

## BIOS Knobs edit for bootscript usage
def bsknobs(readonly = False, skipinit = False):
	import pysvtools.xmlcli.nvram as nvram
	ipc = ipccli.baseaccess()
	ram = nvram.getNVRAM()
	if not skipinit: gcm.svStatus()
	#knobs = {'DfxS3mSoftStrap':0, 'DfxSkipWarmResetPromotion':1}
	print(f'>>> Checking BIOS configuration knobs: DfxS3mSoftStrap, DfxSkipWarmResetPromotion, DwrEnable and IerrResetEnabled <<< ')
	#biosknobs(knobs=knobs, readonly=False)

	try:
		
		ram.pull()
		print(' -- BIOS Knob Data collected -- ')
		Softstrap_val = ram.DfxS3mSoftStrap.getValue()
		Sofstrap_str = ram.DfxS3mSoftStrap.getString()
		
		SkipWarmResetPromotion_val = ram.DfxSkipWarmResetPromotion.getValue()
		SkipWarmResetPromotion_str = ram.DfxSkipWarmResetPromotion.getString()

		DwrEnable_val = ram.DwrEnable.getValue()
		DwrEnable_str = ram.DwrEnable.getString()

		IerrResetEnabled_val = ram.IerrResetEnabled.getValue()
		IerrResetEnabled_str = ram.IerrResetEnabled.getString()
		
		change = False
		
		if Softstrap_val != 0:
			if readonly:
				print(f'> DfxS3mSoftStrap {Softstrap_val} value not Disabled, needs to be changed < ')
			else:
				print(f'> DfxS3mSoftStrap {Sofstrap_str} changing it to Disable < ')
				ram.DfxS3mSoftStrap = 0
			change = True

		if SkipWarmResetPromotion_val != 2:
			if readonly:
				print(f'> DfxSkipWarmResetPromotion {SkipWarmResetPromotion_str} value not Auto, needs to be changed < ')
			else:
				print(f'> DfxSkipWarmResetPromotion {SkipWarmResetPromotion_str} changing it to Auto < ')
				ram.DfxSkipWarmResetPromotion = 2
			change = True

		if DwrEnable_val != 1:
			if readonly:
				print(f'> DwrEnable {DwrEnable_str} value not Enabled, needs to be changed < ')
			else:
				print(f'> DwrEnable {DwrEnable_str} changing it to Enabled < ')
				ram.DwrEnable = 1
			change = True

		if IerrResetEnabled_val != 0:
			if readonly:
				print(f'> IerrResetEnabled {IerrResetEnabled_val} value not Disabled, needs to be changed < ')
			else:
				print(f'> IerrResetEnabled {IerrResetEnabled_str} changing it to Disable < ')
				ram.IerrResetEnabled = 0
			change = True

		if change:
			if readonly:
				print('>>> Issues with BIOS Knobs, update the knobs to avoid issues during boot...  ')
			else:
				print('>>> Updating data into BIOS nvram...  ')
				ram.push()
				print(f'>>> Bios Updated with SoftStrap: {Sofstrap_str} and SkipWarmResetPromotion: {SkipWarmResetPromotion_str} <<< ')
				print(f'>>> Bios Updated with IerrResetEnabled: {IerrResetEnabled_str} and DwrEnable: {DwrEnable_str}  <<< ')
		else:
			print(f'>>> Bios properly set with SoftStrap: {Sofstrap_str} and SkipWarmResetPromotion: {SkipWarmResetPromotion_str} <<< ')
			print(f'>>> Bios properly set with IerrResetEnabled: {IerrResetEnabled_str} and DwrEnable: {DwrEnable_str}  <<< ')

	except:
		print('>>> Error pulling/updating data from/to NVRAM, try again or use PYFIT to edit and check your bios')
		print(r'>>> PYFIT script: C:\PythonSV\graniterapids\users\kwadams\staging\pyfit')
		print('> For proper Bootscript usage the following knobs needs to be configured as follow:')
		print('> DfxS3mSoftStrap = "Disable"')
		print('> DfxSkipWarmResetPromotion = "Auto">')
		print('> IerrResetEnabled = "Disable">')
		print('> DwrEnable = "Enabled">')

## BIOS Knobs edit use key for knob and set the desired value	
def biosknobs(knobs = {}, readonly=False):
	import pysvtools.xmlcli.nvram as nvram
	ipc = ipccli.baseaccess()
	ram = nvram.getNVRAM()
	gcm.svStatus()

	try:
		ram.pull()
		print(' -- BIOS Knob Data collected -- ')
		change = False

		for k, v in knobs.items():

			if ram.searchNames(name=k, exact=True):
				cv = ram.getByName(k)
				if readonly:
					print(f' -- Bios knob value --- {k} : {cv.getString()} ')
				else:
					if v!= cv.getValue():
						ram.setByName(k,v)
						print(f' -- Bios knob {k} changed from: {cv.getValue()} --> {v} ')
						change = True
					else:
						print(f' -- Bios knob {k} value already set at requested value. {cv.getString()} --> {cv.getValue()}:{v} ')

			else:
				print(f' -- Bios knob {k} not found ')
			
			if change: ram.pull()
			if readonly: return ram
		
	
	except:
		print(' -- Error pulling/updating data from/to NVRAM, try again or use PYFIT to edit and your bios')

## ROM to RAM update for fuses checks
def fuseRAM(refresh = False):
	#sv = _get_global_sv()
	if refresh: gcm.svStatus()
	print ("Loading fuse data from ROM to RAM .... ")
	sv.sockets.computes.fuses.load_fuse_ram()
	if config.SELECTED_PRODUCT.upper() != 'CWF': sv.sockets.ios.fuses.load_fuse_ram()

## Tool for fuse checking of the unit
def fuses(rdFuses = True, sktnum =[0], printFuse=False):
	sv = _get_global_sv()
	_fuse_instance = config.FUSE_INSTANCE#['hwrs_top_ram']
	
	# We can remove this by using the sv.sockets[sktnum].computes.names
	#product = {	'gnrsp': 	['compute0', 'compute1'],
	#			'gnrap':	['compute0', 'compute1', 'compute2']}
	computes = []
	computes.extend(sv.socket0.computes.name)

	_masks = {value: {'ia':None,'llc':None} for value in computes}

	if rdFuses:
		fuseRAM()
		#print ("Loading fuse data from RAM to update Mask info")
		#sv.sockets.computes.fuses.load_fuse_ram()
		#sv.sockets.ios.fuses.load_fuse_ram()
	
	## This is to print the fuses in a table format
	fusetable = [['Fuse','Value']]

	masks = {	'ia_compute_0' : None,
				'ia_compute_1' : None,
				'ia_compute_2' : None,
				'llc_compute_0' : None,
				'llc_compute_1' : None,
				'llc_compute_2' : None,
						}
	
	for compute in computes:
		_fuse = PySV(tiles=sktnum, PathTemplates = ['fuses'],instances=_fuse_instance, preTilePath='socket',die=compute, checktype = '')
		_computeN = compute.replace('compute','')
		for fuse in _fuse._instances:
			_masks[compute]['ia'] = fuse.ip_disable_fuses_dword6_core_disable.read()
			_masks[compute]['llc'] = fuse.ip_disable_fuses_dword2_llc_disable.read()
		
		#_computeN = compute.replace('compute','')
		llcmask = _masks[compute]['llc']
		iamask = _masks[compute]['ia']
		masks[f'ia_compute_{_computeN}'] = iamask
		masks[f'llc_compute_{_computeN}'] = llcmask
		fusetable.append([f'ia_compute_{_computeN}',hex(iamask)])
		fusetable.append([f'llc_compute_{_computeN}',hex(llcmask)])


	
	if printFuse:
		print (f'\n>>> Current System fused masks:\n')
		#print (f'orig_compute0 = {hex(int(mask_c0,2))}')
		
	#for value in product[system]:
	#	_computeN = value.replace('compute','')
	#	llcmask = _masks[value]['llc']
	#	iamask = _masks[value]['ia']
	#	masks[f'ia_compute_{_computeN}'] = iamask
	#	masks[f'llc_compute_{_computeN}'] = llcmask
	#	fusetable.append([f'ia_compute_{_computeN}',hex(iamask)])
	#	fusetable.append([f'llc_compute_{_computeN}',hex(llcmask)])

	if printFuse:		
		print(tabulate(fusetable, headers="firstrow", tablefmt='grid'))

		#	print (f'>>> system_llc_mask_compute{_computeN} = {llcmask}')
		#	print (f'>>> system_core_mask_compute{_computeN} = {iamask}')
	
	return masks

## Tool for converting current unit fuses to a pseudo format, considers all three CLASS fuse configurations
## With the latest update it also shows the RowPass Masks as they were included in the config file
def pseudomask(combine = False, boot = False, Type = 'Class', ext_mask = None):
	
	sv = _get_global_sv()
	syscomputes = sv.socket0.computes.name
	product = config.PRODUCT_CONFIG.lower()
	ClassMask, ClassMask_sys, Masks_test = pseudo_type(Type, product)
	
	# Product Specific Function for Masking in pseudo Configuration
	
	ClassMask_sys = pf.pseudo_masking(ClassMask, ClassMask_sys, syscomputes)

	if ext_mask is None:
		masks = fuses()
	else:
		masks = ext_mask

	
	for compute in syscomputes:
		comp_N = sv.socket0.get_by_path(compute).target_info.instance

		_iamask = masks[f'ia_compute_{comp_N}']
		_llc_mask = masks[f'llc_compute_{comp_N}']
		
		if combine:
			_iamask = bin(_iamask | _llc_mask)
		else:
			_iamask = bin(_iamask)
			_llc_mask = bin(_llc_mask)
		
		for key in ClassMask_sys.keys():
			if key not in ClassMask.keys():
				continue

			iaMask = int(_iamask,2) | int(ClassMask_sys[key][compute],2)

			if combine:
				llcMask = iaMask
			else:
				llcMask = int(_llc_mask,2) | int(ClassMask_sys[key][compute],2)

			ia_core_disable_compute = hex(iaMask)
			llc_slice_disable_compute = hex(llcMask)

			Masks_test[key][f'core_comp_{comp_N}'] = ia_core_disable_compute
			Masks_test[key][f'llc_comp_{comp_N}'] = llc_slice_disable_compute


	if not boot:
		
		core_string = ''
		cha_string = ''
		for key in ClassMask_sys.keys():
			if key not in ClassMask.keys():
				continue
			print (f'\nMasks for pseudo {key} \n')
			for compute in syscomputes:
				comp_N = sv.socket0.get_by_path(compute).target_info.instance
				llc_mask = Masks_test[key][f'llc_comp_{comp_N}']
				ia_mask = Masks_test[key][f'core_comp_{comp_N}']
				
				ia_string = f'ia_core_disable_compute_{comp_N} = {ia_mask},'
				llc_string = f'llc_slice_disable_compute_{comp_N} = {llc_mask},'
				
				print (ia_string)
				print (llc_string)

				core_string += ia_string
				cha_string += llc_string
			bootstring = core_string + cha_string
			print (f"\nAdd the following to your bootscript to use the pseudo for {key} \n")
			print (bootstring)

	else:
		## Used with the pseudo_bs function, wont print fuse data, just return the Mask values to be processed by the script
		return Masks_test

## Uses pseudo Mask configurations to boot the unit, applying the HT disabled fuses to leave it ready for Dragon Pseudo
## Added a S2T key to work with the MESH S2T modes
def pseudo_bs(ClassMask = 'FirstPass', Custom = [], boot = True, use_core = False, htdis = True, dis_2CPM = None, fuse_read = True, s2t = False, masks = None, clusterCheck = None, lsb = False, fuse_compute =None, fuse_io = None, fast =False, ppvcfuse = False, skip_init = False,  vbump = {'enabled':False, 'type':['cfc'],'offset': 0,'computes':['compute0', 'compute1', 'compute2']}):
	#vbump = {'type':['cfc'],'offset': 0,'computes':['compute0', 'compute1', 'compute2']}
	if not skip_init: gcm.svStatus(refresh=True)
	vbump_target = vbump['computes']
	vbump_type = vbump['type']
	vbump_offset = vbump['offset']
	vbump_array = {'compute0': [],'compute1': [],'compute2': [],}
	ppvc_config = {	'compute0':[],
			   		'compute1':[],
					'compute2':[],
					'io0':[],
					'io1':[],}
	cfc_array = []
	io_array = []
	ia_array = []
	
	# Init fuse string arrays
	fuse_str_0 = []
	fuse_str_1 = []
	fuse_str_2 = []

	htdis_comp = []
	htdis_io = []
	dis_2CPM_comp = []

	vbump_enabled = vbump['enabled']

	#sv = _get_global_sv()
	product = config.PRODUCT_CONFIG.lower()
	variant = config.PRODUCT_VARIANT
	syscomputes = sv.socket0.computes.name
	if clusterCheck == None: clusterCheck = False

	## Assign Cluster values *can be taken from a pythonsv register, update later on
	if variant == 'AP': cluster = 6
	elif variant == 'SP': cluster = 4
	else: cluster = 2
	
	#if product == 'gnrap':
	
	## Mask Type by default we use Class, but if Custom is used we change it to user, might remove this later on
	mType = 'Class'	
	if ClassMask == 'Custom':
		mType = 'User'
	elif ClassMask == 'External':
		mType = 'External'

	## Hyper Threading Disable fuses needed to run Dragon pseudo content
	if htdis:
		htdis_comp = ['scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_fused_ht_dis=0x1', 'pcu.capid_capid0_ht_dis_fuse=0x1','pcu.pcode_lp_disable=0x2','pcu.capid_capid0_max_lp_en=0x1']
		htdis_io = ['punit_iosf_sb.soc_capid_capid0_max_lp_en=0x1','punit_iosf_sb.soc_capid_capid0_ht_dis_fuse=0x1']

	if dis_2CPM != None:
		dis_2CPM_comp = fuses_dis_2CPM(dis_2CPM, bsformat = True)

	#External fuses added for BurnIn script use
	if fuse_compute == None: fuse_compute = []
	if fuse_io == None: fuse_io = []
	
	## Init Variables and default arrays
	ValidClass = ['FirstPass', 'SecondPass', 'ThirdPass', 'RowPass1', 'RowPass2', 'RowPass3']
	ValidRows = ['ROW1','ROW2','ROW5','ROW6','ROW7']
	ValidCols = ['COL0','COL1','COL2','COL3','COL4','COL5','COL6','COL7','COL8','COL9']
	ValidCustom = ValidRows + ValidCols
	Fmask = '0xfffffffffffffff'
	CompareMask = 	{		'Custom':	{'core_comp_0':Fmask,'core_comp_1':Fmask,'core_comp_2':Fmask,'llc_comp_0':Fmask,'llc_comp_1':Fmask,'llc_comp_2':Fmask},
							}


	## This code can be merged with the mType at the start of code
	if mType == 'Class':
		valid_masks = ValidClass
	elif mType == 'User':
		valid_masks = ValidCustom
	elif mType == 'External':
		valid_masks = ValidCustom
	else:
		print('>>> No valid Mask type selected options: Class or Rows')
		sys.exit()

	## Print data depending on the selection  - Take from Configs
	Class_help = {	'FirstPass': 'Booting only with Columns 0, 3, 6 and 9',
					'SecondPass': 'Booting only with Columns 1, 4, and 7',
					'ThirdPass': 'Booting only with Columns 2, 5, and 8 (Applies to X3)',
					'RowPass1': 'Booting only with CDIE0 - Rows [1,2], CDIE1 - Rows [5,6], CDIE2 - Rows [7]',
					'RowPass2': 'Booting only with CDIE0 - Rows [5,6], CDIE1 - Rows [7], CDIE2 - Rows [1,2]',
					'RowPass3': 'Booting only with CDIE0 - Rows [7], CDIE1 - Rows [1,2], CDIE2 - Rows [5,6]',
					'Custom' : 'Booting with user mix & match configuration, Cols or Rows',
					'External' : 'Use configuration from file .\\ConfigFiles\\GNRMasksDebug.json'
	}
	
	## Checks if the selected ClassMask option is valid
	if ClassMask not in valid_masks:
		if ClassMask == 'Custom':
			for mvalue in Custom:
				#print(valid_masks)
				if mvalue.upper() not in valid_masks:
					
					print(f'>>> Masks to be used in Custom, should be either:')
					#print(f' -- ClassMasks:{ValidClass}')
					print(f'> Rows:{ValidRows}')
					print(f'> Columns:{ValidCols}')
					sys.exit()
		elif ClassMask == 'External':
			print(f'>>> Using external Debug Mask found in file ../ConfigFiles/GNRMasksDebug.json')
		else:			
			print(f'>>> Not a valid ClassMask selected use: FirstPass, SecondPass or ThirdPass')
			sys.exit()
	
	## Checks for system masks, either external input or checking current system values
			
	if masks == None: origMask = fuses(rdFuses = fuse_read)
	else: origMask = masks

	## Custom Mask Build - Will add a Core count at the end to validate if pseudo can be used...
	if ClassMask == 'Custom':
	

		for _CustomVal in Custom:
			CustomVal = _CustomVal.upper()
			Loop_mask = pseudomask(combine = use_core, boot = True, Type = mType, ext_mask = origMask)
			
			CompareMask['Custom']['core_comp_0'] = hex(int(Loop_mask[CustomVal]['core_comp_0'],16) & int(CompareMask['Custom']['core_comp_0'],16))
			CompareMask['Custom']['core_comp_1'] = hex(int(Loop_mask[CustomVal]['core_comp_1'],16) & int(CompareMask['Custom']['core_comp_1'],16))
			if variant == 'AP': CompareMask['Custom']['core_comp_2'] = hex(int(Loop_mask[CustomVal]['core_comp_2'],16) & int(CompareMask['Custom']['core_comp_2'],16))

			CompareMask['Custom']['llc_comp_0'] = hex(int(Loop_mask[CustomVal]['llc_comp_0'],16) & int(CompareMask['Custom']['llc_comp_0'],16))
			CompareMask['Custom']['llc_comp_1'] = hex(int(Loop_mask[CustomVal]['llc_comp_1'],16) & int(CompareMask['Custom']['llc_comp_1'],16))
			if variant == 'AP': CompareMask['Custom']['llc_comp_2'] = hex(int(Loop_mask[CustomVal]['llc_comp_2'],16) & int(CompareMask['Custom']['llc_comp_2'],16))
		
		Masks_test = CompareMask

	## Class Mask Build, depending on the selected option of First/Second or Third Pass
	else:
		Masks_test = pseudomask(combine = use_core, boot = True, Type = mType, ext_mask = origMask)
	

	Masks_test, core_count, llc_count = masks_validation(masks = Masks_test, ClassMask = ClassMask, dies = syscomputes, product = product, _clusterCheck = clusterCheck, _lsb = lsb)

	core_comp0 = Masks_test[ClassMask]['core_comp_0']
	core_comp1 = Masks_test[ClassMask]['core_comp_1']
	if variant == 'AP': core_comp2 = Masks_test[ClassMask]['core_comp_2']

	llc_comp0 = Masks_test[ClassMask]['llc_comp_0']
	llc_comp1 = Masks_test[ClassMask]['llc_comp_1']
	if variant == 'AP': llc_comp2 = Masks_test[ClassMask]['llc_comp_2']


	# Voltage bumps

	if ('cfc' in vbump_type and vbump['enabled']) and not ppvcfuse:
		cfc_array = fuses_cfc_vbumps(offset =  vbump_offset, point = None, fixed_voltage = None, target_compute = None, computes = 3)
		
		for vbump_targ in vbump_target:
			if vbump_target != None and vbump_targ in syscomputes:
				base = f'sv.socket0.{vbump_targ}.fuses.'
				computearray = []
				print(f'>>> Splitting the array for one compute only: Target {vbump_targ}')
				for item in cfc_array:
					if vbump_targ in item:
						fuse = item.replace(base,'')
						fuse = fuse.replace(' ','')
						print(f'> {vbump_targ} fuse --> {fuse}')
						computearray.append(fuse)
				#computearray = bs_fuse_fix(fuse_str = computearray, bases = ['sv.sockets.computes.fuses.'])
				vbump_array[vbump_targ] = vbump_array[vbump_targ] + computearray

	if ('ia' in vbump_type and vbump['enabled']) and not ppvcfuse:
		ia_array = fuses_ia_vbumps(offset = vbump_offset, rgb_array={}, skip_init=False, curve=None, point=None, index=None, fixed_voltage=None, target_compute=None)
		
		for vbump_targ in vbump_target:
			if vbump_target != None and vbump_targ in syscomputes:
				base = f'sv.socket0.{vbump_targ}.fuses.'
				computearray = []
				print(f'>>> Splitting the array for one compute only: Target {vbump_targ}')
				for item in ia_array:
					if vbump_targ in item:
						fuse = item.replace(base,'')
						fuse = fuse.replace(' ','')
						print(f'> {vbump_targ} fuse --> {fuse}')
						computearray.append(fuse)
				#computearray = bs_fuse_fix(fuse_str = computearray, bases = [f'sv.sockets.{vbump_targ}.fuses.'])
				vbump_array[vbump_targ] = vbump_array[vbump_targ] + computearray

	## WIP
	if ('io' in vbump_type and vbump_type['enabled']) and not ppvcfuse:
		cfcarray = fuses_cfc_vbumps(offset =  vbump_type['offset'], point = None, fixed_voltage = None, target_compute = None, computes = 3)

	if ppvcfuse:
		ppvc_config = ppvc(bsformat=True)


	if not s2t:
		## Bootscript with or without htdis fuses
		if variant == 'AP': 
			bscript_0 = f"pwrgoodmethod='usb', pwrgoodport=1, pwrgooddelay=30, fused_unit=True, enable_strap_checks=False,compute_config='{COMPUTE_CONFIG}',enable_pm=True,segment='{SEGMENT}',ia_core_disable_compute_0 = {core_comp0},ia_core_disable_compute_1 = {core_comp1},ia_core_disable_compute_2 = {core_comp2},llc_slice_disable_compute_0 = {llc_comp0},llc_slice_disable_compute_1 = {llc_comp1},llc_slice_disable_compute_2 = {llc_comp2}"
		
		elif variant == 'SP':
			bscript_0 = f"pwrgoodmethod='usb', pwrgoodport=1, pwrgooddelay=30, fused_unit=True, enable_strap_checks=False,compute_config='{COMPUTE_CONFIG}',enable_pm=True,segment='{SEGMENT}',ia_core_disable_compute_0 = {core_comp0},ia_core_disable_compute_1 = {core_comp1},llc_slice_disable_compute_0 = {llc_comp0},llc_slice_disable_compute_1 = {llc_comp1}"
		 
		## Checks for htdis option, might recode this at some point this a bit of a lazy way to do it, will also include the option to add custom fuse strings and fuse files, later on.

		fuse_str_0 = fuse_compute + vbump_array['compute0'] + htdis_comp + dis_2CPM_comp + ppvc_config['compute0']
		fuse_str_1 = fuse_compute + vbump_array['compute1'] + htdis_comp + dis_2CPM_comp + ppvc_config['compute1']
		if variant == 'AP':  fuse_str_2 = fuse_compute + vbump_array['compute2'] + htdis_comp + dis_2CPM_comp + ppvc_config['compute2']
		fuse_io_0 = htdis_io + fuse_io + ppvc_config['io0']
		fuse_io_1 = htdis_io + fuse_io + ppvc_config['io1']
		#bscript_1 = f", fuse_str_compute = {htdis_comp + fuse_compute},fuse_str_io = {htdis_io + fuse_io}"


		if variant == 'AP':
			bscript_1 =f", fuse_str_compute_0 = {fuse_str_0},fuse_str_compute_1 = {fuse_str_1},fuse_str_compute_2 = {fuse_str_2},fuse_str_io_0 = {fuse_io_0},fuse_str_io_1 = {fuse_io_1}"
		elif variant == 'SP':
			bscript_1 =f", fuse_str_compute_0 = {fuse_str_0},fuse_str_compute_1 = {fuse_str_1},fuse_str_io_0 = {fuse_io_0},fuse_str_io_1 = {fuse_io_1}"
		else:
			bscript_1 =f", fuse_str_compute = {fuse_str_0},fuse_str_io = {fuse_io_0}"

		## Display data on screen, showing configuration to be used based on selection
		print (f'\n>>>  Bootscript configuration for {ClassMask} ')
		print (f'>>>  {Class_help[ClassMask]}')
		if ClassMask == 'Custom': 
			print (f'>>>  Custom Mask Selected: {Custom}')
		print (f'>>>  Core/LLC enabled total Count: CORE = {core_count}, LLC = {llc_count}')
		print (f'>>>  Using Compute 0 Masks: CORE = {core_comp0}, LLC = {llc_comp0}')
		print (f'>>>  Using Compute 1 Masks: CORE = {core_comp1}, LLC = {llc_comp1}')
		if variant == 'AP': print (f'>>>  Using Compute 2 Masks: CORE = {core_comp2}, LLC = {llc_comp2}')
		if htdis:print (f'>>>  Applying HT Disabled Fuses : Computes = {htdis_comp}')
		if htdis:print (f'>>>  Applying HT Disabled Fuses : Computes = {htdis_io} \n')
		print (f'>>>  Running Bootscript: \n') 
		print (f">>>  b.go({bscript_0}{bscript_1})")
		

		fuse_option = {'compute0':fuse_str_0,'compute1':fuse_str_1,'compute2':fuse_str_2,'io0':fuse_io_0,'io1':fuse_io_1}
		## Either run the bootscript or just print the bootscript string in case additional feats need to be added on it.
		if fast:
			print (f'>>>  FastBoot option is selected - Starting Boot with Warm Reset')
			print (f'>>>  Be aware, this only changes the CoreMasks keeping current CHA configuration') 
			fast_fuses = []
			fast_fuses += ["sv.socket0.compute0.fuses." + _f for _f in fuse_str_0]
			fast_fuses += ["sv.socket0.compute1.fuses." + _f for _f in fuse_str_1]
			fast_fuses += ["sv.socket0.compute2.fuses." + _f for _f in fuse_str_2]
			fast_fuses += ["sv.socket0.io0.fuses." + _f for _f in fuse_io_0]
			fast_fuses += ["sv.socket0.io1.fuses." + _f for _f in fuse_io_1]			

			fast_fuses += gcm.mask_fuse_core_array(coremask = {'compute0':int(core_comp0,16), 'compute1':int(core_comp1,16), 'compute2':int(core_comp2,16)})

			print (f'>>>  Fuse Configuration to be used in FastBoot\n',fast_fuses) 
			gcm.fuse_cmd_override_reset(fuse_cmd_array=fast_fuses, skip_init=False, boot = boot, s2t=s2t)
			
			# Waits for EFI and checks fuse application
			# pseudo_efi_check(fuse_option)
			gcm.coresEnabled()
			#fast_fuses = []
		elif boot: 
			
			print (f'>>>  Boot option is selected - Starting Bootscript') 
		#	if htdis:
			if variant == 'AP': b.go(pwrgoodmethod='usb', pwrgoodport=1, pwrgooddelay=30, fused_unit=True, enable_strap_checks=False,compute_config=COMPUTE_CONFIG,enable_pm=True,segment=SEGMENT,ia_core_disable_compute_0 = core_comp0,ia_core_disable_compute_1 = core_comp1,ia_core_disable_compute_2 = core_comp2,llc_slice_disable_compute_0 = llc_comp0,llc_slice_disable_compute_1 = llc_comp1,llc_slice_disable_compute_2 = llc_comp2, fuse_str_compute_0 = fuse_str_0, fuse_str_compute_1 = fuse_str_1, fuse_str_compute_2 = fuse_str_2,fuse_str_io_0 = fuse_io_0,fuse_str_io_1 = fuse_io_1)
			if variant == 'SP': b.go(pwrgoodmethod='usb', pwrgoodport=1, pwrgooddelay=30, fused_unit=True, enable_strap_checks=False,enable_pm=True,ia_core_disable_compute_0 = core_comp0,ia_core_disable_compute_1 = core_comp1,llc_slice_disable_compute_0 = llc_comp0,llc_slice_disable_compute_1 = llc_comp1, fuse_str_compute_0 = fuse_str_0, fuse_str_compute_1 = fuse_str_1,fuse_str_io_0 = fuse_io_0,fuse_str_io_1 = fuse_io_1)
			
			# Waits for EFI and checks fuse application
			pseudo_efi_check(fuse_option)

		else: 
			print (f'\n>>>  Boot option not selected -- Copy bootscript code  above and edit if needed to run manually') 
	else:
		return core_count, llc_count, Masks_test

## PSEUDO bs EFI Checks
## Looks for fuse application, in case one of them is not applied will raise a flag
## Checks masking with coresenabled and fuse applied with the fuse override check script
def pseudo_efi_check(fuses):
		print(f'>>>  Waiting for EFI PostCode')
		EFI_POST = gcm.EFI_POST
		gcm._wait_for_post(EFI_POST, sleeptime=60)

		print(f'>>>  Checking all Fuses for Compute0 Applied correctly')
		fuseRAM(refresh=True)

		for f in fuses.keys():
			if f: 
				print(f'>>> Checking fuse application for {f.upper()}')
				gcm.fuse_cmd_override_check(fuse_cmd_array = fuses[f], skip_init= True, bsFuses = f)
		
		gcm.coresEnabled()	

## Unit VID, PRODUCT and QDF checks
def visual_str(socket = sv.socket0, die = 'compute0'):
	scriptHome = os.path.dirname(os.path.realpath(__file__))
	catts_db = rf"{scriptHome}\EFI Tools\catts_db\CattsWrapper.exe"
	#print(catts_db)
	#def get_visual_id(ult_txt_str):
	#	db = subprocess.Popen([catts_db, ult_txt_str], stdout=subprocess.PIPE)
	#	return db.communicate()[0].decode().strip()	

	try:
		#vid = get_visual_id(fu.get_ult(socket=socket, tile=die, ult_in=None)['textStr'])
		vid = fu.get_visual_id(socket=socket, tile=die)
	except:
		print('!!! Error Accessing CATTS...')
		print('!!! Unable to collect Unit Visual ID Data...')
		return ''
	return vid

def request_unit_info():
	data = reqinfo.get_unit_info(sv=sv, ipc=ipc)
	return data
	
def qdf_str():
	qdf = fu.get_qdf_str(socket=sv.socket0, die='cbb0.base')
	return qdf

def product_str(): # DMR will use device_name
	#product = sv.socket0.target_info["device_name"].upper()
	product = config.PRODUCT_CONFIG.upper()
	return product

def variant_str():
	#variant = sv.socket0.target_info["variant"].upper()
	variant = config.PRODUCT_VARIANT.upper()
	return variant

def chop_str():
	#chop = sv.socket0.target_info["chop"].upper()
	chop = config.PRODUCT_CHOP.upper()
	return chop

def get_compute_index(core=None):
	return int(core/config.MAXPHYSICAL)

def ppvc_option():
	selection = None
	product = product_str()
	chop = chop_str()

	if product == 'GNRAP':
		if chop == 'UCC':
			selection = 'GNR AP UCC X3'

	if product == 'GNRSP':
		if chop == 'XCC':
			selection = 'GNR SP XCC'
		if chop == 'HCC':
			selection = 'GNR SP HCC'
		if chop == 'LCC':
			selection = 'GNR SP LCC'
			
	if product == 'CWFAP':
		#if chop == 'XDCC':
		selection = 'CWF AP XDCC X3'

	if product == 'CWFSP':
		#if chop == 'HDCC':
		selection = 'CWF SP HDCC X2'

	return selection

## PPVC Fuses configuration, 
def ppvc(bsformat = False, ppvc_fuses = [], updateram=False):
	print("\n***********************************v********************************************")
	print(f'Searching for PPVC fuses, please enter requested values for proper configuration:')
	#ppvc_fuses = f.ppvc_rgb_reduction(boot=False)
	## I have rebuilt the ppvc script here instead of using what is in GFO in case additional customization is needed
	if updateram: fuseRAM(refresh = False)
	#syscomputes = sv.socket0.computes.name
	ppvc_confg = {	'compute0':[],
			   		'compute1':[],
					'compute2':[],
					'io0':[],
					'io1':[],}
	qdf = qdf_str()
	selection = ppvc_option()

	print(f'Current Unit QDF: {qdf}')
	print(f'Current Unit Product: {selection}')
	try: rgb_values = f.get_rgb_values(qdf, selection)
	except: 
		print(f'Failed collecting data for QDF: {qdf}. ')
		user_input = input(">>> Do you want to try with a different QDF? Y/[N]]: ")
		if user_input.upper() == 'Y':   	
			rgb_values = f.get_rgb_values()
		else:
			print(f'Skipping PPVC Configuration --')
			return ppvc_confg
		
	#computes = len(syscomputes)
	ppvc_fuses+=f.ia_vbump_array(rgb_array=rgb_values) # Adding IA fuses
	ppvc_fuses+=f.cfc_vbump_array(rgb_array=rgb_values) # Adding CFC fuses
	ppvc_fuses+=f.hdc_vbump_array(rgb_array=rgb_values) # Adding HDC fuses
	ppvc_fuses+=f.ddrd_vbump_array(rgb_array=rgb_values) # Adding DDRD fuses
	ppvc_fuses+=f.cfc_io_vbump_array(rgb_array=rgb_values) # Adding CFCxIO fuses
	ppvc_fuses+=f.cfn_vbump_array(rgb_array=rgb_values) # Adding CFN fuses
	ppvc_fuses+=f.vccinf_vbump_array(rgb_array=rgb_values) # Adding VCCINF fuses


	fuses_compute0 = [f for f in ppvc_fuses if 'compute0' in f]
	fuses_compute1 = [f for f in ppvc_fuses if 'compute1' in f]
	fuses_compute2 = [f for f in ppvc_fuses if 'compute2' in f]
	fuses_io0 = [f for f in ppvc_fuses if 'io0' in f]
	fuses_io1 = [f for f in ppvc_fuses if 'io1' in f]

	if bsformat:
		print(f'\n {"*"*5} Modifying fuses to be usable in a bootscript array for each die {"*"*5}\n')
		if fuses_compute0: fuses_compute0 = bs_fuse_fix(fuse_str = fuses_compute0, bases = ['sv.socket0.compute0.fuses.'])
		if fuses_compute1: fuses_compute1 = bs_fuse_fix(fuse_str = fuses_compute1, bases = ['sv.socket0.compute1.fuses.'])
		if fuses_compute2: fuses_compute2 = bs_fuse_fix(fuse_str = fuses_compute2, bases = ['sv.socket0.compute2.fuses.'])
		if fuses_io0: fuses_io0 = bs_fuse_fix(fuse_str = fuses_io0, bases = ['sv.socket0.io0.fuses.'])
		if fuses_io1: fuses_io1 = bs_fuse_fix(fuse_str = fuses_io1, bases = ['sv.socket0.io1.fuses.'])
	
	ppvc_confg = {	'compute0':fuses_compute0,
			   		'compute1':fuses_compute1,
					'compute2':fuses_compute2,
					'io0':fuses_io0,
					'io1':fuses_io1,}
	print(f'PPVC configuration fuses collected adding them to boot configuration')
	print("***********************************v********************************************\n")
	return ppvc_confg

## Voltage read for S2T
def tester_voltage(bsformat = False, volt_dict = {}, volt_fuses = [], fixed = True, vbump=False, updateram=False):
	print("\n***********************************v********************************************")
	print(f'Changing Voltage fuses based on System 2 Tester Configuration')
	#ppvc_fuses = f.ppvc_rgb_reduction(boot=False)
	## I have rebuilt the ppvc script here instead of using what is in GFO in case additional customization is needed
	if updateram: fuseRAM(refresh = False)
	#syscomputes = sv.socket0.computes.name
	volt_confg = {	'compute0':[],
			   		'compute1':[],
					'compute2':[],
					'io0':[],
					'io1':[],}
		
	#computes = len(syscomputes)
	if fixed:
		if volt_dict['core'] != None: volt_fuses+=f.ia_vbump_array(fixed_voltage = volt_dict['core']) # Adding IA fuses
		
		
		if isinstance(volt_dict['cfc_die'], dict):
			for k,v in volt_dict['cfc_die'].items():
				if volt_dict['cfc_die'][k] != None:
					volt_fuses+=f.cfc_vbump_array(fixed_voltage = v, target_compute=int(k[-1]))
		else:
			if volt_dict['cfc_die'] != None:
				volt_fuses+=f.cfc_vbump_array(fixed_voltage = volt_dict['cfc_die']) # Adding CFC fuses
		
		
		if isinstance(volt_dict['hdc_die'], dict):
			for k,v in volt_dict['hdc_die'].items():
				if volt_dict['hdc_die'][k] != None: 
					volt_fuses+=f.hdc_vbump_array(fixed_voltage = v, target_compute=int(k[-1]))
		else:
			if volt_dict['hdc_die'] != None: 
				volt_fuses+=f.hdc_vbump_array(fixed_voltage = volt_dict['hdc_die']) # Adding HDC fuses
		
		if volt_dict['ddrd'] != None:volt_fuses+=f.ddrd_vbump_array(fixed_voltage = volt_dict['ddrd']) # Adding DDRD fuses
		#if volt_dict['ddra'] != None:volt_fuses+=f.ddra_vbump_array(fixed_voltage = volt_dict['ddra'], computes = computes) # Adding DDRA fuses -- WIP
		if volt_dict['cfc_io'] != None:volt_fuses+=f.cfc_io_vbump_array(fixed_voltage = volt_dict['cfc_io']) # Adding CFCxIO fuses
	
	elif vbump:
		if volt_dict['core'] != None: volt_fuses+=f.ia_vbump_array(offset = volt_dict['core']) # Adding IA fuses
		#if volt_dict['cfc_die'] != None: volt_fuses+=f.cfc_vbump_array(offset = volt_dict['cfc_die'], computes = computes) # Adding CFC fuses
		#if volt_dict['hdc_die'] != None: volt_fuses+=f.hdc_vbump_array(offset = volt_dict['hdc_die'], computes = computes) # Adding HDC fuses

		if isinstance(volt_dict['cfc_die'], dict):
			for k,v in volt_dict['cfc_die'].items():
				if volt_dict['cfc_die'][k] != None:
					volt_fuses+=f.cfc_vbump_array(offset = v, target_compute=int(k[-1]))
		else:
			if volt_dict['cfc_die'] != None:
				volt_fuses+=f.cfc_vbump_array(offset = volt_dict['cfc_die']) # Adding CFC fuses
		
		
		if isinstance(volt_dict['hdc_die'], dict):
			for k,v in volt_dict['hdc_die'].items():
				if volt_dict['hdc_die'][k] != None: 
					volt_fuses+=f.hdc_vbump_array(offset = v, target_compute=int(k[-1]))
		else:
			if volt_dict['hdc_die'] != None: 
				volt_fuses+=f.hdc_vbump_array(offset = volt_dict['hdc_die']) # Adding HDC fuses
		

		if volt_dict['ddrd'] != None: volt_fuses+=f.ddrd_vbump_array(offset = volt_dict['ddrd']) # Adding DDRD fuses
		#if volt_dict['ddra'] != None: volt_fuses+=f.ddra_vbump_array(offset = volt_dict['ddra'], computes = computes) # Adding DDRA fuses -- WIP
		if volt_dict['cfc_io'] != None: volt_fuses+=f.cfc_io_vbump_array(offset = volt_dict['cfc_io']) # Adding CFCxIO fuses
   		
	#ppvc_fuses+=f.cfn_vbump_array(fixed_voltage = volt_values['cfn']) # Adding CFN fuses
	#ppvc_fuses+=f.vccinf_vbump_array(fixed_voltage = volt_values['core'], computes = computes) # Adding VCCINF fuses


	fuses_compute0 = [f for f in volt_fuses if 'compute0' in f]
	fuses_compute1 = [f for f in volt_fuses if 'compute1' in f]
	fuses_compute2 = [f for f in volt_fuses if 'compute2' in f]
	fuses_io0 = [f for f in volt_fuses if 'io0' in f]
	fuses_io1 = [f for f in volt_fuses if 'io1' in f]

	if bsformat:
		print(f'\n {"*"*5} Modifying fuses to be usable in a bootscript array for each die {"*"*5}\n')
		if fuses_compute0: fuses_compute0 = bs_fuse_fix(fuse_str = fuses_compute0, bases = ['sv.socket0.compute0.fuses.'])
		if fuses_compute1: fuses_compute1 = bs_fuse_fix(fuse_str = fuses_compute1, bases = ['sv.socket0.compute1.fuses.'])
		if fuses_compute2: fuses_compute2 = bs_fuse_fix(fuse_str = fuses_compute2, bases = ['sv.socket0.compute2.fuses.'])
		if fuses_io0: fuses_io0 = bs_fuse_fix(fuse_str = fuses_io0, bases = ['sv.socket0.io0.fuses.'])
		if fuses_io1: fuses_io1 = bs_fuse_fix(fuse_str = fuses_io1, bases = ['sv.socket0.io1.fuses.'])
	
	volt_confg = {	'compute0':fuses_compute0,
			   		'compute1':fuses_compute1,
					'compute2':fuses_compute2,
					'io0':fuses_io0,
					'io1':fuses_io1,}
	print(f'Voltage configuration fuses collected, adding them to boot configuration')
	print("***********************************v********************************************\n")
	return volt_confg

## Type of avaiable masks for the pseudo Mask and pseudo bs
## Class uses the Column configuration that replicates Class scenario
## User considers specific cases in which we can select columns or rows, this was meant to be used with pseudo_bs script, if used with pseudo mask
## you get all the possible configurations of masks for each single Row / Column.
def pseudo_type(Type, product):
	Configs = pseudoConfigs
	DebugMask = DebugMasks

	if Type != 'External':
		ClassMask = Configs[Type][product]['ClassMask']
		ClassMask_sys = Configs[Type]['ClassMask_sys']
		Masks_test = Configs[Type]['Masks_test']
	else:
		ClassMask = DebugMask[Type][product]['ClassMask']
		ClassMask_sys = DebugMask[Type]['ClassMask_sys']
		Masks_test = DebugMask[Type]['Masks_test']

	
	return ClassMask, ClassMask_sys, Masks_test

## FIVR and PLL WP reader
def reader(dies=['compute0'], ratype = ['fivrs'], ras = ['all'], sktnum = [0]):
	
	#sv = _get_global_sv()
	## Build for GNR UCC AP X3 for the moment
	path = 'C:\\Temp\\'
	gcm.svStatus()
	if 'all' in ras:
		ra_io_fivr = []
		ra_io_pll = []
		if 'fivrs' in ratype or 'all' in ratype:
			RA_array_fivr = ra_type('io','fivrs')
			for key in RA_array_fivr.keys():
				ra_io_fivr.append(RA_array_fivr[key])
		
		if 'plls' in ratype or 'all' in ratype:
			RA_array_pll = ra_type('io','plls')
			for key in RA_array_pll.keys():
				ra_io_pll.append(RA_array_pll[key])

		ra_compute_fivr = []
		ra_compute_pll = []
		if 'fivrs' in ratype or 'all' in ratype:
			RA_array_fivr = ra_type('compute','fivrs')
			for key in RA_array_fivr.keys():
				ra_compute_fivr.append(RA_array_fivr[key])

		if 'plls' in ratype or 'all' in ratype:
			RA_array_pll = ra_type('compute','plls')
			for key in RA_array_pll.keys():
				ra_compute_pll.append(RA_array_pll[key])

	
	for _ratype in ratype:
		#print(_ratype)
		if _ratype == 'fivrs':
			checkreg = 'target_vrci'
			ra_io = ra_io_fivr
			ra_compute = ra_compute_fivr
		else:
			checkreg = 'target_clki'
			ra_io = ra_io_pll
			ra_compute = ra_compute_pll
		#print(ra_compute)
		#print(checkreg)
		for tstdie in dies:
			test_data = {}
			#print (tstdie)
			label = '\n - Resource Adapter (RA) {} values for {} -\n'.format(_ratype, tstdie)
			if tstdie == 'io0' or tstdie == 'io1':
				#test_data = raRead(compute0, 'fivrs')
				io = PySV(tiles=sktnum, PathTemplates = ['uncore.ra'],instances=ra_io, preTilePath='socket',die=tstdie, checktype = checkreg)
				test_data = executeRARead(io, _ratype)
				printRAs(test_data, label)
			else:
				#test_data = raRead(compute0, 'fivrs')
				compute = PySV(tiles=sktnum, PathTemplates = ['uncore.ra'],instances=ra_compute, preTilePath='socket',die=tstdie, checktype = checkreg)
				test_data = executeRARead(compute, _ratype)
				printRAs(test_data, label)

## FIVR Workpoints (WP) Test
def fivrs(dies=['compute0'],ras = ['all'], sktnum = [0], band = {'up':0.01,'down':0.01}, log = False):
	
	#sv = _get_global_sv()
	gcm.svStatus()
	## Build for GNR UCC AP X3 for the moment
	path = 'C:\\Temp\\'
	checkreg = 'target_vrci'
	xlsfile = '{}fivrWPtest_{}.xlsx'.format(path, time.strftime("%Y-%m-%d_%H-%M-%S"))

	if 'all' in ras:
		ra_io = []
		RA_array = ra_type('io','fivrs')
		for key in RA_array.keys():
			ra_io.append(RA_array[key])


		ra_compute = []
		RA_array = ra_type('compute','fivrs')
		for key in RA_array.keys():
			ra_compute.append(RA_array[key])
	else:
		ra_io = ras
		ra_compute = ras
		
	for tstdie in dies:
		test_data = {}
		label = '\n - Resource Adapter (RA) {} values for {} -\n'.format('fivrs', tstdie)
		if tstdie == 'io0' or tstdie == 'io1':
			#test_data = raRead(compute0, 'fivrs')
			io = PySV(tiles=sktnum, PathTemplates = ['uncore.ra'],instances=ra_io, preTilePath='socket',die=tstdie, checktype = checkreg)
			test_data = executeFIVRtest(io, band['up'], band['down'])
			printRAs(test_data, label)
			
		else :
			#test_data = raRead(compute0, 'fivrs')
			compute = PySV(tiles=sktnum, PathTemplates = ['uncore.ra'],instances=ra_compute, preTilePath='socket',die=tstdie, checktype = checkreg)
			test_data = executeFIVRtest(compute, band['up'], band['down'])
			printRAs(test_data, label)
		
		if log: xlswrite(xlsfile, test_data, tstdie)
			#print (init_data)

## PLL Workpoints (WP) Test
def plls(dies=['compute0'],ras = ['all'], sktnum = [0], band = {'up':1,'down':1}, log = False):
	
	#sv = _get_global_sv()
	gcm.svStatus()
	## Build for GNR UCC AP X3 for the moment
	path = 'C:\\Temp\\'
	checkreg = 'target_clki'
	xlsfile = '{}pllsWPtest_{}.xlsx'.format(path, time.strftime("%Y-%m-%d_%H-%M-%S"))

	if 'all' in ras:
		ra_io = []
		RA_array = ra_type('io','plls')
		for key in RA_array.keys():
			ra_io.append(RA_array[key])


		ra_compute = []
		RA_array = ra_type('compute','plls')
		for key in RA_array.keys():
			ra_compute.append(RA_array[key])
	else:
		ra_io = ras
		ra_compute = ras
		
	for tstdie in dies:
		test_data = {}
		label = '\n - Resource Adapter (RA) {} values for {} -\n'.format('plls', tstdie)
		if tstdie == 'io0' or tstdie == 'io1':
			#test_data = raRead(compute0, 'fivrs')
			io = PySV(tiles=sktnum, PathTemplates = ['uncore.ra'],instances=ra_io, preTilePath='socket',die=tstdie, checktype = checkreg)
			test_data = executePLLtest(io, band['up'], band['down'])
			printRAs(test_data, label)
			
		else :
			#test_data = raRead(compute0, 'fivrs')
			compute = PySV(tiles=sktnum, PathTemplates = ['uncore.ra'],instances=ra_compute, preTilePath='socket',die=tstdie, checktype = checkreg)
			test_data = executePLLtest(compute, band['up'], band['down'])
			printRAs(test_data, label)
		
		if log: xlswrite(xlsfile, test_data, tstdie)
			#print (init_data)

# RCs Check WIP do not use
def rcs(dies=['compute0'], rcs = ['rc2, rc5'], sktnum = [0], band = {'pll_up':0.01,'pll_down':0.01,'fvir_up':0.01,'fivr_down':0.01}, log = False ):
		
	sv = _get_global_sv()
	## Build for GNR UCC AP X3 for the moment
	path = 'C:\\Temp\\'
	#checkreg = 'target_vrci'
	xlsfile = '{}RC_test_{}.xlsx'.format(path, time.strftime("%Y-%m-%d_%H-%M-%S"))
	# WIP

## Create a dump file with a a list of MSRs
def msr_read(rlists = [0xCE, 0x199, 0x1AD, 0x1AE, 0x1A0]):

	ipc = _get_global_ipc()
	ipc.halt()
	reglist = []
	regdict = {}
	maxthreads = len(ipc.threads)
	
	init =0 
	initcol = []
	for reg in rlists:
		regs = []
		rlist = ipc.msr(reg)
		for item in rlist:
			#print(item)
			#if init ==0:
			#	initcol.append(item[0])
			#	reglist.append(initcol)
			
			regs.append(str(item))
		regdict[reg] = regs
		init += 1
		#print(initcol)
		
	
	RAkeys = list(regdict.keys())
	RAvalues = list(regdict.values())
	#print(RAkeys)
	#print(RAvalues)
	#reglist = [[i] + [v for v in regdict[k][i]] for i, k in enumerate(regdict)]
	
	for i in range(maxthreads):
		v = []
		for k in regdict.keys():
			v.append(regdict[k][i])
		reglist.append(v)
	#reglist = [[[v] for v in regdict[k][i]] for i ]
	#print(reglist)	

	df = pd.DataFrame(reglist, columns=rlists)
	xlspath = 'C:\\Temp\\MSRsdump.xlsx'
	with pd.ExcelWriter(xlspath, engine='openpyxl', mode='w') as writer:
		# Write the DataFrame to Excel
		df.to_excel(writer,sheet_name='MSRs', index=False)

## Build arrays for FastBoot 
def fuses_dis_2CPM(dis_cores, bsformat = True):
	'''
	dis_cores: 'HIGH' or 'LOW' to disable globally on all modules. usefull to run pseudo MESH
	'''
	valid_configs = [0x3,0xc,0x9,0xa,0x5,0x6]
	if dis_cores == 'HIGH':
		dis=0xc
	elif dis_cores == 'LOW':
		dis=0x3
	elif dis_cores in valid_configs:
		dis = dis_cores
	else:
		print(f"-ERROR- cores has to be define as LOW, HIGH or any value in: {valid_configs}")
		return None
	if bsformat:
		fuse = [f"pcu.pcode_lp_disable={dis:#x}"]
	else:
		fuse = [f"sv.socket0.computes.fuses.pcu.pcode_lp_disable={dis}"]
	return fuse

def fuses_freq_cfc(types = ['io', 'cfc'], domains = ['p0', 'p1', 'pn', 'min'], value = 0x8):
	BootFuses = FuseFileConfigs
	dpmarray = []
	CFC_freq_fuses = BootFuses['CFC']['compFreq']
	CFCIO_freq_fuses = BootFuses['CFC']['ioFreq']

	for _type in types:
		if _type.lower() == 'cfc':
			data = CFC_freq_fuses
		elif _type.lower() == 'io':
			data = CFCIO_freq_fuses
		else:
			print('Not valid type selected use: io, cfc')
			continue
		for domain in domains:
			for fuse in data[domain]:
				dpmarray += [fuse + '=0x%x' % value]
	return dpmarray

def fuses_freq_ia(types = ['ia'], domains = ['p0', 'p1', 'pn', 'min','limits'], value = 0x8):
	BootFuses = FuseFileConfigs
	dpmarray = []
	IA_freq_fuses = BootFuses['IA']['compFreq']

	for _type in types:
		if _type.lower() == 'ia':
			data = IA_freq_fuses
		else:
			print('Not valid type selected use: ia')
			continue
		for domain in domains:
			for fuse in data[domain]:
				dpmarray += [fuse + '=0x%x' % value]
	return dpmarray

def fuses_htdis():
	BootFuses = FuseFileConfigs
	htdis_comp = BootFuses['ht']['compHT']['htdis']
	htdis_io = BootFuses['ht']['ioHT']['htdis']
	dpmarray = []
	dpmarray += htdis_comp 
	dpmarray += htdis_io
	
	return dpmarray

# Move VCCIN and VCCING to use FuseOverride Script
def fuses_vccin(types = ['io', 'compute'], domains = ['active', 'idle', 'safe'], value = 1.89, bsformat = False, skip_init=False):
	if not skip_init: fuseRAM(refresh = True)
	BootFuses = FuseFileConfigs
	dpmarray = []
	newvalue = int(value*1000/5)
	print(f'Converting entered value to hex: {value}V ---> 0x{newvalue:#x}')
	vccin_cdie_fuses = BootFuses['vccin']['compute']
	vccin_iodie_fuses = BootFuses['vccin']['io']

	for _type in types:
		if _type.lower() == 'compute':
			data = vccin_cdie_fuses
			base = 'sv.sockets.computes.fuses.'
		elif _type.lower() == 'io':
			data = vccin_iodie_fuses
			base = 'sv.sockets.ios.fuses.'
		else:
			print('Not valid type selected use: io, compute')
			continue
		for domain in domains:
			fuse = data[domain]
			#base = data['base']
			print(fuse)
			cv = eval(fuse + '.get_value()')
			for v in range(len(cv)):
				cvfloat = cv[v]*5/1000
				if 'computes' in fuse:
					_fuse = fuse.replace('computes',f'compute{v}')
					_base = base.replace('computes',f'compute{v}')
				elif 'ios' in fuse:
					_fuse = fuse.replace('ios',f'io{v}')
					_base = base.replace('ios',f'io{v}')
				print (f"{_fuse} : {cvfloat}:0x%x > {value}: 0x%x" % (cv[v], newvalue))
				if bsformat: _fuse = _fuse.replace(_base,'')
				dpmarray += [_fuse + '=0x%x' % newvalue]
	return dpmarray

def fuses_vccinf(types = ['io', 'compute'], domains = ['active', 'idle', 'safe'], value = 0.85, bsformat = False, skip_init=False):
	if not skip_init: fuseRAM(refresh = True)
	BootFuses = FuseFileConfigs
	dpmarray = []
	newvalue = int(value*1000/5)
	print(f'Converting entered value to hex: {value}V ---> 0x{newvalue:#x}')
	vccin_cdie_fuses = BootFuses['vccinf']['compute']
	vccin_iodie_fuses = BootFuses['vccinf']['io']

	for _type in types:
		if _type.lower() == 'compute':
			data = vccin_cdie_fuses
			base = 'sv.sockets.computes.fuses.'
		elif _type.lower() == 'io':
			data = vccin_iodie_fuses
			base = 'sv.sockets.ios.fuses.'
		else:
			print('Not valid type selected use: io, compute')
			continue
		for domain in domains:
			fuse = data[domain]
			#base = data['base']
			print(fuse)
			cv = eval(fuse + '.get_value()')
			for v in range(len(cv)):
				cvfloat = cv[v]*5/1000
				if 'computes' in fuse:
					_fuse = fuse.replace('computes',f'compute{v}')
					_base = base.replace('computes',f'compute{v}')
				elif 'ios' in fuse:
					_fuse = fuse.replace('ios.',f'io{v}.')
					_base = base.replace('ios.',f'io{v}.')
				print (f"{_fuse} : {cvfloat}:0x%x > {value}: 0x%x" % (cv[v], newvalue))
				if bsformat: _fuse = _fuse.replace(_base,'')
				dpmarray += [_fuse + '=0x%x' % newvalue]
	return dpmarray

## Below arrays uses the GNRFuseOverride script @ thr folder, adding them here for ease of use -- 
def fuses_cfc_vbumps(offset = 0, rgb_array={}, point = None, skip_init=False, fixed_voltage = None, target_compute = None):
	#sv = _get_global_sv
	#sv.refresh()
	if not skip_init: fuseRAM(refresh = True)
	#computes = len(sv.socket0.computes)
	dpmarray = []
	dpmarray = f.cfc_vbump_array(offset = offset, rgb_array= rgb_array, target_point = point, fixed_voltage = fixed_voltage, target_compute = target_compute)
	## Temporary fix
	#if target_compute != None:
	#	computearray = []
	#	print(f'Splitting the array for one compute only: Target {target_compute}')
	#	for item in dpmarray:
	#		if target_compute in item:
	#			computearray.append(item)
	#	dpmarray = computearray
		
	return dpmarray

def fuses_cfc_io_vbump_array(offset = 0, rgb_array={}, skip_init=False, point=None, fixed_voltage=None, target_io= None):
		#sv = _get_global_sv
	#sv.refresh()
	if not skip_init: fuseRAM(refresh = True)
	#computes = len(sv.socket0.computes)
	dpmarray = []
	dpmarray = f.cfc_io_vbump_array(offset = offset, rgb_array= rgb_array, target_point=point, fixed_voltage=fixed_voltage, target_io=target_io)

	return dpmarray

def fuses_hdc_vbumps(offset = 0, rgb_array={}, point = None, skip_init=False, fixed_voltage = None, target_compute = None):
	#sv = _get_global_sv
	#sv.refresh()
	if not skip_init: fuseRAM(refresh = True)
	#computes = len(sv.socket0.computes)
	dpmarray = []
	dpmarray = f.hdc_vbump_array(offset = offset, rgb_array= rgb_array, target_point = point, fixed_voltage = fixed_voltage, target_compute = target_compute)

	#if target_compute != None:
	#	computearray = []
	#	print(f'Splitting the array for one compute only: Target {target_compute}')
	#	for item in dpmarray:
	#		if target_compute in item:
	#			computearray.append(item)
	#	dpmarray = computearray

	return dpmarray

def fuses_ddrd_vbumps(offset = 0, rgb_array={}, point = None, skip_init=False, fixed_voltage = None, target_compute = None):
	#sv = _get_global_sv
	#sv.refresh()
	if not skip_init: fuseRAM(refresh = True)
	#computes = len(sv.socket0.computes)
	dpmarray = []
	dpmarray = f.ddrd_vbump_array(offset = offset, rgb_array= rgb_array, target_point = point, fixed_voltage = fixed_voltage, target_compute = target_compute)
	return dpmarray

def fuses_ddra_vbumps(offset = 0, rgb_array={}, point = None, skip_init=False, fixed_voltage = None, target_compute = None):
	#sv = _get_global_sv
	#sv.refresh()
	if not skip_init: fuseRAM(refresh = True)
	#computes = len(sv.socket0.computes)
	dpmarray = []
	dpmarray = f.ddra_vbump_array(offset = offset, rgb_array= rgb_array, target_point = point, fixed_voltage = fixed_voltage, target_compute = target_compute)
	return dpmarray

def fuses_ia_vbumps(offset = 0, rgb_array={}, skip_init=False, curve=None, point=None, index=None, fixed_voltage=None, target_compute=None):
	
	if not skip_init: fuseRAM(refresh = True)
	dpmarray = []
	dpmarray = f.ia_vbump_array(offset = offset, rgb_array=rgb_array, target_curve=curve, target_point=point, target_index=index, fixed_voltage=fixed_voltage, target_compute=target_compute)
	return dpmarray

def read_fuse_array(fuse_array, skip_init=False):
	#dpm_array = fuse_array
	print('Reading fuse values from entered array... ')
	f.read_array(fuse_array=fuse_array, skip_init=skip_init, load_fuses=False)

## Uses USB Splitter controller to power cycle / on / off the unit -- 
def powercycle(stime = 10, ports = [1,2]):
	import toolext.bootscript.toolbox.power_control.USBPowerSplitterFullControl as pwsc

	print('Power cycling the unit using USB...')
	usb = pwsc.USBPowerSplitter()
	usb.all_powerCycle(_stime = stime, _ports = ports)

def power_on(ports = [1]):
	import toolext.bootscript.toolbox.power_control.USBPowerSplitterFullControl as pwsc

	print('Turning Unit On...')
	usb = pwsc.USBPowerSplitter()
	usb.all_on(_ports = ports)

def power_off(ports = [1]):
	import toolext.bootscript.toolbox.power_control.USBPowerSplitterFullControl as pwsc

	print('Turning Unit Off...')
	usb = pwsc.USBPowerSplitter()
	usb.all_off(_ports = ports)

def power_status():
	ipc = _get_global_ipc()
	on_status = ipc.cv.targpower
	return on_status

def warm_reset():
	ipc = _get_global_ipc()
	print(' Performing Unit warm reset.. Please wait')
	ipc.resettarget()

## MachineBreaks -- To Avoid Unit restart after a FAIL -- 
def ipc_powerdowns():

	ipc = _get_global_ipc()
	print('Configuring MachineCheckBreak=1 and ShutDownBreak=1 to avoid unit reset after a fail')
	ipc.halt()
	ipc.cv.machinecheckbreak=1
	ipc.cv.shutdownbreak=1
	ipc.go()

########################################################################################################################################################################
##
## 													Below all the scripts used by the burn in Test System
##
########################################################################################################################################################################

def burnin(domains=['mesh'], level='mid', boot = True):

	#sv = _get_global_sv()
	gcm.svStatus()
	product = config.PRODUCT_CONFIG
	variant = config.PRODUCT_VARIANT

	_fuse_str_compute = []
	_fuse_str_io = []
	validlevel = ['high', 'mid', 'low']
	validomains = ['mesh', 'core', 'io']
	
	#if level.lower() not in validlevel:
	#	print('Invalid Selection use levels: low, mid or high')
	#	sys.exit()

	#if domains not in validomains:
	#	print('Invalid Selection use levels: low, mid or high')
	#	sys.exit()

	for domain in domains:
		
		if domain != 'io':
			_fuse_str_append = burnin_fuses(domain=domain, level=level)
			_fuse_str_compute += _fuse_str_append
			
		else: 
			_fuse_str_append = burnin_fuses(domain=domain, level=level)
			_fuse_str_io += _fuse_str_append
			_fuse_str_io = bs_fuse_fix(fuse_str = _fuse_str_io, bases = ['sv.sockets.ios.fuses.punit_iosf_sb.','sv.socket0.io0.fuses.punit_iosf_sb.','sv.socket0.io1.fuses.punit_iosf_sb.'])

	if boot: 
		print (f' ---  Boot option is selected - Starting Bootscript') 
		if variant == 'AP': b.go(pwrgoodmethod='usb', pwrgoodport=1, pwrgooddelay=30, fused_unit=True, enable_strap_checks=False,compute_config=COMPUTE_CONFIG,enable_pm=True,segment=SEGMENT, fuse_str_compute = _fuse_str_compute,fuse_str_io = _fuse_str_io)
		if variant == 'SP': b.go(pwrgoodmethod='usb', pwrgoodport=1, pwrgooddelay=30, fused_unit=True, enable_strap_checks=False,compute_config=COMPUTE_CONFIG,enable_pm=True,segment=SEGMENT, fuse_str_compute = _fuse_str_compute,fuse_str_io = _fuse_str_io)
	else: 
		print (f'\n ---  Boot option not selected -- Copy bootscript code  above and edit if needed to run manually')
		print(f'Compute Fuses: \n {_fuse_str_compute}')
		print(f'IO Fuses: \n {_fuse_str_io}')

def burnin_fuses(domain='mesh', level='low', bsformat = True):

	BurnInData = BurnInFuses
	_fuse_str_compute = []
	_fuse_str_io = []
	_fuse_str = []
	if level.lower() not in ['high', 'mid', 'low']:
		print('Invalid Selection use levels: low, mid or high')
		sys.exit()
	else:
		BIdata = BurnInData[level]
	
	if domain == 'core':
		VCCCORE = BIdata['VCCCORE']
		VCCDDRA = BIdata['VCCDDRA']
		VCCDDRD = BIdata['VCCDDRD']

		## Rest of mesh devices moved 500mV from CORE value not lower than 
		VCCCFC = max(VCCCORE - 0.5, 0.8)
		VCCHDC = max(VCCCORE - 0.5, 0.8)
		VCCIN = BIdata['VCCIN']
		VCCINF = BIdata['VCCINF']		
		_type = ['compute']

	if domain == 'mesh':
		VCCCFC = BIdata['VCCCFC']
		VCCHDC = BIdata['VCCHDC']
		VCCCORE = max(VCCCFC - 0.5, 0.8)
		VCCDDRA = max(VCCCFC - 0.5, 0.8)
		VCCDDRD = max(VCCCFC - 0.5, 0.8)
		VCCIN = BIdata['VCCIN']
		VCCINF = BIdata['VCCINF']		
		_type = ['compute']

	if domain == 'io': ## WIP
		VCCCFCIO = BIdata['VCCCFCIO']
		VCCCFNFLEX = BIdata['VCCCFNFLEX']
		VCCCFNHCA = BIdata['VCCCFNHCA']
		VCCCFNPCIE = BIdata['VCCCFNPCIE']
		VCCIOFLEX = BIdata['VCCIOFLEX']
		VCCIOPCIE = BIdata['VCCIOPCIE']
		VCCIN = BIdata['VCCIN']
		VCCINF = BIdata['VCCINF']		
		_type = ['io']

	core_str = fuses_ia_vbumps(fixed_voltage=VCCCORE, target_compute=0)
	ddra_str = fuses_ddrd_vbumps(fixed_voltage=VCCDDRA, computes=1)
	ddrd_str = fuses_ddra_vbumps(fixed_voltage=VCCDDRD, computes=1)
	cfc_str = fuses_cfc_vbumps(fixed_voltage=VCCCFC, computes=1)
	hdc_str = fuses_hdc_vbumps(fixed_voltage=VCCHDC, computes=1)

	_fuse_str = core_str + ddra_str + ddrd_str + cfc_str + hdc_str
	
	## Replace full register name base to be used in bootscript fuse_str
	if bsformat: _fuse_str = bs_fuse_fix(fuse_str = _fuse_str, bases = ['sv.socket0.compute0.fuses.'])

	## VCCIN and VCCINF fuse configuration	
	vccin_str = fuses_vccin(types = _type , domains = ['active', 'idle', 'safe'], value = VCCIN, bsformat = bsformat)
	vccinf_str = fuses_vccinf(types = _type , domains = ['active', 'idle', 'safe'], value = VCCINF, bsformat = bsformat)

	# Complete BurnIn fuse array with all the Voltages changed
	_fuse_str  = _fuse_str + vccin_str + vccinf_str

	return _fuse_str

def bs_fuse_fix(fuse_str = [], bases = ['sv.sockets.computes.fuses.']):
	new_fuse_str = []
	for fuse in fuse_str:
		#newfuse = ""
		for base in bases:
			if base in fuse:
				newfuse = fuse.replace(base,'')
				## Remove any extra space 
				newfuse = newfuse.replace(' ','')
				print(f'Changing fuse from {fuse} --> {newfuse}')
			else:
				continue
			new_fuse_str.append(newfuse)

	return new_fuse_str


########################################################################################################################################################################
##
## 													Below all the scripts used by the S2T pseudo Masking for MESH
##
########################################################################################################################################################################

## Script to check Masks configured, will check if mask si compliant with cluster if option is selected

def masks_validation(masks, ClassMask, dies, product, _clusterCheck, _lsb = False):

	## Assign Cluster values *can be taken from a pythonsv register, update later on
	variant = config.PRODUCT_VARIANT
	if variant == 'AP': cluster = 6
	elif variant == 'SP': cluster = 4
	else: cluster = 2
	
	cores = {'compute0':60,'compute1':60,'compute2':60}
	llcs = {'compute0':60,'compute1':60,'compute2':60}
	core_count = 0
	llc_count = 0

	for compute in dies:
		dieN = compute[-1]
		cores[compute] = 60 - binary_count(masks[ClassMask][f'core_comp_{dieN}'])
		llcs[compute] = 60 - binary_count(masks[ClassMask][f'llc_comp_{dieN}'])

	#min_llc = llcs['compute0'] ## Defaulting to COMP0 if all are the same we dont change it
	min_llc = min(llcs['compute0'],llcs['compute1'],llcs['compute2'])
	if min_llc % 2 != 0:
		## Limiting to a minimum of 2 LLCs
		min_llc = max(min_llc - 1,2)


	print(f'\nRecommended LLC to be used for each Compute die = {min_llc}, to be in line with a clustering of {cluster}')
	for compute in dies:
		print(f'\tEnabled CORES/LLCs for {compute.upper()}: LLCs = {llcs[compute]} , COREs = {cores[compute]}')

	if _clusterCheck:
		print('\nChecking new mask configuration is compliant with system clustering:')
		for compute in dies:
			dieN = compute[-1]
			core_cd = masks[ClassMask][f'core_comp_{dieN}']
			llc_cd = masks[ClassMask][f'llc_comp_{dieN}']
			count_llc = llcs[compute]
			count_core = cores[compute]
			extras = count_llc - min_llc 
			#print(f'{compute} extra {extras} llc')
			if extras > 0:
				print(f' !!!  Current LLC count for compute{dieN}: LLCs = {count_llc}, not compliant with clustering required value {min_llc}, applying fix..\n')
				count_core, count_llc, llc_cd, core_cd = clusterCheck(coremask=core_cd,llcmask=llc_cd, computes = compute, llc_extra = extras, lsb = _lsb)
				masks[ClassMask][f'core_comp_{dieN}'] = core_cd
				masks[ClassMask][f'llc_comp_{dieN}'] = llc_cd
				llcs[compute] = count_llc
				cores[compute] = count_core
				print(f' !!!  Clustering fix completed for {compute.upper()}!!!\n')
	
	for c in dies:
		core_count += cores[c]#cores['compute0'] + cores['compute1'] + cores['compute2']
		llc_count += llcs[c]#llcs['compute0'] + llcs['compute1'] + llcs['compute2']
	
	return masks, core_count, llc_count

## Checks if mask is compliant with clustering configuration for the specified product
## GNR AP - 6, GNRSP - 4
## If mask is not divisible by cluster number then it will start disabling slices at the end or start the die depending on lsb selection
def clusterCheck(coremask, llcmask, computes, llc_extra = 0, lsb = True):
	cores = 0
	llcs = 0
	computeN = computes[-1]

	#print(computes)
	print(' !!!  LLC MASK incoming: ',bin(int(llcmask,16))[2:].zfill(60))

	while llc_extra > 0:
		if llc_extra == 0:
			break
		disMask, first_zero = bit_disable(llcmask, lsb = lsb)
		#print(f'Disabling newllcmask0: {bin(disMask)}')
		newllc = int(llcmask,16) | disMask
		newcore = int(coremask,16) | disMask
		llcmask = hex(newllc)
		coremask = hex(newcore)
		
		#print(f'Disabling newllcmask1: {bin(newllc)}')
		print(f' !!!  Disabling slice: {first_zero + 60*(int(computeN))}')
		llc_extra = llc_extra - 1

	# Check llc count
	cores= 60 - binary_count(coremask)
	llcs= 60 - binary_count(llcmask)
	print(' !!!  LLC MASK outgoing: ',bin(newllc)[2:].zfill(60))

	print(f' !!!  Clustering fix new Core count = {cores}')
	print(f' !!!  Clustering fix new LLC count = {llcs}')

	return cores, llcs, llcmask, coremask

## Old ClusterCheck version, to be removed...
def clustering(mask, computes, llc_extra = 0, lsb = True):
	cores = {'compute0':0,'compute1':0,'compute2':0}
	llcs = {'compute0':0,'compute1':0,'compute2':0}

	#while llc_extra > 0:
	for compute in computes[::-1]:
		computeN = compute[-1]
		print(compute)
		print(bin(int(mask[f'llc_comp_{computeN}'],16)))
		if llc_extra == 0:
			newllc = int(mask[f'llc_comp_{computeN}'],16) 
			newcore = int(mask[f'core_comp_{computeN}'],16) 
			mask[f'llc_comp_{computeN}'] = hex(newllc)
			mask[f'core_comp_{computeN}'] = hex(newcore)				
		
		else:	
			#for key in mask.keys()[-1]:
			disMask, first_zero = bit_disable(mask[f'llc_comp_{computeN}'], lsb = lsb)
			newllc = int(mask[f'llc_comp_{computeN}'],16) | disMask
			newcore = int(mask[f'core_comp_{computeN}'],16) | disMask
			mask[f'llc_comp_{computeN}'] = hex(newllc)
			mask[f'core_comp_{computeN}'] = hex(newcore)
			print(f'Disabling slice: {first_zero + 60*(int(computeN))} to comply with clustering for this unit')
			llc_extra = llc_extra - 1
		# Check llc count
		cores[compute] = 60 - binary_count(mask[f'core_comp_{computeN}'])
		llcs[compute]= 60 - binary_count(mask[f'llc_comp_{computeN}'])
		print(bin(newllc))
		#compute = int(key[-1])

	for compute in computes:
		computeN = compute[-1]
		corecnt = 60 - binary_count(mask[f'core_comp_{computeN}'])
		llcnt = 60 - binary_count(mask[f'llc_comp_{computeN}'])
		print(f'{compute} -- Cores = {corecnt}, LLCS = {llcnt}')
		corecnt = corecnt + cores
		llcnt = llcnt + llcs
		
	print(f'Clustering fix new Core count = {cores}')
	print(f'Clustering fix new LLC count = {llcs}')

	return cores, llcs, mask

## Looks for the first bit depending on the LSB selection, if LSB will disable the lowest slice enabled else will disable the highest
def bit_disable(combineMask, lsb = True, base = 16):
	## We will check for the first enabled slice and enable it
	if type(combineMask) == str:	
		binMask = bin(int(combineMask, base))[2:].zfill(60)
	else:
		binMask = bin(combineMask)[2:].zfill(60)	
	
	if lsb: first_zero = binMask[::-1].find('0')
	else: first_zero = (len(binMask)-1) - (binMask.find('0'))

	disMask = (1 << (first_zero)) #& ((1 << 60)-1) #| combineMask

	return (disMask, first_zero)

########################################################################################################################################################################
##
## 													Add below any auxiliay script - To be used for main script processing
##
########################################################################################################################################################################


## RA Test support code 
def printRAs(data, label = ''):
	#print(data)
	RAkeys = list(data.keys())
	RAvalues = list(data.values())

	# Converting the dictionary values to a list of lists
	table_data = [[k] + [v for v in RAvalues[i].values()] for i, k in enumerate(RAkeys)]

	# Printing the table
	table = tabulate(table_data, headers=["ra_instance.path"] + list(RAvalues[0].keys()), tablefmt="grid")
	if label !='':
		print ('{}'.format(label))
	print(table)

def executeFIVRtest(die, bup = 0.01, bdown = 0.01):
	test_data = {}
	for ra_instance in die._instances:
		# Transitions waitime
		wtime = 0.5
		
		# Read all initial values
		value, ramp, decvalue = raRead(ra_instance,'fivrs')
		
		# Increase Volts
		newValue1 = decvalue + bup
		wrval1 = int(newValue1*1000/2.5)
		newValue1 = wrval1
		
		# Write New values
		raWrite(die, ra_instance, 'fivrs', wrval1)
		
		time.sleep(wtime)
		fbValue1, fbramp1, fbdecvalue1 = raRead(ra_instance,'fivrs')
				
		# Decrease Volts
		newValue2 = decvalue - bdown
		wrval2 = int(newValue2*1000/2.5)
		newValue2 = wrval2
		
		#Write new Values
		raWrite(die, ra_instance, 'fivrs', wrval2)
		time.sleep(wtime)
		fbValue2, fbramp2, fbdecvalue2 = raRead(ra_instance,'fivrs')
		

		# Back to Initial Values

		raWrite(die, ra_instance, 'fivrs', value)
		time.sleep(wtime)
		endvalue, endramp, enddecvalue = raRead(ra_instance,'fivrs')

		# Check fsm

		fsm_state, fsm_busy, v_change_ack = chkfsmsts(ra_instance, 'fivrs')
		if str(fsm_state) != '0x0': 
			results = 'FAIL_fsm'
		elif newValue1 != fbValue1: 
			results = 'FAIL_inc'
		elif newValue2 != fbValue2: 
			results = 'FAIL_dec'
		else:
			results = 'PASS'

		#Increase 
		#value, decvalue, ramp = raRead(ra_instance,'fivrs', newValue)

		test_data[ra_instance.path]= {	'init_value':hex(value), 
										'end_val':hex(endvalue),
										'test_result':results,
										'init_volts':decvalue, 
										'init_ramp':ramp,
										'inc_write_val':hex(newValue1),
										'inc_write_fb':hex(fbValue1),
										'dec_write_val':hex(newValue2),
										'dec_write_fb':hex(fbValue2),
										'fsm_state':fsm_state,
										'fsm_busy':fsm_busy,
										'v_change_ack':v_change_ack,
										}
		#print(test_data[ra_instance.path])

	return (test_data)

def executePLLtest(die, bup = 1, bdown = 1):
	test_data = {}
	for ra_instance in die._instances:
		# Transitions waitime
		wtime = 0.5
		
		# Read all initial values
		value, ramp, decvalue = raRead(ra_instance,'plls')
		
		# Increase Volts
		newValue1 = decvalue + bup
		wrval1 = int(newValue1)
		newValue1 = wrval1
		
		# Write New values
		raWrite(die, ra_instance, 'plls', wrval1)
		
		time.sleep(wtime)
		fbValue1, fbramp1, fbdecvalue1 = raRead(ra_instance,'plls')
				
		# Decrease Volts
		newValue2 = decvalue - bdown
		wrval2 = int(newValue2)
		newValue2 = wrval2
		
		#Write new Values
		raWrite(die, ra_instance, 'plls', wrval2)
		time.sleep(wtime)
		fbValue2, fbramp2, fbdecvalue2 = raRead(ra_instance,'plls')
		

		# Back to Initial Values

		raWrite(die, ra_instance, 'plls', value)
		time.sleep(wtime)
		endvalue, endramp, enddecvalue = raRead(ra_instance,'plls')

		# Check fsm

		fsm_state, fsm_busy, f_change_ack = chkfsmsts(ra_instance, 'plls')
		if str(fsm_state) != '0x0': 
			results = 'FAIL_fsm'
		elif newValue1 != fbValue1: 
			results = 'FAIL_inc'
		elif newValue2 != fbValue2: 
			results = 'FAIL_dec'
		else:
			results = 'PASS'

		#Increase 
		#value, decvalue, ramp = raRead(ra_instance,'fivrs', newValue)

		test_data[ra_instance.path]= {	'init_value':hex(value), 
										'end_val':hex(endvalue),
										'test_result':results,
										'init_freq':decvalue, 
										'pll_mode':ramp,
										'inc_write_val':hex(newValue1),
										'inc_write_fb':hex(fbValue1),
										'dec_write_val':hex(newValue2),
										'dec_write_fb':hex(fbValue2),
										'fsm_state':fsm_state,
										'fsm_busy':fsm_busy,
										'f_change_ack':f_change_ack,
										}
		#print(test_data[ra_instance.path])

	return (test_data)

def executeRARead(die, _ratype):
	test_data = {}
	for ra_instance in die._instances:
		# Read all initial values
		value, ramp, decvalue = raRead(ra_instance, _ratype)
		
		# Check fsm

		fsm_state, fsm_busy, v_change_ack = chkfsmsts(ra_instance, _ratype)

		if _ratype == 'fivrs':
			test_data[ra_instance.path]= {	'init_value':hex(value), 
											'init_volts':decvalue, 
											'init_ramp':ramp,
											'fsm_state':fsm_state,
											'fsm_busy':fsm_busy,
											'v_change_ack':v_change_ack,
											}
		else:
			test_data[ra_instance.path]= {	'init_value':hex(value), 
											'init_ratio':decvalue, 
											'pll_mode':ramp,
											'fsm_state':fsm_state,
											'fsm_busy':fsm_busy,
											'f_change_ack':v_change_ack,
											}
		#print(test_data[ra_instance.path])

	return (test_data)

def chkfsmsts(ra_instance, rdtype):
	
	try:
		if rdtype == 'fivrs':
			fsm_state = ra_instance.wp_sts_vrci.wp_fsm_state.read()
			fsm_busy = ra_instance.wp_sts_vrci.wp_fsm_busy.read()
			change_ack = ra_instance.v_change_ack.read()
			#data[ra_instance.path]= {'volt_hex':value, 'volts':decvalue, 'ramp':ramp}
		else:
			fsm_state = ra_instance.wp_sts_clki.wp_fsm_state.read()
			fsm_busy = ra_instance.wp_sts_clki.wp_fsm_busy.read()
			change_ack = ra_instance.f_change_ack.read()
			#data[ra_instance.path]= {'ratio_hex':value, 'ratio_dec':decvalue, 'mode':mode}
			
			#print (ra_instance)
			#print (data)
	except:
		fsm_state = 'NA'
		fsm_busy = 'NA'
		change_ack = 'NA'
	try: return hex(fsm_state), hex(fsm_busy), hex(change_ack)
	except: return fsm_state, fsm_busy, change_ack

def raRead(ra_instance, rdtype):
		
	try:
		if rdtype == 'fivrs':
			value = ra_instance.current_vrci.voltage
			mode = ra_instance.current_vrci.ramp_type
			decvalue = (int(value)* 2.5) / 1000
				#data[ra_instance.path]= {'volt_hex':value, 'volts':decvalue, 'ramp':ramp}
		else:
			value = ra_instance.current_clki.ratio
			mode = ra_instance.current_clki.pll_mode
			decvalue = int(value) 
				#data[ra_instance.path]= {'ratio_hex':value, 'ratio_dec':decvalue, 'mode':mode}
			
			#print (ra_instance)
			#print (data)
	except:
		value = 'NA'
		mode = 'NA'
		decvalue = 'NA'
		print('Value for instance {} - {} not avaiable skipping'.format(ra_instance.path, rdtype))
	return value, mode, decvalue

def raWrite(die, ra_instance, rdtype, newValue):
	#print (newValue)
	
	# Checks for any master dependancy on the RAs
	rootinstance = leafRAs(die, rdtype, ra_instance)
	#print(rootinstance.path)

	if rdtype == 'fivrs':
		rootinstance.target_vrci.voltage = newValue
		#ramp = ra_instance.target_vrci.ramp_type = newMode
		#decvalue = (int(value)* 2.5) / 1000
		#data[ra_instance.path]= {'volt_hex':value, 'volts':decvalue, 'ramp':ramp}
	else:
		rootinstance.target_clki.ratio = newValue
		#mode = ra_instance.current_vrci.pll_mode.read()
		#decvalue = int(value) 
		#data[ra_instance.path]= {'ratio_hex':value, 'ratio_dec':decvalue, 'mode':mode}
	
	#print (ra_instance)
	#print (data)
	#return data

## RA Test data log to excel 
def xlswrite(xlspath, data, label = 'Test'):

	RAkeys = list(data.keys())
	RAvalues = list(data.values())

	# Converting the dictionary values to a list of lists
	table_data = [[k] + [v for v in RAvalues[i].values()] for i, k in enumerate(RAkeys)]


	print ('Saving xls file in {}'.format(xlspath))

	

	df = pd.DataFrame(table_data, columns=["ra_instance.path"] + list(RAvalues[0].keys()))
	if os.path.isfile(xlspath):
		
		print('Appending data to the file')
		with pd.ExcelWriter(xlspath, engine='openpyxl', mode='a', if_sheet_exists = 'overlay') as writer:
			# Append data to the existing file
			df.to_excel(writer,sheet_name=label, index=False)
	else:
		print('Creating log and adding data to the file')
		with pd.ExcelWriter(xlspath, engine='openpyxl', mode='w') as writer:
			# Write the DataFrame to Excel
			df.to_excel(writer,sheet_name=label, index=False)

## GNR Ra types, in future updates this data will be moved to a json config file
def ra_dict():
	radict = {'compute':[],	'io':[]}
	
	radict['compute'] = ['ra0','ra1','ra2','ra3','ra4',
		   'ra5','ra6','ra7','ra8','ra9',
		   'ra10','ra11','ra12','ra13','ra14',
		   'ra15','ra16','ra17','ra18','ra19',
		   'ra20','ra21','ra22','ra23','ra24',
		   'ra25','ra26','ra27','ra28','ra29',
		   'ra30','ra31','ra32','ra33','ra34',
		   'ra35','ra36','ra37','ra38','ra39',
		   'ra40','ra41','ra42']

	radict['io'] = ['ra0','ra1','ra2','ra3','ra4',
		   'ra5','ra6','ra7','ra8','ra9',
		   'ra10','ra11','ra12','ra13','ra14',
		   'ra15','ra16','ra17','ra18','ra19',
		   'ra20','ra21','ra22','ra23','ra24',
		   'ra25','ra26','ra27','ra28','ra29',
		   'ra30','ra31','ra32','ra33','ra34',
		   'ra35','ra36','ra37','ra38','ra39',
		   'ra40','ra41','ra42','ra43','ra44','ra45']
	
	return radict

## GNR Ra leaf/master dependancy, in future updates this data will be moved to a json config file
def leafRAs(die, ratype, instance):
	
	rootinstance = instance
	
	leafs =	{'fivrs' : {
					'ra28':'ra22',
					'ra30':'ra18',
					'ra37':'ra36'},
				'plls' : {}}

	for leaf in leafs[ratype].keys():
		if leaf in str(instance.path):
			rootinstance = die._socket.get_by_path('{0}.{1}'.format('uncore.ra',leafs[ratype][leaf]))
			print ('Instance {} uses master in location {}'.format(instance.path, rootinstance.path))
	
	return rootinstance

## GNR Ra types, in future updates this data will be moved to a json config file
def ra_type(d_type, ratype):
	
	if d_type == 'compute':
		data = 	{'fivrs' : {
					'ddra1':'ra5',
					'ddrd1':'ra16',
					'hdc0':'ra18',
					'cfc0':'ra22',
					'cfc1':'ra28',
					'hdc3':'ra30',
					'ddrd3':'ra34',
					'ddra3':'ra40'},
				'plls' : {	
					'ddrio1':'ra4',
					'fivr0':'ra9',
					'mesh0':'ra10',
					'ref400':'ra11',
					'x8':'ra12',
					'eprpunit':'ra17',
					'ddrio3':'ra39'	}}

	elif d_type == 'io':
				data = 	{
				'fivrs' : {
					'flexcfn20':'ra2',
					'flexio20':'ra3',
					'hca0':'ra6',
					'flexcfn21':'ra10',
					'flexio21':'ra11',
					'pciecfn50':'ra15',
					'pcieio50':'ra16',
					'pciecfn51':'ra20',
					'pcieio51':'ra21',
					'flexcfn22':'ra25',
					'flexio22':'ra26',
					'mesh0':'ra36',
					'mesh1':'ra37',
					'hca1':'ra39',
					'flexcfn23':'ra43',
					'flexio23':'ra44'},
				'plls' : {	
					'pcie20':'ra4',
					'hca0':'ra7',
					'pcie21':'ra12',
					'pcie50':'ra17',
					'pcie51':'ra22',
					'pcie22':'ra27',
					'infra0':'ra33',
					'mesh0':'ra34',
					'punit0':'ra35',
					'hca1':'ra40',
					'pcie23':'ra45'}
					}

	RAs = data[ratype]

	return RAs

########################################################################################################################################################################
##
## 													IPC and SV Initialization Code
##
########################################################################################################################################################################


## SV initilize		
def _get_global_sv():

	'''
	Lazy initialize for the sapphirerapids sv 'socket' instance

	Return
	------
	sv: class 'components.ComponentManager'
	'''
	global sv
	global ipc

	if sv is None:
		from namednodes import sv
		sv.initialize()
	if not sv.sockets:
		#Msg.print_("No socketlist detected. Restarting baseaccess and sv.refresh")
		ipc = _get_global_ipc()
		ipc.forcereconfig() 
		if ipc.islocked():
			ipc.unlock()
		#ipc.unlock()
		#ipc.uncores.unlock()
		sv.initialize()
		sv.refresh()    #determined this was needed in manual testing
	return sv

## IPC Initialize
def _get_global_ipc():
		'''
		Lazy initialize for the global IPC instance
		'''
		global ipc
		if ipc is None:
			import ipccli
			ipc = ipccli.baseaccess()
			ipc.forcereconfig() 
			ipc.unlock()
			#ipc.uncores.unlock()
		return ipc

########################################################################################################################################################################
##
## 													Miscelaneous code - reusable in multiple implementations
##
########################################################################################################################################################################

## Message prompt code
def prompt_msg(message, timeout = 30):
	print(message)
	for i in range(timeout, 0, -1):
		response = input(f"Please respond with Yes or No within {i} seconds: ")
		if response.lower() in ['yes', 'no']:
			return response.lower()
		time.sleep(1)
	print("Timeout reached. Continuing by default.")
	return None

## Data tabulate - Display data in a organized table format
def printTable(data, label = ''):
	#Convert to lists
	tblkeys = list(data.keys())
	tblvalues = list(data.values())

	# Converting the dictionary values to a list of lists
	table_data = [[k] + [v for v in tblvalues[i].values()] for i, k in enumerate(tblkeys)]

	# Printing the table
	table = tabulate(table_data, headers=["instance"] + list(tblvalues[0].keys()), tablefmt="grid")
	if label !='':
		print ('\n{}'.format(label))
	print(table)

## Data modification to be used in Tabulate format (CFC/IA Ratios code)
def printData(data, curve, die, pointvalue):
	update_data = {die: pointvalue}
	try:
		data[curve].update(update_data)
	except:
		data[curve] = {die: pointvalue}
	
	return data

def binary_count(value, bitcount = '1', lenght = 60):
	## Convert data to be usable by script
	if isinstance(value, int):
		bin_string = bin(value)
	elif isinstance(value, str):
		bin_string = bin(int(value,16))
	else:
		raise ValueError ("Invalid input used for binary string count")
	bin_string = bin_string[2:].zfill(lenght)

	bin_count = bin_string.count(bitcount)
	return bin_count

def dev_dict(filename, useroot = True, selected_product = 'CWF'):
	## Load Configuration json files
	configfilename = filename
	if useroot:
		file_NAME = (__file__).split("\\")[-1].rstrip()
		parent_dir =(__file__).split(file_NAME)[0]
		jsfile = "{}\\product_specific\\{}\\ConfigFiles\\{}".format(parent_dir, selected_product.lower(), configfilename)
	else:
		jsfile = configfilename

	# Change dbgfile to original
	with open (jsfile) as configfile:
		configdata = json.load(configfile)
		devices = configdata

	return devices

# Gets current World Week for reports
def getWW():
	currentdate = datetime.date.today()
	iso_calendar = currentdate.isocalendar()
	WW = iso_calendar[1]

	return WW

########################################################################################################################################################################
##
## 													Configuration Files load, if debug will change the folder
##
########################################################################################################################################################################

pseudoConfigs = dev_dict(f'{config.SELECTED_PRODUCT}MasksConfig.json', selected_product= config.SELECTED_PRODUCT)
DebugMasks = dev_dict(f'{config.SELECTED_PRODUCT}MasksDebug.json', selected_product = config.SELECTED_PRODUCT)
FuseFileConfigs = dev_dict(f'{config.SELECTED_PRODUCT}FuseFileConfigs.json', selected_product = config.SELECTED_PRODUCT)
BurnInFuses = dev_dict(f'{config.SELECTED_PRODUCT}BurnInFuses.json', selected_product = config.SELECTED_PRODUCT)


## Bootscript Data

COMPUTE_CONFIG = config.BOOTSCRIPT_DATA[config.PRODUCT_CONFIG.upper()]['compute_config']
SEGMENT = config.BOOTSCRIPT_DATA[config.PRODUCT_CONFIG.upper()]['segment']