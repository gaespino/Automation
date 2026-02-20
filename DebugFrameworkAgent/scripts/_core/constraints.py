"""
constraints.py — Field validation rules, product constraints, and agent guidance data.

This module is the single source of truth for ALL hard rules and soft warnings
applied to experiment configurations. It is used by:
  - experiment_builder.validate()
  - CLI scripts (validate_experiment.py)
  - Agents (via skills/experiment_constraints.skill.md)

Rules can be added here at any time without touching the agent files — agents
reference this module through the skill document.
"""

from __future__ import annotations
from typing import Any

# =============================================================================
# Section 1 — Valid options per product / field / mode
# =============================================================================

# Configuration (Mask) — valid options in Mesh mode per product
# Slice accepts any integer in the product-specific range (validated separately).
MESH_MASK_OPTIONS: dict[str, list[str]] = {
    "GNR": ["", "RowPass1", "RowPass2", "RowPass3", "FirstPass", "SecondPass", "ThirdPass"],
    "CWF": ["", "RowPass1", "RowPass2", "RowPass3", "FirstPass", "SecondPass", "ThirdPass"],
    "DMR": ["", "Compute0", "Compute1", "Compute2", "Compute3", "Cbb0", "Cbb1", "Cbb2", "Cbb3"],
}

# Slice core range [min, max] per product
SLICE_CORE_RANGE: dict[str, tuple[int, int]] = {
    "GNR": (0, 179),
    "CWF": (0, 179),
    "DMR": (0, 128),
}

# VVAR2 / VVAR3 — mesh vs slice values per product
VVAR_DEFAULTS: dict[str, dict[str, dict[str, str]]] = {
    "GNR": {
        "mesh":  {"VVAR2": "0x1000000", "VVAR3": "0x4000000"},
        "slice": {"VVAR2": "0x1000002", "VVAR3": "0x4000000"},
    },
    "CWF": {
        "mesh":  {"VVAR2": "0x1000000", "VVAR3": "0x4000000"},
        "slice": {"VVAR2": "0x1000002", "VVAR3": "0x4000000"},
    },
    "DMR": {
        "mesh":  {"VVAR2": "0x1000000", "VVAR3": "0x4200000"},
        "slice": {"VVAR2": "0x1000002", "VVAR3": "0x4210000"},
    },
}

# VVAR2 value that restricts Dragon to 2 threads (slice mode value)
_VVAR2_TWO_THREAD = "0x1000002"

# =============================================================================
# Section 2 — Slice-mode blocked fields
# These fields are ONLY valid in Mesh mode; Slice mode must not use them.
# =============================================================================

# Fields that are NEVER valid in Slice mode, for any product
SLICE_BLOCKED_FIELDS: list[str] = [
    "Pseudo Config",
    "Disable 2 Cores",
    "Disable 1 Core",
]

# =============================================================================
# Section 3 — Pseudo / core-disable configuration
# "Pseudo mesh content" = limiting active cores during a Mesh test.
# Product determines which field controls core restriction.
# =============================================================================

# Which field enables pseudo/core-reduction per product
PSEUDO_CORE_FIELD: dict[str, str] = {
    "GNR": "Pseudo Config",      # bool: True enables pseudo config
    "CWF": "Disable 2 Cores",    # str: one of DISABLE_2_CORE_OPTIONS
    "DMR": "Disable 1 Core",     # str: one of DISABLE_1_CORE_OPTIONS
}

# Valid values for Disable 2 Cores (CWF — 4 cores/module, 2-bit combination register)
# 0x3 = cores 0+1, 0xc = cores 2+3, 0x9 = cores 0+3, 0xa = cores 1+3, 0x5 = cores 0+2
DISABLE_2_CORE_OPTIONS: list[str] = ["", "0x3", "0xc", "0x9", "0xa", "0x5"]

# Valid values for Disable 1 Core (DMR — 2-bit register, select 1 of 4 cores)
DISABLE_1_CORE_OPTIONS: list[str] = ["", "0x1", "0x2"]

# Valid Pseudo Config values for GNR (bool field, True = enabled)
# No enumeration needed — it's a boolean.

# =============================================================================
# Section 4 — Unit Chop definitions
# Unit Chop determines the number of compute/CBB units active on the device.
# Must be asked if not specified; affects Check Core validation and DMR pseudo mesh expansion.
# =============================================================================

UNIT_CHOP_INFO: dict[str, dict[str, dict]] = {
    "GNR": {
        "AP": {
            "description": "All Processor — 3 compute modules (Compute 0, 1, 2)",
            "computes": [0, 1, 2],
            "cbbs": [],
            "check_core_note": "Verify core number is within a valid module for the 3-compute AP configuration.",
        },
        "SP": {
            "description": "Scalable Processor — 2 compute modules (Compute 0, 1)",
            "computes": [0, 1],
            "cbbs": [],
            "check_core_note": "Verify core number is within a valid module for the 2-compute SP configuration.",
        },
    },
    "CWF": {
        "AP": {
            "description": "All Processor — 3 compute modules, 4 cores/module",
            "computes": [0, 1, 2],
            "cbbs": [],
            "check_core_note": "CWF has 4 cores per module. Check Core should correspond to a valid core index.",
        },
        "SP": {
            "description": "Scalable Processor — 2 compute modules, 4 cores/module",
            "computes": [0, 1],
            "cbbs": [],
            "check_core_note": "CWF has 4 cores per module. Check Core should correspond to a valid core index.",
        },
    },
    "DMR": {
        "X1": {
            "description": "1-CBB configuration — CBB0 only",
            "computes": [0, 1, 2, 3],   # computes are same across all DMR chops
            "cbbs": [0],
            "check_core_note": "DMR X1: only CBB0 is active. Check Core must be in CBB0.",
        },
        "X2": {
            "description": "2-CBB configuration — CBB0 + CBB1",
            "computes": [0, 1, 2, 3],
            "cbbs": [0, 1],
            "check_core_note": "DMR X2: CBB0 and CBB1 active. Check Core must fall within these CBBs.",
        },
        "X3": {
            "description": "3-CBB configuration — CBB0 + CBB1 + CBB2",
            "computes": [0, 1, 2, 3],
            "cbbs": [0, 1, 2],
            "check_core_note": "DMR X3: CBB0, CBB1, CBB2 active.",
        },
        "X4": {
            "description": "4-CBB (full) configuration — CBB0 + CBB1 + CBB2 + CBB3",
            "computes": [0, 1, 2, 3],
            "cbbs": [0, 1, 2, 3],
            "check_core_note": "DMR X4: all CBBs active.",
        },
    },
}

# DMR Configuration Mask options that are CBB-based (as opposed to Compute-based)
DMR_CBB_MASKS    = ["Cbb0", "Cbb1", "Cbb2", "Cbb3"]
DMR_COMPUTE_MASKS = ["Compute0", "Compute1", "Compute2", "Compute3"]

# =============================================================================
# Section 5 — Test Number priority ordering
# Assign test numbers at the batch level — lower numbers first per priority tier.
#   Tier 1 (lowest numbers): Loops experiments
#   Tier 2: Sweep experiments
#   Tier 3 (highest numbers): Shmoo experiments
# =============================================================================

TEST_NUMBER_PRIORITY: dict[str, int] = {
    "Loops":    1,
    "Sweep":    2,
    "Shmoo":    3,
    "Stability": 1,   # treated same as Loops
}


def assign_test_numbers(experiments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Sort and assign sequential test numbers respecting priority order:
      Loops first → Sweeps → Shmoos last.

    Returns a new list with 'Test Number' fields updated.
    The input list is not mutated.
    """
    import copy

    def _priority(exp: dict) -> int:
        return TEST_NUMBER_PRIORITY.get(exp.get("Test Type", "Loops"), 1)

    sorted_exps = sorted([copy.deepcopy(e) for e in experiments], key=_priority)
    for i, exp in enumerate(sorted_exps, start=1):
        exp["Test Number"] = i

    return sorted_exps


# =============================================================================
# Section 6 — Default values that agents MUST enforce (no silently-applied defaults)
# =============================================================================

# Fields the agent must ASK about — never silently apply a default.
MUST_ASK_FIELDS: list[str] = [
    # Bucket — relates to the failure type or analysis category the unit belongs to.
    # NOT a test type — do NOT guess from content or mode. Always ask.
    "Bucket",          # Ask: "What failure bucket is this unit in? (e.g. BOOT_FAIL, MARGIN, STRESS)"
    "Loops",           # Ask: "How many loops for each experiment?"
    # Sweep params — only relevant when Test Type = Sweep
    "Start",           # Ask: "Sweep start value?"
    "End",             # Ask: "Sweep end value?"
    "Steps",           # Ask: "Sweep step size?"
    "Domain",          # Ask: "Sweep domain? (IA / CFC)"
    "Type",            # Ask: "Sweep type? (Voltage / Frequency)"
    # Shmoo params — only relevant when Test Type = Shmoo
    "ShmooFile",       # Ask: "Shmoo configuration file path?"
    "ShmooLabel",      # Ask: "Shmoo label/identifier?"
]

# Bucket rule: Bucket describes WHY the unit is being tested (failure category on the
# test floor), NOT what the test does. Examples: BOOT_FAIL, CFC_MARGIN, IA_FREQ_MARGIN,
# STRESS, PPVC_CHAR, CUSTOMER_BUG. The agent must ask if not provided — do not infer.
BUCKET_MUST_ASK = True

# Default Test Time to use when user does NOT specify it (do NOT ask — apply silently)
DEFAULT_TEST_TIME = 30

# =============================================================================
# Section 7 — Content-specific mandatory fields
# =============================================================================

# Fields that are ERRORS (not just warnings) when missing
CONTENT_REQUIRED_FIELDS: dict[str, list[str]] = {
    "PYSVConsole": ["Scripts File"],     # pre-script is MANDATORY for PYSVConsole
    "Dragon":      [],                   # ULX Path, Dragon Content Path are warnings
    "Linux":       [],                   # Linux Path, Startup Linux are warnings
}

# Fields to ask the user when building a Dragon experiment
DRAGON_ASK_FIELDS: list[str] = [
    "ULX Path",
    "Dragon Content Path",
    "Dragon Content Line",
    "Startup Dragon",
    "Dragon Pre Command",
    "Dragon Post Command",
    "VVAR0",
    "VVAR1",
]

# Fields to ask the user when building a Linux experiment
LINUX_ASK_FIELDS: list[str] = [
    "Linux Path",
    "Startup Linux",
    "Linux Pre Command",
    "Linux Post Command",
    "Linux Pass String",
    "Linux Fail String",
    "Linux Content Wait Time",
    "Linux Content Line 0",
]

# Fields to ask the user when building a PYSVConsole experiment
PYSV_ASK_FIELDS: list[str] = [
    "Scripts File",
    "Boot Breakpoint",       # required if diagnosing boot failures
    "Bios File",
    "Fuse File",
]

# =============================================================================
# Section 8 — Constraint check functions
# Each function returns (errors: list[str], warnings: list[str])
# Combine results into the main validate() call.
# =============================================================================

def check_slice_restrictions(exp: dict[str, Any]) -> tuple[list[str], list[str]]:
    """
    Rule: Slice mode must NOT use Pseudo Config, Disable 2 Cores, or Disable 1 Core.
    These options physically require Mesh topology to be meaningful.
    """
    errors: list[str] = []
    warnings: list[str] = []
    mode = exp.get("Test Mode", "")

    if mode.lower() != "slice":
        return errors, warnings

    for field in SLICE_BLOCKED_FIELDS:
        val = exp.get(field)
        if val is None or val == "" or val is False:
            continue  # field is inactive — fine
        errors.append(
            f"'{field}' must not be set in Slice mode. "
            f"Pseudo/core-disable configurations are only valid in Mesh mode."
        )
    return errors, warnings


def check_mesh_mask(exp: dict[str, Any], product: str) -> tuple[list[str], list[str]]:
    """
    Rule: In Mesh mode, Configuration (Mask) must be one of the product-valid options.
    In Slice mode, the value must be an integer within [0, product_max].
    """
    errors: list[str] = []
    warnings: list[str] = []
    mode    = exp.get("Test Mode", "")
    mask    = exp.get("Configuration (Mask)")
    product = product.upper()

    if mask is None or mask == "":
        return errors, warnings   # no mask set — fine

    valid = MESH_MASK_OPTIONS.get(product, [])

    if mode.lower() == "mesh":
        if mask not in valid:
            errors.append(
                f"'Configuration (Mask)' value '{mask}' is not valid for {product} Mesh mode. "
                f"Valid options: {valid}"
            )
    elif mode.lower() == "slice":
        slice_range = SLICE_CORE_RANGE.get(product)
        if slice_range:
            try:
                core_num = int(mask)
                if not (slice_range[0] <= core_num <= slice_range[1]):
                    errors.append(
                        f"'Configuration (Mask)' value '{mask}' is out of Slice range "
                        f"{slice_range[0]}–{slice_range[1]} for {product}."
                    )
            except (ValueError, TypeError):
                errors.append(
                    f"'Configuration (Mask)' in Slice mode must be an integer (core number). "
                    f"Got: '{mask}'."
                )
    return errors, warnings


def check_vvar_mode_consistency(exp: dict[str, Any], product: str) -> tuple[list[str], list[str]]:
    """
    Rule: VVAR2 and VVAR3 must match the expected values for the experiment's mode.

    Key warning cases:
      - Mesh experiment using the Slice VVAR2 value (0x1000002) → 2-thread restriction will apply.
      - Slice experiment using the Mesh VVAR2 value (0x1000000) → 2-thread limit is NOT enforced.
    """
    errors: list[str] = []
    warnings: list[str] = []
    mode    = exp.get("Test Mode", "").lower()
    product = product.upper()
    vvar2   = str(exp.get("VVAR2", "") or "")
    vvar3   = str(exp.get("VVAR3", "") or "")

    expected = VVAR_DEFAULTS.get(product, {}).get(mode, {})
    if not expected:
        return errors, warnings

    exp_v2 = expected.get("VVAR2", "")
    exp_v3 = expected.get("VVAR3", "")

    if vvar2 and vvar2 != exp_v2:
        slice_v2 = VVAR_DEFAULTS.get(product, {}).get("slice", {}).get("VVAR2", "")
        mesh_v2  = VVAR_DEFAULTS.get(product, {}).get("mesh",  {}).get("VVAR2", "")

        if mode == "mesh" and vvar2 == slice_v2:
            warnings.append(
                f"VVAR2 is set to '{vvar2}' (the Slice value) in a Mesh experiment. "
                f"This limits Dragon content to 2 threads — this will likely cause errors "
                f"with Mesh content. Expected Mesh VVAR2: '{exp_v2}'."
            )
        elif mode == "slice" and vvar2 == mesh_v2:
            warnings.append(
                f"VVAR2 is set to '{vvar2}' (the Mesh value) in a Slice experiment. "
                f"The 2-thread restriction for Slice content will NOT be enforced. "
                f"Expected Slice VVAR2: '{exp_v2}'."
            )
        else:
            warnings.append(
                f"VVAR2 value '{vvar2}' is non-standard for {product} {mode.capitalize()} mode. "
                f"Expected: '{exp_v2}'. Verify this is intentional."
            )

    if vvar3 and vvar3 != exp_v3:
        warnings.append(
            f"VVAR3 value '{vvar3}' is non-standard for {product} {mode.capitalize()} mode. "
            f"Expected: '{exp_v3}'. Verify this is intentional."
        )

    return errors, warnings


def check_pseudo_core_configuration(
    exp: dict[str, Any],
    product: str,
) -> tuple[list[str], list[str]]:
    """
    Rule: Pseudo/core-disable fields are only valid in Mesh mode (enforced by check_slice_restrictions).
    This checker validates that the VALUE used is within the allowed set for the product.
    """
    errors: list[str] = []
    warnings: list[str] = []
    product = product.upper()

    if product == "CWF":
        val = exp.get("Disable 2 Cores")
        if val and val not in DISABLE_2_CORE_OPTIONS:
            errors.append(
                f"'Disable 2 Cores' value '{val}' is not a valid CWF option. "
                f"Valid: {DISABLE_2_CORE_OPTIONS[1:]}"   # exclude empty string
            )

    elif product == "DMR":
        val = exp.get("Disable 1 Core")
        if val and val not in DISABLE_1_CORE_OPTIONS:
            errors.append(
                f"'Disable 1 Core' value '{val}' is not a valid DMR option. "
                f"Valid: {DISABLE_1_CORE_OPTIONS[1:]}"
            )
    # GNR: Pseudo Config is a bool — no enumeration check needed.
    return errors, warnings


def check_pysvconsole_requirements(exp: dict[str, Any]) -> tuple[list[str], list[str]]:
    """
    Rule: PYSVConsole content REQUIRES a Scripts File — this is an ERROR, not a warning.
    A Boot Breakpoint experiment should also have Bios File or a configured script.
    """
    errors: list[str] = []
    warnings: list[str] = []
    content = exp.get("Content", "")

    if content == "PYSVConsole":
        if not exp.get("Scripts File"):
            errors.append(
                "PYSVConsole content requires 'Scripts File' — a PythonSV script must be specified. "
                "This is mandatory; the experiment cannot run without it."
            )
        if exp.get("Boot Breakpoint") and not exp.get("Bios File"):
            warnings.append(
                "A 'Boot Breakpoint' is set but 'Bios File' is empty. "
                "Verify the breakpoint is configured in the script instead."
            )
    return errors, warnings


def check_dragon_content_requirements(exp: dict[str, Any]) -> tuple[list[str], list[str]]:
    """
    Rule: Dragon content should have ULX Path and Dragon Content Path populated.
    Missing these are warnings (not errors) since content can be embedded.
    Dragon Content Line is intentionally optional — it is a filter, not a required field.
    """
    errors: list[str] = []
    warnings: list[str] = []
    content = exp.get("Content", "")

    if content != "Dragon":
        return errors, warnings

    if not exp.get("ULX Path"):
        warnings.append("Dragon content: 'ULX Path' is not set.")
    if not exp.get("Dragon Content Path"):
        warnings.append("Dragon content: 'Dragon Content Path' is not set.")
    # Dragon Content Line is an optional content filter — blank means run all content.
    # Do NOT warn when it is absent.

    return errors, warnings


def check_linux_content_requirements(exp: dict[str, Any]) -> tuple[list[str], list[str]]:
    """
    Rule: Linux content should have Linux Path and Startup Linux populated.
    """
    errors: list[str] = []
    warnings: list[str] = []
    content = exp.get("Content", "")

    if content != "Linux":
        return errors, warnings

    if not exp.get("Linux Path"):
        warnings.append("Linux content: 'Linux Path' is not set.")
    if not exp.get("Startup Linux"):
        warnings.append("Linux content: 'Startup Linux' is not set.")
    if not exp.get("Linux Pass String"):
        warnings.append("Linux content: 'Linux Pass String' is not set — test may not detect PASS correctly.")

    return errors, warnings


def check_check_core_set(exp: dict[str, Any]) -> tuple[list[str], list[str]]:
    """
    Rule: 'Check Core' should be explicitly set (non-zero) for all non-boot experiments.
    A zero value is valid but should be confirmed intentional.

    NOTE: in a batch, all experiments should share the same Check Core value.
    This is enforced at the batch level in check_batch_check_core().
    """
    errors: list[str] = []
    warnings: list[str] = []
    content    = exp.get("Content", "")
    check_core = exp.get("Check Core")

    # Boot/PYSVConsole without a Check Core is expected
    if content == "PYSVConsole":
        return errors, warnings

    if check_core is None or check_core == 0:
        warnings.append(
            "'Check Core' is 0 or not set. "
            "Confirm the correct core to monitor — this should be explicitly specified, "
            "especially in multi-experiment batches."
        )
    return errors, warnings


def check_batch_check_core(experiments: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """
    Rule: All experiments in a batch should share the same Check Core value.
    Returns batch-level errors/warnings.
    """
    errors: list[str] = []
    warnings: list[str] = []

    cores = {exp.get("Test Name", f"exp{i}"): exp.get("Check Core")
             for i, exp in enumerate(experiments)
             if exp.get("Content") != "PYSVConsole"}

    unique_vals = set(cores.values())
    if len(unique_vals) > 1:
        warnings.append(
            f"Inconsistent 'Check Core' values across batch: "
            + ", ".join(f"'{n}' = {v}" for n, v in cores.items())
            + ". All experiments in a batch should typically use the same Check Core."
        )
    return errors, warnings


# Voltage bump maximum recommended value — warn if exceeded
VOLTAGE_BUMP_MAX: float = 0.3


def check_voltage_bumps(exp: dict[str, Any]) -> tuple[list[str], list[str]]:
    """
    Validate Voltage IA and Voltage CFC bump values.

    Rules:
      - None / missing: no action (field not used)
      - 0: valid — means no voltage bump.  Surface an informational note so the
        user is aware they set an explicit zero (not just omitted it).
      - > 0.3 V: warning — unusually large bump; confirm intentional.
      - < 0: error — negative voltage bump is not a valid operating point.
    """
    errors: list[str] = []
    warnings: list[str] = []

    for field in ("Voltage IA", "Voltage CFC"):
        raw = exp.get(field)
        if raw is None or raw == "":
            continue
        try:
            val = float(raw)
        except (TypeError, ValueError):
            errors.append(f"'{field}' value '{raw}' is not a valid number.")
            continue

        if val < 0:
            errors.append(
                f"'{field}' is {val} V — negative voltage bumps are not valid."
            )
        elif val == 0:
            warnings.append(
                f"'{field}' is set to 0 V (no bump). "
                "Confirm this is intentional — 0 means the nominal voltage will be used."
            )
        elif val > VOLTAGE_BUMP_MAX:
            warnings.append(
                f"'{field}' is {val} V, which exceeds the recommended maximum "
                f"of {VOLTAGE_BUMP_MAX} V. Verify this is correct before running."
            )

    return errors, warnings


def check_test_number_ordering(experiments: list[dict[str, Any]]) -> list[str]:
    """
    Validate that test numbers follow the priority order: Loops < Sweeps < Shmoos.
    Returns a list of warnings (not errors — numbering is advisory).
    """
    warnings: list[str] = []

    prev_priority = 0
    for exp in experiments:
        ttype    = exp.get("Test Type", "Loops")
        tnum     = exp.get("Test Number", 0)
        priority = TEST_NUMBER_PRIORITY.get(ttype, 1)

        if priority < prev_priority:
            warnings.append(
                f"Test Number ordering: '{exp.get('Test Name')}' (type={ttype}, num={tnum}) "
                f"appears after a higher-priority type. "
                f"Expected order: Loops → Sweeps → Shmoos."
            )
        prev_priority = priority

    return warnings


# =============================================================================
# Section 9 — DMR Pseudo Mesh experiment matrix expansion
# Builds all combinations for a full pseudo-mesh run covering all CBBs + computes.
# =============================================================================

def expand_dmr_pseudo_mesh(
    unit_chop: str,
    base_experiment: dict[str, Any],
    disable_1_core_val: str = "0x1",
) -> list[dict[str, Any]]:
    """
    For DMR pseudo-mesh testing, expand a base experiment into a full matrix covering:
      - Each active CBB  (determined by unit_chop: X1=CBB0, X2=CBB0-1, X3=CBB0-2, X4=all)
      - Each valid Compute mask (Compute0–Compute3)
      - Each valid Disable 1 Core option (per DISABLE_1_CORE_OPTIONS)

    Returns a list of experiment dicts (one per combination).
    Each experiment has:
      - 'Configuration (Mask)' set to the CBB or Compute mask
      - 'Disable 1 Core' set to the core disable value
      - 'Test Name' reflects the combination
    """
    import copy

    chop_info = UNIT_CHOP_INFO.get("DMR", {}).get(unit_chop.upper())
    if not chop_info:
        raise ValueError(
            f"Unknown DMR unit chop '{unit_chop}'. Valid: {list(UNIT_CHOP_INFO['DMR'].keys())}"
        )

    active_cbbs     = chop_info["cbbs"]
    active_computes = chop_info["computes"]

    # Build CBB masks limited to active CBBs
    cbb_masks     = [f"Cbb{c}" for c in active_cbbs]
    compute_masks = [f"Compute{c}" for c in active_computes]

    # Disable 1 Core options (excluding empty)
    core_disable_options = [v for v in DISABLE_1_CORE_OPTIONS if v]

    results: list[dict] = []
    for mask in cbb_masks + compute_masks:
        for core_val in core_disable_options:
            exp = copy.deepcopy(base_experiment)
            exp["Configuration (Mask)"] = mask
            exp["Disable 1 Core"]       = core_val
            base_name = base_experiment.get("Test Name", "DMR_Pseudo")
            exp["Test Name"] = f"{base_name}_{mask}_CoreDis{core_val}"
            results.append(exp)

    return results


# =============================================================================
# Section 10 — Agent guidance helpers (used in agent prompts + skill docs)
# =============================================================================

def get_unit_chop_options(product: str) -> list[str]:
    """Return valid unit chop keys for a product (e.g. ['AP', 'SP'] for GNR)."""
    return list(UNIT_CHOP_INFO.get(product.upper(), {}).keys())


def describe_unit_chop(product: str, chop: str) -> str:
    """Return a human-readable description of a unit chop."""
    info = UNIT_CHOP_INFO.get(product.upper(), {}).get(chop.upper(), {})
    return info.get("description", f"Unknown chop '{chop}' for {product}")


def get_pseudo_core_field_and_options(product: str) -> tuple[str, list[str]]:
    """
    Return the (field_name, valid_options) tuple for pseudo/core-disable
    configuration for the given product.

    Returns:
        (field_name, options)  where options is a list of valid string values.
        For GNR, field_name='Pseudo Config' and options=['True'] (it's a bool toggle).
    """
    product = product.upper()
    field   = PSEUDO_CORE_FIELD.get(product, "")
    if product == "GNR":
        return field, ["True"]  # bool — enable only
    elif product == "CWF":
        return field, DISABLE_2_CORE_OPTIONS[1:]   # exclude empty
    elif product == "DMR":
        return field, DISABLE_1_CORE_OPTIONS[1:]   # exclude empty
    return field, []


def get_dragon_vvar_note(mode: str) -> str:
    """Return a plain-language explanation of VVAR2 significance for the given mode."""
    if mode.lower() == "mesh":
        return (
            "Mesh VVAR2 (0x1000000): Dragon content runs with all available threads. "
            "Do NOT use the Slice value (0x1000002) in a Mesh experiment — it will "
            "limit Dragon to 2 threads, causing Mesh content to fail."
        )
    elif mode.lower() == "slice":
        return (
            "Slice VVAR2 (0x1000002): Dragon content is limited to 2 threads, which is "
            "required for Slice topology. Do NOT use the Mesh value (0x1000000) in a "
            "Slice experiment — the 2-thread restriction will not be enforced."
        )
    return "Verify VVAR2 matches the intended mode (Mesh or Slice)."
