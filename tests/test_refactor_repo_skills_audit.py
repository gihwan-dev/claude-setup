from __future__ import annotations

import json
import tempfile
from pathlib import Path

from support import REPO_ROOT, RepoTestCase


AUDIT_SCRIPT = REPO_ROOT / "skills" / "refactor-repo-skills" / "scripts" / "audit_skills.py"


def _write_skill(
    skills_root: Path,
    name: str,
    *,
    description: str,
    body: str,
    with_references: bool = False,
    with_agent: bool = False,
) -> None:
    skill_dir = skills_root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    if with_references:
        (skill_dir / "references").mkdir()
    if with_agent:
        agents_dir = skill_dir / "agents"
        agents_dir.mkdir()
        (agents_dir / "openai.yaml").write_text(
            "interface:\n"
            "  display_name: \"Sample\"\n"
            "  short_description: \"sample\"\n"
            "  default_prompt: \"sample\"\n"
            "policy:\n"
            "  allow_implicit_invocation: false\n",
            encoding="utf-8",
        )
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        "description: >\n"
        f"  {description}\n"
        "---\n\n"
        f"{body}",
        encoding="utf-8",
    )


class RefactorRepoSkillsAuditTests(RepoTestCase):
    def test_audit_ranks_verbose_skill_above_compact_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            skills_root = Path(tmp_dir) / "skills"
            skills_root.mkdir()

            verbose_body = "# Verbose Skill\n\n" + "\n".join(
                [
                    "## Hard Rules",
                    "- fallback 설명을 남긴다.",
                    "- fallback 설명을 남긴다.",
                    "- 반드시 세부 규칙을 아주 길게 적는다.",
                    "- 항상 모든 예시를 본문에 남긴다.",
                ]
                + [f"- fallback 규칙 {index}" for index in range(1, 18)]
                + [f"추가 설명 줄 {index}" for index in range(1, 120)]
            )
            _write_skill(
                skills_root,
                "verbose-skill",
                description=("trigger 중심 설명이 아니라 장문 배경 설명이 길게 이어지는 문장 " * 12).strip(),
                body=verbose_body,
                with_references=False,
                with_agent=False,
            )

            compact_body = "\n".join(
                [
                    "# Compact Skill",
                    "",
                    "## Workflow",
                    "1. Audit the target.",
                    "2. Apply a small change.",
                ]
            )
            _write_skill(
                skills_root,
                "compact-skill",
                description="Short trigger-oriented description.",
                body=compact_body,
                with_references=True,
                with_agent=True,
            )

            completed = self.run_cmd(
                "python3",
                str(AUDIT_SCRIPT),
                "--skills-root",
                str(skills_root),
                "--limit",
                "2",
                "--json",
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["scope_count"], 2)
            self.assertEqual(payload["results"][0]["skill"], "verbose-skill")
            self.assertGreater(payload["results"][0]["score"], payload["results"][1]["score"])
            self.assertFalse(payload["results"][0]["metrics"]["has_references"])
            self.assertFalse(payload["results"][0]["metrics"]["has_agents_openai"])

    def test_audit_supports_skill_name_and_path_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            skills_root = Path(tmp_dir) / "skills"
            skills_root.mkdir()

            _write_skill(
                skills_root,
                "alpha-skill",
                description="Alpha trigger.",
                body="# Alpha\n\n- Always keep it short.\n",
                with_references=False,
                with_agent=False,
            )
            _write_skill(
                skills_root,
                "beta-skill",
                description="Beta trigger.",
                body="# Beta\n\n## Workflow\n1. Use references.\n",
                with_references=True,
                with_agent=True,
            )

            completed = self.run_cmd(
                "python3",
                str(AUDIT_SCRIPT),
                "--skills-root",
                str(skills_root),
                "--skill",
                "alpha-skill",
                "--path",
                str(skills_root / "beta-skill"),
                "--json",
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            payload = json.loads(completed.stdout)
            names = [item["skill"] for item in payload["results"]]
            self.assertEqual(payload["scope_count"], 2)
            self.assertEqual(len(names), 2)
            self.assertGreaterEqual(payload["results"][0]["score"], payload["results"][1]["score"])
            self.assertIn("alpha-skill", names)
            self.assertIn("beta-skill", names)
