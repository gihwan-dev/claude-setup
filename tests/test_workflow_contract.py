from __future__ import annotations

import tomllib
from pathlib import Path

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
    SPEC_VALIDATION_SECTION_ORDER,
    STATUS_SECTION_ORDER,
    STRUCTURE_EXCEPTIONS,
    STRUCTURE_HARD_LIMIT_BEHAVIOR,
    STRUCTURE_LEGACY_OVERSIZED_FILE_BEHAVIOR,
    STRUCTURE_RESPONSIBILITY_MIX_BEHAVIOR,
    STRUCTURE_ROLE_LIMITS,
    STRUCTURE_SOFT_LIMIT_BEHAVIOR,
    STRUCTURE_SPLIT_ROLES,
    TASK_BUNDLE_EXECUTION_PLAN_SECTION_ORDER,
    TASK_BUNDLE_IMPACT_FLAGS,
    TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS,
    TASK_BUNDLE_TRACEABILITY_IDS,
    TASK_BUNDLE_WORK_TYPES,
    decide_helper_close_action,
    decide_spec_validation_gate,
    derive_task_bundle_required_docs,
    should_spawn_advisory_helper,
    validate_markdown_sections,
    validate_task_bundle_root,
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

    def test_structure_policy_constants_cover_strong_mode_contract(self) -> None:
        self.assertEqual("split-first", STRUCTURE_SOFT_LIMIT_BEHAVIOR)
        self.assertEqual("block", STRUCTURE_HARD_LIMIT_BEHAVIOR)
        self.assertEqual("block", STRUCTURE_RESPONSIBILITY_MIX_BEHAVIOR)
        self.assertEqual(
            "allow-only-without-additive-growth",
            STRUCTURE_LEGACY_OVERSIZED_FILE_BEHAVIOR,
        )
        self.assertEqual((220, 300), STRUCTURE_ROLE_LIMITS["component_view"])
        self.assertEqual((150, 220), STRUCTURE_ROLE_LIMITS["react_hook_provider_view_model"])
        self.assertEqual((150, 220), STRUCTURE_ROLE_LIMITS["hook_composable_middleware"])
        self.assertEqual((200, 260), STRUCTURE_ROLE_LIMITS["service_use_case_controller_repository_util_module"])
        self.assertEqual((40, 60), STRUCTURE_ROLE_LIMITS["function"])
        self.assertIn("component", STRUCTURE_SPLIT_ROLES)
        self.assertIn("adapter", STRUCTURE_SPLIT_ROLES)
        self.assertIn("migration snapshot", STRUCTURE_EXCEPTIONS)

    def test_fixture_plan_and_status_section_order(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-task"
        plan_error = validate_markdown_sections(fixture_root / "PLAN.md", PLAN_SECTION_ORDER)
        status_error = validate_markdown_sections(fixture_root / "STATUS.md", STATUS_SECTION_ORDER)
        self.assertIsNone(plan_error, msg=plan_error)
        self.assertIsNone(status_error, msg=status_error)

    def test_fixture_task_bundle_contract(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-bundle-task"
        errors = validate_task_bundle_root(fixture_root)
        self.assertEqual([], errors, msg="\n".join(errors))

        spec_error = validate_markdown_sections(
            fixture_root / "SPEC_VALIDATION.md",
            SPEC_VALIDATION_SECTION_ORDER,
        )
        execution_plan_error = validate_markdown_sections(
            fixture_root / "EXECUTION_PLAN.md",
            TASK_BUNDLE_EXECUTION_PLAN_SECTION_ORDER,
        )
        self.assertIsNone(spec_error, msg=spec_error)
        self.assertIsNone(execution_plan_error, msg=execution_plan_error)

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
            close_protocol="explicit-cancel-or-terminal-close",
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
            close_protocol="explicit-cancel-or-terminal-close",
            late_result_policy="merge-if-relevant",
            timeout_policy=ADVISORY_TIMEOUT_POLICY,
            runtime_status="running",
            observed=True,
        )

        decision = decide_helper_close_action(snapshot)

        self.assertFalse(decision.close_allowed)
        self.assertEqual(decision.action, "status-ping")

    def test_decide_helper_close_action_explicit_cancel_requires_interrupt_and_drain_before_close(self) -> None:
        snapshot = HelperCloseSnapshot(
            helper_id="verification-worker",
            blocking_class="semi-blocking",
            result_contract="final-or-checkpoint",
            close_protocol="explicit-cancel-or-terminal-close",
            late_result_policy="merge-if-relevant",
            timeout_policy="observe-and-status-ping",
            runtime_status="running",
            observed=True,
            status_pinged=True,
            close_reason="explicit-cancel",
        )

        decision = decide_helper_close_action(snapshot)

        self.assertFalse(decision.close_allowed)
        self.assertEqual(decision.action, "interrupt-and-drain")

    def test_decide_helper_close_action_rejects_blocked_and_hard_deadline_on_running_helper(self) -> None:
        # blocked reason should not trigger interrupt on running helper
        blocked_snapshot = HelperCloseSnapshot(
            helper_id="verification-worker",
            blocking_class="semi-blocking",
            result_contract="final-or-checkpoint",
            close_protocol="explicit-cancel-or-terminal-close",
            late_result_policy="merge-if-relevant",
            timeout_policy="observe-and-status-ping",
            runtime_status="running",
            observed=True,
            status_pinged=True,
            close_reason="blocked",
        )
        blocked_decision = decide_helper_close_action(blocked_snapshot)
        self.assertFalse(blocked_decision.close_allowed)
        self.assertIn(blocked_decision.action, {"observe", "status-ping"})

        # hard-deadline should also not trigger interrupt on running helper
        hd_snapshot = HelperCloseSnapshot(
            helper_id="verification-worker",
            blocking_class="semi-blocking",
            result_contract="final-or-checkpoint",
            close_protocol="explicit-cancel-or-terminal-close",
            late_result_policy="merge-if-relevant",
            timeout_policy="observe-and-status-ping",
            runtime_status="running",
            observed=True,
            status_pinged=True,
            close_reason="hard-deadline",
        )
        hd_decision = decide_helper_close_action(hd_snapshot)
        self.assertFalse(hd_decision.close_allowed)
        self.assertIn(hd_decision.action, {"observe", "status-ping"})

    def test_decide_helper_close_action_allows_close_with_strong_reason_and_ack(self) -> None:
        snapshot = HelperCloseSnapshot(
            helper_id="explorer",
            blocking_class="advisory",
            result_contract="preliminary-or-final",
            close_protocol="explicit-cancel-or-terminal-close",
            late_result_policy="merge-if-relevant",
            timeout_policy=ADVISORY_TIMEOUT_POLICY,
            runtime_status="interrupted",
            observed=True,
            status_pinged=True,
            interrupt_sent=True,
            drain_grace_elapsed=True,
            close_reason="explicit-cancel",
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
            close_protocol="explicit-cancel-or-terminal-close",
            late_result_policy="merge-if-relevant",
            timeout_policy=ADVISORY_TIMEOUT_POLICY,
            runtime_status="interrupted",
            observed=True,
            interrupt_sent=True,
            drain_grace_elapsed=True,
            close_reason=None,
        )

        decision = decide_helper_close_action(snapshot)

        self.assertTrue(decision.close_allowed)
        self.assertEqual(decision.action, "allow-close")

    def test_decide_helper_close_action_running_preliminary_does_not_allow_close(self) -> None:
        snapshot = HelperCloseSnapshot(
            helper_id="explorer",
            blocking_class="advisory",
            result_contract="preliminary-or-final",
            close_protocol="explicit-cancel-or-terminal-close",
            late_result_policy="merge-if-relevant",
            timeout_policy=ADVISORY_TIMEOUT_POLICY,
            runtime_status="running",
            observed=True,
            status_pinged=True,
            has_preliminary=True,
            close_reason=None,
        )

        decision = decide_helper_close_action(snapshot)

        self.assertFalse(decision.close_allowed)
        self.assertIn(decision.action, {"background", "status-ping", "observe"})
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

    def test_task_bundle_policy_constants_cover_new_workflow(self) -> None:
        self.assertIn("feature", TASK_BUNDLE_WORK_TYPES)
        self.assertIn("ops", TASK_BUNDLE_WORK_TYPES)
        self.assertIn("workflow_changed", TASK_BUNDLE_IMPACT_FLAGS)
        self.assertIn("high_user_risk", TASK_BUNDLE_IMPACT_FLAGS)
        self.assertIn("task", TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS)
        self.assertIn("required_docs", TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS)
        self.assertIn("success_criteria", TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS)
        self.assertIn("major_boundaries", TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS)
        self.assertEqual("REQ", TASK_BUNDLE_TRACEABILITY_IDS["requirement_prefix"])
        self.assertEqual("RISK", TASK_BUNDLE_TRACEABILITY_IDS["risk_prefix"])
        self.assertEqual(
            (
                "Execution slices",
                "Verification",
                "Stop / Replan conditions",
            ),
            TASK_BUNDLE_EXECUTION_PLAN_SECTION_ORDER,
        )

    def test_task_bundle_required_docs_for_feature_flags(self) -> None:
        docs = set(
            derive_task_bundle_required_docs(
                "feature",
                ("ui_surface_changed", "architecture_significant"),
            )
        )
        self.assertTrue(
            {
                "README.md",
                "EXECUTION_PLAN.md",
                "SPEC_VALIDATION.md",
                "STATUS.md",
                "PRD.md",
                "UX_SPEC.md",
                "TECH_SPEC.md",
                "ACCEPTANCE.feature",
                "ADRs/",
            }.issubset(docs)
        )

    def test_task_bundle_required_docs_for_bugfix_high_risk(self) -> None:
        docs = set(
            derive_task_bundle_required_docs(
                "bugfix",
                ("high_user_risk",),
            )
        )
        self.assertIn("BUG_REPORT.md", docs)
        self.assertIn("ROOT_CAUSE.md", docs)
        self.assertIn("REGRESSION.md", docs)

    def test_task_bundle_required_docs_for_contract_changes(self) -> None:
        docs = set(
            derive_task_bundle_required_docs(
                "feature",
                ("public_contract_changed", "data_contract_changed"),
            )
        )
        self.assertIn("openapi.yaml", docs)
        self.assertIn("schema.json", docs)

    def test_spec_validation_gate_defaults_to_advisory_for_low_risk(self) -> None:
        gate = decide_spec_validation_gate(
            tuple(),
            ("README.md", "EXECUTION_PLAN.md", "STATUS.md"),
        )
        self.assertEqual("advisory", gate)

    def test_spec_validation_gate_uses_flags_and_design_doc_count(self) -> None:
        flagged_gate = decide_spec_validation_gate(
            ("workflow_changed",),
            ("README.md", "EXECUTION_PLAN.md", "STATUS.md"),
        )
        counted_gate = decide_spec_validation_gate(
            tuple(),
            ("PRD.md", "UX_SPEC.md", "TECH_SPEC.md"),
        )
        self.assertEqual("blocking", flagged_gate)
        self.assertEqual("blocking", counted_gate)

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

    def test_design_task_continuity_contract_is_documented(self) -> None:
        skill_content = (REPO_ROOT / "skills" / "design-task" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("continuity gate", skill_content)
        self.assertIn("Task continuity", skill_content)
        self.assertIn("goal differs", skill_content)
        self.assertIn("새 task 생성이 기본", skill_content)
        self.assertIn("task.yaml", skill_content)
        self.assertIn("SPEC_VALIDATION.md", skill_content)
        self.assertIn("success_criteria", skill_content)
        self.assertIn("major_boundaries", skill_content)
        self.assertIn("Not started.", skill_content)

    def test_implement_task_requires_user_confirmation_for_multiple_candidates(self) -> None:
        skill_content = (REPO_ROOT / "skills" / "implement-task" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("여러 active task 폴더가 공존하는 것은 정상 경로다.", skill_content)
        self.assertIn("path 미지정이면 먼저 active 후보를 만든다.", skill_content)
        self.assertIn("후보가 정확히 1개일 때만 자동 선택한다.", skill_content)
        self.assertIn("후보가 2개 이상이면 항상 사용자에게 task를 확인받고 자동 실행하지 않는다.", skill_content)
        self.assertIn("task.yaml", skill_content)
        self.assertIn("PLAN.md", skill_content)
        self.assertIn("blocking", skill_content)
        self.assertIn("EXECUTION_PLAN.md", skill_content)

    def test_structure_first_instruction_drift_is_guarded(self) -> None:
        worker_content = (
            REPO_ROOT / "agent-registry" / "worker" / "instructions.md"
        ).read_text(encoding="utf-8")
        self.assertIn("대상 파일 역할 분류", worker_content)
        self.assertIn("예상 post-change LOC", worker_content)
        self.assertIn("split 필요 여부", worker_content)
        self.assertIn("split-first", worker_content)
        self.assertIn("append 금지", worker_content)
        self.assertIn("exact split proposal", worker_content)

        module_gate_content = (
            REPO_ROOT / "agent-registry" / "module-structure-gatekeeper" / "instructions.md"
        ).read_text(encoding="utf-8")
        self.assertIn("이미 soft limit를 넘긴 파일에 additive diff를 더하면 `fail`이다.", module_gate_content)

        frontend_gate_content = (
            REPO_ROOT / "agent-registry" / "frontend-structure-gatekeeper" / "instructions.md"
        ).read_text(encoding="utf-8")
        self.assertIn("이미 soft limit를 넘긴 React 파일에 additive diff를 더하면 `FAIL`이다.", frontend_gate_content)

        project_planner_content = (
            REPO_ROOT / "agent-registry" / "project-planner" / "instructions.md"
        ).read_text(encoding="utf-8")
        self.assertIn("`task.yaml` bundle", project_planner_content)
        self.assertIn("legacy fallback", project_planner_content)
        self.assertNotIn("`tasks/<task-path>/PLAN.md`", project_planner_content)

    def test_design_and_implement_skills_capture_split_decision_contract(self) -> None:
        design_content = (REPO_ROOT / "skills" / "design-task" / "SKILL.md").read_text(encoding="utf-8")
        implement_content = (REPO_ROOT / "skills" / "implement-task" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("structure preflight", design_content)
        self.assertIn("split decision", design_content)
        self.assertIn("target-file append 금지", design_content)

        self.assertIn("structure preflight", implement_content)
        self.assertIn("split-first trigger", implement_content)
        self.assertIn("exact split proposal", implement_content)

    def test_plan_continuity_reference_exists_with_core_rules(self) -> None:
        reference_path = REPO_ROOT / "skills" / "design-task" / "references" / "plan-continuity-rules.md"
        self.assertTrue(reference_path.exists(), msg=f"missing continuity reference: {reference_path}")

        reference_content = reference_path.read_text(encoding="utf-8")
        self.assertIn("Comparison Matrix", reference_content)
        self.assertIn("reuse-existing", reference_content)
        self.assertIn("create-new", reference_content)
        self.assertIn("ambiguous case", reference_content)
        self.assertIn("success_criteria", reference_content)
        self.assertIn("major_boundaries", reference_content)

    def test_task_bundle_reference_exists_with_core_rules(self) -> None:
        reference_path = REPO_ROOT / "skills" / "design-task" / "references" / "task-bundle-rules.md"
        self.assertTrue(reference_path.exists(), msg=f"missing task bundle reference: {reference_path}")

        reference_content = reference_path.read_text(encoding="utf-8")
        self.assertIn("task.yaml", reference_content)
        self.assertIn("SPEC_VALIDATION.md", reference_content)
        self.assertIn("Traceability", reference_content)
        self.assertIn("success_criteria", reference_content)
        self.assertIn("Execution slices", reference_content)
        self.assertIn("Not started.", reference_content)
