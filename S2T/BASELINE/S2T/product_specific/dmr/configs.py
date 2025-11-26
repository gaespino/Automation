"""
Configuration variables required to properly set System Framework based on product

REV 0.1 --
Code migration to product specific features

"""

CONFIG_PRODUCT = ['DMR', 'DMR_CLTAP']

print (f"Loading Configurations for {CONFIG_PRODUCT} || REV 0.1")

class configurations:

	def __init__(self, product):
		self.product: str = product
		self.config_product: list[str] = CONFIG_PRODUCT
		self.product_check(product)

	def _get_chop(self, sv):
		domains_size = len(sv.socket0.cbbs)
		chop = None

		if domains_size == 4:		
			chop = 'X4'
		elif domains_size == 3:		
			chop = 'X3'
		elif domains_size == 2:
			chop = 'X2'
		elif domains_size == 1:
			chop = 'X1' # holder we don't really support GNR HCC 
		else:
			raise ValueError (f" Invalid Domains size: {domains_size}")
		print(f' GNR Product configuration: {chop}')
		return chop

	def _get_variant(self, sv):
		domains_size = len(sv.socket0.cbbs)
		variant = None
		if domains_size == 4:		
			variant = 'AP'
		elif domains_size == 3:		
			variant = 'AP'
		elif domains_size == 2:
			variant = 'SP'
		elif domains_size == 1:
			variant = 'SP' # holder we don't really support GNR HCC 
		else:
			raise ValueError (f" Invalid Domains size: {domains_size}")
		print(f' GNR Product configuration: {variant}')
		return variant

	def product_check(self, product):
		if product not in CONFIG_PRODUCT:
			raise ValueError (f" Invalid Product, this function is only available for {CONFIG_PRODUCT}")

	def init_product_specific(self):
		
		# Product config
		product = self.product
		
		# System Specific Configurations based on product
		ConfigFile = f'{product}FuseFileConfigs.json'
		CORESTRING = 'MODULE'
		CHASTRING = 'CBO'
		CORETYPES = {'DMR_CLTAP':{	'core':'bigcore',
									'config':'AP', 
									'mods_per_cbb':32, #DMR_TOTAL_MODULES_PER_CBB
									'mods_per_compute':8, #DMR_TOTAL_MODULES_PER_COMPUTE
									'active_per_cbb':32, #DMR_TOTAL_ACTIVE_MODULES_PER_CBB
									'max_cbbs': 4, # DMR TOTAL CBBS
									'max_imhs': 2, # max IMHS total
									'maxcores': 128, # max modules total
									'maxlogcores': 256}, 
					
					'DMR_CLTSP':{	'core':'bigcore', ## Other Flavours ?
									'config':'SP', 
									'mods_per_cbb':32,
									'mods_per_compute':8,
									'active_per_cbb':32, #DMR_TOTAL_ACTIVE_MODULES_PER_CBB
									'max_cbbs': 2, # DMR TOTAL CBBS
									'max_imhs': 1, # max IMHS total
									'maxcores': 64, 
									'maxlogcores': 128}}
		MAXLOGICAL = 32
		MAXPHYSICAL = 32
		classLogical2Physical = {0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:10,11:11,12:12,13:13,14:14,15:15,16:16,17:17,18:18,19:19,20:20,21:21,22:22,23:23,24:24,25:25,26:26,27:27,28:28,29:29,30:30,31:31}
		#classLogical2Physical = {0:6,1:13,2:20,3:27,4:7,5:14,6:21,7:28,8:8,9:15,10:22,11:29,12:34,13:41,14:48,15:55,16:35,17:42,18:49,19:56,20:36,21:43,22:50,23:57}
		physical2ClassLogical = {value: key for key, value in classLogical2Physical.items()}
		phys2colrow= {0: [0, 0], 1: [1, 0], 2: [2, 0], 3: [3, 0], 4: [0, 1], 5: [1, 1], 6: [2, 1], 7: [3, 1], 8: [0, 2], 9: [1, 2], 10: [2, 2], 11: [3, 2], 12: [0, 3], 13: [1, 3], 14: [2, 3], 15: [3, 3], 16: [0, 4], 17: [1, 4], 18: [2, 4], 19: [3, 4], 20: [0, 5], 21: [1, 5], 22: [2, 5], 23: [3, 5], 24: [0, 6], 25: [1, 6], 26: [2, 6], 27: [3, 6], 28: [0, 7], 29: [1, 7], 30: [2, 7], 31: [3, 7]}
		skip_physical = []
		PHY2APICID = [0,2,9,16, 23,1,3,10,17,24,4,11,19,25,5,12,19,26,6,13,20,27,7,14,21,28,8,15,22,29,30,37,44,51,58,31,38,45,52,59,32,39,46,53,33,40,47,54,34, 41,48,55,35,42,49,56,36,43,50,57]
			
		## If using atomid of each module -- module[#].target_info['atomid'] -- Latest version of PySV relocates modules to use Physical Location
		ClassLog2AtomID = {0:6,1:13,2:20,3:27,4:7,5:14,6:21,7:28,8:8,9:15,10:22,11:29,12:34,13:41,14:48,15:55,16:35,17:42,18:49,19:56,20:36,21:43,22:50,23:57} # Logical value : Physical value (only active modules in CWF)
		AtomID2ClassLog = {value: key for key, value in ClassLog2AtomID.items()} # Physical value : Logical value (only active modules in CWF)

		CONFIG = { 'PRODUCT':product,
				'CONFIGFILE': ConfigFile,
				'CORESTRING': CORESTRING,
				'CHASTRING': CHASTRING,
				'CORETYPES': CORETYPES,
				'MAXLOGICAL': MAXLOGICAL,
				'MAXPHYSICAL': MAXPHYSICAL,
				'LOG2PHY': classLogical2Physical,
				'PHY2LOG': physical2ClassLogical,
				'PHY2COLROW': phys2colrow,
				'SKIPPHYSICAL': skip_physical,
				'PHY2APICID': PHY2APICID, # PlaceHolder Not used for now same for GNR / CWF
				'LOG2ATOMID': ClassLog2AtomID,
				'ATOMID2LOG': AtomID2ClassLog,
				}
		
		return CONFIG

	def init_product_fuses(self):

		# Product config
		product = self.product
		
		# Fuses Configurations below required in some parts of the logic to be moved to a product specific 
		pseudoConfigs =f'{product}MasksConfig.json'
		DebugMasks = f'{product}MasksDebug.json'
		ConfigFile = f'{product}FuseFileConfigs.json'
		BurnInFuses = f'{product}BurnInFuses.json'
		fuse_instance = ['hwrs_top_ram']
		cfc_voltage_curves = {	'cfc_curve': ['pcode_cfc_vf_voltage_point0','pcode_cfc_vf_voltage_point1','pcode_cfc_vf_voltage_point2','pcode_cfc_vf_voltage_point3','pcode_cfc_vf_voltage_point4','pcode_cfc_vf_voltage_point5'],
						#'hdc_curve': ['pcode_hdc_vf_voltage_point0','pcode_hdc_vf_voltage_point1','pcode_hdc_vf_voltage_point2','pcode_hdc_vf_voltage_point3','pcode_hdc_vf_voltage_point4','pcode_hdc_vf_voltage_point5'],
						'hdc_curve': ['pcode_l2_vf_voltage_point0','pcode_l2_vf_voltage_point1','pcode_l2_vf_voltage_point2','pcode_l2_vf_voltage_point3','pcode_l2_vf_voltage_point4','pcode_l2_vf_voltage_point5'],
					}
			
		cfc_ratio_curves = {	'cfc_curve': ['pcode_cfc_vf_ratio_point0','pcode_cfc_vf_ratio_point1','pcode_cfc_vf_ratio_point2','pcode_cfc_vf_ratio_point3','pcode_cfc_vf_ratio_point4','pcode_cfc_vf_ratio_point5'],
						'hdc_curve': ['pcode_l2_vf_ratio_point0','pcode_l2_vf_ratio_point1','pcode_l2_vf_ratio_point2','pcode_l2_vf_ratio_point3','pcode_l2_vf_ratio_point4','pcode_l2_vf_ratio_point5'],
						'pstates' : {	'p0':'pcode_sst_pp_0_cfc_p0_ratio', 
										'p1':'pcode_sst_pp_0_cfc_p1_ratio', 
										'pn':'pcode_cfc_pn_ratio', 
										'min':'pcode_cfc_min_ratio'}
					}
		ia_ratio_curves = {	'limits': [f'pcode_sst_pp_##profile##_turbo_ratio_limit_ratios_cdyn_index##idx##_ratio##ratio##'],
						'p1': [f'pcode_sst_pp_##profile##_sse_p1_ratio'],
						'vf_curve': ['pcode_ia_vf_ratio_voltage_index##idx##_ratio_point0','pcode_ia_vf_ratio_voltage_index##idx##_ratio_point1','pcode_ia_vf_ratio_voltage_index##idx##_ratio_point2','pcode_ia_vf_ratio_voltage_index##idx##_ratio_point3','pcode_ia_vf_ratio_voltage_index##idx##_ratio_point4','pcode_ia_vf_ratio_voltage_index##idx##_ratio_point5'],
						'pstates' : {	'p0':'pcode_ia_p0_ratio', 
										'pn':'pcode_ia_pn_ratio', 
										'min':'pcode_ia_min_ratio',
									}
					}				

		ia_ratios_config = {		
									'ppfs' : [0,1,2,3,4],
									'idxs' : [0,1,2,3,4,5],
									'ratios': [0,1,2,3,4,5,6,7],
									'vfidx' :  [0,1,2,3],
									'vfpnt' :  [0,1,2,3,4,5]
									}
			
		ia_voltage_curves = {	'vf_curve': ['pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point0','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point1','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point2','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point3','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point4','pcode_ia_vf_voltage_curve##curve##_voltage_index##idx##_voltage_point5'],
					}
		fuses_600w_comp = []
		fuses_600w_io = []

		htdis_comp = []
		htdis_io = []
		vp2intersect = 	{	'fast':[],
							'bs':[],}

			
		FrameworkFuses = {
							'ConfigFile':				ConfigFile,
							'DebugMasks':				DebugMasks,
							'pseudoConfigs':			pseudoConfigs,
							'BurnInFuses':				BurnInFuses,
							'fuse_instance':			fuse_instance,
							'cfc_ratio_curves':			cfc_ratio_curves,
							'cfc_voltage_curves':		cfc_voltage_curves,
							'ia_ratio_curves':			ia_ratio_curves,
							'ia_voltage_curves':		ia_voltage_curves,
							'ia_ratios_config':			ia_ratios_config,
							'fuses_600w_comp':			fuses_600w_comp,
							'fuses_600w_io':			fuses_600w_io,
							'htdis_comp':				htdis_comp,
							'htdis_io':					htdis_io,
							'vp2intersect':				vp2intersect,
							} 		

		
		return FrameworkFuses

	def init_framework_vars(self):

		# Product config
		product = self.product
		
		# Path of All S2T scripts
		BASE_PATH = 'users.THR.dmr_debug_utilities' 

		## System 2 Tester and bootscript Initialization data 
		bootscript_data = {	'DMR_CLTAP':{'segment':'CWFXDCC','config':['cbb0', 'cbb1', 'cbb2', 'cbb3'], 'compute_config':'x4',},
								'DMR_CLTSP':{'segment':'CWFHDCC','config':['cbb0'], 'compute_config':'x1',}}

		# Licence Configuration CWF
		core_license_dict = {'IA':1,'SSE':1,}
		license_dict = { 0:"Don't set license",1:"SSE/128",}
		core_license_levels = [k for k in core_license_dict.keys()]
				
		# Special QDF configuration CWF
		qdf600 = ['']

		# Mesh Configurations CWF
		ate_masks = 	{
							'DMR_CLTAP':{1:'FirstPass', 2:'SecondPass',3:'ThirdPass', 4:'RowPass1',5:'RowPass2',6:'RowPass3'},
							'DMR_CLTSP':{1:'FirstPass(FullChip)'}
							}
		masks_AP = [v for k,v in ate_masks['DMR_CLTAP'].items()]
		masks_SP = [v for k,v in ate_masks['DMR_CLTSP'].items()]

		ValidClass = {'DMR_CLTAP':masks_AP,'DMR_CLTSP':masks_SP}

		ValidRows = ['ROW5','ROW6','ROW7']
		ValidCols = ['COL1','COL2','COL3','COL4','COL5','COL6','COL7','COL8']
		customs = ValidRows + ValidCols#['ROW5','ROW6','ROW7','COL1','COL2','COL3','COL4','COL5','COL6','COL7','COL8']
		RigthSide_mask = ['COL5','COL6','COL7','COL8']
		LeftSide_mask = ['COL1','COL2','COL3','COL4']

		ate_config = 	{	
							'main':{
									'l1':('\t> 1. ATE pseudo Configuration: '),
									'l1-1':(f'\t\t> CWF XDCC (AP): {masks_AP}'),
									'l1-2':(f'\t\t> CWF XHCC (SP): {masks_SP}'),
									'l4':('\t> 2. Tile Isolation: Specify the Compute to be used for testing'),
									'l5':('\t> 3. Custom: Mix and Match of Columns and Rows'),
									'l6':('\t> 4. Full Chip')},
							'CWFAP':{
									'l1':('\t> 1. FirstPass: All CDIEs - Columns [1, 2, 5, 8]'),
									'l2':('\t> 2. SecondPass: All CDIEs - Columns [1, 3, 6, 8]'),
									'l3':('\t> 2. ThirdPass: All CDIEs - Columns [1, 4, 7, 8]'),
									'l4':('\t> 3. RowPass1: CDIE0 - Rows [5], CDIE1 - Rows [5], CDIE2 - Rows [5]:'),
									'l5':('\t> 4. RowPass2: CDIE0 - Rows [6], CDIE1 - Rows [6], CDIE2 - Rows [6]:'),
									'l6':('\t> 4. RowPass3: CDIE0 - Rows [7], CDIE1 - Rows [7], CDIE2 - Rows [7]:'),
									'maxrng' : 7},
							'CWFSP':{
									'l1': ('\t> 1. FirstPass: Full Chip -- No need for masking on SP'),	
									'maxrng' : 2
									}		
							}

		dis2cpm_menu = 	{	
							'main':{
									'l1':('\t> 1. Not available for this product'),
									'maxrng': 2},
							}
		dis2cpm_dict = {1:None}

		dis1cpm_menu = 	{	
							'main':{
									'l1':('\t> 1. Disable HIGH Core (0x2): Core1'),
									'l2':('\t> 2. Disable LOW Core (0x1): Core0'),
									'maxrng': 3},
							}
		dis1cpm_dict = {1:'HIGH',2:'LOW'}


		FrameworkVars = { 
							'core_license_dict' : 	core_license_dict,
							'license_dict' : license_dict,
							'core_license_levels' : core_license_levels,
							'dis2cpm_menu': dis2cpm_menu,
							'dis2cpm_dict': dis2cpm_dict,
							'dis1cpm_menu': dis1cpm_menu,
							'dis1cpm_dict': dis1cpm_dict,
							'qdf600' : qdf600,
							'ate_config' : ate_config,
							'ate_masks' : ate_masks,
							'ValidClass' : ValidClass,
							'customs' : customs,
							'righthemisphere' : RigthSide_mask,
							'lefthemisphere' : LeftSide_mask,
							'ValidRows' : ValidRows,
							'ValidCols' : ValidCols,
							'bootscript_data' : bootscript_data,
							'base_path': BASE_PATH,
			}
		
		return FrameworkVars

	def init_framework_features(self):

		# Product config
		product = self.product
		
		# System 2 Tester Feature Enabling
		FrameworkFeatures = {
							'debug':				{'default':False,'enabled':True,'disabled_value':False,},
							'targetLogicalCore':	{'default':None,'enabled':True,'disabled_value':None,},
							'targetTile':			{'default':None,'enabled':True,'disabled_value':None,},
							'use_ate_freq':			{'default':True,'enabled':True,'disabled_value':True,},
							'use_ate_volt':			{'default':False,'enabled':True,'disabled_value':False,},
							'flowid':				{'default':1,'enabled':True,'disabled_value':1,},
							'core_freq':			{'default':None,'enabled':True,'disabled_value':None,},
							'mesh_freq':			{'default':None,'enabled':True,'disabled_value':None,},
							'io_freq':				{'default':None,'enabled':True,'disabled_value':None,},
							'license_level':		{'default':None,'enabled':False,'disabled_value':None,},
							'dcf_ratio':			{'default':None,'enabled':False,'disabled_value':None,},
							'stop_after_mrc':		{'default':False,'enabled':True,'disabled_value':False,},
							'boot_postcode':		{'default':False,'enabled':True,'disabled_value':False,},
							'clear_ucode':			{'default':None,'enabled':False,'disabled_value':False,},
							'halt_pcu':				{'default':None,'enabled':False,'disabled_value':False,},
							'dis_acode':			{'default':False,'enabled':False,'disabled_value':False,},
							'dis_ht':				{'default':None,'enabled':False,'disabled_value':False,},
							'dis_2CPM':				{'default':None,'enabled':False,'disabled_value':None,},
							'dis_1CPM':				{'default':None,'enabled':True,'disabled_value':0,},
							'postBootS2T':			{'default':True,'enabled':True,'disabled_value':True,},
							'clusterCheck':			{'default':None,'enabled':True,'disabled_value':None,},
							'lsb':					{'default':False,'enabled':True,'disabled_value':False,},
							'fix_apic':				{'default':None,'enabled':False,'disabled_value':False,},
							'dryrun':				{'default':False,'enabled':True,'disabled_value':False,},
							'fastboot':				{'default':False,'enabled':True,'disabled_value':False,},
							'mlcways':				{'default':None,'enabled':False,'disabled_value':False,},
							'ppvc_fuses':			{'default':None,'enabled':True,'disabled_value':None,},
							'custom_volt':			{'default':None,'enabled':True,'disabled_value':None,},
							'vbumps_volt':			{'default':None,'enabled':True,'disabled_value':None,},
							'reset_start':			{'default':None,'enabled':True,'disabled_value':None,},
							'check_bios':			{'default':None,'enabled':True,'disabled_value':None,},
							'mesh_cfc_volt':		{'default':None,'enabled':True,'disabled_value':None,},
							'mesh_hdc_volt':		{'default':None,'enabled':True,'disabled_value':None,},
							'io_cfc_volt':			{'default':None,'enabled':True,'disabled_value':None,},
							'ddrd_volt':			{'default':None,'enabled':True,'disabled_value':None,},
							'ddra_volt':			{'default':None,'enabled':True,'disabled_value':None,},
							'core_volt':			{'default':None,'enabled':True,'disabled_value':None,},
							'u600w':				{'default':None,'enabled':False,'disabled_value':None,},
							'extMasks':				{'default':None,'enabled':True,'disabled_value':None},
							'reg_select':			{'default':None,'enabled':False,'disabled_value':1,}
							}
		
		return FrameworkFeatures

	def init_dff_data(self):

		# Product config
		product = self.product
		
		CORE_FREQ = {# done - CORE_SSE_HDC_RATIO_6
				1:[8],
				2:[16],
				3:[22],
				4:[26],
				5:[28],
				6:[32, 31, 30, 29]
			}
		CORE_CFC_FREQ = {# done - UNCORE_CFCxCOMP_RATIO_SAFE - Jose Zuñiga recommends to use the safe values
				1:8,
				2:8,
				3:8,
				4:8,
				5:8,
				6:8
			}
		CORE_CFCIO_FREQ = {# done - UNCORE_CFCxIO_RATIO_SAFE - Jose Zuñiga recommends to use the safe values
				1:8,
				2:8,
				3:8,
				4:8,
				5:8,
				6:8
			}

		CFC_FREQ = {# done - UNCORE_CFCxCOMP_RATIO_4
				1:[8],
				2:[14],
				3:[18], 
				4:[22]  
			}
			
		HDC_FREQ = {# done - UNCORE_CFCxCOMP_RATIO_4
				1:[8],
				2:[16],
				3:[22],
				4:[26],
				5:[28],
				6:[32, 31, 30, 29] 
			}
		IO_FREQ = {# done - UNCORE_CFCxIO_RATIO
				1:[8],
				2:[14],
				3:[20],
				4:[24] 
			}
		
		CFC_CORE_FREQ = {# done - CORE_SSE_HDC_RATIO_SAFE - Jose Zuñiga recommends to use the safe values
				1:8,
				2:8,
				3:8,
				4:8,
			}
		HDC_CORE_FREQ = {# done - CORE_SSE_HDC_RATIO_SAFE - Jose Zuñiga recommends to use the safe values
				1:8,
				2:8,
				3:8,
				4:8,
				5:8,
				6:8,
			}
		
		CFCIO_CORE_FREQ = {# done - CORE_SSE_HDC_RATIO_SAFE - - Jose Zuñiga recommends to use the safe values
				1:8,
				2:8,
				3:8,
				4:8,
			}
		
		IO_HDC_FREQ = {# Not used
				1:8,
				2:14,
				3:20,
				4:24,
			}
		
		CFC_IO_FREQ = {# Done - UNCORE_CFCxIO_RATIO
				1:8,
				2:14,
				3:20,
				4:24,
			}
		
		CORE_HDC_CFC_FREQ = {# Not used
				1:8,
				2:8,
				3:8,
				4:8,
			}

		#FivrCondition	All_Safe_RST_PKG
		All_Safe_RST_PKG = {# Safe Voltages
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

		#FivrCondition	All_Safe_RST_CDie
		All_Safe_RST_CDIE = {# Safe Voltages
				'VCORE_RST':0.85,
				'VHDC_RST':0.90,
				'VCFC_CDIE_RST':0.85,
				'VDDRA_RST':0.90,
				'VDDRD_RST':0.85,
			}
			
		cfc_max = 4
		hdc_max = 6
		core_max = 6
		io_max = 4

		wsdl_url = "http://mfglabdffsvc.intel.com/MDODFFWcf/DFFSVC.svc?wsdl"
			
		DFF_DATA_INIT = {
								'CORE_FREQ':CORE_FREQ,
								'CORE_CFC_FREQ': CORE_CFC_FREQ,
								'CORE_CFCIO_FREQ': CORE_CFCIO_FREQ,
								'CFC_FREQ': CFC_FREQ,
								'HDC_FREQ': HDC_FREQ,
								'IO_FREQ': IO_FREQ,
								'CFC_CORE_FREQ': CFC_CORE_FREQ,
								'HDC_CORE_FREQ': HDC_CORE_FREQ,
								'CFCIO_CORE_FREQ': CFCIO_CORE_FREQ,
								'IO_HDC_FREQ': IO_HDC_FREQ,
								'CFC_IO_FREQ': CFC_IO_FREQ,
								'CORE_HDC_CFC_FREQ': CORE_HDC_CFC_FREQ,
								'All_Safe_RST_PKG': All_Safe_RST_PKG,
								'All_Safe_RST_CDIE': All_Safe_RST_CDIE,
								'cfc_max': cfc_max,
								'hdc_max': hdc_max,
								'core_max': core_max,
								'io_max': io_max,
								'wsdl_url': wsdl_url,                            
								}

		return DFF_DATA_INIT

			
