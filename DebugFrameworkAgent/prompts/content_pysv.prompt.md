# PYSVConsole Content Prompt

Use this prompt when `content = PYSVConsole` is selected in the intake.

PYSVConsole executes Python test scripts against the SUT via the PYSV console interface.

---

## Required Fields to Collect

| Field | Description | Example |
|-------|-------------|---------|
| Scripts File | Path to .py script or scripts list file | `S:\GNR\RVP\Scripts\test_pwr.py` |
| Pass String | String in output that marks pass | `Test Complete` |
| Fail String | String in output that marks fail | `Test Failed` |
| Merlin Path | EFI shell path to Merlin binary folder | `FS1:\EFI\Version8.15\BinFiles\Release` |
| Merlin Name | Merlin executable filename | `MerlinX.efi` |
| Merlin Drive | EFI drive designator | `FS1:` |
| FastBoot | Whether to enable fast boot | `True` (GNR/CWF), `False` (DMR) |

---

## Product-Specific Defaults

| Field | GNR | CWF | DMR |
|-------|-----|-----|-----|
| Merlin Path | `FS1:\EFI\Version8.15\BinFiles\Release` | `FS1:\EFI\Version8.15\BinFiles\Release` | `FS1:\EFI\Version8.23\BinFiles\Release` |
| FastBoot | True | True | False |

---

## Questions to Ask User

1. What is the path to the Scripts File?
2. What pass/fail strings should the framework monitor?
3. Do you need a custom Merlin version? (defaults are pre-filled per product)
4. How many loops should the test run? (default: 5)

---

## Relevant Presets

- `gnr_pysv_base` — GNR baseline PYSVConsole
- `cwf_pysv_base` — CWF baseline PYSVConsole
- `dmr_pysv_base` — DMR baseline PYSVConsole
