# Dragon Content Prompt

Use this prompt when `content = Dragon` is selected in the intake.

Dragon content runs ULX binaries against the mesh or slice topology.

---

## Required Fields to Collect

| Field | Description | Example |
|-------|-------------|---------|
| ULX Path | Full path to ULX executable | `S:\GNR\RVP\ULX\xlnk_cpu.exe` |
| ULX CPU | CPU identifier string | `GNR_B0` / `CWF_B0` / `DMR` |
| Dragon Content Path | Path to Dragon content folder | `S:\GNR\RVP\Content\Mesh\` |
| Dragon Content Line | Optional: specific content line | `0` |
| Dragon Pre Command | Shell command before Dragon starts | (optional) |
| Dragon Post Command | Shell command after Dragon ends | (optional) |
| Startup Dragon | Whether to auto-start Dragon | `True` (default) |
| VVAR3 | Voltage variable 3 | `0x4000000` (GNR/CWF), `0x4200000` (DMR) |
| VVAR2 | Voltage variable 2 | `0x1000000` (mesh), `0x1000002` (slice) |
| Product Chop | Product chop identifier | `GNR` / `CWF` / `DMR` |

---

## Product-Specific Defaults (pre-filled)

| Field | GNR | CWF | DMR |
|-------|-----|-----|-----|
| ULX CPU | GNR_B0 | CWF_B0 | DMR |
| VVAR3 (mesh) | 0x4000000 | 0x4000000 | 0x4200000 |
| VVAR2 (mesh) | 0x1000000 | 0x1000000 | 0x1000000 |

---

## How to Collect Dragon Fields

1. **Present the current defaults** (from the loaded preset or working experiment) as a summary table:

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

2. Ask: *"These are the current Dragon content settings. Which fields do you want to change? Say 'looks good' to continue."*

3. For any field changed — or any field still blank — collect the new value:
   - **Dragon Content Line**: *"Do you want to filter to specific functions? Provide names separated by commas, or leave blank for all content."*
   - **VVAR0 / VVAR1**: only if the user opts to customise.
   - **VVAR2 / VVAR3**: do NOT ask — set from product + mode defaults.

4. Blank fields the user does not fill = null in output (no value set).

---

## Relevant Presets

- `gnr_dragon_base_h` — GNR baseline Dragon with high voltage
- `gnr_dragon_base_l` — GNR baseline Dragon with low voltage
- `cwf_dragon_base_h` / `cwf_dragon_base_l`
- `dmr_dragon_base_h` / `dmr_dragon_base_l`
