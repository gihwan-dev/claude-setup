from __future__ import annotations

import json
import tempfile
from pathlib import Path

from support import REPO_ROOT, RepoTestCase
from validate_workflow_contracts import validate_repo
from workflow_contract import GENERATED_SKILL_MANIFEST_NAME


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
                    'long_running = ["plan", "build"]',
                    "",
                    "[projection]",
                    'required_helper_agent_ids = ["helper"]',
                    "documentation_only_builtins = []",
                    "",
                    "[codex]",
                    'default_reasoning_effort = "high"',
                    "",
                    "[manifest]",
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

    def test_manifest_name_export_matches_repo_policy(self) -> None:
        import tomllib

        policy = tomllib.loads((REPO_ROOT / "policy" / "workflow.toml").read_text(encoding="utf-8"))
        self.assertEqual(
            policy["manifest"]["generated_skill_manifest_name"],
            GENERATED_SKILL_MANIFEST_NAME,
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
