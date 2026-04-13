#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1"
REPO_ROOT = Path(__file__).resolve().parents[2]
HYPERAGENT_DIR = Path(__file__).resolve().parent
ANALYZE_SCRIPT = HYPERAGENT_DIR / "analyze_sessions.py"
SCORE_SCRIPT = HYPERAGENT_DIR / "score.py"
GENERATE_SCRIPT = HYPERAGENT_DIR / "generate_variant.py"
ARCHIVE_SCRIPT = HYPERAGENT_DIR / "archive.py"
APPLY_SCRIPT = HYPERAGENT_DIR / "apply.py"


class PipelineError(Exception):
    def __init__(self, step: dict[str, Any]) -> None:
        super().__init__(step.get("error") or step.get("stderr") or step["name"])
        self.step = step


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def default_date_range() -> tuple[str, str]:
    yesterday = date.today() - timedelta(days=1)
    value = yesterday.isoformat()
    return value, value


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid ISO date: {value}") from exc


def parse_json_output(step_name: str, stdout: str) -> dict[str, Any]:
    try:
        output = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise PipelineError(
            {
                "name": step_name,
                "status": "failed",
                "returncode": 0,
                "stdout": stdout,
                "stderr": "",
                "error": f"invalid JSON output: {exc}",
            }
        ) from None
    if not isinstance(output, dict):
        raise PipelineError(
            {
                "name": step_name,
                "status": "failed",
                "returncode": 0,
                "stdout": stdout,
                "stderr": "",
                "error": "JSON output must be an object",
            }
        )
    return output


def run_json_step(
    name: str,
    command: list[str],
    *,
    input_json: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    input_text = json.dumps(input_json, ensure_ascii=False) if input_json is not None else None
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    step = {
        "name": name,
        "status": "success" if result.returncode == 0 else "failed",
        "command": command,
        "returncode": result.returncode,
        "stderr": result.stderr.strip(),
    }
    if result.returncode != 0:
        step["stdout"] = result.stdout.strip()
        step["error"] = step["stderr"] or step["stdout"] or f"{name} failed"
        raise PipelineError(step)

    output = parse_json_output(name, result.stdout)
    step["output_summary"] = summarize_output(name, output)
    if step["stderr"]:
        step["warnings"] = step["stderr"]
    return step, output


def summarize_output(name: str, output: dict[str, Any]) -> dict[str, Any]:
    if name == "analyze":
        return {
            "sessions_analyzed": output.get("sessions_analyzed"),
            "sessions_skipped": output.get("sessions_skipped"),
            "date_range": output.get("date_range"),
        }
    if name == "score":
        diagnostics = output.get("diagnostics") if isinstance(output.get("diagnostics"), dict) else {}
        improvements = output.get("improvements")
        return {
            "scored_entities": diagnostics.get("scored_entities"),
            "improvement_count": len(improvements) if isinstance(improvements, list) else None,
            "baseline_status": output.get("baseline_status", {}).get("state")
            if isinstance(output.get("baseline_status"), dict)
            else None,
        }
    if name == "generate":
        return {
            "candidate_count": output.get("candidate_count"),
            "dry_run": output.get("dry_run"),
            "output_dir": output.get("output_dir"),
        }
    if name == "archive":
        records = output.get("records")
        return {"record_count": len(records) if isinstance(records, list) else None}
    if name == "apply":
        plans = output.get("plans")
        return {"plan_count": len(plans) if isinstance(plans, list) else None}
    return {}


def variants_from_output(output: dict[str, Any]) -> list[dict[str, Any]]:
    variants = output.get("variants")
    if not isinstance(variants, list):
        return []
    return [variant for variant in variants if isinstance(variant, dict)]


def simulate_archive(variants: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    records = []
    for variant in variants:
        records.append(
            {
                "schema_version": SCHEMA_VERSION,
                "event_type": "add",
                "variant_id": variant.get("variant_id"),
                "entity_type": variant.get("entity_type"),
                "entity_id": variant.get("entity_id"),
                "score": variant.get("score"),
                "status": "staged",
                "variant_dir": variant.get("variant_dir"),
                "meta_path": variant.get("meta_file"),
                "source_path": variant.get("source_path"),
                "change_summary": variant.get("suggestion"),
                "git_tag": None,
                "simulated": True,
            }
        )
    output = {
        "schema_version": SCHEMA_VERSION,
        "dry_run": True,
        "archive_path": repo_relative(HYPERAGENT_DIR / "archive.jsonl"),
        "record_count": len(records),
        "records": records,
    }
    step = {
        "name": "archive",
        "status": "success" if variants else "skipped",
        "command": None,
        "returncode": 0,
        "simulated": True,
        "output_summary": summarize_output("archive", output),
    }
    return step, output


def simulate_apply(variants: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    plans = []
    for variant in variants:
        plans.append(
            {
                "schema_version": SCHEMA_VERSION,
                "dry_run": True,
                "variant_id": variant.get("variant_id"),
                "entity_type": variant.get("entity_type"),
                "entity_id": variant.get("entity_id"),
                "variant_dir": variant.get("variant_dir"),
                "payload_path": variant.get("variant_file"),
                "target_path": variant.get("source_path"),
                "action": "apply",
                "status": "planned",
                "simulated": True,
            }
        )
    output = {
        "schema_version": SCHEMA_VERSION,
        "dry_run": True,
        "plan_count": len(plans),
        "plans": plans,
    }
    step = {
        "name": "apply",
        "status": "success" if variants else "skipped",
        "command": None,
        "returncode": 0,
        "simulated": True,
        "output_summary": summarize_output("apply", output),
    }
    return step, output


def archive_variants(variants: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not variants:
        output = {"schema_version": SCHEMA_VERSION, "record_count": 0, "records": []}
        return (
            {
                "name": "archive",
                "status": "skipped",
                "command": None,
                "returncode": 0,
                "output_summary": summarize_output("archive", output),
            },
            output,
        )

    records = []
    commands = []
    for variant in variants:
        variant_dir = variant.get("variant_dir")
        if not isinstance(variant_dir, str) or not variant_dir:
            step = {
                "name": "archive",
                "status": "failed",
                "command": None,
                "returncode": 1,
                "error": "generated variant is missing variant_dir",
            }
            raise PipelineError(step)
        command = [
            sys.executable,
            repo_relative(ARCHIVE_SCRIPT),
            "add",
            "--variant-dir",
            variant_dir,
            "--status",
            "staged",
            "--no-tag",
            "--json",
        ]
        step, output = run_json_step("archive", command)
        commands.append(command)
        records.append(output)

    output = {
        "schema_version": SCHEMA_VERSION,
        "record_count": len(records),
        "records": records,
    }
    step = {
        "name": "archive",
        "status": "success",
        "command": commands,
        "returncode": 0,
        "output_summary": summarize_output("archive", output),
    }
    return step, output


def apply_variants(variants: list[dict[str, Any]], approve: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    if not variants:
        output = {"schema_version": SCHEMA_VERSION, "plan_count": 0, "plans": []}
        return (
            {
                "name": "apply",
                "status": "skipped",
                "command": None,
                "returncode": 0,
                "output_summary": summarize_output("apply", output),
            },
            output,
        )

    plans = []
    commands = []
    for variant in variants:
        variant_dir = variant.get("variant_dir")
        if not isinstance(variant_dir, str) or not variant_dir:
            step = {
                "name": "apply",
                "status": "failed",
                "command": None,
                "returncode": 1,
                "error": "generated variant is missing variant_dir",
            }
            raise PipelineError(step)
        command = [
            sys.executable,
            repo_relative(APPLY_SCRIPT),
            "--variant-dir",
            variant_dir,
            "--json",
        ]
        if approve:
            command.append("--approve")
        step, output = run_json_step("apply", command)
        commands.append(command)
        plans.append(output)

    output = {
        "schema_version": SCHEMA_VERSION,
        "plan_count": len(plans),
        "plans": plans,
    }
    step = {
        "name": "apply",
        "status": "success",
        "command": commands,
        "returncode": 0,
        "output_summary": summarize_output("apply", output),
    }
    return step, output


def build_analyze_command(args: argparse.Namespace, date_range: tuple[str, str]) -> list[str]:
    command = [
        sys.executable,
        repo_relative(ANALYZE_SCRIPT),
        "--date-range",
        date_range[0],
        date_range[1],
        "--json",
        "--min-turns",
        str(args.min_turns),
    ]
    if args.project:
        command.extend(["--project", args.project])
    return command


def run_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now_iso()
    date_range = tuple(args.date_range) if args.date_range else default_date_range()
    steps: list[dict[str, Any]] = []
    outputs: dict[str, Any] = {}

    score_baseline = args.baseline
    with tempfile.TemporaryDirectory(prefix="hyperagent-evolve-") as temp_dir:
        if args.dry_run and score_baseline is None:
            score_baseline = str(Path(temp_dir) / "baseline.json")

        try:
            analyze_step, analysis = run_json_step("analyze", build_analyze_command(args, date_range))
            steps.append(analyze_step)
            outputs["analysis"] = analysis

            score_command = [
                sys.executable,
                repo_relative(SCORE_SCRIPT),
                "--json",
                "--baseline",
                score_baseline or "~/.claude/hyperagent/baseline.json",
            ]
            score_step, scores = run_json_step("score", score_command, input_json=analysis)
            steps.append(score_step)
            outputs["scores"] = scores

            generate_command = [
                sys.executable,
                repo_relative(GENERATE_SCRIPT),
                "--json",
                "--max-variants",
                str(args.max_variants),
            ]
            if args.dry_run:
                generate_command.append("--dry-run")
            generate_step, generated = run_json_step("generate", generate_command, input_json=scores)
            steps.append(generate_step)
            outputs["variants"] = generated

            variants = variants_from_output(generated)
            if args.dry_run:
                archive_step, archive_output = simulate_archive(variants)
                apply_step, apply_output = simulate_apply(variants)
            else:
                archive_step, archive_output = archive_variants(variants)
                apply_step, apply_output = apply_variants(variants, args.approve)
            steps.extend([archive_step, apply_step])
            outputs["archive"] = archive_output
            outputs["apply"] = apply_output

            status = "success"
            error = None
        except PipelineError as exc:
            steps.append(exc.step)
            status = "failed"
            error = exc.step.get("error") or str(exc)

    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "dry_run": args.dry_run,
        "started_at": started_at,
        "finished_at": utc_now_iso(),
        "date_range": {"start": date_range[0], "end": date_range[1]},
        "project": args.project,
        "pipeline_steps": steps,
        "outputs": outputs,
        "error": error,
    }


def print_text_report(result: dict[str, Any]) -> None:
    date_range = result["date_range"]
    print(f"HyperAgent evolve: {result['status']}")
    print(f"Date range: {date_range['start']} to {date_range['end']}")
    for step in result["pipeline_steps"]:
        detail = " (simulated)" if step.get("simulated") else ""
        print(f"- {step['name']}: {step['status']}{detail}")
        if step.get("error"):
            print(f"  error: {step['error']}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the HyperAgent evolution pipeline: analyze -> score -> generate -> archive add -> apply.",
        epilog=(
            "Crontab example (daily 22:00, previous-day default date range):\n"
            "  0 22 * * * cd /Users/choegihwan/Documents/Projects/claude-setup && "
            "/usr/bin/python3 scripts/hyperagent/evolve.py --json "
            ">> ~/.claude/hyperagent/evolve.log 2>&1\n\n"
            "Manual date range example:\n"
            "  python3 scripts/hyperagent/evolve.py --date-range 2026-04-12 2026-04-12 --dry-run --json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true", help="Simulate the full pipeline without archive/apply writes.")
    parser.add_argument("--date-range", nargs=2, metavar=("START", "END"), help="Inclusive ISO date range. Defaults to yesterday.")
    parser.add_argument("--project", help="Project path or slug to pass to analyze_sessions.py.")
    parser.add_argument("--max-variants", type=int, default=3, help="Maximum variants to generate.")
    parser.add_argument("--min-turns", type=int, default=3, help="Minimum user turns passed to analyze_sessions.py.")
    parser.add_argument("--baseline", help="Baseline JSON path for score.py. Dry-run defaults to a temporary baseline.")
    parser.add_argument("--approve", action="store_true", help="Pass --approve to apply.py for Tier 3 variants.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON to stdout.")
    args = parser.parse_args(argv)
    if args.date_range:
        start = parse_iso_date(args.date_range[0])
        end = parse_iso_date(args.date_range[1])
        if start > end:
            parser.error("--date-range START must be <= END")
    if args.max_variants < 1:
        parser.error("--max-variants must be >= 1")
    if args.min_turns < 0:
        parser.error("--min-turns must be >= 0")
    return args


def run(argv: list[str]) -> int:
    args = parse_args(argv)
    result = run_pipeline(args)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text_report(result)
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
