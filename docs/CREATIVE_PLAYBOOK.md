# Creative dual-model playbook

KV is **not** shared. Disk is the bridge.

## Role lock

| Lane | Typical model | Does | Avoids |
|------|---------------|------|--------|
| **Hands** | Composer / long-run agent | tools, implement, hygiene | constitutional rewrites alone |
| **Eyes** | Grok / peer | research, critique, explore | dumping full transcripts |
| **Bridge** | files on disk | handoff packages, PENDING flag | secrets |

## Plays

### P1 · Assembly line

Eyes write `plan.md` → Hands implement → Eyes review `git diff`.

### P2 · Stereo critique

```bash
python3 src/agent_dual_lane/stereo.py --brief "review this design"
```

Hands never share CoT with Eyes; Eyes only sees brief + output.

### P3 · Fork surgery (Grok TUI)

```
/fork --worktree "implement only path/to/file from LATEST handoff"
```

### P4 · Best-of-n (headless)

```bash
grok -p "3 designs for X" --best-of-n 3
```

### P5 · Hot / warm / cold memory

| Tier | Where |
|------|--------|
| Hot | current session |
| Warm | `handoffs/LATEST.md` + PENDING |
| Cold | project MEMORY / experimental-memory |

### P6 · Adversarial pair

Eyes proposes bold idea → Hands implements minimal safe slice.

### P7 · Sleep-time split

While human idle: Eyes research on disk; Hands only pressure hygiene.
