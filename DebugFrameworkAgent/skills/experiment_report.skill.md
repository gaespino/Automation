# Skill: Experiment Report Generation

## Purpose

Every time an experiment is generated or a preset is applied, automatically produce a human-readable configuration report alongside the JSON output. The report makes it easy to review, share, and audit experiment settings — no code required to read it.

---

## Output Formats

| Format | Always available | Notes |
|--------|-----------------|-------|
| **Markdown** (`.md`) | Yes | Plain text, renders in VS Code, GitHub, any Markdown viewer |
| **HTML** (`.html`) | Yes | Styled, opens in any browser; use **File → Print → Save as PDF** to get a PDF |
| **PDF** (`.pdf`) | Optional | Requires `pip install "fpdf2>=2.7"`; produces a true PDF with pagination |

By default both **Markdown** and **HTML** are always generated.

---

## Report Sections

Each report is organized into logical sections. Sections whose fields are all empty are automatically hidden to keep the report clean.

| Section | Always shown | Shown when |
|---------|-------------|-----------|
| Basic Settings | Yes | — |
| Connection & Unit | Yes | — |
| Test Execution | Yes | — |
| Voltage & Frequency | Yes | — |
| Dragon Content | No | `Content` is `Dragon` or any Dragon field is set |
| Linux Content | No | `Content` is `Linux` or any Linux field is set |
| PYSVConsole Content | No | `Content` is `PYSVConsole` or `Scripts File` is set |
| Fuse / BIOS | No | `Fuse File` or `Bios File` is set |
| Shmoo | No | `ShmooFile` or `ShmooLabel` is set |
| Merlin | Yes | — |
| TTL Config | Yes | — |
| Validation Results | When included | Only if `--validate` flag or calling code passes validation results |

---

## How It Works

### Auto-generation (built into `generate_experiment.py` and `apply_preset.py`)

Every successful export automatically creates reports in the same output directory as the JSON:

```
output/
    MyTest.json
    MyTest_report.md        ← always generated
    MyTest_report.html      ← always generated
```

To skip reports:
```bash
python generate_experiment.py --product GNR --no-report ...
```

To request PDF in addition to Markdown + HTML:
```bash
python generate_experiment.py --product GNR --report-format md html pdf ...
```

### Standalone CLI

```bash
# Generate Markdown + HTML (default)
python generate_report.py experiment.json

# Generate only one format
python generate_report.py experiment.json --format md
python generate_report.py experiment.json --format html
python generate_report.py experiment.json --format pdf

# Generate all three + include validation results
python generate_report.py experiment.json --format md html pdf --validate

# Custom output directory
python generate_report.py experiment.json --out ./reports/

# Product label override
python generate_report.py experiment.json --product GNR
```

### Programmatic API

```python
from scripts._core import exporter, experiment_builder

# With validation results
ok, errors, warnings = experiment_builder.validate(my_exp)
written = exporter.write_report(
    my_exp,
    out_dir="./output/",
    name="MyTest",
    formats=("md", "html"),          # or ("md", "html", "pdf")
    validation_result=(ok, errors, warnings),
    product="GNR",
)
# written == {"md": Path("output/MyTest_report.md"), "html": Path("output/MyTest_report.html")}
```

---

## PDF Notes

- The HTML report is designed to be **print-friendly**. In any browser, press **Ctrl+P** (or **Cmd+P** on Mac), choose **Save as PDF**, and you get a formatted PDF without installing any extra packages.
- For automated, code-driven PDF generation, install `fpdf2`:
  ```
  pip install "fpdf2>=2.7"
  ```
  Then add `"pdf"` to the formats list. If fpdf2 is not installed and PDF is requested, a clear error with the install command is printed.

---

## VS Code Task

Use **Terminal → Run Task → DFA: Generate Report** to generate a report from an experiment file without leaving the editor. The task prompts for the experiment file path and runs `generate_report.py --format md html`.

---

## When to Use This Skill

- After generating a new experiment: review the HTML report to spot misconfigured fields.
- Before handing off an experiment to another team member: share the `.md` or `.pdf` report instead of the JSON.
- When investigating test failures: the report timestamps and shows exactly what configuration was active.
- During code review or change management: diff two `.md` reports to see what changed between versions.
