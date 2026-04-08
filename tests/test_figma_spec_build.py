from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from support import REPO_ROOT


_SKILL_ROOT = REPO_ROOT / "skills" / "figma-spec-build"
_SCRIPTS = _SKILL_ROOT / "scripts"
_FIXTURES = _SKILL_ROOT / "tests" / "fixtures"


def _load(module_name: str, filename: str):
    path = _SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


parse_url = _load("figma_spec_parse_url", "parse_url.py")
find_description_nodes = _load("figma_spec_find_descs", "find_description_nodes.py")
jsx_to_spec = _load("figma_spec_jsx_to_spec", "jsx_to_spec.py")
suggest_mappings = _load("figma_spec_suggest", "suggest_mappings.py")


class ParseUrlTests(unittest.TestCase):
    def test_standard_design_url(self) -> None:
        result = parse_url.parse_figma_url(
            "https://www.figma.com/design/ABC123/My_File?node-id=12-34&m=dev"
        )
        self.assertEqual(result["fileKey"], "ABC123")
        self.assertEqual(result["nodeId"], "12:34")
        self.assertEqual(result["fileName"], "My_File")

    def test_branch_url_uses_branch_key(self) -> None:
        result = parse_url.parse_figma_url(
            "https://www.figma.com/design/MAIN/branch/BRANCH/File?node-id=1-2"
        )
        self.assertEqual(result["fileKey"], "BRANCH")
        self.assertEqual(result["nodeId"], "1:2")

    def test_make_url(self) -> None:
        result = parse_url.parse_figma_url(
            "https://www.figma.com/make/MK123/Proto?node-id=5-6"
        )
        self.assertEqual(result["fileKey"], "MK123")
        self.assertEqual(result["nodeId"], "5:6")

    def test_board_url_rejected(self) -> None:
        with self.assertRaises(parse_url.UrlParseError):
            parse_url.parse_figma_url(
                "https://www.figma.com/board/XYZ/Board?node-id=1-2"
            )

    def test_missing_node_id_rejected(self) -> None:
        with self.assertRaises(parse_url.UrlParseError):
            parse_url.parse_figma_url("https://www.figma.com/design/ABC/File")

    def test_non_figma_host_rejected(self) -> None:
        with self.assertRaises(parse_url.UrlParseError):
            parse_url.parse_figma_url(
                "https://example.com/design/ABC/File?node-id=1-2"
            )


class FindDescriptionNodesTests(unittest.TestCase):
    def test_primary_name_match(self) -> None:
        xml = """<frame id="1:1" name="Screen" x="0" y="0" width="2400" height="1000">
            <frame id="1:2" name="Content" x="0" y="0" width="1920" height="1000">
                <text id="1:3" name="Body" x="0" y="0" width="100" height="20" />
            </frame>
            <frame id="1:4" name="Description" x="1920" y="0" width="400" height="1000">
                <text id="1:5" name="Description" x="0" y="0" width="100" height="20" />
            </frame>
        </frame>"""
        results = find_description_nodes.find_description_nodes(xml)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["node_id"], "1:4")
        self.assertEqual(results[0]["parent_node_id"], "1:1")
        self.assertEqual(results[0]["match"], "name")

    def test_fallback_x_position_with_description_text(self) -> None:
        xml = """<frame id="2:1" name="Screen" x="0" y="0" width="2400" height="1000">
            <frame id="2:2" name="설명" x="1920" y="0" width="400" height="1000">
                <text id="2:3" name="Description" x="0" y="0" width="100" height="20" />
            </frame>
        </frame>"""
        results = find_description_nodes.find_description_nodes(xml)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["node_id"], "2:2")
        self.assertEqual(results[0]["match"], "fallback")

    def test_strips_control_chars(self) -> None:
        # Figma occasionally embeds \x08 in layer names
        xml = """<frame id="3:1" name="Screen" x="0" y="0" width="100" height="100">
            <frame id="3:2" name="\x08Description" x="1920" y="0" width="100" height="100" />
        </frame>"""
        # Should not raise — control char must be stripped
        results = find_description_nodes.find_description_nodes(xml)
        # After strip, name becomes "Description" so primary match
        self.assertEqual(len(results), 1)


class JsxToSpecTests(unittest.TestCase):
    def test_sample_description(self) -> None:
        fixture = (_FIXTURES / "sample_description.jsx").read_text(encoding="utf-8")
        output = jsx_to_spec.jsx_to_spec(fixture)

        # Structural assertions (values-agnostic beyond what the fixture requires)
        self.assertIn("## 1.", output)
        self.assertIn("## 2.", output)
        self.assertIn("### [", output)
        self.assertIn("- ", output)
        # Nested bullet indentation
        self.assertIn("  - ", output)
        # JSX template literal should be stripped
        self.assertNotIn("{`", output)
        self.assertNotIn("`}", output)
        # Header "Description" should be skipped
        self.assertNotIn("Description\n\n##", output)

    def test_section_count(self) -> None:
        fixture = (_FIXTURES / "sample_description.jsx").read_text(encoding="utf-8")
        output = jsx_to_spec.jsx_to_spec(fixture)
        # Count ## headers
        section_count = sum(1 for line in output.splitlines() if line.startswith("## "))
        self.assertEqual(section_count, 2)


class SuggestMappingsTests(unittest.TestCase):
    def test_title_match_scores_highest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src" / "components").mkdir(parents=True)
            (repo / "src" / "components" / "DateDropdown.tsx").write_text(
                "export const DateDropdown = () => null;"
            )
            (repo / "src" / "components" / "Unrelated.tsx").write_text(
                "export const Unrelated = () => null;"
            )

            spec_path = repo / "spec.md"
            spec_path.write_text(
                "## 1. Date 설정 드롭다운\n\n"
                "### [Date interval]\n"
                "- rule one\n"
            )

            results = suggest_mappings.suggest_mappings(spec_path, repo, top_n=5)
            self.assertEqual(len(results), 1)
            candidates = results[0]["candidates"]
            self.assertTrue(candidates, "expected at least one candidate")
            self.assertIn("DateDropdown", candidates[0]["path"])

    def test_excludes_test_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src" / "Button.tsx").write_text("export const Button = () => null;")
            (repo / "src" / "Button.test.tsx").write_text("import Button from './Button';")

            spec_path = repo / "spec.md"
            spec_path.write_text("## 1. Button 영역\n\n- click\n")

            results = suggest_mappings.suggest_mappings(spec_path, repo, top_n=5)
            paths = [c["path"] for c in results[0]["candidates"]]
            self.assertFalse(any(".test." in p for p in paths))


if __name__ == "__main__":
    unittest.main()
