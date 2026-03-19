from __future__ import annotations

import json
import tomllib
from pathlib import Path

from support import REPO_ROOT, RepoTestCase
from workflow_contract import (
    AGENT_CONTRACTS_BY_ID,
    AdvisorySliceContext,
    BASELINE_MULTI_REVIEW_HELPERS,
    DEFAULT_MULTI_WORK_EXPLORATION_HELPERS,
    decide_multi_work_route,
    decide_slice_execution_mode,
    derive_csv_fanout_docs,
    derive_multi_review_helpers,
    derive_multi_work_helpers,
    DOCUMENTATION_ONLY_BUILTIN_AGENT_IDS,
    EXPECTED_CODEX_SANDBOX_BY_AGENT,
    expected_reasoning_effort_for,
    LONG_RUNNING_PUBLIC_SURFACE,
    MultiWorkRoutingContext,
    PLAN_SECTION_ORDER,
    REQUIRED_HELPER_AGENT_IDS,
    SliceExecutionPlan,
    SLICE_BUDGET_ENFORCEMENT,
    SLICE_BUDGET_MAX_NET_LOC,
    SLICE_BUDGET_MAX_REPO_FILES,
    SPEC_VALIDATION_SECTION_ORDER,
    STATUS_SECTION_ORDER,
    TASK_BUNDLE_CSV_FANOUT_DOCS,
    TASK_BUNDLE_CSV_FANOUT_ORCHESTRATION_REQUIRED_KEYS,
    TASK_BUNDLE_DELIVERY_STRATEGIES,
    TASK_BUNDLE_EXECUTION_PLAN_SECTION_ORDER,
    TASK_BUNDLE_EXECUTION_TOPOLOGIES,
    TASK_BUNDLE_IMPACT_FLAGS,
    TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS,
    TASK_BUNDLE_TRACEABILITY_IDS,
    TASK_BUNDLE_UI_FIRST_FLAGS,
    TASK_BUNDLE_UI_FIRST_WORK_TYPES,
    TASK_BUNDLE_WORK_TYPES,
    decide_task_bundle_delivery_strategy,
    decide_spec_validation_gate,
    derive_task_bundle_required_docs,
    load_task_bundle_manifest,
    should_spawn_advisory_helper,
    validate_markdown_sections,
    validate_task_bundle_root,
)


class WorkflowContractTests(RepoTestCase):
    def assertHeadingSequence(self, path: Path, headings: tuple[str, ...]) -> None:
        actual = [
            line[3:].strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("## ")
        ]
        self.assertEqual(list(headings), actual, msg=f"unexpected heading order in {path}")

    def assertReferenceManifestFixture(self, root: Path) -> None:
        manifest_path = root / "DESIGN_REFERENCES" / "manifest.json"
        raw_dir = root / "DESIGN_REFERENCES" / "raw"
        curated_dir = root / "DESIGN_REFERENCES" / "curated"

        entries = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertIsInstance(entries, list)
        self.assertGreaterEqual(len(entries), 3, msg=f"expected 3+ reference entries in {manifest_path}")

        adopt_count = 0
        avoid_count = 0
        for entry in entries:
            self.assertIsInstance(entry, dict)
            self.assertTrue(
                {
                    "file",
                    "source_url",
                    "captured_at",
                    "kind",
                    "tags",
                    "adopt_reason",
                    "avoid_reason",
                    "notes",
                }.issubset(entry.keys())
            )
            if entry["kind"] == "adopt":
                adopt_count += 1
            if entry["kind"] == "avoid":
                avoid_count += 1

        self.assertGreaterEqual(adopt_count, 2, msg=f"expected 2+ adopt entries in {manifest_path}")
        self.assertGreaterEqual(avoid_count, 1, msg=f"expected 1+ avoid entry in {manifest_path}")
        self.assertTrue(list(raw_dir.glob("*.svg")), msg=f"expected raw SVG placeholders in {raw_dir}")
        self.assertTrue(list(curated_dir.glob("*.svg")), msg=f"expected curated SVG placeholders in {curated_dir}")

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

    def test_structure_reviewer_agent_has_thresholds(self) -> None:
        agent_path = REPO_ROOT / "agent-registry" / "structure-reviewer" / "agent.toml"
        data = tomllib.loads(agent_path.read_text(encoding="utf-8"))
        thresholds = data.get("thresholds")
        self.assertIsNotNone(thresholds)
        self.assertEqual("split-first", thresholds["soft_limit_behavior"])
        self.assertEqual("block", thresholds["hard_limit_behavior"])
        self.assertEqual("block", thresholds["responsibility_mix_behavior"])
        self.assertEqual(
            "allow-only-without-additive-growth",
            thresholds["legacy_oversized_file_behavior"],
        )
        role_limits = thresholds["role_limits"]
        self.assertEqual(220, role_limits["component_view"]["target"])
        self.assertEqual(300, role_limits["component_view"]["hard"])
        self.assertIn("component", thresholds["split_roles"])
        self.assertIn("adapter", thresholds["split_roles"])
        self.assertIn("migration snapshot", thresholds["exceptions"])

    def test_slice_budget_constants(self) -> None:
        self.assertEqual(3, SLICE_BUDGET_MAX_REPO_FILES)
        self.assertEqual(150, SLICE_BUDGET_MAX_NET_LOC)
        self.assertEqual("split-before-execution", SLICE_BUDGET_ENFORCEMENT)

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

    def test_fixture_task_bundle_contract_allows_optional_implementation_source(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-bundle-task"
        manifest = load_task_bundle_manifest(fixture_root / "task.yaml")
        raw_task_yaml = (fixture_root / "task.yaml").read_text(encoding="utf-8")

        self.assertIn("IMPLEMENTATION_CONTRACT.md", manifest.required_docs)
        self.assertIn("UX_BEHAVIOR_ACCESSIBILITY.md", manifest.required_docs)
        self.assertIn("DESIGN_REFERENCES/", manifest.required_docs)
        self.assertEqual(
            "IMPLEMENTATION_CONTRACT.md",
            manifest.source_of_truth.get("implementation"),
        )
        self.assertEqual("UX_SPEC.md", manifest.source_of_truth.get("ux"))
        self.assertEqual("UX_BEHAVIOR_ACCESSIBILITY.md", manifest.source_of_truth.get("ux_behavior"))
        self.assertEqual("DESIGN_REFERENCES/manifest.json", manifest.source_of_truth.get("design_references"))
        self.assertIn("ux: UX_SPEC.md", raw_task_yaml)
        self.assertIn("ux_behavior: UX_BEHAVIOR_ACCESSIBILITY.md", raw_task_yaml)
        self.assertIn("design_references: DESIGN_REFERENCES/manifest.json", raw_task_yaml)

    def test_pending_and_bootstrapped_bundle_fixtures_capture_bootstrap_state(self) -> None:
        pending_root = REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-pending-bootstrap-task"
        cleared_root = REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-bundle-task"

        pending_errors = validate_task_bundle_root(pending_root)
        cleared_errors = validate_task_bundle_root(cleared_root)
        self.assertEqual([], pending_errors, msg="\n".join(pending_errors))
        self.assertEqual([], cleared_errors, msg="\n".join(cleared_errors))

        pending_manifest = load_task_bundle_manifest(pending_root / "task.yaml")
        cleared_manifest = load_task_bundle_manifest(cleared_root / "task.yaml")
        pending_task_yaml = (pending_root / "task.yaml").read_text(encoding="utf-8")
        cleared_task_yaml = (cleared_root / "task.yaml").read_text(encoding="utf-8")
        pending_validation = (pending_root / "SPEC_VALIDATION.md").read_text(encoding="utf-8")
        cleared_validation = (cleared_root / "SPEC_VALIDATION.md").read_text(encoding="utf-8")

        self.assertNotIn("IMPLEMENTATION_CONTRACT.md", pending_manifest.required_docs)
        self.assertNotIn("implementation", pending_manifest.source_of_truth)
        self.assertEqual("UX_SPEC.md", pending_manifest.source_of_truth.get("ux"))
        self.assertEqual("UX_BEHAVIOR_ACCESSIBILITY.md", pending_manifest.source_of_truth.get("ux_behavior"))
        self.assertEqual("DESIGN_REFERENCES/manifest.json", pending_manifest.source_of_truth.get("design_references"))
        self.assertIn("ux: UX_SPEC.md", pending_task_yaml)
        self.assertIn("ux_behavior: UX_BEHAVIOR_ACCESSIBILITY.md", pending_task_yaml)
        self.assertIn("design_references: DESIGN_REFERENCES/manifest.json", pending_task_yaml)
        self.assertIn("$bootstrap-project-rules", pending_validation)

        self.assertIn("IMPLEMENTATION_CONTRACT.md", cleared_manifest.required_docs)
        self.assertEqual("IMPLEMENTATION_CONTRACT.md", cleared_manifest.source_of_truth.get("implementation"))
        self.assertEqual("UX_SPEC.md", cleared_manifest.source_of_truth.get("ux"))
        self.assertEqual("UX_BEHAVIOR_ACCESSIBILITY.md", cleared_manifest.source_of_truth.get("ux_behavior"))
        self.assertEqual("DESIGN_REFERENCES/manifest.json", cleared_manifest.source_of_truth.get("design_references"))
        self.assertIn("ux: UX_SPEC.md", cleared_task_yaml)
        self.assertIn("ux_behavior: UX_BEHAVIOR_ACCESSIBILITY.md", cleared_task_yaml)
        self.assertIn("design_references: DESIGN_REFERENCES/manifest.json", cleared_task_yaml)
        self.assertIn("$bootstrap-project-rules", cleared_validation)
        self.assertIn("completed", cleared_validation)

    def test_advisory_close_guard_task_section_order(self) -> None:
        task_root = REPO_ROOT / "tasks" / "advisory-helper-close-guard"
        plan_error = validate_markdown_sections(task_root / "PLAN.md", PLAN_SECTION_ORDER)
        status_error = validate_markdown_sections(task_root / "STATUS.md", STATUS_SECTION_ORDER)
        self.assertIsNone(plan_error, msg=plan_error)
        self.assertIsNone(status_error, msg=status_error)

    def test_decide_slice_execution_mode_rejects_broad_prep0_handoff(self) -> None:
        decision = decide_slice_execution_mode(
            SliceExecutionPlan(
                repo_files_planned=2,
                net_loc_planned=80,
                work_labels=("setup", "docs"),
            )
        )

        self.assertFalse(decision.execution_allowed)
        self.assertEqual("split-replan", decision.action)
        self.assertIn(SLICE_BUDGET_ENFORCEMENT, decision.rationale)

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

    def test_should_spawn_explorer_for_repo_exploration(self) -> None:
        context = AdvisorySliceContext(
            helper_id="explorer",
            needs_repo_exploration=True,
            can_change_current_decision=True,
        )
        self.assertTrue(should_spawn_advisory_helper(context))

    def test_should_spawn_web_researcher_for_external_research(self) -> None:
        context = AdvisorySliceContext(
            helper_id="web-researcher",
            needs_external_research=True,
            can_change_current_decision=True,
        )
        self.assertTrue(should_spawn_advisory_helper(context))

    def test_should_spawn_browser_explorer_for_browser_repro(self) -> None:
        context = AdvisorySliceContext(
            helper_id="browser-explorer",
            needs_browser_repro=True,
            can_change_current_decision=True,
        )
        self.assertTrue(should_spawn_advisory_helper(context))

    def test_should_spawn_advisory_helper_selects_react_state_reviewer_for_frontend_slice(self) -> None:
        context = AdvisorySliceContext(
            helper_id="react-state-reviewer",
            is_frontend_slice=True,
            can_change_current_decision=True,
        )
        self.assertTrue(should_spawn_advisory_helper(context))

    def test_should_spawn_advisory_helper_skips_react_state_reviewer_for_non_frontend_slice(self) -> None:
        context = AdvisorySliceContext(
            helper_id="react-state-reviewer",
            is_frontend_slice=False,
            can_change_current_decision=True,
        )
        self.assertFalse(should_spawn_advisory_helper(context))

    def test_react_state_reviewer_is_in_required_helper_agent_ids(self) -> None:
        self.assertIn("react-state-reviewer", REQUIRED_HELPER_AGENT_IDS)

    def test_task_bundle_policy_constants_cover_new_workflow(self) -> None:
        self.assertIn("feature", TASK_BUNDLE_WORK_TYPES)
        self.assertIn("ops", TASK_BUNDLE_WORK_TYPES)
        self.assertIn("workflow_changed", TASK_BUNDLE_IMPACT_FLAGS)
        self.assertIn("high_user_risk", TASK_BUNDLE_IMPACT_FLAGS)
        self.assertIn("task", TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS)
        self.assertIn("required_docs", TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS)
        self.assertIn("success_criteria", TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS)
        self.assertIn("major_boundaries", TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS)
        self.assertIn("delivery_strategy", TASK_BUNDLE_REQUIRED_TASK_YAML_KEYS)
        self.assertEqual(("standard", "ui-first"), TASK_BUNDLE_DELIVERY_STRATEGIES)
        self.assertIn("feature", TASK_BUNDLE_UI_FIRST_WORK_TYPES)
        self.assertIn("bugfix", TASK_BUNDLE_UI_FIRST_WORK_TYPES)
        self.assertEqual(("ui_surface_changed", "workflow_changed"), TASK_BUNDLE_UI_FIRST_FLAGS)
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
                "UX_BEHAVIOR_ACCESSIBILITY.md",
                "DESIGN_REFERENCES/",
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

    def test_task_bundle_delivery_strategy_derivation(self) -> None:
        ui_first = decide_task_bundle_delivery_strategy(
            "feature",
            ("ui_surface_changed",),
        )
        workflow_ui_first = decide_task_bundle_delivery_strategy(
            "bugfix",
            ("workflow_changed",),
        )
        standard = decide_task_bundle_delivery_strategy(
            "ops",
            tuple(),
        )
        self.assertEqual("ui-first", ui_first)
        self.assertEqual("ui-first", workflow_ui_first)
        self.assertEqual("standard", standard)

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
            ("PRD.md", "UX_SPEC.md", "UX_BEHAVIOR_ACCESSIBILITY.md"),
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
            registry_payload = tomllib.loads(
                (REPO_ROOT / "agent-registry" / agent_id / "agent.toml").read_text(encoding="utf-8")
            )
            codex = registry_payload.get("codex")
            self.assertIsInstance(codex, dict, msg=f"missing [codex] for {agent_id}")
            expected_sandbox = codex.get(
                "sandbox_mode",
                EXPECTED_CODEX_SANDBOX_BY_AGENT.get(agent_id, "read-only"),
            )
            self.assertEqual(
                profile.get("sandbox_mode"),
                expected_sandbox,
                msg=f"projected agent sandbox mismatch: {agent_id}",
            )
            self.assertEqual(
                profile.get("model_reasoning_effort"),
                expected_reasoning_effort_for(agent_id),
                msg=f"projected agent reasoning effort drifted: {agent_id}",
            )

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
        self.assertIn("delivery_strategy", skill_content)
        self.assertIn("normalized required_docs", skill_content)
        self.assertIn("source_of_truth.implementation", skill_content)
        self.assertIn("preserved", skill_content)
        self.assertIn("Not started.", skill_content)

    def test_bootstrap_project_rules_skill_contract_is_documented(self) -> None:
        skill_content = (
            REPO_ROOT / "skills" / "bootstrap-project-rules" / "SKILL.md"
        ).read_text(encoding="utf-8")
        prompt_content = (
            REPO_ROOT / "skills" / "bootstrap-project-rules" / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")
        decision_reference = (
            REPO_ROOT / "skills" / "bootstrap-project-rules" / "references" / "decision-catalog.md"
        ).read_text(encoding="utf-8")
        template_reference = (
            REPO_ROOT / "skills" / "bootstrap-project-rules" / "references" / "doc-templates.md"
        ).read_text(encoding="utf-8")

        self.assertIn("docs/ai/ENGINEERING_RULES.md", skill_content)
        self.assertIn("IMPLEMENTATION_CONTRACT.md", skill_content)
        self.assertIn("Locked now", skill_content)
        self.assertIn("Deferred", skill_content)
        self.assertIn("Banned/Avoid", skill_content)
        self.assertIn("bootstrap-project-rules:start", skill_content)
        self.assertIn("AGENTS.md", prompt_content)
        self.assertIn("CLAUDE.md", prompt_content)
        self.assertIn("Decision Catalog", decision_reference)
        self.assertIn("Managed Section Markers", template_reference)

    def test_design_task_documents_post_design_bootstrap_handoff(self) -> None:
        skill_content = (REPO_ROOT / "skills" / "design-task" / "SKILL.md").read_text(encoding="utf-8")
        prompt_content = (
            REPO_ROOT / "skills" / "design-task" / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")
        reference_content = (
            REPO_ROOT / "skills" / "design-task" / "references" / "task-bundle-rules.md"
        ).read_text(encoding="utf-8")

        self.assertIn("$bootstrap-project-rules", skill_content)
        self.assertIn("source_of_truth.implementation", skill_content)
        self.assertIn("IMPLEMENTATION_CONTRACT.md", reference_content)
        self.assertIn("$bootstrap-project-rules", prompt_content)
        self.assertIn("reference-pack", skill_content)
        self.assertIn("figma-less-ui-design", skill_content)
        self.assertIn("UI Planning Packet", skill_content)
        self.assertIn("UX_BEHAVIOR_ACCESSIBILITY.md", skill_content)
        self.assertIn("reuse + delta", skill_content)

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
        self.assertIn("delivery_strategy", skill_content)

    def test_implement_task_reads_optional_implementation_contract(self) -> None:
        skill_content = (REPO_ROOT / "skills" / "implement-task" / "SKILL.md").read_text(encoding="utf-8")
        prompt_content = (
            REPO_ROOT / "skills" / "implement-task" / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")

        self.assertIn("source_of_truth.implementation", skill_content)
        self.assertIn("IMPLEMENTATION_CONTRACT.md", skill_content)
        self.assertIn("$bootstrap-project-rules", skill_content)
        self.assertIn("source_of_truth.implementation", prompt_content)
        self.assertIn("IMPLEMENTATION_CONTRACT.md", prompt_content)
        self.assertIn("UX_SPEC.md", skill_content)
        self.assertIn("UX_BEHAVIOR_ACCESSIBILITY.md", skill_content)
        self.assertIn("checklist", skill_content)
        self.assertIn("state matrix/fixture", skill_content)
        self.assertIn("UX_SPEC.md", prompt_content)
        self.assertIn("UX_BEHAVIOR_ACCESSIBILITY.md", prompt_content)
        self.assertIn("`browser-explorer`", prompt_content)
        self.assertIn("allow_implicit_invocation: false", prompt_content)

    def test_design_and_implement_task_are_explicit_only(self) -> None:
        design_skill_content = (REPO_ROOT / "skills" / "design-task" / "SKILL.md").read_text(encoding="utf-8")
        implement_skill_content = (REPO_ROOT / "skills" / "implement-task" / "SKILL.md").read_text(encoding="utf-8")
        design_prompt_content = (
            REPO_ROOT / "skills" / "design-task" / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")
        implement_prompt_content = (
            REPO_ROOT / "skills" / "implement-task" / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")

        self.assertIn("explicitly writes `design-task` or `$design-task`", design_skill_content)
        self.assertNotIn('"설계해줘"', design_skill_content)
        self.assertNotIn('"계획 세워줘"', design_skill_content)
        self.assertIn("allow_implicit_invocation: false", design_prompt_content)

        self.assertIn("explicitly writes `implement-task` or", implement_skill_content)
        self.assertIn("`$implement-task`", implement_skill_content)
        self.assertNotIn("`구현해줘`", implement_skill_content)
        self.assertNotIn("`다음 단계 진행해`", implement_skill_content)
        self.assertNotIn("`계속해`", implement_skill_content)
        self.assertIn("allow_implicit_invocation: false", implement_prompt_content)

    def test_multi_work_skill_contract_is_documented(self) -> None:
        skill_content = (REPO_ROOT / "skills" / "multi-work" / "SKILL.md").read_text(encoding="utf-8")
        prompt_content = (
            REPO_ROOT / "skills" / "multi-work" / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")
        reference_content = (
            REPO_ROOT / "skills" / "multi-work" / "references" / "routing-contract.md"
        ).read_text(encoding="utf-8")

        self.assertIn("/multi-work", skill_content)
        self.assertIn("멀티 에이전트 탐색", skill_content)
        self.assertIn(
            "서브 에이전트 결과 반환 전에는 `wait`/결과 수집 외 다른 파일 읽기, 검색, 추가 탐색을 금지한다.",
            skill_content,
        )
        self.assertIn("`design-task`", skill_content)
        self.assertIn("`implement-task`", skill_content)
        self.assertIn("direct execution", skill_content)
        self.assertIn("allow_implicit_invocation: false", prompt_content)
        self.assertIn("references/routing-contract.md", prompt_content)
        self.assertIn("scripts/workflow_contract.py", prompt_content)
        self.assertIn("`wait`/결과 수집 외 다른 파일 읽기, 검색, 추가 탐색을 금지", prompt_content)
        self.assertIn("Helper Matrix", reference_content)
        self.assertIn("Routing Matrix", reference_content)
        self.assertIn(
            "서브 에이전트 결과 반환 전에는 `wait`/결과 수집 외 다른 파일 읽기, 검색, 추가 탐색을 금지한다.",
            reference_content,
        )
        self.assertIn("small slices + run-to-boundary", reference_content)

    def test_multi_review_skill_contract_is_documented(self) -> None:
        skill_content = (REPO_ROOT / "skills" / "multi-review" / "SKILL.md").read_text(encoding="utf-8")
        prompt_content = (
            REPO_ROOT / "skills" / "multi-review" / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")
        reference_content = (
            REPO_ROOT / "skills" / "multi-review" / "references" / "reviewer-matrix.md"
        ).read_text(encoding="utf-8")

        self.assertIn("/multi-review", skill_content)
        self.assertIn("read-only", skill_content)
        self.assertIn("reviewer-matrix.md", skill_content)
        self.assertIn("current worktree diff 대 `HEAD`", skill_content)
        self.assertIn(
            "서브 에이전트 결과 반환 전에는 `wait`/결과 수집 외 다른 파일 읽기, 검색, 추가 탐색을 금지한다.",
            skill_content,
        )
        self.assertIn("findings first, summary second", skill_content)
        self.assertIn("allow_implicit_invocation: false", prompt_content)
        self.assertIn("references/reviewer-matrix.md", prompt_content)
        self.assertIn("scripts/workflow_contract.py", prompt_content)
        self.assertIn("`wait`/결과 수집 외 다른 파일 읽기", prompt_content)
        self.assertIn("summary second", prompt_content)
        self.assertIn("Target Precedence", reference_content)
        self.assertIn("Baseline Reviewers", reference_content)
        self.assertIn("Conditional Reviewers", reference_content)
        self.assertIn(
            "서브 에이전트 결과 반환 전에는 `wait`/결과 수집 외 다른 파일 읽기, 검색, 추가 탐색을 금지한다.",
            reference_content,
        )

    def test_multi_work_helper_derivation_and_route_defaults(self) -> None:
        self.assertEqual(DEFAULT_MULTI_WORK_EXPLORATION_HELPERS, derive_multi_work_helpers())
        self.assertEqual(
            ("explorer", "structure-reviewer", "web-researcher"),
            derive_multi_work_helpers(needs_external_research=True),
        )
        self.assertEqual(
            ("explorer", "structure-reviewer", "browser-explorer"),
            derive_multi_work_helpers(needs_browser_repro=True),
        )
        self.assertEqual(
            "design-task",
            decide_multi_work_route(MultiWorkRoutingContext(plan_mode=True)),
        )
        self.assertEqual(
            "implement-task",
            decide_multi_work_route(MultiWorkRoutingContext(existing_task_bundle_available=True)),
        )
        self.assertEqual(
            "design-task",
            decide_multi_work_route(MultiWorkRoutingContext(work_is_large_or_ambiguous=True)),
        )
        self.assertEqual(
            "direct-execution",
            decide_multi_work_route(MultiWorkRoutingContext()),
        )

    def test_multi_review_helper_derivation_uses_baseline_and_conditional_reviewers(self) -> None:
        quiet_helpers = derive_multi_review_helpers(
            AdvisorySliceContext(helper_id="code-quality-reviewer", can_change_current_decision=True)
        )
        self.assertEqual(BASELINE_MULTI_REVIEW_HELPERS, quiet_helpers)

        risky_frontend_helpers = derive_multi_review_helpers(
            AdvisorySliceContext(
                helper_id="code-quality-reviewer",
                files_changed=7,
                public_surface_changed=True,
                shared_types_changed=True,
                public_contract_changed=True,
                is_frontend_slice=True,
                needs_browser_repro=True,
                can_change_current_decision=True,
            )
        )
        self.assertEqual(
            (
                "structure-reviewer",
                "code-quality-reviewer",
                "test-engineer",
                "architecture-reviewer",
                "type-specialist",
                "react-state-reviewer",
                "browser-explorer",
            ),
            risky_frontend_helpers,
        )

    def test_structure_reviewer_instruction_drift_is_guarded(self) -> None:
        self.assertFalse((REPO_ROOT / "agent-registry" / "worker").exists())

        reviewer_content = (
            REPO_ROOT / "agent-registry" / "structure-reviewer" / "instructions.md"
        ).read_text(encoding="utf-8")
        self.assertIn("이미 soft limit를 넘긴 파일에 additive diff를 더하면 `FAIL`이다.", reviewer_content)
        self.assertIn("component/view file: target <=", reviewer_content)
        self.assertIn("React hook/provider/view-model file: target <=", reviewer_content)

    def test_design_and_implement_skills_capture_split_decision_contract(self) -> None:
        design_content = (REPO_ROOT / "skills" / "design-task" / "SKILL.md").read_text(encoding="utf-8")
        implement_content = (REPO_ROOT / "skills" / "implement-task" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("structure preflight", design_content)
        self.assertIn("split decision", design_content)
        self.assertIn("target-file append 금지", design_content)
        self.assertIn("repo-tracked files 3개 이하", design_content)
        self.assertIn("split/replan before execution", design_content)
        self.assertNotIn("하나의 응집된 모듈 경계", design_content)

        self.assertIn("structure preflight", implement_content)
        self.assertIn("split-first trigger", implement_content)
        self.assertIn("exact split proposal", implement_content)
        self.assertIn("repo-tracked files 3개 이하", implement_content)
        self.assertIn("split/replan before execution", implement_content)
        self.assertNotIn("하나의 응집된 모듈 경계", implement_content)

    def test_documentation_recheck_contract_is_documented(self) -> None:
        routing_content = (REPO_ROOT / "docs" / "policy" / "10-routing.md").read_text(encoding="utf-8")
        workflows_content = (REPO_ROOT / "docs" / "policy" / "20-workflows.md").read_text(encoding="utf-8")
        skill_content = (REPO_ROOT / "skills" / "implement-task" / "SKILL.md").read_text(encoding="utf-8")
        instructions_content = (REPO_ROOT / "INSTRUCTIONS.md").read_text(encoding="utf-8")
        prompt_content = (
            REPO_ROOT / "skills" / "implement-task" / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")
        normalized_prompt_content = " ".join(prompt_content.split())

        self.assertIn("small slices + run-to-boundary", routing_content)
        self.assertIn("split/replan before execution", routing_content)
        self.assertIn("small slices + run-to-boundary", workflows_content)
        self.assertIn("python3 scripts/sync_skills_index.py --check", skill_content)
        self.assertIn("python3 scripts/sync_agents.py --check", skill_content)
        self.assertIn("small slices + run-to-boundary", skill_content)
        self.assertIn("slice implementation -> main focused validation -> commit", skill_content)
        self.assertIn("small slices + run-to-boundary", instructions_content)
        self.assertIn("실질 영향 문서를 다시 확인", normalized_prompt_content)
        self.assertIn("small slices + run-to-boundary", normalized_prompt_content)
        self.assertIn("slice implementation -> main focused validation -> commit", normalized_prompt_content)
        self.assertIn("split/replan before execution", normalized_prompt_content)
        self.assertIn("python3 scripts/sync_instructions.py", normalized_prompt_content)
        self.assertIn("python3 scripts/sync_skills_index.py", normalized_prompt_content)
        self.assertIn("python3 scripts/sync_agents.py", normalized_prompt_content)

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
        self.assertIn("delivery_strategy", reference_content)
        self.assertIn("IMPLEMENTATION_CONTRACT.md", reference_content)
        self.assertIn("normalize", reference_content)
        self.assertIn("preserved", reference_content)
        self.assertIn("source_of_truth.implementation", reference_content)

    def test_task_bundle_reference_exists_with_core_rules(self) -> None:
        reference_path = REPO_ROOT / "skills" / "design-task" / "references" / "task-bundle-rules.md"
        self.assertTrue(reference_path.exists(), msg=f"missing task bundle reference: {reference_path}")

        reference_content = reference_path.read_text(encoding="utf-8")
        self.assertIn("task.yaml", reference_content)
        self.assertIn("SPEC_VALIDATION.md", reference_content)
        self.assertIn("Traceability", reference_content)
        self.assertIn("success_criteria", reference_content)
        self.assertIn("Execution slices", reference_content)
        self.assertIn("delivery_strategy", reference_content)
        self.assertIn("Not started.", reference_content)
        self.assertIn("UI Planning Packet", reference_content)
        self.assertIn("UX_BEHAVIOR_ACCESSIBILITY.md", reference_content)
        self.assertIn("DESIGN_REFERENCES/", reference_content)
        self.assertIn("reference-pack", reference_content)

    def test_figma_less_ui_design_skill_contract_is_documented(self) -> None:
        skill_path = REPO_ROOT / "skills" / "figma-less-ui-design" / "SKILL.md"
        prompt_path = REPO_ROOT / "skills" / "figma-less-ui-design" / "agents" / "openai.yaml"
        patterns_path = REPO_ROOT / "skills" / "figma-less-ui-design" / "references" / "official-patterns.md"
        template_path = REPO_ROOT / "skills" / "figma-less-ui-design" / "references" / "ui-planning-templates.md"

        self.assertTrue(skill_path.exists(), msg=f"missing skill file: {skill_path}")
        self.assertTrue(prompt_path.exists(), msg=f"missing prompt file: {prompt_path}")
        self.assertTrue(patterns_path.exists(), msg=f"missing reference file: {patterns_path}")
        self.assertTrue(template_path.exists(), msg=f"missing reference file: {template_path}")

        skill_content = skill_path.read_text(encoding="utf-8")
        prompt_content = prompt_path.read_text(encoding="utf-8")
        patterns_content = patterns_path.read_text(encoding="utf-8")
        template_content = template_path.read_text(encoding="utf-8")

        self.assertIn("UI Planning Packet", skill_content)
        self.assertIn("UX_BEHAVIOR_ACCESSIBILITY.md", skill_content)
        self.assertIn("reuse + delta", skill_content)
        self.assertIn("Goal/Audience/Platform", template_content)
        self.assertIn("Task-based Approval Criteria", template_content)
        self.assertIn("reuse + delta", patterns_content)
        self.assertIn("UX_SPEC.md", prompt_content)
        self.assertIn("allow_implicit_invocation: false", prompt_content)

    def test_reference_pack_skill_contract_is_documented(self) -> None:
        skill_path = REPO_ROOT / "skills" / "reference-pack" / "SKILL.md"
        prompt_path = REPO_ROOT / "skills" / "reference-pack" / "agents" / "openai.yaml"

        self.assertTrue(skill_path.exists(), msg=f"missing skill file: {skill_path}")
        self.assertTrue(prompt_path.exists(), msg=f"missing prompt file: {prompt_path}")

        skill_content = skill_path.read_text(encoding="utf-8")
        prompt_content = prompt_path.read_text(encoding="utf-8")

        self.assertIn("DESIGN_REFERENCES/", skill_content)
        self.assertIn("manifest.json", skill_content)
        self.assertIn("최소 3개", skill_content)
        self.assertIn("allow_implicit_invocation: false", prompt_content)

    def test_ui_first_fixtures_use_ui_planning_packet_headings(self) -> None:
        headings = (
            "Goal/Audience/Platform",
            "30-Second Understanding Checklist",
            "Visual Direction + Anti-goals",
            "Reference Pack (adopt/avoid)",
            "Glossary + Object Model",
            "Layout/App-shell Contract",
            "Token + Primitive Contract",
            "Screen + Flow Coverage",
            "Implementation Prompt/Handoff",
        )
        behavior_headings = (
            "Interaction Model",
            "Keyboard + Focus Contract",
            "Accessibility Contract",
            "Live Update Semantics",
            "State Matrix + Fixture Strategy",
            "Large-run Degradation Rules",
            "Microcopy + Information Expression Rules",
            "Task-based Approval Criteria",
        )
        bundle_ux = REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-bundle-task" / "UX_SPEC.md"
        pending_ux = REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-pending-bootstrap-task" / "UX_SPEC.md"
        bundle_behavior = (
            REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-bundle-task" / "UX_BEHAVIOR_ACCESSIBILITY.md"
        )
        pending_behavior = (
            REPO_ROOT
            / "tests"
            / "fixtures"
            / "tasks"
            / "sample-pending-bootstrap-task"
            / "UX_BEHAVIOR_ACCESSIBILITY.md"
        )
        bundle_readme = REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-bundle-task" / "README.md"
        pending_readme = REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-pending-bootstrap-task" / "README.md"

        self.assertHeadingSequence(bundle_ux, headings)
        self.assertHeadingSequence(pending_ux, headings)
        self.assertHeadingSequence(bundle_behavior, behavior_headings)
        self.assertHeadingSequence(pending_behavior, behavior_headings)
        self.assertIn("UI Planning Packet", bundle_readme.read_text(encoding="utf-8"))
        self.assertIn("Design References", bundle_readme.read_text(encoding="utf-8"))
        self.assertIn("state matrix/fixture", bundle_readme.read_text(encoding="utf-8"))
        self.assertIn("UI Planning Packet", pending_readme.read_text(encoding="utf-8"))
        self.assertIn("Design References", pending_readme.read_text(encoding="utf-8"))
        self.assertIn("state matrix/fixture", pending_readme.read_text(encoding="utf-8"))

    def test_ui_first_fixtures_include_reference_pack_artifacts(self) -> None:
        self.assertReferenceManifestFixture(
            REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-bundle-task"
        )
        self.assertReferenceManifestFixture(
            REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-pending-bootstrap-task"
        )

    def test_task_bundle_execution_topology_constants(self) -> None:
        self.assertEqual(
            set(TASK_BUNDLE_EXECUTION_TOPOLOGIES),
            {"keep-local", "csv-fanout", "hybrid"},
        )
        self.assertEqual(
            set(TASK_BUNDLE_CSV_FANOUT_DOCS),
            {"GLOBAL_CONTEXT.md", "MERGE_POLICY.md"},
        )
        self.assertIn("row_unit", TASK_BUNDLE_CSV_FANOUT_ORCHESTRATION_REQUIRED_KEYS)
        self.assertIn("csv", TASK_BUNDLE_CSV_FANOUT_ORCHESTRATION_REQUIRED_KEYS)
        self.assertIn("merge_policy", TASK_BUNDLE_CSV_FANOUT_ORCHESTRATION_REQUIRED_KEYS)

    def test_fixture_csv_fanout_task_bundle_contract(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-csv-fanout-task"
        errors = validate_task_bundle_root(fixture_root)
        self.assertEqual([], errors, msg="\n".join(errors))

    def test_csv_fanout_fixture_has_orchestration_block(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-csv-fanout-task"
        manifest = load_task_bundle_manifest(fixture_root / "task.yaml")
        self.assertEqual("csv-fanout", manifest.execution_topology)
        self.assertIsNotNone(manifest.orchestration)
        self.assertIn("row_unit", manifest.orchestration)
        self.assertIn("csv", manifest.orchestration)
        self.assertIn("merge_policy", manifest.orchestration)
        self.assertIn("GLOBAL_CONTEXT.md", manifest.required_docs)
        self.assertIn("MERGE_POLICY.md", manifest.required_docs)

    def test_design_task_documents_csv_fanout_contract(self) -> None:
        skill_content = (REPO_ROOT / "skills" / "design-task" / "SKILL.md").read_text(encoding="utf-8")
        reference_content = (
            REPO_ROOT / "skills" / "design-task" / "references" / "task-bundle-rules.md"
        ).read_text(encoding="utf-8")

        self.assertIn("execution_topology", skill_content)
        self.assertIn("csv-fanout", skill_content)
        self.assertIn("GLOBAL_CONTEXT.md", skill_content)
        self.assertIn("MERGE_POLICY.md", skill_content)
        self.assertIn("orchestration", skill_content)
        self.assertIn("integrator", skill_content)
        self.assertIn("Execution Topologies", reference_content)
        self.assertIn("GLOBAL_CONTEXT.md", reference_content)
        self.assertIn("WORK_ITEMS.csv", reference_content)
        self.assertIn("MERGE_POLICY.md", reference_content)

    def test_implement_task_documents_csv_fanout_contract(self) -> None:
        skill_content = (REPO_ROOT / "skills" / "implement-task" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("execution_topology", skill_content)
        self.assertIn("csv-fanout", skill_content)
        self.assertIn("keep-local fallback", skill_content)
        self.assertIn("spawn_agents_on_csv", skill_content)
        self.assertIn("GLOBAL_CONTEXT.md", skill_content)
        self.assertIn("MERGE_POLICY.md", skill_content)

    def test_csv_fanout_continuity_reference_documented(self) -> None:
        reference_path = REPO_ROOT / "skills" / "design-task" / "references" / "plan-continuity-rules.md"
        reference_content = reference_path.read_text(encoding="utf-8")

        self.assertIn("Row-level Continuity", reference_content)
        self.assertIn("execution_topology", reference_content)
        self.assertIn("skip", reference_content)
        self.assertIn("re-execute", reference_content)
        self.assertIn("append", reference_content)
        self.assertIn("superseded", reference_content)

    def test_derive_csv_fanout_docs_function(self) -> None:
        self.assertEqual(TASK_BUNDLE_CSV_FANOUT_DOCS, derive_csv_fanout_docs("csv-fanout"))
        self.assertEqual(tuple(TASK_BUNDLE_CSV_FANOUT_DOCS), derive_csv_fanout_docs("hybrid"))
        self.assertEqual(tuple(), derive_csv_fanout_docs("keep-local"))

    def test_existing_fixture_without_execution_topology_still_passes(self) -> None:
        fixture_root = REPO_ROOT / "tests" / "fixtures" / "tasks" / "sample-bundle-task"
        manifest = load_task_bundle_manifest(fixture_root / "task.yaml")
        self.assertEqual("keep-local", manifest.execution_topology)
        self.assertIsNone(manifest.orchestration)
        errors = validate_task_bundle_root(fixture_root)
        self.assertEqual([], errors, msg="\n".join(errors))
