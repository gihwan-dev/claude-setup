from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import tomllib
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from support import REPO_ROOT, RepoTestCase
from install_assets import (
    _install_internal_skill_assets,
    _install_skill_sources,
    _iter_internal_skill_asset_dirs,
    _iter_installable_skill_dirs,
    _remove_managed_agent_sections,
    install_path,
    expected_generated_skill_names,
    prune_generated_skills,
    resolve_install_mode,
    run_sync,
    update_codex_config,
    write_generated_skill_manifest,
)


class InstallAssetsTests(RepoTestCase):
    def test_resolve_install_mode_keeps_link_for_primary_checkout(self) -> None:
        outputs = iter(
            [
                f"{REPO_ROOT}\n",
                f"{REPO_ROOT / '.git'}\n",
            ]
        )

        def fake_run(
            command: list[str],
            cwd: Path,
            check: bool = False,
            capture_output: bool = False,
            text: bool = False,
        ) -> subprocess.CompletedProcess[str]:
            self.assertEqual(command[:3], ["git", "rev-parse", "--path-format=absolute"])
            return subprocess.CompletedProcess(command, 0, stdout=next(outputs))

        with patch("install_assets.subprocess.run", side_effect=fake_run):
            with redirect_stdout(io.StringIO()) as stdout:
                mode = resolve_install_mode(REPO_ROOT, "link", dry_run=True)

        self.assertEqual(mode, "link")
        self.assertEqual(stdout.getvalue(), "")

    def test_resolve_install_mode_forces_copy_for_linked_worktree(self) -> None:
        worktree_root = Path("/tmp/claude-setup-worktree")
        outputs = iter(
            [
                f"{worktree_root}\n",
                f"{REPO_ROOT / '.git'}\n",
            ]
        )

        def fake_run(
            command: list[str],
            cwd: Path,
            check: bool = False,
            capture_output: bool = False,
            text: bool = False,
        ) -> subprocess.CompletedProcess[str]:
            self.assertEqual(command[:3], ["git", "rev-parse", "--path-format=absolute"])
            return subprocess.CompletedProcess(command, 0, stdout=next(outputs))

        with patch("install_assets.subprocess.run", side_effect=fake_run):
            with redirect_stdout(io.StringIO()) as stdout:
                mode = resolve_install_mode(REPO_ROOT, "link", dry_run=True)

        self.assertEqual(mode, "copy")
        self.assertIn("linked git worktree detected; forcing install mode: copy", stdout.getvalue())

    def test_resolve_install_mode_keeps_link_when_git_detection_fails(self) -> None:
        def fake_run(
            command: list[str],
            cwd: Path,
            check: bool = False,
            capture_output: bool = False,
            text: bool = False,
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 128, stdout="")

        with patch("install_assets.subprocess.run", side_effect=fake_run):
            with redirect_stdout(io.StringIO()) as stdout:
                mode = resolve_install_mode(REPO_ROOT, "link", dry_run=True)

        self.assertEqual(mode, "link")
        self.assertEqual(stdout.getvalue(), "")

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
            legacy_overlay_root = REPO_ROOT / ".agents" / "skills"
            if legacy_overlay_root.exists():
                self.assertIn("legacy overlay detected:", completed.stdout)
            else:
                self.assertNotIn("legacy overlay detected:", completed.stdout)
            self.assertIn("internal skill asset:", completed.stdout)

    def test_codex_managed_block_contains_required_helpers(self) -> None:
        # managed config를 실제 파일로 사용해 업데이트 결과에 필수 helper가 포함되는지 확인
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codex_home = root / ".codex"
            codex_home.mkdir(parents=True)
            (codex_home / "config.toml").write_text('model = "gpt-5.4"\n', encoding="utf-8")

            managed_path = REPO_ROOT / "dist" / "codex" / "config.managed-agents.toml"
            updated = update_codex_config(codex_home, managed_path, dry_run=True)

            parsed = tomllib.loads(updated)
            agents = parsed.get("agents")
            self.assertIsInstance(agents, dict)
            self.assertIn("worker", agents)
            self.assertIn("verification-worker", agents)

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

    def test_install_assets_dry_run_target_forces_copy_in_linked_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            claude_home = root / ".claude"
            codex_home = root / ".codex"
            (claude_home / "skills").mkdir(parents=True)
            (codex_home / "agents").mkdir(parents=True)
            (codex_home / "config.toml").write_text(
                'model = "gpt-5.4"\n[features]\napps = true\n',
                encoding="utf-8",
            )

            with patch("install_assets.is_linked_git_worktree", return_value=True):
                with patch.object(
                    sys,
                    "argv",
                    ["install_assets.py", "--dry-run", "--target", "all"],
                ):
                    with patch.dict(
                        "os.environ",
                        {
                            "CLAUDE_HOME": str(claude_home),
                            "CODEX_HOME": str(codex_home),
                        },
                        clear=False,
                    ):
                        with redirect_stdout(io.StringIO()) as stdout:
                            import install_assets

                            exit_code = install_assets.main()

        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("linked git worktree detected; forcing install mode: copy", output)
        self.assertIn("[dry-run] copy ", output)
        self.assertNotIn("[dry-run] link ", output)

    def test_install_assets_dry_run_dest_forces_copy_in_linked_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "skills"
            destination.mkdir(parents=True)

            with patch("install_assets.is_linked_git_worktree", return_value=True):
                with patch.object(
                    sys,
                    "argv",
                    ["install_assets.py", "--dry-run", "--dest", str(destination)],
                ):
                    with redirect_stdout(io.StringIO()) as stdout:
                        import install_assets

                        exit_code = install_assets.main()

        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("linked git worktree detected; forcing install mode: copy", output)
        self.assertIn("[dry-run] copy ", output)
        self.assertNotIn("[dry-run] link ", output)

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

    def test_install_path_copy_replaces_broken_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "source-skill"
            destination = root / "dest" / "source-skill"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: source-skill\n---\n", encoding="utf-8")
            destination.parent.mkdir(parents=True)
            destination.symlink_to(root / "missing-skill-target")

            install_path(source, destination, mode="copy", dry_run=False)

            self.assertTrue(destination.exists())
            self.assertFalse(destination.is_symlink())
            self.assertTrue((destination / "SKILL.md").exists())

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
