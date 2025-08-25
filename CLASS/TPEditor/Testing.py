def Configuration_dict():

	config = {	'UNCORE': 
		   			{'UCCAP':
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
								'frequencies':["F1", "F2", "F3", "F4"]
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
                                'ALL': # All the file instances
                                    {
                                        'F1': [value for i, value in class_instances(F='F1').items()],
                                        'F2': [value for i, value in class_instances(F='F2').items()],
                                        'F3': [value for i, value in class_instances(F='F3').items()],
                                        'F4': [value for i, value in class_instances(F='F4').items()]								
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
								'F4': {i:value for i, value in class_instances(F='F4').items() if 'FCTRACKING' in i}
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
								'frequencies':["F1", "F2", "F3", "F4"]
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
                                'ALL': # All the file instances
                                    {
                                        'F1': [value for i, value in class_instances(F='F1').items()],
                                        'F2': [value for i, value in class_instances(F='F2').items()],
                                        'F3': [value for i, value in class_instances(F='F3').items()],
                                        'F4': [value for i, value in class_instances(F='F4').items()]								
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
								'F4': {i:value for i, value in class_instances(F='F4').items() if 'FCTRACKING' in i}
							},
                        }
					},
    	   		'CORE':''}
	
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
					}

	return uncore_instances

dictionary = Configuration_dict()

print(dictionary)