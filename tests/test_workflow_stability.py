from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from install_assets import (
    _remove_managed_agent_sections,
    prune_generated_skills,
    update_codex_config,
    write_generated_skill_manifest,
)
from sync_agents import _serialize_agent_toml
from workflow_contract import (
    CORE_HELPER_ORCHESTRATION_EXPECTED,
    DISABLED_WRITABLE_PROJECTION_AGENT_IDS,
    DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS,
    EXPECTED_CODEX_REASONING_EFFORT,
    EXPECTED_CODEX_SANDBOX_BY_AGENT,
    FORBIDDEN_CONTRACT_PHRASES,
    PLAN_SECTION_ORDER,
    REQUIRED_CONTRACT_PHRASES,
    REQUIRED_HELPER_AGENT_IDS,
    STATUS_SECTION_ORDER,
    WRITABLE_PROJECTION_AGENT_IDS,
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

    def test_skill_metadata_and_contract_phrases_cover_new_slice_flow(self) -> None:
        targets = (
            "README.md",
            "CONTRIBUTING.md",
            "skills/implement-task/SKILL.md",
            "skills/design-task/SKILL.md",
            "skills/implement-task/agents/openai.yaml",
            "skills/design-task/agents/openai.yaml",
            "agent-registry/project-planner/instructions.md",
            "agent-registry/worker/instructions.md",
            "agent-registry/explorer/instructions.md",
            "agent-registry/verification-worker/instructions.md",
            "agent-registry/architecture-reviewer/instructions.md",
            "agent-registry/code-quality-reviewer/instructions.md",
            "agent-registry/type-specialist/instructions.md",
            "agent-registry/test-engineer/instructions.md",
            "agent-registry/module-structure-gatekeeper/instructions.md",
            "agent-registry/frontend-structure-gatekeeper/instructions.md",
        )

        for relative_path in targets:
            content = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
            for phrase in REQUIRED_CONTRACT_PHRASES[relative_path]:
                self.assertIn(
                    phrase,
                    content,
                    msg=f"missing contract phrase in {relative_path}: {phrase}",
                )

    def test_quality_preflight_paths_and_forbidden_phrases(self) -> None:
        design_skill = (REPO_ROOT / "skills" / "design-task" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`Quality preflight`", design_skill)
        self.assertIn(
            "`promote-architecture`면 `architecture-reviewer` fan-out으로 boundary/public/shared 영향 결정을 먼저 고정한 뒤 slice를 설계한다.",
            design_skill,
        )

        implement_skill = (REPO_ROOT / "skills" / "implement-task" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        for phrase in FORBIDDEN_CONTRACT_PHRASES["skills/implement-task/SKILL.md"]:
            self.assertNotIn(
                phrase,
                implement_skill,
                msg=f"forbidden phrase still present in implement-task skill: {phrase}",
            )

        implement_prompt = (
            REPO_ROOT / "skills" / "implement-task" / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")
        for phrase in FORBIDDEN_CONTRACT_PHRASES["skills/implement-task/agents/openai.yaml"]:
            self.assertNotIn(
                phrase,
                implement_prompt,
                msg=f"forbidden phrase still present in implement-task prompt: {phrase}",
            )

        reviewer_targets = (
            "agent-registry/code-quality-reviewer/instructions.md",
            "agent-registry/architecture-reviewer/instructions.md",
            "agent-registry/test-engineer/instructions.md",
        )
        for relative_path in reviewer_targets:
            content = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn(
                "`품질판정: keep-local | promote-refactor | promote-architecture`",
                content,
                msg=f"missing quality verdict phrase in {relative_path}",
            )

    def test_core_helper_orchestration_mapping_contract(self) -> None:
        for agent_id, expected in CORE_HELPER_ORCHESTRATION_EXPECTED.items():
            path = REPO_ROOT / "agent-registry" / agent_id / "agent.toml"
            payload = tomllib.loads(path.read_text(encoding="utf-8"))
            orchestration = payload.get("orchestration")
            self.assertIsInstance(orchestration, dict, msg=f"missing [orchestration] in {path}")
            for key, expected_value in expected.items():
                self.assertEqual(
                    orchestration.get(key),
                    expected_value,
                    msg=f"unexpected orchestration mapping {agent_id}.{key}",
                )

    def test_generated_managed_config_contains_required_helpers(self) -> None:
        managed_path = REPO_ROOT / "dist" / "codex" / "config.managed-agents.toml"
        payload = tomllib.loads(managed_path.read_text(encoding="utf-8"))
        agents = payload.get("agents")
        self.assertIsInstance(agents, dict)

        for agent_id in REQUIRED_HELPER_AGENT_IDS:
            entry = agents.get(agent_id)
            self.assertIsInstance(entry, dict, msg=f"missing generated helper {agent_id}")
            config_file = entry.get("config_file")
            self.assertIsInstance(config_file, str, msg=f"missing config_file for {agent_id}")
            profile_path = REPO_ROOT / "dist" / "codex" / config_file
            self.assertTrue(profile_path.exists(), msg=f"missing generated helper profile {profile_path}")

    def test_projected_agents_do_not_expose_writable_roles(self) -> None:
        for path in sorted((REPO_ROOT / "agent-registry").glob("*/agent.toml")):
            payload = tomllib.loads(path.read_text(encoding="utf-8"))
            agent_id = payload.get("id")
            role = payload.get("role")
            projection = payload.get("projection")
            self.assertIsInstance(agent_id, str, msg=f"missing id in {path}")
            self.assertIsInstance(role, str, msg=f"missing role in {path}")
            self.assertIsInstance(projection, dict, msg=f"missing projection in {path}")
            if projection.get("repo") is not True and projection.get("codex") is not True:
                continue
            if agent_id in WRITABLE_PROJECTION_AGENT_IDS:
                self.assertEqual(role, "implementer", msg=f"worker role drifted: {path}")
                continue
            self.assertNotIn(role, {"implementer", "orchestrator"}, msg=f"projected writable role is not allowed: {path}")

    def test_generated_managed_agent_profiles_are_read_only(self) -> None:
        managed_path = REPO_ROOT / "dist" / "codex" / "config.managed-agents.toml"
        payload = tomllib.loads(managed_path.read_text(encoding="utf-8"))
        agents = payload.get("agents")
        self.assertIsInstance(agents, dict)

        for agent_id, entry in agents.items():
            self.assertIsInstance(entry, dict, msg=f"invalid agent entry for {agent_id}")
            config_file = entry.get("config_file")
            self.assertIsInstance(config_file, str, msg=f"missing config_file for {agent_id}")
            profile = tomllib.loads((REPO_ROOT / "dist" / "codex" / config_file).read_text(encoding="utf-8"))
            expected_sandbox = EXPECTED_CODEX_SANDBOX_BY_AGENT.get(agent_id, "read-only")
            self.assertEqual(
                profile.get("sandbox_mode"),
                expected_sandbox,
                msg=f"projected agent sandbox mismatch: {agent_id}",
            )
            self.assertEqual(
                profile.get("model_reasoning_effort"),
                EXPECTED_CODEX_REASONING_EFFORT,
                msg=f"projected agent reasoning effort drifted: {agent_id}",
            )

    def test_disabled_specialized_writers_remain_unprojected(self) -> None:
        for agent_id in DISABLED_WRITABLE_PROJECTION_AGENT_IDS:
            payload = tomllib.loads(
                (REPO_ROOT / "agent-registry" / agent_id / "agent.toml").read_text(encoding="utf-8")
            )
            projection = payload.get("projection")
            self.assertIsInstance(projection, dict, msg=f"missing projection for {agent_id}")
            self.assertFalse(projection.get("repo"), msg=f"repo projection unexpectedly enabled: {agent_id}")
            self.assertFalse(projection.get("codex"), msg=f"codex projection unexpectedly enabled: {agent_id}")

    def test_documentation_only_builtins_are_not_repo_managed(self) -> None:
        managed_payload = tomllib.loads(
            (REPO_ROOT / "dist" / "codex" / "config.managed-agents.toml").read_text(encoding="utf-8")
        )
        managed_agents = managed_payload.get("agents")
        self.assertIsInstance(managed_agents, dict)

        for agent_id in DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS:
            self.assertFalse(
                (REPO_ROOT / "agent-registry" / agent_id).exists(),
                msg=f"documentation-only built-in unexpectedly has registry entry: {agent_id}",
            )
            self.assertNotIn(agent_id, managed_agents, msg=f"documentation-only built-in unexpectedly managed: {agent_id}")

    def test_sync_agents_serialize_roundtrips_orchestration_section(self) -> None:
        serialized = _serialize_agent_toml(
            agent_id="sample-helper",
            role="reviewer",
            description="sample",
            source="codex-builtin",
            repo_projection=False,
            codex_projection=False,
            repo_model=None,
            repo_tools=[],
            codex_agent_key=None,
            codex_config_file=None,
            codex_model=None,
            codex_reasoning_effort=None,
            codex_sandbox_mode=None,
            orchestration={
                "blocking_class": "advisory",
                "result_contract": "preliminary-or-final",
                "close_protocol": "interrupt-drain-ack-close",
                "late_result_policy": "merge-if-relevant",
            },
        )
        payload = tomllib.loads(serialized)
        orchestration = payload.get("orchestration")
        self.assertIsInstance(orchestration, dict)
        self.assertEqual(orchestration.get("blocking_class"), "advisory")
        self.assertEqual(orchestration.get("result_contract"), "preliminary-or-final")
        self.assertEqual(orchestration.get("close_protocol"), "interrupt-drain-ack-close")
        self.assertEqual(orchestration.get("late_result_policy"), "merge-if-relevant")


if __name__ == "__main__":
    unittest.main()
