from __future__ import annotations

import io
import json
import subprocess
import tempfile
import tomllib
from pathlib import Path
from unittest.mock import patch

from support import REPO_ROOT, RepoTestCase
from install_assets import (
    _install_internal_skill_assets,
    _install_skill_sources,
    _iter_internal_skill_asset_dirs,
    _iter_installable_skill_dirs,
    _remove_managed_agent_sections,
    expected_generated_skill_names,
    prune_generated_skills,
    run_sync,
    update_codex_config,
    write_generated_skill_manifest,
)


class InstallAssetsTests(RepoTestCase):
    def test_repo_shared_assets_are_internal_only(self) -> None:
        manifest_payload = json.loads(
            (REPO_ROOT / "skills" / "manifest.json").read_text(encoding="utf-8")
        )
        manifest_names = {entry["name"] for entry in manifest_payload["skills"]}
        generated_names = expected_generated_skill_names(
            REPO_ROOT / "skills",
            REPO_ROOT / ".agents" / "skills",
        )
        internal_asset_names = {
            path.name for path in _iter_internal_skill_asset_dirs(REPO_ROOT / "skills")
        }

        self.assertIn("_shared", internal_asset_names)
        self.assertNotIn("_shared", manifest_names)
        self.assertNotIn("_shared", generated_names)

    def test_install_assets_dry_run_with_temp_homes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            claude_home = root / ".claude"
            codex_home = root / ".codex"
            (claude_home / "skills").mkdir(parents=True)
            (codex_home / "agents").mkdir(parents=True)
            (codex_home / "config.toml").write_text(
                '\n'.join(
                    [
                        'model = "gpt-5.4"',
                        "",
                        "[features]",
                        "apps = true",
                        "",
                    ]
                ),
                encoding="utf-8",
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
            self.assertIn("skill canonical source:", completed.stdout)
            self.assertIn("legacy overlay detected:", completed.stdout)
            self.assertIn("internal skill asset:", completed.stdout)

    def test_run_sync_includes_sync_skills_index(self) -> None:
        calls: list[list[str]] = []

        def fake_run(command: list[str], cwd: Path, check: bool = False) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            return subprocess.CompletedProcess(command, 0)

        with patch("install_assets.subprocess.run", side_effect=fake_run):
            run_sync(REPO_ROOT, dry_run=True)

        flattened = [" ".join(call) for call in calls]
        self.assertTrue(any("scripts/sync_instructions.py --check" in call for call in flattened))
        self.assertTrue(any("scripts/sync_agents.py --check" in call for call in flattened))
        self.assertTrue(any("scripts/sync_skills_index.py --check" in call for call in flattened))

    def test_remove_managed_agent_sections_preserves_unmanaged_agents(self) -> None:
        sample = "\n".join(
            [
                'model = "gpt-5.4"',
                "",
                "[agents.explorer]",
                'config_file = "agents/explorer.toml"',
                "",
                "[agents.explorer.meta]",
                'kind = "legacy"',
                "",
                "[agents.code-reviewer]",
                'config_file = "agents/code-reviewer.toml"',
                "",
                "# BEGIN MANAGED AGENTS (claude-setup)",
                '[agents.explorer]',
                'config_file = "agents/explorer.toml"',
                "# END MANAGED AGENTS (claude-setup)",
                "",
                "[features]",
                "apps = true",
                "",
            ]
        )
        updated = _remove_managed_agent_sections(sample, {"explorer"})

        self.assertNotIn("[agents.explorer.meta]", updated)
        self.assertIn("[agents.code-reviewer]", updated)
        self.assertIn("# BEGIN MANAGED AGENTS (claude-setup)", updated)
        self.assertIn("# END MANAGED AGENTS (claude-setup)", updated)
        self.assertIn("[features]", updated)

    def test_update_codex_config_removes_duplicate_non_helper_agent_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codex_home = root / ".codex"
            codex_home.mkdir(parents=True)
            managed_path = root / "config.managed-agents.toml"
            managed_path.write_text(
                "\n".join(
                    [
                        "[agents.code-reviewer]",
                        'description = "repo-managed"',
                        'config_file = "agents/code-reviewer.toml"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (codex_home / "config.toml").write_text(
                "\n".join(
                    [
                        'model = "gpt-5.4"',
                        "",
                        "[agents.code-reviewer]",
                        'description = "manual"',
                        'config_file = "agents/code-reviewer.toml"',
                        "",
                        "[features]",
                        "apps = true",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            updated = update_codex_config(codex_home, managed_path, dry_run=True)
            parsed = tomllib.loads(updated)
            agents = parsed.get("agents")
            self.assertIsInstance(agents, dict)
            self.assertIn("code-reviewer", agents)
            self.assertEqual(updated.count("[agents.code-reviewer]"), 1)
            self.assertIn("[features]", updated)

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
            self.assertIn("[dry-run] update skill manifest", completed.stdout)

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

    def test_install_skill_sources_applies_canonical_and_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            canonical = root / "skills"
            overlay = root / ".agents" / "skills"
            destination = root / "dest"

            (canonical / "alpha").mkdir(parents=True)
            (canonical / "alpha" / "SKILL.md").write_text("---\nname: alpha\n---\n", encoding="utf-8")
            (canonical / "_shared").mkdir(parents=True)
            (canonical / "_shared" / "storybook-screenshot-guidelines.md").write_text("shared", encoding="utf-8")
            (overlay / "beta").mkdir(parents=True)
            (overlay / "beta" / "SKILL.md").write_text("---\nname: beta\n---\n", encoding="utf-8")

            _install_skill_sources(
                canonical_skills_src=canonical,
                legacy_overlay_src=overlay,
                destination=destination,
                mode="copy",
                dry_run=False,
            )

            self.assertTrue((destination / "alpha" / "SKILL.md").exists())
            self.assertTrue((destination / "beta" / "SKILL.md").exists())
            self.assertFalse((destination / "_shared").exists())

            _install_internal_skill_assets(
                canonical_skills_src=canonical,
                destination=destination,
                mode="copy",
                dry_run=False,
            )

            self.assertTrue((destination / "_shared" / "storybook-screenshot-guidelines.md").exists())

    def test_skill_filters_use_skill_md_instead_of_directory_existence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            canonical = root / "skills"
            overlay = root / ".agents" / "skills"

            (canonical / "alpha").mkdir(parents=True)
            (canonical / "alpha" / "SKILL.md").write_text("---\nname: alpha\n---\n", encoding="utf-8")
            (canonical / "_shared").mkdir(parents=True)
            (canonical / "_shared" / "README.md").write_text("shared", encoding="utf-8")
            (canonical / "notes").mkdir(parents=True)
            (overlay / "beta").mkdir(parents=True)
            (overlay / "beta" / "SKILL.md").write_text("---\nname: beta\n---\n", encoding="utf-8")

            installable_names = [path.name for path in _iter_installable_skill_dirs(canonical)]
            expected_names = expected_generated_skill_names(canonical, overlay)

            self.assertEqual(installable_names, ["alpha"])
            self.assertEqual(expected_names, {"alpha", "beta"})
            self.assertNotIn("_shared", expected_names)
            self.assertNotIn("notes", expected_names)
