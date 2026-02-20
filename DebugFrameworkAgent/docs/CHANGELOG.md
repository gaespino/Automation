# Changelog — DebugFrameworkAgent

All notable changes to the DebugFrameworkAgent package are documented here.

---

## [Unreleased]

---

## [2.5.0] — 2026-02-20

### Added
- **Batch executive summary report** — `report_builder.build_batch_summary_markdown()` and `build_batch_summary_html()`:
  - Groups experiments by `Content` type (Dragon / Linux / PYSVConsole / …)
  - Renders an **Experiment Index** table (all experiments: name, mode, type, content, bucket, check core)
  - Per-group **Common Configuration** table — fields identical across every experiment in the group
  - Per-group **Differences Between Experiments** table — fields that vary, with one column per experiment
  - Content-specific field lists (`_BATCH_COMPARE_FIELDS`) used for Dragon, Linux, PYSVConsole; generic fallback for others
- `exporter.write_batch_report()` — writes batch summary to disk in `md` / `html` formats; returns `{format: Path}` dict
- `constraints.py`: `"Bucket"` added as first entry in `MUST_ASK_FIELDS`; `BUCKET_MUST_ASK = True` constant added
- `skills/experiment_constraints.skill.md` Rule 13 — **Bucket Field**: always ask, never infer from test mode/type/content; examples given (BOOT_FAIL, CFC_MARGIN, STRESS, PPVC_CHAR)
- `skills/experiment_constraints.skill.md` Rule 14 — **Dragon Content Line (Filter)**: blank=run all content; comma-separated values=filter to specific functions; collect per-experiment when batch has mixed filters
- Quick Reference chart in `experiment_constraints.skill.md` updated with Bucket row and Dragon Content filter note

### Changed
- `agents/experiment.agent.md` — Bucket must-ask section added before Check Core step; Dragon content section updated with Content Line filter question and comma-separated syntax explanation
- `skills/experiment_generator.skill.md` — 3 references to `.claude/defaults/experiment_presets.json` updated to `DebugFrameworkAgent/defaults/presets/` (split layout)
- `agents/experiment.agent.md` — preset reference updated from `../defaults/experiment_presets.json` to `../defaults/presets/`
- `.github/copilot-instructions.md` — package directory tree updated to reflect `defaults/presets/` split layout

---

## [2.4.0] — 2026-02-19

### Added
- **Split preset files** — `defaults/experiment_presets.json` replaced by per-product files in `defaults/presets/`:
  - `common.json` (~706 lines) — product-agnostic presets
  - `GNR.json` (~2667 lines)
  - `CWF.json` (~932 lines)
  - `DMR.json` (~2324 lines)
- `preset_loader._load_split_dir()` — internal helper to merge split files into the canonical `{_meta, common, GNR, CWF, DMR}` shape
- `preset_loader.load_all()` now resolves: split directory first → legacy single file fallback; accepts directory path as well as file path
- `docs/CHANGELOG.md` — this file

### Changed
- `preset_loader.load_all()`: default load path is now `defaults/presets/` (split layout); legacy `experiment_presets.json` remains as fallback for tools that reference it directly

---

## [2.3.0] — 2026-02-19

### Added
- `scripts/_core/constraints.py` — single source of truth for all field validation rules:
  - `MESH_MASK_OPTIONS`, `SLICE_CORE_RANGE`, `VVAR_DEFAULTS` per product
  - `SLICE_BLOCKED_FIELDS`, `PSEUDO_CORE_FIELD`, `DISABLE_2_CORE_OPTIONS`, `DISABLE_1_CORE_OPTIONS`
  - `UNIT_CHOP_INFO` (GNR/CWF: AP/SP; DMR: X1/X2/X3/X4)
  - `TEST_NUMBER_PRIORITY` (Loops → Sweep → Shmoo)
  - `MUST_ASK_FIELDS`, `DEFAULT_TEST_TIME = 30`
  - `CONTENT_REQUIRED_FIELDS` (PYSVConsole Scripts File is a hard error)
  - `DRAGON_ASK_FIELDS`, `LINUX_ASK_FIELDS`, `PYSV_ASK_FIELDS`
  - Check functions: `check_slice_restrictions`, `check_mesh_mask`, `check_vvar_mode_consistency`, `check_pseudo_core_configuration`, `check_pysvconsole_requirements`, `check_dragon_content_requirements`, `check_linux_content_requirements`, `check_check_core_set`, `check_batch_check_core`, `check_test_number_ordering`
  - Helpers: `assign_test_numbers`, `expand_dmr_pseudo_mesh`, `get_unit_chop_options`, `get_pseudo_core_field_and_options`, `get_dragon_vvar_note`
- `skills/experiment_constraints.skill.md` — 12-rule agent reference (slice restrictions, VVAR mode consistency, pseudo mesh, unit chop, must-ask fields, DMR full matrix, boot failure detection)
- `tests/test_constraints.py` — 74 new tests covering all constraint functions
- `validate_batch()` in `experiment_builder.py` — batch-level Check Core consistency and test number ordering

### Changed
- `experiment_builder.validate()` now accepts optional `product` parameter; wires all 8 constraint checks
- `scripts/_core/__init__.py` — `constraints` and `report_builder` added to `__all__`
- `agents/orchestrator.agent.md` — updated with Unit Chop intake, Must-Ask table, DMR pseudo mesh matrix, test number priority, boot failure detection
- `agents/experiment.agent.md` — fully rewritten with 7-step constraint-aware workflow; VVAR quick reference table

---

## [2.2.0] — 2026-02-18

### Added
- `scripts/_core/report_builder.py` — Markdown + HTML report generation from experiment dicts
- `scripts/generate_report.py` — CLI entry point for report generation
- `skills/experiment_report.skill.md` — agent skill for report output
- `tests/test_report_builder.py` — report builder tests (35 tests)

---

## [2.1.0] — 2026-02-17

### Added
- **Fuse Wizard skill** — `skills/fuse_wizard.skill.md`, `prompts/fuse_wizard.prompt.md`
- DMR preset wave: 20 new presets (CBB slices, COREHI/CORELO variants, Compute/Cbb mask matrix)
- CWF preset wave: 10 new presets (PPVC extended, CFC/IA sweeps, Linux baseline, Slice baseline)
- GNR preset wave: updated boot cases with mask variants (FirstPass – RowPass3) and TSL breadth/BR/MLC/Sandstone content presets

### Changed
- `defaults/experiment_presets.json` version bumped to `2.0`

---

## [2.0.0] — 2026-02-15

### Added
- Standalone `DebugFrameworkAgent/` package extracted from `.claude/` workspace agent
- `scripts/_core/experiment_builder.py` — `new_blank`, `from_preset`, `validate`, `list_all_fields`
- `scripts/_core/preset_loader.py` — `load_all`, `filter_by_product`, `get_preset`, `merge_custom`, `validate_schema`
- `scripts/_core/exporter.py` — `write_experiment_json`, `write_flow_json`
- `scripts/generate_experiment.py`, `scripts/list_presets.py`, `scripts/validate_experiment.py` CLI scripts
- `agents/orchestrator.agent.md`, `agents/experiment.agent.md`, `agents/flow.agent.md`
- `skills/experiment_generator.skill.md`, `skills/automation_flow_designer.skill.md`
- `defaults/experiment_presets.json` v1.0 — 9 common presets + GNR boot/content/fuse sections
- `tests/` — 169 tests (112 on initial build; grown through waves)
- `docs/SETUP.md`, `docs/WORKFLOWS.md`

### Changed
- Superseded `.claude/agents/debugframework.agent.md` (v1.2); old file marked as deprecated
