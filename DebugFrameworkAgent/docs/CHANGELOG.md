# Changelog — DebugFrameworkAgent

All notable changes to the DebugFrameworkAgent package are documented here.

---

## [Unreleased]

---

## [2.7.0] — 2026-02-20

### Added
- **Disabled experiment handling** — experiments with `"Experiment": "Disabled"` are no longer treated as errors anywhere in the validation pipeline:
  - `experiment_builder.validate()` — early-exit path for `Disabled` status: returns `(True, [], ["EXPERIMENT_DISABLED: …"])` and skips all further field checks; empty/`None` still raises an error
  - `experiment_builder.validate_batch()` — now returns a **4th value** `disabled_names` (`list[str]`): the `Test Name` of every disabled experiment found; batch-level ordering and Check Core checks run only on enabled experiments; signature change: `(bool, list, list, list)`
  - `experiment_builder.filter_disabled(experiments)` — new helper that returns the experiment list with all `Disabled` entries removed (case-insensitive)
  - `skills/experiment_constraints.skill.md` **Rule 15** — "Disabled Experiments in a Batch": specifies the agent prompt flow (list disabled names → ask remove / keep / remove specific), re-enable guidance, and a table of when to prompt vs. stay silent
  - `agents/experiment.agent.md` Path C — new step 2 after `load_from_file()`: detect disabled experiments, list them, ask the user; Step 5 updated to cover `validate_batch()` returning non-empty `disabled_names` mid-session
- **`.tpl` file support** throughout the pipeline — the PPV tab-separated template format is now a first-class input alongside `.json`:
  - `experiment_builder._coerce_tpl_value(s)` — converts raw TSV string cells to `None` / `bool` / `int` / `float` / `str`
  - `experiment_builder._load_tpl(path)` — parses header + one-or-more data rows into `list[dict]`
  - `experiment_builder._json_to_experiment_list(raw, source)` — extracted shared helper that normalises all three JSON structures (list / dict-of-dicts / single dict) into `list[dict]`
  - `experiment_builder.load_from_file()` — updated to detect `.tpl` suffix and parse via `_load_tpl`; `.json` path uses the shared helper
  - `experiment_builder.load_batch_from_file(path)` — **new public function** that returns `list[dict]` from any supported format (`.json` all variants, `.tpl` single or multi-row); preferred entry point for report generation, validation, and batch workflows
  - `scripts/generate_report.py` — replaced manual `json.load()` + three-format detection block with `load_batch_from_file()`; accepts `.json` and `.tpl` transparently
  - `scripts/validate_experiment.py` — same replacement; validates `.tpl` files identically to `.json`
- **Scripts File & Post Process authoring rules** — `skills/experiment_generator.skill.md` **Section 11**:
  - Both fields point to `.txt` files executed via `eval`/`exec` — not imported as modules
  - Allowed vs. avoid table (simple imports/assignments OK; class defs, try/except, nested loops not)
  - Escalation rule: complex logic → create `<name>.py`, single import + function call in the `.txt`
  - Suggested agent phrasing for explaining the constraint to users
- **16 new tests** in `tests/test_experiment_builder.py` — `.tpl` loading (single/multi row, coercion of `None`/`bool`/`int`/`float`, empty cell), `load_batch_from_file()` coverage (all JSON structures, `.tpl`, edge cases, copy safety)
- **17 new tests** in `tests/test_experiment_builder.py` — `TestDisabledExperiment` class covering `validate()`, `validate_batch()`, and `filter_disabled()` for all disabled-experiment scenarios

### Changed
- `experiment_builder.validate_batch()` — **breaking signature change**: now returns `(all_valid, all_errors, all_warnings, disabled_names)` instead of `(all_valid, all_errors, all_warnings)`; callers that unpack exactly 3 values must be updated
- `report_builder.build_batch_summary_markdown()` / `build_batch_summary_html()` — **diff table redesign**: replaced the unbounded wide table (one column per experiment) with per-experiment vertical subsections, each showing `Field | Value` for that experiment's differing fields only; HTML version wraps each block in a styled `.diff-card` panel; table width is now fixed regardless of batch size
- `scripts/generate_report.py` — `json` import removed (no longer needed); `EXPERIMENT_JSON` positional arg renamed to `EXPERIMENT_FILE` in help text; docstring updated to document `.tpl` support
- `scripts/validate_experiment.py` — same doc/help update; internal format-detection code removed in favour of `load_batch_from_file()`

### Tests
- Total: **384 passed, 1 skipped** (up from 368 before this release)

---

## [2.6.0] — 2026-02-20

### Added
- **PPV Bridge** (`scripts/_core/ppv_bridge.py`) — optional read-only integration with a local PPV installation:
  - `discover_ppv()` — multi-priority auto-discovery: `PPV_ROOT` env var → explicit override → relative path candidates (repo-layout-aware) → common absolute paths; validated by checking for `configs/*ControlPanelConfig.json`
  - `PPVBridge` class — `load_live_field_config()`, `sync_enums()`, `get_valid_enum()`, `get_field_enable_config()`, `get_field_configs()`, `load_ppv_experiment()`, `get_output_path()`, `validate_enum_value()`
  - Module-level singleton: `get_bridge()` / `reset_bridge()`
  - Fully graceful degradation — all methods return `None` / fallback when PPV is absent
- **Enum validation in `experiment_builder.validate()`** — when PPV bridge is available, `Test Mode`, `Test Type`, `Content`, `Voltage Type`, `Type`, and `Domain` are validated against the live PPV config; soft warnings (not errors) for mismatches
- **`exporter._resolve_output_dir()`** — resolves the best output directory: caller-supplied → PPV bridge suggestion → `DebugFrameworkAgent/output/` fallback
- **`exporter.suggest_output_dir(unit_id, product)`** — public helper for tools/agents to display the expected output path before writing
- **PPV status line in `generate_experiment.py`** — prints `"PPV detected at: …"` or `"PPV not found — running in standalone mode."` on startup
- **GitHub Models client** (`scripts/github_model_client.py`) — stdlib-only (`urllib` + `json`) AI client:
  - `GitHubModelClient(token, model, timeout)` — reads `GITHUB_TOKEN` from env
  - `ask()`, `ask_with_agent_context()`, `translate_to_overrides()`
  - `load_agent_file()`, `load_skill_file()`, `load_prompt_file()` helpers
  - CLI: `--message`, `--agent`, `--skill`, `--prompt-file`, `--translate`, `--product`, `--model`, `--list-models`
- **GitHub Actions workflows** (`.github/workflows/`):
  - `generate-experiments.yml` — manual dispatch: product / preset / mode / unit_id / overrides / report_format inputs; uploads experiment + report artifacts
  - `validate-experiments.yml` — push + PR + manual triggers; validates all output JSONs; posts summary comment on pull requests
  - `list-presets.yml` — manual dispatch: builds preset catalog in JSON or Markdown; uploads as artifact
- **`docs/GITHUB_ACTIONS.md`** — setup guide, workflow reference, client API docs, and troubleshooting table
- **`tests/test_ppv_bridge.py`** — 42 tests covering discovery, availability, config loading, enum sync, field config, experiment loading, output path, enum validation, and singleton management
- **`tests/test_github_integration.py`** — 33 tests covering workflow file structure, client initialisation, ask/translate behaviour, and prompt file loading (all network calls mocked)

### Changed
- `experiment_builder._get_bridge()` — lazy-import helper so bridge is only loaded when validation actually runs (zero cost when PPV absent)
- `generate_experiment.py` — PPV status line printed once at startup before argument processing

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
