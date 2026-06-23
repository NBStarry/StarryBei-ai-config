---
type: Index
title: StarryBei AI Config Knowledge Bundle
description: OKF-style knowledge bundle for cross-tool AI configuration, agent workflows, and multi-host operational playbooks.
tags: [okf, knowledge, ai-config, agents]
timestamp: 2026-06-23T18:00:00+08:00
---

# StarryBei AI Config Knowledge Bundle

This directory is a lightweight OKF-style knowledge bundle: Markdown files with YAML frontmatter, one concept per file, linked together with normal Markdown links.

## Purpose

Make the repository readable by humans and AI agents across hosts and tools.

The bundle records durable concepts that are broader than one tool's runtime config:

- cross-host configuration intent
- proxy and model routing policy
- agent workflow boundaries
- migration notes between macOS / Windows / SSH environments
- operational playbooks that should stay tool-neutral

## Concepts

### Systems

- [Hermes Agent](systems/hermes-agent.md)
- [Clash Verge / Mihomo](systems/clash-verge.md)

### Playbooks

- [Unified Proxy Configuration](playbooks/unified-proxy-config.md)
- [SSH TUI Proxy Environment](playbooks/ssh-tui-proxy-env.md)

## Rules

- Keep one concept per file.
- Every concept document must have YAML frontmatter with at least `type`, `title`, `description`, and `tags`.
- Do not store subscription URLs, API keys, OAuth tokens, passwords, node secrets, or private identifiers here.
- Use placeholders such as `[REDACTED]` for sensitive values.
- Prefer intent and validation steps over machine-specific blobs.
- Put operational commands in playbooks; put facts about systems in system concept files.

## Why not just README

README files explain a directory. OKF concept files explain reusable knowledge units that agents can discover, link, and reuse without loading the whole repo into context.
