# Test Sweep Prompt

Use this prompt when `test_type = Sweep` is selected in the intake.

Sweeps iterate over a voltage or frequency range in defined steps.

---

## Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| Type | Sweep axis type | `Voltage` \| `Frequency` |
| Domain | Die domain to sweep | `IA` \| `CFC` |
| Start | Starting value (mV or MHz) | `900` (voltage), `3000` (freq) |
| End | Ending value | `1100` (voltage), `4200` (freq) |
| Steps | Number of steps between Start and End | `5` |
| Voltage Type | Which voltage rail | `vbump` \| `vid` |

---

## Sweep Logic

The framework calculates step increments as:
`increment = (End - Start) / (Steps - 1)`

**Validation rules:**
- End > Start (enforced by validator)
- Steps >= 2
- Domain must be `IA` or `CFC`
- Type must be `Voltage` or `Frequency`

---

## Questions to Ask User

1. Are you sweeping **Voltage** or **Frequency**?
2. Which domain — **IA** or **CFC**? (if unsure, IA is most common)
3. What is the **start** value?
4. What is the **end** value?
5. How many **steps** do you want between start and end?
6. For voltage sweeps: `vbump` or `vid`? (default: vbump)

---

## Common Sweep Configurations

| Use case | Type | Domain | Start | End | Steps |
|----------|------|--------|-------|-----|-------|
| Vbump margin | Voltage | IA | 850 | 1100 | 6 |
| Frequency step-down | Frequency | IA | 4200 | 3000 | 5 |
| CFC voltage walk | Voltage | CFC | 800 | 1050 | 6 |

---

## Relevant Presets

- `{product}_voltage_sweep_ia` — IA domain voltage sweep
- `{product}_voltage_sweep_cfc` — CFC domain voltage sweep
- `{product}_freq_sweep` — IA frequency sweep
