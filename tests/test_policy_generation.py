from __future__ import annotations

import json
from pathlib import Path

from support import REPO_ROOT, RepoTestCase
from sync_instructions import (
    build_agents_content,
    build_claude_content,
    build_global_agents_content,
    build_instructions_content,
    load_manifest,
    load_sections,
)
from sync_skills_index import (
    _collect_skill_entries,
    _render_index,
    _render_manifest,
)


class PolicyGenerationTests(RepoTestCase):
    def test_policy_generation_commands_pass_on_repo(self) -> None:
        commands = (
            ("python3", "scripts/sync_instructions.py", "--check"),
            ("python3", "scripts/sync_skills_index.py", "--check"),
        )
        for command in commands:
            completed = self.run_cmd(*command)
            self.assertEqual(
                completed.returncode,
                0,
                msg=f"command failed: {' '.join(command)}\nstdout={completed.stdout}\nstderr={completed.stderr}",
            )

    def test_docs_policy_generates_current_instruction_files(self) -> None:
        policy_root = REPO_ROOT / "docs" / "policy"
        manifest = load_manifest(policy_root)
        self.assertIn("00-core.md", manifest["sections"])
        sections = load_sections(policy_root, list(manifest["sections"]))

        global_section_names = list(manifest.get("global_sections", manifest["sections"]))
        global_sections = load_sections(policy_root, global_section_names)

        expected_instructions = build_instructions_content(str(manifest["title"]), sections)
        expected_agents = build_agents_content(sections)
        expected_claude = build_claude_content()
        expected_global_agents = build_global_agents_content(global_sections)

        self.assertEqual(
            (REPO_ROOT / "INSTRUCTIONS.md").read_text(encoding="utf-8"),
            expected_instructions,
        )
        self.assertEqual(
            (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            expected_agents,
        )
        self.assertEqual(
            (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8"),
            expected_claude,
        )
        self.assertEqual(
            (REPO_ROOT / "dist" / "codex" / "AGENTS.md").read_text(encoding="utf-8"),
            expected_global_agents,
        )

    def test_claude_wrapper_imports_agents_and_contributing(self) -> None:
        claude_path = REPO_ROOT / "CLAUDE.md"
        content = claude_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        self.assertLessEqual(len(lines), 200, msg=f"{claude_path} exceeded 200 lines")

        self.assertIn("@AGENTS.md", content)
        self.assertIn("@CONTRIBUTING.md", content)
        self.assertNotIn("@docs/policy/", content)

    def test_core_policy_section_is_exposed_in_generated_docs(self) -> None:
        agents_content = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        instructions_content = (REPO_ROOT / "INSTRUCTIONS.md").read_text(encoding="utf-8")
        self.assertIn("00-core.md", agents_content)
        self.assertIn("## 핵심 원칙", instructions_content)

    def test_global_agents_excludes_repo_specific_content(self) -> None:
        content = (REPO_ROOT / "dist" / "codex" / "AGENTS.md").read_text(encoding="utf-8")
        # 레포 전용 내용이 없어야 함
        self.assertNotIn("Source Of Truth", content)
        self.assertNotIn("Required Commands", content)
        self.assertNotIn("Detailed Policy Files", content)
        self.assertNotIn("CONTRIBUTING.md", content)
        self.assertNotIn("scripts/sync_instructions", content)
        self.assertNotIn("scripts/sync_agents", content)
        self.assertNotIn("scripts/sync_skills_index", content)
        # repo-only 마커가 붙은 라인은 필터링되어야 함
        self.assertNotIn("repo-only", content)
        # 핵심 정책 내용은 포함되어야 함
        self.assertIn("핵심 원칙", content)
        self.assertIn("에이전트 카탈로그", content)
        self.assertIn("판정 흐름", content)
        self.assertIn("한국어 기본", content)

    def test_global_agents_manifest_controls_included_sections(self) -> None:
        policy_root = REPO_ROOT / "docs" / "policy"
        manifest = load_manifest(policy_root)
        global_sections = list(manifest.get("global_sections", []))
        self.assertTrue(len(global_sections) > 0, "global_sections must be defined")
        # 핵심 정책 섹션은 포함되어야 함
        self.assertIn("00-core.md", global_sections)
        self.assertIn("10-routing.md", global_sections)
        self.assertIn("20-workflows.md", global_sections)

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
