from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from support import REPO_ROOT, RepoTestCase

MODULE_PATH = REPO_ROOT / "skills" / "_shared" / "scripts" / "review_hotspots.py"


def _load_review_hotspots_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("review_hotspots", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"failed to load module spec for {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReviewHotspotsTests(RepoTestCase):
    def test_load_hotspot_policy_returns_positive_thresholds(self) -> None:
        module = _load_review_hotspots_module()
        loaded = module.load_hotspot_policy(REPO_ROOT)

        self.assertIsInstance(loaded.min_changed_files, int)
        self.assertGreater(loaded.min_changed_files, 0)
        self.assertIsInstance(loaded.min_total_diff_loc, int)
        self.assertGreater(loaded.min_total_diff_loc, 0)
        self.assertIsInstance(loaded.max_hotspot_paths, int)
        self.assertGreater(loaded.max_hotspot_paths, 0)

    def test_classifier_stays_diff_only_below_threshold(self) -> None:
        module = _load_review_hotspots_module()
        changes = [
            module.FileChange(path="src/alpha.py", added=40, deleted=10),
            module.FileChange(path="src/beta.py", added=30, deleted=20),
        ]

        result = module.classify_review_scope(changes)

        self.assertEqual(result["review_mode"], "diff-only")
        self.assertEqual(result["hotspot_paths"], [])
        self.assertEqual(result["overflow_hotspot_paths"], [])
        self.assertEqual(result["maintainability_reasons"], [])

    def test_classifier_upgrades_to_hotspot_review(self) -> None:
        module = _load_review_hotspots_module()
        changes = [
            module.FileChange(path="src/alpha.py", added=70, deleted=20),
            module.FileChange(path="src/beta.py", added=40, deleted=15),
            module.FileChange(path="README.md", added=10, deleted=0),
        ]

        result = module.classify_review_scope(changes)

        self.assertEqual(result["review_mode"], "diff+full-file-hotspots")
        self.assertEqual(
            result["hotspot_paths"],
            ["src/alpha.py", "src/beta.py", "README.md"],
        )
        self.assertEqual(result["overflow_hotspot_paths"], [])
        self.assertGreaterEqual(len(result["maintainability_reasons"]), 2)

    def test_classifier_caps_hotspots_and_reports_overflow(self) -> None:
        module = _load_review_hotspots_module()
        changes = [
            module.FileChange(path="src/alpha.py", added=90, deleted=0),
            module.FileChange(path="src/beta.py", added=80, deleted=0),
            module.FileChange(path="src/gamma.py", added=70, deleted=0),
            module.FileChange(path="src/delta.py", added=60, deleted=0),
        ]

        result = module.classify_review_scope(changes)

        self.assertEqual(result["review_mode"], "diff+full-file-hotspots")
        self.assertEqual(
            result["hotspot_paths"],
            ["src/alpha.py", "src/beta.py", "src/gamma.py"],
        )
        self.assertEqual(result["overflow_hotspot_paths"], ["src/delta.py"])
        self.assertIn("omitted by cap", " ".join(result["maintainability_reasons"]))

    def test_classifier_ignores_lockfiles_for_hotspot_thresholds(self) -> None:
        module = _load_review_hotspots_module()
        changes = [
            module.FileChange(path="package-lock.json", added=300, deleted=0),
            module.FileChange(path="src/alpha.py", added=40, deleted=10),
            module.FileChange(path="src/beta.py", added=30, deleted=20),
        ]

        result = module.classify_review_scope(changes)

        self.assertEqual(result["review_mode"], "diff-only")
        self.assertEqual(result["hotspot_paths"], [])
