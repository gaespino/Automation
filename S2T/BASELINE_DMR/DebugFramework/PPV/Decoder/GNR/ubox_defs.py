########################################################################################################################
# Description :: Ubox parameters/encodings
# To Do:
########################################################################################################################

##############################################
# Constants
##############################################

# number of sockets/M2IOSF stacks supported by the Ubox HW, not necessarily how many are supported by the consuming SOC
NUM_MAX_SOCKETS = 8
NUM_IIO_MAX = 15

NUM_RACU_ENTRIES = 8

#####################
# NRA FSMs
#####################

SUBUNIT_BY_VAL = {
  0:'SMI',
  1:'GLOB_INT',
  2:'LOC_LOCK',
  3:'GLOB_LOCK',
  4:'SYS_LOCK',
  5:'NCB_SPEC',
  6:'NCS_SPEC',
  7:'RACU',
  8:'PMREQ',
  9:'GLOB_EOI',
  10:'LOC_EOI'
}
SUBUNIT_BY_NAME = dict((v2, k2) for k2, v2 in SUBUNIT_BY_VAL.items())

NUM_NCU_TARGETS_NRA = len(list(SUBUNIT_BY_VAL.keys()))

GLBINT_FSM = {
  0b000: 'IDLE',
  0b001: 'START',
  0b010: 'RQST',
  0b011: 'SEND',
  0b100: 'AKRDY',
  0b101: 'CMP'
}

GLBEOI_FSM = {
  0b000: 'IDLE',
  0b001: 'START',
  0b010: 'RQST',
  0b011: 'SEND',
  0b100: 'AKRDY',
  0b101: 'CMP'
}

LOCEOI_FSM = {
  0b00: 'IDLE',
  0b01: 'RQST',
  0b10: 'AKRDY'
}

SMI_FSM = {
  0b000: 'IDLE',
  0b001: 'START',
  0b010: 'RQST',
  0b011: 'SEND',
  0b100: 'SEND_CMP'
}

PMREQ_FSM = {
  0b000: 'IDLE',
  0b001: 'START',
  0b010: 'RQST',
  0b011: 'SEND',
  0b100: 'CMP'
}

GV_FSM = {
  0b000: 'IDLE',
  0b001: 'Gv_blk',
  0b010: 'Cbo_drain',
  0b011: 'Wakeup_drain',
  0b111: 'Blk_IV',
  0b100: 'Blk_Cmp',
  0b101: 'Blk_hold',
  0b110: 'UnBlk'
}

APIC_MODE_FSM = {
  0b00: 'XAPIC_FLAT',
  0b01: 'X2APIC_MODE',
  0b10: 'XAPIC_CLUSTER'
}

GLBLOCK_FSM = {
  0b000: 'IDLE',
  0b001: 'RQST',
  0b011: 'AKRDY',
  0b010: 'LK_CMP',
  0b110: 'RQST2',
  0b100: 'AKRDY2'
}

NCSSPEC_FSM = {
  0b00: 'IDLE',
  0b01: 'AKRDY',
  0b10: 'BDCST'
}

NCBSPEC_FSM = {
  0b00: 'IDLE',
  0b01: 'AKRDY',
  0b10: 'SEND'
}

MSTRLOCK_FSM = {
  0b0000: 'IDLE',
  0b0001: 'STOP1A',
  0b0010: 'STOP1B',
  0b0011: 'STOP2A',
  0b0100: 'STOP2B',
  0b0101: 'STOP2C',
  0b0110: 'AKRDY1',
  0b0111: 'LOCK',
  0b1000: 'START1A',
  0b1001: 'START2A',
  0b1010: 'START2B',
  0b1011: 'START2C',
  0b1100: 'AKRDY2',
  0b1101: 'WAIT',
  0b1110: 'STOP1A_GT'
}

STOPREQ1_FSM = {
  0b0000: 'IDLE',
  0b0001: 'SMIBLK',
  0b0010: 'PCU_LK',
  0b0011: 'IV_MAP',
  0b0100: 'STOP_CORE',
  0b0101: 'AKRDY1',
  0b0110: 'WAIT',
  0b0111: 'HOLD',
  0b1000: 'AKRDY2',
  0b1001: 'WAIT_GT',
  0b1010: 'STOP_GT',
  0b1011: 'AKRDY3'
}

STOPREQ2_FSM = {
  0b0001: 'IDLE',
  0b0010: 'STOP2A',
  0b0011: 'AKRDY1',
  0b0100: 'WAIT1',
  0b0101: 'STOP2B',
  0b0110: 'AKRDY2',
  0b0111: 'WAIT2',
  0b1000: 'STOP2C',
  0b1001: 'CBO_DRAIN',
  0b1010: 'AKRDY3',
  0b1011: 'PMREQBLK'
}

STARTREQ1_FSM = {
  0b00: 'IDLE',
  0b01: 'START',
  0b10: 'AKRDY'
}

STARTREQ2_FSM = {
  0b0000: 'IDLE',
  0b0001: 'START2A',
  0b0010: 'AKRDY1',
  0b0011: 'WAIT1',
  0b0100: 'START2B',
  0b0101: 'AKRDY2',
  0b0110: 'WAIT2',
  0b0111: 'START2C',
  0b1000: 'START_CORE',
  0b1001: 'PCU_UNL',
  0b1010: 'AKRDY3'
}

#####################
# Mesh interface
#####################

BLBUF_DEC = {
  0:'UPI NCB 0',
  1:'UPI NCB 1',
  2:'UPI NCS 0',
  3:'UPI NCS 1',
  4:'UPI DRS 0',
  5:'UPI DRS 1',
  6:'COMMON  0',
  7:'COMMON  1'
}

NUM_OUTBOUND_BUFFERS = len(list(BLBUF_DEC.keys()))

IV_OPCODES = {
  0x8: 'VLW',
  0x10: 'LTDoorbell',
  0x19: 'IntLog',
  0x1a: 'IntPhy'
}

#####################
# MCAs
#####################

MSCOD = {
  0x8003: 'MISALG_CFGWR_SMM',
  0x8005: 'MISALG_CFGWR_NONSMM',
  0x8002: 'MISALG_CFGRD_SMM',
  0x8004: 'MISALG_CFGRD_NONSMM',
  0x8007: 'MISALG_MMIOWR_SMM',
  0x8009: 'MISALG_MMIOWR_NONSMM',
  0x8006: 'MISALG_MMIORD_SMM',
  0x8008: 'MISALG_MMIORD_NONSMM',
  0x8000: 'POISON',
  0x8001: 'UNSUPPORTED_OPCODE',
  0x800B: 'LOCK_MASTER_TIMEOUT',
  0x800A: 'SMI_TIMEOUT',
  0x800C: 'GPSB_PARITY_ERR',
  0x800D: 'SAI_ERROR',
  0x800E: 'SEMAPHORE_ERR',
  0x800F: 'AKEGR_WRV_ENTRY',
  0x8010: 'BLEGR_WRV_ENTRY',
  0x8011: 'AKCEGR_WRV_ENTRY',
  0x8012: 'AKEGR_OVERFLOW',
  0x8013: 'BLEGR_OVERFLOW',
  0x8014: 'AKCEGR_OVERFLOW',
  0x8015: 'CHA_UBOX_OF_NCB',
  0x8016: 'CHA_UBOX_OF_NCS',
  0x8017: 'UPI_UBOX_OF_NCB',
  0x8018: 'UPI_UBOX_OF_NCS',
  0x8019: 'ING_PARITY_ERR',
  0x801A: 'M2IOSF_UBOX_OF_NCB',
  0x801B: 'M2IOSF_UBOX_OF_NCS',
  0x801C: 'SGX_DOORBELL_ERR'
}

MCACOD = {
  0x0E0B: 'IOSF error',
  0x401: "XuCode",
  0x405: "uCode shutdown",
  0x406: 'Sunpass error',
  0x407: 'Ubox general error',
  0x408: 'SAD errors',
  0x40b: "BIST error",
  0x40c: "Shutdown suppression",
  0x412: 'SCF Bridge IP:CMS error',
  0x413: 'SCF Bridge IP:SBO error'
}

SHUTDOWN_ERR_MSCOD = {
  1: "MCE when CR4.MCE is clear",
  2: "MCE when MCIP bit is set",
  3: "MCE under WFS",
  4: "Unrecoverable error during security flow execution",
  5: "SW triple fault shutdown",
  6: "VMX exit consistency check failures",
  7: "RSM consistency check failures",
  8: "Invalid conditions on protected mode SMM entry",
  9: "Unrecoverable error during security flow execution"
}

##############################################
# Helper functions
##############################################

SBO_MSCOD={

0x0	:"SBO_AD_CTRL_PAR_ERR",
0x1	:"SBO_AK_CTRL_PAR_ERR",
0x2	:"SBO_BL_CTRL_PAR_ERR",
0x3	:"SBO_BL_DATA_PAR_ERR"
}

CMS_MSCOD={
    0x0: "TGR_INGR_AD_PLD_ERR in AD CHA-CMS",
    0x1: "TGR_EGR_AD_PLD_ERR in AD CHA-CMS",
    0x2: "AGT0_EGR_AD_PLD_ERR in AD CHA-CMS",
    0x3: "AGT1_EGR_AD_PLD_ERR in AD CHA-CMS",
    0x4: "TGR_INGR_AD_PLD_ERR in AD SA-CMS",
    0x5: "TA_AD_PLD_ERR in AD SA-CMS",
    0x6: "AGT0_AD_PLD_ERR in AD SA-CMS",
    0x7: "AGT1_AD_PLD_ERR in AD SA-CMS",
    0x8: "TGR_INGR_BL_PLD_ERR in BL CHA-CMS",
    0x9: "TGR_EGR_BL_PLD_ERR in BL CHA-CMS",
    0xa: "AGT0_BL_PLD_ERR in BL CHA-CMS",
    0xb: "AGT1_BL_PLD_ERR in BL CHA-CMS",
    0xc: "TGR_INGR_BL_PLD_ERR in BL SA-CMS",
    0xd: "AGT_BL_PLD_ERR in BL SA-CMS",
    0xe: "TA_BL_PLD_ERR in BL SA-CMS",
    0xf: "TGR_INGR_AK_PLD_ERR in AK CHA-CMS",
    0x10: "TGR_EGR_AK_PLD_ERR in AK CHA-CMS",
    0x11: "AGT0_AK_PLD_ERR in AK SA-CMS",
    0x12: "AGT1_AK_PLD_ERR in AK SA-CMS",
    0x13: "TGR_INGR_AD_OVFL_ERR in AD CHA-CMS",
    0x14: "TGR_EGR_AD_OVFL_ERR in AD CHA-CMS",
    0x15: "AGT0_AD_OVFL_ERR in AD CHA-CMS",
    0x16: "AGT1_AD_OVFL_ERR in AD CHA-CMS",
    0x17: "TGR_INGR_AD_OVFL_ERR in AD SA-CMS",
    0x18: "TGR_EGR_AD_OVFL_ERR in AD SA-CMS",
    0x19: "TA_AD_OVFL_ERR in AD SA-CMS",
    0x1a: "AGT0_AD_OVFL_ERR in AD SA-CMS",
    0x1b: "AGT1_AD_OVFL_ERR in AD SA-CMS",
    0x1c: "TGR_INGR_BL_OVFL_ERR in BL CHA-CMS",
    0x1d: "TGR_EGR_BL_OVFL_ERR in BL CHA-CMS",
    0x1e: "AGT0_BL_OVFL_ERR in BL CHA-CMS",
    0x1f: "AGT1_BL_OVFL_ERR in BL CHA-CMS",
    0x20: "TGR_INGR_BL_OVFL_ERR in BL SA-CMS",
    0x21: "TGR_EGR_BL_OVFL_ERR in BL SA-CMS",
    0x22: "TA_BL_OVFL_ERR in BL SA-CMS",
    0x23: "AGT0_BL_OVFL_ERR in BL SA-CMS",
    0x24: "AGT1_BL_OVFL_ERR in BL SA-CMS",
    0x25: "TGR_INGR_AK_OVFL_ERR in AK CHA-CMS",
    0x26: "TGR_EGR_AK_OVFL_ERR in AK CHA-CMS",
    0x27: "AGT0_AK_OVFL_ERR in AK CHA-CMS",
    0x28: "AGT1_AK_OVFL_ERR in AK CHA-CMS",
    0x29: "TGR_INGR_AK_OVFL_ERR in AK SA-CMS",
    0x2a: "TGR_EGR_AK_OVFL_ERR in AK SA-CMS",
    0x2b: "TA_AK_OVFL_ERR in AK SA-CMS",
    0x2c: "AGT0_AK_OVFL_ERR in AK SA-CMS",
    0x2d: "AGT1_AK_OVFL_ERR in AK SA-CMS",
    0x2e: "TGR_INGR_IV_OVFL_ERR in IV CHA-CMS",
    0x2f: "TGR_EGR_IV_OVFL_ERR in IV CHA-CMS",
    0x30: "AGT1_IV_OVFL_ERR in IV CHA-CMS",
    0x31: "TGR_INGR_IV_OVFL_ERR in IV SA-CMS",
    0x32: "TGR_EGR_IV_OVFL_ERR in IV SA-CMS",
    0x33: "AGT1_IV_OVFL_ERR in IV SA-CMS"
}
