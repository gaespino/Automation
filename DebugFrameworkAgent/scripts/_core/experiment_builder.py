"""
experiment_builder.py — Build, populate, and validate experiment dicts.

Provides product-aware blank experiments, preset application, and
all validation rules from experiment_generator.skill.md Section 5.
No external dependencies.
"""

from __future__ import annotations
import copy
import json
import pathlib
import re
from typing import Any

from . import constraints as _c

# --------------------------------------------------------------------------
# Product-specific defaults  (Skill Section 10)
# --------------------------------------------------------------------------

PRODUCT_DEFAULTS: dict[str, dict] = {
    "GNR": {
        "Check Core":   36,
        "COM Port":     11,
        "IP Address":   "192.168.0.2",
        "ULX CPU":      "GNR_B0",
        "Product Chop": "GNR",
        "VVAR3":        "0x4000000",
        "VVAR3_slice":  "0x4000000",
        "VVAR2":        "0x1000000",
        "VVAR2_slice":  "0x1000002",
        "Merlin Path":  "FS1:\\EFI\\Version8.15\\BinFiles\\Release",
        "FastBoot":     True,
        "FastBoot_sweep": True,
    },
    "CWF": {
        "Check Core":   7,
        "COM Port":     11,
        "IP Address":   "10.250.0.2",
        "ULX CPU":      "CWF_B0",
        "Product Chop": "CWF",
        "VVAR3":        "0x4000000",
        "VVAR3_slice":  "0x4000000",
        "VVAR2":        "0x1000000",
        "VVAR2_slice":  "0x1000002",
        "Merlin Path":  "FS1:\\EFI\\Version8.15\\BinFiles\\Release",
        "FastBoot":     True,
        "FastBoot_sweep": False,
    },
    "DMR": {
        "Check Core":   24,
        "COM Port":     9,
        "IP Address":   "192.168.0.2",
        "ULX CPU":      "DMR",
        "Product Chop": "DMR",
        "VVAR3":        "0x4200000",
        "VVAR3_slice":  "0x4210000",
        "VVAR2":        "0x1000000",
        "VVAR2_slice":  "0x1000002",
        "Merlin Path":  "FS1:\\EFI\\Version8.23\\BinFiles\\Release",
        "FastBoot":     False,
        "FastBoot_sweep": False,
    },
}

TTL_DEFAULTS: dict[str, dict[str, str]] = {
    "GNR": {
        "boot":    "R:/Templates/GNR/version_1_0/TTL_Boot",
        "mesh":    "S:\\GNR\\RVP\\TTLs\\TTL_DragonMesh",
        "slice":   "S:\\GNR\\RVP\\TTLs\\TTL_DragonSlice",
        "linux":   "Q:\\DPM_Debug\\GNR\\TTL_Linux",
    },
    "CWF": {
        "boot":    "R:/Templates/CWF/version_1_0/TTL_Boot",
        "mesh":    "R:/Templates/CWF/version_2_0/TTL_DragonMesh",
        "slice":   "R:\\Templates\\CWF\\version_2_0\\TTL_DragonSlice",
        "linux":   "R:\\Templates\\CWF\\version_2_0\\TTL_Linux",
    },
    "DMR": {
        "boot":    "R:/Templates/DMR/version_1_0/TTL_Boot",
        "mesh":    "R:\\Templates\\DMR\\version_2_0\\TTL_DragonMesh",
        "slice":   "R:/Templates/DMR/version_2_0/TTL_DragonSlice",
        "linux":   None,
    },
}

# Canonical blank experiment template — all 76 fields
_BLANK_EXPERIMENT: dict[str, Any] = {
    "Experiment":             "Enabled",
    "Test Name":              "",
    "Test Mode":              "Mesh",
    "Test Type":              "Loops",
    "Visual ID":              "",
    "Bucket":                 "BASELINE",
    "COM Port":               11,
    "IP Address":             "192.168.0.2",
    "Content":                "Dragon",
    "Test Number":            1,
    "Test Time":              30,
    "Reset":                  True,
    "Reset on PASS":          True,
    "FastBoot":               True,
    "Core License":           None,
    "600W Unit":              False,
    "Pseudo Config":          False,
    "Post Process":           None,
    "Configuration (Mask)":   None,
    "Boot Breakpoint":        None,
    "Check Core":             0,
    "Voltage Type":           "vbump",
    "Voltage IA":             None,
    "Voltage CFC":            None,
    "Frequency IA":           None,
    "Frequency CFC":          None,
    "Loops":                  5,
    "Type":                   None,
    "Domain":                 None,
    "Start":                  None,
    "End":                    None,
    "Steps":                  None,
    "ShmooFile":              None,
    "ShmooLabel":             None,
    "ULX Path":               None,
    "ULX CPU":                None,
    "Product Chop":           None,
    "Dragon Pre Command":     None,
    "Dragon Post Command":    None,
    "Startup Dragon":         None,
    "Dragon Content Path":    None,
    "Dragon Content Line":    None,
    "VVAR0":                  None,
    "VVAR1":                  None,
    "VVAR2":                  None,
    "VVAR3":                  None,
    "VVAR_EXTRA":             None,
    "TTL Folder":             None,
    "Scripts File":           None,
    "Pass String":            "Test Complete",
    "Fail String":            "Test Failed",
    "Stop on Fail":           True,
    "Fuse File":              None,
    "Bios File":              None,
    "Merlin Name":            None,
    "Merlin Drive":           None,
    "Merlin Path":            None,
    "Disable 2 Cores":        None,
    "Disable 1 Core":         None,
    "Linux Pre Command":      None,
    "Linux Post Command":     None,
    "Linux Pass String":      None,
    "Linux Fail String":      None,
    "Startup Linux":          None,
    "Linux Path":             None,
    "Linux Content Wait Time": None,
    "Linux Content Line 0":   None,
    "Linux Content Line 1":   None,
    "Linux Content Line 2":   None,
    "Linux Content Line 3":   None,
    "Linux Content Line 4":   None,
    "Linux Content Line 5":   None,
    "Linux Content Line 6":   None,
    "Linux Content Line 7":   None,
    "Linux Content Line 8":   None,
    "Linux Content Line 9":   None,
}

_IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def new_blank(product: str = "GNR", mode: str = "mesh") -> dict[str, Any]:
    """
    Return a fully-populated blank experiment with product-specific defaults applied.

    Args:
        product: GNR | CWF | DMR (case-insensitive).
        mode:    mesh | slice | boot | linux  — determines VVAR2/3 and TTL defaults.
    """
    product = product.upper()
    mode    = mode.lower()

    if product not in PRODUCT_DEFAULTS:
        raise ValueError(f"Unknown product '{product}'.")

    exp = copy.deepcopy(_BLANK_EXPERIMENT)
    pd  = PRODUCT_DEFAULTS[product]

    exp["COM Port"]     = pd["COM Port"]
    exp["IP Address"]   = pd["IP Address"]
    exp["ULX CPU"]      = pd["ULX CPU"]
    exp["Product Chop"] = pd["Product Chop"]
    exp["Merlin Name"]  = "MerlinX.efi"
    exp["Merlin Drive"] = "FS1:"
    exp["Merlin Path"]  = pd["Merlin Path"]
    exp["FastBoot"]     = pd["FastBoot"]

    if mode == "slice":
        exp["VVAR2"]    = pd["VVAR2_slice"]
        exp["VVAR3"]    = pd["VVAR3_slice"]
        exp["Test Mode"] = "Slice"
        exp["Check Core"] = pd["Check Core"]
    elif mode == "boot":
        exp["Check Core"] = None
        exp["FastBoot"]   = False
        exp["Content"]    = "PYSVConsole"
    else:
        exp["Check Core"] = pd["Check Core"]
        exp["VVAR2"] = pd["VVAR2"]
        exp["VVAR3"] = pd["VVAR3"]

    ttl = TTL_DEFAULTS.get(product, {}).get(mode if mode in ("boot", "slice", "linux") else "mesh")
    if ttl:
        exp["TTL Folder"] = ttl

    return exp


def apply_preset(preset: dict, overrides: dict | None = None) -> dict[str, Any]:
    """
    Take a preset dict (from preset_loader.get_preset) and apply overrides.

    Returns a new experiment dict — the original preset is not mutated.

    Args:
        preset:    A preset record (must have 'experiment' key).
        overrides: Dict of {field_name: value} to apply on top of the preset defaults.
    """
    if "experiment" not in preset:
        raise ValueError("Preset dict has no 'experiment' key.")

    exp = copy.deepcopy(preset["experiment"])
    if overrides:
        for field, value in overrides.items():
            if field in exp:
                exp[field] = value
            else:
                # Allow adding new keys (e.g. custom fields)
                exp[field] = value
    return exp


def load_from_file(path: pathlib.Path | str) -> dict[str, Any]:
    """
    Load an existing experiment JSON file from disk.

    The file must contain either:
      - A single experiment dict (object at root), or
      - A list with one experiment dict (first element used).

    Returns:  A copy of the experiment dict ready for editing.
    Raises:   FileNotFoundError if the file does not exist.
              ValueError if the file is not valid JSON or the structure is unexpected.
    """
    p = pathlib.Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Experiment file not found: {p}")

    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{p}': {exc}") from exc

    if isinstance(raw, list):
        if not raw:
            raise ValueError(f"'{p}' contains an empty list — no experiment to load.")
        raw = raw[0]

    if not isinstance(raw, dict):
        raise ValueError(f"'{p}' does not contain an experiment dict (got {type(raw).__name__}).")

    return copy.deepcopy(raw)


def update_fields(
    experiment: dict[str, Any],
    changes:    dict[str, Any],
) -> dict[str, Any]:
    """
    Apply a dict of field changes to an experiment, returning a new copy.

    - Keys that already exist in the experiment are updated.
    - New keys (not in the template) are also accepted and added.
    - The original experiment is NOT mutated.

    Args:
        experiment: The current experiment dict.
        changes:    {field_name: new_value} to apply.

    Returns:  Updated experiment dict (new copy).
    """
    updated = copy.deepcopy(experiment)
    for field, value in changes.items():
        updated[field] = value
    return updated


def validate(
    experiment: dict[str, Any],
    product:    str | None = None,
) -> tuple[bool, list[str], list[str]]:
    """
    Validate an experiment dict against all rules.

    Args:
        experiment: Experiment dict.
        product:    Product context (GNR/CWF/DMR). If not provided, uses
                    experiment['Product Chop'] if available, else 'GNR'.

    Returns:
        (is_valid, errors, warnings)
        errors   — must be fixed before export
        warnings — advisory; export still proceeds
    """
    errors:   list[str] = []
    warnings: list[str] = []

    def e(msg):  errors.append(msg)
    def w(msg):  warnings.append(msg)
    def _merge(errs, warns): errors.extend(errs); warnings.extend(warns)

    exp  = experiment
    name = exp.get("Test Name", "")
    mode = exp.get("Test Mode", "")
    typ  = exp.get("Test Type", "")
    cont = exp.get("Content", "")
    prod = (product or exp.get("Product Chop") or "GNR").upper()

    # ── Required non-empty fields ──────────────────────────────────────────
    if not exp.get("Experiment"):
        e("'Experiment' must not be empty.")
    if not name:
        e("'Test Name' must not be empty.")

    # ── Sweep validation ───────────────────────────────────────────────────
    if typ == "Sweep":
        start      = exp.get("Start")
        end        = exp.get("End")
        steps      = exp.get("Steps")
        domain     = exp.get("Domain")
        sweep_type = exp.get("Type")

        if start is None or start == 0:
            e("Sweep: 'Start' must be set and non-zero.")
        if end is None or end == 0:
            e("Sweep: 'End' must be set and non-zero.")
        if steps is None or steps == 0:
            e("Sweep: 'Steps' must be set and non-zero.")
        if start is not None and end is not None and end <= start:
            e(f"Sweep: 'End' ({end}) must be greater than 'Start' ({start}).")
        if not domain:
            e("Sweep: 'Domain' must be set (CFC or IA).")
        if not sweep_type:
            e("Sweep: 'Type' must be set (Voltage or Frequency).")

    # ── Shmoo validation ───────────────────────────────────────────────────
    if typ == "Shmoo":
        if not exp.get("ShmooFile"):
            e("Shmoo: 'ShmooFile' must not be empty.")

    # ── IP address format ──────────────────────────────────────────────────
    ip = exp.get("IP Address", "")
    if ip and not _IP_RE.match(str(ip)):
        e(f"'IP Address' value '{ip}' does not match expected format x.x.x.x.")

    # ── TTL Folder warning ─────────────────────────────────────────────────
    if not exp.get("TTL Folder"):
        w("'TTL Folder' is empty. Experiment may not run correctly.")

    # ── Constraint checks (from constraints.py) ────────────────────────────
    _merge(*_c.check_slice_restrictions(exp))
    _merge(*_c.check_mesh_mask(exp, prod))
    _merge(*_c.check_vvar_mode_consistency(exp, prod))
    _merge(*_c.check_pseudo_core_configuration(exp, prod))
    _merge(*_c.check_pysvconsole_requirements(exp))
    _merge(*_c.check_dragon_content_requirements(exp))
    _merge(*_c.check_linux_content_requirements(exp))
    _merge(*_c.check_check_core_set(exp))
    _merge(*_c.check_voltage_bumps(exp))

    return len(errors) == 0, errors, warnings


def validate_batch(
    experiments: list[dict[str, Any]],
    product:     str | None = None,
) -> tuple[bool, list[str], list[str]]:
    """
    Validate a list of experiments as a batch.

    Runs per-experiment validation on each member AND applies batch-level
    checks (consistent Check Core, test number ordering).

    Returns:
        (all_valid, all_errors, all_warnings)
    """
    all_errors:   list[str] = []
    all_warnings: list[str] = []

    for i, exp in enumerate(experiments):
        ok, errs, warns = validate(exp, product=product)
        label = exp.get("Test Name", f"exp[{i}]")
        for err  in errs:  all_errors.append(f"[{label}] {err}")
        for warn in warns: all_warnings.append(f"[{label}] {warn}")

    # Batch-level checks
    _, batch_warns = _c.check_batch_check_core(experiments)
    all_warnings.extend(batch_warns)

    ordering_warns = _c.check_test_number_ordering(experiments)
    all_warnings.extend(ordering_warns)

    return len(all_errors) == 0, all_errors, all_warnings


def get_ask_user_fields(preset: dict) -> list[str]:
    """Return the ask_user field list from a preset."""
    return list(preset.get("ask_user", []))


def get_product_defaults(product: str) -> dict:
    """Return a copy of the product-defaults dict for a given product."""
    product = product.upper()
    if product not in PRODUCT_DEFAULTS:
        raise ValueError(f"Unknown product '{product}'.")
    return dict(PRODUCT_DEFAULTS[product])


def get_ttl_defaults(product: str) -> dict:
    """Return a copy of the TTL defaults dict for a given product."""
    product = product.upper()
    return dict(TTL_DEFAULTS.get(product, {}))


def list_all_fields() -> list[str]:
    """Return the full ordered list of experiment field names."""
    return list(_BLANK_EXPERIMENT.keys())
