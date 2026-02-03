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

if cfl.DEV_MODE:
	importlib.reload(cfl)

config = cfl.config
config.reload()

# Product Functions
pf = config.get_functions()
ffg = config.get_fusefilegen()

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

else:
	gcm = import_module(f'{BASE_PATH}.S2T.{LEGACY_NAMING}CoreManipulation')
	dpmtileview = import_module(f'{BASE_PATH}.S2T.Logger.ErrorReport')
	dpmlog = import_module(f'{BASE_PATH}.S2T.Logger.logger')
	p2ip = import_module(f'{BASE_PATH}.S2T.Tools.portid2ip')
	reqinfo = import_module(f'{BASE_PATH}.S2T.Tools.requests_unit_info')


## Imports from THR folder - These are external scripts, always use same path
f = None
fo = None
try:
	fo = import_module(f'{BASE_PATH}.{THR_NAMING}FuseOverride')
	f = fo.DMRFuseOverrides()

	print(' [+] FuseOverride imported successfully')
except Exception as e:
	print(f' [x] Could not import FuseOverride, some features may be limited: {e}')

## Reload of all imported scripts
if cfl.DEV_MODE:
	importlib.reload(gcm)
	importlib.reload(dpmlog)
	importlib.reload(dpmtileview)
	if fo is not None:
		importlib.reload(fo)

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
	def __init__(self, tiles=[0], PathTemplates = ['uncore.ra'],instances=['ra22','ra18'], preTilePath='socket',die='cbb0', checktype = 'current_vcri'):

		self._instances = []
		self.readcheck = checktype
		# All tiles
		for tile in tiles:
			self._socket = sv.get_by_path('{0}{1}.{2}'.format(preTilePath,tile,die))
			for template in PathTemplates:
				for i in instances:
					try:
						if i is not None:
							self._instances.append(self._socket.get_by_path('{0}.{1}'.format(template,i)))
						else:
							self._instances.append(self._socket.get_by_path('{}'.format(template)))
					except:
						print(f'PythonSV instance {i} cannot be read, skipping')

		# Perform a check on all the instances, if there is a non readable one, remove it
		if checktype != '':
			self.instancechk()

	def instancechk(self):

		for _instance in self._instances:
			try:
				read_check = _instance.get_by_path('{}'.format(self.readcheck))
				print(f'instance {_instance.path}.{self.readcheck} correctly readable')
				#print(read_check.path)
				read_check.read()
			except:
				print(f'instance {_instance.path}.{self.readcheck} cannot be read, removing it')
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
	def __init__(self, dies = ['all'], regs = 'all', sktnum = [0], fuse_ram = True) -> None:
		self.sv = _get_global_sv()
		self.ipc = ipccli.baseaccess()

		self.regs = regs
		self.sktnum = sktnum
		self.fuse_ram = fuse_ram
		self.cfc_voltages = config.CFC_VOLTAGE_CURVES
		self.cfc_ratios = config.CFC_RATIO_CURVES

		self.imh_cv = ['uncore.punit.punit_regs.punit_gpsb']
		self.cbb_cv = ['base.punit_fuses']


		if 'all' in dies:
			dies = []
			dies.extend(sv.socket0.imhs.name)
			dies.extend(sv.socket0.cbbs.name)
		self.dies = dies

		self._set_variables()

	def _set_instance(self, sktnum, template, instance, die, check) -> PySV:

		return PySV(tiles=sktnum, PathTemplates = template, instances=instance, preTilePath='socket',die=die, checktype = check)

	def _generate_fuse_from_config(self, fuse, p1, p1_name, p2=None, p2_name=None, p3=None, p3_name=None) -> str:

		if p2 is None:
			return fuse.replace(p1_name, str(p1))
		if p3 is None:
			return fuse.replace(p1_name, str(p1)).replace(p2_name, str(p2))

		return fuse.replace(p1_name, str(p1)).replace(p2_name, str(p2)).replace(p3_name, str(p3))

	def _set_variables(self) -> None:
		# CBB Base
		self.base_path = ['base']
		self.base_path_cv = ['pcudata']
		self.base_instance = ['fuses.punit_fuses']
		self.base_instance_cv_cfc = [None]
		self.base_instance_cv_ia = ['punit_regs.punit_gpsb.gpsb_infvnn_io_regs'] ## Not used reading TOP
		self.base_fuse_test_reg = 'fw_fuses_cfc_min_ratio'
		self.base_cv_test_cfc_v = 'wp_cv_ring_fivr_0' # Voltage
		self.base_cv_test_cfc_f = 'wp_cv_ring'#Ratio

		  # CBB Top
		self.top_path = ['computes']
		self.top_instance = ['fuses'] #computes.fuses.core0_fuse
		self.top_instance_cv_ia = ['pmas.pmsb.io_wp1'] # WP_CV_Ring Voltage/Frequency
		self.top_fuse_test_reg = 'core0_fuse.core_fuse_core_fuse_acode_ia_base_vf_ratio_0'

		# IMH
		self.imh_path = ['fuses']
		self.imh_instance = ['punit']
		self.imh_path_cv = ['pcodeio_map']
		self.imh_instance_cv = [None]
		self.imh_fuse_test_v = 'pcode_cfcio_vf_voltage_point0'
		self.imh_fuse_test_f = 'pcode_cfcio_min_ratio'
		self.imh_cv_test_reg = 'io_wp_rc_cv_ps_0' # Voltage / Ratio

	def voltage(self) -> None:

		#Self Class values
		regs = self.regs
		fuse_ram = self.fuse_ram
		dies = self.dies
		sktnum = self.sktnum

		# Data inits
		data_cfc = {}
		data_hdc = {}
		data_cfc_io = {}
		#data_pstates = {}
		data_read = {}
		data_read_io = {}

		# Check for arguments in reg key
		valid_regs = {	'fuses':{'fuses': True, 	'cv':False},
						'cv': 	{'fuses': False, 	'cv':True},
						'all':	{'fuses': True, 	'cv':True}}

		if regs not in valid_regs.keys():
			print ('No valid register selection to be read, valid options are: \n' +
					'fuses:	Reads all fused data configured for CFC Ratios. \n' +
					'cv: 	Reads current mesh value for CFC ratios. \n' +
					'all: 	Reads fuses and current values for CFC ratios. (default) '  )
			sys.exit()

		regfuse = valid_regs[regs]['fuses']
		regcv = valid_regs[regs]['cv']

		# Read all fuses first
		if fuse_ram and regfuse:
			fuseRAM()

		curves = self.cfc_voltages

		for die in dies:

			if re.search(r'imh*', die):
				die_inst = self._set_instance(sktnum, self.imh_path, self.imh_instance, die, self.imh_fuse_test_v)
				mesh_val = self._set_instance(sktnum, self.imh_path_cv, self.imh_instance_cv, die, self.imh_cv_test_reg)

			elif re.search(r'cbb*', die):
				die_inst = self._set_instance(sktnum, self.base_path, self.base_instance, die, self.base_fuse_test_reg)
				mesh_val = self._set_instance(sktnum, self.base_path_cv, self.base_instance_cv_cfc, die, self.base_cv_test_cfc_v)
			else:
				print(f'Not valid die selected {die}: Skipping...')
				continue

			if regfuse:
				for fuse in die_inst._instances:
					# CFC VF fuses (VOLTAGE)
					for point in curves['points']:

						if 'imh' in die:
							for curve in curves['cfcio_curve']:
								for domain in curves['cfcio_domains']:
									_fuse = self._generate_fuse_from_config(curve, point, '#points#', domain, '#domain#')
									pointvalue = fuse.readregister(_fuse)
									printData(data_cfc_io, _fuse, die, hex(pointvalue))
						else:

							for curve in curves['cfc_curve']:
								for cfc in curves['cfcs']:
									_fuse = self._generate_fuse_from_config(curve, cfc, '#cfcs#', point, '#points#')
									pointvalue = fuse.readregister(_fuse)
									printData(data_cfc, _fuse, die, hex(pointvalue))


			if regcv:
				# Mesh current value / Add some extra code for the hdc read, this one can be checked directly from the RA
				for mesh in mesh_val._instances:

					if 'imh' in die:
						meshvalue = mesh.get_by_path(self.imh_cv_test_reg).readfield('voltage')
						print(data_read, f'{self.imh_cv_test_reg}.voltage', die, hex(meshvalue))
						printData(data_read_io, f'{self.imh_cv_test_reg}.voltage', die, hex(meshvalue))
					else:
						for cfc in curves['cfcs']:
							meshvalue = mesh.get_by_path(f'wp_cv_ring_fivr_{cfc}').readfield('voltage')
							print(data_read, f'wp_cv_ring_fivr_{cfc}[0].voltage', die, hex(meshvalue))
							printData(data_read, f'wp_cv_ring_fivr_{cfc}[0].voltage', die, hex(meshvalue))

		if regfuse:
			if data_cfc:
				printTable(data_cfc, "CFC CBB VF fuses (VOLTAGE)")
			#printTable(data_hdc, "HDC VF fuses (VOLTAGE)")
			if data_cfc_io:
				printTable(data_cfc_io, "CFC IO VF fuses (VOLTAGE)")

		if regcv:
			if data_read:
				printTable(data_read, "Voltages CBB Current Values (MESH)")
			if data_read_io:
				printTable(data_read_io, "Voltages IO Current Values (MESH)")

	def ratios(self):

		#Self Class values
		regs = self.regs
		fuse_ram = self.fuse_ram
		dies = self.dies
		sktnum = self.sktnum

		# Data inits
		data_cfc = {}
		data_hdc = {}
		data_cfc_io = {}
		data_pstates_io = {}
		data_pstates = {}
		data_read = {}
		data_read_io = {}

		#Check for arguemnts in reg key
		valid_regs = {	'fuses':{'fuses': True, 	'cv':False},
						'cv': 	{'fuses': False, 	'cv':True},
						'all':	{'fuses': True, 	'cv':True}}

		if regs not in valid_regs.keys():
			print ('No valid register selection to be read, valid options are: \n' +
					'fuses:	Reads all fused data configured for CFC Ratios. \n' +
					'cv: 	Reads current mesh value for CFC ratios. \n' +
					'all: 	Reads fuses and current values for CFC ratios. (default) '  )
			sys.exit()

		regfuse = valid_regs[regs]['fuses']
		regcv = valid_regs[regs]['cv']

		# Read all fuses first
		if fuse_ram and regfuse:
			fuseRAM()

		curves = self.cfc_ratios #config.CFC_RATIO_CURVES

		for die in dies:

			if re.search(r'imh*', die):
				die_inst = self._set_instance(sktnum, self.imh_path, self.imh_instance, die, self.imh_fuse_test_f)
				mesh_val = self._set_instance(sktnum, self.imh_path_cv, self.imh_instance_cv, die, self.imh_cv_test_reg)

			elif re.search(r'cbb*', die):
				die_inst = self._set_instance(sktnum, self.base_path, self.base_instance, die, self.base_fuse_test_reg)
				mesh_val = self._set_instance(sktnum, self.base_path_cv, self.base_instance_cv_cfc, die, self.base_cv_test_cfc_f)

			else:
				print(f'Not valid die selected {die}: Skipping...')
				continue

			if regfuse:
				for fuse in die_inst._instances:
					# CFC VF fuses (RATIO)
					if 'imh' in die:
						for domain in curves['cfcio_domains']:
							for curve in curves['cfcio_curve']:
								_fuse = self._generate_fuse_from_config(curve, domain, '#domain#')
								pointvalue = fuse.readregister(_fuse)
								printData(data_cfc_io, _fuse, die, hex(pointvalue))

						  # CFCIO Pstate fuses (RATIO)
						for pstate in curves['pstates_io'].keys():
							if curves['pstates_io'][pstate] is None:
								continue
							for domain in curves['cfcio_domains']:
								_fuse = self._generate_fuse_from_config(curves['pstates_io'][pstate], domain, '#domain#')
								pstatevalue = fuse.readregister(_fuse)
								printData(data_pstates_io, _fuse, die, hex(pstatevalue))

					else:
						for curve in curves['cfc_curve']:
							pointvalue = fuse.readregister(curve)
							printData(data_cfc, curve, die, hex(pointvalue))


						# CFC Pstate fuses (RATIO)
						for pstate in curves['pstates'].keys():
							if curves['pstates'][pstate] is None:
								continue

							pstatevalue = fuse.readregister(curves['pstates'][pstate])
							printData(data_pstates, pstate, die, hex(pstatevalue))
					#if re.search(r'compute*', die):
					#	# HDC VF fuses (RATIO)
					#
					#	for curve in curves['hdc_curve']:
					#		pointvalue = fuse.readregister(curve)
					#		printData(data_hdc, curve, die, hex(pointvalue))



			if regcv:
				# Mesh current value
				for mesh in mesh_val._instances:

					if 'imh' in die:
						meshvalue = mesh.get_by_path(self.imh_cv_test_reg).readfield('ratio')
						printData(data_read_io, f'{self.imh_cv_test_reg}.ratio', die, hex(meshvalue))
					else:
						meshvalue = mesh.get_by_path(f'{self.base_cv_test_cfc_f}').readfield('ratio')
						printData(data_read, f'{self.base_cv_test_cfc_f}.ratio', die, hex(meshvalue))
		if regfuse:
			if data_cfc:
				printTable(data_cfc, "CFC CBB VF fuses (RATIO)")
			if data_cfc_io:
				printTable(data_cfc_io, "CFC IO VF fuses (RATIO)")
			#printTable(data_hdc, "HDC VF fuses (RATIO)")
			if data_pstates:
				printTable(data_pstates, "Pstates Values (RATIO)")
			if data_pstates_io:
				printTable(data_pstates_io, "Pstates IO Values (RATIO)")
		if regcv:
			if data_read:
				printTable(data_read, "Ratios CBB Current Values (MESH)")
			if data_read_io:
				printTable(data_read_io, "Ratios IO Current Values (MESH)")

	#def curves(self)

## IA Voltage/Ratio values and VF Curve data
class ia():

	def __init__(self, dies = ['all'], regs = 'all', sktnum = [0], fuse_ram = True):
		self.sv = _get_global_sv()
		self.ipc = ipccli.baseaccess()

		self.regs = regs
		self.sktnum = sktnum
		self.fuse_ram = fuse_ram
		self.ia_voltages = config.IA_VOLTAGE_CURVES
		self.ia_ratios = config.IA_RATIO_CURVES
		self.Ia_config = config.IA_RATIO_CONFIG

		if 'all' in dies:

			dies = sv.socket0.cbbs.name
			#if _die == 'gnrap':
			#	dies = ['compute0', 'compute1', 'compute2']
			#elif _die == 'gnrsp':
			#	dies = ['compute0', 'compute1']

		self.dies = dies
		self._set_variables()

	def _set_instance(self, sktnum, template, instance, die, check) -> PySV:

		return PySV(tiles=sktnum, PathTemplates = template, instances=instance, preTilePath='socket',die=die, checktype = check)

	def _generate_fuse_from_config(self, fuse, p1, p1_name, p2=None, p2_name=None, p3=None, p3_name=None) -> str:

		if p2 is None:
			return fuse.replace(p1_name, str(p1))
		if p3 is None:
			return fuse.replace(p1_name, str(p1)).replace(p2_name, str(p2))

		return fuse.replace(p1_name, str(p1)).replace(p2_name, str(p2)).replace(p3_name, str(p3))

	def _set_variables(self) -> None:
		# CBB Base
		self.base_path = ['base']
		self.base_path_cv = ['pcudata']
		self.base_instance = ['fuses.punit_fuses']
		self.base_instance_cv_cfc = [None]
		self.base_instance_cv_ia = ['punit_regs.punit_gpsb.gpsb_infvnn_io_regs'] ## Not used reading TOP
		self.base_fuse_test_reg = 'fw_fuses_cfc_min_ratio'
		self.base_cv_test_cfc_v = 'wp_cv_ring_fivr_0' # Voltage
		self.base_cv_test_cfc_f = 'wp_cv_ring'#Ratio

		  # CBB Top
		self.top_path = ['computes']
		self.top_instance = ['fuses'] #computes.fuses.core0_fuse
		self.top_instance_cv_ia = ['pmas'] #computes.fuses.core0_fuse
		self.top_cv_test_ia = 'pmsb.io_wp1' # WP_CV_Ring Voltage/Frequency
		self.top_cv_ia = 'pmsb.io_wp1' # WP_CV_Ring Voltage/Frequency
		self.top_fuse_test_reg = 'core0_fuse.core_fuse_core_fuse_acode_ia_base_vf_ratio_0'
		self.top_path_cv = ['computes']
		# IMH
		self.imh_path = ['fuses']
		self.imh_instance = ['punit']
		self.imh_path_cv = ['pcodeio_map']
		self.imh_instance_cv = [None]
		self.imh_fuse_test_v = 'pcode_cfcio_vf_voltage_point0'
		self.imh_fuse_test_f = 'pcode_cfcio_min_ratio'
		self.imh_cv_test_reg = 'io_wp_rc_cv_ps_0' # Voltage / Ratio

	def _check_data_type(self, value) -> str:
		# Check if value is hex or int
		if isinstance(value, int):
			return hex(value)
		# Check if value is hex string
		else:
			return value

	def _get_header_compute_cbb(self, die) -> list:
		return sv.socket0.get_by_path(die).computes.name

	## Ratios information for IA/CORES
	def ratios(self, vf = True):
		#Self Class values
		regs = self.regs
		fuse_ram = self.fuse_ram
		dies = self.dies
		sktnum = self.sktnum

		## Init Values
		data_limits ={}
		data_p1 = {}
		data_pstates = {}
		data_read = {}
		data_vf = {}
		data_deltas = {}


		valid_regs = {	'fuses':{'fuses': True, 	'cv':False},
						'cv': 	{'fuses': False, 	'cv':True},
						'all':	{'fuses': True, 	'cv':True}}

		if regs not in valid_regs.keys():
			print ('No valid register selection to be read, valid options are: \n' +
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
		curves = self.ia_ratios
		config = self.Ia_config


		for die in dies:
			computes_list = self._get_header_compute_cbb(die)

			if re.search(r'cbb*', die):
				#instance = ['pcu']
				die_inst = self._set_instance(sktnum, self.base_path, self.base_instance, die, self.base_fuse_test_reg)
				top_inst = self._set_instance(sktnum, self.top_path, self.top_instance, die, self.top_fuse_test_reg)

				#base_val = self._set_instance(sktnum, self.base_path_cv, self.base_instance_cv_cfc, die, self.base_cv_test_cfc_f)
				top_val = self._set_instance(sktnum, self.top_path_cv, self.top_instance_cv_ia, die, self.top_cv_test_ia)

			else:
				print(f'Not valid die selected {die}: Skipping...')
				continue

			## Dumps all fuse data if option is selected
			if regfuse:
				for fuse in die_inst._instances:

					# Limit fuses (RATIO)
					for curve in curves['limits']:
						for pp in config['ppfs']:
							for idx in config['idxs']:
								for ratio in config['ratios']:
									new_curve = self._generate_fuse_from_config(curve, pp, '#ppfs#', idx, '#idxs#', ratio, '#ratios#')
									pointvalue = self._check_data_type(fuse.get_by_path(new_curve).get_value())
									printData(data_limits, new_curve, f'{die}', pointvalue)
									#print(f'{new_curve} = {pointvalue}')

					# P1 fuses (RATIO)
					for curve in curves['p1']:
						for pp in config['ppfs']:
							new_curve = self._generate_fuse_from_config(curve, pp, '#ppfs#')

							pointvalue = self._check_data_type(fuse.get_by_path(new_curve).get_value())
							#print(f'{new_curve} = {pointvalue}')
							printData(data_p1, new_curve, f'{die}', pointvalue)

					# CFC Pstate fuses (RATIO)
					for pstate in curves['pstates'].keys():
						if pstate in config['fusetype']['top']:
							continue
						pstatevalue = self._check_data_type(fuse.get_by_path(curves['pstates'][pstate]).get_value())
						#print(f'{pstate} = {pstatevalue}')
						printData(data_pstates, pstate, f'{die}:{computes_list}', pstatevalue)

				for fuse in top_inst._instances:

					# VF curve ratio values
					for curve in curves['vf_curve']:
						for core in config['cores']:
							for pnt in config['vfpnt']:
								new_curve = self._generate_fuse_from_config(curve,core, '#cores#', pnt, '#vfpnt#')
								#print(new_curve)
								pointvalue = self._check_data_type(fuse.get_by_path(new_curve).get_value())
								printData(data_vf, new_curve, f'{die}:{computes_list}', pointvalue)

					# VF curve ratio values
					for curve in curves['vf_deltas']:
						for core in config['cores']:
							for idx in config['vfidx']:
								for pnt in config['vfpnt']:
									new_curve = self._generate_fuse_from_config(curve,core, '#cores#', idx, '#vfidx#', pnt, '#vfpnt#')
									pointvalue = self._check_data_type(fuse.get_by_path(new_curve).get_value())
									printData(data_deltas, new_curve, f'{die}:{computes_list}', pointvalue)

					# IA Pstate fuses (RATIO)

					for core in config['cores']:
						for pstate in curves['pstates']['p0']:
							new_curve = self._generate_fuse_from_config(pstate, core, '#cores#')
							pstatevalue = self._check_data_type(fuse.get_by_path(new_curve).get_value())
							printData(data_pstates, f'p0_core{core}', f'{die}:{computes_list}', pstatevalue)

			# Dumps current core ratio valus if option is selected
			if regcv:
				for mesh in top_val._instances:
					#print(f'Mesh instance: {mesh.path}')
					for inst in mesh:
						svregister = f'{self.top_cv_ia}'
						try:
							meshvalue = self._check_data_type(inst.get_by_path(svregister).core_frequency.get_value())
							#print(type(inst.get_by_path(svregister).core_frequency.get_value()))
						except:
							meshvalue = 'Not readable'

						printData(data_read, f'{inst.path}.{svregister}.core_frequency', f'{die}', meshvalue)
						#print(f'{meshcv}.ratio = {hex(meshvalue)}')

		if regfuse:
			printTable(data_limits, "IA VF limit fuses (RATIO)")
			printTable(data_p1, "IA P1 power profiles fuses (RATIO)")
			printTable(data_pstates, "IA Pstates Values (RATIO)")
			printTable(data_vf, "IA VF Curve Values (RATIO)")
			printTable(data_deltas, "IA VF Delta Values (RATIO)")
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
			print ('No valid register selection to be read, valid options are: \n' +
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

		curves = self.ia_voltages
		config = self.Ia_config
		#{	'vf_curve': ['pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point0','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point1','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point2','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point3','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point4','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point5'],
		#		}

		#if 'all' in dies:
		#	dies = ['compute0', 'compute1', 'compute2']

		for die in dies:
			computes_list = self._get_header_compute_cbb(die)
			if re.search(r'cbb*', die):
				#instance = ['pcu']
				#die_inst = self._set_instance(sktnum, self.base_path, self.base_instance, die, self.base_fuse_test_reg)
				top_inst = self._set_instance(sktnum, self.top_path, self.top_instance, die, self.top_fuse_test_reg)

				#base_val = self._set_instance(sktnum, self.base_path_cv, self.base_instance_cv_cfc, die, self.base_cv_test_cfc_f)
				top_val = self._set_instance(sktnum, self.top_path_cv, self.top_instance_cv_ia, die, self.top_cv_test_ia)

			else:
				print(f'Not valid die selected {die}: Skipping...')
				continue

			## Dumps all fuse data if option is selected
			if regfuse:
				for fuse in top_inst._instances:

					# VF curve voltage values
					for pnt in config['vfpnt']:
						for core in config['cores']:
							for curve in curves['vf_curve']:
								new_curve = self._generate_fuse_from_config(curve, core, '#cores#', pnt, '#vfpnt#')
								pointvalue = self._check_data_type(fuse.get_by_path(new_curve).get_value())
								printData(data_vf, new_curve, f'{die}:{computes_list}', pointvalue)

			# Dumps current core voltage valus if option is selected
			if regcv:
				for mesh in top_val._instances:
					for inst in mesh:
						svregister = f'{self.top_cv_test_ia}'
						try:
							meshvalue = self._check_data_type(inst.get_by_path(svregister).core_voltage.get_value())
						except:
							meshvalue = 'Not readable'
						printData(data_read, f'{inst.path}.{svregister}.core_voltage', f'{die}', meshvalue)

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
	print('>>> Using Bootscript to start the unit <<< ')
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
			logger('Collecting HWLS Data')
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
	print('>>> Checking BIOS configuration knobs: DfxS3mSoftStrap, DfxSkipWarmResetPromotion, DwrEnable and IerrResetEnabled <<< ')
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
	pf.fusesUpdate(sv)

## Tool for fuse checking of the unit
def fuses(rdFuses=True, sktnum=[0], printFuse=False):
	sv = _get_global_sv()
	#_fuse_instance = config.FUSE_INSTANCE # base.fuses

	imhs = []
	imhs.extend(sv.socket0.imhs.name)

	cbbs = []
	cbbs.extend(sv.socket0.cbbs)

	if rdFuses:
		fuseRAM()

	fusetable = [['Fuse','Value']]

	masks = {}

	for cbb in cbbs:
		cbb_name = cbb.name
		masks[f"ia_{cbb_name}"] =  cbb.base.fuses.punit_fuses.fw_fuses_sst_pp_0_module_disable_mask.read()
		masks[f"llc_{cbb_name}"] = cbb.base.fuses.punit_fuses.fw_fuses_llc_slice_ia_ccp_dis.read()
		fusetable.append([f'ia_{cbb_name}',hex(masks[f"ia_{cbb_name}"])])
		fusetable.append([f'llc_{cbb_name}',hex(masks[f"llc_{cbb_name}"])])

	if printFuse:
		print ('\n>>> Current System fused masks:\n')
		print(tabulate(fusetable, headers="firstrow", tablefmt='grid'))

	return masks

## Tool for converting current unit fuses to a pseudo format, considers all three CLASS fuse configurations
## With the latest update it also shows the RowPass Masks as they were included in the config file
def pseudomask(combine = False, boot = False, Type = 'Class', ext_mask = None):

	sv = _get_global_sv()
	syscbbs = sv.socket0.cbbs.name
	product = config.PRODUCT_CONFIG.lower()
	ClassMask, ClassMask_sys, Masks_test = pseudo_type(Type, product)

	# Product Specific Function for Masking in pseudo Configuration
	ClassMask_sys = pf.pseudo_masking(ClassMask, ClassMask_sys, syscbbs)

	if ext_mask is None:
		masks = fuses()
	else:
		masks = ext_mask


	for cbb in syscbbs:
		cbb_N = sv.socket0.get_by_path(cbb).target_info.instance

		_iamask = masks[f'ia_cbb{cbb_N}']
		_llc_mask = masks[f'llc_cbb{cbb_N}']

		if combine:
			_iamask = bin(_iamask | _llc_mask)
		else:
			_iamask = bin(_iamask)
			_llc_mask = bin(_llc_mask)

		for key in ClassMask_sys.keys():
			if key not in ClassMask.keys():
				continue

			iaMask = int(_iamask,2) | int(ClassMask_sys[key][cbb],2)

			if combine:
				llcMask = iaMask
			else:
				llcMask = int(_llc_mask,2) | int(ClassMask_sys[key][cbb],2)

			ia_core_disable_cbb = hex(iaMask)
			llc_slice_disable_cbb = hex(llcMask)

			Masks_test[key][f'core_cbb_{cbb_N}'] = ia_core_disable_cbb
			Masks_test[key][f'llc_cbb_{cbb_N}'] = llc_slice_disable_cbb


	if not boot:

		core_string = ''
		llc_string = ''
		for key in ClassMask_sys.keys():
			if key not in ClassMask.keys():
				continue


			print (f'\nMasks for pseudo {key} \n')
			for cbb in syscbbs:
				cbb_N = sv.socket0.get_by_path(cbb).target_info.instance
				llc_mask = Masks_test[key][f'llc_cbb_{cbb_N}']
				ia_mask = Masks_test[key][f'core_cbb_{cbb_N}']

				_core_string = f"'cbb_base{cbb_N}' : {ia_mask},"
				_llc_string = f"'cbb_base{cbb_N}' : {llc_mask},"

				#print (core_string)
				#print (llc_string)

				core_string += _core_string
				llc_string += _llc_string

			# This will return the fuse strings to be used in the bootscript
			fuse_ia = f'ia_core_disable = {{{core_string[:-1]}}}'
			fuse_llc = f'llc_slice_disable = {{{llc_string[:-1]}}}'
			bootstring = f'{fuse_ia}, {fuse_llc}'
			print (f"\nAdd the following to your bootscript to use the pseudo for {key} \n")
			print (bootstring)

			# ClearString
			core_string = ''
			llc_string = ''

	else:
		## Used with the pseudo_bs function, wont print fuse data, just return the Mask values to be processed by the script
		return Masks_test

# Already implemented in the chop_str
#def getChipConfig():
#	from namednodes import sv
#	number_of_cbbs = len(sv.socket0.cbbs.names)
#
#	if number_of_cbbs == 4:
#		return 'X4'
#
#	return 'X1'

## Helper function to format hex mask with leading zeros for 32-bit representation
def format_mask_hex(mask_value, bits=32):
	"""
	Convert hex mask string to zero-padded hex format.
	Args:
		mask_value: Hex string (e.g., '0xffffff' or '0xff')
		bits: Number of bits for the output (default 32)
	Returns:
		Zero-padded hex string (e.g., '0x00ffffff' for 32 bits)
	"""
	hex_digits = bits // 4  # 32 bits = 8 hex digits
	return '0x' + hex(int(mask_value, 16))[2:].zfill(hex_digits)

## Uses pseudo Mask configurations to boot the unit, applying the HT disabled fuses to leave it ready for Dragon Pseudo
## Added a S2T key to work with the MESH S2T modes
def pseudo_bs(ClassMask = 'RowEvenPass',
			  Custom = [],
			  boot = True,
			  use_core = False,
			  htdis = True,
			  dis_2CPM = None,
			  dis_1CPM = None,
			  fuse_read = True,
			  s2t = False,
			  masks = None,
			  clusterCheck = None,
			  lsb = False,
			  fuse_cbb =None,
			  fuse_io = None,
			  fast =False,
			  ppvcfuse = False,
			  skip_init = False,
			  vbump = {'enabled':False, 'type':['cfc'],'offset': 0,'cbbs':['cbb0', 'cbb1', 'cbb2', 'cbb3'],'imhs':['imh0', 'imh1'],'computes':['compute0', 'compute1', 'compute2', 'compute3']},
			  dis_mask_checker = True,
			  dis_axon = True):

	#vbump = {'type':['cfc'],'offset': 0,'computes':['compute0', 'compute1', 'compute2']}
	if not skip_init: gcm.svStatus(refresh=True)

	# Product Init
	product = config.PRODUCT_CONFIG.lower()
	chipConfig = chop_str()

	syscbbs = sv.socket0.cbbs.name
	sysimhs = sv.socket0.imhs.name
	clusterCheck = False # Option disbabled in DMR

	# Voltage bumps configuration
	#vbump_target = vbump['cbbs']
	vbump_type = vbump['type']
	vbump_offset = vbump['offset']
	vbump_enabled = vbump['enabled']

	# Generate required arrays / dictionaries
	vbump_array = {cbb: [] for cbb in syscbbs}
	vbump_array.update({imh: [] for imh in sysimhs})

	ppvc_config = {cbb: [] for cbb in syscbbs}
	ppvc_config.update({imh: [] for imh in sysimhs})

	cfc_array = []
	io_array = []
	ia_array = []

	# Init fuse string arrays for base bootscript
	strings = ['base','top0','top1','top2','top3']
	fuse_str_0 = {fs: [] for fs in strings}
	fuse_str_1 = {fs: [] for fs in strings}
	fuse_str_2 = {fs: [] for fs in strings}
	fuse_str_3 = {fs: [] for fs in strings}


	htdis_comp = [] # Not used just for reference
	htdis_io = [] # Not used just for reference
	dis_2CPM_cbb = [] # Not used yet
	dis_1CPM_cbb = []

	## NOT USED: Assign Cluster values *can be taken from a pythonsv register, update later on
	# if variant == 'AP': cluster = 6
	# elif variant == 'SP': cluster = 4
	# else: cluster = 2


	## Mask Type by default we use Class, but if Custom is used we change it to user, might remove this later on
	mType = 'Class'
	if ClassMask == 'Custom':
		mType = 'User'
	elif ClassMask == 'External':
		mType = 'External'

	## NOT USED:Hyper Threading Disable fuses needed to run Dragon pseudo content
	# if htdis:
	# 	htdis_comp = ['scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_fused_ht_dis=0x1', 'pcu.capid_capid0_ht_dis_fuse=0x1','pcu.pcode_lp_disable=0x2','pcu.capid_capid0_max_lp_en=0x1']
	# 	htdis_io = ['punit_iosf_sb.soc_capid_capid0_max_lp_en=0x1','punit_iosf_sb.soc_capid_capid0_ht_dis_fuse=0x1']

	if dis_1CPM != None:
		dis_1CPM_cbb = fuses_dis_1CPM(dis_1CPM, bsformat = True)

	#External fuses added for BurnIn script use
	if fuse_cbb == None: fuse_cbb = []
	if fuse_io == None: fuse_io = []

	## Init Variables and default arrays
	ValidClass = ['RowEvenPass', 'RowOddPass', 'ColumnEvenPass', 'ColumnOddPass', 'Computes0', 'Computes1', 'Computes2', 'Computes3', 'Computes02', 'Computes01', 'Computes13', 'Computes23', 'Computes012', 'Computes123', 'Computes023', 'Computes013', 'Custom', 'External']
	ValidRows = ['ROW0','ROW1','ROW2','ROW3','ROW4','ROW5','ROW6','ROW7']
	ValidCols = []
	ValidCustom = ValidRows + ValidCols
	Fmask = '0xffffffff'
	cbb_size = len(syscbbs)
	imh_size = len(sysimhs)

	# Buidlding the compare mask structure
	core_masks = {f'core_cbb_{num}': Fmask for num in range(cbb_size)}
	llc_masks = {f'llc_cbb_{num}': Fmask for num in range(cbb_size)}
	CompareMask = { 'Custom': {**core_masks, **llc_masks} }

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
	Class_help = {	'RowEvenPass': 'Booting only with Rows 0, 2, 4 and 6',
					'RowOddPass': 'Booting only with Rows 1, 3, 5, and 7',
					'ColumnEvenPass': 'Booting only with Columns 0 and 2',
					'ColumnOddPass': 'Booting only with Columns 1 and 3',
					'Custom' : 'Booting with user mix & match configuration, Cols or Rows',
					'Computes0' : 'Booting only with Computes 0 and 2 on each CBB',
					'Computes1' : 'Booting only with Computes 0 and 2 on each CBB',
					'Computes2' : 'Booting only with Computes 0 and 2 on each CBB',
					'Computes3' : 'Booting only with Computes 0 and 2 on each CBB',
					'Computes02' : 'Booting only with Computes 0 and 2 on each CBB',
					'Computes01' : 'Booting only with Computes 0 and 1 on each CBB',
					'Computes13' : 'Booting only with Computes 1 and 3 on each CBB',
					'Computes23' : 'Booting only with Computes 2 and 3 on each CBB',
					'External' : 'Use configuration from file .\\ConfigFiles\\DMRMasksDebug.json'
	}

	## Checks if the selected ClassMask option is valid
	if ClassMask not in valid_masks:
		if ClassMask == 'Custom':
			for mvalue in Custom:
				#print(valid_masks)
				if mvalue.upper() not in valid_masks:

					print('>>> Masks to be used in Custom, should be either:')
					#print(f' -- ClassMasks:{ValidClass}')
					print(f'> Rows:{ValidRows}')
					print(f'> Columns:{ValidCols}')
					sys.exit()
		elif ClassMask == 'External':
			print('>>> Using external Debug Mask found in file ../ConfigFiles/DMRMasksDebug.json')
		else:
			print(f'>>> Not a valid ClassMask selected use: {valid_masks}')
			sys.exit()

	## Checks for system masks, either external input or checking current system values

	if masks == None: origMask = fuses(rdFuses = fuse_read)
	else: origMask = masks

	## Custom Mask Build - Will add a Core count at the end to validate if pseudo can be used...
	if ClassMask == 'Custom':


		for _CustomVal in Custom:
			CustomVal = _CustomVal.upper()
			Loop_mask = pseudomask(combine = use_core, boot = True, Type = mType, ext_mask = origMask)
			for idx in range(cbb_size):
				CompareMask['Custom'][f'core_cbb_{idx}'] = hex(int(Loop_mask[CustomVal][f'core_cbb_{idx}'],16) & int(CompareMask['Custom'][f'core_cbb_{idx}'],16))
				CompareMask['Custom'][f'llc_cbb_{idx}'] = hex(int(Loop_mask[CustomVal][f'llc_cbb_{idx}'],16) & int(CompareMask['Custom'][f'llc_cbb_{idx}'],16))

			#CompareMask['Custom']['core_cbb_0'] = hex(int(Loop_mask[CustomVal]['core_cbb_0'],16) & int(CompareMask['Custom']['core_cbb_0'],16))
			#if chipConfig == 'X4':
			#	CompareMask['Custom']['core_cbb_1'] = hex(int(Loop_mask[CustomVal]['core_cbb_1'],16) & int(CompareMask['Custom']['core_cbb_1'],16))
			#	CompareMask['Custom']['core_cbb_2'] = hex(int(Loop_mask[CustomVal]['core_cbb_2'],16) & int(CompareMask['Custom']['core_cbb_2'],16))
			#	CompareMask['Custom']['core_cbb_3'] = hex(int(Loop_mask[CustomVal]['core_cbb_3'],16) & int(CompareMask['Custom']['core_cbb_3'],16))

			#CompareMask['Custom']['llc_cbb_0'] = hex(int(Loop_mask[CustomVal]['llc_cbb_0'],16) & int(CompareMask['Custom']['llc_cbb_0'],16))
			#if chipConfig == 'X4':
			#	CompareMask['Custom']['llc_cbb_1'] = hex(int(Loop_mask[CustomVal]['llc_cbb_1'],16) & int(CompareMask['Custom']['llc_cbb_1'],16))
			#	CompareMask['Custom']['llc_cbb_2'] = hex(int(Loop_mask[CustomVal]['llc_cbb_2'],16) & int(CompareMask['Custom']['llc_cbb_2'],16))
			#	CompareMask['Custom']['llc_cbb_3'] = hex(int(Loop_mask[CustomVal]['llc_cbb_3'],16) & int(CompareMask['Custom']['llc_cbb_3'],16))

		Masks_test = CompareMask

	## Class Mask Build, depending on the selected option of First/Second or Third Pass
	else:
		Masks_test = pseudomask(combine = use_core, boot = True, Type = mType, ext_mask = origMask)


	Masks_test, core_count, llc_count = masks_validation(masks = Masks_test, ClassMask = ClassMask, dies = syscbbs, product = product, _clusterCheck = clusterCheck, _lsb = lsb)

	# Dynamically assign core and llc masks based on number of CBBs in syscbbs
	# Always assign cbb0 (minimum requirement)
	core_cbb0 = Masks_test[ClassMask]['core_cbb_0']
	llc_cbb0 = Masks_test[ClassMask]['llc_cbb_0']

	# Initialize optional CBBs to None (will be assigned if they exist)
	core_cbb1 = llc_cbb1 = '0x0'
	core_cbb2 = llc_cbb2 = '0x0'
	core_cbb3 = llc_cbb3 = '0x0'

	if len(syscbbs) >= 2:
		core_cbb1 = Masks_test[ClassMask]['core_cbb_1']
		llc_cbb1 = Masks_test[ClassMask]['llc_cbb_1']

	if len(syscbbs) >= 3:
		core_cbb2 = Masks_test[ClassMask]['core_cbb_2']
		llc_cbb2 = Masks_test[ClassMask]['llc_cbb_2']

	if len(syscbbs) >= 4:
		core_cbb3 = Masks_test[ClassMask]['core_cbb_3']
		llc_cbb3 = Masks_test[ClassMask]['llc_cbb_3']

	# Voltage bumps only change cbbs

	if ('cfc' in vbump_type and vbump['enabled']) and not ppvcfuse:
		#cfc_array_imhs = f.cfc_vbump_array(offset = vbump_offset, include_cbbs=False)
		cfc_array = f.cfc_vbump_array(offset = vbump_offset, include_imhs=False)

	if ('ia' in vbump_type and vbump['enabled']) and not ppvcfuse:
		ia_array = f.ia_vbump_array(offset = vbump_offset)

		# Note: IA will include MLC voltage bumps as well
		#ia_array += f.mlc_vbump_array(offset = vbump_offset)

	# pending pereiras
	if ppvcfuse:
		ppvc_config = ppvc(bsformat=False)

	if not s2t:

		## Checks for htdis option, might recode this at some point this a bit of a lazy way to do it, will also include the option to add custom fuse strings and fuse files, later on.
		# Flatten ppvc_config dictionary values into a single list
		all_ppvc_fuses = []
		if ppvcfuse and isinstance(ppvc_config, dict):
			for key, fuse_list in ppvc_config.items():
				all_ppvc_fuses.extend(fuse_list)
		all_fuses = ia_array + cfc_array + dis_1CPM_cbb + fuse_cbb + all_ppvc_fuses

		if fast:
			print ('>>>  FastBoot option is selected - Starting Boot with Warm Reset')
			print ('>>>  Be aware, this only changes the CoreMasks keeping current CHA configuration')
			fast_fuses = all_fuses

			fast_fuses += gcm.mask_fuse_module_array(ia_masks = {'cbb0':int(core_cbb0,16), 'cbb1':int(core_cbb1,16), 'cbb2':int(core_cbb2,16)})

			print ('>>>  Fuse Configuration to be used in FastBoot\n',fast_fuses)

			# Execute only if Debug is not selected
			if not debug:
				gcm.fuse_cmd_override_reset(fuse_cmd_array=fast_fuses, skip_init=False, boot = boot, s2t=s2t)
			else:
				print ('>>>  Debug mode selected, skipping FastBoot fuse application step\n')
				for fuse in fast_fuses:
					print (f'>>>  Fuse to be applied: {fuse}\n')

			# Waits for EFI and checks fuse application
			# pseudo_efi_check(fuse_option)
			gcm.modulesEnabled()

		else:
			fuse_str = {}
			## Bootscript with or without htdis fuses
			if chipConfig == 'X4':
				fuse_str_0 = dmr_fuse_fix(fuse_str = all_fuses, cbb_name= 'cbb0')
				fuse_str_1 = dmr_fuse_fix(fuse_str = all_fuses, cbb_name= 'cbb1')
				fuse_str_2 = dmr_fuse_fix(fuse_str = all_fuses, cbb_name= 'cbb2')
				fuse_str_3 = dmr_fuse_fix(fuse_str = all_fuses, cbb_name= 'cbb3')
				llc_fuse_data = {'cbb_base0':llc_cbb0, 'cbb_base1':llc_cbb1, 'cbb_base2':llc_cbb2, 'cbb_base3':llc_cbb3}
				ia_fuse_data = {'cbb_base0':core_cbb0, 'cbb_base1':core_cbb1, 'cbb_base2':core_cbb2, 'cbb_base3':core_cbb3}
				bscript_0 = (	'pwrgoodmethod="usb", '
								'pwrgoodport=[1,2], '
								'pwrgooddelay=30, '
								'fused_unit=True, '
								f'disable_mask_checker={dis_mask_checker}, '
								f'disable_axon={dis_axon}, '
								'enable_strap_checks=False, '
								f'compute_config="{chipConfig}", '
								'enable_pm=True, '
								f'ia_core_disable= {ia_fuse_data}, '
								f'llc_slice_disable={llc_fuse_data}'
								)

				fuse_str = {
							'cbb_base0':fuse_str_0['base'],
							'cbb0_top0':fuse_str_0['top0'],
							'cbb0_top1':fuse_str_0['top1'],
							'cbb0_top2':fuse_str_0['top2'],
							'cbb0_top3':fuse_str_0['top3'],
							'cbb_base1':fuse_str_1['base'],
							'cbb1_top0':fuse_str_1['top0'],
							'cbb1_top1':fuse_str_1['top1'],
							'cbb1_top2':fuse_str_1['top2'],
							'cbb1_top3':fuse_str_1['top3'],
							'cbb_base2':fuse_str_2['base'],
							'cbb2_top0':fuse_str_2['top0'],
							'cbb2_top1':fuse_str_2['top1'],
							'cbb2_top2':fuse_str_2['top2'],
							'cbb2_top3':fuse_str_2['top3'],
							'cbb_base3':fuse_str_3['base'],
							'cbb3_top0':fuse_str_3['top0'],
							'cbb3_top1':fuse_str_3['top1'],
							'cbb3_top2':fuse_str_3['top2'],
							'cbb3_top3':fuse_str_3['top3']
							}

			elif chipConfig == 'X1':
				fuse_str_0 = dmr_fuse_fix(fuse_str = all_fuses, cbb_name= 'cbb0')
				llc_fuse_data = {'cbb_base0':llc_cbb0}
				ia_fuse_data = {'cbb_base0':core_cbb0}
				bscript_0 = (	'pwrgoodmethod="usb", '
								'pwrgoodport=[1,2], '
								'pwrgooddelay=30, '
								'fused_unit=True, '
								'enable_strap_checks=False, '
								f'disable_mask_checker={dis_mask_checker}, '
								f'disable_axon={dis_axon}, '
								f'compute_config="{chipConfig}", '
								'enable_pm=True, '
								f'ia_core_disable= {ia_fuse_data}, '
								f'llc_slice_disable={llc_fuse_data}'
								)

				fuse_str = {
							'cbb_base0':fuse_str_0['base'],
							'cbb0_top0':fuse_str_0['top0'],
							'cbb0_top1':fuse_str_0['top1'],
							'cbb0_top2':fuse_str_0['top2'],
							'cbb0_top3':fuse_str_0['top3'],
							}

				bscript_1 = (
				', fuse_str='
				f'{fuse_str}'
				','# dynamic_fuse_inject={{"top":my_method}}'
				)
			## Display data on screen, showing configuration to be used based on selection
			print (f'\n>>>  Bootscript configuration for {ClassMask} ')
			print (f'>>>  {Class_help[ClassMask]}')
			if ClassMask == 'Custom':
				print (f'>>>  Custom Mask Selected: {Custom}')
			# print (f'>>>  Core/LLC enabled total Count: CORE = {core_count}, LLC = {llc_count}')
			print (f'>>>  Using Compute 0 Masks: CORE = {core_cbb0}, LLC = {llc_cbb0}')

			if chipConfig == 'X4':
				print (f'>>>  Using Compute 1 Masks: CORE = {core_cbb1}, LLC = {llc_cbb1}')
				print (f'>>>  Using Compute 2 Masks: CORE = {core_cbb2}, LLC = {llc_cbb2}')
				print (f'>>>  Using Compute 3 Masks: CORE = {core_cbb3}, LLC = {llc_cbb3}')
			# if htdis:print (f'>>>  Applying HT Disabled Fuses : Computes = {htdis_comp}')
			# if htdis:print (f'>>>  Applying HT Disabled Fuses : Computes = {htdis_io} \n')
			print ('>>>  Running Bootscript: \n')
			print (f">>>  b.go({bscript_0}{bscript_1})")


			fuse_option = {'cbb0':fuse_str_0,'cbb1':fuse_str_1,'cbb2':fuse_str_2, 'cbb3':fuse_str_3}

			## Either run the bootscript or just print the bootscript string in case additional feats need to be added on it.
			# pending pereiras -- Not finished yet
			if not debug and boot:
				print ('>>>  Boot option is selected - Starting Bootscript')
			#	if htdis:

				if chipConfig == 'X4': b.go(pwrgoodmethod="usb",
											pwrgoodport=[1,2],
											pwrgooddelay=30,
											fused_unit=True,
											enable_strap_checks=False,
											disable_mask_checker=dis_mask_checker,
											disable_axon=dis_axon,
											compute_config=chipConfig,
											enable_pm=True,
											ia_core_disable={"cbb_base0":core_cbb0, "cbb_base1":core_cbb1, "cbb_base2":core_cbb2, "cbb_base3":core_cbb3},
											llc_slice_disable={"cbb_base0":llc_cbb0, "cbb_base1":llc_cbb1, "cbb_base2":llc_cbb2, "cbb_base3":llc_cbb3},
											fuse_str=fuse_str)

				if chipConfig == 'X1': b.go(pwrgoodmethod='usb',
											pwrgoodport=[1,2],
											pwrgooddelay=30,
											fused_unit=True,
											enable_strap_checks=False,
											disable_mask_checker=dis_mask_checker,
											disable_axon=dis_axon,
											compute_config=chipConfig,
											enable_pm=True,
											ia_core_disable={"cbb_base0":core_cbb0}, llc_slice_disable={"cbb_base0":llc_cbb0},
											fuse_str=fuse_str)
			else:
				if debug: print ('>>>  Debug mode selected, skipping Bootscript execution step\n')
				# Waits for EFI and checks fuse application
				print ('\n>>>  Boot option not selected -- Copy bootscript code  above and edit if needed to run manually')
	else:

		# Returning counts in case we need to validate something in S2T -- Not used currently
		return core_count, llc_count, Masks_test


# pereiras, pending to add the correct regs, currently it's dummy function
def my_method(socket: str, die: str, fuse_override_iteration=None)->int:
	print("Testing")
	socket_id = int(socket)
	if 'cbb' in die:
		cbb_name = die.split('.')
		sv.sockets[socket_id].sub_components[cbb_name[0]].computes.fuses.core0_fuse.core_fuse_core_fuse_acode_ia_base_vf_voltage_0=0x8
	return 0

## PSEUDO bs EFI Checks
## Looks for fuse application, in case one of them is not applied will raise a flag
## Checks masking with coresenabled and fuse applied with the fuse override check script
def pseudo_efi_check(fuses):
		print('>>>  Waiting for EFI PostCode')
		EFI_POST = gcm.EFI_POST
		gcm._wait_for_post(EFI_POST, sleeptime=60)

		print('>>>  Checking all Fuses for Compute0 Applied correctly')
		fuseRAM(refresh=True)

		for f in fuses.keys():
			if f:
				print(f'>>> Checking fuse application for {f.upper()}')
				gcm.fuse_cmd_override_check(fuse_cmd_array = fuses[f], skip_init= True, bsFuses = f)

		gcm.modulesEnabled()

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

def get_selected_product(): # DMR will use device_name
	#product = sv.socket0.target_info["device_name"].upper()
	product = config.SELECTED_PRODUCT.upper()
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
	return int((core % config.MODS_PER_CBB) / config.MODS_PER_COMPUTE)

def get_cbb_index(core=None):
	return int(core/config.MODS_PER_CBB)

def get_single_compute_apic_location(core=None):
	target_compute = get_compute_index(core=core)
	apic_location = core - target_compute * 8
	return apic_location

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

# CBB Top and Base fuse string modification for bootscript array usage
def dmr_fuse_fix(fuse_str = {}, cbb_name = 'cbb0', sockets = ['0','s']):
	bs_fuse_array = []

	fuses_keys = ['base','top0','top1','top2','top3']
	fuses = {k:[] for k in fuses_keys}
	base_string = '.base.'
	bases = [f'sv.socket{socket}.{cbb_name}.base.fuses.' for socket in sockets]

	compute_string = ['s', '0', '1', '2', '3']

	# Check for Base and Top fuses
	# Base Check
	fuses['base'].extend(bs_fuse_fix(fuse_str = fuse_str, bases = bases))

	# Top Check
	for cs in compute_string:
		top_bases = [f'sv.socket{socket}.{cbb_name}.compute{cs}.fuses.' for socket in sockets]
		if cs != 's':
			fuses[f'top{cs}'].extend(bs_fuse_fix(fuse_str = fuse_str, bases = top_bases))
		else:
			fstring = bs_fuse_fix(fuse_str = fuse_str, bases = top_bases)

			fuses['top0'].extend(fstring)
			fuses['top1'].extend(fstring)
			fuses['top2'].extend(fstring)
			fuses['top3'].extend(fstring)

	return fuses

## PPVC Fuses configuration,
def ppvc(bsformat = False, ppvc_fuses = [], updateram=False):
	print("\n***********************************v********************************************")
	print('Searching for PPVC fuses, please enter requested values for proper configuration:')
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
			print('Skipping PPVC Configuration --')
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
	print('PPVC configuration fuses collected adding them to boot configuration')
	print("***********************************v********************************************\n")
	return ppvc_confg

## Voltage read for S2T
def tester_voltage(bsformat = False, volt_dict = {}, volt_fuses = None, fixed = True, vbump=False, updateram=False, fixmlc=True):
	print("\n***********************************v********************************************")
	print(f'Changing Voltage fuses based on System 2 Tester Configuration: Type {"Fixed" if fixed else ""}{"vBump" if vbump else ""}')
	for k,v in volt_dict.items():
		print(f'>>>  Voltage setting for {k.upper()}: {v}V')
	#ppvc_fuses = f.ppvc_rgb_reduction(boot=False)
	## I have rebuilt the ppvc script here instead of using what is in GFO in case additional customization is needed
	if updateram: fuseRAM(refresh = False)

	# This is changing for DMR -- not compatible with previous products (GNR/CWF)
	# Be careful when updating this section in older products
	if volt_fuses == None:
		volt_fuses = []

	cbbs = config.MAX_CBBS
	base_top_config = {'base':[], 'top0':[], 'top1':[], 'top2':[], 'top3':[]}
	imh_config = {'imh0':[], 'imh1':[]}


	volt_config = { f'cbb{c}': base_top_config for c in range(cbbs)}
	volt_config.update(imh_config)

	#computes = len(syscomputes)
	if fixed:
		if volt_dict['core'] != None: volt_fuses+=f.ia_vbump_array(fixed_voltage = volt_dict['core']) # Adding IA fuses


		if isinstance(volt_dict['cfc_die'], dict):
			for k,v in volt_dict['cfc_die'].items():
				if volt_dict['cfc_die'][k] != None:
					volt_fuses+=f.cfc_vbump_array(fixed_voltage = v, target_cbb=int(k[-1]), include_cbbs=True, include_imhs=False)
		else:
			if volt_dict['cfc_die'] != None:
				volt_fuses+=f.cfc_vbump_array(fixed_voltage = volt_dict['cfc_die'], include_cbbs=True, include_imhs=False) # Adding CFC fuses

		if isinstance(volt_dict['core_mlc'], dict):
			for k,v in volt_dict['core_mlc'].items():
				if volt_dict['core_mlc'][k] != None:
					volt_fuses+=fuses_mlc_vbumps(fixed_voltage = v, target_cbb=int(k[-1]), fix=fixmlc)

		else:
			if volt_dict['core_mlc'] != None:
				volt_fuses+=fuses_mlc_vbumps(fixed_voltage = volt_dict['core_mlc'], fix=fixmlc)

		# No HDC in DMR -- Left for reference
		if isinstance(volt_dict['hdc_die'], dict):
			for k,v in volt_dict['hdc_die'].items():
				if volt_dict['hdc_die'][k] != None:
					volt_fuses+=f.hdc_vbump_array(fixed_voltage = v, target_cbb=int(k[-1]))
		else:
			if volt_dict['hdc_die'] != None:
				volt_fuses+=f.hdc_vbump_array(fixed_voltage = volt_dict['hdc_die']) # Adding HDC fuses


		if volt_dict['ddrd'] != None:volt_fuses+=f.ddrd_vbump_array(fixed_voltage = volt_dict['ddrd']) # Adding DDRD fuses
		#if volt_dict['ddra'] != None:volt_fuses+=f.ddra_vbump_array(fixed_voltage = volt_dict['ddra'], computes = computes) # Adding DDRA fuses -- WIP
		if volt_dict['cfc_io'] != None:volt_fuses+=f.cfc_vbump_array(fixed_voltage = volt_dict['cfc_io'], include_cbbs=False, include_imhs=True) # Adding CFCxIO fuses

	elif vbump:
		if volt_dict['core'] != None: volt_fuses+=f.ia_vbump_array(offset = volt_dict['core']) # Adding IA fuses
		#if volt_dict['cfc_die'] != None: volt_fuses+=f.cfc_vbump_array(offset = volt_dict['cfc_die'], computes = computes) # Adding CFC fuses
		#if volt_dict['hdc_die'] != None: volt_fuses+=f.hdc_vbump_array(offset = volt_dict['hdc_die'], computes = computes) # Adding HDC fuses

		if isinstance(volt_dict['cfc_die'], dict):
			for k,v in volt_dict['cfc_die'].items():
				if volt_dict['cfc_die'][k] != None:
					volt_fuses+=f.cfc_vbump_array(offset = v, target_cbb=int(k[-1]), include_cbbs=True, include_imhs=False)
		else:
			if volt_dict['cfc_die'] != None:
				volt_fuses+=f.cfc_vbump_array(offset = volt_dict['cfc_die'], include_cbbs=True, include_imhs=False) # Adding CFC fuses

		if isinstance(volt_dict['core_mlc'], dict):
			for k,v in volt_dict['core_mlc'].items():
				if volt_dict['core_mlc'][k] != None:
					volt_fuses+=fuses_mlc_vbumps(offset = v, target_cbb=int(k[-1]), fix=fixmlc)

		else:
			if volt_dict['core_mlc'] != None:
				volt_fuses+=fuses_mlc_vbumps(offset = volt_dict['core_mlc'], fix=fixmlc)

		# No HDC in DMR -- Left for reference
		if isinstance(volt_dict['hdc_die'], dict):
			for k,v in volt_dict['hdc_die'].items():
				if volt_dict['hdc_die'][k] != None:
					volt_fuses+=f.hdc_vbump_array(offset = v, target_cbb=int(k[-1]))
		else:
			if volt_dict['hdc_die'] != None:
				volt_fuses+=f.hdc_vbump_array(offset = volt_dict['hdc_die']) # Adding HDC fuses


		if volt_dict['ddrd'] != None: volt_fuses+=f.ddrd_vbump_array(offset = volt_dict['ddrd']) # Adding DDRD fuses
		#if volt_dict['ddra'] != None: volt_fuses+=f.ddra_vbump_array(offset = volt_dict['ddra'], computes = computes) # Adding DDRA fuses -- WIP
		if volt_dict['cfc_io'] != None: volt_fuses+=f.cfc_vbump_array(offset = volt_dict['cfc_io'], include_cbbs=False, include_imhs=True) # Adding CFCxIO fuses

	#ppvc_fuses+=f.cfn_vbump_array(fixed_voltage = volt_values['cfn']) # Adding CFN fuses
	#ppvc_fuses+=f.vccinf_vbump_array(fixed_voltage = volt_values['core'], computes = computes) # Adding VCCINF fuses


	fuses_cbb0 = [f for f in volt_fuses if '.cbb0' in f]
	fuses_cbb1 = [f for f in volt_fuses if '.cbb1' in f]
	fuses_cbb2 = [f for f in volt_fuses if '.cbb2' in f]
	fuses_cbb3 = [f for f in volt_fuses if '.cbb3' in f]
	fuses_imh0 = [f for f in volt_fuses if '.imh0' in f]
	fuses_imh1 = [f for f in volt_fuses if '.imh1' in f]

	if bsformat:
		print(f'\n {"*"*5} Modifying fuses to be usable in a bootscript array for each die {"*"*5}\n')
		if fuses_cbb0: fuses_cbb0 = dmr_fuse_fix(fuse_str = fuses_cbb0, cbb_name = 'cbb0')
		if fuses_cbb1: fuses_cbb1 = dmr_fuse_fix(fuse_str = fuses_cbb1, cbb_name = 'cbb1')
		if fuses_cbb2: fuses_cbb2 = dmr_fuse_fix(fuse_str = fuses_cbb2, cbb_name = 'cbb2')
		if fuses_cbb3: fuses_cbb3 = dmr_fuse_fix(fuse_str = fuses_cbb3, cbb_name = 'cbb3')
		if fuses_imh0: fuses_imh0 = bs_fuse_fix(fuse_str = fuses_imh0, bases = ['sv.socket0.imh0.fuses.'])
		if fuses_imh1: fuses_imh1 = bs_fuse_fix(fuse_str = fuses_imh1, bases = ['sv.socket0.imh0.fuses.'])

	volt_config = {	'cbb0':fuses_cbb0,
					'cbb1':fuses_cbb1,
					'cbb2':fuses_cbb2,
					'cbb3':fuses_cbb3,
					'imh0':fuses_imh0,
					'imh1':fuses_imh1,}

	print('Voltage configuration fuses collected, adding them to boot configuration')
	print("***********************************v********************************************\n")
	return volt_config

def process_fuse_file(fuse_file_path):
	"""
	Process a .fuse file and return the list of register assignments.

	Args:
		fuse_file_path: Path to the .fuse configuration file

	Returns:
		List of register assignments in format: ['sv.socket0.cbb0.base.fuses.register=0x1', ...]
	"""
	if not fuse_file_path:
		return []

	try:
		print(f"\n>>> Processing fuse file: {fuse_file_path}")
		fuse_list = ffg.process_fuse_file(fuse_file_path)
		print(f">>> Successfully loaded {len(fuse_list)} fuses from file")
		return fuse_list
	except FileNotFoundError:
		print(f"ERROR: Fuse file not found: {fuse_file_path}")
		return []
	except ValueError as e:
		print(f"ERROR: Failed to parse fuse file: {e}")
		return []
	except Exception as e:
		print(f"ERROR: Unexpected error processing fuse file: {e}")
		return []

def external_fuses(external_fuses = None, bsformat = False, ):
	if external_fuses is None:
		external_fuses = []

	print("\n***********************************v********************************************")
	print('Adding External fuses to the boot configuration')
	#ppvc_fuses = f.ppvc_rgb_reduction(boot=False)
	## I have rebuilt the ppvc script here instead of using what is in GFO in case additional customization is needed

	cbb_range = sv.socket0.cbbs.name
	imh_range = sv.socket0.imhs.name

	# Initialize fuse dictionaries dynamically based on available units
	cbb_fuses = {cbb: [] for cbb in cbb_range}
	imh_fuses = {imh: [] for imh in imh_range}

	# Separate specific and common fuses
	fuses_cbbs_common = [f for f in external_fuses if '.cbbs.' in f]
	fuses_imhs_common = [f for f in external_fuses if '.imhs.' in f]

	# Process specific CBB fuses dynamically
	all_possible_cbbs = ['cbb0', 'cbb1', 'cbb2', 'cbb3', 'cbb4', 'cbb5', 'cbb6', 'cbb7']  # Extend as needed
	for cbb in all_possible_cbbs:
		temp_fuses = [f for f in external_fuses if f'.{cbb}.' in f]
		if temp_fuses:
			if cbb in cbb_range:
				cbb_fuses[cbb] = temp_fuses
			else:
				print(f'WARNING: Fuses for {cbb} are included but system does not have {cbb}. Fuses will NOT be applied.')

	# Process specific IMH fuses dynamically
	all_possible_imhs = ['imh0', 'imh1', 'imh2', 'imh3']  # Extend as needed
	for imh in all_possible_imhs:
		temp_fuses = [f for f in external_fuses if f'.{imh}.' in f]
		if temp_fuses:
			if imh in imh_range:
				imh_fuses[imh] = temp_fuses
			else:
				print(f'WARNING: Fuses for {imh} are included but system does not have {imh}. Fuses will NOT be applied.')

	# Expand common CBB fuses to all available CBBs
	for fuse in fuses_cbbs_common:
		print(f'>>>  Expanding common CBB fuse to all CBBs: {fuse}')
		for cbb in cbb_range:
			expanded_fuse = fuse.replace('.cbbs.', f'.{cbb}.')
			cbb_fuses[cbb].append(expanded_fuse)

	# Expand common IMH fuses to all available IMHs
	for fuse in fuses_imhs_common:
		print(f'>>>  Expanding common IMH fuse to all IMHs: {fuse}')
		for imh in imh_range:
			expanded_fuse = fuse.replace('.imhs.', f'.{imh}.')
			imh_fuses[imh].append(expanded_fuse)

	# Print specific fuses being added (only non-expanded ones)
	all_specific_fuses = []
	for fuse_list in list(cbb_fuses.values()) + list(imh_fuses.values()):
		all_specific_fuses.extend(fuse_list)

	for f in all_specific_fuses:
		is_expanded = False
		for common_fuse in fuses_cbbs_common + fuses_imhs_common:
			if common_fuse.replace('.cbbs.', '.').replace('.imhs.', '.') in f:
				is_expanded = True
				break
		if not is_expanded:
			print(f'>>>  External fuse to be added: {f}')

	# Apply bsformat transformation if requested
	if bsformat:
		print(f'\n {"*"*5} Modifying fuses to be usable in a bootscript array for each die {"*"*5}\n')
		for cbb in cbb_range:
			if cbb_fuses[cbb]:
				cbb_fuses[cbb] = dmr_fuse_fix(fuse_str=cbb_fuses[cbb], cbb_name=cbb)
		for imh in imh_range:
			if imh_fuses[imh]:
				imh_fuses[imh] = bs_fuse_fix(fuse_str=imh_fuses[imh], bases=[f'sv.socket0.{imh}.fuses.'])

	# Build external_config dictionary with all units
	external_config = {}
	for cbb in cbb_range:
		external_config[cbb] = cbb_fuses[cbb]
	for imh in imh_range:
		external_config[imh] = imh_fuses[imh]

	# Keep common lists for reference  -- Not using this currently
	#external_config['cbbs'] = fuses_cbbs_common
	#external_config['imhs'] = fuses_imhs_common

	print('External configuration fuses collected, adding them to boot configuration')
	print("***********************************v********************************************\n")
	return external_config

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

## Build arrays for FastBoot - Place for the 4CPM product
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

def fuses_dis_1CPM(dis_cores, bsformat = True):
	'''
	dis_cores: 'HIGH' or 'LOW' to disable globally on all modules. usefull to run pseudo MESH
	'''
	valid_configs = [0x1, 0x2]
	if dis_cores == 'HIGH':
		dis=0x2
	elif dis_cores == 'LOW':
		dis=0x1
	elif dis_cores in valid_configs:
		dis = dis_cores
	else:
		print(f"-ERROR- cores has to be define as LOW, HIGH or any value in: {valid_configs}")
		return None
	fuse=[]
	if bsformat:
		for core_n in range (0,8):
			fuse += [f"fuses.core{core_n}_fuse.core_fuse_core_fuse_pma_lp_enable={dis:#x}"]
	else:
		for core_n in range (0,8):
			fuse += [f"sv.socket0.cbbs.computes.fuses.core{core_n}_fuse.core_fuse_core_fuse_pma_lp_enable={dis}"]
		# fuse = [f"sv.socket0.computes.fuses.pcu.pcode_lp_disable={dis}"]
	return fuse

def fuses_freq_cfc(ratio: hex = 0x8, include_imhs: bool=True, include_cbbs: bool = True)->list:
	dpmarray = []
	dpmarray = f.cfc_fixed_ratio_array(	ratio=ratio,
										include_imhs=include_imhs,
										include_cbbs=include_cbbs)
	return dpmarray

def fuses_freq_ia(ratio: hex = 0x8, include_imhs: bool=True, include_cbbs: bool = False, include_boot: bool = False)->list:
	dpmarray = []
	dpmarray = f.ia_fixed_ratio_array(	ratio=ratio,
										include_imhs=include_imhs,
										include_cbbs=include_cbbs)
	if include_boot:
		dpmarray += f.ia_fixed_boot_array(ratio=ratio)
	return dpmarray

# HT Disable fuse array not implemented for DMR - use disable 1CPM instead
def fuses_htdis() -> NotImplementedError:
	return NotImplementedError("HT Disable fuses are not available for DMR product")

# VCCIN fuse array not implemented for DMR yet
def fuses_vccin(types = ['io', 'compute'], domains = ['active', 'idle', 'safe'], value = 1.89, bsformat = False, skip_init=False):
	raise NotImplementedError("VCCIN not implemented yet for DMR product")

# Reference Call to FuseOverride Class for VCCINF VBump arrays
def fuses_vccinf( offset: float = 0,
                 skip_init: bool = False,
                 rgb_array: dict = {},
                 target_socket: int | None = None,
                 target_imhs: int | None = None,
                 fixed_voltage: float | None = None) -> list:

	if not skip_init: fuseRAM(refresh = True)

	dpmarray = f.vccinf_vbump_array_imh(	offset=offset,
									rgb_array=rgb_array,
									target_socket=target_socket,
									target_imhs=target_imhs,
									fixed_voltage=fixed_voltage)
	return dpmarray

## Below arrays uses the GNRFuseOverride script @ thr folder, adding them here for ease of use --
# Reference Call to FuseOverride Class for CFC VBump arrays
def fuses_cfc_vbumps(offset: float = 0,
                     rgb_array: dict = {},
                     skip_init: bool = False,
                     target_socket: int | None = None,
                     target_cbb: int | None = None,
                     target_compute: int | None = None,
                     target_core: int | None = None,
                     fixed_voltage: float | None = None,
                     ) -> list:

	if not skip_init: fuseRAM(refresh = True)
	include_cbbs = True
	include_imhs = False
	dpmarray = []
	dpmarray = f.cfc_vbump_array(	offset=offset,
									rgb_array=rgb_array,
									target_socket=target_socket,
									target_cbb=target_cbb, target_compute=target_compute,
									target_core=target_core, fixed_voltage=fixed_voltage,
									include_cbbs=include_cbbs, include_imhs=include_imhs)


	return dpmarray

# Reference Call to FuseOverride Class for CFCxIO VBump arrays
def fuses_cfc_io_vbump_array(offset: float = 0,
                     rgb_array: dict = {},
                     skip_init: bool = False,
                     target_socket: int | None = None,
                     target_cbb: int | None = None,
                     target_compute: int | None = None,
                     target_core: int | None = None,
                     fixed_voltage: float | None = None,
                     ) -> list:

	if not skip_init: fuseRAM(refresh = True)
	include_cbbs = False
	include_imhs = True
	dpmarray = []
	dpmarray = f.cfc_vbump_array(	offset=offset,
									rgb_array=rgb_array,
									target_socket=target_socket,
									target_cbb=target_cbb, target_compute=target_compute,
									target_core=target_core, fixed_voltage=fixed_voltage,
									include_cbbs=include_cbbs, include_imhs=include_imhs)


	return dpmarray

# This function is not available for DMR
def fuses_hdc_vbumps(offset = 0, rgb_array={}, point = None, skip_init=False, fixed_voltage = None, target_compute = None):
	raise NotImplementedError('-ERROR- HDC VBump fuses are not available for DMR product')

# Reference Call to FuseOverride Class for DDRD VBump arrays
def fuses_ddrd_vbumps(offset: float = 0,
                      skip_init: bool = False,
                      rgb_array: dict = {},
                      target_socket: int| None = None,
                      target_imhs: int | None = None,
                      fixed_voltage: float | None = None) -> list:

	if not skip_init: fuseRAM(refresh = True)
	#computes = len(sv.socket0.computes)
	dpmarray = []
	dpmarray = f.ddrd_vbump_array(offset = offset,
                               rgb_array= rgb_array,
                               target_socket = target_socket,
                               target_imhs = target_imhs,
                               fixed_voltage = fixed_voltage)
	return dpmarray

# This function is not implemented for DMR yet
def fuses_ddra_vbumps(offset = 0, rgb_array={}, point = None, skip_init=False, fixed_voltage = None, target_compute = None):
	raise NotImplementedError("DDRA VBump fuses are not yet implemented for DMR product")

# Reference Call to FuseOverride Class for IA VBump arrays
def fuses_ia_vbumps(offset: float = 0,
                    rgb_array: dict = {},
                    skip_init: bool = False,
                    fixed_voltage: float | None = None,
                    target_socket: int | None = None,
                    target_cbb: int | None = None,
                    target_compute: int | None = None,
                    target_core: int | None = None ) -> list:

	if not skip_init: fuseRAM(refresh = True)
	dpmarray = []
	dpmarray = f.ia_vbump_array(offset=offset,
                             rgb_array=rgb_array,
                             target_socket=target_socket,
                             target_cbb=target_cbb,
                             target_compute=target_compute,
                             target_core=target_core,
                             fixed_voltage=fixed_voltage)
	return dpmarray

# Reference Call to FuseOverride Class for MLC VBump arrays
def fuses_mlc_vbumps(offset: float = 0,
                    rgb_array: dict = {},
                    skip_init: bool = True,
                    fixed_voltage: float | None = None,
                    target_socket: int | None = None,
                    target_cbb: int | None = None,
                    target_compute: int | None = None,
                    target_core: int | None = None,
                    fix=True) -> list:

	if not skip_init: fuseRAM(refresh = True)
	dpmarray = []
	dpmarray = f.mlc_vbump_array(offset=offset,
                             rgb_array=rgb_array,
                             target_socket=target_socket,
                             target_cbb=target_cbb,
                             target_compute=target_compute,
                             target_core=target_core,
                             fixed_voltage=fixed_voltage)
	return dpmarray if not fix else mlc_fuse_fix(dpmarray)


def read_fuse_array(fuse_array: list, skip_init: bool = False):
	#dpm_array = fuse_array
	print('Reading fuse values from entered array... ')
	f.read_array(fuse_array=fuse_array, skip_init=skip_init, load_fuses=False)

## Uses USB Splitter controller to power cycle / on / off the unit --
def powercycle(stime = 20, ports = [1,2]):
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
		print (' ---  Boot option is selected - Starting Bootscript')
		if variant == 'AP': b.go(pwrgoodmethod='usb', pwrgoodport=1, pwrgooddelay=30, fused_unit=True, enable_strap_checks=False,compute_config=COMPUTE_CONFIG,enable_pm=True,segment=SEGMENT, fuse_str_compute = _fuse_str_compute,fuse_str_io = _fuse_str_io)
		if variant == 'SP': b.go(pwrgoodmethod='usb', pwrgoodport=1, pwrgooddelay=30, fused_unit=True, enable_strap_checks=False,compute_config=COMPUTE_CONFIG,enable_pm=True,segment=SEGMENT, fuse_str_compute = _fuse_str_compute,fuse_str_io = _fuse_str_io)
	else:
		print ('\n ---  Boot option not selected -- Copy bootscript code  above and edit if needed to run manually')
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
	MAXCORESPERCBB = config.MAXPHYSICAL
	if variant == 'AP': cluster = 6
	elif variant == 'SP': cluster = 4
	else: cluster = 2

	cores = {'cbb0':MAXCORESPERCBB,'cbb1':MAXCORESPERCBB,'cbb2':MAXCORESPERCBB,'cbb3':MAXCORESPERCBB}
	llcs = {'cbb0':MAXCORESPERCBB,'cbb1':MAXCORESPERCBB,'cbb2':MAXCORESPERCBB,'cbb3':MAXCORESPERCBB}
	core_count = 0
	llc_count = 0

	for compute in dies:
		dieN = compute[-1]
		cores[compute] = MAXCORESPERCBB - binary_count(masks[ClassMask][f'core_cbb_{dieN}'])
		llcs[compute] = MAXCORESPERCBB - binary_count(masks[ClassMask][f'llc_cbb_{dieN}'])

	#min_llc = llcs['compute0'] ## Defaulting to COMP0 if all are the same we dont change it
	min_llc = min(llcs['cbb0'],llcs['cbb1'],llcs['cbb2'], llcs['cbb3'])
	if min_llc % 2 != 0:
		## Limiting to a minimum of 2 LLCs
		min_llc = max(min_llc - 1,2)

	if _clusterCheck:
		print(f'\nRecommended LLC to be used for each Compute die = {min_llc}, to be in line with a clustering of {cluster}')
		for compute in dies:
			print(f'\tEnabled CORES/LLCs for {compute.upper()}: LLCs = {llcs[compute]} , COREs = {cores[compute]}')

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

# Temporal fix for MLC Fuses bit assignments
def mlc_fuse_fix(fuse_str = []):
	new_fuse_str = merge_register_bit_assignments(fuse_str, reg_width=24)
	return new_fuse_str

def merge_register_bit_assignments(register_assignments, reg_width=32):
	"""
	Merge multiple bit-range assignments for the same base register into complete register values.

	This function takes register assignments with bit ranges and combines them into single
	full-register assignments, filling unspecified bits with 0.

	Parameters
	----------
	register_assignments : list of str
		List of register assignment strings with bit ranges.
		Format: "base.register.path[high:low] = value" or "base.register.path[bit] = value"
		Example: "sv.socket0.cbb0.compute0.fuses.core0_fuse.core_fuse_core_fuse_acode_acode_spare_word_0[8:0] = 0xb7"
	reg_width : int, optional
		Register width in bits (default: 32)

	Returns
	-------
	list of str
		List of complete register assignments in format "base.register.path = 0xvalue"

	Examples
	--------
	>>> assignments = [
	...     "sv.socket0.cbb0.compute0.fuses.core0_fuse.core_fuse_core_fuse_acode_acode_spare_word_0[8:0] = 0xb7",
	...     "sv.socket0.cbb0.compute0.fuses.core0_fuse.core_fuse_core_fuse_acode_acode_spare_word_0[24:16] = 0xbc"
	... ]
	>>> result = merge_register_bit_assignments(assignments)
	>>> print(result[0])
	'sv.socket0.cbb0.compute0.fuses.core0_fuse.core_fuse_core_fuse_acode_acode_spare_word_0 = 0xbc00b7'
	"""
	import re

	# Dictionary to store register base paths and their bit assignments
	register_map = {}

	# Regular expression to parse register assignments
	# Matches: base_path[high:low] = value or base_path[bit] = value
	pattern = r'^(.+?)\[(\d+)(?::(\d+))?\]\s*=\s*(.+)$'

	for assignment in register_assignments:
		assignment = assignment.strip()
		match = re.match(pattern, assignment)

		if not match:
			continue

		base_register = match.group(1).strip()

		# Handle both [high:low] and [bit] formats
		if match.group(3):  # Range format [high:low]
			high_bit = int(match.group(2))
			low_bit = int(match.group(3))
		else:  # Single bit format [bit]
			high_bit = low_bit = int(match.group(2))

		# Ensure high_bit >= low_bit
		if high_bit < low_bit:
			high_bit, low_bit = low_bit, high_bit

		value_str = match.group(4).strip()
		# Convert value to integer (handles 0x prefix automatically)
		value = int(value_str, 0)

		# Initialize register entry if not exists
		if base_register not in register_map:
			register_map[base_register] = 0  # Start with all bits at 0

		# Create a mask for the bit range and shift the value
		bit_count = high_bit - low_bit + 1
		mask = (1 << bit_count) - 1  # Create mask of appropriate width
		masked_value = value & mask  # Ensure value fits in the bit range

		# Clear the bits in the register and set the new value
		clear_mask = ~(mask << low_bit) & ((1 << reg_width) - 1)
		register_map[base_register] = (register_map[base_register] & clear_mask) | (masked_value << low_bit)

	# Build the result list of complete register assignments
	result = []
	for base_register, final_value in register_map.items():
		# Format the value with appropriate hex width
		hex_width = (reg_width + 3) // 4  # Number of hex digits needed
		result.append(f"{base_register} = 0x{final_value:0{hex_width}x}")

	return result

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
