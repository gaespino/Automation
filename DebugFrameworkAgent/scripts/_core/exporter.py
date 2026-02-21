"""
exporter.py — Write experiment and flow artefacts to disk.

All functions accept an output directory / file path as a pathlib.Path
(or str) and return the resolved Path of the written file.
No external dependencies for core formats; PDF requires fpdf2>=2.7 (optional).
"""

from __future__ import annotations
import json
import pathlib
from typing import Any

from . import report_builder as _rb


# --------------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------------

def _ensure_parent(path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _safe_filename(name: str) -> str:
    """Strip characters invalid on Windows/Linux from a proposed filename."""
    return "".join(c for c in name if c.isalnum() or c in "-_. ").strip()


def _resolve_output_dir(
    out_dir:  pathlib.Path | str | None,
    unit_id:  str | None = None,
    product:  str | None = None,
) -> pathlib.Path:
    """
    Resolve the best output directory to use.

    When *out_dir* is provided it is used as-is (resolved absolute).
    When *out_dir* is None the PPV bridge is consulted for a suggestion;
    if PPV is unavailable the default is DebugFrameworkAgent/output/.

    Args:
        out_dir: Caller-supplied directory, or None to auto-resolve.
        unit_id: Optional unit identifier used by the PPV bridge.
        product: Optional product hint (currently unused; reserved for future).

    Returns:
        Resolved absolute Path to the chosen output directory.
    """
    if out_dir is not None:
        return pathlib.Path(out_dir).resolve()

    # Try PPV bridge for a context-aware path suggestion
    try:
        from . import ppv_bridge as _ppv
        bridge = _ppv.get_bridge()
        if bridge.is_available:
            return bridge.get_output_path(unit_id=unit_id)
    except Exception:
        pass

    # Fallback: DebugFrameworkAgent/downloads/
    fallback = pathlib.Path(__file__).parents[2] / "downloads"
    if unit_id:
        fallback = fallback / unit_id
    return fallback.resolve()


def suggest_output_dir(
    unit_id: str | None = None,
    product: str | None = None,
) -> pathlib.Path:
    """
    Return a suggested output directory without writing any files.

    Useful for agent/CLI tools that want to display the expected path
    before committing to it.

    Returns:
        Resolved output directory Path (PPV-aware when available).
    """
    return _resolve_output_dir(None, unit_id=unit_id, product=product)


# --------------------------------------------------------------------------
# Experiment export
# --------------------------------------------------------------------------

def write_experiment_json(
    experiment: dict[str, Any],
    out_dir:    pathlib.Path | str,
    name:       str | None = None,
) -> pathlib.Path:
    """
    Write a single experiment dict to <out_dir>/<name>.json.

    Args:
        experiment: Experiment dict (from experiment_builder).
        out_dir:    Output directory — created if absent.
        name:       File stem; defaults to experiment['Test Name'].
                    Non-filename-safe characters are stripped.
    Returns:
        Resolved path to the written file.
    """
    out_dir = pathlib.Path(out_dir).resolve()

    stem = _safe_filename(name or experiment.get("Test Name", "experiment") or "experiment")
    if not stem:
        stem = "experiment"

    out_path = out_dir / f"{stem}.json"
    _ensure_parent(out_path)

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(experiment, fh, indent=2, ensure_ascii=False)

    return out_path


def write_experiments_batch(
    experiments: list[dict[str, Any]],
    out_dir:     pathlib.Path | str,
    filename:    str = "experiments.json",
) -> pathlib.Path:
    """
    Write a list of experiment dicts as an array to a single JSON file.

    Returns the resolved path of the written file.
    """
    out_dir  = pathlib.Path(out_dir).resolve()
    out_path = out_dir / filename
    _ensure_parent(out_path)

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(experiments, fh, indent=2, ensure_ascii=False)

    return out_path


def write_tpl(
    experiment: dict[str, Any],
    out_dir:    pathlib.Path | str,
    name:       str | None = None,
    product:    str = "GNR",
) -> pathlib.Path:
    """
    Write a .tpl (tab-separated template) version of an experiment.

    The .tpl format is a pair of header/value rows, tab-separated,
    matching the PPV import format.

    Returns the resolved path.
    """
    out_dir = pathlib.Path(out_dir).resolve()
    stem    = _safe_filename(name or experiment.get("Test Name", "experiment") or "experiment")
    if not stem:
        stem = "experiment"

    out_path = out_dir / f"{stem}.tpl"
    _ensure_parent(out_path)

    keys   = list(experiment.keys())
    values = [str(v) if v is not None else "" for v in experiment.values()]

    with open(out_path, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write("\t".join(keys) + "\n")
        fh.write("\t".join(values) + "\n")

    return out_path


# --------------------------------------------------------------------------
# Flow file export (four files)
# --------------------------------------------------------------------------

def write_flow_files(
    structure:  dict[str, Any],
    flows:      dict[str, Any],
    ini_text:   str,
    positions:  dict[str, Any],
    out_dir:    pathlib.Path | str,
) -> dict[str, pathlib.Path]:
    """
    Write all four automation flow artefacts to out_dir.

    Args:
        structure:  TestStructure dict (from flow_builder.build_structure).
        flows:      TestFlows dict    (from flow_builder.build_flows).
        ini_text:   INI string        (from flow_builder.build_ini).
        positions:  Positions dict    (from flow_builder.build_positions).
        out_dir:    Output directory — created if absent.

    Returns:
        Dict mapping artefact name → resolved file path.
    """
    out_dir = pathlib.Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, pathlib.Path] = {}

    def _write_json(data: dict, fname: str) -> pathlib.Path:
        p = out_dir / fname
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        return p

    written["structure"] = _write_json(structure,  "TestStructure.json")
    written["flows"]     = _write_json(flows,      "TestFlows.json")
    written["positions"] = _write_json(positions,  "positions.json")

    ini_path = out_dir / "unit_config.ini"
    with open(ini_path, "w", encoding="utf-8") as fh:
        fh.write(ini_text)
    written["ini"] = ini_path

    return written


# --------------------------------------------------------------------------
# Preset / config round-trip
# --------------------------------------------------------------------------

def write_preset_file(
    presets_data: dict[str, Any],
    out_path:     pathlib.Path | str,
) -> pathlib.Path:
    """Write an experiment_presets.json (full data dict) to disk."""
    out_path = pathlib.Path(out_path).resolve()
    _ensure_parent(out_path)

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(presets_data, fh, indent=2, ensure_ascii=False)

    return out_path


# --------------------------------------------------------------------------
# Report export
# --------------------------------------------------------------------------

def write_report(
    experiment:        dict[str, Any],
    out_dir:           pathlib.Path | str,
    name:              str | None = None,
    formats:           tuple[str, ...] = ("md", "html"),
    validation_result: tuple | None = None,
    product:           str | None = None,
) -> dict[str, pathlib.Path]:
    """
    Write a human-readable experiment configuration report.

    Supported formats:
      "md"   — Markdown (always available, zero deps)
      "html" — Styled HTML (zero deps; open in browser, print to PDF with Ctrl+P)
      "pdf"  — True PDF    (requires:  pip install "fpdf2>=2.7")

    Args:
        experiment:        Experiment dict (from experiment_builder).
        out_dir:           Output directory — created if absent.
        name:              Filename stem; defaults to experiment['Test Name'].
        formats:           Tuple of format strings, e.g. ("md", "html") or ("pdf",) or ("md", "html", "pdf").
        validation_result: Optional (ok, errors, warnings) tuple from experiment_builder.validate().
        product:           Product label shown in the report header (e.g. "GNR").

    Returns:
        Dict mapping format → resolved path, e.g. {"md": Path(...), "html": Path(...)}.
    """
    out_dir = pathlib.Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = _safe_filename(name or experiment.get("Test Name", "experiment") or "experiment")
    if not stem:
        stem = "experiment"

    written: dict[str, pathlib.Path] = {}

    for fmt in formats:
        fmt_lower = fmt.lower()

        if fmt_lower == "md":
            content = _rb.build_markdown(experiment, validation_result=validation_result, product=product)
            p = out_dir / f"{stem}_report.md"
            p.write_text(content, encoding="utf-8")
            written["md"] = p

        elif fmt_lower == "html":
            content = _rb.build_html(experiment, validation_result=validation_result, product=product)
            p = out_dir / f"{stem}_report.html"
            p.write_text(content, encoding="utf-8")
            written["html"] = p

        elif fmt_lower == "pdf":
            p = out_dir / f"{stem}_report.pdf"
            _rb.write_pdf(experiment, p, validation_result=validation_result, product=product)
            written["pdf"] = p

        else:
            raise ValueError(f"Unknown report format: {fmt!r}. Choose from: md, html, pdf")

    return written


def write_batch_report(
    experiments: list[dict[str, Any]],
    out_dir:     pathlib.Path | str,
    name:        str | None = None,
    formats:     tuple[str, ...] = ("md", "html"),
    product:     str | None = None,
    batch_name:  str | None = None,
) -> dict[str, pathlib.Path]:
    """
    Write an executive batch summary report for a list of experiments.

    The report groups experiments by Content type, highlights shared settings,
    and calls out fields that differ between experiments.

    Supported formats:
      "md"   — Markdown (always available, zero deps)
      "html" — Styled HTML (zero deps; open in browser, print to PDF with Ctrl+P)

    Args:
        experiments: List of experiment dicts (from experiment_builder).
        out_dir:     Output directory — created if absent.
        name:        Filename stem; defaults to "batch_summary".
        formats:     Tuple of format strings, e.g. ("md", "html").
        product:     Product label shown in the report header (e.g. "GNR").
        batch_name:  Display title used as the report heading.

    Returns:
        Dict mapping format → resolved path, e.g. {"md": Path(...), "html": Path(...)}.
    """
    out_dir = pathlib.Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = _safe_filename(name or "batch_summary")
    if not stem:
        stem = "batch_summary"

    written: dict[str, pathlib.Path] = {}

    for fmt in formats:
        fmt_lower = fmt.lower()

        if fmt_lower == "md":
            content = _rb.build_batch_summary_markdown(
                experiments, product=product, batch_name=batch_name
            )
            p = out_dir / f"{stem}.md"
            p.write_text(content, encoding="utf-8")
            written["md"] = p

        elif fmt_lower == "html":
            content = _rb.build_batch_summary_html(
                experiments, product=product, batch_name=batch_name
            )
            p = out_dir / f"{stem}.html"
            p.write_text(content, encoding="utf-8")
            written["html"] = p

        else:
            raise ValueError(f"Unknown batch report format: {fmt!r}. Choose from: md, html")

    return written
