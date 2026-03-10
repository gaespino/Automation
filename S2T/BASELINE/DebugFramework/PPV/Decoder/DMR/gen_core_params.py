"""Generate core_params.json for DMR (Diamond Rapids) BigCore (PNC) MCA decoder."""
import json

# Cache hierarchy MCACOD values common to all ML2 cache error types
CACHE_MCACODS = {
    '277': 'D_CACHE_L2_RD_ERR',
    '297': 'G_CACHE_L2_WR_ERR',
    '309': 'D_CACHE_L2_DRD_ERR',
    '325': 'D_CACHE_L2_DWR_ERR',
    '337': 'I_CACHE_L2_IRD_ERR',
    '357': 'D_CACHE_L2_PREFETCH_ERR',
    '377': 'G_CACHE_L2_EVICT_ERR',
    '389': 'D_CACHE_L2_SNOOP_ERR',
    '393': 'G_CACHE_L2_SNOOP_ERR',
}

CACHE_OP_NAMES = {
    '277': 'Generic read / SETMON',
    '297': 'MLC Flush',
    '309': 'Data read (DCU RD/RFO/ITOM)',
    '325': 'Data write (DCU WB)',
    '337': 'Instr fetch (IFU CRD)',
    '357': 'Prefetch (MPL RD/RFO/CRD)',
    '377': 'Fill/Evict',
    '389': 'Snoop (probe/confirm)',
    '393': 'Snoop',
}


def cache_mcacod_entries(err_type_label):
    """Return all cache hierarchy MCACOD entries with the given error type prefix."""
    return {
        mcacod: {
            'Name': f'{err_type_label} - {CACHE_OP_NAMES[mcacod]}',
            'Description': desc,
        }
        for mcacod, desc in CACHE_MCACODS.items()
    }


data = {
    '_META': {
        'product': 'DMR (Diamond Rapids)',
        'core_arch': 'BigCore (PNC - Panther Cove)',
        'smt': 'No SMT/HT - one thread per core',
        'notes': [
            'IFU/DCU/DTLB tables are GNR BigCore baseline - compatible with DMR PNC architecture',
            'DCU in DMR uses EXTENDED 22-bit MSCOD (bits 37:16, not 31:16). decoder_dmr.py handles this.',
            'ML2 MSCOD is a bitfield register. MSCOD entries cover single-bit patterns for direct lookup.',
            'For multi-bit MSCOD values, the decoder returns raw MSCOD+MCACOD - use _MSCOD_BITFIELDS.',
            'Source: GNR core_params + DMR mcadecode.py (based on DMR_MCA_CUSTOMER_DOCUMENTATION.xlsx)',
            'Bank map: Bank0=IFU, Bank1=DCU, Bank2=DTLB, Bank3=ML2(MLC)',
        ],
    },

    # -------------------------------------------------------------------------
    # IFU (Bank 0) - Instruction Fetch Unit
    # Unchanged from GNR BigCore baseline
    # -------------------------------------------------------------------------
    'IFU': {
        'MSCOD': {
            '0':  {'MCACOD': {
                '5':    {'Name': 'PRF parity', 'Description': 'Pipeline Error'},
                '1030': {'Name': 'Rob MC Trusted Path', 'Description': 'Internal Unclassified'},
            }},
            '1':  {'MCACOD': {'5': {'Name0': 'DSB FE', 'Description0': 'Pipeline Error', 'Name1': 'DSB Data', 'Description1': 'Pipeline Error'}}},
            '2':  {'MCACOD': {
                '5':    {'Name': 'msram', 'Description': 'Pipeline Error'},
                '1030': {'Name': 'Patch Ram Trust MCA', 'Description': 'Internal Unclassified'},
                '336':  {'Name': 'IFU inclusion error (2)', 'Description': 'I_CACHE_L1_IRD_ERR'},
            }},
            '3':  {'MCACOD': {
                '5':  {'Name': 'IQ', 'Description': 'Pipeline Error'},
                '16': {'Name': 'IFU iTLB parity error (correctable) + dsb hit', 'Description': 'I_TLB_L1_ERR'},
            }},
            '4':  {'MCACOD': {
                '5':   {'Name': 'DSB FE offset/nata', 'Description': 'Pipeline Error'},
                '336': {'Name': 'IFU IC data parity error', 'Description': 'I_CACHE_L1_IRD_ERR'},
            }},
            '5':  {'MCACOD': {
                '5':   {'Name': 'DSB FE tag', 'Description': 'Pipeline Error'},
                '336': {'Name': 'IFU IC tag parity error', 'Description': 'I_CACHE_L1_IRD_ERR'},
            }},
            '6':  {'MCACOD': {
                '5':  {'Name': 'TMUL parity error', 'Description': 'Pipeline Error'},
                '16': {'Name': 'IFU iTLB parity error', 'Description': 'I_TLB_L1_ERR'},
            }},
            '7':  {'MCACOD': {'5': {'Name': 'IDQ uop', 'Description': 'Pipeline Error'}}},
            '8':  {'MCACOD': {'5': {'Name': 'BIQ (BIT + baqbrd)', 'Description': 'Pipeline Error'}}},
            '9':  {'MCACOD': {'5': {'Name': 'mspatch - CAM parity error', 'Description': 'Pipeline Error'}}},
            '10': {'MCACOD': {'5': {'Name': 'mspatch - data parity error', 'Description': 'Pipeline Error'}}},
            '11': {'MCACOD': {'5': {'Name': 'msrom PTR', 'Description': 'Pipeline Error'}}},
            '12': {'MCACOD': {
                '5':   {'Name': 'RAT parity error (freelist)', 'Description': 'Pipeline Error'},
                '336': {'Name': 'IFU poison (parity error on MLC data)', 'Description': 'I_CACHE_L1_IRD_ERR'},
            }},
            '14': {'MCACOD': {'5': {'Name': 'RS/IDQ imm parity', 'Description': 'Pipeline Error'}}},
            '15': {'MCACOD': {
                '1034': {'Name': 'EXE RC error', 'Description': 'Internal Unclassified'},
                '336':  {'Name': 'IFU inclusion error', 'Description': 'I_CACHE_L1_IRD_ERR'},
            }},
            '16': {'MCACOD': {'5': {'Name': 'RS parity error (rsbpc)', 'Description': 'Pipeline Error'}}},
            '17': {'MCACOD': {'5': {'Name': 'RS parity error (rsbpc)', 'Description': 'Pipeline Error'}}},
            '18': {'MCACOD': {'5': {'Name': 'ROB parity error (roalc)', 'Description': 'Pipeline Error'}}},
            '19': {'MCACOD': {'5': {'Name': 'ImmdFolding EU Error', 'Description': 'Pipeline Error'}}},
            '20': {'MCACOD': {'5': {'Name': 'ImmdFolding DATA Error', 'Description': 'Pipeline Error'}}},
            '21': {'MCACOD': {'5': {'Name': 'ImmdFolding MEM Error', 'Description': 'Pipeline Error'}}},
            '22': {'MCACOD': {'5': {'Name': 'MS UNIQ ROM', 'Description': 'Pipeline Error'}}},
            '23': {'MCACOD': {'5': {'Name': 'IFQ parity error', 'Description': 'Pipeline Error'}}},
            '24': {'MCACOD': {'5': {'Name': 'ROBTTD Parity Error', 'Description': 'Pipeline Error'}}},
            '25': {'MCACOD': {'4': {'Name': 'TMUL_ALU error', 'Description': 'FRC Error'}}},
            '26': {'MCACOD': {'4': {'Name': 'FMA01', 'Description': 'FRC Error'}}},
            '27': {'MCACOD': {'4': {'Name': 'FMA23', 'Description': 'FRC Error'}}},
            '28': {'MCACOD': {'4': {'Name': 'F16', 'Description': 'FRC Error'}}},
            '29': {'MCACOD': {'4': {'Name': 'SHUF', 'Description': 'FRC Error'}}},
            '30': {'MCACOD': {'4': {'Name': 'FA', 'Description': 'FRC Error'}}},
            '31': {'MCACOD': {'4': {'Name': 'SiMD', 'Description': 'FRC Error'}}},
            '32': {'MCACOD': {'5': {'Name': 'AES', 'Description': 'Pipeline Error'}}},
            '33': {'MCACOD': {'5': {'Name': 'VEC_LDWB', 'Description': 'Pipeline Error'}}},
        }
    },

    # -------------------------------------------------------------------------
    # DCU (Bank 1) - Data Cache Unit
    # NOTE: DMR DCU uses EXTENDED 22-bit MSCOD (bits 37:16, not standard 31:16)
    # decoder_dmr.py core_decoder() already handles this for bank='DCU'
    # -------------------------------------------------------------------------
    'DCU': {
        '_DCU_NOTES': 'DMR DCU EXTENDED 22-bit MSCOD (bits 37:16). decoder_dmr.py handles this.',
        'MSCOD': {
            '32': {'MCACOD': {
                '1025': {'Name': 'WB access to APIC space (from APIC) [SW]', 'Description': 'Internal Unclassified'},
                '1028': {'Name': 'APIC load/store - read error [HW]', 'Description': 'Internal Unclassified'},
            }},
            '16': {'MCACOD': {
                '372': {'Name': 'WBINVD error', 'Description': 'D_CACHE_L1_EVICT_ERR'},
                '308': {'Name0': 'DCU Data - Load Poison - correctable', 'Description0': 'D_CACHE_L1_DRD_ERR',
                        'Name1': 'DCU Data - Load Poison - uncorrectable', 'Description1': 'D_CACHE_L1_DRD_ERR'},
            }},
            '17': {'MCACOD': {'308': {'Name': 'Stuffed load - Load Poison - uncorrectable', 'Description': 'D_CACHE_L1_DRD_ERR'}}},
            '0': {'MCACOD': {
                '292': {'Name': 'Store read error', 'Description': 'D_CACHE_L1_WR_ERR'},
                '276': {'Name0': 'Load read error - correctable', 'Description0': 'D_CACHE_L1_RD_ERR',
                        'Name1': 'Load read error - uncorrectable - non modified', 'Description1': 'D_CACHE_L1_RD_ERR',
                        'Name2': 'Load read error - uncorrectable - modified line', 'Description2': 'D_CACHE_L1_RD_ERR'},
                '388': {'Name': 'Snoop error', 'Description': 'D_CACHE_L1_SNOOP_ERR'},
                '356': {'Name': 'HWP', 'Description': 'D_CACHE_L1_PREFETCH_ERR'},
                '372': {'Name0': 'DCU evict parity err - correctable', 'Description0': 'D_CACHE_L1_EVICT_ERR',
                        'Name1': 'DCU evict parity err - uncorrectable - modified data', 'Description1': 'D_CACHE_L1_EVICT_ERR'},
                '5': {'Name': 'SDB parity', 'Description': 'Pipeline Error'},
            }},
            '6160': {'MCACOD': {'276': {'Name': 'DCU L0 Data buffer Parity Error', 'Description': 'D_CACHE_L1_RD_ERR'}}},
            '6161': {'MCACOD': {'276': {'Name': 'DCU L1 Data buffer Parity Error', 'Description': 'D_CACHE_L1_RD_ERR'}}},
            '6162': {'MCACOD': {'276': {'Name': 'DCU L1 WB Buffer Parity Error', 'Description': 'D_CACHE_L1_RD_ERR'}}},
            '0x1?10': {'MCACOD': {'372': {'Name': 'DCU L1 Flush Parity Error', 'Description': 'D_CACHE_L1_EVICT_ERR'}}},
            '0x1?00': {'MCACOD': {
                '388': {'Name': 'DCU L1 Snoop Parity Error', 'Description': 'D_CACHE_L1_SNOOP_ERR'},
                '292': {'Name': 'DCU L1 WB (from L0) Parity Error', 'Description': 'D_CACHE_L1_WR_ERR'},
            }},
            '0x1?11': {'MCACOD': {
                '372': {'Name': 'DCU L1 Fill Parity Error', 'Description': 'D_CACHE_L1_EVICT_ERR'},
                '276': {'Name': 'DCU L1 Rd/RFO Parity Error', 'Description': 'D_CACHE_L1_RD_ERR'},
            }},
        }
    },

    # -------------------------------------------------------------------------
    # DTLB (Bank 2) - Data Translation Lookaside Buffer
    # Unchanged from GNR BigCore baseline
    # -------------------------------------------------------------------------
    'DTLB': {
        'MSCOD': {
            '0': {'MCACOD': {
                '20': {'Name': 'DTLB Tag - UC on Stores, C on Loads', 'Description': 'D_TLB_L1_ERR'},
                '25': {'Name': 'STLB Tag Parity', 'Description': 'G_TLB_L2_ERR'},
            }},
            '1': {'MCACOD': {
                '20': {'Name': 'DTLB Data - UC on Stores, C on Loads, include also Physical-Address from ICLB(UC, C from PNC)', 'Description': 'D_TLB_L1_ERR'},
                '25': {'Name': 'STLB Data Parity', 'Description': 'G_TLB_L2_ERR'},
            }},
            '2': {'MCACOD': {
                '25': {'Name': 'PDE/EPDE tag parity', 'Description': 'G_TLB_L2_ERR'},
                '5':  {'Name': 'IEU (FSCP) parity', 'Description': 'Pipeline Error'},
            }},
            '3': {'MCACOD': {
                '25':   {'Name': 'PDE/EPDE data parity', 'Description': 'G_TLB_L2_ERR'},
                '1030': {'Name': 'Trust IEU', 'Description': 'Internal Unclassified'},
            }},
            '4': {'MCACOD': {
                '5':    {'Name': 'SRF', 'Description': 'Pipeline Error'},
                '1030': {'Name': 'Trust AGU', 'Description': 'Internal Unclassified'},
            }},
            '13': {'MCACOD': {'5': {'Name': 'ICLB Attributes Parity', 'Description': 'Pipeline Error'}}},
            '25': {'MCACOD': {'5': {'Name': 'SB FineNet Array Parity Error', 'Description': 'Pipeline Error'}}},
        }
    },

    # -------------------------------------------------------------------------
    # ML2 (Bank 3) - Module Level Cache (L2 / MLC)
    # DMR-specific: MSCOD is a bitfield register.
    # MSCOD entries below cover single-bit (simple error) patterns for direct lookup.
    # Multi-bit MSCOD: decoder returns raw values; see _MSCOD_BITFIELDS for manual decode.
    # -------------------------------------------------------------------------
    'ML2': {
        '_ML2_NOTES': [
            'ML2 = Module Level Cache (L2), Bank 3. Also referred to as MLC.',
            'MSCOD is a BITFIELD register; multiple bits can be set simultaneously for compound errors.',
            'See _MSCOD_BITFIELDS for the bitfield decode reference.',
            'MSCOD entries listed cover single-bit (simple error) patterns for direct decoder lookup.',
            'For multi-bit MSCOD, the decoder falls back to raw MSCOD+MCACOD display.',
            'In DMR, Acode no longer has a single valid bit; error details are reported in MLC bank.',
            'MCACOD cache hierarchy values: 277=D_CACHE_L2_RD_ERR, 297=G_CACHE_L2_WR_ERR,',
            '  309=D_CACHE_L2_DRD_ERR, 325=D_CACHE_L2_DWR_ERR, 337=I_CACHE_L2_IRD_ERR,',
            '  357=D_CACHE_L2_PREFETCH_ERR, 377=G_CACHE_L2_EVICT_ERR,',
            '  389=D_CACHE_L2_SNOOP_ERR, 393=G_CACHE_L2_SNOOP_ERR',
        ],
        '_MSCOD_BITFIELDS': {
            'MLC_Timeout_type': {
                '_note': 'Used when MCACOD=0x400 (1024, 3-strike WD timeout). Bits indicate stall reason.',
                'TimeOutThread':     {'min': 0,  'max': 0},
                'ActiveThreads':     {'min': 2,  'max': 3},
                'XQ_Empty':          {'min': 6,  'max': 6},
                'LQ_Empty':          {'min': 7,  'max': 7},
                'SnpQ_Empty':        {'min': 8,  'max': 8},
                'No_U2C_Req_Credit': {'min': 9,  'max': 9},
                'No_C2U_Credits':    {'min': 10, 'max': 12},
                'ExtCmpCntIsZero':   {'min': 13, 'max': 13},
                'FBVCntIsZero':      {'min': 14, 'max': 14},
                'VirtLLC_Prefetch':  {'min': 15, 'max': 15},
            },
            'Others_type': {
                '_note': 'Used for tag/data/MESI/misc/C6SRAM errors. Each field encodes error type.',
                'Tag':    {'min': 0, 'max': 1, 'decode': {'0': 'no err', '1': 'C err', '2': 'UC err', '3': 'reserved'}},
                'MESI':   {'min': 2, 'max': 3, 'decode': {'0': 'no err', '1': 'C err', '2': 'UC err', '3': 'reserved'}},
                'Data':   {'min': 4, 'max': 5, 'decode': {'0': 'no err', '1': 'C err', '2': 'UC err', '3': 'Psn+no Fwd'}},
                'Misc':   {'min': 6, 'max': 7, 'decode': {'0': 'no err', '1': 'SQ/IDI err', '2': 'WD', '3': 'Trust'}},
                'C6SRAM': {'min': 8, 'max': 8, 'decode': {'0': 'no err', '1': 'err'}},
            },
        },
        'MSCOD': {
            '0': {
                '_note': 'No bitfield error bits set. Error fully characterized by MCACOD alone.',
                'MCACOD': {
                    '5':    {'Name': 'SQDB or IDI (addr/data) parity',       'Description': 'Pipeline Error'},
                    '277':  {'Name': 'Generic read - SETMON (zlen)',          'Description': 'D_CACHE_L2_RD_ERR'},
                    '297':  {'Name': 'MLC Flush (ecc error on tag or data)', 'Description': 'G_CACHE_L2_WR_ERR'},
                    '309':  {'Name': 'Data read - DCU RD, RFO, ITOM',        'Description': 'D_CACHE_L2_DRD_ERR'},
                    '325':  {'Name': 'Data write - DCU WB',                   'Description': 'D_CACHE_L2_DWR_ERR'},
                    '337':  {'Name': 'Instr fetch - IFU CRD (code read)',    'Description': 'I_CACHE_L2_IRD_ERR'},
                    '357':  {'Name': 'Prefetch - MPL RD, RFO, CRD',          'Description': 'D_CACHE_L2_PREFETCH_ERR'},
                    '377':  {'Name': 'Fill/Evict - eviction',                 'Description': 'G_CACHE_L2_EVICT_ERR'},
                    '389':  {'Name': 'Snoop - probe / confirm',               'Description': 'D_CACHE_L2_SNOOP_ERR'},
                    '393':  {'Name': 'Snoop',                                 'Description': 'G_CACHE_L2_SNOOP_ERR'},
                    '1024': {'Name': 'WDTimeout (3 strike)',                  'Description': 'Internal Unclassified'},
                    '1029': {'Name': 'SQDB or IDI (addr/data) parity',       'Description': 'Internal Unclassified'},
                    '1030': {'Name': 'Trust',                                 'Description': 'Internal Unclassified'},
                    '1033': {'Name': 'Error during C6 restore',              'Description': 'Internal Unclassified'},
                    '1038': {'Name': 'acode-pm-ucss internal errors',         'Description': 'Internal Unclassified'},
                },
            },
            '1':   {'_note': 'bits 1:0=01: Tag CE. MCACOD=cache access type.',
                    'MCACOD': cache_mcacod_entries('Tag CE')},
            '2':   {'_note': 'bits 1:0=10: Tag UCE. MCACOD=cache access type.',
                    'MCACOD': cache_mcacod_entries('Tag UCE')},
            '4':   {'_note': 'bits 3:2=01: MESI CE. MCACOD=cache access type.',
                    'MCACOD': cache_mcacod_entries('MESI CE')},
            '8':   {'_note': 'bits 3:2=10: MESI UCE. MCACOD=cache access type.',
                    'MCACOD': cache_mcacod_entries('MESI UCE')},
            '16':  {'_note': 'bits 5:4=01: Data CE. MCACOD=cache access type.',
                    'MCACOD': cache_mcacod_entries('Data CE')},
            '32':  {'_note': 'bits 5:4=10: Data UCE. MCACOD=cache access type.',
                    'MCACOD': cache_mcacod_entries('Data UCE')},
            '48':  {
                '_note': 'bits 5:4=11: Data Poison+no Forward. Typically occurs on read-side operations.',
                'MCACOD': {
                    mcacod: {'Name': f'Data Psn+no Fwd - {CACHE_OP_NAMES[mcacod]}', 'Description': desc}
                    for mcacod, desc in CACHE_MCACODS.items()
                    if mcacod in ('277', '309', '337', '357', '389', '393')
                },
            },
            '64':  {
                '_note': 'bits 7:6=01: Misc=SQ/IDI error (SQ queue or IDI interface parity).',
                'MCACOD': {
                    '5':    {'Name': 'Misc SQ/IDI error', 'Description': 'Pipeline Error'},
                    '1029': {'Name': 'Misc SQ/IDI error', 'Description': 'Internal Unclassified'},
                },
            },
            '128': {
                '_note': 'bits 7:6=10: Misc=WD (Watchdog). See MLC_Timeout_type bitfield for stall reason detail.',
                'MCACOD': {'1024': {'Name': 'WDTimeout - Watchdog fired (3-strike)', 'Description': 'Internal Unclassified'}},
            },
            '129': {
                '_note': 'MSCOD=0x81: WD(bit7)+TimeOutThread(bit0). Most common 3-strike MSCOD pattern in DMR.',
                'MCACOD': {'1024': {'Name': 'WDTimeout (3 strike) - WD + TimeOutThread', 'Description': 'Internal Unclassified'}},
            },
            '192': {
                '_note': 'bits 7:6=11: Misc=Trust error.',
                'MCACOD': {'1030': {'Name': 'Trust error (Misc bits=11)', 'Description': 'Internal Unclassified'}},
            },
            '256': {
                '_note': 'bit 8=1: C6SRAM error (error in C6 save state SRAM).',
                'MCACOD': {'1033': {'Name': 'C6SRAM error - Error during C6 restore', 'Description': 'Internal Unclassified'}},
            },
        },
    },
}

outpath = r'c:\Git\Automation\PPV\Decoder\DMR\core_params.json'
with open(outpath, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=1, ensure_ascii=False)

# Validate
with open(outpath, 'r', encoding='utf-8') as f:
    check = json.load(f)
lines = open(outpath).readlines()
print(f'Written OK. Lines: {len(lines)}, Top-level keys: {list(check.keys())}')
ml2_mscod_keys = list(check['ML2']['MSCOD'].keys())
print(f'ML2 MSCOD keys ({len(ml2_mscod_keys)}): {ml2_mscod_keys}')
ifu_mscod_keys = list(check['IFU']['MSCOD'].keys())
print(f'IFU MSCOD keys ({len(ifu_mscod_keys)}): {ifu_mscod_keys}')
