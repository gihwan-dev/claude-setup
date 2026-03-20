from __future__ import annotations

import json
from pathlib import Path

from support import REPO_ROOT, RepoTestCase
from sync_skills_index import (
    _collect_skill_entries,
    _render_index,
    _render_manifest,
)


class RepoSurfaceTests(RepoTestCase):
    def test_sync_commands_pass_on_repo(self) -> None:
        commands = (
            ("python3", "scripts/sync_agents.py", "--check"),
            ("python3", "scripts/sync_skills_index.py", "--check"),
        )
        for command in commands:
            completed = self.run_cmd(*command)
            self.assertEqual(
                completed.returncode,
                0,
                msg=f"command failed: {' '.join(command)}\nstdout={completed.stdout}\nstderr={completed.stderr}",
            )

    def test_skills_index_and_manifest_match_skill_frontmatter(self) -> None:
        entries = _collect_skill_entries(REPO_ROOT / "skills")
        expected_index = _render_index(entries)
        expected_manifest = _render_manifest(entries)

        actual_index = (REPO_ROOT / "skills" / "INDEX.md").read_text(encoding="utf-8")
        actual_manifest = (REPO_ROOT / "skills" / "manifest.json").read_text(encoding="utf-8")

        self.assertEqual(actual_index, expected_index)
        self.assertEqual(actual_manifest, expected_manifest)

        manifest_payload = json.loads(actual_manifest)
        names = {entry["name"] for entry in manifest_payload["skills"]}
        self.assertNotIn("_shared", names)
        self.assertNotIn("skills/_shared", actual_index)
        self.assertEqual(manifest_payload["canonical_source_root"], "skills")
        self.assertEqual(manifest_payload["legacy_overlay_root"], ".agents/skills")

    def test_legacy_policy_pipeline_files_are_absent(self) -> None:
        removed_paths = (
            REPO_ROOT / "docs" / "policy",
            REPO_ROOT / "scripts" / "sync_instructions.py",
            REPO_ROOT / "scripts" / "sync-instructions.sh",
            REPO_ROOT / "AGENTS.md",
            REPO_ROOT / "INSTRUCTIONS.md",
            REPO_ROOT / "CLAUDE.md",
            REPO_ROOT / "dist" / "codex" / "AGENTS.md",
        )
        for path in removed_paths:
            self.assertFalse(path.exists(), msg=f"legacy policy pipeline still exists: {path}")

    def test_docs_skills_tasks_and_hooks_have_no_legacy_policy_references(self) -> None:
        banned_snippets = (
            "docs/policy",
            "scripts/sync_instructions.py",
            "dist/codex/AGENTS.md",
            "INSTRUCTIONS.md",
            "AGENTS.md",
            "CLAUDE.md",
        )
        roots = (
            REPO_ROOT / "README.md",
            REPO_ROOT / "CONTRIBUTING.md",
            REPO_ROOT / "skills",
            REPO_ROOT / "tasks",
            REPO_ROOT / "dist",
            REPO_ROOT / "hooks",
        )
        suffixes = {".md", ".json", ".toml", ".sh", ".yaml", ".yml"}

        for root in roots:
            paths = [root] if root.is_file() else sorted(
                path for path in root.rglob("*") if path.is_file() and path.suffix in suffixes
            )
            for path in paths:
                content = path.read_text(encoding="utf-8")
                for snippet in banned_snippets:
                    self.assertNotIn(
                        snippet,
                        content,
                        msg=f"found legacy policy reference `{snippet}` in {path}",
                    )
