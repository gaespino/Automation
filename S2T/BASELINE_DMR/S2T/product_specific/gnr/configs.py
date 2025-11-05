"""
Configuration variables required to properly set System Framework based on product

REV 0.1 --
Code migration to product specific features

"""

CONFIG_PRODUCT = 'GNR'

print (f"Loading Configurations for {CONFIG_PRODUCT} || REV 0.1")

class configurations:
    
	def __init__(self, product):
		self.product: str = product
		self.config_product: str = CONFIG_PRODUCT
		self.product_check(product)

	def product_check(self, product):
		if product != CONFIG_PRODUCT:
			raise ValueError (f" Invalid Product, this function is only available for {CONFIG_PRODUCT}")

	def init_product_specific(self):
	
		# Product config
		product = self.product
		
		# System Specific Configurations based on product
		ConfigFile = f'{product}FuseFileConfigs.json'
		CORESTRING = 'CORE'
		CORETYPES = {	'GNRAP':{'core':'bigcore','config':'AP', 'maxcores': 180, 'maxlogcores': 132},
							'GNRSP':{'core':'bigcore','config':'SP', 'maxcores': 120, 'maxlogcores': 88}}
		MAXLOGICAL = 44
		MAXPHYSICAL = 60
		classLogical2Physical = {0:0, 1:1, 2:2, 3:3, 4:6, 5:7, 6:8, 7:9, 8:10, 9:13, 10:14, 11:15, 12:16, 13:17, 14:20, 15:21, 16:22, 17:23, 18:24, 19:27, 20:28, 21:29, 22:30, 23:31, 24:34, 25:35, 26:36, 27:37, 28:38, 29:41, 30:42, 31:43, 32:44, 33:45, 34:48, 35:49, 36:50, 37:51, 38:52, 39:55, 40:56, 41:57, 42:58, 43:59}
		physical2ClassLogical = {value: key for key, value in classLogical2Physical.items()}
		phys2colrow= { 0:[0,1], 1:[0,2], 2:[1,1], 3:[1,2], 4:[1,3], 5:[1,4], 6:[1,5], 7:[1,6], 8:[1,7], 9:[2,1], 10:[2,2], 11:[2,3], 12:[2,4], 13:[2,5], 14:[2,6], 15:[2,7], 16:[3,1], 17:[3,2], 18:[3,3], 19:[3,4], 20:[3,5], 21:[3,6], 22:[3,7], 23:[4,1], 24:[4,2], 25:[4,3], 26:[4,4], 27:[4,5], 28:[4,6], 29:[4,7], 30:[5,1], 31:[5,2], 32:[5,3], 33:[5,4], 34:[5,5], 35:[5,6], 36:[5,7], 37:[6,1], 38:[6,2], 39:[6,3], 40:[6,4], 41:[6,5], 42:[6,6], 43:[6,7], 44:[7,1], 45:[7,2], 46:[7,3], 47:[7,4], 48:[7,5], 49:[7,6], 50:[7,7], 51:[8,1], 52:[8,2], 53:[8,3], 54:[8,4], 55:[8,5], 56:[8,6], 57:[8,7], 58:[9,1], 59:[9,2] }
		skip_physical = [4,5,11,12,18,19,25,26,32,33,39,40,46,47,53,54]
		PHY2APICID = [0,2,9,16, 23,1,3,10,17,24,4,11,19,25,5,12,19,26,6,13,20,27,7,14,21,28,8,15,22,29,30,37,44,51,58,31,38,45,52,59,32,39,46,53,33,40,47,54,34, 41,48,55,35,42,49,56,36,43,50,57]

		## Not Used for bigcore
		ClassLog2AtomID = None 
		AtomID2ClassLog = None

		CONFIG = { 'PRODUCT':product,
				'CONFIGFILE': ConfigFile,
				'CORESTRING': CORESTRING,
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

		fuse_instance = ['hwrs_top_rom']

		cfc_voltage_curves = {	'cfc_curve': ['pcode_cfc_vf_voltage_point0','pcode_cfc_vf_voltage_point1','pcode_cfc_vf_voltage_point2','pcode_cfc_vf_voltage_point3','pcode_cfc_vf_voltage_point4','pcode_cfc_vf_voltage_point5'],
						'hdc_curve': ['pcode_hdc_vf_voltage_point0','pcode_hdc_vf_voltage_point1','pcode_hdc_vf_voltage_point2','pcode_hdc_vf_voltage_point3','pcode_hdc_vf_voltage_point4','pcode_hdc_vf_voltage_point5'],

					}
			
		cfc_ratio_curves = {	'cfc_curve': ['pcode_cfc_vf_ratio_point0','pcode_cfc_vf_ratio_point1','pcode_cfc_vf_ratio_point2','pcode_cfc_vf_ratio_point3','pcode_cfc_vf_ratio_point4','pcode_cfc_vf_ratio_point5'],
						'hdc_curve': ['pcode_hdc_vf_ratio_point0','pcode_hdc_vf_ratio_point1','pcode_hdc_vf_ratio_point2','pcode_hdc_vf_ratio_point3','pcode_hdc_vf_ratio_point4','pcode_hdc_vf_ratio_point5'],
						'pstates' : {	'p0':'pcode_sst_pp_0_cfc_p0_ratio', 
										'p1':'pcode_sst_pp_0_cfc_p1_ratio', 
										'pn':'pcode_cfc_pn_ratio', 
										'min':'pcode_cfc_min_ratio'}
					}
		ia_ratio_curves = {	'limits': [f'pcode_sst_pp_##profile##_turbo_ratio_limit_ratios_cdyn_index##idx##_ratio##ratio##'],
						'p1': [f'pcode_sst_pp_##profile##_sse_p1_ratio',f'pcode_sst_pp_##profile##_avx2_p1_ratio',f'pcode_sst_pp_##profile##_avx512_p1_ratio',f'pcode_sst_pp_##profile##_amx_p1_ratio'],
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
			
		fuses_600w_comp = ['pcu.pcode_sst_pp_0_power=0x226','pcu.punit_ptpcioregs_package_power_sku_pkg_min_pwr_fuse=0xa50','pcu.pcode_non_vccin_power=0x300','pcu.pcode_pkg_icc_max_app=0x23f','pcu.pcode_loadline_res=0x4','pcu.pcode_loadline_res_rev2=0x190','pcu.pcode_pkg_icc_max=0x2ee','pcu.pcode_pkg_icc_p1_max=0x2ee']
		fuses_600w_io = ['punit_iosf_sb.pcode_sst_pp_0_power=0x266','punit_iosf_sb.pmsrvr_ptpcioregs_package_power_sku_pkg_min_pwr_fuse=0xa50','punit_iosf_sb.pcode_non_vccin_power=0x300','punit_iosf_sb.pcode_pkg_icc_max_app=0x23f','punit_iosf_sb.pcode_loadline_res=0x4','punit_iosf_sb.pcode_loadline_res_rev2=0x190','punit_iosf_sb.pcode_pkg_icc_max=0x2ee','punit_iosf_sb.pcode_pkg_icc_p1_max=0x2ee']

		htdis_comp = ['scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_fused_ht_dis=0x1', 'pcu.capid_capid0_ht_dis_fuse=0x1','pcu.pcode_lp_disable=0x2','pcu.capid_capid0_max_lp_en=0x1']
		htdis_io = ['punit_iosf_sb.soc_capid_capid0_max_lp_en=0x1','punit_iosf_sb.soc_capid_capid0_ht_dis_fuse=0x1']
		vp2intersect = {	'fast':['sv.socket0.computes.fuses.scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_vp2intersect_dis=0x0'],
							'bs':['scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_vp2intersect_dis=0x0'],}
			
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

		## System 2 Tester and bootscript Initialization data 

		bootscript_data = {	'GNRAP':{'segment':'GNRUCC', 'config':['compute0', 'compute1', 'compute2'], 'compute_config':'x3',},
								'GNRSP':{'segment':'GNRXCC', 'config':['compute0', 'compute1'], 'compute_config':'x2',}}

		# Licence Configuration GNR
		core_license_dict = {'IA':1,'SSE':1,'AVX2':3,'AVX3':5, 'AMX':7}
		license_dict = { 0:"Don't set license",1:"SSE/128",2:"AVX2/256 Light", 3:"AVX2/256 Heavy", 4:"AVX3/512 Light", 5:"AVX3/512 Heavy", 6:"TMUL Light", 7:"TMUL Heavy"}
		core_license_levels = [k for k in core_license_dict.keys()]

		# Special QDF configuration GNR
		qdf600 = ['RVF5']

		# Mesh Configurations GNR
		ate_masks = {
							'GNRAP':{1:'FirstPass', 2:'SecondPass', 3:'ThirdPass', 4:'RowPass1',5:'RowPass2',6:'RowPass3'},
							'GNRSP':{1:'FirstPass', 2:'SecondPass', 3:'RowPass1', 4:'RowPass2'}
							}

		masks_AP = [v for k,v in ate_masks['GNRAP'].items()]
		masks_SP = [v for k,v in ate_masks['GNRSP'].items()]

		ValidClass = {'GNRAP':masks_AP,'GNRSP':masks_SP}
		ValidRows = ['ROW1','ROW2','ROW5','ROW6','ROW7']
		ValidCols = ['COL0','COL1','COL2','COL3','COL4','COL5','COL6','COL7','COL8','COL9']
		customs = ValidRows + ValidCols #['ROW1','ROW2','ROW5','ROW6','ROW7','COL0','COL1','COL2','COL3','COL4','COL5','COL6','COL7','COL8','COL9']
		RigthSide_mask = ['COL5','COL6','COL7','COL8','COL9']
		LeftSide_mask = ['COL0','COL1','COL2','COL3','COL4']

		ate_config = 	{	
							'main':{
									'l1':('\t> 1. ATE pseudo Configuration: '),
									'l1-1':(f'\t\t> GNR UCC: {masks_AP}'),
									'l1-2':(f'\t\t> GNR XCC: {masks_SP}'),
									'l4':('\t> 2. Tile Isolation: Specify the Compute to be used for testing'),
									'l5':('\t> 3. Custom: Mix and Match of Columns and Rows'),
									'l6':('\t> 4. Full Chip')},
							'GNRAP':{
									'l1':('\t> 1. FirstPass: All CDIEs - Columns [0, 3, 6, 9]'),
									'l2':('\t> 2. SecondPass: All CDIEs - Columns [1, 4, 7]'),
									'l3':('\t> 3. ThirdPass: All CDIEs - Columns [2, 5, 8]'),
									'l4':('\t> 4. RowPass1: CDIE0 - Rows [1,2], CDIE1 - Rows [5,6], CDIE2 - Rows [7]:'),
									'l5':('\t> 5. RowPass2: CDIE0 - Rows [5,6], CDIE1 - Rows [7], CDIE2 - Rows [1,2]:'),
									'l6':('\t> 6. RowPass3: CDIE0 - Rows [7], CDIE1 - Rows [1,2], CDIE2 - Rows [5,6]:'),
									'maxrng' : 7},
							'GNRSP':{
									'l1': ('\t> 1. FirstPass: Columns 0, 1, 3, 5, 7 and 9'),
									'l2': ('\t> 2. SecondPass: Columns 0, 2, 4, 6, 8 and 9:'),	
									'l3': ('\t> 3. RowPass1: CDIE0 - Rows [1,2], CDIE1 - Rows [5,6,7]:'),	
									'l4': ('\t> 4. RowPass2: CDIE0 - Rows [5,6,7], CDIE1 - Rows [1,2]:'),		
									'maxrng' : 5
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
									'l1':('\t> 1. Not available for this product'),
									'maxrng': 2},
							}
		
		dis1cpm_dict = {1:None}

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
			}
		
		return FrameworkVars

	def init_framework_features(self):

		# Product config
		product = self.product
		
		FrameworkFeatures = {
							'	debug':					{'default':False,'enabled':True,'disabled_value':False,},
								'targetLogicalCore':	{'default':None,'enabled':True,'disabled_value':None,},
								'targetTile':			{'default':None,'enabled':True,'disabled_value':None,},
								'use_ate_freq':			{'default':True,'enabled':True,'disabled_value':True,},
								'use_ate_volt':			{'default':False,'enabled':True,'disabled_value':False,},
								'flowid':				{'default':1,'enabled':True,'disabled_value':1,},
								'core_freq':			{'default':None,'enabled':True,'disabled_value':None,},
								'mesh_freq':			{'default':None,'enabled':True,'disabled_value':None,},
								'io_freq':				{'default':None,'enabled':True,'disabled_value':None,},
								'license_level':		{'default':None,'enabled':True,'disabled_value':0,},
								'dcf_ratio':			{'default':None,'enabled':True,'disabled_value':None,},
								'stop_after_mrc':		{'default':False,'enabled':True,'disabled_value':False,},
								'boot_postcode':		{'default':False,'enabled':True,'disabled_value':False,},
								'clear_ucode':			{'default':None,'enabled':False,'disabled_value':False,},
								'halt_pcu':				{'default':None,'enabled':False,'disabled_value':False,},
								'dis_acode':			{'default':False,'enabled':True,'disabled_value':False,},
								'dis_ht':				{'default':None,'enabled':True,'disabled_value':False,},
								'dis_2CPM':				{'default':None,'enabled':False,'disabled_value':None,},
								'dis_1CPM':				{'default':None,'enabled':False,'disabled_value':None,},
								'postBootS2T':			{'default':True,'enabled':True,'disabled_value':True,},
								'clusterCheck':			{'default':None,'enabled':True,'disabled_value':None,},
								'lsb':					{'default':False,'enabled':True,'disabled_value':False,},
								'fix_apic':				{'default':None,'enabled':True,'disabled_value':False,},
								'dryrun':				{'default':False,'enabled':True,'disabled_value':False,},
								'fastboot':				{'default':False,'enabled':True,'disabled_value':False,},
								'mlcways':				{'default':None,'enabled':True,'disabled_value':None,},
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
								'extMasks':				{'default':None,'enabled':True,'disabled_value':None,},
								'reg_select':			{'default':None,'enabled':True,'disabled_value':1,},
							}

		return FrameworkFeatures

	def init_dff_data(self):
		
		# Product config
		product = self.product
		
		CORE_FREQ = {# 
				1:[8],
				2:[18], # previuosly 17
				3:[24],
				4:[32],
				5:[36,34,34,33], ## Changed as of TPS507 previously 38,36,34,32
				6:[40,38,32,30], ## Changed as of TPS507 previously 40,38,36,34
				7:[44,42,40,38]
			}
		CORE_CFC_FREQ = {# 
				1:8,
				2:18, ## Changed as of TPS507 previously 18
				3:18,
				4:18, ## Changed as of TPS507 previously 22
				5:20, ## Changed as of TPS507 previously 22
				6:22,
				7:22
			}
		CORE_CFCIO_FREQ = {# 
				1:8,
				2:14,
				3:20,
				4:25,
				5:25,
				6:25,
				7:25
			}
		CFC_FREQ = {# 
				1:[8],
				2:[14],
				3:[18], # Updated for newest F3 values of 18 (Hex 0x12)
				4:[22,21,20,19]  # Updated for newest F4 values of 22 (Hex 0x16)
			}

		HDC_FREQ = {# done - UNCORE_CFCxCOMP_RATIO_4
				1:[8],
				2:[14],
				3:[18], 
				4:[22]  
			}
			
		IO_FREQ = {# 
				1:[8],
				2:[14],
				3:[20],
				4:[24,23,22,21] ## This should be 25?
			}
		CFC_CORE_FREQ = {# 
				1:14,
				2:14,
				3:14,
				4:16,
			}
		HDC_CORE_FREQ = {# 
				1:14,
				2:14,
				3:14,
				4:16,
			}
		CFCIO_CORE_FREQ = {# 
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
		CFC_IO_FREQ = {# 
				1:16,
				2:16,
				3:16,
				4:22,
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
		hdc_max = 4
		core_max = 7
		io_max = 4
			
		#log2Phys10x5 = {0:0, 1:1, 2:2, 3:3, 4:6, 5:7, 6:8, 7:9, 8:10, 9:13, 10:14, 11:15, 12:16, 13:17, 14:20, 15:21, 16:22, 17:23, 18:24, 19:27, 20:28, 21:29, 22:30, 23:31, 24:34, 25:35, 26:36, 27:37, 28:38, 29:41, 30:42, 31:43, 32:44, 33:45, 34:48, 35:49, 36:50, 37:51, 38:52, 39:55, 40:56, 41:57, 42:58, 43:59}
		#Phys2log10x5 = {v:k for k, v in log2Phys10x5.items()}
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
		
