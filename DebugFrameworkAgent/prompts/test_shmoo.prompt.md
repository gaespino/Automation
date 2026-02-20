# Test Shmoo Prompt

Use this prompt when `test_type = Shmoo` is selected in the intake.

Shmoo runs a 2-dimensional parameter sweep defined by a pre-built ShmooFile.

---

## Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| ShmooFile | Path to the .shmoo definition file | `S:\GNR\RVP\Shmoo\voltage_freq_shmoo.json` |
| ShmooLabel | Human-readable label for this shmoo run | `GNR_B0_VF_Shmoo_v2` |
| Test Time | Max time per shmoo point (seconds) | `60` |
| Loops | Loops at each shmoo point | `1` |

---

## Shmoo File Format Summary

A ShmooFile defines the 2D sweep grid. Each point is evaluated independently.
The framework plots pass/fail results as a heat map.

Minimum required fields in ShmooFile JSON:
```json
{
  "x_axis": {"name": "Frequency (MHz)", "values": [3000, 3200, 3400, 3600, 3800, 4000]},
  "y_axis": {"name": "Voltage (mV)",    "values": [ 900,  950, 1000, 1050, 1100]},
  "pass_string": "Test Complete",
  "fail_string": "Test Failed"
}
```

---

## Questions to Ask User

1. What is the path to the ShmooFile?
2. What label should identify this shmoo run?
3. How many loops at each grid point? (default: 1)
4. What is the per-point time limit? (default: 60s)

---

## Relevant Presets

- `{product}_shmoo_vf` — Voltage vs Frequency shmoo
- `{product}_shmoo_stability` — Long-duration stability shmoo
