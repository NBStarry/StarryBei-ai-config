---
type: Playbook
title: SSH TUI Proxy Environment
description: Ensure Hermes TUI sessions launched over SSH inherit the same proxy behavior as the Feishu gateway.
tags: [hermes, tui, ssh, proxy, codex]
timestamp: 2026-06-23T18:00:00+08:00
---

# SSH TUI Proxy Environment

Use this playbook when Hermes TUI works differently from Feishu gateway, especially when TUI is launched over SSH and Codex requests fail with `APIConnectionError`.

## Symptom

Feishu replies quickly, but TUI appears stuck or fails with connection errors.

Typical cause:

```text
Feishu gateway process has HTTP_PROXY / HTTPS_PROXY.
SSH-launched TUI process does not.
```

## Diagnosis

Compare proxy environment variables for running processes:

```bash
ps aux | grep -Ei 'gateway run|hermes --tui|tui_gateway.entry|ui-tui' | grep -v grep
```

For each PID, inspect environment without printing secrets:

```bash
python3 - <<'PY'
import subprocess, re
needles = ['gateway run', 'hermes --tui', 'tui_gateway.entry', 'ui-tui/dist/entry.js']
ps = subprocess.check_output(['ps', 'axo', 'pid=,command='], text=True)
for needle in needles:
    for line in ps.splitlines():
        if needle in line:
            pid = line.strip().split()[0]
            env = subprocess.check_output(['ps', 'eww', '-p', pid], text=True, stderr=subprocess.STDOUT)
            print(f'## {needle} pid={pid}')
            for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY', 'SSH_CONNECTION']:
                m = re.search(r'(?:^| )' + re.escape(key) + r'=([^ ]*)', env)
                print(f'{key}=' + (m.group(1) if m else '<unset>'))
PY
```

Healthy TUI sessions should have at least:

```text
HTTP_PROXY=http://127.0.0.1:<port>
HTTPS_PROXY=http://127.0.0.1:<port>
```

## Immediate fix

Before launching TUI over SSH:

```bash
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897
export https_proxy=http://127.0.0.1:7897
hermes --tui
```

Adjust the port for the host.

## Persistent fix

Put proxy variables in a startup path that the SSH-launched TUI actually reads.

Options:

1. `~/.hermes/.env` for Hermes-managed environment variables.
2. A wrapper script such as `~/.local/bin/hermes-tui`.
3. Shell profile loaded by SSH non-login or login shells, depending on the host's shell behavior.

Wrapper example:

```bash
#!/bin/bash
export HTTP_PROXY=${HTTP_PROXY:-http://127.0.0.1:7897}
export HTTPS_PROXY=${HTTPS_PROXY:-http://127.0.0.1:7897}
export http_proxy=${http_proxy:-$HTTP_PROXY}
export https_proxy=${https_proxy:-$HTTPS_PROXY}
exec hermes --tui "$@"
```

## Verification

```bash
curl --silent --show-error --max-time 15 \
  -o /tmp/codex-direct.out \
  -w 'direct http=%{http_code} time=%{time_total} err=%{errormsg}\n' \
  https://chatgpt.com/backend-api/codex

curl --silent --show-error --proxy http://127.0.0.1:7897 --max-time 15 \
  -o /tmp/codex-proxy.out \
  -w 'proxy http=%{http_code} time=%{time_total} err=%{errormsg}\n' \
  https://chatgpt.com/backend-api/codex
```

If the proxied request succeeds and direct request fails or is unstable, TUI must be launched with proxy variables.

## Related concepts

- [Hermes Agent](../systems/hermes-agent.md)
- [Unified Proxy Configuration](unified-proxy-config.md)
- [Clash Verge / Mihomo](../systems/clash-verge.md)
