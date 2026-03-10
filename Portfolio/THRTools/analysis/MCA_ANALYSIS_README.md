# MCA Analysis — Developer & Onboarding Guide

This document is the authoritative reference for the `MCAAnalyzer` Python module and its
per-product configuration files.  Use it when:

- Enabling MCA Analysis for a new product (e.g. **DMR**)
- Adding a new IP type (e.g. a new MCA register bank)
- Adding or adjusting root-cause priority rules
- Debugging "NotFound" or wrong-hint results

---

## Table of Contents

1. [Architecture overview](#1-architecture-overview)
2. [Folder and file structure](#2-folder-and-file-structure)
3. [Per-product config files](#3-per-product-config-files)
   - 3.1 `ip_translation.json`
   - 3.2 `layout.json`
   - 3.3 `scoring_config.json`
   - 3.4 `priority_rules.json`
4. [Analysis pipeline](#4-analysis-pipeline)
5. [How Root Cause and Debug Hints are chosen](#5-how-root-cause-and-debug-hints-are-chosen)
6. [Priority rules system](#6-priority-rules-system)
   - 6.1 Rule structure
   - 6.2 Condition operators
   - 6.3 Available context fields
   - 6.4 Examples
   - 6.5 Catch-all rule
7. [Adding a new product (e.g. DMR)](#7-adding-a-new-product-eg-dmr)
8. [Adding a new IP type](#8-adding-a-new-ip-type)
9. [Translation miss alarms](#9-translation-miss-alarms)
10. [GUI switch](#10-gui-switch)
11. [Debug mode](#11-debug-mode)
12. [Output columns reference](#12-output-columns-reference)

---

## 1. Architecture overview

```
MCAparser.py
  └─ gen_mca_analysis()
       └─ MCAAnalyzer(product='GNR')
            ├─ analyze(cha_df, llc_df, core_df, firsterr_df, ppv_df)
            │    ├─ _build_rev_cha_count()    → CHA Hint / CHA Fail Area
            │    ├─ _build_rev_llc_count()    → LLC Hint / LLC Fail Area
            │    ├─ _build_rev_core_count()   → Core Hint / Core Fail Area / Other / SrcIDs
            │    └─ _build_analysis()         → final MCA_Analysis DataFrame
            └─ result['analysis'] written to Excel tab "MCA_Analysis"
```

The analyzer replicates the original Excel **Analysis** tab logic:

1. Count ML2/MCA register hits per logical instance (same as Excel Rev\*Count arrays).
2. If one instance dominates → that becomes the Hint.
3. On a tie → use the UBOX **FirstError** count to pick the dominant instance.
4. Non-CORE/CHA/LLC first errors (PUNIT, UPI, …) become **Other Errors** and gate out
   spurious Core MCAs.

---

## 2. Folder and file structure

```
PPV/
├── parsers/
│   └── MCAAnalyzer.py          ← main analysis engine
├── gui/
│   └── PPVDataChecks.py        ← GUI entry point (MCA Analysis checkbox)
└── analysis/
    ├── MCA_ANALYSIS_README.md  ← this file
    ├── GNR/
    │   ├── ip_translation.json
    │   ├── layout.json
    │   ├── scoring_config.json
    │   └── priority_rules.json
    ├── CWF/                    ← same structure as GNR (shares die layout)
    │   ├── ip_translation.json
    │   ├── layout.json
    │   ├── scoring_config.json
    │   └── priority_rules.json
    └── DMR/                    ← placeholder — fill in when DMR data is available
        ├── ip_translation.json
        ├── layout.json
        ├── scoring_config.json
        └── priority_rules.json
```

---

## 3. Per-product config files

### 3.1 `ip_translation.json`

Consolidated IP translation table with three sections.

```json
{
  "firsterror_ip": {
    "<ip_key>": "<translate_string>"
  },
  "firsterror_device": {
    "<device_key>": { "translate": "<string>", "offset": <int> }
  },
  "failing_ips": {
    "<translate_string>": "<register_type>"
  }
}
```

#### `firsterror_ip`
Maps the **IP key** (from the `FirstError – IP` column in the raw data / FirstErr tab) to a
human-readable category string.

| Raw key example       | Translates to |
|-----------------------|---------------|
| `core_coregp`         | `CORE`        |
| `scf_cha`             | `CHA`         |
| `punit_ptpcioregs_0`  | `PUNIT`       |
| `ubox_ncevents`       | `UBOX`        |

#### `firsterror_device`
Maps the **device key** (from the `FirstError – Device` column) to a translated label and a
**logical offset**.  The offset corrects for per-compute-tile numbering gaps:

```
logical_id = physical_id - (physical_id // block_size) * offset
```

where `block_size = (instances_per_compute) + offset`.

Example for GNR CPUCore (offset = 4, 60 cores per compute tile):
```
block_size = 60 + 4 = 64
physical 148  →  148 // 64 = 2  →  148 - 2×4 = 140  →  CORE140
```

| Device key   | Translate  | Offset | Notes                                |
|--------------|------------|--------|--------------------------------------|
| `cpucore`    | `CORE`     | 4      | per-compute-tile gap in GNR/CWF      |
| `cpuscf`     | `SCF`      | 4      | same gap for SCF (CHA array)         |
| `eprpunit`   | `EPRPUNIT` | 0      | no gap — raw id is already logical   |
| `ddrmc`      | `DDRMC`    | 0      | no gap                               |

If a device key is **not found**, the raw value is used as-is (offset = 0) and a
[translation-miss warning](#9-translation-miss-alarms) is emitted.

#### `failing_ips`
Maps the translated IP category to which register type it appears in.

| Translated IP | Register type      | Meaning                      |
|---------------|--------------------|------------------------------|
| `B2CMI`       | `MCERRLOGGINGREG`  | Machine Check Error register |
| `PUNIT`       | `IERRLOGGINGREG`   | Internal Error register      |
| `UBOX`        | `IERRLOGGINGREG`   | Internal Error register      |

This table has two purposes:

1. **IERR gate** — when the dominant first error is an `IERRLOGGINGREG` entry
   (e.g. PUNIT), Core MCAs are treated as cascade effects and `Core Hint` is
   forced to `NotFound`.
2. **Other Errors scanning** — `_build_other_errors` scans **both** MCERR and
   IERR rows.  IPs that appear only in MCERR rows (B2CMI, MSE, CMS, SBO) are
   captured because the IERR-only filter was removed.  CORE/CHA/LLC entries
   that appear in MCERR are still excluded by the `is_core`/`is_cha`/`is_llc`
   guard, so there is no double-counting.

---

### 3.2 `layout.json`

Maps each **logical instance id** (0-based integer string key) to its physical location on
the die.

```json
{
  "0": { "compute": "COMPUTE0", "row": "1", "col": "0" },
  "1": { "compute": "COMPUTE0", "row": "2", "col": "0" },
  ...
  "64": { "compute": "COMPUTE1", "row": "1", "col": "0" }
}
```

The `compute` field is used to generate the **Failing Area** column:
`Compute{N} : Row{R} : Col{C}`.

For DMR, populate this file with the logical-id → die-location mapping from your silicon
floorplan once it is available.

---

### 3.3 `scoring_config.json`

Controls how the **Failing Area** is selected when multiple candidate locations are found.
Each candidate scores `score_compute` for a Compute-tile match, `score_row` for a Row match,
and `score_col` for a Column match.  The candidate with the highest total score wins.

```json
{
  "score_compute": 1,
  "score_row":     2,
  "score_col":     4
}
```

These values mirror the original Excel Rev\*Count sheet `Score` cells.  Adjust per product
without any code changes.

---

### 3.4 `priority_rules.json`

Defines the **Root Cause** and **Debug Hints** selection priority.  See
[Section 6](#6-priority-rules-system) for full documentation.

---

## 4. Analysis pipeline

The `analyzer.analyze()` method runs four stages:

### Stage 1 — `_build_rev_cha_count` / `_build_rev_llc_count` / `_build_rev_core_count`

For each VisualID:

1. Filter the decoded DataFrame to ML2 rows for that VID.
2. Count occurrences per logical instance (extracted from the `Instance` column).
3. If one instance has a clearly higher count → that instance is the **Hint**.
4. If multiple instances are tied:
   - Parse the UBOX `MCERRLOGGINGREG FirstError – Location` column.
   - Convert physical portid → logical id using `ip_translation.json` device offsets.
   - Count how many times each logical id appears as the first error.
   - The instance with the highest FirstError count breaks the tie.
5. **IERR gate** (Core only): if the UBOX `IERRLOGGINGREG` first error is a non-CORE type
   (e.g. PUNIT), the CORE MCAs are cascade effects:
   - `Core Hint = NotFound`
   - `Other = <PUNIT/UPI/…>:<device_label><id>`

### Stage 2 — `_build_analysis`

Joins all per-VID results into the final Analysis DataFrame, resolves **Root Cause** and
**Debug Hints** using the [priority rules](#6-priority-rules-system), and adds PPV metadata
(Lot, WW).

---

## 5. How Root Cause and Debug Hints are chosen

For every VID row the analyzer builds a **priority order** — an ordered list of IP categories
(`other`, `cha`, `llc`, `core`) — and then picks the first category that has a non-empty value.

**Root Cause** picks the first present entry from the priority order:
- `other` → raw Other string (e.g. `PUNIT:EPRPUNIT1`)
- `cha`   → CHA Hint (e.g. `CHA134`)
- `llc`   → LLC Hint
- `core`  → Core Hint

**Debug Hints** picks the first non-empty next-step string:
- `other` → `Defeature: <Other>  -- Check CORE or CHA MCAs for more data.`
- `cha`   → `Disable CHA: <hint> - Signature: <OrigReq> - <ISMQ> : <LocPort>`
- `llc`   → `Disable LLC: <hint>`
- `core`  → `Disable CORE: <hint> - MCAs: <core_mcas>`

The **default** priority order is `other → cha → llc → core` and is configurable via
`default_root_cause_order` / `default_debug_hints_order` in `priority_rules.json`.

Rules can **override** the order for specific conditions (see next section).

---

## 6. Priority rules system

Rules are defined in `analysis/{product}/priority_rules.json` and evaluated at runtime for
every row in `_build_analysis`.  **Rules are tested in declaration order; the first matching
rule wins.**  If no rule matches, the default order is used.

### 6.1 Rule structure

```json
{
  "name": "human-readable name",
  "description": "optional explanation",
  "condition": {
    "<condition_key>": <value>,
    ...
  },
  "override_root_cause_order" : ["other", "llc", "core", "cha"],
  "override_debug_hints_order": ["other", "llc", "core", "cha"]
}
```

- All conditions in a single rule are ANDed (every condition must be true for the rule to
  match).
- `override_root_cause_order` and `override_debug_hints_order` can each be omitted
  independently; the default order is used for whichever key is absent.

### 6.2 Condition operators

Three operator suffixes work on **string context fields**:

| Operator suffix | Matches when…                              | Example                                    |
|-----------------|--------------------------------------------|--------------------------------------------|
| `_equals`       | value exactly equals the given string      | `"top_origreq_equals": "PortIn"`           |
| `_in`           | value is a member of the given list        | `"top_origreq_in": ["PortIn", "PortOut"]`  |
| `_contains`     | given string is a substring of the value   | `"core_mcas_contains": "bank"`             |

**Boolean presence flags** use direct equality (no suffix):

| Condition key      | True when…                          |
|--------------------|-------------------------------------|
| `cha_hint_present` | CHA Hint is not `NotFound`          |
| `llc_hint_present` | LLC Hint is not `NotFound`          |
| `core_hint_present`| Core Hint is not `NotFound`         |
| `srcid_present`    | SrcIDs is not `NotFound`            |
| `other_present`    | Other field is non-empty            |

### 6.3 Available context fields

All fields below are available to every rule condition — no code changes required to use any
of them.

| Field name     | Type    | Source column       | Example values           |
|----------------|---------|---------------------|--------------------------|
| `top_origreq`  | string  | `Top OrigReq`       | `PortIn`, `Read`, `WrPush`|
| `top_opcode`   | string  | `Top OpCode`        | `RdCur`, `WrPush`        |
| `top_ismq`     | string  | `Top ISMQ`          |                          |
| `top_sad`      | string  | `Top SAD`           |                          |
| `top_locport`  | string  | `Top SAD LocPort`   |                          |
| `core_mcas`    | string  | `Core Mcas`         | `WDTimeout (3 strike)`   |

### 6.4 Examples

**Match multiple OrigReq values:**
```json
{
  "name": "PortIn or PortOut nuisance",
  "condition": {
    "top_origreq_in": ["PortIn", "PortOut"],
    "cha_hint_present": true
  },
  "override_root_cause_order" : ["other", "llc", "core", "cha"],
  "override_debug_hints_order": ["other", "llc", "core", "cha"]
}
```

**Prioritize Core when a specific error type appears:**
```json
{
  "name": "Core bank error — elevate Core",
  "condition": {
    "core_mcas_contains": "bank",
    "core_hint_present": true
  },
  "override_root_cause_order" : ["core", "other", "cha", "llc"],
  "override_debug_hints_order": ["core", "other", "cha", "llc"]
}
```

**Prioritize based on OpCode:**
```json
{
  "name": "RdCur with LLC failure",
  "condition": {
    "top_opcode_equals": "RdCur",
    "llc_hint_present": true,
    "core_hint_present": false
  },
  "override_root_cause_order" : ["other", "llc", "cha", "core"],
  "override_debug_hints_order": ["other", "llc", "cha", "core"]
}
```

**Match a substring in any OrigReq value:**
```json
{
  "name": "Any Port transaction",
  "condition": {
    "top_origreq_contains": "Port"
  },
  "override_root_cause_order" : ["other", "llc", "core", "cha"],
  "override_debug_hints_order": ["other", "llc", "core", "cha"]
}
```

### 6.5 Catch-all rule

A rule with an empty (or absent) `condition` key matches every row.  Place it **last** to act
as a product-wide default override that takes effect only when no earlier rule matched:

```json
{
  "name": "Fallback — elevate Other for this product",
  "condition": {},
  "override_root_cause_order" : ["other", "cha", "llc", "core"],
  "override_debug_hints_order": ["other", "cha", "llc", "core"]
}
```

---

## 7. Adding a new product (e.g. DMR)

The DMR placeholder folder (`analysis/DMR/`) already contains empty config files.
Follow these steps to fully enable DMR:

### Step 1 — `ip_translation.json`

Populate all three sections from the DMR `Map` tab in the original Excel workbook:

1. **`firsterror_ip`** — copy the `FirstError IP → Translate` table rows.
2. **`firsterror_device`** — copy the `FirstError Device → Translate` table rows, noting the
   correct `offset` for each device type (check the per-compute-tile gap in the floorplan).
3. **`failing_ips`** — list every IP translate string and whether it appears in
   `MCERRLOGGINGREG` or `IERRLOGGINGREG`.

### Step 2 — `layout.json`

Map every logical instance id to its die location.  The key is the zero-based integer as a
string; the value contains `compute`, `row`, and `col`.

```json
{
  "0":  { "compute": "COMPUTE0", "row": "1", "col": "0" },
  "1":  { "compute": "COMPUTE0", "row": "2", "col": "0" },
  ...
}
```

Derive this table from the DMR silicon floorplan / die map.

### Step 3 — `scoring_config.json`

Update the score weights if the DMR Excel Rev\*Count sheet uses different values:

```json
{
  "score_compute": 1,
  "score_row":     2,
  "score_col":     4
}
```

### Step 4 — `priority_rules.json`

Add product-specific rules.  Start with the same default order as GNR/CWF and add rules as
new failure patterns are identified.  The `_condition_operators_reference` block inside the
file documents all available operators for quick reference.

### Step 5 — `MCAAnalyzer` code constants

If DMR uses IP categories that do not yet appear in the module-level sets, add them:

```python
# parsers/MCAAnalyzer.py — top of file
_CORE_TRANSLATE = {'CORE'}
_CHA_TRANSLATE  = {'CHA', 'SCF'}
_LLC_TRANSLATE  = {'LLC', 'SCF_LLC'}
```

Add new translate strings to the appropriate set if your `firsterror_ip` entries map to a
label that is not already there.

### Step 6 — Test

```python
from PPV.parsers.MCAAnalyzer import MCAAnalyzer

a = MCAAnalyzer('DMR')
print(a.score_compute, a.score_row, a.score_col)
print(a.firsterror_ip_map)
```

Run the analyzer against a real DMR decoded file and compare with the reference Excel output.
Use `debug=True` for a per-VID trace:

```python
result = a.analyze(cha_df=..., core_df=..., firsterr_df=..., debug=True)
```

---

## 8. Adding a new IP type

When a new IP register array (e.g. UPI, PCIe) becomes available in the decoded data:

1. **`ip_translation.json → firsterror_ip`** — add the new IP key and its translated label:
   ```json
   "upi_port": "UPI"
   ```

2. **`ip_translation.json → firsterror_device`** — add the device key with its offset:
   ```json
   "upipxp": { "translate": "UPI", "offset": 0 }
   ```

3. **`ip_translation.json → failing_ips`** — add the translated label and its register type.
   Use `"MCERRLOGGINGREG"` for memory-bus IPs (B2CMI, MSE, CMS, SBO) and
   `"IERRLOGGINGREG"` for internal-error IPs (PUNIT, UBOX, UPI):
   ```json
   "UPI": "IERRLOGGINGREG"
   ```

4. **`MCAAnalyzer.py`** — no code change is needed.  `_build_other_errors` now
   scans both IERR and MCERR rows, so any non-CORE/CHA/LLC IP will be captured
   regardless of which register it appears in.  If the new IP should also trigger
   the `Core Hint = NotFound` gate, it must map to `IERRLOGGINGREG` in
   `failing_ips`.

5. **`priority_rules.json`** — add a rule if the new IP needs custom priority:
   ```json
   {
     "name": "UPI error — elevate Other",
     "condition": {
       "other_present": true,
       "top_origreq_contains": "UPI"
     },
     "override_root_cause_order" : ["other", "cha", "llc", "core"],
     "override_debug_hints_order": ["other", "cha", "llc", "core"]
   }
   ```

6. If the new IP should appear in the **CHA**, **LLC**, or **Core** hint columns (not just
   Other), add its translate string to the appropriate constant in `MCAAnalyzer.py`:

   ```python
   _CHA_TRANSLATE  = {'CHA', 'SCF', 'NEW_CHA_VARIANT'}
   ```

---

## 9. Translation miss alarms

When `_parse_firsterr_location` encounters an ip_key or device_key that is **not** in
`ip_translation.json`, it:

1. Uses the raw value as-is (no crash).
2. Prints a one-shot warning to stdout:
   ```
   WARNING [MCAAnalyzer] Unknown FirstError IP key 'new_ip' – using raw value. Add to ip_translation.json.
   WARNING [MCAAnalyzer] Unknown FirstError Device key 'new_device' – using raw value, offset=0. Add to ip_translation.json.
   ```
3. Adds the key to `analyzer._translation_misses` (a `set`) for programmatic inspection:
   ```python
   if analyzer._translation_misses:
       print("Missing translation entries:", analyzer._translation_misses)
   ```

Add the missing entries to `ip_translation.json` and re-run to clear the warnings.

---

## 10. GUI switch

The **MCA Analysis** checkbox in `PPVDataChecks.py` controls whether `gen_mca_analysis()` is
called.  It is **checked by default**.

The checkbox passes `mca_analysis=True` to `MCAparser.mcap()`, which gates
`gen_mca_analysis()` on `self.mca_analysis`.

To disable analysis for a run, uncheck the box before generating the report.

---

## 11. Debug mode

Pass `debug=True` to `analyzer.analyze()` to enable a verbose per-VID trace:

```python
result = analyzer.analyze(
    cha_df=..., llc_df=..., core_df=..., firsterr_df=...,
    debug=True
)
```

The trace prints:
- Input DataFrame row counts
- Per-VID ML2 instance counts
- Whether tie-breaking was triggered and the FirstError counts
- IERR gate decisions (e.g. "PUNIT gate → Core Hint forced to NotFound")
- Final summary table for all VIDs

---

## 12. Output columns reference

The `MCA_Analysis` Excel tab contains the following columns:

| Column            | Description                                                              |
|-------------------|--------------------------------------------------------------------------|
| `VisualIDs`       | Unit Visual ID                                                           |
| `Lot`             | Unique lot values from PPV tab (comma-separated if multiple)             |
| `WW`              | Decimal WW from PPV tab                                                  |
| `# Runs`          | Number of MCA runs for this VID                                          |
| `Core Hint`       | Most-failing logical Core instance (e.g. `CORE140`) or `NotFound`       |
| `Core Fail Area`  | Die location of the Core hint (`Compute{N} : Row{R} : Col{C}`)          |
| `CHA Hint`        | Most-failing logical CHA instance or `NotFound`                          |
| `CHA Fail Area`   | Die location of the CHA hint                                             |
| `LLC Hint`        | Most-failing logical LLC instance or `NotFound`                          |
| `LLC Fail Area`   | Die location of the LLC hint                                             |
| `SrcIDs`          | CHA SrcID value(s) or `NotFound`                                         |
| `Other`           | Non-CORE/CHA/LLC first-error IP (e.g. `PUNIT:EPRPUNIT1`)                |
| `Top OrigReq`     | Most-common OrigReq transaction type                                     |
| `Top OpCode`      | Most-common OpCode                                                       |
| `Top ISMQ`        | Most-common ISMQ value                                                   |
| `Top SAD`         | Most-common SAD                                                          |
| `Top SAD LocPort` | Most-common SAD LocPort                                                  |
| `Core MCAs`       | Most-common Core MCA error description (from `MCACOD (ErrDecode)`)      |
| `Root Cause`      | Primary failing IP instance — selected by priority rule order            |
| `Debug Hints`     | First-action next step — selected by priority rule order                 |
| `Failing Area`    | Die location corresponding to the Root Cause                             |
