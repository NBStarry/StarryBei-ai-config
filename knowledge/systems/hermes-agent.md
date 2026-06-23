---
type: System
title: Hermes Agent
description: Personal agent runtime used through Feishu, TUI, terminal tools, skills, memory, cron jobs, and model provider routing.
resource: https://hermes-agent.nousresearch.com/docs
tags: [hermes, agent, feishu, tui, skills, memory]
timestamp: 2026-06-23T18:00:00+08:00
---

# Hermes Agent

Hermes Agent is the personal assistant runtime behind Feishu DM/group chats, terminal tools, TUI sessions, cron jobs, skills, and persistent memory.

## Role in this repository

This repository stores public, reusable configuration and documentation for AI tools. Hermes itself uses its own profile under `~/.hermes`, but this repo can hold tool-neutral knowledge and playbooks that Hermes, Claude Code, Codex, and future agents can all read.

## Relevant linked concepts

- [Unified Proxy Configuration](../playbooks/unified-proxy-config.md)
- [SSH TUI Proxy Environment](../playbooks/ssh-tui-proxy-env.md)
- [Clash Verge / Mihomo](clash-verge.md)

## Durable conventions

- Secrets live in `.env`, auth stores, or ignored local files; never in public knowledge files.
- Procedures that require exact command sequences belong in skills or playbooks.
- Stable system facts belong in OKF concept files.
- Temporary task progress belongs in session logs or `VERIFY.md`, not in memory or OKF.

## Common runtime surfaces

| Surface | Purpose | Notes |
|---|---|---|
| Feishu gateway | Daily assistant interaction | Usually starts with a controlled environment and proxy variables. |
| TUI | Local/SSH interactive use | SSH-launched TUI may not inherit proxy variables; see [SSH TUI Proxy Environment](../playbooks/ssh-tui-proxy-env.md). |
| Cron | Scheduled jobs | Jobs should be self-contained and avoid noisy success messages. |
| Skills | Reusable procedural memory | Best for workflows with exact steps, pitfalls, and verification. |
| OKF knowledge | Reusable conceptual memory | Best for cross-tool concepts and portable context. |

## Verification checks

```bash
hermes status --all
hermes config check
hermes skills list
hermes cron list
```

For provider/network issues, also verify the proxy path with the real model endpoint, not only a generic connectivity URL.
