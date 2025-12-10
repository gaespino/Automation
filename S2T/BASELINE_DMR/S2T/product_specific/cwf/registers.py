"""
Class register data

REV 0.1 --
Code migration to product specific features

"""

import os
import json 
from dataclasses import dataclass

CONFIG_PRODUCT = 'CWF'
MESH_DICT = "s2tmeshdata.json"
SLICE_DICT = "s2tregdata.json"
CRDICT = "crdict.json"


print (f"Loading CLASS registers data for {CONFIG_PRODUCT} || REV 0.1")

@dataclass
class registers:
      
    # Read S2T register configuration files
    @staticmethod
    def regs_dict(jfile, dictname = 's2t_reg', folder = 'RegFiles'):
        ## Change filename accordingly, the name needs to be changed here and inside CommonRingCmds Class
        #jfile = "s2tregdata.json"
        scriptHome = os.path.dirname(os.path.realpath(__file__))

        o_path = os.path.join(scriptHome, folder)
        
        j_file = os.path.join(o_path, jfile)
            
        with open (j_file) as regfile:
            configdata = json.load(regfile)
            jsondict = configdata[dictname]

        return jsondict

    @staticmethod
    def mesh_crs_min():
        
        _mesh_crs_min = {
        "al_cr_arch_fuses": 0x401, # 0x400# FMA5_DIS ( should be fixed in new regression) 
        "thread0.al_cr_git_deallocmask": 0xfff3, #  Not found
        "thread1.al_cr_git_deallocmask": 0xfffc, #  Not found
        "bpu1_cr_debug": 0xa8000, #system has 0xa8400 --> dis_lsd_start_end (10:10) -- Invalidate the Start/End markers for the LSD state machine
        "core_cr_arch_fuses": 0x401, #0xbe100859, # 0x00000000 : residue_cheking_dis (04:04) -- Disable residue checking for SKL server. 000000 : fma5_dis (10:10) -- Disable allocation to FMA5 (do not use server-core FMA5 hw)
        "core_cr_iq_crmode": 0x0, #0x20244, # system = 0x200
        "core_cr_parity_rc": 0x2003, #0xf7D,  # system = 0xFFF
        }

        return _mesh_crs_min

    @staticmethod
    def slice_crs_min():
        _slice_crs_min = {

        # good
        # "ag_cr_ia32_cr_efer": 0x501 #  sce (00:00) -- System Call Enable Bit
        # "al_cr_arch_fuses": 0x0,
        "al_cr_git_deallocmask": 0xfffc,
        # "al_cr_testtail": 0x144,  # Outputs.  NOT NEEDED
        #  "bac_cr_ia32_cr_efer": 0x400, #Not needed as this is an output
        "bpu1_cr_debug": 0xa8000, #system has 0xa8400 --> dis_lsd_start_end (10:10) -- Invalidate the Start/End markers for the LSD state machine
        "core_cr_arch_fuses": 0xbe100859, # System has 0xbe100849  # delta 0x00000000 : residue_cheking_dis (04:04) -- Disable residue checking for SKL server
        # "core_cr_ia32_cr_efer": 0x501, # set by code
        "core_cr_iq_crmode": 0x200, # Need to look into this
        # "core_cr_parity_rc": 0xfff, # system already has 0xFFF
        "core_cr_pebs_frontend": 0x800,
        "core_cr_prefetch_ctl": 0x3,
        "ctap_cr_debug_counter_0": 0x200,
        # good

        # PROBLEMS: 
        #"ctap_cr_tap_config": 0x70101de7, # Slice mode. Cant do all of these
        "ctap_cr_tap_config": 0x22,  # Disable prefetchers and power gating
        ## -- good
        "dcu_cr_arch_fuses": 0xc000000,
        "dcu_cr_defeature": 0x261d80030,
        "dcu_cr_uarch": 0x3fc1b4e,
        ## -- good

        ## -- abajo
        # "dsbfe_cr_sou_recl_debug": 0x20800,
        ## -- arriba

        # good
        "ieslow_cr_arch_fuses": 0x8,
        "ieslow_cr_vmcs_pla_ctl": 0x7d97,
        # good


        ## -- good
        "ifu_cr_debug_mode": 0x124000,
        "ifu_cr_debug_mode3": 0x870,
        "iq_cr_arch_fuses": 0x100801,
        ## -- good

        ## --- good gold
        "iq_cr_debug": 0xe00,
        ## "iq_cr_iq_crmode": 0x200,  THIS NEEDS TO  BE LOOKED INTO as it has a lot of enables/disables
        ## --- good gold

        ## --- good gold
        "mi_cr_arch_fuses": 0x800,
        ## --- good gold

        ## ---- Abajo
        #problem
        # mi_cr_parity_rc": 0x843,
        ## --- arriba


        ## --- abajo
        # problem
        #"ml2_cr_ml_cache_control": 0x187fff3,
        ## ---- Arriba

        ## --- good gold
        "ml2_cr_xq_debug": 0x2a040000,
        "ml2_cr_xq_debug2": 0x40045400,
        ## --- good gold

        ## --- good gold
        "ml3_cr_mlc_pwr_mgmt_timer_ctrl": 0x4,
        "ml3_cr_opd_control": 0x8140,
        ## --- good gold

        ## --- good
        "ml5_cr_mlc_iccp_config": 0xaa02,
        "ml5_cr_mlc_iccp_status": 0x53ee,

        "ml6_cr_pref_debug": 0x4213,
        "ml6_cr_pref_dpt": 0x42f53792,
        "ml6_cr_prefetch_ctl": 0x3,
        "ms_cr_defeature": 0x2cb00080,

        "ms_cr_hw_mbb": 0x1c0000400002c0f3,
        "ms_cr_ia32_cr_efer": 0x1,
        "ms_cr_mswrms_mbb": 0x1004,
        "ms_cr_pebs_frontend": 0x800,
        "ms_cr_uarch_cov": 0xbc3,
        ## --- good




        # good

        "pmh_cr_arch_fuses": 0xb0000000,
        "pmh_cr_asid_result": 0xc008,
        "pmh_cr_ia32_cr_efer": 0x400,

        #---- below this
        #"pmh_cr_mtrrdefault": 0x806, # problematic
        #---- above this

        "rat_cr_defeature": 0x0,
        "rat_cr_last_call_uip": 0x62a1,
        "rat_cr_psegbits": 0x7,
        "rat_cr_pwrdn_ovrd": 0xc0,
        "rat_cr_tagword": 0xff,


        "rob1_cr_crdalstall": 0x8,
        "rob1_cr_crdctrl": 0x20,
        "rob1_cr_event_info": 0x4e3818,
        "rob1_cr_event_inhibit": 0x300800,
        "rob1_cr_ia32_cr_efer": 0x400,
        "rob1_cr_parity_rc": 0x7bf,
        "rob1_cr_rs_pvp2_ctl_1": 0x7f6a35d,

        "rs_cr_rs_dft": 0x0,

        "scp_cr_arch_fuses": 0x8000058,
        "scp_cr_core_llc_flush_cfg": 0x0,
        "scp_cr_core_scoped_misc_flags": 0x0,
        "scp_cr_flow_details": 0x880000,
        "scp_cr_misc_flags": 0x80,
        "scp_cr_target_sleep_state": 0x20101,
        # good
        }
        return _slice_crs_min

    @staticmethod
    def cr_dict():
        """
        Load register dictionary from crdict.json file.
        Converts desired_value from hex string to integer.
        Filters out registers with N/A values.
        """
        # Registers with N/A values (incomplete data)
        na_list = [
            "brkptfilctl",
            "brkptfilstate",
            "brkptfiltrignow",
            "vdmpg",
            "uclkdcm",
            "ulcppulse",
            "uelcpload",
            "ulcpload",
            "ljpll_calib_config",
            "ljpll_tapconfig",
            "ljpll_flltapconfig",
            "ljpll_odcs_tapconfig",
            "fsmisrctl",
            "scanbicfg",
            "scanbiresult",
            "tap2pmasurv",
            "atomipidcode",
            "cpubist",
            "readpdrlt1",
            "readpdrht1",
            "readpdrht0",
            "brkpttrignow",
            "brkptctl0",
            "mbpinsynctrig",
            "brkptctl1",
            "brkptctl2",
            "crbusgo64",
            "crbusnogo64",
            "clkcompstrap",
            "stopclk",
            "ondiedroop",
            "aryfrz",
            "brkptinfrctl",
            "brkptinfrstate",
            "brkptinfrtrignow",
            "viewdigital",
            "bilbocfg",
            "bilboext",
            "tap2vrc",
            "tap2vrcstrap",
            "ccmctl",
            "ifdimen",
            "tap2crislvstrap",
            "tap2crislvpll",
            "tap2crislvplldetmode",
            "tap2crislvdts",
            "tap2crislvdtsdetmode",
            "indiectl",
            "lcpctl",
            "centrallcp",
            "iosfsbovrgo",
            "iosfsbovrrsp",
            "iosfsbovrnogo",
            "detmodes",
            "stfstrap",
            "epbistcfg",
            "epbiststatus",
            "stfcfg",
            "tap2stf",
            "dat",
            "scandumpuclk",
            "scandumpxclk",
            "fusacfg",
            "fusastatus",
            "brkptstate0",
            "brkptstate1",
            "brkptstate2",
            "fusaaddr",
            "scanclkfrzinfr",
            "scancfg",
            "atpgcfg",
            "scanclkfrz",
            "scancapttrig",
            "udscreg",
            "sib_bus_scmisr_sib_reg",
            "sib_bus_scmask_sib_reg",
            "sib_bus_sccfg_sib_reg",
            "sib_c0_iec_scmisr_sib_reg",
            "sib_c0_iec_scmask_sib_reg",
            "sib_c0_iec_sccfg_sib_reg",
            "sib_c0_rsv_scmisr_sib_reg",
            "sib_c0_rsv_scmask_sib_reg",
            "sib_c0_rsv_sccfg_sib_reg",
            "sib_c0_arr_scmisr_sib_reg",
            "sib_c0_arr_scmask_sib_reg",
            "sib_c0_arr_sccfg_sib_reg",
            "sib_c0_fec_scmisr_sib_reg",
            "sib_c0_fec_scmask_sib_reg",
            "sib_c0_fec_sccfg_sib_reg",
            "sib_c0_fpa_scmisr_sib_reg",
            "sib_c0_fpa_scmask_sib_reg",
            "sib_c0_fpa_sccfg_sib_reg",
            "sib_c0_mec_scmisr_sib_reg",
            "sib_c0_mec_scmask_sib_reg",
            "sib_c0_mec_sccfg_sib_reg"
        ]
        
        json_data = registers.regs_dict(jfile=CRDICT, dictname='cr_dict')
        _crdict = {
            key: int(reg_info.get('desired_value', '0x0'), 16)
            for key, reg_info in json_data.items()
            if key not in na_list
        }
        return _crdict

    @staticmethod
    def s2t_reg(skip_keys=None):
        """
        Load register dictionary from s2tregdata.json file.
        
        Args:
            skip_keys (list, optional): List of register keys to skip/exclude from the dictionary.
                                       Defaults to None (no keys skipped).
        
        Returns:
            dict: Dictionary with register names as keys and their desired_values (converted to int).
        
        Example:
            # Load all registers
            regs = registers.s2t_reg()
            
            # Load registers but skip specific ones
            regs = registers.s2t_reg(skip_keys=['ic_cr_mci_addr', 'mec_cr_mci_ctl'])
        """
        # Registers: Not working / breaks the system
        not_ok_list = [
                        "bus_cr_pic_tsc",
                        "clpu_cr_misc0",
                        "fpc_cr_scmisr_result_0",
                        "ic_cr_fec_cr_scmisr_result_0",
                        "ic_cr_ic_post_si_debug_data_4ucode",
                        "ic_cr_poison_go_err_pa",
                        "iec_cr_scmisr_result_0",
                        "iec_cr_scmisr_result_1",
                        "ms_cr_datout",
                        "ms_cr_last_taken_patch",
                        "thread0.arr_cr_ret_status",
                        "thread0.arr_cr_retire_uip",
                        "thread0.arr_cr_scmisr_result_0",
                        "thread0.arr_cr_tagword",
                        "thread0.arr_cr_xstate_trk_set_and_status",
                        "thread0.bnl_cr_icectlpmr",
                        "thread0.bus_cr_pending_set_and_status",
                        "thread0.bus_cr_pic_timer_status",
                        "thread0.bus_cr_ucode_pla_data_0",
                        "thread0.bus_cr_ucode_pla_data_1",
                        "thread0.ebl_cr_lt_doorbell",
                        "thread0.mec_cr_scmisr_result_0",
                        "thread0.pic_cr_cross_core_communication_mycore",
                        "thread0.pic_cr_pic_timer_current_count_reg",
                        "thread0.pic_cr_queue_status",
                        "thread0.pic_cr_status",
                        "thread0.pic_cr_tpr_update",
                        "thread0.pmg_cr_pst_acnt",
                        "thread0.pmg_cr_pst_mcnt",
                        "thread0.pmg_cr_pst_pcnt",
                        # Registers: Different in SLC config / But are not ok and breaks the system
                        "ag2_cr_tdx_pa_mask",
                        "bus_cr_comparator_error",
                        "bus_cr_dlsm_set_and_status",
                        "bus_cr_dlsm_tracker",
                        "bus_cr_dynamic_lockstep_ctl",
                        "bus_cr_pic_core_pm_state_status",
                        "pmh_cr_c6dramrr_base",
                        "pmh_cr_c6dramrr_mask",
                        "pmh_cr_emrr_base",
                        "pmh_cr_emrr_mask",
                        "pmh_cr_emxrr_base",
                        "pmh_cr_emxrr_mask",
                        "pmh_cr_seamrr_base",
                        "pmh_cr_tdx_pa_mask",
                        "pmh_cr_umrr_base",
                        "pmh_cr_umrr_mask",
                        "thread0.arr1_cr_cr0",
                        "thread0.arr_cr_lbr_index",
                        "thread0.bnl_cr_pppe",
                        "thread0.fpc_cr_event_info",
                        "thread0.ia32_cr_perf_global_ctrl_preserve_alias",
                        "thread0.ic_cr_probe_mode_status",
                        "ia32_cr_uarch_misc_ctl", # From last list included in CRDICT
                        "thread0.virt_cr_pppe_event_status" # From last list included in CRDICT
                    ]
        
        # Registers: Issues with Raritan + Slow / Bad Performance
        raritan_and_slow_list = [
                        # Issues with Raritan
                        "ia32_cr_smrr_physbase",
                        "ia32_cr_smrr_physmask",
                        "thread0.ag1_cr_efer",
                        "thread0.arr1_cr_sys_flags",
                        "thread0.bnl_cr_cs_l_d_bits",
                        "thread0.bus_cr_pcpins",
                        "thread0.ia32_cr_efer",
                        "thread0.ms_cr_fast_branch_ucode",
                        "thread0.x86_cr_apicbase",
                        "thread0.x86_cr_cr0",
                        "thread0.x86_cr_cr3",
                        "x86_cr_mtrrphysbase0",
                        "x86_cr_mtrrphysbase1",
                        "x86_cr_mtrrphysbase2",
                        "x86_cr_mtrrphysmask0",
                        "x86_cr_mtrrphysmask1",
                        "x86_cr_mtrrphysmask2",
                        # Slow / Bad Performance after applying
                        "thread0.ag2_cr_cr0",
                        "thread0.id_cr_debug_defeature",
                        "thread0.virt_cr_vmx_control" ## Last List -- added in CRDICT
                    ]

        # Initialize skip list
        if skip_keys is None:
            skip_keys = not_ok_list + raritan_and_slow_list
        
        # Load the JSON data using the existing regs_dict method
        json_data = registers.regs_dict(jfile=SLICE_DICT, dictname='s2t_reg')
        
        # Build the dictionary from JSON data using desired_value
        _s2t_reg = {
            key: int(reg_info.get('desired_value', '0x0'), 16)
            for key, reg_info in json_data.items()
            if key not in skip_keys
        }
        
        return _s2t_reg

    @staticmethod
    def slice_dict():
        _s2t_dict = registers.regs_dict(jfile = SLICE_DICT)
        return _s2t_dict

    @staticmethod
    def mesh_dict():
        _mesh_dict = registers.regs_dict(dictname='mesh_crs', jfile = MESH_DICT)
        return _mesh_dict

