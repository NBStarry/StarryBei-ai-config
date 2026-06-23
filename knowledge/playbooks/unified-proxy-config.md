---
type: Playbook
title: Unified Proxy Configuration
description: Host-neutral design for keeping OpenAI, search, and general proxy routing consistent across different machines.
tags: [proxy, clash, mihomo, multi-host, openai, codex]
timestamp: 2026-06-23T18:00:00+08:00
---

# Unified Proxy Configuration

Use this playbook when making proxy behavior consistent across multiple hosts.

## Goal

Different machines may have different local files, ports, subscriptions, and OS paths. They should still expose the same logical routing policy to tools:

```text
OpenAI -> HK-Failover
Proxy -> Search-Failover
Search-Failover -> HK-Failover -> US-Failover
```

## Standard logical groups

| Group | Type | Purpose |
|---|---|---|
| `OpenAI` | selector | Explicit selector for OpenAI, ChatGPT, and Codex traffic. |
| `HK-Failover` | fallback / url-test | Preferred fast path for OpenAI/Codex. |
| `US-Failover` | fallback / url-test | Backup or US-required path. |
| `Search-Failover` | fallback / selector | Browser search and web research path. |
| `Proxy` | selector | General default selector, should include `Search-Failover`. |

## Standard rules

Route AI domains to `OpenAI`:

```text
chatgpt.com
openai.com
oaistatic.com
oaiusercontent.com
api.openai.com
```

Route search domains to `Search-Failover`:

```text
google.com
bing.com
duckduckgo.com
search.brave.com
```

## Host-specific variables

Keep these outside the shared knowledge file:

| Variable | Example | Notes |
|---|---|---|
| local HTTP proxy port | `127.0.0.1:7897` | May be `7890` on another host. |
| Mihomo control endpoint | `/tmp/verge/verge-mihomo.sock` | OS-specific. |
| subscription profile file | `[REDACTED]` | Never commit subscription URLs or raw secrets. |
| provider file paths | `profiles/<id>.yaml` | IDs may differ by host. |

## Implementation pattern

1. Define the same logical group names on every host.
2. Import host-local nodes through `proxy-providers` or local provider files.
3. Keep sensitive provider URLs and node secrets out of Git.
4. Patch persistent Clash Verge profile enhancements, not only generated runtime YAML.
5. Reload Mihomo.
6. Verify live group state via the Mihomo API.
7. Smoke test the real traffic endpoint.

## Verification commands

```bash
curl --silent --show-error --max-time 5 \
  --unix-socket /tmp/verge/verge-mihomo.sock \
  http://127.0.0.1/proxies > /tmp/mihomo-proxies.json

python3 - <<'PY'
import json
p=json.load(open('/tmp/mihomo-proxies.json')).get('proxies', {})
for name in ['OpenAI', 'Proxy', 'Search-Failover', 'HK-Failover', 'US-Failover']:
    g=p.get(name)
    if g:
        print(name, 'type=', g.get('type'), 'now=', g.get('now'), 'all=', len(g.get('all') or []))
PY

curl --silent --show-error --proxy http://127.0.0.1:7897 --max-time 15 \
  -o /tmp/codex.out \
  -w 'codex http=%{http_code} time=%{time_total}\n' \
  https://chatgpt.com/backend-api/codex
```

Expected Codex health result:

```text
http=403 or another non-timeout HTTP response
```

Timeout, DNS failure, or `APIConnectionError` means the route is not healthy.

## Related concepts

- [Clash Verge / Mihomo](../systems/clash-verge.md)
- [Hermes Agent](../systems/hermes-agent.md)
- [SSH TUI Proxy Environment](ssh-tui-proxy-env.md)
