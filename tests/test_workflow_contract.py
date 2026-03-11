from __future__ import annotations

import tomllib

from support import REPO_ROOT, RepoTestCase
from workflow_contract import (
    ADVISORY_TIMEOUT_POLICY,
    AGENT_CONTRACTS_BY_ID,
    AdvisorySliceContext,
    CORE_HELPER_ORCHESTRATION_EXPECTED,
    DISABLED_WRITABLE_PROJECTION_AGENT_IDS,
    DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS,
    EXPECTED_CODEX_REASONING_EFFORT,
    EXPECTED_CODEX_SANDBOX_BY_AGENT,
    HelperCloseSnapshot,
    INVALID_CLOSE_REASON,
    LONG_RUNNING_PUBLIC_SURFACE,
    PLAN_SECTION_ORDER,
    REQUIRED_HELPER_AGENT_IDS,
    STATUS_SECTION_ORDER,
    decide_helper_close_action,
    should_spawn_advisory_helper,
    validate_markdown_sections,
)


class WorkflowContractTests(RepoTestCase):
    def test_validate_workflow_contract_command_passes_on_repo(self) -> None:
        completed = self.run_cmd("python3", "scripts/validate_workflow_contracts.py")
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"validate_workflow_contracts failed\nstdout={completed.stdout}\nstderr={completed.stderr}",
        )

    def test_helper_sets_are_derived_from_policy_and_registry(self) -> None:
        policy = tomllib.loads((REPO_ROOT / "policy" / "workflow.toml").read_text(encoding="utf-8"))
        self.assertEqual(
            tuple(policy["public_surface"]["long_running"]),
            LONG_RUNNING_PUBLIC_SURFACE,
        )
        self.assertEqual(
            tuple(policy["projection"]["required_helper_agent_ids"]),
            REQUIRED_HELPER_AGENT_IDS,
        )
        for agent_id in REQUIRED_HELPER_AGENT_IDS:
            self.assertIn(agent_id, AGENT_CONTRACTS_BY_ID)
            orchestration = AGENT_CONTRACTS_BY_ID[agent_id].get("orchestration")
            self.assertEqual(orchestration, CORE_HELPER_ORCHESTRATION_EXPECTED[agent_id])

    def test_fixture_plan_and_status_section_order(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-task"
        plan_error = validate_markdown_sections(fixture_root / "PLAN.md", PLAN_SECTION_ORDER)
        status_error = validate_markdown_sections(fixture_root / "STATUS.md", STATUS_SECTION_ORDER)
        self.assertIsNone(plan_error, msg=plan_error)
        self.assertIsNone(status_error, msg=status_error)

    def test_advisory_close_guard_task_section_order(self) -> None:
        task_root = REPO_ROOT / "tasks" / "advisory-helper-close-guard"
        plan_error = validate_markdown_sections(task_root / "PLAN.md", PLAN_SECTION_ORDER)
        status_error = validate_markdown_sections(task_root / "STATUS.md", STATUS_SECTION_ORDER)
        self.assertIsNone(plan_error, msg=plan_error)
        self.assertIsNone(status_error, msg=status_error)

    def test_core_helper_orchestration_mapping_contract(self) -> None:
        for agent_id, expected in CORE_HELPER_ORCHESTRATION_EXPECTED.items():
            path = REPO_ROOT / "agent-registry" / agent_id / "agent.toml"
            payload = tomllib.loads(path.read_text(encoding="utf-8"))
            orchestration = payload.get("orchestration")
            self.assertIsInstance(orchestration, dict, msg=f"missing [orchestration] in {path}")
            self.assertEqual(orchestration, expected, msg=f"unexpected orchestration mapping for {agent_id}")

    def test_decide_helper_close_action_rejects_bad_advisory_sequence(self) -> None:
        snapshot = HelperCloseSnapshot(
            helper_id="explorer",
            blocking_class="advisory",
            result_contract="preliminary-or-final",
            close_protocol="interrupt-drain-ack-close",
            late_result_policy="merge-if-relevant",
            timeout_policy=ADVISORY_TIMEOUT_POLICY,
            runtime_status="running",
            observed=True,
            status_pinged=True,
            wait_timed_out_count=2,
            close_reason=INVALID_CLOSE_REASON,
        )

        decision = decide_helper_close_action(snapshot)

        self.assertFalse(decision.close_allowed)
        self.assertEqual(decision.action, "background")
        self.assertTrue(decision.accept_late_result)

    def test_decide_helper_close_action_requires_status_ping_for_running_helper(self) -> None:
        snapshot = HelperCloseSnapshot(
            helper_id="explorer",
            blocking_class="advisory",
            result_contract="preliminary-or-final",
            close_protocol="interrupt-drain-ack-close",
            late_result_policy="merge-if-relevant",
            timeout_policy=ADVISORY_TIMEOUT_POLICY,
            runtime_status="running",
            observed=True,
        )

        decision = decide_helper_close_action(snapshot)

        self.assertFalse(decision.close_allowed)
        self.assertEqual(decision.action, "status-ping")

    def test_decide_helper_close_action_requires_interrupt_and_drain_before_close(self) -> None:
        snapshot = HelperCloseSnapshot(
            helper_id="verification-worker",
            blocking_class="semi-blocking",
            result_contract="final-or-checkpoint",
            close_protocol="interrupt-drain-ack-close",
            late_result_policy="merge-if-relevant",
            timeout_policy="observe-and-status-ping",
            runtime_status="running",
            observed=True,
            status_pinged=True,
            close_reason="blocked",
        )

        decision = decide_helper_close_action(snapshot)

        self.assertFalse(decision.close_allowed)
        self.assertEqual(decision.action, "interrupt-and-drain")

    def test_decide_helper_close_action_allows_close_with_strong_reason_and_ack(self) -> None:
        snapshot = HelperCloseSnapshot(
            helper_id="explorer",
            blocking_class="advisory",
            result_contract="preliminary-or-final",
            close_protocol="interrupt-drain-ack-close",
            late_result_policy="merge-if-relevant",
            timeout_policy=ADVISORY_TIMEOUT_POLICY,
            runtime_status="interrupted",
            observed=True,
            status_pinged=True,
            interrupt_sent=True,
            drain_grace_elapsed=True,
            close_reason="blocked",
            has_preliminary=True,
        )

        decision = decide_helper_close_action(snapshot)

        self.assertTrue(decision.close_allowed)
        self.assertEqual(decision.action, "allow-close")
        self.assertIn("strong close reason", decision.rationale)

    def test_decide_helper_close_action_allows_close_with_terminal_status_only_ack(self) -> None:
        snapshot = HelperCloseSnapshot(
            helper_id="explorer",
            blocking_class="advisory",
            result_contract="preliminary-or-final",
            close_protocol="interrupt-drain-ack-close",
            late_result_policy="merge-if-relevant",
            timeout_policy=ADVISORY_TIMEOUT_POLICY,
            runtime_status="interrupted",
            observed=True,
            interrupt_sent=True,
            drain_grace_elapsed=True,
            close_reason="hard-deadline",
        )

        decision = decide_helper_close_action(snapshot)

        self.assertTrue(decision.close_allowed)
        self.assertEqual(decision.action, "allow-close")
        self.assertIn("hard-deadline", decision.rationale)

    def test_should_spawn_advisory_helper_skips_small_low_risk_slice(self) -> None:
        context = AdvisorySliceContext(
            helper_id="code-quality-reviewer",
            can_change_current_decision=True,
        )
        self.assertFalse(should_spawn_advisory_helper(context))

    def test_should_spawn_advisory_helper_selects_only_relevant_helper(self) -> None:
        architecture_context = AdvisorySliceContext(
            helper_id="architecture-reviewer",
            files_changed=7,
            can_change_current_decision=True,
        )
        type_context = AdvisorySliceContext(
            helper_id="type-specialist",
            files_changed=7,
            can_change_current_decision=True,
        )

        self.assertTrue(should_spawn_advisory_helper(architecture_context))
        self.assertFalse(should_spawn_advisory_helper(type_context))

    def test_should_spawn_advisory_helper_uses_existing_trigger_for_reviewer(self) -> None:
        context = AdvisorySliceContext(
            helper_id="code-quality-reviewer",
            files_changed=3,
            can_change_current_decision=True,
        )
        self.assertTrue(should_spawn_advisory_helper(context))

    def test_generated_managed_agent_profiles_match_contract_defaults(self) -> None:
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
