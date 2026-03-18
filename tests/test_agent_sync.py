from __future__ import annotations

import io
import os
import sys
import tempfile
import tomllib
from pathlib import Path
from unittest.mock import patch

from support import REPO_ROOT, RepoTestCase
import bootstrap_registry
import sync_agents
from workflow_contract import (
    REQUIRED_HELPER_AGENT_IDS,
    SLICE_BUDGET_ENFORCEMENT,
    SLICE_BUDGET_MAX_NET_LOC,
    SLICE_BUDGET_MAX_REPO_FILES,
)


class AgentSyncTests(RepoTestCase):
    def _write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _seed_minimal_bootstrap_repo(self, repo_root: Path) -> None:
        self._write_text(
            repo_root / "policy" / "workflow.toml",
            (REPO_ROOT / "policy" / "workflow.toml").read_text(encoding="utf-8"),
        )
        self._write_text(
            repo_root / "agents" / "custom-reviewer.md",
            "\n".join(
                [
                    "---",
                    "name: custom-reviewer",
                    "role: reviewer",
                    'description: "Custom reviewer"',
                    "tools: Read, Grep, Glob",
                    "model: sonnet",
                    "---",
                    "",
                    "custom reviewer instructions",
                    "",
                ]
            ),
        )

    def test_sync_agents_check_command_passes_on_repo(self) -> None:
        completed = self.run_cmd("python3", "scripts/sync_agents.py", "--check")
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"sync_agents --check failed\nstdout={completed.stdout}\nstderr={completed.stderr}",
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

    def test_slice_budget_policy_defaults(self) -> None:
        policy = tomllib.loads((REPO_ROOT / "policy" / "workflow.toml").read_text(encoding="utf-8"))
        slice_budget = policy.get("slice_budget")
        self.assertIsInstance(slice_budget, dict)
        self.assertEqual(slice_budget.get("max_repo_files"), SLICE_BUDGET_MAX_REPO_FILES)
        self.assertEqual(slice_budget.get("max_net_loc"), SLICE_BUDGET_MAX_NET_LOC)
        self.assertEqual(slice_budget.get("enforcement"), SLICE_BUDGET_ENFORCEMENT)

    def test_browser_explorer_is_projected_with_danger_full_access_profile(self) -> None:
        self.assertIn("browser-explorer", REQUIRED_HELPER_AGENT_IDS)

        managed_path = REPO_ROOT / "dist" / "codex" / "config.managed-agents.toml"
        payload = tomllib.loads(managed_path.read_text(encoding="utf-8"))
        agents = payload.get("agents")
        self.assertIsInstance(agents, dict)

        browser_entry = agents.get("browser-explorer")
        self.assertIsInstance(browser_entry, dict)
        self.assertEqual(
            browser_entry.get("config_file"),
            "agents/browser-explorer.toml",
        )

        profile_path = REPO_ROOT / "dist" / "codex" / "agents" / "browser-explorer.toml"
        self.assertTrue(profile_path.exists(), msg=f"missing browser-explorer profile {profile_path}")

        profile = tomllib.loads(profile_path.read_text(encoding="utf-8"))
        self.assertEqual(profile.get("sandbox_mode"), "danger-full-access")

    def test_writer_agent_is_projected_with_danger_full_access_profile(self) -> None:
        self.assertIn("writer", REQUIRED_HELPER_AGENT_IDS)

        managed_path = REPO_ROOT / "dist" / "codex" / "config.managed-agents.toml"
        payload = tomllib.loads(managed_path.read_text(encoding="utf-8"))
        agents = payload.get("agents")
        self.assertIsInstance(agents, dict)

        writer_entry = agents.get("writer")
        self.assertIsInstance(writer_entry, dict)
        self.assertEqual(
            writer_entry.get("config_file"),
            "agents/writer.toml",
        )

        profile_path = REPO_ROOT / "dist" / "codex" / "agents" / "writer.toml"
        self.assertTrue(profile_path.exists(), msg=f"missing writer profile {profile_path}")

        profile = tomllib.loads(profile_path.read_text(encoding="utf-8"))
        self.assertEqual(profile.get("sandbox_mode"), "danger-full-access")
        self.assertEqual(profile.get("model_reasoning_effort"), "high")

    def test_projected_agents_do_not_expose_extra_writable_roles(self) -> None:
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
            self.assertNotIn(
                role,
                {"implementer", "orchestrator"},
                msg=f"projected writable role is not allowed: {path}",
            )

    def test_deprecated_bootstrap_shim_delegates_to_bootstrap_registry(self) -> None:
        sample_entries = [
            sync_agents.AgentEntry(
                agent_id="sample-helper",
                role="reviewer",
                description="sample",
                source="registry",
                repo_projection=False,
                codex_projection=False,
                repo_model=None,
                repo_tools=[],
                codex_agent_key=None,
                codex_config_file=None,
                codex_model=None,
                codex_reasoning_effort=None,
                codex_sandbox_mode=None,
                instructions="sample\n",
            )
        ]

        with (
            patch.object(sys, "argv", ["sync_agents.py", "--bootstrap-from-current"]),
            patch.object(bootstrap_registry, "bootstrap_from_current") as bootstrap_mock,
            patch.object(sync_agents, "_read_agent_entries", return_value=sample_entries),
            patch.object(sync_agents, "_validate_entries"),
            patch.object(sync_agents, "_sync_from_registry", return_value=0) as sync_mock,
            patch("sys.stderr", new_callable=io.StringIO) as fake_stderr,
        ):
            exit_code = sync_agents.main()

        self.assertEqual(exit_code, 0)
        bootstrap_mock.assert_called_once()
        sync_mock.assert_called_once()
        self.assertIn("deprecated", fake_stderr.getvalue())

    def test_bootstrap_check_combo_is_rejected_without_mutation(self) -> None:
        with (
            patch.object(sys, "argv", ["sync_agents.py", "--bootstrap-from-current", "--check"]),
            patch.object(bootstrap_registry, "bootstrap_from_current") as bootstrap_mock,
            patch.object(sync_agents, "_read_agent_entries") as read_entries_mock,
            patch.object(sync_agents, "_sync_from_registry") as sync_mock,
            patch("sys.stderr", new_callable=io.StringIO) as fake_stderr,
        ):
            exit_code = sync_agents.main()

        self.assertEqual(exit_code, 2)
        bootstrap_mock.assert_not_called()
        read_entries_mock.assert_not_called()
        sync_mock.assert_not_called()
        self.assertIn("cannot be combined", fake_stderr.getvalue())

    def test_bootstrap_registry_roundtrip_keeps_required_helpers_and_ignores_optional_worker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repo_root = root / "repo"
            registry_root = root / "registry"
            codex_home = root / ".codex"
            self._seed_minimal_bootstrap_repo(repo_root)
            self._write_text(
                codex_home / "config.toml",
                "\n".join(
                    [
                        'model = "gpt-5.4"',
                        "",
                        "[agents.worker]",
                        'description = "Builtin worker"',
                        'config_file = "worker.toml"',
                        "",
                        "[agents.verification-worker]",
                        'description = "Builtin verification-worker"',
                        'config_file = "verification-worker.toml"',
                        "",
                    ]
                ),
            )
            self._write_text(
                codex_home / "worker.toml",
                "\n".join(
                    [
                        'model = "gpt-5.4"',
                        "",
                        'developer_instructions = """',
                        "worker instructions",
                        '"""',
                        "",
                    ]
                ),
            )
            self._write_text(
                codex_home / "verification-worker.toml",
                "\n".join(
                    [
                        'model = "gpt-5.4"',
                        "",
                        'developer_instructions = """',
                        "verification-worker instructions",
                        '"""',
                        "",
                    ]
                ),
            )
            policy = tomllib.loads(
                (repo_root / "policy" / "workflow.toml").read_text(encoding="utf-8")
            )

            with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}, clear=False):
                bootstrap_registry.bootstrap_from_current(repo_root, registry_root)
                entries = sync_agents._read_agent_entries(registry_root)
                sync_agents._validate_entries(entries)
                exit_code = sync_agents._sync_from_registry(repo_root, entries, check=False)

            self.assertEqual(exit_code, 0)
            self.assertFalse((registry_root / "worker").exists())

            helper_payload = tomllib.loads(
                (registry_root / "verification-worker" / "agent.toml").read_text(encoding="utf-8")
            )
            projection = helper_payload.get("projection")
            codex = helper_payload.get("codex")

            self.assertIsInstance(projection, dict)
            self.assertIsInstance(codex, dict)
            self.assertTrue(projection.get("repo"))
            self.assertTrue(projection.get("codex"))
            effort_overrides = policy["codex"].get("reasoning_effort_overrides", {})
            expected_effort = effort_overrides.get(
                "verification-worker",
                policy["codex"]["default_reasoning_effort"],
            )
            self.assertEqual(
                codex.get("reasoning_effort"),
                expected_effort,
            )
            self.assertEqual(codex.get("sandbox_mode"), "read-only")

            generated_profile = tomllib.loads(
                (repo_root / "dist" / "codex" / "agents" / "verification-worker.toml").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                generated_profile.get("model_reasoning_effort"),
                expected_effort,
            )
            self.assertEqual(generated_profile.get("sandbox_mode"), "read-only")
            self.assertFalse((repo_root / "agents" / "worker.md").exists())
            self.assertFalse((repo_root / "dist" / "codex" / "agents" / "worker.toml").exists())

    def test_bootstrap_registry_missing_profile_fails_without_partial_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repo_root = root / "repo"
            registry_root = root / "registry"
            codex_home = root / ".codex"
            self._seed_minimal_bootstrap_repo(repo_root)
            self._write_text(
                codex_home / "config.toml",
                "\n".join(
                    [
                        'model = "gpt-5.4"',
                        "",
                        "[agents.verification-worker]",
                        'description = "Builtin verification-worker"',
                        'config_file = "missing-verification-worker.toml"',
                        "",
                    ]
                ),
            )

            with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}, clear=False):
                with self.assertRaisesRegex(ValueError, "profile not found"):
                    bootstrap_registry.bootstrap_from_current(repo_root, registry_root)

            self.assertEqual(list(registry_root.glob("*")), [])
