from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from support import REPO_ROOT, RepoTestCase


def _load_project_context_module():
    module_name = "gitlab_issue_creator_project_context"
    module_path = (
        REPO_ROOT
        / "skills"
        / "gitlab-issue-creator"
        / "scripts"
        / "project_context.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


project_context = _load_project_context_module()


class GitlabIssueCreatorTests(RepoTestCase):
    def test_parse_repo_ref_accepts_shorthand(self) -> None:
        target = project_context.parse_repo_ref(
            "group/subgroup/project",
            default_host="gitlab.example.com",
        )

        self.assertEqual(target.host, "gitlab.example.com")
        self.assertEqual(target.project_path, "group/subgroup/project")
        self.assertEqual(target.project_path_encoded, "group%2Fsubgroup%2Fproject")

    def test_parse_repo_ref_accepts_https_url(self) -> None:
        target = project_context.parse_repo_ref(
            "https://gitlab.com/team/project.git",
            default_host="gitlab.example.com",
        )

        self.assertEqual(target.host, "gitlab.com")
        self.assertEqual(target.project_path, "team/project")

    def test_parse_repo_ref_accepts_git_ssh_url(self) -> None:
        target = project_context.parse_repo_ref(
            "git@gitlab.exem.xyz:platform/api.git",
            default_host="gitlab.com",
        )

        self.assertEqual(target.host, "gitlab.exem.xyz")
        self.assertEqual(target.project_path, "platform/api")

    def test_resolve_target_from_remote_lines_uses_single_gitlab_remote(self) -> None:
        remote_lines = "\n".join(
            [
                "origin https://github.com/example/repo.git (fetch)",
                "origin https://github.com/example/repo.git (push)",
                "mirror git@gitlab.exem.xyz:platform/api.git (fetch)",
                "mirror git@gitlab.exem.xyz:platform/api.git (push)",
            ]
        )

        target = project_context.resolve_target_from_remote_lines(
            remote_lines,
            default_host="gitlab.com",
        )

        self.assertEqual(target.host, "gitlab.exem.xyz")
        self.assertEqual(target.project_path, "platform/api")
        self.assertEqual(target.source, "git_remote:mirror")

    def test_resolve_target_from_remote_lines_rejects_multiple_gitlab_remotes(self) -> None:
        remote_lines = "\n".join(
            [
                "origin git@gitlab.com:group/one.git (fetch)",
                "upstream git@gitlab.exem.xyz:group/two.git (fetch)",
            ]
        )

        with self.assertRaises(project_context.ResolutionError):
            project_context.resolve_target_from_remote_lines(
                remote_lines,
                default_host="gitlab.com",
            )

    def test_resolve_target_from_remote_lines_rejects_github_only_remotes(self) -> None:
        remote_lines = "\n".join(
            [
                "origin https://github.com/example/repo.git (fetch)",
                "origin https://github.com/example/repo.git (push)",
            ]
        )

        with self.assertRaises(project_context.ResolutionError):
            project_context.resolve_target_from_remote_lines(
                remote_lines,
                default_host="gitlab.com",
            )
