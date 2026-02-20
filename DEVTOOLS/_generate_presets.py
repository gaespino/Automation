"""
_generate_presets.py — Wave 2 preset generation script.
Populates GNR / CWF / DMR sections in experiment_presets.json.
Run once; safe to re-run (overwrites product sections).
"""
import json, pathlib

PRESETS_FILE = pathlib.Path(r"c:\Git\Automation\.claude\defaults\experiment_presets.json")
data = json.loads(PRESETS_FILE.read_text(encoding="utf-8"))

# ─── shared ask-user lists ───────────────────────────────────────────────
ASK_BOOT    = ["Visual ID", "Bucket", "COM Port", "IP Address"]
ASK_LOOPS   = ["Visual ID", "Bucket", "COM Port", "IP Address", "Loops"]
ASK_SWEEP   = ["Visual ID", "Bucket", "COM Port", "IP Address"]
ASK_SLICE   = ["Visual ID", "Bucket", "COM Port", "IP Address",
               "Configuration (Mask)", "Check Core", "Loops"]
ASK_LINUX   = ["Visual ID", "Bucket", "COM Port", "IP Address", "Loops"]
ASK_CORE    = ["Visual ID", "Bucket", "COM Port", "IP Address", "Check Core", "Loops"]
ASK_CORE_NO_LOOPS = ["Visual ID", "Bucket", "COM Port", "IP Address", "Check Core"]


def _preset(label, desc, products, ask_user, experiment):
    return {
        "label": label,
        "description": desc,
        "products": products,
        "ask_user": ask_user,
        "experiment": experiment,
    }


def _blank_exp():
    """Return experiment skeleton with every possible field set to None/default."""
    return {
        "Experiment": "Enabled",
        "Test Name": None,
        "Test Mode": None,
        "Test Type": None,
        "Visual ID": "TemplateVID",
        "Bucket": "TemplateBucket",
        "COM Port": 11,
        "IP Address": "192.168.0.2",
        "Content": None,
        "Test Number": None,
        "Test Time": 30,
        "Reset": True,
        "Reset on PASS": True,
        "FastBoot": False,
        "Core License": None,
        "600W Unit": False,
        "Pseudo Config": False,
        "Post Process": None,
        "Configuration (Mask)": None,
        "Boot Breakpoint": None,
        "Check Core": 0,
        "Voltage Type": "vbump",
        "Voltage IA": None,
        "Voltage CFC": None,
        "Frequency IA": None,
        "Frequency CFC": None,
        "Loops": None,
        "Type": None,
        "Domain": None,
        "Start": None,
        "End": None,
        "Steps": None,
        "ShmooFile": None,
        "ShmooLabel": None,
        "ULX Path": None,
        "ULX CPU": None,
        "Product Chop": None,
        "Dragon Pre Command": None,
        "Dragon Post Command": None,
        "Startup Dragon": None,
        "Dragon Content Path": None,
        "Dragon Content Line": None,
        "VVAR0": None,
        "VVAR1": None,
        "VVAR2": None,
        "VVAR3": None,
        "VVAR_EXTRA": None,
        "TTL Folder": None,
        "Scripts File": None,
        "Pass String": "Test Complete",
        "Fail String": "Test Failed",
        "Stop on Fail": True,
        "Fuse File": None,
        "Bios File": None,
        "Merlin Name": None,
        "Merlin Drive": None,
        "Merlin Path": None,
        "Disable 2 Cores": None,
        "Disable 1 Core": None,
        "Linux Pre Command": None,
        "Linux Post Command": None,
        "Linux Pass String": None,
        "Linux Fail String": None,
        "Startup Linux": None,
        "Linux Path": None,
        "Linux Content Wait Time": None,
        "Linux Content Line 0": None,
        "Linux Content Line 1": None,
        "Linux Content Line 2": None,
        "Linux Content Line 3": None,
        "Linux Content Line 4": None,
        "Linux Content Line 5": None,
        "Linux Content Line 6": None,
        "Linux Content Line 7": None,
        "Linux Content Line 8": None,
        "Linux Content Line 9": None,
    }


# ════════════════════════════════════════════════════════════════════════════
#  GNR
# ════════════════════════════════════════════════════════════════════════════

GNR_BOOT_TTL   = "R:/Templates/GNR/version_1_0/TTL_Boot"
GNR_BOOT_SCRP  = "R:/Templates/scripts/boot_example.txt"
GNR_FUSE_SCRP  = "R:/Templates/scripts/fuse_generation.txt"
GNR_MESH_TTL   = "S:\\GNR\\RVP\\TTLs\\TTL_DragonMesh"
GNR_SLICE_TTL  = "S:\\GNR\\RVP\\TTLs\\TTL_DragonSlice"
GNR_LINUX_TTL  = "Q:\\DPM_Debug\\GNR\\TTL_Linux"
GNR_CONTENT_CP = "FS1:\\content\\Dragon\\7410_0x0E_PPV_MegaMem\\GNR128C_H_1UP\\"
GNR_SLICE_CP   = "FS1:\\content\\Dragon\\GNR1C_Q_Slice_2M_pseudoSBFT_System"
GNR_BOOT_CP    = "FS1:\\content\\Dragon\\GNR50C_L_MOSBFT_HToff_pseudoSBFT_System\\"
GNR_MERLIN     = "FS1:\\EFI\\Version8.15\\BinFiles\\Release"


def _gnr_dragon_overlay(e, cp, vvar0="0x4C4B40", vvar2="0x1000000", vvar3="0x4000000"):
    e["ULX Path"]           = "FS1:\\EFI\\ulx"
    e["ULX CPU"]            = "GNR_B0"
    e["Product Chop"]       = "GNR"
    e["Startup Dragon"]     = "startup_efi.nsh"
    e["Dragon Content Path"]= cp
    e["VVAR0"]  = vvar0
    e["VVAR1"]  = "80064000"
    e["VVAR2"]  = vvar2
    e["VVAR3"]  = vvar3
    e["Merlin Name"]  = "MerlinX.efi"
    e["Merlin Drive"] = "FS1:"
    e["Merlin Path"]  = GNR_MERLIN


def _gnr_boot(test_name, test_no, loops=2, reset=True, bb=None,
              mask=None, check_core=0, scripts=None, test_type="Loops",
              sweep_type=None, sweep_domain=None,
              sweep_start=None, sweep_end=None, sweep_steps=None):
    e = _blank_exp()
    e.update({
        "Test Name": test_name,
        "Test Mode": "Mesh",
        "Test Type": test_type,
        "Content": "PYSVConsole",
        "Test Number": test_no,
        "Reset": reset, "Reset on PASS": reset,
        "Boot Breakpoint": bb,
        "Check Core": check_core,
        "Loops": loops,
        "Configuration (Mask)": mask,
        "TTL Folder": GNR_BOOT_TTL,
        "Scripts File": scripts or GNR_BOOT_SCRP,
        "Linux Content Wait Time": 0,
        "Type": sweep_type, "Domain": sweep_domain,
        "Start": sweep_start, "End": sweep_end, "Steps": sweep_steps,
    })
    _gnr_dragon_overlay(e, GNR_BOOT_CP)
    return e


def _gnr_dragon_content(test_name, test_no, mode="Mesh", loops=5,
                        check=36, fast=True, config=None,
                        vvar0="0x4C4B40", vvar2="0x1000000", vvar3="0x4000000",
                        cp=None, ttl=None, line=None,
                        test_type="Loops",
                        sweep_type=None, sweep_domain=None,
                        sweep_start=None, sweep_end=None, sweep_steps=None,
                        vtype="vbump", vIA=None, vCFC=None, fIA=None, fCFC=None):
    e = _blank_exp()
    cp  = cp  or GNR_CONTENT_CP
    ttl = ttl or GNR_MESH_TTL
    e.update({
        "Test Name": test_name,
        "Test Mode": mode,
        "Test Type": test_type,
        "Content": "Dragon",
        "Test Number": test_no,
        "FastBoot": fast,
        "Check Core": check,
        "Loops": loops,
        "Configuration (Mask)": config,
        "Voltage Type": vtype,
        "Voltage IA": vIA, "Voltage CFC": vCFC,
        "Frequency IA": fIA, "Frequency CFC": fCFC,
        "Dragon Content Line": line,
        "TTL Folder": ttl,
        "Type": sweep_type, "Domain": sweep_domain,
        "Start": sweep_start, "End": sweep_end, "Steps": sweep_steps,
    })
    _gnr_dragon_overlay(e, cp, vvar0=vvar0, vvar2=vvar2, vvar3=vvar3)
    return e


# ── GNR boot_cases ──────────────────────────────────────────────────────────
gnr_boot = {}

gnr_boot["gnr_boot_baseline"] = _preset(
    "GNR — Boot Baseline",
    "Standard GNR boot loop (PYSVConsole). Most common starting point for boot-failure investigation.",
    ["GNR"], ASK_BOOT,
    _gnr_boot("Baseline", 11))

gnr_boot["gnr_boot_issue"] = _preset(
    "GNR — Boot Issue",
    "Non-resetting boot loop. Halts at 0xbf000000 breakpoint for live debug access.",
    ["GNR"], ASK_BOOT,
    _gnr_boot("BootIssue", 10, loops=1, reset=False, bb="0xbf000000"))

for key, lbl, dom, typ, s, en, st, no, desc in [
    ("gnr_bootissue_vbcfc",  "GNR — Boot vbump CFC Sweep",    "CFC", "Voltage",    0.0,  0.2,  0.05, 20,
     "Boot sweep on CFC voltage domain. Margin characterization for non-booting debug."),
    ("gnr_bootissue_vbia",   "GNR — Boot vbump IA Sweep",     "IA",  "Voltage",    0.0,  0.2,  0.05, 30,
     "Boot sweep on IA voltage domain."),
    ("gnr_bootissue_flatcfc","GNR — Boot CFC Frequency Flat", "CFC", "Frequency",  8.0, 22.0,  4.0,  40,
     "Boot frequency sweep on CFC domain (8-22 GHz, 4 GHz steps)."),
    ("gnr_bootissue_flatia", "GNR — Boot IA Frequency Flat",  "IA",  "Frequency",  8.0, 32.0,  4.0,  50,
     "Boot frequency sweep on IA domain (8-32 GHz, 4 GHz steps)."),
]:
    gnr_boot[key] = _preset(lbl, desc, ["GNR"], ASK_SWEEP,
        _gnr_boot(key.split("gnr_")[-1], no, test_type="Sweep",
                  reset=False, bb="0xbf000000", loops=2,
                  sweep_type=typ, sweep_domain=dom,
                  sweep_start=s, sweep_end=en, sweep_steps=st))

for key, mask_val, no in [
    ("gnr_maskcheck_firstpass",  "FirstPass",  101),
    ("gnr_maskcheck_secondpass", "SecondPass", 102),
    ("gnr_maskcheck_thirdpass",  "ThirdPass",  103),
    ("gnr_maskcheck_rowpass1",   "RowPass1",   201),
    ("gnr_maskcheck_rowpass2",   "RowPass2",   202),
    ("gnr_maskcheck_rowpass3",   "RowPass3",   203),
]:
    gnr_boot[key] = _preset(
        f"GNR — Mask Check {mask_val}",
        f"Boot loop using ATE mask '{mask_val}'. Isolates failing core regions during debug.",
        ["GNR"], ASK_BOOT,
        _gnr_boot(f"MaskChecks_{mask_val}", no, loops=1, reset=False,
                  bb="0xbf000000", mask=mask_val))

gnr_boot["gnr_fuse_collection"] = _preset(
    "GNR — Fuse Collection",
    "Runs fuse_generation.txt. Collects fuse override values for margin tuning.",
    ["GNR"], ASK_BOOT,
    _gnr_boot("FuseCollection", 10, loops=1, reset=False,
              bb="0xbf000000", check_core=None, scripts=GNR_FUSE_SCRP))

# ── GNR content_cases ───────────────────────────────────────────────────────
gnr_content = {}

gnr_content["gnr_baseline"] = _preset(
    "GNR — Baseline Dragon (vbump)",
    "Standard GNR mesh Dragon loop. vbump mode. Check Core 36.",
    ["GNR"], ASK_LOOPS,
    _gnr_dragon_content("Baseline", 11))

gnr_content["gnr_baseline_ppvc"] = _preset(
    "GNR — Baseline Dragon (ppvc)",
    "GNR mesh Dragon loop with PPVC voltage mode. VVAR0=0x1C9C380.",
    ["GNR"], ASK_LOOPS,
    _gnr_dragon_content("BaselinePPVC", 11, vtype="ppvc", vvar0="0x1C9C380"))

gnr_content["gnr_baseline_xtended"] = _preset(
    "GNR — Baseline Extended (ppvc)",
    "Extended GNR mesh loop. PPVC + VVAR0=0x989680.",
    ["GNR"], ASK_LOOPS,
    _gnr_dragon_content("BaselineXtended", 11, vtype="ppvc", vvar0="0x989680"))

_e = _gnr_dragon_content("Slice_TSL_mini", 1, mode="Slice",
                          check=36, config=36, ttl=GNR_SLICE_TTL,
                          cp=GNR_SLICE_CP, vvar2="0x1000002")
_e["600W Unit"] = True
_e["Startup Linux"] = "startup_linux.nsh"
_e["Linux Content Wait Time"] = 999999
_e["Linux Content Line 0"] = (
    "/usr/local/bin/ocelot --flow /root/content/LOS/LOS-23WW24/Mlc/flows/"
    "Mlc_mp1.xml --write_log_file_to_stdout=on --ituff=on")
_e["Linux Content Line 1"] = (
    "/usr/local/bin/ocelot --flow /root/content/LOS/LOS-23WW24/Mlc/flows/"
    "Mlc_data_integrity.xml --write_log_file_to_stdout=on --ituff=on")
gnr_content["gnr_slice_tsltiny"] = _preset(
    "GNR — Slice TSL Mini",
    "Single-core Slice mode (core 36). Runs TSL MLC ocelot flows under Linux.",
    ["GNR"], ASK_SLICE, _e)

for key, lbl, dom, typ, s, en, st, cfg, fast, desc in [
    ("gnr_cfc_voltage",   "GNR — CFC Voltage Sweep",       "CFC", "Voltage",    0.05, 0.2,  0.05, None, True,
     "CFC voltage sweep. Start=0.05 V, End=0.2 V, Steps=0.05."),
    ("gnr_cfc_frequency", "GNR — CFC Frequency Flat",      "CFC", "Frequency",  8.0, 22.0,  4.0,  None, True,
     "CFC frequency sweep 8-22 GHz, 4 GHz steps."),
    ("gnr_ia_voltage",    "GNR — IA Voltage Sweep",        "IA",  "Voltage",    0.05, 0.2,  0.05, None, True,
     "IA voltage sweep. Start=0.05 V, End=0.2 V, Steps=0.05."),
    ("gnr_ia_freq_lo",    "GNR — IA Frequency Low",        "IA",  "Frequency",  8.0, 32.0,  4.0,  None, True,
     "IA frequency sweep 8-32 GHz, 4 GHz steps."),
    ("gnr_ia_freq_hi",    "GNR — IA Frequency High",       "IA",  "Frequency", 36.0, 40.0,  4.0, "FirstPass", False,
     "High-end IA frequency sweep 36-40 GHz, 4 GHz steps. Uses FirstPass ATE mask."),
]:
    gnr_content[key] = _preset(lbl, desc, ["GNR"], ASK_SWEEP,
        _gnr_dragon_content(key, 11, test_type="Sweep", fast=fast, config=cfg,
                            sweep_type=typ, sweep_domain=dom,
                            sweep_start=s, sweep_end=en, sweep_steps=st))

def _gnr_linux_base(test_name, test_no, ttl=GNR_LINUX_TTL):
    e = _blank_exp()
    e.update({
        "Test Name": test_name, "Test Mode": "Mesh", "Test Type": "Loops",
        "Content": "Linux", "Test Number": test_no,
        "FastBoot": True, "Check Core": 36, "600W Unit": True, "Loops": 5,
        "Pass String": "exit: pass", "Fail String": "exit: fail",
        "TTL Folder": ttl,
    })
    _gnr_dragon_overlay(e, GNR_CONTENT_CP)
    e["Startup Linux"] = "startup_linux.nsh"
    e["Linux Content Wait Time"] = 999999
    return e


for key, name, loop_flag, path, desc in [
    ("gnr_tsl3s_breadth", "TSL3s_Breadth", 3000, "GNR1C_breadth_HT.list",
     "3s breadth TSL; tests wide memory access patterns."),
    ("gnr_tsl1s_breadth", "TSL1s_Breadth", 1000, "GNR1C_breadth_HT.list",
     "1s breadth TSL; quicker breadth screen."),
    ("gnr_tsl3s_br",      "TSL3s_BR",      3000, "GNR1C_BR_HT.list",
     "3s bit-reverse TSL; targets bit-reversal addressing patterns."),
    ("gnr_tsl1s_br",      "TSL1s_BR",      1000, "GNR1C_BR_HT.list",
     "1s bit-reverse TSL; quicker BR screen."),
]:
    _e = _gnr_linux_base(name, 9)
    _e["Linux Path"] = "cd /root/content/DPM/TSL"
    _e["Linux Content Line 0"] = (
        f"/root/content/LOS/TSL/bin/tslengine "
        f"-F /root/content/DPM/TSL/{path} "
        f"-L {loop_flag} -z test_{loop_flag}.log -o -r 10")
    gnr_content[key] = _preset(
        f"GNR — {name}",
        f"GNR {desc}",
        ["GNR"], ASK_LINUX, _e)

_e = _gnr_linux_base("MLC", 9)
_e["Pass String"] = "Result=SUCCESS"; _e["Fail String"] = "Result=FAILED"
_e["Linux Path"] = "cd /root/content/DPM/MLC"
_e["Linux Content Line 0"] = "/usr/local/bin/ocelot --flow /root/content/LOS/LOS-23WW24/Mlc/flows/Mlc.xml --write_log_file_to_stdout=on"
_e["Linux Content Line 1"] = "/usr/local/bin/ocelot --flow /root/content/LOS/LOS-23WW24/Mlc/flows/Mlc_data_integrity.xml --write_log_file_to_stdout=on"
_e["Linux Content Line 2"] = "/usr/local/bin/ocelot --flow /root/content/LOS/LOS-23WW24/Mlc/flows/Mlc_mp1.xml --write_log_file_to_stdout=on"
_e["Linux Content Line 3"] = "/usr/local/bin/ocelot --flow /root/content/LOS/LOS-23WW24/Mlc/flows/Mlc_mp2.xml --write_log_file_to_stdout=on"
gnr_content["gnr_mlc"] = _preset("GNR — MLC (Memory Latency Checker)",
    "GNR MLC ocelot 4-flow suite. Memory bandwidth and latency characterization.",
    ["GNR"], ASK_LINUX, _e)

_e = _gnr_linux_base("Sandstone", 9)
_e["Linux Path"] = "cd /root/content/DPM/Sandstone"
_e["Linux Content Line 0"] = "/root/content/LOS/TSL/bin/sandstone --max-test-loop-count=5 -t 200 -vv -o 0304_nominal_alltest.log"
gnr_content["gnr_sandstone"] = _preset("GNR — Sandstone",
    "GNR Sandstone memory stress test (5 loops, 200s timeout, -vv).",
    ["GNR"], ASK_LINUX, _e)

# ── GNR fuse_collection ─────────────────────────────────────────────────────
gnr_fuse = {}
gnr_fuse["gnr_fuse_collection"] = _preset(
    "GNR — Fuse Collection",
    "Runs fuse_generation.txt. Generates fuse override values for margin analysis.",
    ["GNR"], ASK_BOOT,
    _gnr_boot("FuseCollection", 10, loops=1, reset=False,
              bb="0xbf000000", check_core=None, scripts=GNR_FUSE_SCRP))


# ════════════════════════════════════════════════════════════════════════════
#  CWF
# ════════════════════════════════════════════════════════════════════════════

CWF_MESH_TTL  = "R:/Templates/CWF/version_2_0/TTL_DragonMesh"
CWF_SLICE_TTL = "R:\\Templates\\CWF\\version_2_0\\TTL_DragonSlice"
CWF_LINUX_TTL = "R:\\Templates\\CWF\\version_2_0\\TTL_Linux"
CWF_BOOT_TTL  = "R:/Templates/CWF/version_1_0/TTL_Boot"
CWF_CP        = "FS1:\\content\\Dragon\\7834_0x43_PPV_MegaMem\\CWF72M_H_1UP\\"
CWF_MERLIN    = "FS1:\\EFI\\Version8.15\\BinFiles\\Release"
CWF_FUSE_SCRP = "R:/Templates/scripts/fuse_generation.txt"


def _cwf_dragon_overlay(e, cp=None, vvar0="0x4C4B40", vvar1="80064000",
                         vvar2="0x1000000", vvar3="0x4000000"):
    cp = cp or CWF_CP
    e["ULX Path"]           = "FS1:\\EFI\\ulx"
    e["ULX CPU"]            = "CWF_B0"
    e["Product Chop"]       = "CWF"
    e["Startup Dragon"]     = "startup_efi.nsh"
    e["Dragon Content Path"]= cp
    e["VVAR0"]  = vvar0
    e["VVAR1"]  = vvar1
    e["VVAR2"]  = vvar2
    e["VVAR3"]  = vvar3
    e["Merlin Name"]  = "MerlinX.efi"
    e["Merlin Drive"] = "FS1:"
    e["Merlin Path"]  = CWF_MERLIN


def _cwf_content(test_name, test_no, loops=2, check=7, fast=True, config=None,
                 mode="Mesh", ttl=None, line=None, vtype="vbump",
                 vvar0="0x4C4B40", vvar1="80064000", vvar2="0x1000000", vvar3="0x4000000",
                 vIA=None, vCFC=None, fIA=None, fCFC=None, test_type="Loops",
                 sweep_type=None, sweep_domain=None,
                 sweep_start=None, sweep_end=None, sweep_steps=None,
                 cp=None, stop_fail=True):
    e = _blank_exp()
    ttl = ttl or CWF_MESH_TTL
    e.update({
        "Test Name": test_name, "Test Mode": mode,
        "Test Type": test_type, "Content": "Dragon", "Test Number": test_no,
        "COM Port": 11, "IP Address": "10.250.0.2",
        "FastBoot": fast, "Check Core": check, "Loops": loops,
        "Configuration (Mask)": config, "Voltage Type": vtype,
        "Voltage IA": vIA, "Voltage CFC": vCFC,
        "Frequency IA": fIA, "Frequency CFC": fCFC,
        "Dragon Content Line": line, "TTL Folder": ttl,
        "Type": sweep_type, "Domain": sweep_domain,
        "Start": sweep_start, "End": sweep_end, "Steps": sweep_steps,
        "Stop on Fail": stop_fail,
    })
    _cwf_dragon_overlay(e, cp=cp, vvar0=vvar0, vvar1=vvar1, vvar2=vvar2, vvar3=vvar3)
    return e


cwf_content = {}

cwf_content["cwf_base_drag_h"] = _preset(
    "CWF — Base Dragon H (vbump)",
    "Standard CWF Dragon mesh loop. Check Core 7. vbump mode with Volt/Freq hints.",
    ["CWF"], ASK_LOOPS,
    _cwf_content("BaseDragonH", 1, vIA=0.02, vCFC=0.01, fIA=8, fCFC=12, line="Demo"))

cwf_content["cwf_base_ppvc"] = _preset(
    "CWF — Base Dragon PPVC",
    "CWF PPVC mode Dragon loop. VVAR1=0x80064000.",
    ["CWF"], ASK_LOOPS,
    _cwf_content("BasePPVC", 2, vtype="ppvc", vvar1="0x80064000", line="Demo, Ditto"))

cwf_content["cwf_base_extend"] = _preset(
    "CWF — Base Dragon Extended (ppvc)",
    "Extended PPVC mode. VVAR0=0x989680, VVAR1=0x80064000.",
    ["CWF"], ASK_LOOPS,
    _cwf_content("BaseExtend", 3, vtype="ppvc",
                 vvar0="0x989680", vvar1="0x80064000", line="Demo, Ditto"))

for key, lbl, dom, typ, s, en, st, no, desc in [
    ("cwf_cfc_vbp",   "CWF — CFC Voltage (vbP)",   "CFC", "Voltage",   -0.03, 0.06, 0.03, 10,
     "CWF CFC voltage bump sweep. Range -0.03 to +0.06 V, 0.03 V steps. 3 loops."),
    ("cwf_cfc_flats", "CWF — CFC Frequency Flats",  "CFC", "Frequency",  8.0, 12.0,  4.0, 11,
     "CWF CFC frequency flat sweep. 8-12 GHz, 4 GHz steps."),
    ("cwf_ia_vbp",    "CWF — IA Voltage (vbP)",     "IA",  "Voltage",   -0.03, 0.06, 0.03, 20,
     "CWF IA voltage bump sweep. Range -0.03 to +0.06 V, 0.03 V steps."),
    ("cwf_ia_flats",  "CWF — IA Frequency Flats",   "IA",  "Frequency",  8.0, 12.0,  4.0, 21,
     "CWF IA frequency flat sweep. 8-12 GHz, 4 GHz steps."),
]:
    cwf_content[key] = _preset(lbl, desc, ["CWF"], ASK_SWEEP,
        _cwf_content(key, no, loops=3, fast=False, test_type="Sweep",
                     sweep_type=typ, sweep_domain=dom,
                     sweep_start=s, sweep_end=en, sweep_steps=st))

_e = _cwf_content("BaseLineLinux", 11, check=7, ttl=CWF_LINUX_TTL, fast=True, loops=1)
_e["Content"] = "Linux"
_e["Scripts File"]  = "C:\\SystemDebug\\pre_execution.txt"
_e["Post Process"]  = "C:\\SystemDebug\\post_execution.txt"
_e["Startup Linux"] = "startup_linux.nsh"
_e["Linux Content Wait Time"] = 999999
_e["Linux Content Line 0"] = (
    "/usr/local/bin/ocelot --flow /root/content/LOS/LOS-23WW24/Mlc/flows/"
    "Mlc_mp2.xml --write_log_file_to_stdout=on --ituff=on")
cwf_content["cwf_linux_baseline"] = _preset(
    "CWF — Baseline Linux (MLC)",
    "CWF Linux baseline using MLC ocelot mp2 flow.",
    ["CWF"], ASK_LINUX, _e)

_e = _cwf_content("BaseLineSlice", 11, check=7, config=7,
                   mode="Slice", ttl=CWF_SLICE_TTL, vvar2="0x1000002", line="Demo")
_e["ULX CPU"] = "CWF"
_e["Scripts File"] = "C:\\SystemDebug\\pre_execution.txt"
_e["Post Process"]  = "C:\\SystemDebug\\post_execution.txt"
cwf_content["cwf_slice_baseline"] = _preset(
    "CWF — Baseline Slice (Dragon)",
    "Single-core Slice targeting CWF core 7. Dragon content with pseudoSBFT.",
    ["CWF"], ASK_SLICE, _e)

# ── CWF fuse_collection ─────────────────────────────────────────────────────
cwf_fuse = {}
_e = _blank_exp()
_e.update({
    "Test Name": "FuseCollection", "Test Mode": "Mesh", "Test Type": "Loops",
    "Content": "PYSVConsole", "Test Number": 10,
    "COM Port": 11, "IP Address": "10.250.0.2",
    "Reset": False, "Reset on PASS": False,
    "Boot Breakpoint": "0xbf000000", "Check Core": None, "Loops": 1,
    "TTL Folder": CWF_BOOT_TTL,
    "Scripts File": CWF_FUSE_SCRP,
    "Linux Content Wait Time": 0,
})
_cwf_dragon_overlay(_e)
cwf_fuse["cwf_fuse_collection"] = _preset(
    "CWF — Fuse Collection",
    "Runs fuse_generation.txt with CWF paths. Generates CWF fuse override values.",
    ["CWF"], ASK_BOOT, _e)


# ════════════════════════════════════════════════════════════════════════════
#  DMR
# ════════════════════════════════════════════════════════════════════════════

DMR_MESH_TTL  = "R:\\Templates\\DMR\\version_2_0\\TTL_DragonMesh"
DMR_SLICE_TTL = "R:/Templates/DMR/version_2_0/TTL_DragonSlice"
DMR_BOOT_TTL  = "R:/Templates/DMR/version_1_0/TTL_Boot"
DMR_CP_H      = "FS1:\\content\\Dragon\\8154_0x5D_PPV_prelim\\DMR128M_H_1UP\\"
DMR_CP_M      = "FS1:\\content\\Dragon\\8154_0x5D_PPV_prelim\\DMR128M_M_1UP\\"
DMR_CP_R      = "FS1:\\content\\Dragon\\8154_0x5D_PPV_prelim\\DMR128M_R_1UP\\"
DMR_CP_SLICE  = "FS1:\\content\\Dragon\\8059_0x55_Slice\\DMR1M_Q_Slice_4M_pseudoSBFT_Tester\\"
DMR_CP_RO     = "FS1:\\content\\Dragon\\8142_0x552_RO\\DMR32M_L_RO_Bcast_pseudoSBFT_Tester\\"
DMR_MERLIN    = "FS1:\\EFI\\Version8.23\\BinFiles\\Release"
DMR_FUSE_SCRP = "R:/Templates/scripts/fuse_generation_dmr.txt"
DMR_BOOT_SCRP = "R:/Templates/scripts/boot_example_dmr.txt"


def _dmr_dragon_overlay(e, cp, vvar0="0x4C4B40", vvar1="80064000",
                         vvar2="0x1000000", vvar3="0x4200000"):
    e["ULX Path"]           = "FS1:\\EFI\\ulx"
    e["ULX CPU"]            = "DMR"
    e["Product Chop"]       = "DMR"
    e["Startup Dragon"]     = "startup_efi.nsh"
    e["Dragon Content Path"]= cp
    e["VVAR0"]  = vvar0
    e["VVAR1"]  = vvar1
    e["VVAR2"]  = vvar2
    e["VVAR3"]  = vvar3
    e["Merlin Name"]  = "MerlinX.efi"
    e["Merlin Drive"] = "FS1:"
    e["Merlin Path"]  = DMR_MERLIN


def _dmr_content(test_name, test_no, cp, loops=2, check=24, config=None,
                 mode="Mesh", fast=False, ttl=None, line=None,
                 vvar0="0x4C4B40", vvar1="80064000", vvar2="0x1000000", vvar3="0x4200000",
                 post=None, disable1=None, stop_fail=True,
                 test_type="Loops",
                 sweep_type=None, sweep_domain=None,
                 sweep_start=None, sweep_end=None, sweep_steps=None):
    e = _blank_exp()
    ttl = ttl or DMR_MESH_TTL
    e.update({
        "Test Name": test_name, "Test Mode": mode,
        "Test Type": test_type, "Content": "Dragon", "Test Number": test_no,
        "COM Port": 9, "IP Address": "192.168.0.2",
        "FastBoot": fast, "Check Core": check, "Loops": loops,
        "Configuration (Mask)": config,
        "Post Process": post, "Dragon Content Line": line, "TTL Folder": ttl,
        "Disable 1 Core": disable1, "Stop on Fail": stop_fail,
        "Type": sweep_type, "Domain": sweep_domain,
        "Start": sweep_start, "End": sweep_end, "Steps": sweep_steps,
    })
    _dmr_dragon_overlay(e, cp, vvar0=vvar0, vvar1=vvar1, vvar2=vvar2, vvar3=vvar3)
    return e


dmr_content = {}

dmr_content["dmr_dragon_base_h"] = _preset(
    "DMR — Dragon Base H",
    "Standard DMR Dragon mesh loop (H bin). Check Core 24. Includes TOR dump post-process.",
    ["DMR"], ASK_LOOPS,
    _dmr_content("DragonBaseH", 11, DMR_CP_H, vvar1="0x80064000",
                 post="R:/Templates/scripts/dmr_tor_dump.txt"))

dmr_content["dmr_dragon_base_m"] = _preset(
    "DMR — Dragon Base M",
    "DMR Dragon mesh loop — M bin content. No post-process.",
    ["DMR"], ASK_LOOPS,
    _dmr_content("DragonBaseM", 11, DMR_CP_M))

dmr_content["dmr_dragon_base_r"] = _preset(
    "DMR — Dragon Base R",
    "DMR Dragon mesh loop — R bin content.",
    ["DMR"], ASK_LOOPS,
    _dmr_content("DragonBaseR", 11, DMR_CP_R))

for key, lbl, dom, typ, s, en, st, no, desc in [
    ("dmr_cfc_vbp",   "DMR — CFC Voltage (vbP)",   "CFC", "Voltage",   -0.03, 0.06, 0.03, 20,
     "DMR CFC voltage bump sweep. Range -0.03 to +0.06 V, 0.03 V steps."),
    ("dmr_cfc_flatr", "DMR — CFC Frequency Flat",   "CFC", "Frequency",  8.0, 12.0,  4.0, 21,
     "DMR CFC frequency flat sweep. 8-12 GHz, 4 GHz steps."),
    ("dmr_ia_flatr",  "DMR — IA Frequency Flat",    "IA",  "Frequency",  8.0, 24.0,  4.0, 31,
     "DMR IA frequency flat sweep. 8-24 GHz, 4 GHz steps."),
    ("dmr_ia_vbp",    "DMR — IA Voltage (vbP)",     "IA",  "Voltage",   -0.03, 0.06, 0.03, 30,
     "DMR IA voltage bump sweep. Range -0.03 to +0.06 V, 0.03 V steps."),
]:
    dmr_content[key] = _preset(lbl, desc, ["DMR"], ASK_SWEEP,
        _dmr_content(key, no, DMR_CP_H, loops=3, test_type="Sweep",
                     sweep_type=typ, sweep_domain=dom,
                     sweep_start=s, sweep_end=en, sweep_steps=st))

dmr_content["dmr_slice_base"] = _preset(
    "DMR — Dragon Base Slice",
    "DMR single-core Slice mode (core 24). Slice pseudoSBFT tester content.",
    ["DMR"], ASK_SLICE,
    _dmr_content("DragonBaseSlice", 11, DMR_CP_SLICE, check=24, config=24,
                  mode="Slice", ttl=DMR_SLICE_TTL, line="Demo, Leekspin",
                  vvar0="0x2dc6c0", vvar2="0x1000002", vvar3="0x4210000",
                  stop_fail=False))

# COREHI / CORELO — full mesh
dmr_content["dmr_corehi"] = _preset(
    "DMR — Dragon Base COREHI (Core 1)",
    "DMR RO mesh targeting Core 1 (higher). Disable 1 Core = 0x2.",
    ["DMR"], ASK_CORE,
    _dmr_content("DragonBaseCOREHI", 11, DMR_CP_RO, line="Ditto, Twiddle",
                  vvar1="0x80064000", disable1="0x2", stop_fail=False))

dmr_content["dmr_corelo"] = _preset(
    "DMR — Dragon Base CORELO (Core 0)",
    "DMR RO mesh targeting Core 0 (lower). Disable 1 Core = 0x1.",
    ["DMR"], ASK_CORE,
    _dmr_content("DragonBaseCORELO", 11, DMR_CP_RO, line="Ditto, Twiddle",
                  vvar1="0x80064000", disable1="0x1", stop_fail=False))

# CBB Slices
for key, name, cfg, chk, line_ in [
    ("dmr_slice_cbb0",    "Slice_CBB0",    7,   7,   None),
    ("dmr_slice_cbb1_32", "Slice_CBB1_32", 32,  32,  None),
    ("dmr_slice_cbb1_48", "Slice_CBB1_48", 48,  48,  None),
    ("dmr_slice_cbb2",    "Slice_CBB2",    84,  84,  "Demo, Yakko"),
    ("dmr_slice_cbb3",    "Slice_CBB3",    126, 126, "Demo, Scylla"),
]:
    cbb_lbl = name.split("_CBB")[1].split("_")[0]
    dmr_content[key] = _preset(
        f"DMR — {name}",
        f"DMR Slice CBB{cbb_lbl} targeting Check Core={chk}. pseudoSBFT slice content.",
        ["DMR"], ASK_SLICE,
        _dmr_content(name, 11, DMR_CP_SLICE, check=chk, config=cfg,
                      mode="Slice", ttl=DMR_SLICE_TTL, line=line_,
                      vvar0="0x2dc6c0", vvar2="0x1000002", vvar3="0x4210000",
                      stop_fail=False))

# COREHI/CORELO CBB
for key, name, cfg, chk, d1 in [
    ("dmr_corehi_cbb0",   "DragonBaseCOREHI_CBB0",   "Cbb0", 0,   "0x2"),
    ("dmr_corehi_cbb1",   "DragonBaseCOREHI_CBB1",   "Cbb1", 32,  "0x2"),
    ("dmr_corelo_cbb2",   "DragonBaseCORELO_CBB2",   "Cbb2", 64,  "0x1"),
    ("dmr_corelo_cbb3",   "DragonBaseCORELO_CBB3",   "Cbb2", 104, "0x1"),
]:
    core_str = "COREHI (Core 1)" if d1 == "0x2" else "CORELO (Core 0)"
    dmr_content[key] = _preset(
        f"DMR — {core_str} {cfg}",
        f"DMR RO mesh targeting {core_str}, ATE mask {cfg}, Check Core={chk}.",
        ["DMR"], ASK_CORE_NO_LOOPS,
        _dmr_content(name, 100, DMR_CP_RO, check=chk, config=cfg,
                      vvar1="0x80064000", disable1=d1, stop_fail=False))

# COREHI/CORELO Compute
for key, name, cfg, chk, d1 in [
    ("dmr_corehi_compute0", "DragonBaseCOREHI_Compute0", "Compute0", 32, "0x2"),
    ("dmr_corehi_compute1", "DragonBaseCOREHI_Compute1", "Compute1", 32, "0x2"),
    ("dmr_corelo_compute2", "DragonBaseCORELO_Compute2", "Compute2", 48, "0x1"),
    ("dmr_corelo_compute3", "DragonBaseCORELO_Compute3", "Compute3", 32, "0x1"),
]:
    core_str = "COREHI (Core 1)" if d1 == "0x2" else "CORELO (Core 0)"
    dmr_content[key] = _preset(
        f"DMR — {core_str} {cfg}",
        f"DMR RO mesh targeting {core_str}, ATE mask {cfg}, Check Core={chk}.",
        ["DMR"], ASK_CORE_NO_LOOPS,
        _dmr_content(name, 100, DMR_CP_RO, check=chk, config=cfg,
                      vvar1="0x80064000", disable1=d1, stop_fail=False))

# ── DMR boot_cases ───────────────────────────────────────────────────────────
dmr_boot = {}
_e = _blank_exp()
_e.update({
    "Test Name": "BootBaseline", "Test Mode": "Mesh", "Test Type": "Loops",
    "Content": "PYSVConsole", "Test Number": 100,
    "COM Port": 9, "IP Address": "192.168.0.2",
    "Reset": False, "Reset on PASS": False,
    "Boot Breakpoint": "0xbf000000", "Check Core": 32, "Loops": 2,
    "TTL Folder": DMR_BOOT_TTL,
    "Scripts File": DMR_BOOT_SCRP,
    "Linux Content Wait Time": 0,
})
dmr_boot["dmr_boot_baseline"] = _preset(
    "DMR — Boot Baseline",
    "DMR boot baseline (PYSVConsole). Halts at 0xbf000000. Check Core 32. No reset.",
    ["DMR"], ASK_BOOT, _e)

# ── DMR fuse_collection ──────────────────────────────────────────────────────
dmr_fuse = {}
_e = _blank_exp()
_e.update({
    "Test Name": "FuseGenerator", "Test Mode": "Mesh", "Test Type": "Loops",
    "Content": "PYSVConsole", "Test Number": 100,
    "COM Port": 9, "IP Address": "192.168.0.2",
    "Reset": False, "Reset on PASS": False,
    "Boot Breakpoint": "0xbf000000", "Check Core": 32, "Loops": 2,
    "TTL Folder": DMR_BOOT_TTL,
    "Scripts File": DMR_FUSE_SCRP,
    "Linux Content Wait Time": 0,
})
dmr_fuse["dmr_fuse_generator"] = _preset(
    "DMR — Fuse Generator",
    "Runs fuse_generation_dmr.txt. DMR-specific fuse override generation.",
    ["DMR"], ASK_BOOT, _e)


# ════════════════════════════════════════════════════════════════════════════
#  WRITE FILE
# ════════════════════════════════════════════════════════════════════════════

data["GNR"] = {
    "boot_cases":     gnr_boot,
    "content_cases":  gnr_content,
    "fuse_collection": gnr_fuse,
}
data["CWF"] = {
    "boot_cases":     {},
    "content_cases":  cwf_content,
    "fuse_collection": cwf_fuse,
}
data["DMR"] = {
    "boot_cases":     dmr_boot,
    "content_cases":  dmr_content,
    "fuse_collection": dmr_fuse,
}

PRESETS_FILE.write_text(
    json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8"
)

# Verify
result = json.loads(PRESETS_FILE.read_text(encoding="utf-8"))
counts = {
    "common":      len(result["common"]),
    "GNR boot":    len(result["GNR"]["boot_cases"]),
    "GNR content": len(result["GNR"]["content_cases"]),
    "GNR fuse":    len(result["GNR"]["fuse_collection"]),
    "CWF content": len(result["CWF"]["content_cases"]),
    "CWF fuse":    len(result["CWF"]["fuse_collection"]),
    "DMR boot":    len(result["DMR"]["boot_cases"]),
    "DMR content": len(result["DMR"]["content_cases"]),
    "DMR fuse":    len(result["DMR"]["fuse_collection"]),
}
total = sum(counts.values())
print("Preset counts:", counts)
print(f"Total presets : {total}")
print(f"File size     : {PRESETS_FILE.stat().st_size:,} bytes")
print("OK — file written successfully.")
