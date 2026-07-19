#!/usr/bin/env python3
"""Scaffold a stereo-critique run (hands implement, eyes critique without CoT)."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path


def _slug(t: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", t.strip().lower())[:48].strip("-")
    return s or "task"


def scaffold(brief: str, out_root: Path) -> Path:
    sid = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + _slug(brief)
    d = out_root / sid
    d.mkdir(parents=True, exist_ok=True)
    (d / "brief.md").write_text(f"# Stereo brief\n\n{brief}\n", encoding="utf-8")
    (d / "prompt_hands.md").write_text(
        f"# Hands\n\nImplement or produce artifact for:\n\n{brief}\n\n"
        f"Write result to `hands_out.md` in this directory.\n",
        encoding="utf-8",
    )
    (d / "prompt_eyes.md").write_text(
        f"# Eyes\n\nYou do **not** see Hands chain-of-thought. Only brief + hands_out/git diff.\n\n"
        f"Brief:\n{brief}\n\nWrite critique to `eyes_out.md` and 5-line `synthesis.md`.\n",
        encoding="utf-8",
    )
    (d / "README.md").write_text(
        "# Stereo run\n\n1. Hands: prompt_hands.md\n2. Eyes: prompt_eyes.md\n3. Merge synthesis.md\n",
        encoding="utf-8",
    )
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--out", default="stereo_runs")
    args = ap.parse_args()
    d = scaffold(args.brief, Path(args.out))
    print(str(d.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
