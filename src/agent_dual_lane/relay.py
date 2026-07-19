#!/usr/bin/env python3
"""Dual-lane external-memory handoff (stdlib only).

status | package | absorb | watch

No shared KV between models. Package high-signal layers; peer continues fresh.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _mb(path: Path) -> float | None:
    if not path.is_file():
        return None
    return round(path.stat().st_size / (1024 * 1024), 3)


def _lane_metrics(lane: dict, key: str) -> dict:
    root = Path(lane.get("session_dir") or "")
    m = {
        "lane": key,
        "label": lane.get("label"),
        "session_dir": str(root) if root else None,
        "exists": root.is_dir(),
    }
    if not m["exists"]:
        m["pressure"] = "unknown"
        m["score"] = 0
        return m
    m["updates_mb"] = _mb(root / "updates.jsonl")
    m["events_mb"] = _mb(root / "events.jsonl")
    m["chat_mb"] = _mb(root / "chat_history.jsonl")
    cc = root / "compaction_checkpoints"
    m["compaction_checkpoints"] = len(list(cc.glob("*"))) if cc.is_dir() else 0
    return m


def _score(m: dict, cfg: dict) -> dict:
    th = cfg.get("thresholds_mb") or {}
    tho = cfg.get("thresholds_other") or {}
    score = 0
    reasons = []
    upd = m.get("updates_mb") or 0
    ev = m.get("events_mb") or 0
    cc = m.get("compaction_checkpoints") or 0
    if upd >= float(th.get("updates_handoff", 100)):
        score = max(score, 3)
        reasons.append(f"updates_handoff_{upd}mb")
    elif upd >= float(th.get("updates_warn", 40)):
        score = max(score, 2)
        reasons.append(f"updates_warn_{upd}mb")
    if ev >= float(th.get("events_handoff", 60)):
        score = max(score, 3)
        reasons.append(f"events_handoff_{ev}mb")
    elif ev >= float(th.get("events_warn", 35)):
        score = max(score, 2)
        reasons.append(f"events_warn_{ev}mb")
    if cc >= int(tho.get("compaction_handoff", 80)):
        score = max(score, 3)
        reasons.append(f"compaction_handoff_{cc}")
    elif cc >= int(tho.get("compaction_warn", 40)):
        score = max(score, 2)
        reasons.append(f"compaction_warn_{cc}")
    m["score"] = score
    m["reasons"] = reasons
    m["pressure"] = {0: "ok", 1: "elevated", 2: "warn", 3: "handoff"}[score]
    return m


def status(cfg: dict) -> dict:
    lanes = cfg.get("lanes") or {}
    out = {"schema": "agent_dual_lane_status.v1", "ts": _utc(), "lanes": {}}
    for key, lane in lanes.items():
        out["lanes"][key] = _score(_lane_metrics(lane, key), cfg)
    items = list(out["lanes"].items())
    items.sort(key=lambda x: x[1].get("score") or 0, reverse=True)
    if len(items) >= 2 and (items[0][1].get("score") or 0) >= 2:
        out["recommended"] = f"{items[0][0]}→{items[1][0]}"
    else:
        out["recommended"] = None
    out["truth"] = "No shared KV. Handoff = external memory package + peer inject."
    pending = Path(cfg.get("handoff_dir") or "handoffs") / "PENDING.json"
    p = _load(pending)
    out["pending"] = bool(p.get("pending"))
    out["pending_id"] = p.get("id")
    return out


def package(cfg: dict, source: str, dest: str, note: str = "") -> dict:
    root = Path(cfg.get("handoff_dir") or "handoffs")
    root.mkdir(parents=True, exist_ok=True)
    st = status(cfg)
    src = (st["lanes"] or {}).get(source) or {}
    dst = (st["lanes"] or {}).get(dest) or {}
    hid = f"dlcr-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{source}-to-{dest}"
    md = root / f"{hid}.md"
    body = f"""# Dual-Lane Handoff `{hid}`

**Generated:** {_utc()}
**Source:** {source} · pressure={src.get('pressure')} · updates_mb={src.get('updates_mb')}
**Dest:** {dest} · pressure={dst.get('pressure')}
**Note:** {note}

## Truth

This is **not** a full session dump. Peer should continue from these layers only.

## Layer 1 — State

```json
{json.dumps(src, indent=2)}
```

## Layer 2 — Narrative

Paste plan/summary pointers or short bullets here (edit after package if needed).

## Layer 3 — Intent (high-signal only)

- Prefer recent user goals, not tool noise
- Avoid training-drill / harness spam

## Layer 4 — Priority paths

List files/skills the peer should open first.

## Layer 5 — Protocol

1. Do **not** load source updates.jsonl wholesale
2. Mark absorb: `python3 …/relay.py absorb --id {hid} --by peer --config …`
3. No secrets in this file

— agent-dual-lane-handoff
"""
    md.write_text(body, encoding="utf-8")
    meta = {
        "schema": "agent_dual_lane_handoff.v1",
        "id": hid,
        "ts": _utc(),
        "source": source,
        "dest": dest,
        "md": str(md),
        "note": note,
        "metrics_source": src,
        "metrics_dest": dst,
        "absorbed_by": [],
    }
    _save(root / f"{hid}.json", meta)
    latest = root / "LATEST.md"
    latest.write_text(
        f"# Latest handoff\n\n- id: `{hid}`\n- path: `{md}`\n- ts: {_utc()}\n- pending: true\n",
        encoding="utf-8",
    )
    _save(
        root / "PENDING.json",
        {"schema": "pending.v1", "pending": True, "id": hid, "md": str(md), "ts": _utc()},
    )
    return meta


def absorb(cfg: dict, handoff_id: str, by: str) -> dict:
    root = Path(cfg.get("handoff_dir") or "handoffs")
    jp = root / f"{handoff_id}.json"
    if not jp.is_file():
        matches = list(root.glob(f"*{handoff_id}*.json"))
        if not matches:
            return {"ok": False, "error": "not_found", "id": handoff_id}
        jp = matches[0]
    meta = _load(jp)
    meta.setdefault("absorbed_by", []).append({"by": by, "ts": _utc()})
    _save(jp, meta)
    _save(
        root / "PENDING.json",
        {
            "schema": "pending.v1",
            "pending": False,
            "id": meta.get("id"),
            "absorbed_by": by,
            "ts": _utc(),
        },
    )
    latest = root / "LATEST.md"
    latest.write_text(
        f"# Latest handoff\n\n- id: `{meta.get('id')}`\n- pending: false\n"
        f"- absorbed_by: `{by}`\n- ts: {_utc()}\n",
        encoding="utf-8",
    )
    return {"ok": True, "id": meta.get("id"), "absorbed_by": meta["absorbed_by"]}


def watch(cfg: dict) -> dict:
    st = status(cfg)
    rec = st.get("recommended")
    armed = bool((cfg.get("auto_handoff") or {}).get("armed"))
    if not rec:
        return {"ok": True, "action": "none", "status": st}
    src, dst = rec.split("\u2192")
    src_score = (st["lanes"].get(src) or {}).get("score") or 0
    if src_score < 3:
        return {"ok": True, "action": "none", "status": st}
    if not armed:
        meta = package(cfg, src, dst, note="watch propose (auto not armed)")
        return {"ok": True, "action": "propose", "package": meta, "status": st}
    meta = package(cfg, src, dst, note="auto watch")
    return {"ok": True, "action": "package", "package": meta, "status": st}


def _extract_config(argv: list[str]) -> tuple[str, list[str]]:
    """Allow --config before or after the subcommand."""
    config = "examples/config.json"
    cleaned: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--config" and i + 1 < len(argv):
            config = argv[i + 1]
            i += 2
            continue
        if a.startswith("--config="):
            config = a.split("=", 1)[1]
            i += 1
            continue
        cleaned.append(a)
        i += 1
    return config, cleaned


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    config_arg, cleaned = _extract_config(raw)
    ap = argparse.ArgumentParser(description="Agent dual-lane handoff relay")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    p_pkg = sub.add_parser("package")
    p_pkg.add_argument("--source", default="composer")
    p_pkg.add_argument("--dest", default="peer")
    p_pkg.add_argument("--note", default="")
    p_ab = sub.add_parser("absorb")
    p_ab.add_argument("--id", required=True)
    p_ab.add_argument("--by", default="peer")
    sub.add_parser("watch")
    args = ap.parse_args(cleaned)
    cfg_path = Path(config_arg)
    if not cfg_path.is_file():
        alt = Path(__file__).resolve().parents[2] / config_arg
        if alt.is_file():
            cfg_path = alt
    cfg = _load(cfg_path)
    if not cfg:
        raise SystemExit(f"missing config: {config_arg}")
    if not Path(cfg.get("handoff_dir", "handoffs")).is_absolute():
        pkg = Path(__file__).resolve().parents[2]
        cfg["handoff_dir"] = str(pkg / (cfg.get("handoff_dir") or "handoffs"))

    if args.cmd == "status":
        out = status(cfg)
    elif args.cmd == "package":
        out = package(cfg, args.source, args.dest, note=args.note)
    elif args.cmd == "absorb":
        out = absorb(cfg, args.id, args.by)
    else:
        out = watch(cfg)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
