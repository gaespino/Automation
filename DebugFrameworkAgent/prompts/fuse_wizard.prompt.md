# Fuse Wizard Prompt

Use this prompt when `content = FuseWizard` is selected in the intake.

FuseWizard performs fuse read, program, or verify operations on the SUT.

---

## Warning

> **Fuse operations are irreversible on physical silicon.**
> Always test on emulation or pre-silicon units first.
> Confirm with the platform engineering team before programming fuses on lab units.

---

## Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| Fuse File | Path to the fuse definition/patch file | `S:\GNR\Fuses\patch_v2.xml` |
| Bios File | BIOS binary used during fuse operation | `S:\GNR\BIOS\gnr_b0_bios.bin` |
| COM Port | Serial port for SUT communication | `11` (GNR/CWF), `9` (DMR) |
| IP Address | SUT IP address | Product default |
| Test Mode | Always `Boot` for fuse operations | `Boot` (enforced) |
| Content | Always `FuseWizard` | auto-set |

---

## Operation Types

| Mode | Description |
|------|-------------|
| Read | Non-destructive read of current fuse state |
| Verify | Compare current fuse state against Fuse File |
| Program | Write Fuse File values to SUT (irreversible) |

---

## Questions to Ask User

1. What operation do you need — Read, Verify, or Program?
2. What is the path to the Fuse File?
3. What BIOS binary should be used?
4. Has this Fuse File been validated on emulation? (Program mode only)
5. Has the fuse operation been approved by the platform team? (Program mode only)

---

## Relevant Presets

- `{product}_fuse_read`   — Non-destructive fuse state read
- `{product}_fuse_verify` — Fuse state verify against patch file

> **Note:** No `_fuse_program` presets are provided.
> Program experiments must be created manually with explicit field values.
