from __future__ import annotations

import json
import tempfile
import tomllib
from pathlib import Path

from support import REPO_ROOT, RepoTestCase
from validate_workflow_contracts import validate_repo
from workflow_contract import (
    BUNDLE_AGENT_ORCHESTRATION_MAIN_THREAD_ROLES,
    BUNDLE_AGENT_ORCHESTRATION_REQUIRED_KEYS,
    BUNDLE_AGENT_ORCHESTRATION_STRATEGIES,
    BUNDLE_CSV_FANOUT_ORCHESTRATION_REQUIRED_KEYS,
    BUNDLE_EXECUTION_PLAN_SECTION_ORDER,
    BUNDLE_EXECUTION_PLAN_SLICE_REQUIRED_FIELDS,
    BUNDLE_TASK_YAML_REQUIRED_KEYS,
    GENERATED_SKILL_MANIFEST_NAME,
)


class WorkflowContractTests(RepoTestCase):
    def _write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _seed_minimal_repo(self, repo_root: Path) -> None:
        self._write_text(
            repo_root / "policy" / "workflow.toml",
            "\n".join(
                [
                    "[public_surface]",
                    'long_running = ["design-task", "implement-task", "parallel-workflow"]',
                    "",
                    "[projection]",
                    'required_helper_agent_ids = ["helper"]',
                    "documentation_only_builtins = []",
                    "",
                    "[codex]",
                    'default_reasoning_effort = "high"',
                    "",
                    "[task_documents]",
                    'bundle_task_yaml_required_keys = ["task", "goal", "success_criteria", "major_boundaries", "work_type", "impact_flags", "required_docs", "source_of_truth", "ids", "delivery_strategy", "agent_orchestration", "validation_gate", "current_phase"]',
                    'bundle_agent_orchestration_required_keys = ["strategy", "main_thread_role", "planning_helpers", "execution_roles", "context_policy", "fallback_policy", "review_policy"]',
                    'bundle_agent_orchestration_strategies = ["manager"]',
                    'bundle_agent_orchestration_main_thread_roles = ["synthesize-control-only"]',
                    'bundle_execution_plan_section_order = ["Execution slices", "Verification", "Stop / Replan conditions"]',
                    'bundle_execution_plan_slice_required_fields = ["Change boundary", "Expected files", "Orchestration", "Preflight helpers", "Execution skill", "Implementation owner", "Integration owner", "Validation owner", "Allowed main-thread actions", "Focused validation plan", "Stop / Replan trigger"]',
                    'bundle_csv_fanout_orchestration_required_keys = ["row_unit", "batch_mode", "shared_context_files", "roles", "artifact_root", "change_group_policy"]',
                    'generated_skill_manifest_name = ".generated-skills.json"',
                    "",
                ]
            ),
        )
        self._write_text(
            repo_root / "skills" / "demo" / "SKILL.md",
            "\n".join(
                [
                    "---",
                    "name: demo",
                    'description: "Demo skill"',
                    "---",
                    "",
                    "# Demo",
                    "",
                    "Plain prose is allowed here.",
                    "",
                ]
            ),
        )
        self._write_text(
            repo_root / "skills" / "manifest.json",
            json.dumps({"skills": []}, indent=2) + "\n",
        )

    def test_validate_workflow_contract_command_passes_on_repo(self) -> None:
        completed = self.run_cmd("python3", "scripts/validate_workflow_contracts.py")
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"validate_workflow_contracts failed\nstdout={completed.stdout}\nstderr={completed.stderr}",
        )

    def test_task_document_exports_match_repo_policy(self) -> None:
        policy = tomllib.loads((REPO_ROOT / "policy" / "workflow.toml").read_text(encoding="utf-8"))
        self.assertEqual(
            policy["task_documents"]["generated_skill_manifest_name"],
            GENERATED_SKILL_MANIFEST_NAME,
        )
        self.assertEqual(
            tuple(policy["task_documents"]["bundle_task_yaml_required_keys"]),
            BUNDLE_TASK_YAML_REQUIRED_KEYS,
        )
        self.assertEqual(
            tuple(policy["task_documents"]["bundle_agent_orchestration_required_keys"]),
            BUNDLE_AGENT_ORCHESTRATION_REQUIRED_KEYS,
        )
        self.assertEqual(
            tuple(policy["task_documents"]["bundle_agent_orchestration_strategies"]),
            BUNDLE_AGENT_ORCHESTRATION_STRATEGIES,
        )
        self.assertEqual(
            tuple(policy["task_documents"]["bundle_agent_orchestration_main_thread_roles"]),
            BUNDLE_AGENT_ORCHESTRATION_MAIN_THREAD_ROLES,
        )
        self.assertEqual(
            tuple(policy["task_documents"]["bundle_execution_plan_section_order"]),
            BUNDLE_EXECUTION_PLAN_SECTION_ORDER,
        )
        self.assertEqual(
            tuple(policy["task_documents"]["bundle_execution_plan_slice_required_fields"]),
            BUNDLE_EXECUTION_PLAN_SLICE_REQUIRED_FIELDS,
        )
        self.assertEqual(
            tuple(policy["task_documents"]["bundle_csv_fanout_orchestration_required_keys"]),
            BUNDLE_CSV_FANOUT_ORCHESTRATION_REQUIRED_KEYS,
        )

    def test_validate_repo_reports_invalid_policy_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._seed_minimal_repo(repo_root)
            self._write_text(repo_root / "policy" / "workflow.toml", "[projection\n")

            errors = validate_repo(repo_root, run_sync_checks=False)

        self.assertTrue(
            any("invalid TOML" in error for error in errors),
            msg=f"expected invalid policy error, got: {errors}",
        )

    def test_validate_repo_reports_invalid_skill_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._seed_minimal_repo(repo_root)
            self._write_text(
                repo_root / "skills" / "demo" / "SKILL.md",
                "# Missing frontmatter\n",
            )

            errors = validate_repo(repo_root, run_sync_checks=False)

        self.assertTrue(
            any("skill frontmatter validation failed" in error for error in errors),
            msg=f"expected frontmatter error, got: {errors}",
        )

    def test_validate_repo_reports_invalid_manifest_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._seed_minimal_repo(repo_root)
            self._write_text(repo_root / "skills" / "manifest.json", "{not-json}\n")

            errors = validate_repo(repo_root, run_sync_checks=False)

        self.assertTrue(
            any("invalid JSON" in error for error in errors),
            msg=f"expected JSON error, got: {errors}",
        )

    def test_validate_repo_allows_prose_and_heading_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._seed_minimal_repo(repo_root)
            self._write_text(
                repo_root / "skills" / "demo" / "SKILL.md",
                "\n".join(
                    [
                        "---",
                        "name: demo",
                        'description: "Demo skill"',
                        "---",
                        "",
                        "## Totally Different Heading",
                        "",
                        "Free-form guidance should not fail validation.",
                        "",
                    ]
                ),
            )

            errors = validate_repo(repo_root, run_sync_checks=False)

        self.assertEqual([], errors)

    def test_validate_repo_reports_missing_agent_orchestration_keys_in_fixture_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._seed_minimal_repo(repo_root)
            self._write_text(
                repo_root / "tests" / "fixtures" / "tasks" / "demo-task" / "task.yaml",
                "\n".join(
                    [
                        "task: demo-task",
                        "goal: Demo goal.",
                        "success_criteria:",
                        "  - Ships a bounded change.",
                        "major_boundaries:",
                        "  - Demo boundary",
                        "work_type: feature",
                        "impact_flags:",
                        "  - architecture_significant",
                        "required_docs:",
                        "  - README.md",
                        "source_of_truth:",
                        "  product: README.md",
                        "ids:",
                        "  requirement_prefix: REQ",
                        "delivery_strategy: standard",
                        "agent_orchestration:",
                        "  strategy: manager",
                        "validation_gate: blocking",
                        "current_phase: design",
                        "",
                    ]
                ),
            )
            self._write_text(
                repo_root / "tests" / "fixtures" / "tasks" / "demo-task" / "EXECUTION_PLAN.md",
                "\n".join(
                    [
                        "# Execution slices",
                        "",
                        "## SLICE-1",
                        "",
                        "- Change boundary: Demo",
                        "- Expected files: 1",
                        "- Orchestration: manager lane",
                        "- Preflight helpers: explorer",
                        "- Implementation owner: worker",
                        "- Integration owner: worker",
                        "- Validation owner: verification-worker",
                        "- Allowed main-thread actions: bundle-doc synthesis",
                        "- Focused validation plan: smoke check",
                        "- Stop / Replan trigger: boundary drift",
                        "",
                        "# Verification",
                        "",
                        "- smoke check",
                        "",
                        "# Stop / Replan conditions",
                        "",
                        "- boundary drift",
                        "",
                    ]
                ),
            )

            errors = validate_repo(repo_root, run_sync_checks=False)

        self.assertTrue(
            any("missing agent_orchestration key 'main_thread_role'" in error for error in errors),
            msg=f"expected agent_orchestration error, got: {errors}",
        )

    def test_validate_repo_reports_missing_slice_orchestration_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._seed_minimal_repo(repo_root)
            self._write_text(
                repo_root / "tests" / "fixtures" / "tasks" / "demo-task" / "task.yaml",
                "\n".join(
                    [
                        "task: demo-task",
                        "goal: Demo goal.",
                        "success_criteria:",
                        "  - Ships a bounded change.",
                        "major_boundaries:",
                        "  - Demo boundary",
                        "work_type: feature",
                        "impact_flags:",
                        "  - architecture_significant",
                        "required_docs:",
                        "  - README.md",
                        "source_of_truth:",
                        "  product: README.md",
                        "ids:",
                        "  requirement_prefix: REQ",
                        "delivery_strategy: standard",
                        "agent_orchestration:",
                        "  strategy: manager",
                        "  main_thread_role: synthesize-control-only",
                        "  planning_helpers:",
                        "    - explorer",
                        "  execution_roles:",
                        "    implementation: worker",
                        "  context_policy: bundle-docs-and-structured-results-only",
                        "  fallback_policy: blocked-lane-means-split-replan",
                        "  review_policy: explicit-multi-review",
                        "validation_gate: blocking",
                        "current_phase: design",
                        "",
                    ]
                ),
            )
            self._write_text(
                repo_root / "tests" / "fixtures" / "tasks" / "demo-task" / "EXECUTION_PLAN.md",
                "\n".join(
                    [
                        "# Execution slices",
                        "",
                        "## SLICE-1",
                        "",
                        "- Change boundary: Demo",
                        "- Expected files: 1",
                        "- Focused validation plan: smoke check",
                        "- Stop / Replan trigger: boundary drift",
                        "",
                        "# Verification",
                        "",
                        "- smoke check",
                        "",
                        "# Stop / Replan conditions",
                        "",
                        "- boundary drift",
                        "",
                    ]
                ),
            )

            errors = validate_repo(repo_root, run_sync_checks=False)

        self.assertTrue(
            any("missing slice field 'Orchestration'" in error for error in errors),
            msg=f"expected execution-plan orchestration error, got: {errors}",
        )
