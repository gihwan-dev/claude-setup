from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from install_assets import prune_generated_skills, write_generated_skill_manifest
from workflow_contract import (
    PLAN_SECTION_ORDER,
    REQUIRED_HELPER_AGENT_IDS,
    STATUS_SECTION_ORDER,
    validate_markdown_sections,
)


class WorkflowContractTests(unittest.TestCase):
    def run_cmd(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        return subprocess.run(
            list(args),
            cwd=REPO_ROOT,
            env=merged_env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_contract_commands_pass_on_repo(self) -> None:
        commands = (
            ("python3", "scripts/sync_instructions.py", "--check"),
            ("python3", "scripts/sync_agents.py", "--check"),
            ("python3", "scripts/validate_workflow_contracts.py"),
        )
        for command in commands:
            completed = self.run_cmd(*command)
            self.assertEqual(
                completed.returncode,
                0,
                msg=f"command failed: {' '.join(command)}\nstdout={completed.stdout}\nstderr={completed.stderr}",
            )

    def test_install_assets_dry_run_with_temp_homes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            claude_home = root / ".claude"
            codex_home = root / ".codex"
            (claude_home / "skills").mkdir(parents=True)
            (codex_home / "agents").mkdir(parents=True)

            config_lines = []
            for helper_id in REQUIRED_HELPER_AGENT_IDS:
                config_file = f"agents/{helper_id}.toml"
                config_lines.extend(
                    [
                        f"[agents.{helper_id}]",
                        f'description = "{helper_id}"',
                        f'config_file = "{config_file}"',
                        "",
                    ]
                )
                profile_path = codex_home / config_file
                profile_path.parent.mkdir(parents=True, exist_ok=True)
                profile_path.write_text(
                    "\n".join(
                        [
                            'model = "gpt-5.4"',
                            'model_reasoning_effort = "xhigh"',
                            'sandbox_mode = "read-only"',
                            'developer_instructions = "helper profile"',
                            "",
                        ]
                    ),
                    encoding="utf-8",
                )

            (codex_home / "config.toml").write_text(
                "\n".join(config_lines), encoding="utf-8"
            )

            completed = self.run_cmd(
                "python3",
                "scripts/install_assets.py",
                "--dry-run",
                "--target",
                "all",
                env={
                    "CLAUDE_HOME": str(claude_home),
                    "CODEX_HOME": str(codex_home),
                },
            )
            self.assertEqual(
                completed.returncode,
                0,
                msg=f"install_assets dry-run failed\nstdout={completed.stdout}\nstderr={completed.stderr}",
            )

    def test_install_assets_dry_run_dest_runs_skill_prune_and_manifest_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "skills"
            destination.mkdir(parents=True)

            stale_generated = destination / "milestone-runner"
            stale_generated.mkdir()
            (destination / "my-manual-skill").mkdir()
            write_generated_skill_manifest(
                destination,
                {"design-task", "milestone-runner"},
                dry_run=False,
            )

            completed = self.run_cmd(
                "python3",
                "scripts/install_assets.py",
                "--dry-run",
                "--dest",
                str(destination),
            )
            self.assertEqual(
                completed.returncode,
                0,
                msg=f"install_assets --dest dry-run failed\nstdout={completed.stdout}\nstderr={completed.stderr}",
            )
            self.assertIn(
                f"[dry-run] prune {stale_generated} (stale generated skill)",
                completed.stdout,
            )
            self.assertIn(
                "[dry-run] update skill manifest",
                completed.stdout,
            )

    def test_skill_prune_uses_generated_manifest_scope_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / "skills"
            skills_dir.mkdir(parents=True)

            stale_generated = skills_dir / "milestone-runner"
            stale_generated.mkdir()
            (skills_dir / "design-task").mkdir()
            (skills_dir / "implement-task").mkdir()
            manual_skill = skills_dir / "my-manual-skill"
            manual_skill.mkdir()

            broken_symlink = skills_dir / "milestone"
            broken_symlink.symlink_to(skills_dir / "missing-milestone-target")

            previous_generated = {"milestone-runner", "design-task", "milestone"}
            expected_generated = {"design-task", "implement-task"}
            prune_generated_skills(
                skills_dir=skills_dir,
                expected_generated_names=expected_generated,
                previous_generated_names=previous_generated,
                dry_run=False,
            )
            write_generated_skill_manifest(
                skills_dir,
                expected_generated,
                dry_run=False,
            )

            self.assertFalse(stale_generated.exists())
            self.assertFalse(broken_symlink.exists() or broken_symlink.is_symlink())
            self.assertTrue(manual_skill.exists())
            self.assertTrue((skills_dir / "design-task").exists())
            self.assertTrue((skills_dir / "implement-task").exists())

    def test_skill_prune_removes_legacy_milestone_dir_without_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_dir = Path(tmpdir) / "skills"
            skills_dir.mkdir(parents=True)

            legacy_copied_dir = skills_dir / "milestone-runner"
            legacy_copied_dir.mkdir()
            manual_skill = skills_dir / "my-manual-skill"
            manual_skill.mkdir()

            prune_generated_skills(
                skills_dir=skills_dir,
                expected_generated_names={"design-task", "implement-task"},
                previous_generated_names=set(),
                dry_run=False,
            )

            self.assertFalse(legacy_copied_dir.exists())
            self.assertTrue(manual_skill.exists())

    def test_fixture_plan_and_status_section_order(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-task"
        plan_error = validate_markdown_sections(
            fixture_root / "PLAN.md", PLAN_SECTION_ORDER
        )
        status_error = validate_markdown_sections(
            fixture_root / "STATUS.md", STATUS_SECTION_ORDER
        )
        self.assertIsNone(plan_error, msg=plan_error)
        self.assertIsNone(status_error, msg=status_error)


if __name__ == "__main__":
    unittest.main()
