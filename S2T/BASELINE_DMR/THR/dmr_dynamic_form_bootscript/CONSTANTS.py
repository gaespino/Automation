class Constants:
    MESSAGE_TYPE_ERROR = "ERROR"
    MESSAGE_TYPE_INFO = "INFO"
    MESSAGE_TYPE_WARNING = "WARNING"

    FIELD_PROPERTY_REQUIRED = "required"
    FIELD_PROPERTY_TYPE = "type"


    COMBOBOX_BOOT_TYPE_DEFAULT_OPTION = "Bootscript"
    COMBOBOX_BOOT_TYPE_BOOTSCRIPT = "Bootscript"
    COMBOBOX_BOOT_TYPE_OPTIONS = ["Bootscript"]

    JSON_CONFIG_KEY_BOOTSCRIPT_PARAMETERS="bootscript_parameters"

    FRAME_TITLE_BOOT_TYPE = "Boot Type"
    FRAME_TITLE_BOOTSCRIPT_PARAMETERS = "Bootscript Parameters"
    FRAME_TITLE_RECIPES = "Recipes"
    FRAME_TITLE_BOOT_MAIN = "Boot"

    DEFAULT_DESTINATION_JSON_FILES_PATH = r"\\amr.corp.intel.com\ec\proj\mdl\cr\prod\hdmx_intel\engineering\dev\team_thr\dmr_thr_tools\dmr_dynamic_form_bootscript"

    BOOTSCRIPT_ALLOWED_PROJECT_ARGS = ['allmc_mode', 'bypass_power_check', 'cdie_bgr_wa', 'compute_config', 'compute_s3m_fw_bypass_0', 'dfxagg_wa', 'disable_unit_recipe', 'dump_fuse', 'dynamic_fuse_inject', 'emulation', 'enable_efi_break', 'enable_fivr_checks', 'enable_fuse_checks', 'enable_gpsb_checks', 'enable_pll_checks', 'enable_pm', 'enable_reset_break', 'enable_reset_target', 'enable_screening', 'enable_strap_checks', 'exit_on_mca', 'fast_boot', 'fivr_wa', 'force_pre_unit_fuse_file', 'force_static_fuse_apply', 'fuse_files', 'fuse_offload_only', 'fuse_str', 'fused_unit', 'hvm_mode', 'ia_core_disable', 'ia_core_disable_logical', 'ignore_bkc', 'ignore_security_straps', 'initpwrcycle', 'io_primary_s3m_fw_bypass_0', 'io_secondary_s3m_fw_bypass_0', 'itp_reconnect', 'llc_slice_disable', 'llc_slice_disable_logical', 'manual_fivr_ramp', 'pcode_lip', 'phase_2_delay', 'platform', 'postcode_breakpoint', 'ppv_mode', 'punit_wa', 'pwrgoodbaudrate', 'pwrgoodcheck', 'pwrgoodcomport', 'pwrgooddelay', 'pwrgoodhost', 'pwrgoodmethod', 'pwrgoodport', 'pwrgoodpwd', 'pwrgooduser', 'pwrgoodxml', 'qdf_ovrd', 's3m_bypass', 's3m_bypass_case_compute', 's3m_bypass_case_primary', 's3m_bypass_case_secondary', 's3m_cpld_ecc_wa', 's3m_debug_cfr', 's3m_fw_bypass_0', 's3m_fw_bypass_1', 's3m_fw_bypass_2', 's3m_hw_bypass', 's3m_production_fw', 's3m_redo_fuse_override', 's3m_rom_bypass_file', 's3m_tap_fw_bypass_0', 's3m_tap_fw_bypass_2', 's3m_unsigned_patch', 'segment', 'skip_bkc_check', 'static_fuse_files', 'stepping', 'strict', 'stub', 'tap_delay', 'targsim', 'user_pwrgoodmethod', 'warm_postcode_breakpoint', 'warm_reset_timeout']

    BOOTSCRIPT_DEFAULT_ARGUMENTS = {}

    DEFAULT_PARAMETER_THR_DINAMYC_INJECTION_NAME = "thr_dynamic_injections"

    VOLTAGE_BUMP_TYPE = "voltage_bump"
    OFFSET_LABEL = "offset"
    FUSE_OVERRIDE_TYPE = "fuse_override"
    NEW_VALUE_LABEL = "new_value"

    POWER_DOWN_REGISTERS = [
        "cbbs.base.ccf_pmsb_envs.clr_pmsb_top.pma_regs_cbos.misc_cfg.pwrdn_ovrd=0x1",
        "cbbs.base.i_ccf_envs.cbo_dtf_obs_enc_regss.dso_cfg_dtf_src_config_reg.pwrdn_ovrd=0x1",
        "cbbs.base.i_ccf_envs.cfi_obss.rx_dso.dso_cfg_dtf_src_config_reg.pwrdn_ovrd=0x1",
        "cbbs.base.i_ccf_envs.cfi_obss.tx_dso.dso_cfg_dtf_src_config_reg.pwrdn_ovrd=0x1",
        "cbbs.base.i_ccf_envs.egresss.pwrdn_ovrd=0x7FFFFFFFFF",
        "cbbs.base.i_ccf_envs.ingresss.cbo_pwrdn_ovrd2=0x1FF",
        "cbbs.base.i_ccf_envs.ncu_dtf_obs_enc_regs.dso_cfg_dtf_src_config_reg.pwrdn_ovrd=0x1",
        "cbbs.base.punit_regs.punit_gpsb.gpsb_infst_io_regs.misc_pcode_hw_configs_infst.pwrdn_ovrd_st_ios=0x1",
        "cbbs.base.punit_regs.punit_gpsb.gpsb_infvnn_crs.pwrdn_ovrd=0xFFFFFFF",
        "cbbs.base.punit_regs.punit_gpsb.punit_dso_regs.dso_cfg_dtf_src_config_reg.pwrdn_ovrd=0x1",
        "cbbs.base.sb_obss.sb_obs_dtf_obs_enc_regs.dso_cfg_dtf_src_config_reg.pwrdn_ovrd=0x1",
        "cbbs.compute0.mcast_core.core_gpsb_top.core_pma_gpsb.pwrdn_ovrd=0xFFFFFFFF",
        "cbbs.computes.modules.ml2_cr_pwrdn_ovrd=0xFFFFFFFF",
        "cbbs.computes.modules.ml3_cr_pwrdn_ovrd=0xFFFFFFFF",
        "cbbs.computes.modules.ml4_cr_pwrdn_ovrd=0xFFFFFFFF",
        "cbbs.computes.modules.ml6_cr_pwrdn_ovrd=0xFFFFF",
        "cbbs.computes.modules.ctap_cr_pwrdn_ovrd_core=0xFF",
        "cbbs.computes.modules.cores.ifu_cr_pwrdn_ovrd=0xFFFFFFFF",
        "cbbs.computes.modules.cores.ifu_cr_pwrdn_ovrd2=0x8000003F",
        "cbbs.computes.modules.cores.bpu1_cr_pwrdn_ovrd=0xFFFFFFFF",
        "cbbs.computes.modules.cores.bac_cr_pwrdn_ovrd=0x1F9F",
        "cbbs.computes.modules.cores.dsbfe_cr_pwrdn_ovrd=0x41FFBF",
        "cbbs.computes.modules.cores.ieslow_cr_ieu_pwrdn_ovrd=0xFFFFFF",
        "cbbs.computes.modules.cores.ieslow_cr_fp_pwrdn_ovrd=0xFFFFFFFF",
        "cbbs.computes.modules.cores.ieslow_cr_tm_pwrdn_ovrd=0xFFFFFFFF",
        "cbbs.computes.modules.cores.ieslow_cr_tm_pwrdn_ovrd2=0x3FFE",
        "cbbs.computes.modules.cores.ieslow_cr_si_pwrdn_ovrd=0x1FFFFFF",
        "cbbs.computes.modules.cores.ag_cr_pwrdn_ovrd=0x7F",
        "cbbs.computes.modules.cores.mi_cr_pwrdn_ovrd=0xFFFFFFFF",
        "cbbs.computes.modules.cores.mi_cr_pwrdn_ovrd2=0xFFFFFFFF",
        "cbbs.computes.modules.cores.pmh_cr_pwrdn_ovrd=0x17FBFD",
        "cbbs.computes.modules.cores.dcu_cr_pwrdn_ovrd=0x3F80FFFFFFFFF",
        "cbbs.computes.modules.cores.dtlb_cr_pwrdn_ovrd=0xFFFFFFFF",
        "cbbs.computes.modules.cores.mob_cr_pwrdn_ovrd=0xFFFFFFFF",
        "cbbs.computes.modules.cores.ms_cr_pwrdn_ovrd_2=0xF80FFFDF",
        "cbbs.computes.modules.cores.ms_cr_pwrdn_ovrd=0xFFFFFFFF",
        "cbbs.computes.modules.cores.iq_cr_pwrdn_ovrd=0x7EFC7BFF",
        "cbbs.computes.modules.cores.iq_cr_pwrdn_ovrd2=0x800003F9",
        "cbbs.computes.modules.cores.rob1_cr_pwrdn_ovrd=0x1F3FFEFFFFFFFF",
        "cbbs.computes.modules.cores.rat_cr_pwrdn_ovrd=0xFDBFFFFFFFFFFFFF",
        "cbbs.computes.modules.cores.rat_cr_pwrdn_ovrd2=0x7FFC1FFF",
        "cbbs.computes.modules.cores.al_cr_alloc_pwrdn_ovrd=0xFFFFFFFF",
        "cbbs.computes.modules.cores.rs_cr_alloc_pwrdn_ovrd=0x1FFFFFF",
        "cbbs.computes.modules.cores.rs_cr_alloc_pwrdn_ovrd1=0xF",
        "cbbs.computes.modules.cores.rs_cr_rs_pwrdn_ovrd=0xFFFFFFFF",
        "cbbs.computes.modules.cores.rsvec_cr_rs2_pwrdn_ovrd=0x1FFFFFFF",
        "cbbs.pcudata.pwrdn_ovrd=0xFFFFFFF",
        "cbbs.pcudata.misc_pcode_hw_configs_infst.pwrdn_ovrd_st_ios=0x1",
        "cbbs.pcudata.dso_cfg_dtf_src_config_reg.pwrdn_ovrd=0x1",
        "cbbs.computes.pmas.gpsb.pwrdn_ovrd=0xFFFFFFFF",
        "imhs.punit.ptpcfsms.ptpcfsms.pwrdn_ovrd=0x3F",
        "imhs.punit.ptpcfsms_pmsb.ptpcfsms_pmsb.pmsb_pwrdn_ovrd=0x3F",
        "imhs.punit.ptpcioregs.ptpcioregs.dso_cfg_dtf_src_config.pwrdn_ovrd=0x1",
        "imhs.scf.cms.cmss.pwrdn_ovrd=0xFFFFFFFFF",
        "imhs.scms_multicasts.cms_uni.pwrdn_ovrd=0xFFFFFFFFF",
        "imhs.scf.sca.scas.ingress.ing_pwrdn_ovrd=0x1FF",
        "imhs.scf.sca.sca_multi.ingress.ing_pwrdn_ovrd=0x1FF",
        "imhs.scf.sca.scas.pipe.pipe_pwrdn_ovrd=0x1FFFF",
        "imhs.scf.sca.sca_multi.pipe.pipe_pwrdn_ovrd=0x1FFFF",
        "imhs.scf.sca.scas.util.util_pwrdn_ovrd=0xF",
        "imhs.scf.sca.sca_multi.util.util_pwrdn_ovrd=0xF"
    ]



