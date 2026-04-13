from __future__ import annotations

import argparse
import json
import tempfile
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from support import REPO_ROOT, RepoTestCase
from hyperagent import analyze_sessions
from hyperagent import apply as hyper_apply
from hyperagent import archive, evolve, generate_variant, score
from validate_workflow_contracts import validate_repo


class HyperAgentTests(RepoTestCase):
    def _write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _sample_analysis_report(self) -> dict[str, object]:
        return {
            "schema_version": "1",
            "generated_at": "2026-04-13T00:00:00Z",
            "sessions_analyzed": 2,
            "sessions_skipped": 0,
            "date_range": {"start": "2026-04-10", "end": "2026-04-11"},
            "signals": {
                "by_session": [
                    {
                        "session_id": "s-negative",
                        "timestamp": "2026-04-10T00:00:00Z",
                        "turn_count": 4,
                        "user_corrections": 2,
                        "repeated_instructions": 1,
                        "positive_feedback": 0,
                        "tool_failures": [{"tool": "Bash", "count": 1}],
                        "skill_invocations": [{"skill": "commit", "count": 1}],
                        "agent_dispatches": [{"agent": "verification-worker", "count": 2}],
                        "complexity": {"score": 0.0, "negative_signal_weight_factor": 1.0},
                    },
                    {
                        "session_id": "s-positive",
                        "timestamp": "2026-04-11T00:00:00Z",
                        "turn_count": 4,
                        "user_corrections": 0,
                        "repeated_instructions": 0,
                        "positive_feedback": 1,
                        "tool_failures": [],
                        "skill_invocations": [{"skill": "commit", "count": 1}],
                        "agent_dispatches": [{"agent": "verification-worker", "count": 1}],
                        "complexity": {"score": 0.0, "negative_signal_weight_factor": 1.0},
                    },
                ],
                "aggregated": {},
            },
        }

    def _variant_meta(self, *, entity_type: str, entity_id: str, source_path: str, variant_id: str = "v-test") -> dict[str, object]:
        return {
            "schema_version": "1",
            "variant_id": variant_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "strategy": "refine",
            "source_path": source_path,
            "original_path": source_path,
            "source_score": 0.42,
            "created_at": "2026-04-13T00:00:00Z",
            "files_modified": [Path(source_path).name],
            "suggestions_applied": ["accuracy"],
            "evidence_sessions": ["s-negative"],
            "status": "staged",
        }

    def test_hyperagent_policy_matches_nfr_caps(self) -> None:
        policy = tomllib.loads((REPO_ROOT / "policy" / "hyperagent.toml").read_text(encoding="utf-8"))

        self.assertEqual(policy["trigger"]["mode"], "daily-cron")
        self.assertEqual(policy["cost_budget"]["hard_cap_usd_per_cycle"], 5.0)
        self.assertEqual(policy["cost_budget"]["monthly_budget_usd"], 30.0)
        self.assertEqual(policy["variant_limits"]["max_active_per_entity"], 5)
        self.assertEqual(policy["variant_limits"]["max_total"], 50)
        self.assertEqual(policy["trigger"]["max_targets_per_cycle"], 1)
        self.assertEqual(policy["trigger"]["cycle_timeout_seconds"], 600)
        self.assertEqual(policy["scoring"]["decay_half_life_days"], 7)
        self.assertEqual(policy["scoring"]["baseline_min_sessions"], 5)
        self.assertEqual(policy["paths"]["archive"], "scripts/hyperagent/archive.jsonl")

    def test_analyze_sessions_extracts_fixture_signals(self) -> None:
        rows = [
            {
                "type": "user",
                "sessionId": "s1",
                "timestamp": "2026-04-13T00:00:00Z",
                "message": {"content": "please run $commit for tests/test_hyperagent.py"},
            },
            {
                "type": "assistant",
                "sessionId": "s1",
                "timestamp": "2026-04-13T00:01:00Z",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "toolu_1",
                            "name": "Bash",
                            "input": {"cmd": "pytest tests/test_hyperagent.py"},
                        }
                    ]
                },
            },
            {
                "type": "user",
                "sessionId": "s1",
                "timestamp": "2026-04-13T00:02:00Z",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "toolu_1",
                            "is_error": True,
                            "content": "Error: failed",
                        }
                    ]
                },
            },
            {
                "type": "user",
                "sessionId": "s1",
                "timestamp": "2026-04-13T00:03:00Z",
                "message": {"content": "아니 그게 아니라 tests/test_hyperagent.py 다시 해줘"},
            },
            {
                "type": "user",
                "sessionId": "s1",
                "timestamp": "2026-04-13T00:04:00Z",
                "message": {"content": "원래대로 다시 해줘"},
            },
            {
                "type": "user",
                "sessionId": "s1",
                "timestamp": "2026-04-13T00:05:00Z",
                "message": {"content": "좋아 perfect thanks"},
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "project" / "session.jsonl"
            self._write_text(session_path, "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")
            with patch.object(analyze_sessions, "KNOWN_SKILLS", {"commit"}):
                messages, skipped = analyze_sessions.parse_jsonl(session_path)
                analysis = analyze_sessions.analyze_session(session_path, messages)

        self.assertEqual(skipped, 0)
        self.assertIsNotNone(analysis)
        assert analysis is not None
        self.assertEqual(analysis.turn_count, 4)
        self.assertEqual(analysis.user_corrections, 2)
        self.assertEqual(analysis.repeated_instructions, 1)
        self.assertEqual(analysis.positive_feedback, 1)
        self.assertEqual(analysis.skill_invocations["commit"], 1)
        self.assertEqual(analysis.tool_failures["Bash"], 1)

    def test_analyze_report_aggregates_entity_breakdowns(self) -> None:
        analysis = analyze_sessions.SessionAnalysis(
            session_id="s1",
            project="project",
            timestamp=datetime(2026, 4, 13, tzinfo=timezone.utc),
            turn_count=2,
            session_duration_seconds=60,
            user_corrections=1,
            repeated_instructions=0,
            tool_failures=analyze_sessions.Counter({"Bash": 2}),
            tool_failure_patterns=analyze_sessions.Counter({("Bash", "error"): 2}),
            positive_feedback=1,
            skill_invocations=analyze_sessions.Counter({"commit": 2}),
            agent_dispatches=analyze_sessions.Counter({"verification-worker": 1}),
            tool_count=4,
            unique_tools={"Bash"},
            files_touched={"tests/test_hyperagent.py"},
            branch_switches=0,
            complexity={"grade": "simple", "score": 0.1},
        )

        report = analyze_sessions.build_report([analysis], sessions_skipped=0, date_range=("2026-04-13", "2026-04-13"))
        aggregated = report["signals"]["aggregated"]

        self.assertEqual(aggregated["total_tool_failures"], 2)
        self.assertEqual(aggregated["top_skills_by_usage"][0]["skill"], "commit")
        self.assertEqual(aggregated["top_agents_by_dispatch"][0]["agent"], "verification-worker")
        self.assertEqual(aggregated["by_skill"][0]["correction_rate"], 0.5)

    def test_score_builds_samples_for_skill_agent_and_orchestration(self) -> None:
        report = self._sample_analysis_report()
        samples = score.build_samples(report)
        sample_keys = {(sample.entity_type, sample.entity_id) for sample in samples}

        self.assertIn(("skill", "commit"), sample_keys)
        self.assertIn(("agent", "verification-worker"), sample_keys)
        self.assertIn(("orchestration", "global"), sample_keys)

    def test_score_generates_improvement_for_weak_entity(self) -> None:
        report = self._sample_analysis_report()
        samples = score.build_samples(report)
        scores = score.aggregate_entity_scores(
            samples,
            baseline_data={"entities": {}},
            reference_time=datetime(2026, 4, 13, tzinfo=timezone.utc),
            half_life_days=7,
            trend_threshold=0.15,
        )
        improvements = score.improvements_from_scores(scores)

        self.assertTrue(improvements)
        self.assertEqual(improvements[0]["priority"], "high")
        self.assertIn(improvements[0]["entity_type"], {"agent", "skill", "orchestration"})
        self.assertIn("evidence_sessions", improvements[0])

    def test_score_creates_baseline_after_minimum_sessions(self) -> None:
        report = self._sample_analysis_report()
        sessions = report["signals"]["by_session"]
        report["signals"]["by_session"] = [
            {**sessions[1], "session_id": f"s-baseline-{index}", "timestamp": f"2026-04-{index + 1:02d}T00:00:00Z"}
            for index in range(5)
        ]
        samples = score.build_samples(report)

        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline.json"
            data, status = score.load_or_create_baseline(
                baseline_path,
                samples,
                min_sessions=5,
                half_life_days=7,
                trend_threshold=0.15,
            )

            self.assertTrue(baseline_path.exists())
            self.assertTrue(status["created"])
            self.assertIn("skill:commit", data["entities"])

    def test_generate_variant_writes_payload_and_meta(self) -> None:
        improvement = generate_variant.Improvement(
            entity_type="agent",
            entity_id="verification-worker",
            score=0.42,
            priority="high",
            reason="accuracy",
            suggestion="Require stronger evidence before conclusions.",
            target="agent-registry/verification-worker/instructions.md",
            trend={"direction": "degrading"},
            baseline_delta=-0.2,
            evidence_sessions=["s-negative"],
            rank=1,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            registry = root / "agent-registry"
            skills = root / "skills"
            output_dir = root / "variants"
            self._write_text(registry / "verification-worker" / "instructions.md", "base instructions\n")

            plans = generate_variant.build_variant_plans([improvement], registry, skills, output_dir)
            result = generate_variant.execute_plan(plans[0], "2026-04-13T00:00:00Z", "score-report.json", False)

            meta = json.loads(plans[0].meta_path.read_text(encoding="utf-8"))
            payload = plans[0].output_path.read_text(encoding="utf-8")

        self.assertTrue(result["written"])
        self.assertEqual(meta["schema_version"], "1")
        self.assertEqual(meta["entity_id"], "verification-worker")
        self.assertIn("HyperAgent variant patch", payload)
        self.assertIn("Require stronger evidence", payload)

    def test_generate_variant_selects_target_alias_and_respects_limit(self) -> None:
        improvements = [
            generate_variant.Improvement("agent", "verification-worker", 0.4, "high", "accuracy", "Fix it", None, None, None, [], 1),
            generate_variant.Improvement("skill", "commit", 0.6, "medium", "completion_rate", "Fix commit", None, None, None, [], 2),
        ]

        selected = generate_variant.select_improvements(improvements, "agent:verification-worker", max_variants=1)
        limited = generate_variant.select_improvements(improvements, None, max_variants=1)

        self.assertEqual([item.entity_id for item in selected], ["verification-worker"])
        self.assertEqual(len(limited), 1)

    def test_archive_materializes_status_changes_and_prunes_limits(self) -> None:
        events = [
            {"event_type": "add", "variant_id": "v1", "entity_id": "agent-a", "entity_type": "agent", "score": 0.9},
            {"event_type": "add", "variant_id": "v2", "entity_id": "agent-a", "entity_type": "agent", "score": 0.8},
            {"event_type": "add", "variant_id": "v3", "entity_id": "agent-a", "entity_type": "agent", "score": 0.7},
            {"event_type": "add", "variant_id": "v4", "entity_id": "agent-a", "entity_type": "agent", "score": 0.1, "status": "applied"},
            {"event_type": "status_change", "variant_id": "v2", "new_status": "rejected"},
        ]

        records = archive.materialize_records(events)
        rejected = next(record for record in records if record["variant_id"] == "v2")
        candidates = archive.prune_candidates(records, max_per_entity=2, max_total=50, min_score=None)
        candidate_ids = {record["variant_id"] for record in candidates}

        self.assertEqual(rejected["status"], "rejected")
        self.assertIn("v3", candidate_ids)
        self.assertNotIn("v4", candidate_ids)

    def test_archive_selects_best_record(self) -> None:
        records = [
            {"variant_id": "low", "entity_id": "agent-a", "score": 0.2, "created_at": "2026-04-12T00:00:00Z"},
            {"variant_id": "high", "entity_id": "agent-a", "score": 0.9, "created_at": "2026-04-11T00:00:00Z"},
        ]

        ordered = archive.sort_best_first(records)

        self.assertEqual(ordered[0]["variant_id"], "high")

    def test_apply_build_plan_marks_missing_target_as_tier3_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            variant_dir = repo_root / "scripts" / "hyperagent" / "variants" / "new-skill" / "v-test"
            self._write_text(variant_dir / "meta.json", json.dumps(self._variant_meta(entity_type="skill", entity_id="new-skill", source_path="skills/new-skill/SKILL.md")) + "\n")
            self._write_text(variant_dir / "SKILL.md", "# New skill\n")
            args = argparse.Namespace(from_archive=False, entity=None, variant_dir=str(variant_dir), approve=False, dry_run=True)

            with patch.object(hyper_apply, "REPO_ROOT", repo_root), patch.object(
                hyper_apply,
                "PROPOSALS_DIR",
                repo_root / "scripts" / "hyperagent" / "proposals",
            ):
                plan = hyper_apply.build_plan(args)

        self.assertEqual(plan["tier"], 3)
        self.assertEqual(plan["action"], "pending")
        self.assertEqual(plan["target_path"], "skills/new-skill/SKILL.md")

    def test_apply_build_plan_marks_existing_agent_as_tier1_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            target = repo_root / "agent-registry" / "verification-worker" / "instructions.md"
            variant_dir = repo_root / "scripts" / "hyperagent" / "variants" / "verification-worker" / "v-test"
            self._write_text(target, "old instructions\n")
            self._write_text(variant_dir / "instructions.md", "new instructions\n")
            self._write_text(
                variant_dir / "meta.json",
                json.dumps(
                    self._variant_meta(
                        entity_type="agent",
                        entity_id="verification-worker",
                        source_path="agent-registry/verification-worker/instructions.md",
                    )
                )
                + "\n",
            )
            args = argparse.Namespace(from_archive=False, entity=None, variant_dir=str(variant_dir), approve=False, dry_run=True)

            with patch.object(hyper_apply, "REPO_ROOT", repo_root):
                plan = hyper_apply.build_plan(args)

        self.assertEqual(plan["tier"], 1)
        self.assertEqual(plan["action"], "apply")
        self.assertIn(["git", "add", "agent-registry/verification-worker/instructions.md"], plan["commands"])

    def test_evolve_simulates_archive_and_apply_outputs(self) -> None:
        variants = [
            {
                "variant_id": "v1",
                "entity_type": "agent",
                "entity_id": "verification-worker",
                "variant_dir": "scripts/hyperagent/variants/verification-worker/v1",
                "variant_file": "scripts/hyperagent/variants/verification-worker/v1/instructions.md",
                "meta_file": "scripts/hyperagent/variants/verification-worker/v1/meta.json",
                "source_path": "agent-registry/verification-worker/instructions.md",
                "score": 0.4,
                "suggestion": "Improve evidence checks.",
            }
        ]

        archive_step, archive_output = evolve.simulate_archive(variants)
        apply_step, apply_output = evolve.simulate_apply(variants)

        self.assertTrue(archive_step["simulated"])
        self.assertEqual(archive_output["record_count"], 1)
        self.assertTrue(apply_step["simulated"])
        self.assertEqual(apply_output["plans"][0]["status"], "planned")

    def test_evolve_rejects_invalid_json_step_output(self) -> None:
        with self.assertRaises(evolve.PipelineError):
            evolve.parse_json_output("score", "[]")

    def test_validate_workflow_contracts_checks_hyperagent_surface_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._write_text(repo_root / "policy" / "workflow.toml", "[public_surface]\nlong_running = []\n")
            self._write_text(repo_root / "policy" / "hyperagent.toml", "[trigger\n")
            self._write_text(repo_root / "skills" / "manifest.json", json.dumps({"skills": []}) + "\n")
            self._write_text(
                repo_root / "skills" / "demo" / "SKILL.md",
                "---\nname: demo\ndescription: Demo\n---\n\n# Demo\n",
            )
            (repo_root / "scripts" / "hyperagent").mkdir(parents=True)

            errors = validate_repo(repo_root, run_sync_checks=False)

        self.assertTrue(any("invalid TOML" in error and "hyperagent.toml" in error for error in errors))
        self.assertTrue(any("missing hyperagent script" in error for error in errors))
