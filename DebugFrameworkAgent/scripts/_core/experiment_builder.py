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


def _get_bridge():
    """Lazily import and return the PPVBridge singleton, or None if unavailable."""
    try:
        from . import ppv_bridge as _ppv
        return _ppv.get_bridge()
    except Exception:  # pragma: no cover
        return None


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


# --------------------------------------------------------------------------
# .tpl file helpers
# --------------------------------------------------------------------------

def _coerce_tpl_value(s: str) -> Any:
    """
    Convert a raw .tpl string cell back to a Python value.

    Rules (applied in order):
      - ``""``        → ``None``
      - ``"true"``    → ``True``   (case-insensitive)
      - ``"false"``   → ``False``  (case-insensitive)
      - integer text  → ``int``
      - float text    → ``float``
      - anything else → ``str``
    """
    if s == "":
        return None
    lo = s.strip().lower()
    if lo == "true":
        return True
    if lo == "false":
        return False
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _load_tpl(p: pathlib.Path) -> list[dict[str, Any]]:
    """
    Parse a tab-separated .tpl file.

    Format written by ``exporter.write_tpl()``:
      Line 0   — tab-separated field names (header)
      Line 1…  — one tab-separated value row per experiment

    Returns a list of experiment dicts (one per data row).
    Raises ``ValueError`` if the file cannot be parsed.
    """
    text  = p.read_text(encoding="utf-8")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) < 2:
        raise ValueError(
            f"'{p}' does not look like a valid .tpl file "
            f"(expected at least a header row and one data row; got {len(lines)} non-empty line(s))."
        )

    headers = lines[0].split("\t")
    experiments: list[dict[str, Any]] = []
    for row_idx, line in enumerate(lines[1:], start=1):
        cells = line.split("\t")
        # Pad with empty strings if row is shorter than headers
        while len(cells) < len(headers):
            cells.append("")
        exp = {
            header: _coerce_tpl_value(cells[i])
            for i, header in enumerate(headers)
        }
        experiments.append(exp)
    return experiments


# --------------------------------------------------------------------------
# File loading — supports .json and .tpl
# --------------------------------------------------------------------------

_SINGLE_EXP_KEYS: frozenset[str] = frozenset({"Test Name", "Experiment", "Test Type"})


def _json_to_experiment_list(raw: Any, source: pathlib.Path) -> list[dict[str, Any]]:
    """
    Normalise a parsed JSON value into a list of experiment dicts.

    Accepts three structures:
      1. ``[ {...}, {...} ]``  — list of experiment dicts
      2. ``{ "name": {...}, … }`` — outer dict whose *values* are experiment dicts
      3. ``{ "Test Name": … }`` — single experiment dict

    Raises ``ValueError`` for unexpected structures.
    """
    if isinstance(raw, list):
        if not raw:
            raise ValueError(f"'{source}' contains an empty list — no experiments to load.")
        return [copy.deepcopy(e) for e in raw]
    if isinstance(raw, dict):
        if any(k in raw for k in _SINGLE_EXP_KEYS):
            # Single experiment at root level
            return [copy.deepcopy(raw)]
        # Outer dict whose values are experiment dicts
        values = [v for v in raw.values() if isinstance(v, dict)]
        if not values:
            raise ValueError(
                f"'{source}' is a dict but none of its values look like experiment dicts."
            )
        return [copy.deepcopy(v) for v in values]
    raise ValueError(
        f"'{source}' does not contain an experiment or list of experiments "
        f"(got {type(raw).__name__})."
    )


def load_from_file(path: pathlib.Path | str) -> dict[str, Any]:
    """
    Load a **single** experiment from disk.

    Supported file formats:
      - ``.json`` — standard JSON export (single dict, list, or dict-of-dicts)
      - ``.tpl``  — tab-separated PPV template (header row + one data row; if the
                    .tpl contains multiple data rows, the **first** row is returned)

    Returns:  A copy of the experiment dict ready for editing.
    Raises:   ``FileNotFoundError`` if the file does not exist.
              ``ValueError`` if the file cannot be parsed or has no experiments.
    """
    p = pathlib.Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Experiment file not found: {p}")

    if p.suffix.lower() == ".tpl":
        exps = _load_tpl(p)
        return copy.deepcopy(exps[0])

    # JSON path
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{p}': {exc}") from exc

    return _json_to_experiment_list(raw, p)[0]


def load_batch_from_file(path: pathlib.Path | str) -> list[dict[str, Any]]:
    """
    Load **all** experiments from a file, returning a list of experiment dicts.

    Supported file formats:
      - ``.json`` — single dict → ``[dict]``; list → list; dict-of-dicts → list of values
      - ``.tpl``  — header + one or more data rows → one dict per row

    This is the preferred loader for report generation, validation, and batch
    workflows because it works transparently with both file types.

    Returns:  List of experiment dicts (copies safe to mutate).
    Raises:   ``FileNotFoundError`` / ``ValueError`` on missing or invalid files.
    """
    p = pathlib.Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Experiment file not found: {p}")

    if p.suffix.lower() == ".tpl":
        return _load_tpl(p)

    # JSON path
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{p}': {exc}") from exc

    return _json_to_experiment_list(raw, p)


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
        warnings — advisory; export still proceeds.
                   A warning starting with ``"EXPERIMENT_DISABLED:"`` means
                   the ``"Experiment"`` field is set to ``"Disabled"``; all
                   other validation is skipped and the caller should prompt
                   the user about removing the experiment from the output.
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

    # ── Experiment status ──────────────────────────────────────────────────
    _exp_status = str(exp.get("Experiment") or "").strip()
    if not _exp_status:
        e("'Experiment' must not be empty.")
    elif _exp_status.lower() == "disabled":
        # Disabled experiments are intentionally skipped by the Framework.
        # Skip all further validation and surface as a distinct advisory so
        # callers (agent, CLI) can prompt the user about removal.
        return True, [], ["EXPERIMENT_DISABLED: This experiment is marked Disabled and will be skipped at runtime."]

    # ── Required non-empty fields ──────────────────────────────────────────
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

    # ── Optional PPV enum validation (requires PPV on the host) ───────────
    bridge = _get_bridge()
    if bridge is not None and bridge.is_available:
        _ENUM_FIELD_MAP = [
            ("Test Mode",    "TEST_MODES"),
            ("Test Type",    "TEST_TYPES"),
            ("Content",      "CONTENT_OPTIONS"),
            ("Voltage Type", "VOLTAGE_TYPES"),
            ("Type",         "TYPES"),
            ("Domain",       "DOMAINS"),
        ]
        for field_name, enum_key in _ENUM_FIELD_MAP:
            field_val = exp.get(field_name)
            if field_val:  # skip None / empty — other rules handle required fields
                ok, msg = bridge.validate_enum_value(prod, enum_key, str(field_val))
                if not ok:
                    w(msg)

    return len(errors) == 0, errors, warnings


def validate_batch(
    experiments: list[dict[str, Any]],
    product:     str | None = None,
) -> tuple[bool, list[str], list[str], list[str]]:
    """
    Validate a list of experiments as a batch.

    Runs per-experiment validation on each member AND applies batch-level
    checks (consistent Check Core, test number ordering).

    Disabled experiments (``"Experiment" == "Disabled"``) are never treated
    as errors — they are instead collected into ``disabled_names`` so the
    caller / agent can prompt the user about removing them from the output.

    Returns:
        (all_valid, all_errors, all_warnings, disabled_names)
        disabled_names — Test Names of experiments marked Disabled
    """
    all_errors:        list[str] = []
    all_warnings:      list[str] = []
    disabled_names:    list[str] = []
    enabled_exps:      list[dict[str, Any]] = []

    for i, exp in enumerate(experiments):
        ok, errs, warns = validate(exp, product=product)
        label = exp.get("Test Name", f"exp[{i}]")

        # Separate out the disabled-experiment advisory from regular warnings
        disabled_flags = [w for w in warns if w.startswith("EXPERIMENT_DISABLED:")]
        regular_warns  = [w for w in warns if not w.startswith("EXPERIMENT_DISABLED:")]

        if disabled_flags:
            disabled_names.append(label)
        else:
            enabled_exps.append(exp)

        for err  in errs:          all_errors.append(f"[{label}] {err}")
        for warn in regular_warns: all_warnings.append(f"[{label}] {warn}")

    # Batch-level checks run only against enabled experiments so disabled
    # entries do not pollute ordering / Check-Core consistency results.
    _, batch_warns = _c.check_batch_check_core(enabled_exps)
    all_warnings.extend(batch_warns)

    ordering_warns = _c.check_test_number_ordering(enabled_exps)
    all_warnings.extend(ordering_warns)

    return len(all_errors) == 0, all_errors, all_warnings, disabled_names


def filter_disabled(experiments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a copy of the experiment list with disabled experiments removed.

    Disabled experiments have ``"Experiment" == "Disabled"`` (case-insensitive).
    All other experiments (including those marked ``"Enabled"`` or with any
    other truthy status) are kept.
    """
    return [
        exp for exp in experiments
        if str(exp.get("Experiment") or "").strip().lower() != "disabled"
    ]


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
