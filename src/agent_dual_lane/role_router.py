#!/usr/bin/env python3
"""Route tasks to hands (long-run) vs eyes (loose) vs fork/parallel plays."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

HANDS = ("implement", "fix", "refactor", "ship", "tool", "test", "patch", "code")
EYES = ("research", "brainstorm", "critique", "review", "explore", "design", "strategy")
PARALLEL = ("parallel", "best-of", "worktrees", "multi path")
FORK = ("fork", "isolated", "worktree only")


def route(task: str) -> dict:
    low = task.lower()
    h = sum(1 for k in HANDS if k in low)
    e = sum(1 for k in EYES if k in low)
    p = sum(1 for k in PARALLEL if k in low)
    f = sum(1 for k in FORK if k in low)
    if p:
        primary, model = "parallel_subagents", "subagents + worktrees / --best-of-n"
    elif f or (h and e):
        primary, model = "fork_dual", "/fork --worktree + secondary model"
    elif h > e:
        primary, model = "hands", "long-run / Composer-style"
    elif e > h:
        primary, model = "eyes", "loose / Grok-style peer"
    else:
        primary, model = "assembly_line", "eyes plan → hands execute → eyes review"
    return {
        "schema": "role_route.v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "task": task,
        "primary": primary,
        "model_hint": model,
        "scores": {"hands": h, "eyes": e, "parallel": p, "fork": f},
        "truth": "No shared KV. Bridge = disk handoff package.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    args = ap.parse_args()
    print(json.dumps(route(args.task), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
