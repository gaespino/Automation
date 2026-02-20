# Test Loops Prompt

Use this prompt when `test_type = Loops` is selected in the intake.

The Loops test type repeats the content execution a fixed number of times,
resetting the SUT between iterations.

---

## Required Fields

| Field | Description | Default |
|-------|-------------|---------|
| Loops | Number of repetitions | `5` |
| Test Time | Max time per loop (seconds) | `30` |
| Reset | Reset board between loops | `True` |
| Reset on PASS | Also reset on a passing iteration | `True` |
| Stop on Fail | Halt the run on first failure | `True` |
| Pass String | Output string indicating pass | `Test Complete` |
| Fail String | Output string indicating fail | `Test Failed` |

---

## Questions to Ask User

1. How many loops should the test run? (default: 5)
2. What is the per-loop time limit in seconds? (default: 30)
3. Should the test stop on first failure? (default: Yes)
4. Are the default pass/fail strings correct, or do you need custom ones?

---

## Common Loop Configurations

| Scenario | Loops | Test Time | Reset on PASS |
|----------|-------|-----------|---------------|
| Quick smoke | 3 | 20 | True |
| Standard regression | 10 | 60 | True |
| Long soak | 50 | 120 | True |
| Stress (no reset on pass) | 20 | 90 | False |

---

## Relevant Presets

Loops presets are available in the `test` category for each product:
- `{product}_loops_quick`
- `{product}_loops_standard`
- `{product}_loops_soak`
