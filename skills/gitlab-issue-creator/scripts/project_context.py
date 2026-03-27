#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse


class ResolutionError(ValueError):
    """Raised when the GitLab target cannot be resolved safely."""


@dataclass(frozen=True)
class RepoTarget:
    host: str
    project_path: str
    source: str

    @property
    def project_path_encoded(self) -> str:
        return quote(self.project_path, safe="")


def _normalize_project_path(value: str) -> str:
    normalized = value.strip().strip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    normalized = normalized.strip("/")
    if not normalized or "/" not in normalized:
        raise ResolutionError(f"invalid GitLab project path: {value!r}")
    return normalized


def read_default_host() -> str:
    completed = subprocess.run(
        ["glab", "config", "get", "host"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 0 and completed.stdout.strip():
        return completed.stdout.strip()
    return "gitlab.com"


def parse_repo_ref(
    value: str,
    *,
    default_host: str,
    source: str = "explicit",
) -> RepoTarget:
    raw = value.strip()
    if not raw:
        raise ResolutionError("empty repo reference")

    parsed = urlparse(raw)
    if parsed.scheme and parsed.hostname:
        return RepoTarget(
            host=parsed.hostname,
            project_path=_normalize_project_path(parsed.path),
            source=source,
        )

    ssh_url = re.match(r"^(?:.+@)?(?P<host>[^:]+):(?P<path>.+)$", raw)
    if ssh_url is not None and "/" in ssh_url.group("path"):
        return RepoTarget(
            host=ssh_url.group("host"),
            project_path=_normalize_project_path(ssh_url.group("path")),
            source=source,
        )

    return RepoTarget(
        host=default_host,
        project_path=_normalize_project_path(raw),
        source=source,
    )


_REMOTE_LINE_RE = re.compile(
    r"^(?P<name>\S+)\s+(?P<url>\S+)\s+\((?P<kind>fetch|push)\)$"
)


def _looks_like_gitlab_host(host: str, *, default_host: str) -> bool:
    lowered = host.lower()
    return lowered == default_host.lower() or "gitlab" in lowered


def resolve_target_from_remote_lines(
    remote_lines: str,
    *,
    default_host: str,
) -> RepoTarget:
    candidates: dict[tuple[str, str], RepoTarget] = {}

    for line in remote_lines.splitlines():
        match = _REMOTE_LINE_RE.match(line.strip())
        if match is None or match.group("kind") != "fetch":
            continue

        parsed = parse_repo_ref(
            match.group("url"),
            default_host=default_host,
            source=f"git_remote:{match.group('name')}",
        )
        if not _looks_like_gitlab_host(parsed.host, default_host=default_host):
            continue
        candidates[(parsed.host, parsed.project_path)] = parsed

    if not candidates:
        raise ResolutionError(
            "no GitLab remote found; pass --repo <group/project> or a full GitLab URL"
        )
    if len(candidates) > 1:
        choices = ", ".join(
            f"{host}/{path}" for host, path in sorted(candidates.keys())
        )
        raise ResolutionError(
            "multiple GitLab remotes found; pass --repo explicitly: " + choices
        )
    return next(iter(candidates.values()))


def resolve_target(
    *,
    repo_ref: str | None,
    default_host: str,
    cwd: Path,
) -> RepoTarget:
    if repo_ref:
        return parse_repo_ref(repo_ref, default_host=default_host)

    completed = subprocess.run(
        ["git", "remote", "-v"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or "git remote -v failed"
        raise ResolutionError(stderr)

    return resolve_target_from_remote_lines(completed.stdout, default_host=default_host)


def _run_glab_api(target: RepoTarget, endpoint: str) -> Any:
    completed = subprocess.run(
        ["glab", "api", "--hostname", target.host, endpoint],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "glab api failed"
        raise RuntimeError(
            f"glab api failed for {target.host} ({endpoint}). "
            f"Run: glab auth login --hostname {target.host}\n{stderr}"
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON from glab api for {endpoint}: {exc}") from exc


def _run_optional_glab_api(target: RepoTarget, endpoint: str) -> Any:
    completed = subprocess.run(
        ["glab", "api", "--hostname", target.host, endpoint],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return []
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []


def _slim_project(project: dict[str, Any]) -> dict[str, Any]:
    namespace = project.get("namespace") or {}
    return {
        "id": project.get("id"),
        "name": project.get("name"),
        "name_with_namespace": project.get("name_with_namespace"),
        "path_with_namespace": project.get("path_with_namespace"),
        "web_url": project.get("web_url"),
        "issues_access_level": project.get("issues_access_level"),
        "issues_template": project.get("issues_template"),
        "namespace_full_path": namespace.get("full_path"),
    }


def _slim_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "name": user.get("name"),
        "state": user.get("state"),
        "web_url": user.get("web_url"),
    }


def _slim_label(label: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": label.get("id"),
        "name": label.get("name"),
        "description": label.get("description"),
        "color": label.get("color"),
        "priority": label.get("priority"),
        "archived": label.get("archived"),
    }


def _slim_milestone(milestone: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": milestone.get("id"),
        "iid": milestone.get("iid"),
        "title": milestone.get("title"),
        "description": milestone.get("description"),
        "state": milestone.get("state"),
        "start_date": milestone.get("start_date"),
        "due_date": milestone.get("due_date"),
        "web_url": milestone.get("web_url"),
    }


def _slim_issue_template(template: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": template.get("key") or template.get("name"),
        "name": template.get("name") or template.get("key"),
    }


def build_context(target: RepoTarget) -> dict[str, Any]:
    project = _run_glab_api(target, f"projects/{target.project_path_encoded}")
    current_user = _run_glab_api(target, "user")
    labels = _run_glab_api(
        target, f"projects/{target.project_path_encoded}/labels?per_page=100"
    )
    users = _run_glab_api(
        target, f"projects/{target.project_path_encoded}/users?per_page=100"
    )
    milestones = _run_glab_api(
        target,
        f"projects/{target.project_path_encoded}/milestones?state=active&per_page=100",
    )
    issue_templates = _run_optional_glab_api(
        target, f"projects/{target.project_path_encoded}/templates/issues"
    )

    web_url = project.get("web_url") or f"https://{target.host}/{target.project_path}"
    return {
        "target": {
            **asdict(target),
            "project_path_encoded": target.project_path_encoded,
            "repo_selector": web_url,
        },
        "project": _slim_project(project),
        "current_user": _slim_user(current_user),
        "labels": [_slim_label(label) for label in labels],
        "users": [_slim_user(user) for user in users],
        "milestones": [_slim_milestone(milestone) for milestone in milestones],
        "issue_templates": [
            _slim_issue_template(template)
            for template in issue_templates
            if isinstance(template, dict)
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve a GitLab repo target and fetch issue-creation metadata"
    )
    parser.add_argument("--repo", help="GitLab repo path, full URL, or Git SSH URL")
    parser.add_argument(
        "--hostname",
        help="Override default GitLab hostname for path-like repo refs",
    )
    parser.add_argument(
        "--cwd",
        default=".",
        help="Working directory for git remote detection",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation")
    args = parser.parse_args()

    default_host = args.hostname or read_default_host()
    cwd = Path(args.cwd).resolve()

    try:
        target = resolve_target(repo_ref=args.repo, default_host=default_host, cwd=cwd)
        payload = build_context(target)
    except (ResolutionError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, ensure_ascii=False, indent=args.indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
