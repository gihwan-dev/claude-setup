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
from workflow_contract import REQUIRED_HELPER_AGENT_IDS, WRITABLE_PROJECTION_AGENT_IDS


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
            if agent_id in WRITABLE_PROJECTION_AGENT_IDS:
                self.assertEqual(role, "implementer", msg=f"worker role drifted: {path}")
                continue
            self.assertNotIn(
                role,
                {"implementer", "orchestrator"},
                msg=f"projected writable role is not allowed: {path}",
            )

    def test_sync_agents_serialize_roundtrips_orchestration_section(self) -> None:
        serialized = sync_agents._serialize_agent_toml(
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
                "close_protocol": "explicit-cancel-or-terminal-close",
                "late_result_policy": "merge-if-relevant",
                "timeout_policy": "background-no-close",
                "allowed_close_reasons": ["explicit-cancel"],
            },
        )
        payload = tomllib.loads(serialized)
        orchestration = payload.get("orchestration")
        self.assertIsInstance(orchestration, dict)
        self.assertEqual(orchestration.get("blocking_class"), "advisory")
        self.assertEqual(orchestration.get("result_contract"), "preliminary-or-final")
        self.assertEqual(orchestration.get("close_protocol"), "explicit-cancel-or-terminal-close")
        self.assertEqual(orchestration.get("late_result_policy"), "merge-if-relevant")
        self.assertEqual(orchestration.get("timeout_policy"), "background-no-close")
        self.assertEqual(
            orchestration.get("allowed_close_reasons"),
            ["explicit-cancel"],
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
                orchestration=None,
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

    def test_bootstrap_registry_roundtrip_uses_policy_defaults_for_worker(self) -> None:
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
            policy = tomllib.loads(
                (repo_root / "policy" / "workflow.toml").read_text(encoding="utf-8")
            )

            with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}, clear=False):
                bootstrap_registry.bootstrap_from_current(repo_root, registry_root)
                entries = sync_agents._read_agent_entries(registry_root)
                sync_agents._validate_entries(entries)
                exit_code = sync_agents._sync_from_registry(repo_root, entries, check=False)

            self.assertEqual(exit_code, 0)

            worker_payload = tomllib.loads(
                (registry_root / "worker" / "agent.toml").read_text(encoding="utf-8")
            )
            projection = worker_payload.get("projection")
            orchestration = worker_payload.get("orchestration")
            codex = worker_payload.get("codex")

            self.assertIsInstance(projection, dict)
            self.assertIsInstance(orchestration, dict)
            self.assertIsInstance(codex, dict)
            self.assertTrue(projection.get("repo"))
            self.assertTrue(projection.get("codex"))
            self.assertEqual(
                codex.get("reasoning_effort"),
                policy["codex"]["expected_reasoning_effort"],
            )
            self.assertEqual(
                codex.get("sandbox_mode"),
                policy["codex"]["sandbox_overrides"]["worker"],
            )
            self.assertEqual(orchestration.get("blocking_class"), "blocking")
            self.assertEqual(orchestration.get("result_contract"), "final-or-checkpoint")
            self.assertEqual(orchestration.get("close_protocol"), "explicit-cancel-or-terminal-close")
            self.assertEqual(orchestration.get("late_result_policy"), "not-applicable")
            self.assertEqual(
                orchestration.get("timeout_policy"),
                policy["helper_close"]["non_advisory_timeout_policy"],
            )
            self.assertEqual(
                orchestration.get("allowed_close_reasons"),
                policy["helper_close"]["strong_close_reasons"],
            )

            generated_profile = tomllib.loads(
                (repo_root / "dist" / "codex" / "agents" / "worker.toml").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                generated_profile.get("model_reasoning_effort"),
                policy["codex"]["expected_reasoning_effort"],
            )
            self.assertEqual(
                generated_profile.get("sandbox_mode"),
                policy["codex"]["sandbox_overrides"]["worker"],
            )
            self.assertTrue((repo_root / "agents" / "worker.md").exists())

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
                        "[agents.worker]",
                        'description = "Builtin worker"',
                        'config_file = "missing-worker.toml"',
                        "",
                    ]
                ),
            )

            with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}, clear=False):
                with self.assertRaisesRegex(ValueError, "profile not found"):
                    bootstrap_registry.bootstrap_from_current(repo_root, registry_root)

            self.assertEqual(list(registry_root.glob("*")), [])
