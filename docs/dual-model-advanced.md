# Advanced dual-model patterns (Grok TUI & friends)

## Hard truth

| Myth | Reality |
|------|---------|
| Two models share KV | No public API for that |
| `/model` keeps internal state | Same transcript only |
| Compaction jumps to other model | Compacts **this** session |

Value = **role split + external memory + controlled parallelism**.

## Native Grok Build primitives power users use

- `/fork [--worktree] [directive]` — peer agent with copied history
- `fork_secondary_model` in config — child on another model
- Subagents + git worktrees — parallel explores
- `--best-of-n N` — headless variance
- `--experimental-memory` — cross-session facts under `~/.grok/memory/`
- `compaction.memory_flush` — flush decisions before compact

## Multi-model routing (community pattern)

Orchestrator (expensive/rare) + sub-agents (volume). Or:

**Plan (eyes) → Execute (hands) → Review (eyes)** on disk.

## This repo

Implements the **warm bridge**: 5-layer package + PENDING + role router + stereo scaffold.

Related reading: MemGPT hierarchical memory, Anthropic multi-agent synthesis, Letta sleep-time compute.
