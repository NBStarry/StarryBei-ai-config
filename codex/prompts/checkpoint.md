---
description: Run the current repository checkpoint closeout flow
argument-hint: SESSION="<session name>" [TOPIC=topic] [COMMIT_MESSAGE="message"]
---

Use the repository checkpoint workflow for the current working directory.

Inputs:
- `SESSION`: the current Codex or external-agent session name. If it is missing or ambiguous, ask the user for it before editing files.
- `TOPIC`: optional `sessions/<topic>.md` basename for a new session that has no owned STATUS file yet.
- `COMMIT_MESSAGE`: optional handoff commit message for repositories whose checkpoint script supports it.

Execution rules:
1. If a `checkpoint` skill is available, load and follow it as the source of truth.
2. If no `checkpoint` skill is available but `scripts/checkpoint.sh` exists, inspect that script and use it as the mechanical gate.
3. If neither exists, explain that this repository has no checkpoint workflow instead of inventing one.
4. Before editing any file, re-read its current content.
5. Prefer this command shape when the script exists:

```bash
bash scripts/checkpoint.sh prepare "$SESSION" "$TOPIC"
bash scripts/checkpoint.sh finish "$SESSION" "$COMMIT_MESSAGE"
```

Do not treat this prompt as the checkpoint specification. It is only a Codex slash-menu adapter; the repository skill, script, and `AGENTS.md` remain authoritative.
