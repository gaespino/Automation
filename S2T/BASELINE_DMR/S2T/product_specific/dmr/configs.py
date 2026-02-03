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
		print(f' DMR Product configuration: {chop}')
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
		print(f' DMR Product configuration: {variant}')
		return variant

	def product_check(self, product):
		if product not in CONFIG_PRODUCT:
			raise ValueError (f" Invalid Product, this function is only available for {CONFIG_PRODUCT}")

	def _get_cbb_config(self, sv):
		return sv.socket0.cbbs.name

	def init_product_specific(self, sv=None):

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

	def init_product_fuses(self, sv=None):

		# Product config
		product = self.product

		# Fuses Configurations below required in some parts of the logic to be moved to a product specific
		pseudoConfigs =f'{product}MasksConfig.json'
		DebugMasks = f'{product}MasksDebug.json'
		ConfigFile = f'{product}FuseFileConfigs.json'
		BurnInFuses = f'{product}BurnInFuses.json'
		fuse_instance = ['base.fuses']
		cfc_voltage_curves = {	'cfc_curve': ['fw_fuses_cfc#cfcs#_vf_voltage_#points#'],
								'cfcio_curve': ['pcode_cfc#domain#_vf_voltage_point#points#'],
						#'hdc_curve': ['pcode_hdc_vf_voltage_point0','pcode_hdc_vf_voltage_point1','pcode_hdc_vf_voltage_point2','pcode_hdc_vf_voltage_point3','pcode_hdc_vf_voltage_point4','pcode_hdc_vf_voltage_point5'],
						'hdc_curve': [], # no HDC
						'cfcs' : [0,1,2,3,4,5,6,7],
      					'points' : [0,1,2,3,4,5],
						'cfcio_domains' : ['io','mem']
					}

		cfc_ratio_curves = {'cfc_curve': ['fw_fuses_cfc_vf_ratio_0','fw_fuses_cfc_vf_ratio_1','fw_fuses_cfc_vf_ratio_2','fw_fuses_cfc_vf_ratio_3','fw_fuses_cfc_vf_ratio_4','fw_fuses_cfc_vf_ratio_5'],
						'cfcio_curve': ['pcode_cfc#domain#_vf_ratio_point0','pcode_cfc#domain#_vf_ratio_point1','pcode_cfc#domain#_vf_ratio_point2','pcode_cfc#domain#_vf_ratio_point3','pcode_cfc#domain#_vf_ratio_point4','pcode_cfc#domain#_vf_ratio_point5'],
                        'hdc_curve': [], # no HDC
						'pstates' : {	'p0':'fw_fuses_sst_pp_0_cfc_p0_ratio',
										'p1':'fw_fuses_sst_pp_0_cfc_p1_ratio',
										'pn':None,
										'min':'fw_fuses_cfc_min_ratio'},
						'pstates_io' : { 'p0':'pcode_sst_pp_0_cfc#domain#_p0_ratio',
                					'p1':'pcode_sst_pp_0_cfc#domain#_p1_ratio',
									'pn':None,
									'min':'pcode_cfc#domain#_min_ratio'},
						'cfcio_domains' : ['io','mem'],
					}
		ia_ratio_curves = {	'limits': ['fw_fuses_sst_pp_#ppfs#_turbo_ratio_limit_ratios_cdyn_index#idxs#_ratio#ratios#'],
						'p1': ['fw_fuses_sst_pp_#ppfs#_sse_p1_ratio', 'fw_fuses_sst_pp_#ppfs#_amx_p1_ratio', 'fw_fuses_sst_pp_#ppfs#_avx2_p1_ratio', 'fw_fuses_sst_pp_#ppfs#_avx512_p1_ratio'],
						'vf_curve': ['core#cores#_fuse.core_fuse_core_fuse_acode_ia_base_vf_ratio_#vfpnt#'],
						'vf_deltas': ['core#cores#_fuse.core_fuse_core_fuse_acode_ia_delta_idx#vfidx#_vf_voltage_#vfpnt#'],
						'pstates' : {	'p0':['core#cores#_fuse.core_fuse_core_fuse_acode_core_ia_p0_ratio', 'core#cores#_fuse.core_fuse_core_fuse_acode_core_ia_p0_ratio_avx256','core#cores#_fuse.core_fuse_core_fuse_acode_core_ia_p0_ratio_avx512', 'core#cores#_fuse.core_fuse_core_fuse_acode_core_ia_p0_ratio_tmul'],
										'pn':'fw_fuses_ia_pn_ratio',
										'min':'fw_fuses_ia_min_ratio',
										'boot':'fw_fuses_ia_boot_ratio'

									},

					}

		ia_ratios_config = {
									'ppfs' : [0,1,2,3,4],
									'idxs' : [0,1,2,3,4,5],
									'ratios': [0,1,2,3,4,5,6,7],
									'vfidx' :  [1,2,3,4],
									'vfpnt' :  [0,1,2,3,4,5,6,7,8,9,10,11],
                					'cores' : [0,1,2,3,4,5,6,7],
                     				'fusetype': {'base':['pn','p1','min','boot'],'top':['p0','vf_curve', 'vf_deltas']}
									}

		ia_voltage_curves = {	'vf_curve': ['core#cores#_fuse.core_fuse_core_fuse_acode_ia_base_vf_voltage_#vfpnt#'],
								'mlc_curve': [], # WIP
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

	def init_framework_vars(self, sv=None):

		# Product config
		product = self.product

		# Path of All S2T scripts
		BASE_PATH = 'users.THR.dmr_debug_utilities'

		## System 2 Tester and bootscript Initialization data
		bootscript_data = {	'DMR_CLTAP':{'segment':'DMRUCC','config':self._get_cbb_config(sv), 'compute_config':self._get_chop(sv),},
								'DMR_CLTSP':{'segment':'DMRHDCC','config':['cbb0'], 'compute_config':'x1',}} # Holder for SP always x1

		# Licence Configuration CWF
		core_license_dict = {'IA':1,'SSE':1,'AVX2':2,'AVX3':3, 'AMX':4}
		license_dict = { 0:"Don't set license",1:"SSE/128",2:"AVX2/256 Heavy", 3:"AVX3/512 Heavy", 4:"TMUL Heavy"}
		core_license_levels = [k for k in core_license_dict.keys()]

		# Special QDF configuration CWF
		qdf600 = ['']

		# Mesh Configurations CWF
		ate_masks = 	{
							'DMR_CLTAP':{1:'Computes0', 2:'Computes1',3:'Computes2', 4:'Computes3', 5:'Computes123', 6:'Computes023', 7:'Computes013', 8:'Computes012'},
							'DMR_CLTSP':{1:'Computes0', 2:'Computes1',3:'Computes2', 4:'Computes3', 5:'Computes123', 6:'Computes023', 7:'Computes013', 8:'Computes012'}
							}
		masks_AP = [v for k,v in ate_masks['DMR_CLTAP'].items()]
		masks_SP = [v for k,v in ate_masks['DMR_CLTSP'].items()]

		ValidClass = {'DMR_CLTAP':masks_AP,'DMR_CLTSP':masks_SP}

		ValidRows = ['ROW0','ROW1','ROW2','ROW3','ROW4','ROW5','ROW6','ROW7']
		ValidCols = []
		customs = ValidRows + ValidCols#['ROW5','ROW6','ROW7','COL1','COL2','COL3','COL4','COL5','COL6','COL7','COL8']
		RigthSide_mask = []
		LeftSide_mask = []

		ate_config = 	{
							'main':{
									'l1':('\t> 1. ATE pseudo Configuration: '),
									'l1-1':(f'\t\t> DMR UCC (AP): {masks_AP}'),
									'l1-2':(f'\t\t> DMR XCC (SP): {masks_SP} -- Not ready for testing'),
									'l4':('\t> 2. Tile Isolation: Specify the CBB to be used for testing'),
									'l5':('\t> 3. Custom: Mix and Match of Rows (Use consecutive rows only)'),
									'l6':('\t> 4. Full Chip')},
							'DMR_CLTAP':{
									'l1':('\t> 1. Compute0: Enables compute0 on al CBBs'),
									'l2':('\t> 2. Compute1: Enables compute1 on al CBBs'),
									'l3':('\t> 2. Compute2: Enables compute2 on al CBBs'),
									'l4':('\t> 3. Compute3: Enables compute3 on al CBBs'),
									'l5':('\t> 4. Remove Compute0: Disables compute0 on al CBBs'),
									'l6':('\t> 5. Remove Compute1: Disables compute1 on al CBBs'),
         							'l7':('\t> 6. Remove Compute2: Disables compute2 on al CBBs'),
									'l8':('\t> 7. Remove Compute3: Disables compute3 on al CBBs'),
									'maxrng' : 9},
							'DMR_CLTSP':{
									'l1': ('\t> 1. FirstPass: Full Chip -- No need for masking on SP'),	## Placeholder
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

	def init_framework_features(self, sv=None):

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
							'license_level':		{'default':None,'enabled':True,'disabled_value':None,},
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
							'fastboot':				{'default':False,'enabled':False,'disabled_value':False,}, # Ned to revisit
							'mlcways':				{'default':None,'enabled':False,'disabled_value':False,},
							'ppvc_fuses':			{'default':None,'enabled':True,'disabled_value':None,},
							'custom_volt':			{'default':None,'enabled':True,'disabled_value':None,},
							'vbumps_volt':			{'default':None,'enabled':True,'disabled_value':None,},
							'reset_start':			{'default':None,'enabled':True,'disabled_value':None,},
							'check_bios':			{'default':None,'enabled':True,'disabled_value':None,},
							'mesh_cfc_volt':		{'default':None,'enabled':True,'disabled_value':None,},
							'mesh_hdc_volt':		{'default':None,'enabled':False,'disabled_value':None,},
							'io_cfc_volt':			{'default':None,'enabled':True,'disabled_value':None,},
							'ddrd_volt':			{'default':None,'enabled':True,'disabled_value':None,},
							'ddra_volt':			{'default':None,'enabled':True,'disabled_value':None,},
							'core_volt':			{'default':None,'enabled':True,'disabled_value':None,},
							'core_mlc_volt':		{'default':None,'enabled':True,'disabled_value':None,},
							'u600w':				{'default':None,'enabled':False,'disabled_value':None,},
							'extMasks':				{'default':None,'enabled':True,'disabled_value':None},
							'reg_select':			{'default':None,'enabled':False,'disabled_value':1,}
							}

		return FrameworkFeatures

	def init_dff_data(self, sv=None):

		# Product config
		product = self.product

		CORE_FREQ = {# done - CORE_SSE_HDC_RATIO_6
				1:[8],
				2:[14],
				3:[19],
				4:[24],
				5:[34, 32, 31, 30],
				6:[38, 36, 34, 32],
				7:[38, 36, 34, 32],
			}
		CORE_CFC_FREQ = {# done - UNCORE_CFCxCOMP_RATIO_SAFE - Jose Zuñiga recommends to use the safe values
				1:8,
				2:8,
				3:8,
				4:8,
				5:8,
				6:8,
				7:8
			}
		CORE_CFCIO_FREQ = {# done - UNCORE_CFCxIO_RATIO_SAFE - Jose Zuñiga recommends to use the safe values
				1:8,
				2:8,
				3:8,
				4:8,
				5:8,
				6:8,
				7:8
			}

		CFC_FREQ = {# done - UNCORE_CFCxCOMP_RATIO_4
				1:[8],
				2:[14],
				3:[17],
				4:[27]
			}

		MEM_FREQ = {# done - UNCORE_CFCxCOMP_RATIO_4
				1:[8],
				2:[16],
				3:[20],
				4:[21]
			}

		HDC_FREQ = {# done - UNCORE_CFCxCOMP_RATIO_4  -- NOT USED IN DMR
				1:[8],
				2:[16],
				3:[22],
				4:[26],
				5:[28],
				6:[32, 31, 30, 29]
			}

		MLC_FREQ = {# done - UNCORE_CFCxCOMP_RATIO_4  --
				1:[8],
				2:[14],
				3:[19],
				4:[24],
				5:[34, 32, 31, 30],
				6:[38, 36, 34, 32],
				7:[38, 36, 34, 32],
			}

		IO_FREQ = {# done - UNCORE_CFCxIO_RATIO
				1:[8],
				2:[16],
				3:[20],
				4:[21]
			}

		CFC_CORE_FREQ = {# done - CORE_SSE_HDC_RATIO_SAFE -
				1:8,
				2:8,
				3:8,
				4:8,
			}
		HDC_CORE_FREQ = {# done - CORE_SSE_HDC_RATIO_SAFE -
				1:8,
				2:8,
				3:8,
				4:8,
				5:8,
				6:8,
			}

		CFCIO_CORE_FREQ = {# done - CORE_SSE_HDC_RATIO_SAFE - -
				1:8,
				2:8,
				3:8,
				4:8,
			}

		MEM_CORE_FREQ = {# done - CORE_SSE_HDC_RATIO_SAFE - -
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
				2:16,
				3:20,
				4:21,
			}

		CORE_HDC_CFC_FREQ = {# Not used
				1:8,
				2:8,
				3:8,
				4:8,
			}

		#FivrCondition	All_Safe_RST_PKG
		All_Safe_RST_PKG = {# Safe Voltages
				'VCORE_RST':0.9,
				'VCCRING_RST':0.90,
				'VCCC2IA_RST':0.90,
				'VCCMLC_RST':0.90,
				'VCCCFCMEM_RST':0.85,
				'VCCCFCIO_RST':0.83,
				'VCCFIXDIG_E_RST':0.85,
				'VCCFIXDIG_W_RST':0.85,
				'VCCFIXDIG_MIO_1_RST':0.85,
				'VCCFIXDIG_MIO_2_RST':0.85,
				'VCCFIXDIG_MIO_3_RST':0.85,
				'VCCFIXDIG_MIO_4_RST':0.85,
				'VCCUCIE_NE_RST':0.90,
				'VCCUCIE_NW_RST':0.90,
				'VCCUCIE_SE_RST':0.90,
				'VCCUCIE_SW_RST':0.90,
			}

		#FivrCondition	All_Safe_RST_CDie
		All_Safe_CBB = {# Safe Voltages
				'VCORE_RST':0.90,
				'VCCRING_RST':0.90,
				'VCCC2IA_RST':0.90,
				'VCCMLC_RST':0.90,
			}

		cfc_max = 4
		hdc_max = 7
		core_max = 7
		io_max = 4
		mem_max = 4
		mlc_max = 7
		max_mlc_volt_per_cbb = 4

		wsdl_url = "http://mfglabdffsvc.intel.com/MDODFFWcf/DFFSVC.svc?wsdl"

		DFF_DATA_INIT = {
								'CORE_FREQ':CORE_FREQ,
								'CORE_CFC_FREQ': CORE_CFC_FREQ,
								'CORE_CFCIO_FREQ': CORE_CFCIO_FREQ,
								'CFC_FREQ': CFC_FREQ,
								'HDC_FREQ': HDC_FREQ,
								'MLC_FREQ': MLC_FREQ,
								'IO_FREQ': IO_FREQ,
								'MEM_FREQ': MEM_FREQ,
								'CFC_CORE_FREQ': CFC_CORE_FREQ,
								'HDC_CORE_FREQ': HDC_CORE_FREQ,
								'CFCIO_CORE_FREQ': CFCIO_CORE_FREQ,
								'MEM_CORE_FREQ': MEM_CORE_FREQ,
								'IO_HDC_FREQ': IO_HDC_FREQ,
								'CFC_IO_FREQ': CFC_IO_FREQ,
								'CORE_HDC_CFC_FREQ': CORE_HDC_CFC_FREQ,
								'All_Safe_RST_PKG': All_Safe_RST_PKG,
								'All_Safe_CBB': All_Safe_CBB,
								'cfc_max': cfc_max,
								'hdc_max': hdc_max,
								'core_max': core_max,
								'io_max': io_max,
								'mem_max': mem_max,
								'mlc_max': mlc_max,
								'max_mlc_volt_per_cbb': max_mlc_volt_per_cbb,
								'wsdl_url': wsdl_url,
								}

		return DFF_DATA_INIT


