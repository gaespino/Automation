# Skill: Experiment Generator

This skill provides the complete domain knowledge for generating Debug Framework experiment configuration files.

---

## 0. Preset System

Presets are stored in `DebugFrameworkAgent/defaults/presets/` as per-product files (`common.json`, `GNR.json`, `CWF.json`, `DMR.json`). Each preset is a fully-populated experiment dict with:
- `label` — display name shown in the preset menu
- `description` — one-line explanation of the preset's purpose
- `products` — list of compatible product codes
- `ask_user` — the minimal set of fields to prompt; all other fields use preset defaults
- `experiment` — the complete pre-filled field dict

### Preset workflow (Path C)
1. Load `DebugFrameworkAgent/defaults/presets/` using `preset_loader.load_all()` (auto-merges all product files).
2. Filter presets by selected product (show only those whose `products` list includes the product).
3. Display numbered menu with `label` and `description`.
4. On selection, copy the preset's `experiment` dict as the working data.
5. Prompt **only** the `ask_user` fields, showing the preset value as the current default.
6. Offer an "anything else?" free-form override step.
7. Proceed to validation and export like any other path.

### Available presets

| # | Label | Test Type | Content | Voltage | Notes |
|---|-------|-----------|---------|---------|-------|
| 1 | Baseline Loops — Dragon (vbump) | Loops | Dragon | vbump | Most common; all products |
| 2 | PPVC Loops — Dragon (ppvc) | Loops | Dragon | ppvc | Power delivery char |
| 3 | Fixed Voltage Loops — Dragon | Loops | Dragon | fixed | Margin char at fixed V |
| 4 | Voltage Sweep — IA Domain | Sweep | Dragon | fixed | Voltage margin sweep |
| 5 | Frequency Sweep — IA Domain | Sweep | Dragon | vbump | Frequency margin sweep |
| 6 | Shmoo Test | Shmoo | Dragon | vbump | 2D param map |
| 7 | Baseline Loops — Linux | Loops | Linux | vbump | Linux binary/script |
| 8 | Slice Mode Loops | Loops | Dragon | vbump | Single-core isolation |
| 9 | Stress Test — AllFail Mode | Loops | Dragon | vbump | 20-loop stress, AllFail node |

### Adding custom presets
To add a new preset, edit the appropriate file in `DebugFrameworkAgent/defaults/presets/` (`common.json` for all-product presets, `GNR.json` / `CWF.json` / `DMR.json` for product-specific ones). The key should be descriptive (e.g. `gnr_boot_baseline`).

---

## 1. Output Format

The final output is a JSON file keyed by experiment name. Each value is the experiment's field dictionary:

```json
{
  "Baseline_Mesh": {
    "Experiment": "Enabled",
    "Test Name": "Baseline Loop Test",
    "Test Mode": "Mesh",
    "Test Type": "Loops",
    "Visual ID": "45S50N5500909",
    "Bucket": "BASELINE",
    "COM Port": 8,
    "IP Address": "192.168.1.100",
    "Content": "Dragon",
    "Test Number": 1,
    "Test Time": 45,
    "Reset": true,
    "Reset on PASS": true,
    "FastBoot": true,
    "Core License": "",
    "Pseudo Config": true,
    "Voltage Type": "vbump",
    "Voltage IA": null,
    "Voltage CFC": null,
    "Frequency IA": null,
    "Frequency CFC": null,
    "Loops": 5,
    "Type": null,
    "Domain": null,
    "Start": null,
    "End": null,
    "Steps": null,
    "ShmooFile": null,
    "ShmooLabel": null,
    "Configuration (Mask)": "",
    "Check Core": 0,
    "Boot Breakpoint": "0xa2000000",
    "TTL Folder": "",
    "Scripts File": "",
    "Pass String": "Test Complete",
    "Fail String": "FAILED",
    "Stop on Fail": false,
    "Post Process": "",
    "ULX Path": "",
    "ULX CPU": "",
    "Dragon Pre Command": "",
    "Dragon Post Command": "",
    "Startup Dragon": "",
    "Dragon Content Path": "",
    "Dragon Content Line": "",
    "VVAR0": "",
    "VVAR1": "",
    "VVAR2": "",
    "VVAR3": "",
    "VVAR_EXTRA": "",
    "Merlin Name": "",
    "Merlin Drive": "",
    "Merlin Path": "",
    "Fuse File": "",
    "Bios File": ""
  }
}
```

> Fields not applicable to the selected Test Type or Content type should be `null` (not omitted) to maintain schema consistency.

---

## 2. .tpl File Format

A `.tpl` file is a JSON file with this wrapper structure:

```json
{
  "version": "1.0",
  "product": "GNR",
  "created": "2026-02-19",
  "experiments": {
    "Baseline_Mesh": { ...experiment fields... },
    "PPVC_Mesh": { ...experiment fields... }
  }
}
```

The `experiments` dict matches the export JSON exactly. When loading a `.tpl`, use the `experiments` key as the data source.

---

## 3. Complete Field Catalogue

Fields are organized by section. Section order for interactive collection:

1. Basic Information
2. Unit Data
3. Test Configuration
4. Voltage & Frequency
5. Loops *(only when Test Type == "Loops")*
6. Sweep *(only when Test Type == "Sweep")*
7. Shmoo *(only when Test Type == "Shmoo")*
8. Linux *(only when Content == "Linux")*
9. Dragon *(only when Content == "Dragon")*
10. Advanced Configuration
11. Merlin

### Section 1: Basic Information

| Field | Type | Default | Options | Required |
|-------|------|---------|---------|----------|
| `Experiment` | str | `""` | — | ✅ |
| `Test Name` | str | `""` | — | ✅ |
| `Test Mode` | str | `"Mesh"` | Mesh, Slice | ✅ |
| `Test Type` | str | `"Loops"` | Loops, Sweep, Shmoo | ✅ |

### Section 2: Unit Data

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `Visual ID` | str | `""` | Chip visual/labeling ID |
| `Bucket` | str | `""` | Test category |
| `COM Port` | int | `1` | Serial port number |
| `IP Address` | str | `""` | Format: `x.x.x.x` |
| `Product` | str | product | Auto-set from product selection |

### Section 3: Test Configuration

| Field | Type | Default | Options / Notes |
|-------|------|---------|----------------|
| `Content` | str | `"Linux"` | Linux, Dragon, PYSVConsole |
| `Test Number` | int | `0` | Sequence number |
| `Test Time` | int | `0` | Seconds |
| `Reset` | bool | `false` | Reset before test |
| `Reset on PASS` | bool | `false` | Reset after pass |
| `FastBoot` | bool | `false` | Enable fast boot |
| `Core License` | str | `""` | *GNR/DMR only.* Options: `""`, `1: SSE/128`, `2: AVX2/256 Light`, `3: AVX2/256 Heavy`, `4: AVX3/512 Light`, `5: AVX3/512 Heavy`, `6: TMUL Light`, `7: TMUL Heavy` |
| `600W Unit` | bool | `false` | Use 600W PSU |
| `Pseudo Config` | bool | `false` | *GNR only.* Enable pseudo config mode |
| `Post Process` | str | `""` | Post-processing script path |
| `Configuration (Mask)` | str | `""` | *Mesh:* RowPass1–3, FirstPass, SecondPass, ThirdPass; *Slice:* core number (GNR/CWF: 0–179, DMR: 0–128) |
| `Boot Breakpoint` | str | `""` | e.g. `0xa2000000` |
| `Disable 2 Cores` | str | `""` | *CWF only.* Options: `0x3`, `0xc`, `0x9`, `0xa`, `0x5` |
| `Disable 1 Core` | str | `""` | *DMR only.* Options: `0x1`, `0x2` |
| `Check Core` | int | `0` | Core to monitor |

### Section 4: Voltage & Frequency

| Field | Type | Default | Options |
|-------|------|---------|---------|
| `Voltage Type` | str | `"vbump"` | vbump, fixed, ppvc |
| `Voltage IA` | float | `0.0` | IA domain voltage (V); `null` if not used |
| `Voltage CFC` | float | `0.0` | CFC domain voltage (V); `null` if not used |
| `Frequency IA` | int | `0` | IA frequency (MHz); `null` if not used |
| `Frequency CFC` | int | `0` | CFC frequency (MHz); `null` if not used |

### Section 5: Loops *(condition: Test Type == "Loops")*

| Field | Type | Default |
|-------|------|---------|
| `Loops` | int | `1` |

### Section 6: Sweep *(condition: Test Type == "Sweep")*

| Field | Type | Default | Options |
|-------|------|---------|---------|
| `Type` | str | `"Voltage"` | Voltage, Frequency |
| `Domain` | str | `"IA"` | IA, CFC |
| `Start` | float | `0.0` | Sweep start value |
| `End` | float | `0.0` | Sweep end value; must be > Start |
| `Steps` | float | `1.0` | Sweep increment |

### Section 7: Shmoo *(condition: Test Type == "Shmoo")*

| Field | Type | Default |
|-------|------|---------|
| `ShmooFile` | str | `""` |
| `ShmooLabel` | str | `""` |

### Section 8: Linux *(condition: Content == "Linux")*

| Field | Type | Default |
|-------|------|---------|
| `Linux Path` | str | `""` |
| `Linux Pre Command` | str | `""` |
| `Linux Post Command` | str | `""` |
| `Linux Pass String` | str | `""` |
| `Linux Fail String` | str | `""` |
| `Linux Content Wait Time` | int | `0` |
| `Startup Linux` | str | `""` |
| `Linux Content Line 0` – `Linux Content Line 9` | str | `""` |

### Section 9: Dragon *(condition: Content == "Dragon")*

| Field | Type | Default |
|-------|------|---------|
| `ULX Path` | str | `""` |
| `ULX CPU` | str | `""` |
| `Product Chop` | str | `""` |
| `Dragon Pre Command` | str | `""` |
| `Dragon Post Command` | str | `""` |
| `Startup Dragon` | str | `""` |
| `Dragon Content Path` | str | `""` |
| `Dragon Content Line` | str | `""` |
| `VVAR0` – `VVAR3` | str | `""` |
| `VVAR_EXTRA` | str | `""` |

### Section 10: Advanced Configuration

| Field | Type | Default |
|-------|------|---------|
| `TTL Folder` | str | `""` |
| `Scripts File` | str | `""` |
| `Pass String` | str | `""` |
| `Fail String` | str | `""` |
| `Stop on Fail` | bool | `false` |
| `Fuse File` | str | `""` |
| `Bios File` | str | `""` |

### Section 11: Merlin

| Field | Type | Default |
|-------|------|---------|
| `Merlin Name` | str | `""` |
| `Merlin Drive` | str | `""` |
| `Merlin Path` | str | `""` |

---

## 4. Product-Specific Field Availability

From `field_enable_config` in the config JSONs:

| Field | GNR | CWF | DMR |
|-------|-----|-----|-----|
| `Pseudo Config` | ✅ | ❌ | ❌ |
| `Disable 2 Cores` | ❌ | ✅ | ❌ |
| `Disable 1 Core` | ❌ | ❌ | ✅ |
| `Core License` | ✅ | ❌ | ✅ |

All other fields are available for all products.

---

## 5. Validation Rules

| Rule | Error Level |
|------|------------|
| `Experiment` must not be empty | Error |
| `Test Name` must not be empty | Error |
| Experiment names must be unique in the export file | Error |
| `IP Address` must match `^\d{1,3}(\.\d{1,3}){3}$` if provided | Error |
| If `Test Type == "Sweep"`: `Start`, `End`, `Steps` must all be non-zero | Error |
| If `Test Type == "Sweep"`: `End > Start` | Error |
| If `Test Type == "Shmoo"`: `ShmooFile` must not be empty | Error |
| If `Content == "Linux"`: `Linux Path` is empty | Warning |
| If `Content == "Dragon"`: `ULX Path` is empty | Warning |
| `Loops` must be >= 1 if `Test Type == "Loops"` | Warning |
| `Test Time` of 0 means no timeout (valid but worth noting) | Info |

---

## 6. Null Field Policy

For fields that do not apply to the current Test Type or Content, write `null` (not the default value, not omitted):

- `Test Type == "Loops"` → `Type`, `Domain`, `Start`, `End`, `Steps`, `ShmooFile`, `ShmooLabel` = `null`
- `Test Type == "Sweep"` → `Loops`, `ShmooFile`, `ShmooLabel` = `null`
- `Test Type == "Shmoo"` → `Loops`, `Type`, `Domain`, `Start`, `End`, `Steps` = `null`
- `Content != "Linux"` → all Linux fields = `null` (or `""` for string fields)
- `Content != "Dragon"` → all Dragon fields = `null` (or `""` for string fields)

---

## 7. Session Save Behavior

When the user opts to save a `.tpl`:

1. Wrap all experiments in the `.tpl` envelope (see Section 2).
2. Save to `<requested_path>/<name>.tpl`.
3. Also save the export JSON to `<requested_path>/<name>.json` for direct use by `ControlPanel.py`.
4. Report both file paths to the user.

---

## 8. Config File Paths

The config files that drive field options are at:
- `PPV/configs/GNRControlPanelConfig.json`
- `PPV/configs/CWFControlPanelConfig.json`
- `PPV/configs/DMRControlPanelConfig.json`

---

## 9. Fuse Collection Wizard

The Fuse Collection wizard builds a special boot-mode experiment that generates fuse override data. It is triggered when the user:
- Selects a fuse preset from the product preset menu, **or**
- Answers "yes" to the intake question *"Does this involve fuse override data collection?"*

### Wizard interaction

1. Ask: **"Which product? (GNR / CWF / DMR)"** (skip if already known from intake).
2. Ask: **"Boot COM port"** — show product default (11 for GNR/CWF; 9 for DMR).
3. Ask: **"Check Core"** — show product default (`null` for GNR/CWF fuse runs; `32` for DMR).
4. Ask: **"Output path for the experiment JSON?"**

### Product-specific fuse parameters

| Field | GNR | CWF | DMR |
|---|---|---|---|
| `Content` | `PYSVConsole` | `PYSVConsole` | `PYSVConsole` |
| `TTL Folder` | `R:/Templates/GNR/version_1_0/TTL_Boot` | `R:/Templates/CWF/version_1_0/TTL_Boot` | `R:/Templates/DMR/version_1_0/TTL_Boot` |
| `Scripts File` | `R:/Templates/scripts/fuse_generation.txt` | `R:/Templates/scripts/fuse_generation.txt` | `R:/Templates/scripts/fuse_generation_dmr.txt` |
| `Reset` | `false` | `false` | `false` |
| `Boot Breakpoint` | `0xbf000000` | `0xbf000000` | `0xbf000000` |
| `Check Core` | `null` | `null` | `32` |
| `Loops` | `1` | `1` | `2` |
| `COM Port` | `11` | `11` | `9` |
| `ULX CPU` | `GNR_B0` | `CWF_B0` | *(boot only — not used)* |

### Preset keys (Path C)
- GNR: `gnr_fuse_collection` (in `GNR.fuse_collection`)
- CWF: `cwf_fuse_collection` (in `CWF.fuse_collection`)
- DMR: `dmr_fuse_generator` (in `DMR.fuse_collection`)

### Notes
- GNR and CWF share `fuse_generation.txt`; only the TTL folder path differs.
- DMR uses a dedicated script (`fuse_generation_dmr.txt`) and requires `Check Core = 32`.
- All fuse runs use `Reset = false` and `Reset on PASS = false` to preserve state.
- After fuse collection, remind the user to stage the generated `.fuse` file before running content experiments.

---

## 10. Product Configuration Reference

Per-product default values for the most commonly varied fields. Use as authoritative defaults when building new experiments or validating user-provided values.

### Critical field defaults by product

| Field | GNR | CWF | DMR |
|---|---|---|---|
| `Check Core` (content loops) | `36` | `7` | `24` |
| `COM Port` | `11` | `11` | `9` |
| `IP Address` | `192.168.0.2` | `10.250.0.2` | `192.168.0.2` |
| `ULX CPU` | `GNR_B0` | `CWF_B0` | `DMR` |
| `Product Chop` | `GNR` | `CWF` | `DMR` |
| `VVAR3` (mesh) | `0x4000000` | `0x4000000` | `0x4200000` |
| `VVAR3` (slice) | `0x4000000` | `0x4000000` | `0x4210000` |
| `VVAR2` (mesh) | `0x1000000` | `0x1000000` | `0x1000000` |
| `VVAR2` (slice) | `0x1000002` | `0x1000002` | `0x1000002` |
| `Merlin Path` | `FS1:\EFI\Version8.15\BinFiles\Release` | `FS1:\EFI\Version8.15\BinFiles\Release` | `FS1:\EFI\Version8.23\BinFiles\Release` |
| `FastBoot` (content loops) | `true` | `true` | `false` |
| `FastBoot` (sweeps) | `true` | `false` | `false` |
| `Post Process` (Dragon Base H) | `null` | `null` | `R:/Templates/scripts/dmr_tor_dump.txt` |

### TTL folder patterns

| Mode | GNR | CWF | DMR |
|---|---|---|---|
| Boot | `R:/Templates/GNR/version_1_0/TTL_Boot` | `R:/Templates/CWF/version_1_0/TTL_Boot` | `R:/Templates/DMR/version_1_0/TTL_Boot` |
| Mesh (content) | `S:\GNR\RVP\TTLs\TTL_DragonMesh` | `R:/Templates/CWF/version_2_0/TTL_DragonMesh` | `R:\Templates\DMR\version_2_0\TTL_DragonMesh` |
| Slice | `S:\GNR\RVP\TTLs\TTL_DragonSlice` | `R:\Templates\CWF\version_2_0\TTL_DragonSlice` | `R:/Templates/DMR/version_2_0/TTL_DragonSlice` |
| Linux | `Q:\DPM_Debug\GNR\TTL_Linux` | `R:\Templates\CWF\version_2_0\TTL_Linux` | *(no standard Linux TTL)* |

### COREHI / CORELO naming convention (DMR only)

DMR supports intra-module single-core targeting via the `Disable 1 Core` field:

| Name | `Disable 1 Core` | Meaning |
|---|---|---|
| `COREHI` | `"0x2"` | Core 1 — higher core in module |
| `CORELO` | `"0x1"` | Core 0 — lower core in module |

Used with content path: `DMR32M_L_RO_Bcast_pseudoSBFT_Tester`. Both require `Stop on Fail = false`.

### Sweep range reference

| Sweep family | Domain | Start | End | Steps |
|---|---|---|---|---|
| Voltage bump (vbP) | CFC or IA | `-0.03` | `0.06` | `0.03` |
| Voltage characterisation | CFC or IA | `0.05` | `0.2` | `0.05` |
| Frequency flat — CFC (GNR) | CFC | `8.0` | `22.0` | `4.0` |
| Frequency flat — CFC (CWF/DMR) | CFC | `8.0` | `12.0` | `4.0` |
| Frequency flat — IA (GNR) | IA | `8.0` | `32.0` | `4.0` |
| Frequency flat — IA (CWF/DMR) | IA | `8.0` | `24.0` | `4.0` |
| Frequency high — IA (GNR) | IA | `36.0` | `40.0` | `4.0` |

---

## 11. Scripts File & Post Process — Authoring Rules

### How these fields are executed

Both `Scripts File` and `Post Process` point to **`.txt` files** whose content is read at runtime and executed via Python's `eval()` / `exec()` mechanism inside the Framework. They are **not** imported as modules — they are plain text evaluated in the framework's execution context.

Because of this, **complex Python constructs are fragile inside these files**. The Framework evaluates them in a specific scope and any syntax Python cannot cleanly resolve in `eval`/`exec` (multi-step logic, nested functions, class definitions, exception handling blocks) will cause silent failures or hard-to-debug errors.

### Rule: Keep script content minimal

When asked to write, edit, or suggest content for a `Scripts File` or `Post Process` text file, follow these constraints:

| ✅ Allowed | ❌ Avoid |
|---|---|
| Simple import statements | Class definitions |
| Single-line function calls | `try` / `except` / `finally` blocks |
| Direct variable assignments | Multi-level nested `if`/`for`/`while` |
| Calls to already-imported module functions | Lambda expressions with side effects |
| One-liner conditionals (ternary only) | `async`/`await` constructs |
| `print()` for logging | Decorator definitions |

**Good example** (acceptable script file content):
```python
import my_post_processor
my_post_processor.run(results_folder, unit_id)
```

**Bad example** (do NOT suggest):
```python
def process():
    for r in results:
        if r.status == 'FAIL':
            try:
                upload(r)
            except Exception as e:
                print(e)
process()
```

### Rule: Complex logic → external `.py` module

If the user's requirement cannot be expressed in one or two lines:

1. **Suggest building a standalone `.py` file** in the same folder as the script (e.g. alongside the existing `fuse_generation.txt`).
2. The `.py` file contains all the complex logic as ordinary importable Python.
3. The `.txt` script file keeps a single `import` + single function call.

**Suggested phrasing when escalating:**
> "This logic is too complex for a direct script file (`.txt` files are executed via `eval`). I recommend creating `<name>.py` in `R:/Templates/scripts/` with the full logic, then calling it from the script file with a single import + function call."

### Applies to both fields

- `Scripts File` — runs before/during the test loop (setup, fuse operations, custom instrumentation)
- `Post Process` — runs after all results are collected (data upload, report generation, file staging)

Both share the same execution constraints described above.
