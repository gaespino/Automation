#!/usr/bin/env python3
"""
Deployment Validation & Review Agent
=====================================
Validates Python syntax, runs linting, executes quick tests, and creates
draft GitHub Pull Requests for deployment review.

Can be called from:
  - The Universal Deployment Tool GUI ("Validate & Review..." button)
  - The terminal directly
  - GitHub Copilot Chat via deploy_validator.agent.md

Usage examples:
  python deploy_agent.py --validate --lint --product GNR --target C:/path/to/target
  python deploy_agent.py --validate --lint --test --quick --product CWF
  python deploy_agent.py --pr --pr-title "Deploy GNR 2026-02-23" --draft
  python deploy_agent.py --validate --lint --test --pr --product DMR --target C:/path

Author: GitHub Copilot
Version: 1.0.0
Date: February 23, 2026
"""

import ast
import os
import sys
import json
import subprocess
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Ensure UTF-8 output on Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────

DEVTOOLS_PATH = Path(__file__).parent
WORKSPACE_ROOT = DEVTOOLS_PATH.parent
REPORTS_DIR = DEVTOOLS_PATH

# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────

def _print(msg: str, symbol: str = ""):
    """Print with optional leading symbol."""
    prefix = f"{symbol} " if symbol else ""
    print(f"{prefix}{msg}", flush=True)


def _header(title: str):
    print(f"\n{'=' * 72}", flush=True)
    print(f"  {title}", flush=True)
    print(f"{'=' * 72}", flush=True)


def _section(title: str):
    print(f"\n{'- ' * 30}", flush=True)
    print(f"  {title}", flush=True)
    print(f"{'- ' * 30}", flush=True)


# ──────────────────────────────────────────────────────────────────────────
# Syntax Validation (stdlib only -- ast.parse)
# ──────────────────────────────────────────────────────────────────────────

def validate_syntax(files: List[Path]) -> Dict[str, Optional[str]]:
    """
    Validate Python syntax using ast.parse for each file.

    Returns:
        dict mapping file path -> error string (or None if clean)
    """
    _section("Syntax Validation (ast.parse)")
    results: Dict[str, Optional[str]] = {}
    ok_count = 0
    error_count = 0

    py_files = [f for f in files if Path(f).suffix == '.py' and Path(f).exists()]
    _print(f"Checking {len(py_files)} Python file(s)...")

    for fpath in py_files:
        fpath = Path(fpath)
        try:
            source = fpath.read_text(encoding='utf-8', errors='replace')
            ast.parse(source, filename=str(fpath))
            results[str(fpath)] = None
            ok_count += 1
            _print(f"{fpath.name}", "[OK]")
        except SyntaxError as e:
            err_msg = f"SyntaxError at line {e.lineno}: {e.msg}"
            results[str(fpath)] = err_msg
            error_count += 1
            _print(f"{fpath.name}  ->  {err_msg}", "[FAIL]")
        except Exception as e:
            err_msg = f"Error: {e}"
            results[str(fpath)] = err_msg
            error_count += 1
            _print(f"{fpath.name}  ->  {err_msg}", "[FAIL]")

    _print(f"\nSyntax: {ok_count} OK  |  {error_count} errors")
    return results


# ──────────────────────────────────────────────────────────────────────────
# Linting (flake8 / pyflakes / pylint -- auto-detect first available)
# ──────────────────────────────────────────────────────────────────────────

def _detect_linter() -> Optional[str]:
    """Return the first available linter command, or None."""
    for linter in ('flake8', 'pyflakes', 'pylint'):
        if shutil.which(linter):
            return linter
    # Try via python -m
    for mod in ('flake8', 'pyflakes', 'pylint'):
        try:
            result = subprocess.run(
                [sys.executable, '-m', mod, '--version'],
                capture_output=True, timeout=10
            )
            if result.returncode == 0:
                return f"python -m {mod}"
        except Exception:
            pass
    return None


def run_linting(
    files: List[Path],
    tool: Optional[str] = None
) -> Dict[str, object]:
    """
    Run linting on the given Python files.

    Args:
        files: List of file paths to lint
        tool: Override linter command (auto-detect if None)

    Returns:
        dict with keys: tool, files_checked, issues, raw_output, returncode
    """
    _section("Linting")
    py_files = [str(f) for f in files if Path(f).suffix == '.py' and Path(f).exists()]

    linter = tool or _detect_linter()
    if not linter:
        _print("No linter found. Install flake8, pyflakes, or pylint.", "[WARN]")
        _print("  pip install flake8")
        return {
            'tool': None, 'files_checked': len(py_files),
            'issues': [], 'raw_output': 'No linter available.', 'returncode': -1
        }

    _print(f"Using linter: {linter}")
    _print(f"Checking {len(py_files)} file(s)...")

    if not py_files:
        _print("No Python files to lint.")
        return {'tool': linter, 'files_checked': 0, 'issues': [], 'raw_output': '', 'returncode': 0}

    # Build command
    if linter.startswith('python -m'):
        module = linter.split()[-1]
        cmd = [sys.executable, '-m', module] + py_files
    else:
        cmd = [linter] + py_files

    # Extra flags per tool
    if 'flake8' in linter:
        cmd += ['--max-line-length=120', '--statistics']
    elif 'pylint' in linter:
        cmd += ['--output-format=text', '--score=no', '--disable=C0114,C0115,C0116']

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )
        raw = result.stdout + result.stderr
        print(raw, flush=True)

        issues = []
        for line in raw.splitlines():
            line = line.strip()
            if line and not line.startswith('---') and ':' in line:
                # Try to extract file:line: message patterns
                issues.append(line)

        issue_count = len([l for l in raw.splitlines() if l.strip()])
        if result.returncode == 0:
            _print(f"Linting passed -- {len(py_files)} file(s) clean.", "[OK]")
        else:
            _print(f"Linting found issues ({result.returncode}).", "[WARN]")

        return {
            'tool': linter, 'files_checked': len(py_files),
            'issues': issues, 'raw_output': raw, 'returncode': result.returncode
        }

    except subprocess.TimeoutExpired:
        _print("Linting timed out after 120 seconds.", "[FAIL]")
        return {'tool': linter, 'files_checked': len(py_files), 'issues': [],
                'raw_output': 'Timeout.', 'returncode': -2}
    except Exception as e:
        _print(f"Linting failed: {e}", "[FAIL]")
        return {'tool': linter, 'files_checked': len(py_files), 'issues': [],
                'raw_output': str(e), 'returncode': -3}


# ──────────────────────────────────────────────────────────────────────────
# Quick Test Mode (pytest)
# ──────────────────────────────────────────────────────────────────────────

def quick_test_mode(
    target_dir: Optional[Path] = None,
    pattern: str = "test_*.py",
    quick: bool = True
) -> Dict[str, object]:
    """
    Discover and run tests under target_dir using pytest.

    Args:
        target_dir: Root directory to search for tests (default: workspace root)
        pattern: Test file glob pattern
        quick: If True, use -x (stop on first failure) and -q (quiet)

    Returns:
        dict with keys: tests_found, passed, failed, errors, raw_output, returncode
    """
    _section("Quick Test Mode (pytest)")

    search_dir = target_dir or WORKSPACE_ROOT
    _print(f"Discovering tests in: {search_dir}")

    if not shutil.which('pytest') and not _module_available('pytest'):
        _print("pytest not found. Install with: pip install pytest", "[WARN]")
        return {
            'tests_found': 0, 'passed': 0, 'failed': 0,
            'errors': 0, 'raw_output': 'pytest not available.', 'returncode': -1
        }

    # Collect test files first
    test_files = list(Path(search_dir).rglob(pattern))
    # Also look for *_test.py
    test_files += [f for f in Path(search_dir).rglob("*_test.py") if f not in test_files]
    # Exclude __pycache__ etc.
    test_files = [
        f for f in test_files
        if '__pycache__' not in str(f) and '.venv' not in str(f)
        and 'node_modules' not in str(f)
    ]

    _print(f"Test files found: {len(test_files)}")
    for tf in test_files[:10]:
        _print(f"  {tf.relative_to(search_dir)}")
    if len(test_files) > 10:
        _print(f"  ... and {len(test_files) - 10} more")

    if not test_files:
        _print("No test files found -- skipping test run.")
        return {
            'tests_found': 0, 'passed': 0, 'failed': 0,
            'errors': 0, 'raw_output': 'No tests found.', 'returncode': 0
        }

    cmd = [sys.executable, '-m', 'pytest', str(search_dir)]
    if quick:
        cmd += ['-x', '-q']  # stop on first failure, quiet
    cmd += ['--tb=short', '--no-header', '-rN']

    _print(f"\nRunning: {' '.join(cmd)}\n")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300, cwd=str(search_dir)
        )
        raw = result.stdout + result.stderr
        print(raw, flush=True)

        passed = raw.count(' passed')
        failed = raw.count(' failed')
        errors = raw.count(' error')

        if result.returncode == 0:
            _print("Tests passed.", "[OK]")
        else:
            _print("Tests have failures -- see output above.", "[FAIL]")

        return {
            'tests_found': len(test_files), 'passed': passed,
            'failed': failed, 'errors': errors,
            'raw_output': raw, 'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        _print("Test run timed out (>300s).", "[FAIL]")
        return {
            'tests_found': len(test_files), 'passed': 0, 'failed': 0,
            'errors': 1, 'raw_output': 'Timeout.', 'returncode': -2
        }
    except Exception as e:
        _print(f"Test run failed: {e}", "[FAIL]")
        return {
            'tests_found': len(test_files), 'passed': 0, 'failed': 0,
            'errors': 1, 'raw_output': str(e), 'returncode': -3
        }


def _module_available(module: str) -> bool:
    """Check if a Python module is importable."""
    try:
        result = subprocess.run(
            [sys.executable, '-c', f'import {module}'],
            capture_output=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────────────────
# GitHub PR Creation (gh CLI -- DRAFT ONLY, never auto-merges)
# ──────────────────────────────────────────────────────────────────────────

def create_pr(
    title: str,
    body: str = "",
    branch: Optional[str] = None,
    base: str = "main",
    draft: bool = True
) -> Dict[str, object]:
    """
    Create a GitHub Pull Request using the gh CLI.

    IMPORTANT: This function ONLY creates DRAFT PRs.
    Merging must be done manually by an engineer.

    Args:
        title: PR title
        body: PR description (Markdown)
        branch: Source branch (auto-detected from git if None)
        base: Base branch to merge into
        draft: Always forced to True -- draft PRs only

    Returns:
        dict with keys: url, success, error, command_used
    """
    _section("GitHub Pull Request")

    if not shutil.which('gh'):
        msg = (
            "gh CLI not found. Install from https://cli.github.com/\n"
            "Then run: gh auth login"
        )
        _print(msg, "[FAIL]")
        return {'url': None, 'success': False, 'error': 'gh CLI not installed.', 'command_used': ''}

    # Check auth
    auth_check = subprocess.run(
        ['gh', 'auth', 'status'], capture_output=True, text=True, timeout=15
    )
    if auth_check.returncode != 0:
        _print("gh auth failed -- please run: gh auth login", "[FAIL]")
        return {
            'url': None, 'success': False,
            'error': 'Not authenticated with gh CLI.',
            'command_used': 'gh auth status'
        }

    # Auto-detect current branch if not specified
    if not branch:
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True, text=True, timeout=10, cwd=str(WORKSPACE_ROOT)
            )
            branch = result.stdout.strip() if result.returncode == 0 else "main"
        except Exception:
            branch = "main"

    _print(f"Source branch : {branch}")
    _print(f"Base branch   : {base}")
    _print(f"Title         : {title}")
    _print(f"Draft PR      : True (DRAFT ONLY -- must be reviewed/merged manually)")

    cmd = [
        'gh', 'pr', 'create',
        '--title', title,
        '--base', base,
        '--head', branch,
        '--draft',           # ALWAYS draft -- engineers review before merge
    ]
    if body:
        cmd += ['--body', body]
    else:
        cmd += ['--body', f"Auto-generated draft PR.\n\nCreated by deploy_agent.py on {datetime.now().strftime('%Y-%m-%d %H:%M')}."]

    _print(f"\nRunning: {' '.join(cmd[:6])} ...")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60, cwd=str(WORKSPACE_ROOT)
        )
        output = result.stdout.strip() + result.stderr.strip()

        if result.returncode == 0:
            pr_url = result.stdout.strip()
            _print(f"Draft PR created!", "[OK]")
            _print(f"PR URL: {pr_url}")
            _print("\nNOTE: This is a DRAFT PR. An engineer must review and merge it.")
            return {'url': pr_url, 'success': True, 'error': None, 'command_used': ' '.join(cmd)}
        else:
            _print(f"PR creation failed (exit {result.returncode}):", "[FAIL]")
            _print(output)
            return {
                'url': None, 'success': False,
                'error': output, 'command_used': ' '.join(cmd)
            }
    except subprocess.TimeoutExpired:
        return {'url': None, 'success': False, 'error': 'Timeout.', 'command_used': ' '.join(cmd)}
    except Exception as e:
        return {'url': None, 'success': False, 'error': str(e), 'command_used': ' '.join(cmd)}


# ──────────────────────────────────────────────────────────────────────────
# Collect target files
# ──────────────────────────────────────────────────────────────────────────

def collect_python_files(target_dir: Optional[Path]) -> List[Path]:
    """Recursively collect all .py files under target_dir."""
    if not target_dir or not Path(target_dir).exists():
        return []
    result = []
    ignore = {'__pycache__', '.venv', '.git', '.pytest_cache', 'node_modules'}
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in ignore]
        for f in files:
            if f.endswith('.py'):
                result.append(Path(root) / f)
    return result


# ──────────────────────────────────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────────────────────────────────

def run_full_check(
    product: str,
    target_dir: Optional[Path],
    files: Optional[List[Path]] = None,
    do_validate: bool = True,
    do_lint: bool = True,
    do_test: bool = False,
    quick: bool = True,
) -> Dict[str, object]:
    """
    Run validate + lint + optional tests and return consolidated results.

    Args:
        product: Product name (GNR, CWF, DMR, ...)
        target_dir: Directory containing deployed files
        files: Explicit file list (auto-collected from target_dir if None)
        do_validate: Run syntax validation
        do_lint: Run linting
        do_test: Run quick tests
        quick: Use -x in pytest (stop on first failure)

    Returns:
        Consolidated results dict
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    _header(f"Deployment Check | {product} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    _print(f"Target       : {target_dir or '(not specified)'}")
    _print(f"Validate     : {do_validate}")
    _print(f"Lint         : {do_lint}")
    _print(f"Test         : {do_test} {'(quick mode)' if quick else ''}")

    if files is None:
        files = collect_python_files(target_dir)
    _print(f"Python files : {len(files)}")

    results: Dict[str, object] = {
        'timestamp': timestamp,
        'product': product,
        'target': str(target_dir),
        'files_checked': len(files),
        'syntax': None,
        'lint': None,
        'tests': None,
        'overall_pass': True,
    }

    syntax_errors = 0
    if do_validate:
        results['syntax'] = validate_syntax(files)
        syntax_errors = sum(1 for v in results['syntax'].values() if v is not None)
        if syntax_errors:
            results['overall_pass'] = False

    lint_issues = 0
    if do_lint:
        results['lint'] = run_linting(files)
        if results['lint'].get('returncode', 0) not in (0, 1):
            # returncode 1 from flake8 means issues found (not a failure)
            pass
        lint_issues = len(results['lint'].get('issues', []))

    if do_test:
        results['tests'] = quick_test_mode(target_dir, quick=quick)
        if results['tests'].get('returncode', 0) != 0:
            results['overall_pass'] = False

    _header("SUMMARY")
    if do_validate:
        sym = "[OK]" if syntax_errors == 0 else "[FAIL]"
        _print(f"Syntax errors  : {syntax_errors}", sym)
    if do_lint:
        sym = "[OK]" if lint_issues == 0 else "[WARN]"
        _print(f"Lint issues    : {lint_issues}", sym)
    if do_test and results['tests']:
        t = results['tests']
        sym = "[OK]" if t.get('returncode', 0) == 0 else "[FAIL]"
        _print(f"Tests          : {t.get('passed', 0)} passed / {t.get('failed', 0)} failed", sym)

    overall_sym = "[OK]" if results['overall_pass'] else "[FAIL]"
    _print(f"Overall        : {'PASS' if results['overall_pass'] else 'FAIL'}", overall_sym)

    return results


# ──────────────────────────────────────────────────────────────────────────
# Report generation
# ──────────────────────────────────────────────────────────────────────────

def generate_check_report(results: Dict, output_file: Optional[Path] = None) -> Path:
    """
    Write a JSON check report to DEVTOOLS/check_report_YYYYMMDD_HHMMSS.json.

    Returns the path to the written file.
    """
    timestamp = results.get('timestamp', datetime.now().strftime('%Y%m%d_%H%M%S'))
    if output_file is None:
        output_file = REPORTS_DIR / f"check_report_{timestamp}.json"

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        _print(f"Check report saved: {output_file}", "[OK]")
    except Exception as e:
        _print(f"Could not save check report: {e}", "[WARN]")

    return output_file


# ──────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Deployment Validation & Review Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Validate syntax + lint for GNR deployment:
    python deploy_agent.py --validate --lint --product GNR --target C:/path/to/target

  Full check with quick tests:
    python deploy_agent.py --validate --lint --test --quick --product CWF

  Create a draft PR (requires gh CLI + auth):
    python deploy_agent.py --pr --pr-title "Deploy GNR 2026-02-23" --draft

  Full check + draft PR:
    python deploy_agent.py --validate --lint --product DMR --target C:/path --pr

NOTE: PRs are always created as DRAFT. Engineers must review and merge manually.
        """
    )

    # Validation flags
    parser.add_argument('--validate', action='store_true',
                        help='Run Python syntax validation (ast.parse)')
    parser.add_argument('--lint', action='store_true',
                        help='Run linting (flake8 / pyflakes / pylint, auto-detect)')
    parser.add_argument('--test', action='store_true',
                        help='Run tests with pytest')
    parser.add_argument('--quick', action='store_true',
                        help='Quick test mode: stop on first failure (-x)')

    # Scope
    parser.add_argument('--product', default='UNKNOWN',
                        help='Product name (GNR, CWF, DMR, ...)')
    parser.add_argument('--target', default=None,
                        help='Target directory to validate / collect files from')
    parser.add_argument('--files', nargs='*',
                        help='Explicit list of files to check (overrides --target)')

    # PR flags
    parser.add_argument('--pr', action='store_true',
                        help='Create a draft GitHub PR via gh CLI')
    parser.add_argument('--pr-title', default=None,
                        help='PR title (default: "Deploy <product> <date>")')
    parser.add_argument('--pr-body', default=None,
                        help='PR description body (Markdown)')
    parser.add_argument('--pr-base', default='main',
                        help='Base branch for the PR (default: main)')
    parser.add_argument('--pr-branch', default=None,
                        help='Source branch (auto-detected if not specified)')
    parser.add_argument('--draft', action='store_true',
                        help='Force draft PR. Always true -- provided for compatibility.')

    # Report
    parser.add_argument('--report-only', action='store_true',
                        help='Run checks and save JSON report without deploying')
    parser.add_argument('--report-file', default=None,
                        help='Path for the JSON check report output')
    parser.add_argument('--no-report', action='store_true',
                        help='Skip saving the JSON check report')

    args = parser.parse_args()

    # Default: if no action specified, show help
    if not any([args.validate, args.lint, args.test, args.pr]):
        parser.print_help()
        sys.exit(0)

    target_dir = Path(args.target) if args.target else None
    files: Optional[List[Path]] = None
    if args.files:
        files = [Path(f) for f in args.files if Path(f).exists()]

    # Run checks
    check_results: Optional[Dict] = None
    if args.validate or args.lint or args.test:
        check_results = run_full_check(
            product=args.product,
            target_dir=target_dir,
            files=files,
            do_validate=args.validate,
            do_lint=args.lint,
            do_test=args.test,
            quick=args.quick,
        )

        if not args.no_report:
            report_path = Path(args.report_file) if args.report_file else None
            generate_check_report(check_results, report_path)

    # Create PR
    if args.pr:
        pr_title = args.pr_title or (
            f"Deploy {args.product} -- {datetime.now().strftime('%Y-%m-%d')}"
        )
        pr_body = args.pr_body or (
            f"Deployment validation results for **{args.product}**.\n\n"
            f"- Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"- Target: `{target_dir or 'N/A'}`\n\n"
            f"Generated by `deploy_agent.py`. Review all changes before merging."
        )
        pr_result = create_pr(
            title=pr_title,
            body=pr_body,
            branch=args.pr_branch,
            base=args.pr_base,
            draft=True  # Always draft
        )
        if check_results is not None:
            check_results['pr'] = pr_result

    # Final exit code
    if check_results is not None and not check_results.get('overall_pass', True):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
