---
type: System
title: Clash Verge / Mihomo
description: Local proxy system used to route OpenAI/Codex, search, browser, and general network traffic across macOS hosts.
tags: [clash, clash-verge, mihomo, proxy, macos, networking]
timestamp: 2026-06-23T18:00:00+08:00
---

# Clash Verge / Mihomo

Clash Verge Rev runs Mihomo locally and provides proxy groups used by Hermes, browser automation, Claude Code, Codex, and terminal tools.

## Current design intent

Keep routing policy stable across hosts while allowing each host to have different local subscription files, ports, and OS paths.

The target policy is documented in [Unified Proxy Configuration](../playbooks/unified-proxy-config.md).

## macOS reference paths

```text
~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/
├── clash-verge.yaml
├── clash-verge-check.yaml
├── profiles.yaml
├── profiles/
└── providers/
```

Runtime API socket:

```text
/tmp/verge/verge-mihomo.sock
```

Typical local HTTP proxy port:

```text
127.0.0.1:7897
```

## Stable routing concepts

| Concept | Meaning |
|---|---|
| `OpenAI` | Selector for ChatGPT / OpenAI / Codex traffic. |
| `HK-Failover` | Preferred fast route for OpenAI/Codex when Hong Kong nodes are healthy. |
| `US-Failover` | Backup route when Hong Kong routes fail or a US route is needed. |
| `Search-Failover` | Search/browser traffic selector, separate from OpenAI traffic. |
| `Proxy` | General default selector. Should not be blindly forced for all traffic unless intended. |

## Health check principle

Use the endpoint that represents the traffic being protected.

For OpenAI/Codex routing, a good health check is:

```text
https://chatgpt.com/backend-api/codex
```

A `403` response from that endpoint is acceptable proof that the network path reached the protected service. It is better than only testing generic endpoints such as `https://www.gstatic.com/generate_204`.

## Security rules

Never commit:

- subscription URLs
- node passwords
- proxy provider secrets
- OAuth tokens
- API keys
- raw generated configs containing provider credentials

Document the structure and verification steps, not the sensitive payload.

## Verification checks

```bash
curl --silent --show-error --max-time 5 \
  --unix-socket /tmp/verge/verge-mihomo.sock \
  http://127.0.0.1/proxies > /tmp/mihomo-proxies.json

curl --silent --show-error --proxy http://127.0.0.1:7897 --max-time 15 \
  -o /tmp/codex.out \
  -w 'codex http=%{http_code} time=%{time_total}\n' \
  https://chatgpt.com/backend-api/codex
```
