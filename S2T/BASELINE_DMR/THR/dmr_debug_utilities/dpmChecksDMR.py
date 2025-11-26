# DPM debug tools
# Developer: gaespino
# Update: 8/2/2024
# Version: 0.01 
# Last Update notes: Added the pseudo bs capabilities to use Custom Masks, set htdis = False if none pseudo content is being used.
# Any issues please contact gabriel.espinoza.ballestero@intel.com



import time
import csv
import os, sys
# import ipccli
# import namednodes
# import pandas as pd
# import getpass
from tabulate import tabulate
from openpyxl import load_workbook
import re
import toolext.bootscript.boot as b
import json
import DMRFuseOverride as f

#ipc = ipccli.baseaccess()

# site = "amr.corp.intel.com"
# scriptpath = "ec\\proj\\mdl\\cr\\intel\\engineering\\dev\\team_ftw\\jfnavarr\\Scripts\\Automate_TileView_Results_GNR"
# tileviewPath = f"\\\\{site}\\{scriptpath}"
# 
# sys.path.append(tileviewPath)
# import tileview_results as dpmtileview

verbose = False
sv = None
ipc = None
debug= True

## Instance Initiator - Can be optimized but it works for now, used to simplify code a bit
class CWFPySV():
	from namednodes import sv
	
	"""
	Class constructor for CWF PythonSV path creation.
	"""
	def __init__(self, tiles=[0], PathTemplates = ["uncore.ra"],instances=["ra22","ra18"], preTilePath="socket", die="cbb0", checktype = "current_vcri"):

		self._instances = []
		self.readcheck = checktype
		# All tiles
		for tile in tiles:
			self._socket = sv.get_by_path("{0}{1}.{2}".format(preTilePath,tile,die))
			for template in PathTemplates:
				for i in instances:
					try:
						self._instances.append(self._socket.get_by_path("{0}.{1}".format(template,i)))
					except:
						print(f"PythonSV instance {i} cannot be read, skipping")
		
		# Perform a check on all the instances, if there is a non readable one, remove it 
		if checktype != "": 
			self.instancechk()

	def instancechk(self):
		
		for _instance in self._instances:
			try:
				read_check = _instance.get_by_path("{}".format(self.readcheck))
				#print(read_check.path)
				read_check.read()
			except:
				print(f"instance {_instance.path} cannot be read, removing it")
				self._instances.remove(_instance)
				

## CFC Voltage/Ratio values and VF Curve data
class cfc():
	# Not changed from GNR
	def __init__(self, dies = ["all"], regs = "all", sktnum = [0], fuse_ram = True):
		self.sv = _get_global_sv()			
		#self.ipc = ipccli.baseaccess()
		
		self.regs = regs
		self.sktnum = sktnum
		self.fuse_ram = fuse_ram
		
		if "all" in dies:
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
		mesh_inst = ["pcodeio_map"]
		meshcv = "io_wp_rc_cv_ps_0"

		# Check for arguments in reg key
		valid_regs = {	"fuses":{"fuses": True, 	"cv":False}, 
						"cv": 	{"fuses": False, 	"cv":True}, 
						"all":	{"fuses": True, 	"cv":True}}
		
		if regs not in valid_regs.keys():
			print ("No valid register selection to be read, valid options are: \n" +
				   "fuses:	Reads all fused data configured for CFC Ratios. \n" +
				   "cv: 	Reads current mesh value for CFC ratios. \n" +
				   "all: 	Reads fuses and current values for CFC ratios. (default) "  )
			sys.exit()
		
		regfuse = valid_regs[regs]["fuses"]
		regcv = valid_regs[regs]["cv"]

		# Read all fuses first
		if fuse_ram and regfuse:
			sv.sockets.computes.fuses.load_fuse_ram()
			sv.sockets.ios.fuses.load_fuse_ram()
		
		curves = {	"cfc_curve": ["pcode_cfc_vf_voltage_point0","pcode_cfc_vf_voltage_point1","pcode_cfc_vf_voltage_point2","pcode_cfc_vf_voltage_point3","pcode_cfc_vf_voltage_point4","pcode_cfc_vf_voltage_point5"],
					#"hdc_curve": ["pcode_hdc_vf_voltage_point0","pcode_hdc_vf_voltage_point1","pcode_hdc_vf_voltage_point2","pcode_hdc_vf_voltage_point3","pcode_hdc_vf_voltage_point4","pcode_hdc_vf_voltage_point5"],
					"hdc_curve": ["pcode_l2_vf_ratio_point0","pcode_l2_vf_ratio_point1","pcode_l2_vf_ratio_point2","pcode_l2_vf_ratio_point3","pcode_l2_vf_ratio_point4","pcode_l2_vf_ratio_point5"],
				}

		for die in dies:
			
			if re.search(r"io*", die): 
				instance = ["punit_iosf_sb"]
				
			elif re.search(r"compute*", die): 
				instance = ["pcu"]
			else:
				print(f"Not valid die selected {die}: Skipping...")
				continue
			#print (f"\n### {str(die).upper()}  - CFC Voltages fused values ###")
			die_inst = CWFPySV(tiles=sktnum, PathTemplates = ["fuses"],instances=instance, preTilePath="socket",die=die, checktype = "pcode_cfc_min_ratio")
			mesh_val = CWFPySV(tiles=sktnum, PathTemplates = ["uncore"],instances=mesh_inst, preTilePath="socket",die=die, checktype = meshcv)
			
			if regfuse:
				for fuse in die_inst._instances:
					# CFC VF fuses (VOLTAGE)

					for curve in curves["cfc_curve"]:
						pointvalue = fuse.readregister(curve)
						printData(data_cfc, curve, die, hex(pointvalue))

					if re.search(r"compute*", die):
						# HDC VF fuses (VOLTAGE)

						for curve in curves["hdc_curve"]:
							pointvalue = fuse.readregister(curve)
							printData(data_hdc, curve, die, hex(pointvalue))

			if regcv:
				# Mesh current value / Add some extra code for the hdc read, this one can be checked directly from the RA
				for mesh in mesh_val._instances:

					meshvalue = mesh.io_wp_rc_cv_ps_0.readfield("voltage")
					printData(data_read, "io_wp_rc_cv_ps_0.voltage", die, hex(meshvalue))

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
		mesh_inst = ["pcodeio_map"]
		meshcv = "io_wp_rc_cv_ps_0"

		#Check for arguemnts in reg key
		valid_regs = {	"fuses":{"fuses": True, 	"cv":False}, 
						"cv": 	{"fuses": False, 	"cv":True}, 
						"all":	{"fuses": True, 	"cv":True}}
		
		if regs not in valid_regs.keys():
			print ("No valid register selection to be read, valid options are: \n" +
				   "fuses:	Reads all fused data configured for CFC Ratios. \n" +
				   "cv: 	Reads current mesh value for CFC ratios. \n" +
				   "all: 	Reads fuses and current values for CFC ratios. (default) "  )
			sys.exit()
		
		regfuse = valid_regs[regs]["fuses"]
		regcv = valid_regs[regs]["cv"]
		
		# Read all fuses first
		if fuse_ram and regfuse:
			sv.sockets.computes.fuses.load_fuse_ram()
			sv.sockets.ios.fuses.load_fuse_ram()
		
		curves = {	"cfc_curve": ["pcode_cfc_vf_ratio_point0","pcode_cfc_vf_ratio_point1","pcode_cfc_vf_ratio_point2","pcode_cfc_vf_ratio_point3","pcode_cfc_vf_ratio_point4","pcode_cfc_vf_ratio_point5"],
					"hdc_curve": ["pcode_l2_vf_ratio_point0","pcode_l2_vf_ratio_point1","pcode_l2_vf_ratio_point2","pcode_l2_vf_ratio_point3","pcode_l2_vf_ratio_point4","pcode_l2_vf_ratio_point5"],
					"pstates" : {	"p0":"pcode_sst_pp_0_cfc_p0_ratio", 
									"p1":"pcode_sst_pp_0_cfc_p1_ratio", 
									"pn":"pcode_cfc_pn_ratio", 
									"min":"pcode_cfc_min_ratio"}
				}

		for die in dies:
			
			if re.search(r"io*", die): 
				instance = ["punit_iosf_sb"]
				
			elif re.search(r"compute*", die): 
				instance = ["pcu"]
			else:
				print(f"Not valid die selected {die}: Skipping...")
				continue
			#print (f"\n### {str(die).upper()}  - CFC Ratios fused values ###")
			die_inst = CWFPySV(tiles=sktnum, PathTemplates = ["fuses"],instances=instance, preTilePath="socket",die=die, checktype = "pcode_cfc_min_ratio")
			mesh_val = CWFPySV(tiles=sktnum, PathTemplates = ["uncore"],instances=mesh_inst, preTilePath="socket",die=die, checktype = meshcv)
			
			if regfuse:
				for fuse in die_inst._instances:
					# CFC VF fuses (RATIO)

					for curve in curves["cfc_curve"]:
						pointvalue = fuse.readregister(curve)
						printData(data_cfc, curve, die, hex(pointvalue))

					if re.search(r"compute*", die):
						# HDC VF fuses (RATIO)

						for curve in curves["hdc_curve"]:
							pointvalue = fuse.readregister(curve)
							printData(data_hdc, curve, die, hex(pointvalue))

					# CFC Pstate fuses (RATIO)
					for pstate in curves["pstates"].keys():
						pstatevalue = fuse.readregister(curves["pstates"][pstate])
						printData(data_pstates, pstate, die, hex(pstatevalue))
			
			if regcv:
				# Mesh current value
				for mesh in mesh_val._instances:

					meshvalue = mesh.io_wp_rc_cv_ps_0.readfield("ratio")
					printData(data_read, "io_wp_rc_cv_ps_0.ratio", die, hex(meshvalue))

		if regfuse:
			printTable(data_cfc, "CFC VF fuses (RATIO)")
			printTable(data_hdc, "HDC VF fuses (RATIO)")
			printTable(data_pstates, "Pstates Values (RATIO)")
		if regcv:
			printTable(data_read, "Ratios Current Values (MESH)")

	#def curves(self)

#Aqui va el de class ia
class ia():
	
	def __init__(self, dies = ["all"], regs = "all", sktnum = [0], fuse_ram = True):
		#self.sv = _get_global_sv()			
		#self.ipc = ipccli.baseaccess()
		
		self.regs = regs
		self.sktnum = sktnum
		self.fuse_ram = fuse_ram
		
		if "all" in dies:
			_die = sv.socket0.target_info["segment"].lower()
			dies = sv.socket0.computes.name
			#if _die == "gnrap":
			#	dies = ["compute0", "compute1", "compute2"]
			#elif _die == "gnrsp":
			#	dies = ["compute0", "compute1"]
		
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
		mesh_inst = ["pcodeio_map"]
		meshcv = "io_wp_ia_cv_ps_0"
		
		# Curves defaults
		pp = 0
		idx = 0
		ratio = 0
		
		# Enumerate all the variables needed for power curves	
		ppfs = [0,1,2,3,4]
		idxs = [0,1,2,3,4,5]
		vfidxs = [0,1,2,3]
		ratios = [0,1,2,3,4,5,6,7]
		search_string = ["profile", "idx", "ratio"] # Not used


		valid_regs = {	"fuses":{"fuses": True, 	"cv":False}, 
						"cv": 	{"fuses": False, 	"cv":True}, 
						"all":	{"fuses": True, 	"cv":True}}

		if regs not in valid_regs.keys():
			print ("No valid register selection to be read, valid options are: \n" +
				   "fuses:	Reads all fused data configured for IA Ratios. \n" +
				   "cv: 	Reads current mesh value for IA ratios. \n" +
				   "all: 	Reads fuses and current values for IA ratios. (default) "  )
			sys.exit()
		
		regfuse = valid_regs[regs]["fuses"]
		regcv = valid_regs[regs]["cv"]	
		
		# Read all fuses first
		if fuse_ram and regfuse:
			sv.sockets.computes.fuses.load_fuse_ram()
			sv.sockets.ios.fuses.load_fuse_ram()

		#Steven - aqui creo que iria solo la curva de SSE? averiguar con SRF
		"""
		curves = {	"limits": [f"pcode_sst_pp_##profile##_turbo_ratio_limit_ratios_cdyn_index##idx##_ratio##ratio##"],
					"p1": [f"pcode_sst_pp_##profile##_sse_p1_ratio",f"pcode_sst_pp_##profile##_avx2_p1_ratio",f"pcode_sst_pp_##profile##_avx512_p1_ratio",f"pcode_sst_pp_##profile##_amx_p1_ratio"],
					"vf_curve": ["pcode_ia_vf_ratio_voltage_index##idx##_ratio_point0","pcode_ia_vf_ratio_voltage_index##idx##_ratio_point1","pcode_ia_vf_ratio_voltage_index##idx##_ratio_point2","pcode_ia_vf_ratio_voltage_index##idx##_ratio_point3","pcode_ia_vf_ratio_voltage_index##idx##_ratio_point4","pcode_ia_vf_ratio_voltage_index##idx##_ratio_point5"],
					"pstates" : {	"p0":"pcode_ia_p0_ratio", 
									"pn":"pcode_ia_pn_ratio", 
									"min":"pcode_ia_min_ratio",
								}
				}
		"""
		#David - solo SSE license se usa, AVX no
		curves = {	"limits": ["pcode_sst_pp_##profile##_turbo_ratio_limit_ratios_cdyn_index##idx##_ratio##ratio##"],
					"p1": ["pcode_sst_pp_##profile##_sse_p1_ratio"],
					"vf_curve": ["pcode_ia_vf_ratio_voltage_index##idx##_ratio_point0","pcode_ia_vf_ratio_voltage_index##idx##_ratio_point1","pcode_ia_vf_ratio_voltage_index##idx##_ratio_point2","pcode_ia_vf_ratio_voltage_index##idx##_ratio_point3","pcode_ia_vf_ratio_voltage_index##idx##_ratio_point4","pcode_ia_vf_ratio_voltage_index##idx##_ratio_point5"],
					"pstates" : {	"p0":"pcode_ia_p0_ratio", 
									"pn":"pcode_ia_pn_ratio", 
									"min":"pcode_ia_min_ratio",
								}
				}

		#if "all" in dies:
		#	dies = ["compute0", "compute1", "compute2"]

		for die in dies:

			if re.search(r"compute*", die): 
				instance = ["pcu"]
			else:
				print(f"Not valid die selected {die}: Skipping...")
				continue
			#print (f"\n### {str(die).upper()}  - IA Ratios fused values ###")
			die_inst = CWFPySV(tiles=sktnum, PathTemplates = ["fuses"],instances=instance, preTilePath="socket",die=die, checktype = "pcode_ia_min_ratio")
			mesh_val = CWFPySV(tiles=sktnum, PathTemplates = ["uncore"],instances=mesh_inst, preTilePath="socket",die=die, checktype = meshcv)
			
			## Dumps all fuse data if option is selected
			if regfuse:
				for fuse in die_inst._instances:
					
					# Limit fuses (RATIO)
					for curve in curves["limits"]:
						for pp in ppfs:
							for idx in idxs:
								for ratio in ratios:
									new_curve = curve
									
									#for _search in search_string:
									new_curve = new_curve.replace("##profile##",str(pp))
									new_curve = new_curve.replace("##idx##",str(idx))
									new_curve = new_curve.replace("##ratio##",str(ratio))
									
									pointvalue = fuse.readregister(new_curve)
									printData(data_limits, new_curve, die, hex(pointvalue))
									#print(f"{new_curve} = {pointvalue}")
					
					# VF curve ratio values
					for idx in vfidxs:
						for curve in curves["vf_curve"]:

							new_curve = curve
							new_curve = new_curve.replace("##idx##",str(idx))
							pointvalue = fuse.readregister(new_curve)
							printData(data_vf, new_curve, die, hex(pointvalue))

					# P1 fuses (RATIO)
					for curve in curves["p1"]:
						for pp in ppfs:
							new_curve = curve
							new_curve = new_curve.replace("##profile##",str(pp))
							pointvalue = fuse.readregister(new_curve)
							#print(f"{new_curve} = {pointvalue}")
							printData(data_p1, new_curve, die, hex(pointvalue))

					# CFC Pstate fuses (RATIO)
					for pstate in curves["pstates"].keys():
						pstatevalue = fuse.readregister(curves["pstates"][pstate])
						#print(f"{pstate} = {pstatevalue}")
						printData(data_pstates, pstate, die, hex(pstatevalue))

			
			# Dumps current core ratio valus if option is selected
			if regcv:
				for mesh in mesh_val._instances:

					for core in range(64):
						svregister = f"io_wp_ia_cv_ps_{core}"
						meshvalue = mesh.readregister(svregister).readfield("ratio")
						printData(data_read, f"{svregister}.ratio", die, hex(meshvalue))
					#print(f"{meshcv}.ratio = {hex(meshvalue)}")
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
		mesh_inst = ["pcodeio_map"]
		meshcv = "io_wp_ia_cv_ps_0"
		
		# Curves defaults
		pp = 0
		idx = 0
		ratio = 0
		
		# Enumerate all the variables needed for power curves	
		
		idxs = [0,1,2,3]
		vcurves = [0,1,2,3,4,5,6,7,8,9,10,11]
		search_string = ["profile", "idx", "ratio"] # Not used


		valid_regs = {	"fuses":{"fuses": True, 	"cv":False}, 
						"cv": 	{"fuses": False, 	"cv":True}, 
						"all":	{"fuses": True, 	"cv":True}}

		if regs not in valid_regs.keys():
			print ("No valid register selection to be read, valid options are: \n" +
				   "fuses:	Reads all fused data configured for IA Ratios. \n" +
				   "cv: 	Reads current mesh value for IA ratios. \n" +
				   "all: 	Reads fuses and current values for IA ratios. (default) "  )
			sys.exit()
		
		regfuse = valid_regs[regs]["fuses"]
		regcv = valid_regs[regs]["cv"]	
		
		# Read all fuses first
		if fuse_ram and regfuse:
			sv.sockets.computes.fuses.load_fuse_ram()
			sv.sockets.ios.fuses.load_fuse_ram()

		curves = {	"vf_curve": ["pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point0","pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point1","pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point2","pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point3","pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point4","pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point5"],
				}

		#if "all" in dies:
		#	dies = ["compute0", "compute1", "compute2"]

		for die in dies:

			if re.search(r"compute*", die): 
				instance = ["pcu"]
			else:
				print(f"Not valid die selected {die}: Skipping...")
				continue
			#print (f"\n### {str(die).upper()}  - IA Ratios fused values ###")
			die_inst = CWFPySV(tiles=sktnum, PathTemplates = ["fuses"],instances=instance, preTilePath="socket",die=die, checktype = "pcode_ia_min_ratio")
			mesh_val = CWFPySV(tiles=sktnum, PathTemplates = ["uncore"],instances=mesh_inst, preTilePath="socket",die=die, checktype = meshcv)
			
			## Dumps all fuse data if option is selected
			if regfuse:
				for fuse in die_inst._instances:

					# VF curve voltage values
					for vcurve in vcurves:
						for idx in idxs:
							for curve in curves["vf_curve"]:
								new_curve = curve
								new_curve = new_curve.replace("##curve##",str(vcurve))
								new_curve = new_curve.replace("##idx##",str(idx))
								pointvalue = fuse.readregister(new_curve)
								printData(data_vf, new_curve, die, hex(pointvalue))
			
			# Dumps current core voltage valus if option is selected
			if regcv:
				for mesh in mesh_val._instances:

					for core in range(64):
						svregister = f"io_wp_ia_cv_ps_{core}"
						meshvalue = mesh.readregister(svregister).readfield("voltage")
						printData(data_read, f"{svregister}.voltage", die, hex(meshvalue))
					#print(f"{meshcv}.ratio = {hex(meshvalue)}")
		if regfuse:

			printTable(data_vf, "IA VF Curve Values (VOLTAGE)")
		if regcv:
			printTable(data_read, "IA Voltage Current Values")

def tileview(test="", chkmem = 0, debug_mca = 0, folder="C:\\temp\\"):
	#gcm.svStatus()
	#dpmtileview.run(test, chkmem, debug_mca, folder)
	pass

## BIOS Knobs edit for bootscript usage
def bsknobs(readonly = False, skipinit = False):
	import pysvtools.xmlcli.nvram as nvram
	import ipccli
	ipc = ipccli.baseaccess()
	ram = nvram.getNVRAM()
	#if not skipinit: gcm.svStatus()
	#knobs = {"DfxS3mSoftStrap":0, "DfxSkipWarmResetPromotion":1}
	print(">>> Checking BIOS configuration knobs: DfxS3mSoftStrap, DfxSkipWarmResetPromotion, DwrEnable and IerrResetEnabled <<< ")
	#biosknobs(knobs=knobs, readonly=False)

	try:
		
		ram.pull()
		print(" -- BIOS Knob Data collected -- ")
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
				print(f"> DfxS3mSoftStrap {Softstrap_val} value not Disabled, needs to be changed < ")
			else:
				print(f"> DfxS3mSoftStrap {Sofstrap_str} changing it to Disable < ")
				ram.DfxS3mSoftStrap = 0
			change = True

		if SkipWarmResetPromotion_val != 2:
			if readonly:
				print(f"> DfxSkipWarmResetPromotion {SkipWarmResetPromotion_str} value not Auto, needs to be changed < ")
			else:
				print(f"> DfxSkipWarmResetPromotion {SkipWarmResetPromotion_str} changing it to Auto < ")
				ram.DfxSkipWarmResetPromotion = 2
			change = True

		if DwrEnable_val != 1:
			if readonly:
				print(f"> DwrEnable {DwrEnable_str} value not Enabled, needs to be changed < ")
			else:
				print(f"> DwrEnable {DwrEnable_str} changing it to Enabled < ")
				ram.DwrEnable = 1
			change = True

		if IerrResetEnabled_val != 0:
			if readonly:
				print(f"> IerrResetEnabled {IerrResetEnabled_val} value not Disabled, needs to be changed < ")
			else:
				print(f"> IerrResetEnabled {IerrResetEnabled_str} changing it to Disable < ")
				ram.IerrResetEnabled = 0
			change = True

		if change:
			if readonly:
				print(">>> Issues with BIOS Knobs, update the knobs to avoid issues during boot...  ")
			else:
				print(">>> Updating data into BIOS nvram...  ")
				ram.push()
				print(f">>> Bios Updated with SoftStrap: {Sofstrap_str} and SkipWarmResetPromotion: {SkipWarmResetPromotion_str} <<< ")
				print(f">>> Bios Updated with IerrResetEnabled: {IerrResetEnabled_str} and DwrEnable: {DwrEnable_str}  <<< ")
		else:
			print(f">>> Bios properly set with SoftStrap: {Sofstrap_str} and SkipWarmResetPromotion: {SkipWarmResetPromotion_str} <<< ")
			print(f">>> Bios properly set with IerrResetEnabled: {IerrResetEnabled_str} and DwrEnable: {DwrEnable_str}  <<< ")

	except:
		print(">>> Error pulling/updating data from/to NVRAM, try again or use PYFIT to edit and check your bios")
		print(r">>> PYFIT script: C:\PythonSV\graniterapids\users\kwadams\staging\pyfit")
		print("> For proper Bootscript usage the following knobs needs to be configured as follow:")
		print("> DfxS3mSoftStrap = 'Disable'")
		print("> DfxSkipWarmResetPromotion = 'Auto'>")
		print("> IerrResetEnabled = 'Disable'>")
		print("> DwrEnable = 'Enabled'>")

## BIOS Knobs edit use key for knob and set the desired value	
def biosknobs(knobs = {}, readonly=False):
	import pysvtools.xmlcli.nvram as nvram
	import ipccli
	ipc = ipccli.baseaccess()
	ram = nvram.getNVRAM()
	#gcm.svStatus()

	try:
		ram.pull()
		print(" -- BIOS Knob Data collected -- ")
		change = False

		for k, v in knobs.items():

			if ram.searchNames(name=k, exact=True):
				cv = ram.getByName(k)
				if readonly:
					print(f" -- Bios knob value --- {k} : {cv.getString()} ")
				else:
					if v!= cv.getValue():
						ram.setByName(k,v)
						print(f" -- Bios knob {k} changed from: {cv.getValue()} --> {v} ")
						change = True
					else:
						print(f" -- Bios knob {k} value already set at requested value. {cv.getString()} --> {cv.getValue()}:{v} ")

			else:
				print(f" -- Bios knob {k} not found ")
			
			if change: ram.pull()
			if readonly: return ram
		
	
	except:
		print(" -- Error pulling/updating data from/to NVRAM, try again or use PYFIT to edit and your bios")

## ROM to RAM update for fuses checks
def fuseRAM(refresh = False):
	#sv = _get_global_sv()
	#if refresh: gcm.svStatus()
	print ("Loading fuse data from ROM to RAM .... ")
	sv.sockets.computes.fuses.load_fuse_ram()
	sv.sockets.ios.fuses.load_fuse_ram()


## Uses USB Splitter controller to power cycle the unit
def powercycle(stime = 10, ports = None):
	import toolext.bootscript.toolbox.power_control.USBPowerSplitterFullControl as pwsc

	print("Power cycling the unit using USB...")
	usb = pwsc.USBPowerSplitter()
	usb.all_powerCycle(_stime = stime, _ports = ports)

## Tool for fuse checking of the unit
def fuses(rdFuses=True, sktnum=[0]):
	sv = _get_global_sv()
	_fuse_instance = ["hwrs_top_late"]
	
	imhs = []
	imhs.extend(sv.socket0.imhs.name)

	cbbs = []
	cbbs.extend(sv.socket0.cbbs)

	_masks = {value: {"ia":None,"llc":None} for value in imhs}
	_llcmasks = {value: {"ia":None,"llc":None} for value in imhs}

	if rdFuses:
		print ("Loading fuse data from RAM to update Mask info")
		sv.sockets.cbbs.computes.fuses.load_fuse_ram()
		sv.sockets.imhs.fuses.load_fuse_ram()
	# for imh in imhs:
	# 	_fuse = CWFPySV(tiles=sktnum, PathTemplates = ["fuses"],instances=_fuse_instance, preTilePath="socket", die=imh, checktype = "")
	# 	for fuse in _fuse._instances:
	# 		_masks[imh]["ia"] = fuse.ip_disable_fuses_dword6_core_disable.get_value()
	# 		_llcmasks[imh]["llc"] = fuse.ip_disable_fuses_dword2_llc_disable.get_value()

	masks = {}

	for cbb in cbbs:
		cbb_name = cbb.name 
		# if cbb == "cbb0":
		masks[f"ia_{cbb_name}"] =  cbb.base.fuses.punit_fuses.fw_fuses_sst_pp_0_module_disable_mask
		masks[f"llc_{cbb_name}"] = cbb.base.fuses.punit_fuses.fw_fuses_llc_slice_ia_ccp_dis
		# if cbb == "cbb1":
		# 	masks[f"ia_{cbb}"] = _masks["imh0"]["ia"] >> 32
		# 	masks[f"llc_{cbb}"] = sv.socket0.cbb1.base.fuses.punit_fuses.fw_fuses_llc_slice_ia_ccp_dis.get_value()
		# if cbb == "cbb2":
		# 	masks[f"ia_{cbb}"] = _masks["imh1"]["ia"] & 0xFFFFFFFF
		# 	masks[f"llc_{cbb}"] = sv.socket0.cbb2.base.fuses.punit_fuses.fw_fuses_llc_slice_ia_ccp_dis.get_value()
		# if cbb == "cbb3":
		# 	masks[f"ia_{cbb}"] = _masks["imh1"]["ia"] >> 32
		# 	masks[f"llc_{cbb}"] = _llcmasks["imh1"]["llc"] >> 32
		# if cbb == "cbb0":
		# 	masks[f"ia_{cbb}"] = _masks["imh0"]["ia"] & 0xFFFFFFFF
		# 	masks[f"llc_{cbb}"] = _llcmasks["imh0"]["llc"] & 0xFFFFFFFF
		# if cbb == "cbb1":
		# 	masks[f"ia_{cbb}"] = _masks["imh0"]["ia"] >> 32
		# 	masks[f"llc_{cbb}"] = _llcmasks["imh0"]["llc"] >> 32
		# if cbb == "cbb2":
		# 	masks[f"ia_{cbb}"] = _masks["imh1"]["ia"] & 0xFFFFFFFF
		# 	masks[f"llc_{cbb}"] = _llcmasks["imh1"]["llc"] & 0xFFFFFFFF
		# if cbb == "cbb3":
		# 	masks[f"ia_{cbb}"] = _masks["imh1"]["ia"] >> 32
		# 	masks[f"llc_{cbb}"] = _llcmasks["imh1"]["llc"] >> 32

	if rdFuses:		
		print (f"\t Masks \n {masks}")
	
	return masks

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
		for core_n in range (0,7):
			fuse += [f"fuses.core{core_n}_fuse.core_fuse_core_fuse_pma_lp_enable={dis:#x}"]
	else:
		for core_n in range (0,7):
			fuse += [f"sv.socket0.cbbs.computes.fuses.core{core_n}_fuse.core_fuse_core_fuse_pma_lp_enable={dis}"]
		# fuse = [f"sv.socket0.computes.fuses.pcu.pcode_lp_disable={dis}"]
	return fuse

def getChipConfig():
	from namednodes import sv
	number_of_cbbs = len(sv.socket0.cbbs.names)
	
	if number_of_cbbs == 4:
		return 'X4'

	return 'X1'

def gen_product_bootstring(bootopt = '', compute_config = 'X1', b_extra = '', _boot_disable_ia = '', _boot_disable_llc ='',fuse_string ='', fuse_files = '') -> str:
 
    # Future Releases will call a product_specific function here,
    chip = getChipConfig()
 
    if chip == 'SP':
        #_boot_string = f'{bootopt}(fused_unit=True, enable_strap_checks=False, compute_config="{compute_cofig}", segment="{segment}", enable_pm=True {b_extra}, {_boot_disable_ia} {_boot_disable_llc} {fuse_string} fuse_files_compute=[{_fuse_files_compute}], fuse_files_io=[{_fuse_files_io}])'
        _boot_string = f'{bootopt}(fused_unit=True, enable_strap_checks=False, compute_config="{compute_config}", enable_pm=True {b_extra},{_boot_disable_ia}{_boot_disable_llc}{fuse_string}{fuse_files})'
 
        #_boot_string = ('%s(fused_unit=False, pwrgoodmethod="usb", compute_config="%s", ia_core_disable={%s}, llc_slice_disable={%s}, fuse_str={"cbb_base":%s, "imh":%s})') % (bootopt, product[die]['compute_config'], _boot_disable_ia, _boot_disable_llc, _fuse_str_cbb, _fuse_str_imh)
 
        #_boot_string = ('%s(fused_unit=True, enable_strap_checks=False,enable_pm=True %s, %s %s %s fuse_files_compute=[%s], fuse_files_io=[%s])') % (bootopt, b_extra, _boot_disable_ia, _boot_disable_llc, fuse_string,_fuse_files_compute, _fuse_files_io)
   
    else:
        #_boot_string = f'{bootopt}(fused_unit=True, enable_strap_checks=False, compute_config="{compute_cofig}", segment="{segment}", enable_pm=True {b_extra}, {_boot_disable_ia} {_boot_disable_llc} {fuse_string} fuse_files_compute=[{_fuse_files_compute}], fuse_files_io=[{_fuse_files_io}])'
        _boot_string = f'{bootopt}(fused_unit=True, enable_strap_checks=False, compute_config="{compute_config}", enable_pm=True {b_extra},{_boot_disable_ia}{_boot_disable_llc}{fuse_string}{fuse_files})'
        #_boot_string = ('%s(fused_unit=True, enable_strap_checks=False,compute_config="%s",enable_pm=True,segment="%s" %s, %s %s %s fuse_files_compute=[%s], fuse_files_io=[%s])') % (bootopt, compute_cofig, segment, b_extra, _boot_disable_ia, _boot_disable_llc,fuse_string,_fuse_files_compute, _fuse_files_io)
 
    return _boot_string



def pseudo_bs(ClassMask = 'RowEvenPass', Custom = [], boot = True, use_core = False, htdis = True, dis_2CPM = None, dis_1CPM = None, fuse_read = True, s2t = False, masks = None, clusterCheck = None, lsb = False, fuse_cbb =None, fuse_io = None, fast =False, ppvcfuse = False, skip_init = False,  vbump = {'enabled':False, 'type':['cfc'],'offset': 0,'cbbs':['cbb0', 'cbb1', 'cbb2', 'cbb3'],'imhs':['imh0', 'imh1'],'computes':['compute0', 'compute1', 'compute2', 'compute3']}):
	#vbump = {'type':['cfc'],'offset': 0,'computes':['compute0', 'compute1', 'compute2']}
	if not skip_init: gcm.svStatus(refresh=True)
	# vbump_target = vbump['cbbs']
	vbump_type = vbump['type']
	vbump_offset = vbump['offset']
	vbump_array = {'cbb0': [],'cbb1': [],'cbb2': [], 'cbb3': [], 'imh0': [], 'imh1': []}
	ia_fuse_str_vbump_array = {'cbb0': [],'cbb1': [],'cbb2': [], 'cbb3': []}
	ppvc_config = {	'cbb0':[],
			   		'cbb1':[],
					'cbb2':[],
					'cbb3':[],
					'io0':[],
					'io1':[],}
	cfc_array = []
	io_array = []
	ia_array = []
	
	# Init fuse string arrays
	fuse_str_0 = []
	fuse_str_1 = []
	fuse_str_2 = []

	# htdis_comp = []
	# htdis_io = []
	dis_2CPM_cbb = []

	# vbump_enabled = vbump['enabled']

	#sv = _get_global_sv()
	product = PRODUCT_CONFIG.lower()
	chipConfig = getChipConfig()
	
	syscbbs = sv.socket0.cbbs.name
	sysimhs = sv.socket0.imhs.name
	# if clusterCheck == None: clusterCheck = False

	## Assign Cluster values *can be taken from a pythonsv register, update later on
	# if variant == 'AP': cluster = 6
	# elif variant == 'SP': cluster = 4
	# else: cluster = 2
	
	#if product == 'gnrap':
	
	## Mask Type by default we use Class, but if Custom is used we change it to user, might remove this later on
	mType = 'Class'	
	if ClassMask == 'Custom':
		mType = 'User'
	elif ClassMask == 'External':
		mType = 'External'

	## Hyper Threading Disable fuses needed to run Dragon pseudo content
	# if htdis:
	# 	htdis_comp = ['scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_fused_ht_dis=0x1', 'pcu.capid_capid0_ht_dis_fuse=0x1','pcu.pcode_lp_disable=0x2','pcu.capid_capid0_max_lp_en=0x1']
	# 	htdis_io = ['punit_iosf_sb.soc_capid_capid0_max_lp_en=0x1','punit_iosf_sb.soc_capid_capid0_ht_dis_fuse=0x1']

	if dis_1CPM != None:
		dis_1CPM_cbb = fuses_dis_1CPM(dis_1CPM, bsformat = True)

	#External fuses added for BurnIn script use
	if fuse_cbb == None: fuse_cbb = []
	if fuse_io == None: fuse_io = []
	
	## Init Variables and default arrays
	ValidClass = ['RowEvenPass', 'RowOddPass', 'ColumnEvenPass', 'ColumnOddPass']
	ValidRows = ['ROW0','ROW1','ROW2','ROW3','ROW4','ROW5','ROW6','ROW7']
	ValidCols = ['COL0','COL1','COL2','COL3']
	ValidCustom = ValidRows + ValidCols
	Fmask = '0xffffffff'
	CompareMask = 	{		'Custom':	{'core_cbb_0':Fmask,'core_cbb_1':Fmask,'core_cbb_2':Fmask,'core_cbb_3':Fmask,'llc_cbb_0':Fmask,'llc_cbb_1':Fmask,'llc_cbb_2':Fmask,'llc_cbb_3':Fmask},
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
	Class_help = {	'RowEvenPass': 'Booting only with Rows 0, 2, 4 and 6',
					'RowOddPass': 'Booting only with Rows 1, 3, 5, and 7',
					'ColumnEvenPass': 'Booting only with Columns 0 and 2',
					'ColumnOddPass': 'Booting only with Columns 1 and 3',
					'Custom' : 'Booting with user mix & match configuration, Cols or Rows',
					'External' : 'Use configuration from file .\\ConfigFiles\\DMRMasksDebug.json'
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
			print(f'>>> Using external Debug Mask found in file ../ConfigFiles/DMRMasksDebug.json')
		else:			
			print(f'>>> Not a valid ClassMask selected use: RowEvenPass, RowOddPass, ColumnEvenPass, ColumnOddPass')
			sys.exit()
	
	## Checks for system masks, either external input or checking current system values
			
	if masks == None: origMask = fuses(rdFuses = fuse_read)
	else: origMask = masks

	## Custom Mask Build - Will add a Core count at the end to validate if pseudo can be used...
	if ClassMask == 'Custom':
	

		for _CustomVal in Custom:
			CustomVal = _CustomVal.upper()
			Loop_mask = pseudomask(combine = use_core, boot = True, Type = mType, ext_mask = origMask)
			
			CompareMask['Custom']['core_cbb_0'] = hex(int(Loop_mask[CustomVal]['core_cbb_0'],16) & int(CompareMask['Custom']['core_cbb_0'],16))
			if chipConfig == 'X4': 
				CompareMask['Custom']['core_cbb_1'] = hex(int(Loop_mask[CustomVal]['core_cbb_1'],16) & int(CompareMask['Custom']['core_cbb_1'],16))
				CompareMask['Custom']['core_cbb_2'] = hex(int(Loop_mask[CustomVal]['core_cbb_2'],16) & int(CompareMask['Custom']['core_cbb_2'],16))
				CompareMask['Custom']['core_cbb_3'] = hex(int(Loop_mask[CustomVal]['core_cbb_3'],16) & int(CompareMask['Custom']['core_cbb_3'],16))

			CompareMask['Custom']['llc_cbb_0'] = hex(int(Loop_mask[CustomVal]['llc_cbb_0'],16) & int(CompareMask['Custom']['llc_cbb_0'],16))
			if chipConfig == 'X4': 
				CompareMask['Custom']['llc_cbb_1'] = hex(int(Loop_mask[CustomVal]['llc_cbb_1'],16) & int(CompareMask['Custom']['llc_cbb_1'],16))
				CompareMask['Custom']['llc_cbb_2'] = hex(int(Loop_mask[CustomVal]['llc_cbb_2'],16) & int(CompareMask['Custom']['llc_cbb_2'],16))
				CompareMask['Custom']['llc_cbb_3'] = hex(int(Loop_mask[CustomVal]['llc_cbb_3'],16) & int(CompareMask['Custom']['llc_cbb_3'],16))
		
		Masks_test = CompareMask

	## Class Mask Build, depending on the selected option of First/Second or Third Pass
	else:
		Masks_test = pseudomask(combine = use_core, boot = True, Type = mType, ext_mask = origMask)
	

	# Masks_test, core_count, llc_count = masks_validation(masks = Masks_test, ClassMask = ClassMask, dies = syscomputes, product = product, _clusterCheck = clusterCheck, _lsb = lsb)

	core_cbb0 = Masks_test[ClassMask]['core_cbb_0']
	if chipConfig == 'X4': 
		core_cbb1 = Masks_test[ClassMask]['core_cbb_1']
		core_cbb2 = Masks_test[ClassMask]['core_cbb_2']
		core_cbb3 = Masks_test[ClassMask]['core_cbb_3']

	llc_cbb0 = Masks_test[ClassMask]['llc_cbb_0']
	if chipConfig == 'X4': 
		llc_cbb1 = Masks_test[ClassMask]['llc_cbb_1']
		llc_cbb2 = Masks_test[ClassMask]['llc_cbb_2']
		llc_cbb3 = Masks_test[ClassMask]['llc_cbb_3']


	# Voltage bumps

	if ('cfc' in vbump_type and vbump['enabled']) and not ppvcfuse:
		cfc_array_imhs = f.cfc_vbump_array(offset = vbump_offset, include_cbbs=False)
		cfc_array_cbbs = f.cfc_vbump_array(offset = vbump_offset, include_imhs=False)
		
		for vbump_targ in vbump['imhs']:
			if vbump['imhs'] != None and vbump_targ in sysimhs:
				
				imhrray = []
				print(f'>>> Splitting the array for one compute only: Target {vbump_targ}')
				for item in cfc_array_imhs:
					if vbump_targ in item:
						
						base = f'sv.socket0.{vbump_targ}.'
						fuse = item.replace(base,'')
						fuse = fuse.replace(' ','')
						print(f'> {vbump_targ} fuse --> {fuse}')
						imhrray.append(fuse)
				#computearray = bs_fuse_fix(fuse_str = computearray, bases = ['sv.sockets.computes.fuses.'])
				vbump_array[vbump_targ] = vbump_array[vbump_targ] + imhrray

		for vbump_targ in vbump['cbbs']:
			if vbump['cbbs'] != None and vbump_targ in syscbbs:
				
				cbbrray = []
				print(f'>>> Splitting the array for one compute only: Target {vbump_targ}')
				for item in cfc_array_cbbs:
					if vbump_targ in item:
						base = f'sv.socket0.{vbump_targ}.base.'
						fuse = item.replace(base,'')
						fuse = fuse.replace(' ','')
						print(f'> {vbump_targ} fuse --> {fuse}')
						cbbrray.append(fuse)
				#computearray = bs_fuse_fix(fuse_str = computearray, bases = ['sv.sockets.computes.fuses.'])
				vbump_array[vbump_targ] = vbump_array[vbump_targ] + cbbrray

	if ('ia' in vbump_type and vbump['enabled']) and not ppvcfuse:
		ia_array = f.ia_vbump_array(offset = vbump_offset)
		
		for cbb_targ in vbump['cbbs']:
			for vbump_targ in vbump['computes']:
				if cbb_targ != None and cbb_targ in syscbbs:
					base = f'sv.socket0.{cbb_targ}.{vbump_targ}.'
					cbbrray = []
					print(f'>>> Splitting the array for one compute only: Target {cbb_targ} {vbump_targ}')
					for item in ia_array:
						if vbump_targ in item:
							fuse = item.replace(base,'')
							fuse = fuse.replace(' ','')
							print(f'> {vbump_targ} fuse --> {fuse}')
							cbbrray.append(fuse)
					#computearray = bs_fuse_fix(fuse_str = computearray, bases = [f'sv.sockets.{vbump_targ}.fuses.'])
					ia_fuse_str_vbump_array[vbump_targ] = ia_fuse_str_vbump_array[vbump_targ] + cbbrray

	## WIP
	# if ('io' in vbump_type and vbump_type['enabled']) and not ppvcfuse:
	# 	cfcarray = fuses_cfc_vbumps(offset =  vbump_type['offset'], point = None, fixed_voltage = None, target_compute = None, computes = 3)
	# pending pereiras
	# if ppvcfuse:
	# 	ppvc_config = ppvc(bsformat=True)


	if not s2t:
		## Bootscript with or without htdis fuses
		if chipConfig == 'X4': 
			bscript_0 = ('pwrgoodmethod="usb", pwrgoodport=1, pwrgooddelay=30, fused_unit=True, enable_strap_checks=False,compute_config=%s,enable_pm=True, ia_core_disable={cbb_base0:%s, cbb_base1:%s, cbb_base2:%s, cbb_base3:%s}, llc_slice_disable={cbb_base0:%s, cbb_base1:%s, cbb_base2:%s, cbb_base3:%s}') % (chipConfig, core_cbb0, core_cbb1, core_cbb2, core_cbb3, llc_cbb0, llc_cbb1, llc_cbb2, llc_cbb3)
		
		elif chipConfig == 'X1':
			bscript_0 = ('pwrgoodmethod="usb", pwrgoodport=1, pwrgooddelay=30, fused_unit=True, enable_strap_checks=False,compute_config=%s,enable_pm=True, ia_core_disable={cbb_base0:%s}, llc_slice_disable={cbb_base0:%s}') % (chipConfig, core_cbb0, llc_cbb0)
		 
		## Checks for htdis option, might recode this at some point this a bit of a lazy way to do it, will also include the option to add custom fuse strings and fuse files, later on.

		fuse_str_0 = fuse_cbb + vbump_array['cbb0'] + dis_1CPM_cbb + ppvc_config['cbb0']
		if chipConfig == 'X4':  
			fuse_str_1 = fuse_cbb + vbump_array['cbb1'] + dis_1CPM_cbb + ppvc_config['cbb1']
			fuse_str_2 = fuse_cbb + vbump_array['cbb2'] + dis_1CPM_cbb + ppvc_config['cbb2']
			fuse_str_3 = fuse_cbb + vbump_array['cbb3'] + dis_1CPM_cbb + ppvc_config['cbb3']
		# fuse_io_0 = fuse_io + ppvc_config['io0']
		# fuse_io_1 = fuse_io + ppvc_config['io1']
		#bscript_1 = f", fuse_str_compute = {htdis_comp + fuse_compute},fuse_str_io = {htdis_io + fuse_io}"


		if chipConfig == 'X4':
			# bscript_1 =f", fuse_str_compute_0 = {fuse_str_0},fuse_str_compute_1 = {fuse_str_1},fuse_str_compute_2 = {fuse_str_2},fuse_str_io_0 = {fuse_io_0},fuse_str_io_1 = {fuse_io_1}"
			bscript_1 =(', fuse_str={cbb_base0:%s, cbb_base1:%s, cbb_base2:%s, cbb_base3:%s}, dynamic_fuse_inject={"top":my_method}') % (fuse_str_0, fuse_str_1, fuse_str_2, fuse_str_3)
		elif chipConfig == 'X1':
			bscript_1 =(', fuse_str={cbb_base0:%s}, dynamic_fuse_inject={"top":my_method}') % (fuse_str_0)

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
		print (f'>>>  Running Bootscript: \n') 
		print (f">>>  b.go({bscript_0}{bscript_1})")
		

		fuse_option = {'cbb0':fuse_str_0,'cbb1':fuse_str_1,'cbb2':fuse_str_2, 'cbb2':fuse_str_3}
		## Either run the bootscript or just print the bootscript string in case additional feats need to be added on it.
		# pending pereiras
		if fast:
			print (f'>>>  FastBoot option is selected - Starting Boot with Warm Reset')
			# print (f'>>>  Be aware, this only changes the CoreMasks keeping current CHA configuration') 
			# fast_fuses = []
			# fast_fuses += ["sv.socket0.compute0.fuses." + _f for _f in fuse_str_0]
			# fast_fuses += ["sv.socket0.compute1.fuses." + _f for _f in fuse_str_1]
			# fast_fuses += ["sv.socket0.compute2.fuses." + _f for _f in fuse_str_2]
			# fast_fuses += ["sv.socket0.io0.fuses." + _f for _f in fuse_io_0]
			# fast_fuses += ["sv.socket0.io1.fuses." + _f for _f in fuse_io_1]			

			# fast_fuses += gcm.mask_fuse_core_array(coremask = {'compute0':int(core_comp0,16), 'compute1':int(core_comp1,16), 'compute2':int(core_comp2,16)})

			# print (f'>>>  Fuse Configuration to be used in FastBoot\n',fast_fuses) 
			# gcm.fuse_cmd_override_reset(fuse_cmd_array=fast_fuses, skip_init=False, boot = boot, s2t=s2t)
			
			# # Waits for EFI and checks fuse application
			# # pseudo_efi_check(fuse_option)
			# gcm.coresEnabled()
			# #fast_fuses = []
		elif boot: 
			
			print (f'>>>  Boot option is selected - Starting Bootscript') 
		#	if htdis:
			if chipConfig == 'X1': b.go(pwrgoodmethod="usb", pwrgoodport=1, pwrgooddelay=30, fused_unit=True, enable_strap_checks=False,compute_config=chipConfig,enable_pm=True, ia_core_disable={"cbb_base0":core_cbb0, "cbb_base1":core_cbb1, "cbb_base2":core_cbb2, "cbb_base3":core_cbb3}, llc_slice_disable={"cbb_base0":llc_cbb0, "cbb_base1":llc_cbb1, "cbb_base2":llc_cbb2, "cbb_base3":llc_cbb3}, fuse_str={"cbb_base0":fuse_str_0, "cbb_base1":fuse_str_1, "cbb_base2":fuse_str_2, "cbb_base3":fuse_str_3})
			if chipConfig == 'X4': b.go(pwrgoodmethod='usb', pwrgoodport=1, pwrgooddelay=30, fused_unit=True, enable_strap_checks=False,compute_config=chipConfig,enable_pm=True, ia_core_disable={"cbb_base0":core_cbb0}, llc_slice_disable={"cbb_base0":llc_cbb0}, fuse_str={"cbb_base0":fuse_str_0})
			
			# Waits for EFI and checks fuse application
			# pending pereiras
			# pseudo_efi_check(fuse_option)

		else: 
			print (f'\n>>>  Boot option not selected -- Copy bootscript code  above and edit if needed to run manually') 
	else:
		# return core_count, llc_count, Masks_test
		return Masks_test
	
# pereiras, pending to add the correct regs, currently it's dummy funciton
def my_method(socket: str, die: str, fuse_override_iteration=None)->int:
	print(f"Testing")
	socket_id = int(socket)
	if 'cbb' in die:
		cbb_name = die.split('.')
		sv.sockets[socket_id].sub_components[cbb_name[0]].computes.fuses.core0_fuse.core_fuse_core_fuse_acode_ia_base_vf_voltage_0=0x8
	return 0

## Tool for converting current unit fuses to a pseudo format, considers all three CLASS fuse configurations
def pseudomask(combine = False, boot = False, Type = 'Class', ext_mask = None):
	
	sv = _get_global_sv()
	syscbbs = sv.socket0.cbbs.name
	product = PRODUCT_CONFIG.lower()
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
		
		# core_string = ''
		# imh_string = ''
		for key in ClassMask_sys.keys():
			if key not in ClassMask.keys():
				continue
			print (f'\nMasks for pseudo {key} \n')
			for cbb in syscbbs:
				cbb_N = sv.socket0.get_by_path(cbb).target_info.instance
				llc_mask = Masks_test[key][f'llc_cbb_{cbb_N}']
				ia_mask = Masks_test[key][f'core_cbb_{cbb_N}']
				
				ia_string = f'ia_core_disable_cbb_{cbb_N} = {ia_mask},'
				llc_string = f'llc_slice_disable_cbb_{cbb_N} = {llc_mask},'
				
				print (ia_string)
				print (llc_string)

			# 	core_string += ia_string
			# 	imh_string += llc_string
			# bootstring = core_string + imh_string
			# print (f"\nAdd the following to your bootscript to use the pseudo for {key} \n")
			# print (bootstring)

	else:
		## Used with the pseudo_bs function, wont print fuse data, just return the Mask values to be processed by the script
		return Masks_test
	

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


## Check Masks configured, will check if mask is compliant with cluster if option is selected
def masks_validation(masks, ClassMask, dies, product, _clusterCheck, _lsb = False):

	## Assign Cluster values *can be taken from a pythonsv register, update later on
	if product == "cwfap": cluster = 6
	elif product == "cwfsp": cluster = 4
	else: cluster = 2
	
	cores = {"compute0":60,"compute1":60,"compute2":60}
	llcs = {"compute0":60,"compute1":60,"compute2":60}
	core_count = 0
	llc_count = 0

	for compute in dies:
		dieN = compute[-1]
		cores[compute] = 60 - binary_count(masks[ClassMask][f"core_comp_{dieN}"])
		llcs[compute] = 60 - binary_count(masks[ClassMask][f"llc_comp_{dieN}"])

	min_llc = min(llcs["compute0"],llcs["compute1"],llcs["compute2"])
	if min_llc % 2 != 0:
		## Limiting to a minimum of 2 LLCs
		min_llc = max(min_llc - 1,2)

	print(f"\nRecommended LLC to be used for each Compute die = {min_llc}, to be in line with a clustering of {cluster}")
	for compute in dies:
		print(f"\tEnabled CORES/LLCs for {compute.upper()}: LLCs = {llcs[compute]} , COREs = {cores[compute]}")

	if _clusterCheck:
		print("\nChecking new mask configuration is compliant with system clustering:")
		for compute in dies:
			dieN = compute[-1]
			core_cd = masks[ClassMask][f"core_comp_{dieN}"]
			llc_cd = masks[ClassMask][f"llc_comp_{dieN}"]
			count_llc = llcs[compute]
			count_core = cores[compute]
			extras = count_llc - min_llc 
			
			if extras > 0:
				print(f" !!!  Current LLC count for compute{dieN}: LLCs = {count_llc}, not compliant with clustering required value {min_llc}, applying fix..\n")
				count_core, count_llc, llc_cd, core_cd = clusterCheck(coremask=core_cd,llcmask=llc_cd, computes = compute, llc_extra = extras, lsb = _lsb)
				masks[ClassMask][f"core_comp_{dieN}"] = core_cd
				masks[ClassMask][f"llc_comp_{dieN}"] = llc_cd
				llcs[compute] = count_llc
				cores[compute] = count_core
				print(f" !!!  Clustering fix completed for {compute.upper()}!!!\n")
	
	core_count = cores["compute0"] + cores["compute1"] + cores["compute2"]
	llc_count = llcs["compute0"] + llcs["compute1"] + llcs["compute2"]
	
	return masks, core_count, llc_count


## Checks if mask is compliant with clustering configuration for the specified product
## GNR AP - 6, GNRSP - 4
## If mask is not divisible by cluster number then it will start disabling slices at the end or start the die depending on lsb selection
def clusterCheck(coremask, llcmask, computes, llc_extra = 0, lsb = True):
	cores = 0
	llcs = 0
	computeN = computes[-1]

	#print(computes)
	print(" !!!  LLC MASK incoming: ",bin(int(llcmask,16))[2:].zfill(60))

	while llc_extra > 0:
		if llc_extra == 0:
			break
		disMask, first_zero = bit_disable(llcmask, lsb = lsb)
		#print(f"Disabling newllcmask0: {bin(disMask)}")
		newllc = int(llcmask,16) | disMask
		newcore = int(coremask,16) | disMask
		llcmask = hex(newllc)
		coremask = hex(newcore)
		
		#print(f"Disabling newllcmask1: {bin(newllc)}")
		print(f" !!!  Disabling slice: {first_zero + 60*(int(computeN))}")
		llc_extra = llc_extra - 1

	# Check llc count
	cores= 60 - binary_count(coremask)
	llcs= 60 - binary_count(llcmask)
	print(" !!!  LLC MASK outgoing: ",bin(newllc)[2:].zfill(60))

	print(f" !!!  Clustering fix new Core count = {cores}")
	print(f" !!!  Clustering fix new LLC count = {llcs}")

	return cores, llcs, llcmask, coremask


## Looks for the first bit depending on the LSB selection, if LSB will disable the lowest slice enabled else will disable the highest
def bit_disable(combineMask, lsb = True, base = 16):
	## We will check for the first enabled slice and enable it
	if type(combineMask) == str:	
		binMask = bin(int(combineMask, base))[2:].zfill(60)
	else:
		binMask = bin(combineMask)[2:].zfill(60)	
	
	if lsb: first_zero = binMask[::-1].find("0")
	else: first_zero = (len(binMask)-1) - (binMask.find("0"))

	disMask = (1 << (first_zero)) #& ((1 << 60)-1) #| combineMask

	return (disMask, first_zero)


## Below arrays uses the GNRFuseOverride script in thr folder, adding them here for ease of use
def fuses_cfc_vbumps(offset = 0, rgb_array={}, target_socket = None, skip_init=False, target_cbb=None, target_compute = None, target_core=None,  fixed_voltage = None, include_imhs=True, include_cbbs=True):
	#sv = _get_global_sv
	#sv.refresh()
	if not skip_init: fuseRAM(refresh = True)
	#computes = len(sv.socket0.computes)
	dpmarray = []
	dpmarray = f.cfc_vbump_array(offset = offset, rgb_array= rgb_array, target_socket = target_socket, target_cbb = target_cbb, target_compute = target_compute, target_core = target_core, fixed_voltage = fixed_voltage, include_cbbs=include_cbbs, include_imhs=include_imhs)
	## Temporary fix
	#if target_compute != None:
	#	computearray = []
	#	print(f'Splitting the array for one compute only: Target {target_compute}')
	#	for item in dpmarray:
	#		if target_compute in item:
	#			computearray.append(item)
	#	dpmarray = computearray
		
	return dpmarray

def fuses_ia_vbumps(offset = 0, rgb_array={}, target_socket = None, skip_init=False, target_cbb=None, target_compute = None, target_core=None,  fixed_voltage = None, include_imhs=True, include_cbbs=True):
	dpmarray = []
	dpmarray = f.ia_vbump_array(offset = offset, rgb_array= rgb_array, target_socket = target_socket, target_cbb = target_cbb, target_compute = target_compute, target_core = target_core, fixed_voltage = fixed_voltage, include_cbbs=include_cbbs, include_imhs=include_imhs)
	return dpmarray

########################################################################################################################################################################
##
## 													IPC and SV Initialization Code
##
########################################################################################################################################################################

## SV initilize		
def _get_global_sv():

	"""
	Lazy initialize for the sapphirerapids sv "socket" instance

	Return
	------
	sv: class "components.ComponentManager"
	"""
	global sv
	global ipc

	if sv is None:
		from namednodes import sv
		sv.initialize()
	if not sv.sockets:
		#Msg.print_("No socketlist detected. Restarting baseaccess and sv.refresh")
		#ipc = _get_global_ipc()
		#ipc.forcereconfig() 
		#if ipc.islocked():
			#ipc.unlock()
		#ipc.unlock()
		#ipc.uncores.unlock()
		sv.initialize()
		sv.refresh()    #determined this was needed in manual testing
	return sv

## IPC Initialize
def _get_global_ipc():
		"""
		Lazy initialize for the global IPC instance
		"""
		global ipc
		if ipc is None:
			import ipccli
			#ipc = ipccli.baseaccess()
			#ipc.forcereconfig() 
			#ipc.unlock()
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
        if response.lower() in ["yes", "no"]:
            return response.lower()
        time.sleep(1)
    print("Timeout reached. Continuing by default.")
    return None


## Data tabulate - Display data in a organized table format
def printTable(data, label = ""):
	#Convert to lists
	tblkeys = list(data.keys())
	tblvalues = list(data.values())

	# Converting the dictionary values to a list of lists
	table_data = [[k] + [v for v in tblvalues[i].values()] for i, k in enumerate(tblkeys)]

	# Printing the table
	table = tabulate(table_data, headers=["instance"] + list(tblvalues[0].keys()), tablefmt="grid")
	if label !="":
		print ("\n{}".format(label))
	print(table)


## Data modification to be used in Tabulate format (CFC/IA Ratios code)
def printData(data, curve, die, pointvalue):
	update_data = {die: pointvalue}
	try:
		data[curve].update(update_data)
	except:
		data[curve] = {die: pointvalue}
	
	return data


def dev_dict(filename, useroot = True):
	## Load Configuration json files
	configfilename = filename
	if useroot:
		file_NAME = (__file__).split("\\")[-1].rstrip()
		parent_dir =(__file__).split(file_NAME)[0] # + "S2T\\product_specific\\cwf\\"
		if debug:
			jsfile = "{}ConfigFiles\\{}".format(parent_dir, configfilename)
		else:
			jsfile = "{}\\ConfigFiles\\{}".format(parent_dir, configfilename)
	else:
		jsfile = configfilename

	# Change dbgfile to original
	with open (jsfile) as configfile:
		configdata = json.load(configfile)
		devices = configdata

	return devices


def binary_count(value, bitcount = "1", lenght = 60):
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



########################################################################################################################################################################
##
## 													Configuration Files load, if debug will change the folder
##
########################################################################################################################################################################

pseudoConfigs = dev_dict("DMRMasksConfig.json")
DebugMasks = dev_dict("DMRMasksDebug.json")