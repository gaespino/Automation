# Skill: Experiment Field Constraints & Rules

> **Reference**: `scripts/_core/constraints.py` — all rules are programmatically enforced here.
> Agents should use this document to understand *why* rules exist and *how* to handle them in conversation.

---

## Rule 1 — Slice Mode Restrictions

**Fields that MUST NOT be used in Slice mode:**

| Field | Why |
|---|---|
| `Pseudo Config` | Physically only valid in Mesh topology |
| `Disable 2 Cores` | Only valid in Mesh topology |
| `Disable 1 Core` | Only valid in Mesh topology |

- If a user requests any of these for a Slice experiment → **reject with an error**, explain the restriction, and ask if they meant Mesh.
- The validator (`check_slice_restrictions`) raises an error if these fields are set and `Test Mode == Slice`.

---

## Rule 2 — Configuration (Mask) Valid Options

### Mesh Mode

| Product | Valid Mask Values |
|---------|-----------------|
| GNR | `""`, `RowPass1`, `RowPass2`, `RowPass3`, `FirstPass`, `SecondPass`, `ThirdPass` |
| CWF | `""`, `RowPass1`, `RowPass2`, `RowPass3`, `FirstPass`, `SecondPass`, `ThirdPass` |
| DMR | `""`, `Compute0`, `Compute1`, `Compute2`, `Compute3`, `Cbb0`, `Cbb1`, `Cbb2`, `Cbb3` |

> New options can be added to `MESH_MASK_OPTIONS` in `constraints.py` without changing any other code.

### Slice Mode

| Product | Core Number Range |
|---------|------------------|
| GNR | 0 – 179 |
| CWF | 0 – 179 |
| DMR | 0 – 128 |

The value must be an **integer** (the specific core to slice on). Non-integer slice values are an error.

---

## Rule 3 — Dragon VVAR2/VVAR3 Mode Consistency

VVAR2 controls thread count in Dragon content. **Wrong VVAR2 = content failures.**

| Mode | VVAR2 | VVAR3 (GNR/CWF) | VVAR3 (DMR) | Effect |
|------|-------|-----------------|-------------|--------|
| Mesh | `0x1000000` | `0x4000000` | `0x4200000` | All threads active |
| Slice | `0x1000002` | `0x4000000` | `0x4210000` | **2 threads only** |

**Warning scenarios the agent must surface:**

1. **Mesh experiment with Slice VVAR2** (`0x1000002`):
   > "VVAR2 is set to the Slice value in a Mesh experiment — Dragon content will be limited to 2 threads.
   > This WILL cause Mesh content to fail. Intended?"

2. **Slice experiment with Mesh VVAR2** (`0x1000000`):
   > "VVAR2 is set to the Mesh value in a Slice experiment — the 2-thread restriction is NOT enforced.
   > Slice content may fail. Intended?"

3. **Any other non-standard VVAR2/VVAR3**:
   > Advisory warning — may be intentional (user-defined configs).

---

## Rule 4 — Pseudo / Core-Disable Configuration (Pseudo Mesh Content)

When a user asks for *"pseudo mesh content"*, *"core hi/lo"*, *"pseudo SBFT"*, or similar:

| Product | Field to use | Valid Values | Note |
|---------|-------------|--------------|------|
| GNR | `Pseudo Config` | `True` | Boolean toggle |
| CWF | `Disable 2 Cores` | `0x3`, `0xc`, `0x9`, `0xa`, `0x5` | 2-bit combo register, 4 cores/module |
| DMR | `Disable 1 Core` | `0x1`, `0x2` | 2-bit register |

**CWF Core Disable bitmap** (4 cores per module, 2-bit combination register):

| Value | Cores disabled |
|-------|---------------|
| `0x3` | Core 0 + Core 1 |
| `0xc` | Core 2 + Core 3 |
| `0x9` | Core 0 + Core 3 |
| `0xa` | Core 1 + Core 3 |
| `0x5` | Core 0 + Core 2 |

**DMR Core Disable** (1 core, 2-bit register):

| Value | Core disabled |
|-------|--------------|
| `0x1` | Core 0 |
| `0x2` | Core 1 |

**If user asks for pseudo mesh without specifying which core/module:**
→ Ask: *"Which module/core combination do you want to disable? (see options above)"*

**This applies to Mesh mode only.** Slice mode with these fields → Rule 1 error.

---

## Rule 5 — Unit Chop

Unit chop defines the physical configuration of the silicon device and determines:
- Which `Check Core` values are valid
- Which masks are valid for DMR (CBBs)
- Number of computes available

**Always ask for unit chop if not provided.**

| Product | Chop Options | Description |
|---------|-------------|-------------|
| GNR | `AP` | 3 compute modules (Compute 0, 1, 2) |
| GNR | `SP` | 2 compute modules (Compute 0, 1) |
| CWF | `AP` | 3 compute modules, 4 cores/module |
| CWF | `SP` | 2 compute modules, 4 cores/module |
| DMR | `X1` | 1 CBB active (CBB0) |
| DMR | `X2` | 2 CBBs active (CBB0 + CBB1) |
| DMR | `X3` | 3 CBBs active (CBB0 + CBB1 + CBB2) |
| DMR | `X4` | 4 CBBs active (all) |

> **DMR Compute count is the same regardless of chop** — computes are Compute0–Compute3 on every DMR unit.
> Only the number of CBBs changes with chop.

**Placeholder note**: Check Core validation against specific module boundaries is a future enhancement.
Current behavior: warn if Check Core is 0 or unset.

---

## Rule 6 — Check Core

- **Must be asked** if not specified by the user.
- Should be **the same across all experiments in a batch**.
- `0` is technically valid but almost always unintentional — warn and confirm.
- Exception: PYSVConsole experiments do not require a Check Core.

**Agent prompt when Check Core is missing:**
> "What core should I monitor for these experiments? (Check Core — typically a core in the first valid module for your unit chop)"

---

## Rule 7 — Test Time

- Default: **30 seconds**.
- Apply silently — do **not** ask the user unless they raise it.
- If user asks for a specific test time → honor it and apply to all experiments unless they specify per-experiment.

---

## Rule 8 — Loops, Sweep Parameters, Shmoo Parameters

**These must ALWAYS be asked — never silently apply a preset default.**

| Field | Question to ask |
|-------|----------------|
| `Loops` | "How many loops do you need for each experiment?" |
| `Start` (Sweep) | "What is the sweep start value?" |
| `End` (Sweep) | "What is the sweep end value?" |
| `Steps` (Sweep) | "What step size/increment for the sweep?" |
| `Domain` (Sweep) | "Which domain to sweep? (IA / CFC)" |
| `Type` (Sweep) | "Sweeping Voltage or Frequency?" |
| `ShmooFile` | "What is the Shmoo configuration file path?" |
| `ShmooLabel` | "What Shmoo label/identifier should be used?" |

---

## Rule 9 — Test Number Assignment (Batch)

Assign test numbers in priority order across the entire batch:

1. **Tier 1 — Loops** experiments get the lowest numbers (starting from 1)
2. **Tier 2 — Sweep** experiments follow
3. **Tier 3 — Shmoo** experiments get the highest numbers

Use `constraints.assign_test_numbers(experiments)` or `validate_batch()` to automatically reorder.

---

## Rule 10 — Content-Specific Questions

### Dragon

**Show current values first, then ask what to change:**

Before collecting any Dragon fields, display the current preset/working-experiment values as a table:

| Field | Current Value |
|-------|---------------|
| ULX Path | *(value or blank)* |
| ULX CPU | *(value or blank)* |
| Product Chop | *(value or blank)* |
| Dragon Content Path | *(value or blank)* |
| Dragon Content Line | *(value or blank — filter)* |
| Startup Dragon | *(value or blank)* |
| Dragon Pre Command | *(value or blank)* |
| Dragon Post Command | *(value or blank)* |
| VVAR0 | *(value or blank)* |
| VVAR1 | *(value or blank)* |

Then ask: *"These are the current Dragon content settings. Which fields do you want to change? Say 'looks good' to keep them as-is."*

- For blank fields the user leaves unchanged → keep null in output.
- `Dragon Content Line` *(filter)* — if the user changes it, ask: *"Provide function names separated by commas. Leave blank to run all content."* Multiple filters are comma-separated in a single string.
- `VVAR0`, `VVAR1` — only collect if user opts to customise.
- `VVAR2` / `VVAR3` are **mode-managed** — do NOT ask (see Rule 3); warn if VVAR2 conflicts with current mode.

**Mesh vs Slice Dragon differences:**

| Config | Mesh | Slice |
|--------|------|-------|
| VVAR2 | `0x1000000` (all threads) | `0x1000002` (2 threads only) |
| Dragon Content Path | Mesh-specific content file | Slice-specific content file |
| Dragon Content Line | Mesh content function | Slice content function |

### Linux

**Show current values first, then ask what to change:**

Before collecting any Linux fields, display the current preset/working-experiment values as a table:

| Field | Current Value |
|-------|---------------|
| Linux Path | *(value or blank)* |
| Startup Linux | *(value or blank)* |
| Linux Pass String | *(value or blank)* |
| Linux Fail String | *(value or blank)* |
| Linux Pre Command | *(value or blank)* |
| Linux Post Command | *(value or blank)* |
| Linux Content Line 0 | *(value or blank)* |
| Linux Content Wait Time | *(value or blank)* |

Then ask: *"These are the current Linux content settings. Which fields do you want to change? Say 'looks good' to keep them as-is."*

- For blank fields the user leaves unchanged → keep null in output.
- `Linux Content Line 1` through `Linux Content Line 9` — only collect if the user needs additional command lines.
- Fields left blank after review = no value set (null in output).

### PYSVConsole

**Mandatory (ERROR if missing):**
- `Scripts File` — PythonSV script path. **Cannot run without this.**

**Should also ask:**
- `Boot Breakpoint` — if diagnosing boot/EFI issues
- `Bios File` — if a BIOS override is needed
- `Fuse File` — if fuse configuration is needed

---

## Rule 11 — Boot Failure / No EFI Suggestion

If a user reports: *"unit is not booting"*, *"not reaching EFI"*, *"stuck at POST"*, or similar:

→ **Suggest PYSVConsole experiment with Boot Breakpoint**:

```
Content: PYSVConsole
Boot Breakpoint: <appropriate breakpoint>
Scripts File:    <PythonSV script to analyze boot state>
Bios File:       <BIOS file if boot override needed>
```

Offer to help develop the PythonSV script or accept a user-provided one.
Document available boot breakpoints for each product.

---

## Rule 12 — DMR Pseudo Mesh Full Matrix Expansion

When a user asks for *"all pseudo mesh configurations"* or *"core hi + lo with CBBs and Computes"* for DMR:

1. Ask for unit chop (X1/X2/X3/X4) — determines active CBBs.
2. Ask for `Disable 1 Core` value, or build **all combinations**.
3. Build matrix: `active_cbbs × active_computes × core_disable_options`
4. Each combination becomes a separate experiment.

Use `constraints.expand_dmr_pseudo_mesh(unit_chop, base_experiment)` to generate the full list.

**Example for X2 (CBB0 + CBB1), Disable 1 Core = 0x1:**
- `Cbb0 + CoreDis0x1`
- `Cbb1 + CoreDis0x1`
- `Compute0 + CoreDis0x1`
- `Compute1 + CoreDis0x1`
- `Compute2 + CoreDis0x1`
- `Compute3 + CoreDis0x1`

---

## Rule 13 — Bucket Field

`Bucket` identifies **why the unit is being tested** — the failure category or analysis campaign it belongs to on the test floor. It is NOT derived from test type or content.

- **Always ask** if not already provided: *"What failure bucket or analysis category is this unit under? (e.g. BOOT_FAIL, CFC_MARGIN, IA_FREQ_MARGIN, STRESS, PPVC_CHAR, CUSTOMER_BUG)"*
- **Never infer** Bucket from `Test Mode`, `Test Type`, or `Content`.
- If a user gives a preset that includes a `Bucket` value, still confirm it before finalising.
- `BUCKET_MUST_ASK = True` in `constraints.py` — it is treated the same as `Loops`, `Start`, `End` etc.

---

## Rule 14 — Dragon Content Line (Filter)

`Dragon Content Line` controls which test functions inside the Dragon content file to execute.

- If left **blank**: Dragon runs all content in the file (default behaviour).
- If **one or more values** are provided: Dragon filters execution to those functions only.
- **Multiple filters** are entered as a **comma-separated string** in a single `Dragon Content Line` field.
  - Example: `func_mmf_mesh, func_ddr5_mesh`
- Ask the user: *"Do you want to filter Dragon content to specific functions? If yes, provide function names separated by commas. Leave blank for all content."*
- In batch builds, different experiments can have **different filter values** — collect per experiment.

---

## Rule 15 — Disabled Experiments in a Batch

The `"Experiment"` field accepts two values:
- **`"Enabled"`** — the experiment is active and will run on the Framework.
- **`"Disabled"`** — the experiment is intentionally skipped by the Framework at runtime.

### Validation behaviour

`experiment_builder.validate()` **never errors** on a disabled experiment.
Instead it returns a warning tagged `"EXPERIMENT_DISABLED: ..."` so the caller can detect it.
`experiment_builder.validate_batch()` returns a dedicated 4th value, `disabled_names`, listing the `Test Name` of every disabled experiment found.

### Agent behaviour — what to do when disabled experiments are detected

When loading a file (`load_from_file`) or receiving a batch that includes disabled experiments:

1. **Do NOT raise an error or block the workflow.**
2. List the disabled experiments clearly:
   ```
   The following experiments are marked Disabled:
     • <Test Name 1>
     • <Test Name 2>
   ```
3. Ask the user:
   > *"These experiments are disabled — they will be skipped by the Framework at runtime. Would you like to remove them from the output file, or keep them as-is?"*
   >
   > Options:
   > - **Remove all** → call `experiment_builder.filter_disabled(experiments)` and proceed with the filtered list.
   > - **Keep all** → leave the list unchanged and proceed.
   > - **Remove specific ones** → ask which ones to remove, then pop them by Test Name before proceeding.
4. If the user says they want to re-enable any: set `"Experiment": "Enabled"` using `update_fields(exp, {"Experiment": "Enabled"})`.
5. After the user's choice, continue with validation and export as normal.

### When to prompt vs. when to stay silent

| Scenario | Action |
|---|---|
| Single experiment loaded and it is Disabled | Prompt as above before editing |
| Batch loaded with ≥1 Disabled entry | Prompt once, list all disabled names |
| Batch loaded with ALL entries Disabled | Prompt the same way — do not auto-remove silently |
| User explicitly Creates a new experiment and asks for `Experiment = Disabled` | Accept, no prompt needed — the user already knows |
| validate_batch returns `disabled_names = []` | No prompt needed — nothing to ask |

---

## Config File Compliance Notes

*(Source: GNRControlPanelConfig.json, CWFControlPanelConfig.json, DMRControlPanelConfig.json)*

All field types and descriptions in the three config files are consistent with this constraint document.
Key field type reference:

| Field | Type | Notes |
|-------|------|-------|
| `COM Port` | `int` | Integer port number |
| `Voltage IA`, `Voltage CFC` | `float` | Voltage bump in Volts. `0` = no bump (valid, informational note). Max recommended: **0.3 V** (warning if exceeded). Negative values are an error. |
| `Frequency IA`, `Frequency CFC` | `int` | MHz |
| `Loops` | `int` | Test iterations |
| `Start`, `End`, `Steps` | `float` | Sweep parameters |
| `Test Number` | `int` | Sequential assignment |
| `Test Time` | `int` | Seconds; default 30 |
| `Check Core` | `int` | Core index |
| `Configuration (Mask)` | `str` (Mesh) / `int` (Slice) | Conditional type |
| `Pseudo Config` | `bool` | GNR only |
| `Disable 2 Cores` | `str` | CWF only; hex string |
| `Disable 1 Core` | `str` | DMR only; hex string |
| `Reset`, `Reset on PASS`, `FastBoot`, `Stop on Fail`, `600W Unit` | `bool` | All boolean |

---

## Quick Reference: What to Ask When

```
New experiment request received:
├── Product?                       → GNR / CWF / DMR  [ALWAYS]
├── Unit Chop?                     → AP/SP (GNR/CWF) or X1-X4 (DMR)  [ALWAYS if not given]
├── Test Mode?                     → Mesh / Slice  [ALWAYS]
├── Test Type?                     → Loops / Sweep / Shmoo  [ALWAYS]
├── Content?                       → Dragon / Linux / PYSVConsole  [ALWAYS]
├── Bucket?                        → ask ALWAYS — never infer  [ALWAYS]
├── Check Core?                    → ask if not given  [ALWAYS except PYSVConsole]
│
├── IF Loops → How many loops?     [ALWAYS — never default]
├── IF Sweep → Start, End, Steps, Domain, Type  [ALWAYS — never default]
├── IF Shmoo → ShmooFile, ShmooLabel  [ALWAYS — never default]
│
├── IF Dragon → ULX Path, Content Path, Startup, Pre/Post commands
│          → Dragon Content Line (filter) — ask, comma-separated, blank = all content
├── IF Linux  → Linux Path, Startup, Pass/Fail Strings, Content Lines, Pre/Post commands
├── IF PYSVConsole → Scripts File [MANDATORY], Boot Breakpoint if boot issue
│
├── IF Mode=Mesh + "pseudo"/"core hi-lo"/"sbft":
│   ├── GNR → Pseudo Config = True (no further ask needed)
│   ├── CWF → Disable 2 Cores: 0x3 / 0xc / 0x9 / 0xa / 0x5  [ask]
│   └── DMR → Disable 1 Core: 0x1 / 0x2  [ask]
│
└── Test Time → 30s default, do NOT ask unless user specifies
```
