# Linux Content Prompt

Use this prompt when `content = Linux` is selected in the intake.

Linux content runs stress workloads on the SUT under a Yocto/kernel environment.

---

## Required Fields to Collect

| Field | Description | Example |
|-------|-------------|---------|
| Linux Path | Path to Linux image/script folder | `Q:\DPM_Debug\GNR\Linux\` |
| Startup Linux | Auto-start Linux environment | `True` (default) |
| Linux Pre Command | Command before Linux starts | (optional) |
| Linux Post Command | Command after Linux ends | (optional) |
| Linux Pass String | String indicating test pass | `Test Complete` |
| Linux Fail String | String indicating test fail | `Test Failed` |
| Linux Content Wait Time | Seconds to wait for content load | `120` |
| Linux Content Line 0–9 | Up to 10 test execution lines | (content-specific) |

---

## Product-Specific TTL Defaults

| Product | Linux TTL Path |
|---------|----------------|
| GNR | `Q:\DPM_Debug\GNR\TTL_Linux` |
| CWF | `R:\Templates\CWF\version_2_0\TTL_Linux` |
| DMR | *(not available — verify before use)* |

---

## How to Collect Linux Fields

1. **Present the current defaults** (from the loaded preset or working experiment) as a summary table:

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

2. Ask: *"These are the current Linux content settings. Which fields do you want to change? Say 'looks good' to continue."*

3. For any field changed — or any field still blank — collect the new value:
   - **Linux Content Line 1–9**: only collect if the user needs additional execution lines.
   - Fields left blank by the user = null in output (no value set).

---

## Relevant Presets

- `gnr_linux_base` — GNR baseline Linux loops
- `cwf_linux_base` — CWF baseline Linux loops
