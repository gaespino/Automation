import json
import os
import shutil

def Configuration_dict():

	config = {	'UNCORE': 
		   			{
					'Freq':["F1", "F2", "F3", "F4"],
					'Products':
						{						
						'UCCAP':
							{
							
								'Configuration':
								{
									'path': 'Modules/FUN_UNCORE_COMP/InputFiles',
									'shmoo': 'UncoreFC_shmoo_config.json',
									'fctracking': '.InitialDefeatureTracking.json',
									'patmods': "FUN_UCC.patmod.json",
									'setpoints': 'FUN_UTP_setpoints.json',
									'fuseconfig': "FUN_UCCAP.fuseconfig.json",
									'ConfigFile':"~HDMT_TPL_DIR/Modules/FUN_UNCORE_COMP/InputFiles/",								
								},
								'Instances':
								{
									'DRAGON':
										{
											'F1': [value for i, value in class_instances(F='F1').items() if 'DRG' in i],
											'F2': [value for i, value in class_instances(F='F2').items() if 'DRG' in i],
											'F3': [value for i, value in class_instances(F='F3').items() if 'DRG' in i],
											'F4': [value for i, value in class_instances(F='F4').items() if 'DRG' in i]
										},
									'MPM':
										{
											'F1': [value for i, value in class_instances(F='F1').items() if 'MPM' in i],
											'F2': [value for i, value in class_instances(F='F2').items() if 'MPM' in i],
											'F3': [value for i, value in class_instances(F='F3').items() if 'MPM' in i],
											'F4': [value for i, value in class_instances(F='F4').items() if 'MPM' in i]
										},
									'MESH UUFC':
										{
											'F1': [value for i, value in class_instances(F='F1').items() if 'UUFC' in i],
											'F2': [value for i, value in class_instances(F='F2').items() if 'UUFC' in i],
											'F3': [value for i, value in class_instances(F='F3').items() if 'UUFC' in i],
											'F4': [value for i, value in class_instances(F='F4').items() if 'UUFC' in i]
										},
									'CORE_VMIN':
										{
											'F1': [value for i, value in class_instances(F='F1').items() if 'COREVMINF1' in i],
											#'F2': [value for i, value in class_instances(F='F2').items() if 'COREVMIN' in i],
											'F3': [value for i, value in class_instances(F='F3').items() if 'COREVMINF3' in i],
											#'F4': [value for i, value in class_instances(F='F4').items() if 'COREVMIN' in i]
										},
									'ALL': # All the file instances
										{
											'F1': [value for i, value in class_instances(F='F1').items() if not 'COREVMINF3' in i],
											'F2': [value for i, value in class_instances(F='F2').items() if not 'COREVMIN' in i],
											'F3': [value for i, value in class_instances(F='F3').items() if not 'COREVMINF1' in i],
											'F4': [value for i, value in class_instances(F='F4').items() if not 'COREVMIN' in i]								
										},
									'EXTERNAL': # Instances from an external file
										{
											'FILE':[]
										}						
								},
								'FCTRACKING':
								{
									'F1': {i:value for i, value in class_instances(F='F1').items() if 'FCTRACKING' in i},
									'F2': {i:value for i, value in class_instances(F='F2').items() if 'FCTRACKING' in i},
									'F3': {i:value for i, value in class_instances(F='F3').items() if 'FCTRACKING' in i},
									'F4': {i:value for i, value in class_instances(F='F4').items() if 'FCTRACKING' in i},
									'END': {i:value for i, value in class_instances(F='DPM').items() if 'ENDTRACKING' in i},
								},
							},
						'HCCSP':
							{
							
								'Configuration':
								{
									'path': 'Modules\FUN_UNCORE_COMP\InputFiles',
									'shmoo': 'UncoreFC_shmoo_config.json',
									'fctracking': '.InitialDefeatureTracking.json',
									'patmods': "FUN_HCCSP.patmod.json",
									'setpoints': 'FUN_UTP_setpoints.json',
									'fuseconfig': "FUN_HCCSP.fuseconfig.json",
									'ConfigFile':"~HDMT_TPL_DIR/Modules/FUN_UNCORE_COMP/InputFiles/",
								},
								'Instances':
								{
									'DRAGON':
										{
											'F1': [value for i, value in class_instances(F='F1').items() if 'DRG' in i],
											'F2': [value for i, value in class_instances(F='F2').items() if 'DRG' in i],
											'F3': [value for i, value in class_instances(F='F3').items() if 'DRG' in i],
											'F4': [value for i, value in class_instances(F='F4').items() if 'DRG' in i]
										},
									'MPM':
										{
											'F1': [value for i, value in class_instances(F='F1').items() if 'MPM' in i],
											'F2': [value for i, value in class_instances(F='F2').items() if 'MPM' in i],
											'F3': [value for i, value in class_instances(F='F3').items() if 'MPM' in i],
											'F4': [value for i, value in class_instances(F='F4').items() if 'MPM' in i]
										},
									'MESH UUFC':
										{
											'F1': [value for i, value in class_instances(F='F1').items() if 'UUFC' in i],
											'F2': [value for i, value in class_instances(F='F2').items() if 'UUFC' in i],
											'F3': [value for i, value in class_instances(F='F3').items() if 'UUFC' in i],
											'F4': [value for i, value in class_instances(F='F4').items() if 'UUFC' in i]
										},
									'CORE_VMIN':
										{
											'F1': [value for i, value in class_instances(F='F1').items() if 'COREVMINF1' in i],
											#'F2': [value for i, value in class_instances(F='F2').items() if 'COREVMIN' in i],
											'F3': [value for i, value in class_instances(F='F3').items() if 'COREVMINF3' in i],
											#'F4': [value for i, value in class_instances(F='F4').items() if 'COREVMIN' in i]
										},
									'ALL': # All the file instances
										{
											'F1': [value for i, value in class_instances(F='F1').items() if not 'COREVMINF3' in i],
											'F2': [value for i, value in class_instances(F='F2').items() if not 'COREVMIN' in i],
											'F3': [value for i, value in class_instances(F='F3').items() if not 'COREVMINF1' in i],
											'F4': [value for i, value in class_instances(F='F4').items() if not 'COREVMIN' in i]								
										},
									'EXTERNAL': # Instances from an external file
										{
											'FILE':[]
										}						
								},
								'FCTRACKING':
								{
									'F1': {i:value for i, value in class_instances(F='F1').items() if 'FCTRACKING' in i},
									'F2': {i:value for i, value in class_instances(F='F2').items() if 'FCTRACKING' in i},
									'F3': {i:value for i, value in class_instances(F='F3').items() if 'FCTRACKING' in i},
									'F4': {i:value for i, value in class_instances(F='F4').items() if 'FCTRACKING' in i},
									'END': {i:value for i, value in class_instances(F='DPM').items() if 'ENDTRACKING' in i},
								},
							}
						},
					},
		   		'CORE': ## This is still WIP, UNCORE is working
					{ 
					'Freq':["F1", "F2", "F3", "F4", "F5", "F6", "F7"],
					'Products':
						{
						'UCCAP':
						{                         
								'Configuration':
								{
									'path': 'Modules\FUN_UNCORE_COMP\InputFiles',
									'shmoo': 'UncoreFC_shmoo_config.json',
									'fctracking': '.InitialDefeatureTracking.json',
									'patmods': "FUN_UCC.patmod.json",
									'setpoints': 'FUN_UTP_setpoints.json',
									'fuseconfig': "FUN_UCCAP.fuseconfig.json",
									'ConfigFile':"~HDMT_TPL_DIR/Modules/FUN_UNCORE_COMP/InputFiles/",								
								},
								'Instances':
								{
									'SBFT':
										{

										},
									'SLICE':
										{

										},
									'EXTERNAL': # Instances from an external file
										{
											'FILE':[]
										}						
								},
								'FCTRACKING':
								{
									
								},
							},
						}
					   
				}
			}
	
	return config

def fungroup(selection = 'UNCORE', product= 'UCCAP'):

	prod = {'UCCAP': {'patmods':'FUN_UCC', 'fuse':'FUN_UCCAP'}}
	
	funSelection = {'UNCORE': 
				 		{	'path': 'Modules\FUN_UNCORE_COMP\InputFiles',
							'shmoo': 'UncoreFC_shmoo_config.json',
							'fctracking': '.InitialDefeatureTracking.json',
							'patmods': f"{prod[product]['patmods']}.patmod.json",
							'setpoints': 'FUN_UTP_setpoints.json',
							'fuseconfig': f"{prod[product]['fuse']}.fuseconfig.json",
							'ConfigFile':"~HDMT_TPL_DIR/Modules/FUN_UNCORE_COMP/InputFiles/"
	   					}
					}
	return funSelection[selection]

def class_instances(F):
	
	uncore_instances = {f'DRG_{F}_CD0':			f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHDRGCD0',
						f'DRG_{F}_CD1':			f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHDRGCD1',
						f'DRG_{F}_CD2':			f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHDRGCD2',
						f'UUFC_{F}_PARALLEL':	f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHTWPARALLEL',
						f'UUFC_{F}_CFC_MESHTW':	f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHTW',
						f'UUFC_{F}_HDC_MESHTW':	f'FUN_UNCORE_COMP::UNCORE_HDC_VMIN_K_CHKCFCHDC{F}_STF_HDC_VMIN_{F}_MESHTW',
						f'MPM_{F}_CD0':			f'FUN_UNCORE_COMP::UNCORE_DDR_VMIN_K_CHKDDRD{F}_STF_DDRD_VMIN_{F}_DDRMPMCD1',
						f'MPM_{F}_CD1':			f'FUN_UNCORE_COMP::UNCORE_DDR_VMIN_K_CHKDDRD{F}_STF_DDRD_VMIN_{F}_DDRMPMCD2',
						f'MPM_{F}_CD2':			f'FUN_UNCORE_COMP::UNCORE_DDR_VMIN_K_CHKDDRD{F}_STF_DDRD_VMIN_{F}_DDRMPMCD3',
						f'FCTRACKINGA_{F}':		f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGA',
						f'FCTRACKINGB_{F}':		f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGB',
						f'FCTRACKINGC_{F}':		f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGC',	
						f'FCTRACKINGD_{F}':		f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGD',
						f'COREVMINF3_END_PASS1':	f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_END_STF_CFCHDC_VMIN_F3_DPM_PASS1',
						f'COREVMINF3_END_PASS2':	f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_END_STF_CFCHDC_VMIN_F3_DPM_PASS2',
						f'COREVMINF3_END_PASS3':	f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_END_STF_CFCHDC_VMIN_F3_DPM_PASS3',
						f'COREVMINF1_END':	f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_END_STF_CFCHDC_VMIN_F1_DPM',
						f'ENDTRACKINGA_{F}':		f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_END_X_X_X_X_FCTRACKINGA',
						f'ENDTRACKINGB_{F}':		f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_END_X_X_X_X_FCTRACKINGB',
						f'ENDTRACKINGC_{F}':		f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_END_X_X_X_X_FCTRACKINGC',	
					}

	return uncore_instances

def configSave(selection, config, savefile, clear=False):
	
	if os.path.isfile(savefile) and not clear:
		print(f'Configuration file exists in current TP, reading it...')
		dConfig = configRead(savefile)
	else:
		print(f'Configuration file doesn not exists in current TP, creating it...')
		dConfig = {
					'Config1': None, 
					'Config2': None,
					'Config3': None,}
	
	
	cfile = savefile
	if selection in dConfig.keys() and not clear:
		dConfig[selection] = config
		json_save(savefile, dConfig)
		print(f' --- Saving {selection} to the configuration file: {cfile}')
	elif clear:
		print(f' --- Clearing {cfile}, to avoid non desired old tests to be loaded..')
		json_save(savefile, dConfig)

	else:
		print(f' --- Nothing to save in Config file')

def voltages():

	voltages = {	'CORE':	{
							'AMXF7':{
									'VoltageTargets':'VminVars.VCORE_RST',
									'StartVoltages':"DUT.SPEED_F7_VMINSTART_AMX",
									'EndVoltageLimits': "DUT.SPEED_F7_VMINEND_AMX",
									'StartVoltegesForRetry': 'VminVars.SPEED_F7_VMINRETRY_AMX',
									'ForwardingIdentifier': 'VminForwardingVars.AMXF7Corner',
									'OffsetValue': "0.02",
									'StartOffset': "DUT.SPEED_F7_STARTOFFSET_AMX"
									},
							'AMXF3':{
									'VoltageTargets':'VminVars.VCORE_RST',
									'StartVoltages':"DUT.SPEED_F3_VMINSTART_AMX",
									'EndVoltageLimits': "DUT.SPEED_F3_VMINEND_AMX",
									'StartVoltegesForRetry': 'VminVars.SPEED_F3_VMINRETRY_AMX',
									'ForwardingIdentifier': 'VminForwardingVars.AMXF3Corner',
									'OffsetValue': "0.02",
									'StartOffset': "DUT.SPEED_F3_STARTOFFSET_AMX"
									},
							'AMXF1':{
									'VoltageTargets':'VminVars.VCORE_RST',
									'StartVoltages':"DUT.SPEED_F1_VMINSTART_AMX",
									'EndVoltageLimits': "DUT.SPEED_F1_VMINEND_AMX",
									'StartVoltegesForRetry': 'VminVars.SPEED_F1_VMINRETRY_AMX',
									'ForwardingIdentifier': 'VminForwardingVars.AMXF1Corner',
									'OffsetValue': "0.02",
									'StartOffset': "DUT.SPEED_F1_STARTOFFSET_AMX"
									},		
							},
			 		'CFC':	{
						 	'CFCF1':{
									'VoltageTargets':'VminVars.VCFC_COMP',
									'StartVoltages':"DUT.SPEED_F1_VMINSTART_CFCCDIE",
									'EndVoltageLimits': "DUT.SPEED_F1_VMINEND_CFCCDIE",
									'StartVoltegesForRetry': 'VminVars.SPEED_F1_VMINRETRY_CFCCDIE',
									'ForwardingIdentifier': 'VminForwardingVars.CFCCOMPF1Corner',
									'OffsetValue': "0.01",
									'StartOffset': "DUT.SPEED_F1_STARTOFFSET_CFCCDIE"
									},
							'CFCF2':{
									'VoltageTargets':'VminVars.VCFC_COMP',
									'StartVoltages':"DUT.SPEED_F2_VMINSTART_CFCCDIE",
									'EndVoltageLimits': "DUT.SPEED_F2_VMINEND_CFCCDIE",
									'StartVoltegesForRetry': 'VminVars.SPEED_F2_VMINRETRY_CFCCDIE',
									'ForwardingIdentifier': 'VminForwardingVars.CFCCOMPF2Corner',
									'OffsetValue': "0.01",
									'StartOffset': "DUT.SPEED_F2_STARTOFFSET_CFCCDIE"
									},
							'CFCF3':{
									'VoltageTargets':'VminVars.VCFC_COMP',
									'StartVoltages':"DUT.SPEED_F3_VMINSTART_CFCCDIE",
									'EndVoltageLimits': "DUT.SPEED_F3_VMINEND_CFCCDIE",
									'StartVoltegesForRetry': 'VminVars.SPEED_F3_VMINRETRY_CFCCDIE',
									'ForwardingIdentifier': 'VminForwardingVars.CFCCOMPF3Corner',
									'OffsetValue': "0.01",
									'StartOffset': "DUT.SPEED_F3_STARTOFFSET_CFCCDIE"
									},
							'CFCF4':{
									'VoltageTargets':'VminVars.VCFC_COMP',
									'StartVoltages':"DUT.SPEED_F4_VMINSTART_CFCCDIE",
									'EndVoltageLimits': "DUT.SPEED_F4_VMINEND_CFCCDIE",
									'StartVoltegesForRetry': 'VminVars.SPEED_F4_VMINRETRY_CFCCDIE',
									'ForwardingIdentifier': 'VminForwardingVars.CFCCOMPF2Corner',
									'OffsetValue': "0.01",
									'StartOffset': "DUT.SPEED_F4_STARTOFFSET_CFCCDIE"
									},
							}
				}
	
	return voltages

def frequencies (cfc=None, ddr=None, funslc=None, ia=None, cfcio=None):
	
	freqdict = {
				'CFCF1':{	
						"RST:CFC_CDIE":8,
						"RST:DDR":24,
						"TTR:FUNSLC_HVM":8,
						"RST:IA":14,
						"RST:CFC_IO":16
						},
				'CFCF2':{	
						"RST:CFC_CDIE":14,
						"RST:DDR":24,
						"TTR:FUNSLC_HVM":8,
						"RST:IA":14,
						"RST:CFC_IO":16
						},
				'CFCF3':{	
						"RST:CFC_CDIE":18,
						"RST:DDR":24,
						"TTR:FUNSLC_HVM":8,
						"RST:IA":14,
						"RST:CFC_IO":16
						},
				'CFCF4':{	
						"RST:CFC_CDIE":22,
						"RST:DDR":24,
						"TTR:FUNSLC_HVM":8,
						"RST:IA":14,
						"RST:CFC_IO":16
						},
				'COREF1':{	
						"RST:CFC_CDIE":16,
						"RST:DDR":24,
						"TTR:FUNSLC_HVM":8,
						"RST:IA":8,
						"RST:CFC_IO":16
						},
				'COREF3':{	
						"RST:CFC_CDIE":16,
						"RST:DDR":24,
						"TTR:FUNSLC_HVM":8,
						"RST:IA":24,
						"RST:CFC_IO":16
						},
				'COREF7':{	
						"RST:CFC_CDIE":16,
						"RST:DDR":24,
						"TTR:FUNSLC_HVM":8,
						"RST:IA":40,
						"RST:CFC_IO":16
						},
						}
	
	return freqdict


def freqPreinstance(cfc=None, ddr=None, funslc=None, ia=None, cfcio=None):

	preinstance = 	{
					'TestPointPreinstance': 
						{	
						"RST:CFC_CDIE":cfc,
						"RST:DDR":ddr,
						"TTR:FUNSLC_HVM":funslc,
						"RST:IA":ia,
						"RST:CFC_IO":cfcio
						}
					}
	
	Name = 'TestPointPreinstance'
	value = [f"{i}:{v}" for i,v in preinstance[Name].items() if v]
	preinstanceString = ','.join(str,value)

	return preinstanceString

def configRead(savefile):
	print('Reading Configuration File')
	with open(savefile, 'r') as file: dConfig = json.load(file)
	return dConfig

def filecopy(src, dst, overwrite =True):
	if os.path.isfile(dst) and not overwrite:
		print(f' -- File already in Test program location, overwrite key disabled not updating file: {dst}.')
	else:
		print(f' -- Moving file to Test program location: {dst}.')
		shutil.copy(src, dst)

def json_save(filename, dict):
	jfile = filename 
	print(f"Saving jsonfile data in file: {jfile}")
	with open(jfile, 'w') as json_file:
		json.dump(dict, json_file, indent = 1)

dictionary = Configuration_dict()
ShmooConfigs = Configuration_dict()

Frequencies = {key:value['Freq'] for key, value in ShmooConfigs.items()}
func_groups = [key for key in ShmooConfigs.keys()]
group_products = {g:[p for p in ShmooConfigs[g]['Products'].keys()] for g in ShmooConfigs.keys()}

#print('Frequencies', Frequencies)

#print('Functional Groups', func_groups)

#print('Group Products', group_products)

