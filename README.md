# agent-dual-lane-handoff

**External-memory handoff between two AI coding sessions** (e.g. Grok TUI Composer + Grok peer).

> Models do **not** share KV cache. Continuity = structured disk package + fresher peer.

Designed for advanced dual-model setups (Grok Build Composer 2.5 + Grok, or any two long-running agent sessions).

## Why

When one session grows huge (`updates.jsonl` hundreds of MB), context rot hits **before** the hard limit. Power users already use:

- `/fork` + worktrees
- plan / execute / review across models
- cross-session memory files

This repo formalizes a **5-layer handoff package** + role routing + creative plays (stereo critique, assembly line).

## Install

```bash
git clone https://github.com/Phuderoso/agent-dual-lane-handoff.git
cd agent-dual-lane-handoff
# stdlib only for core tools
python3 src/agent_dual_lane/relay.py status --config examples/config.json
```

## Quick start

1. Copy `examples/config.json` and set two session directories (or any paths you measure).
2. `python3 src/agent_dual_lane/relay.py package --config …`
3. Point the peer agent at `handoffs/LATEST.md` — do **not** paste full transcripts.
4. Peer runs `absorb --id …` when done.

## Tools

| Script | Role |
|--------|------|
| `relay.py` | status / package / handoff pointer / absorb / watch |
| `role_router.py` | recommend hands vs eyes vs fork vs parallel |
| `stereo.py` | scaffold stereo-critique directories |

## Creative plays

See [docs/CREATIVE_PLAYBOOK.md](docs/CREATIVE_PLAYBOOK.md).

## Research notes

- [docs/dual-model-advanced.md](docs/dual-model-advanced.md) — Grok TUI primitives + multi-model routing
- Pattern family: MemGPT hierarchical memory, Anthropic multi-agent synthesis, Letta sleep-time compute

## Safety

- Never put secrets/passwords in handoff bodies
- Auto-deliver is off by default
- Prefer small packages (<20KB) over dumping session logs

## Origin

Extracted from a multi-agent “organism” workspace (Nihira/Elyra dual-lane work, 2026) for other AIs and humans running dual Grok/Composer environments.

## License

MIT
