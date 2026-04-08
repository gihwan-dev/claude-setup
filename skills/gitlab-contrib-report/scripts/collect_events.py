#!/usr/bin/env python3
"""Collect GitLab contribution events via glab CLI and output aggregated JSON."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any


def _run_glab(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["glab", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def check_auth() -> str | None:
    """Return authenticated hostname or None."""
    result = _run_glab(["auth", "status"])
    combined = result.stdout + result.stderr
    for line in combined.splitlines():
        stripped = line.strip()
        if stripped.startswith("Logged in to") or stripped.startswith("✓ Logged in to"):
            for token in stripped.split():
                if "." in token and not token.startswith("("):
                    host = token.rstrip(",").rstrip(".")
                    if host:
                        return host
    # fallback: try glab config
    result = _run_glab(["config", "get", "host"])
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def get_user(hostname: str) -> dict[str, Any]:
    result = _run_glab(["api", "/user", "--hostname", hostname])
    if result.returncode != 0:
        print(f"error: glab api /user failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def fetch_events(
    hostname: str,
    user_id: int,
    start_date: str,
    end_date: str | None = None,
    max_pages: int = 100,
) -> list[dict[str, Any]]:
    """Fetch all user events via paginated glab api calls."""
    all_events: list[dict[str, Any]] = []
    page = 1

    while page <= max_pages:
        endpoint = f"/users/{user_id}/events?per_page=100&page={page}&after={start_date}"
        if end_date:
            endpoint += f"&before={end_date}"

        result = _run_glab(["api", endpoint, "--hostname", hostname])
        if result.returncode != 0:
            print(
                f"warning: page {page} failed, using collected data so far",
                file=sys.stderr,
            )
            break

        try:
            events = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"warning: invalid JSON on page {page}, stopping", file=sys.stderr)
            break

        if not events:
            break

        all_events.extend(events)
        page += 1

    return all_events


def _iso_week(dt: date) -> str:
    iso = dt.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _quarter(dt: date) -> str:
    q = (dt.month - 1) // 3 + 1
    return f"{dt.year}-Q{q}"


def aggregate(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate raw events into counts by various time dimensions."""
    monthly: defaultdict[str, int] = defaultdict(int)
    weekly: defaultdict[str, int] = defaultdict(int)
    yearly: defaultdict[str, int] = defaultdict(int)
    daily: defaultdict[str, int] = defaultdict(int)
    quarterly: defaultdict[str, int] = defaultdict(int)
    monthly_by_action: defaultdict[str, defaultdict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    action_totals: defaultdict[str, int] = defaultdict(int)

    for event in events:
        created_at = event.get("created_at", "")
        action = event.get("action_name", "unknown")

        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
        except (ValueError, AttributeError):
            continue

        month_key = dt.strftime("%Y-%m")
        week_key = _iso_week(dt)
        year_key = str(dt.year)
        day_key = dt.isoformat()
        quarter_key = _quarter(dt)

        monthly[month_key] += 1
        weekly[week_key] += 1
        yearly[year_key] += 1
        daily[day_key] += 1
        quarterly[quarter_key] += 1
        monthly_by_action[month_key][action] += 1
        action_totals[action] += 1

    return {
        "monthly": dict(sorted(monthly.items())),
        "weekly": dict(sorted(weekly.items())),
        "yearly": dict(sorted(yearly.items())),
        "daily": dict(sorted(daily.items())),
        "quarterly": dict(sorted(quarterly.items())),
        "monthly_by_action": {
            k: dict(v) for k, v in sorted(monthly_by_action.items())
        },
        "action_totals": dict(sorted(action_totals.items(), key=lambda x: -x[1])),
    }


def build_summary(
    events: list[dict[str, Any]],
    agg: dict[str, Any],
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """Build the top-level summary stats."""
    active_days = len(agg["daily"])
    total = len(events)
    avg_per_active_day = round(total / active_days, 1) if active_days else 0

    return {
        "period_start": start_date,
        "period_end": end_date,
        "total_events": total,
        "active_days": active_days,
        "avg_per_active_day": avg_per_active_day,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect GitLab contribution events")
    parser.add_argument("--hostname", help="GitLab hostname (auto-detected if omitted)")
    parser.add_argument(
        "--months",
        type=int,
        default=12,
        help="Number of months to look back (default: 12)",
    )
    parser.add_argument("--from-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--indent", type=int, default=2)
    args = parser.parse_args()

    # 1. Auth check
    hostname = args.hostname or check_auth()
    if not hostname:
        print("error: glab not authenticated. Run: glab auth login", file=sys.stderr)
        return 1

    # 2. Get user
    user = get_user(hostname)
    user_id = user["id"]
    username = user["username"]

    # 3. Determine date range
    today = date.today()
    if args.from_date:
        start_date = args.from_date
    else:
        start = today - timedelta(days=args.months * 30)
        start_date = start.isoformat()

    end_date = args.to_date or today.isoformat()

    # 4. Fetch events
    print(
        f"Collecting events for @{username} ({start_date} ~ {end_date})...",
        file=sys.stderr,
    )
    events = fetch_events(hostname, user_id, start_date, end_date)
    print(f"Collected {len(events)} events.", file=sys.stderr)

    # 5. Aggregate
    agg = aggregate(events)
    summary = build_summary(events, agg, start_date, end_date)

    # 6. Output
    payload = {
        "user": {"id": user_id, "username": username},
        "hostname": hostname,
        "summary": summary,
        "aggregation": agg,
    }

    print(json.dumps(payload, ensure_ascii=False, indent=args.indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
