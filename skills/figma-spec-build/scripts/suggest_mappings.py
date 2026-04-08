#!/usr/bin/env python3
"""Suggest codebase file candidates for each section in a spec markdown file.

Reads a spec markdown with H2 sections (## N. Title), extracts English nouns
plus translated Korean keywords, then runs ripgrep across the target repo to
score candidate files.

Usage:
    python3 suggest_mappings.py --spec specs/19030-97432.md --repo . [--top-n 5]

Output (stdout): JSON array:
    [
      {
        "section_id": "1",
        "title": "Date 설정 드롭다운",
        "search_terms": ["Date", "Dropdown", "Select"],
        "candidates": [
          {"path": "src/components/DateDropdown.tsx", "score": 0.82,
           "matched_terms": ["Date", "Dropdown"],
           "reason": "filename match: Dropdown, Date"}
        ]
      }
    ]

Exit codes:
    0 success (empty candidates list if no matches)
    1 spec file missing / repo invalid
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Korean -> English keyword hints. Small and extensible.
_KEYWORD_MAP: dict[str, list[str]] = {
    "드롭다운": ["Dropdown", "Select"],
    "드롭 다운": ["Dropdown", "Select"],
    "버튼": ["Button"],
    "차트": ["Chart"],
    "테이블": ["Table", "Grid"],
    "필터": ["Filter"],
    "랭킹": ["Rank", "Ranking", "Top"],
    "카드": ["Card"],
    "모달": ["Modal", "Dialog"],
    "팝업": ["Popup", "Dialog"],
    "툴팁": ["Tooltip"],
    "탭": ["Tab", "Tabs"],
    "배지": ["Badge", "Chip", "Tag"],
    "아이콘": ["Icon"],
    "검색": ["Search"],
    "로그인": ["Login", "Signin"],
    "로그아웃": ["Logout", "Signout"],
    "페이지네이션": ["Pagination", "Paginator"],
    "메뉴": ["Menu", "Nav"],
    "네비게이션": ["Nav", "Navigation", "Menu"],
    "사이드바": ["Sidebar", "Drawer"],
    "토글": ["Toggle", "Switch"],
    "체크박스": ["Checkbox"],
    "라디오": ["Radio"],
    "입력": ["Input", "Field"],
    "폼": ["Form"],
    "정보": ["Info"],
    "영역": ["Area", "Section", "Panel"],
    "상세": ["Detail"],
    "목록": ["List"],
    "조회": ["Query", "Search", "Fetch"],
    "설정": ["Setting", "Config"],
    "날짜": ["Date"],
    "기간": ["Period", "Range"],
    "시간": ["Time"],
    "진단": ["Diagnosis", "Diagnostic"],
    "즐겨찾기": ["Favorite", "Bookmark", "Star"],
    "경고": ["Alert", "Warning"],
    "알림": ["Notification", "Alert", "Toast"],
    "프로필": ["Profile"],
    "대시보드": ["Dashboard"],
    "통계": ["Stat", "Stats", "Metric"],
    "리포트": ["Report"],
    "그래프": ["Graph", "Chart"],
    "도넛": ["Donut", "Doughnut", "Pie"],
    "파이": ["Pie"],
    "바": ["Bar"],
    "라인": ["Line"],
    "레전드": ["Legend"],
    "퀵": ["Quick"],
    "액션": ["Action"],
    "좌측": ["Left"],
    "우측": ["Right"],
    "상단": ["Top", "Header"],
    "하단": ["Bottom", "Footer"],
    "헤더": ["Header"],
    "푸터": ["Footer"],
    "바디": ["Body", "Content"],
}
# Title terms get a 2x score multiplier (title is more specific than body).
_TITLE_BOOST = 2.0

_SECTION_RE = re.compile(r"^## (\d+)\.\s*(.+?)\s*$")
_ENGLISH_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9]{2,}\b")
_STOPWORDS = {
    "the", "and", "for", "from", "with", "this", "that", "are", "was",
    "will", "can", "into", "over", "under", "your", "you", "has", "have",
    "SQL",  # usually too broad
}
_TEST_PATH_RE = re.compile(
    r"(__tests__|\.test\.|\.spec\.|\.stories\.|/node_modules/|/dist/|/build/|/\.next/|/\.git/)"
)

_FE_EXTENSIONS = {".ts", ".tsx", ".jsx", ".js", ".vue", ".svelte"}
_EXCLUDE_DIRS = {"node_modules", "dist", "build", ".next", ".git", ".turbo", "coverage"}


def _iter_source_files(repo: Path):
    """Yield source file paths under repo, skipping excluded directories."""
    stack = [repo]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except (PermissionError, OSError):
            continue
        for entry in entries:
            if entry.is_dir():
                if entry.name in _EXCLUDE_DIRS or entry.name.startswith("."):
                    continue
                stack.append(entry)
            elif entry.is_file() and entry.suffix in _FE_EXTENSIONS:
                yield entry


def _load_spec_sections(path: Path) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _SECTION_RE.match(line)
        if match:
            if current is not None:
                sections.append(current)
            current = {
                "section_id": match.group(1),
                "title": match.group(2),
                "body_lines": [],
            }
        elif current is not None:
            current["body_lines"].append(line)  # type: ignore[union-attr]
    if current is not None:
        sections.append(current)
    return sections


def _extract_search_terms(title: str, body: str) -> list[tuple[str, bool]]:
    """Return list of (term, is_title_term) tuples."""
    terms: list[tuple[str, bool]] = []
    seen: set[str] = set()
    stopwords_lower = {s.lower() for s in _STOPWORDS}

    def _add(word: str, is_title: bool) -> None:
        if word in seen:
            # Upgrade to title-term if we see it in title first
            return
        seen.add(word)
        terms.append((word, is_title))

    # English nouns in title (high weight)
    for word in _ENGLISH_WORD_RE.findall(title):
        if word.lower() in stopwords_lower:
            continue
        _add(word, True)

    # Korean translations from title
    for korean, english_list in _KEYWORD_MAP.items():
        if korean in title:
            for en in english_list:
                _add(en, True)

    # English nouns in body
    for word in _ENGLISH_WORD_RE.findall(body):
        if word.lower() in stopwords_lower:
            continue
        _add(word, False)

    # Korean translations from body
    for korean, english_list in _KEYWORD_MAP.items():
        if korean in body:
            for en in english_list:
                _add(en, False)

    return terms


def _search_term(term: str, repo: Path, cache: dict[Path, str]) -> list[str]:
    """Find files whose path or content contains `term` (case-insensitive).

    `cache` memoizes file content reads across calls.
    """
    term_lower = term.lower()
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    matches: list[str] = []
    for file_path in _iter_source_files(repo):
        path_str = str(file_path)
        if _TEST_PATH_RE.search(path_str):
            continue
        # Fast path: term in path
        if term_lower in path_str.lower():
            matches.append(path_str)
            continue
        # Content search
        content = cache.get(file_path)
        if content is None:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except (OSError, UnicodeDecodeError):
                content = ""
            cache[file_path] = content
        if pattern.search(content):
            matches.append(path_str)
    return matches


def _score_file(file_path: Path, term: str) -> tuple[float, list[str]]:
    """Return (score contribution, matched reasons)."""
    name = file_path.stem
    lower_term = term.lower()
    lower_name = name.lower()
    reasons: list[str] = []
    score = 0.0

    if lower_term == lower_name:
        score += 1.0
        reasons.append(f"exact filename: {term}")
    elif lower_term in lower_name:
        score += 1.0
        reasons.append(f"filename contains: {term}")

    # Directory name match
    for part in file_path.parts[:-1]:
        if lower_term == part.lower() or lower_term in part.lower():
            score += 0.2
            reasons.append(f"directory: {part}")
            break

    # Body match (weight lower; we already know rg matched)
    score += 0.3

    return score, reasons


def _suggest_for_section(
    section: dict[str, object],
    repo: Path,
    top_n: int,
    content_cache: dict[Path, str],
) -> dict[str, object]:
    title = str(section["title"])
    body = "\n".join(section.get("body_lines", []))  # type: ignore[arg-type]
    terms = _extract_search_terms(title, body)

    aggregate: dict[str, dict[str, object]] = {}
    for term, is_title in terms:
        weight = _TITLE_BOOST if is_title else 1.0
        for raw_path in _search_term(term, repo, content_cache):
            try:
                rel = Path(raw_path).resolve().relative_to(repo.resolve())
            except ValueError:
                rel = Path(raw_path)
            key = str(rel)
            contribution, reasons = _score_file(rel, term)
            contribution *= weight
            entry = aggregate.setdefault(
                key,
                {
                    "path": key,
                    "score": 0.0,
                    "matched_terms": [],
                    "reasons": [],
                },
            )
            entry["score"] = float(entry["score"]) + contribution  # type: ignore[assignment]
            matched = entry["matched_terms"]  # type: ignore[assignment]
            if term not in matched:  # type: ignore[operator]
                matched.append(term)  # type: ignore[attr-defined]
            reasons_list = entry["reasons"]  # type: ignore[assignment]
            for r in reasons:
                if r not in reasons_list:  # type: ignore[operator]
                    reasons_list.append(r)  # type: ignore[attr-defined]

    # Normalize scores per section to [0, 1]
    if aggregate:
        max_score = max(float(e["score"]) for e in aggregate.values())  # type: ignore[arg-type]
        if max_score > 0:
            for entry in aggregate.values():
                entry["score"] = round(float(entry["score"]) / max_score, 3)  # type: ignore[assignment]

    candidates = sorted(
        aggregate.values(),
        key=lambda e: float(e["score"]),  # type: ignore[arg-type]
        reverse=True,
    )[:top_n]

    # Flatten reasons into single 'reason' field
    for c in candidates:
        reasons = c.pop("reasons", [])
        c["reason"] = ", ".join(reasons) if reasons else "body match"

    return {
        "section_id": section["section_id"],
        "title": title,
        "search_terms": [t for t, _ in terms],
        "candidates": candidates,
    }


def suggest_mappings(
    spec_path: Path, repo: Path, top_n: int = 5
) -> list[dict[str, object]]:
    sections = _load_spec_sections(spec_path)
    content_cache: dict[Path, str] = {}
    return [_suggest_for_section(s, repo, top_n, content_cache) for s in sections]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Suggest codebase file candidates for each spec section"
    )
    parser.add_argument("--spec", required=True, help="Path to spec markdown")
    parser.add_argument("--repo", required=True, help="Path to target repo root")
    parser.add_argument("--top-n", type=int, default=5, help="Candidates per section")
    parser.add_argument("--indent", type=int, default=2, help="JSON indent")
    args = parser.parse_args()

    spec = Path(args.spec)
    repo = Path(args.repo)
    if not spec.exists():
        print(f"error: spec not found: {spec}", file=sys.stderr)
        return 1
    if not repo.exists() or not repo.is_dir():
        print(f"error: repo path invalid: {repo}", file=sys.stderr)
        return 1

    results = suggest_mappings(spec, repo, args.top_n)
    print(json.dumps(results, ensure_ascii=False, indent=args.indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
