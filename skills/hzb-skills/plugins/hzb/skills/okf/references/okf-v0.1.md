# OKF v0.1 reference

## Sources

- Google Cloud Blog, “How the Open Knowledge Format can improve data sharing,” 2026-06-13: <https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing>
- Official Open Knowledge Format v0.1 draft specification: <https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md>
- Official repository and reference implementations: <https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf>

This reference summarizes the cited v0.1 draft. Recheck the official specification before claiming compatibility with a newer version.

## Model

- A **knowledge bundle** is the distributable directory tree.
- A **concept** is one non-reserved Markdown document.
- A **concept ID** is the file path relative to the bundle root without `.md`.
- A **link** is a normal Markdown link between concepts.
- A **citation** points to material supporting a claim.

Bundles may be a Git repository, archive, or subdirectory of a larger repository. Git is recommended for history, attribution, review, and diffs.

## Reserved files

### `index.md`

- Optional at any directory level.
- Used for progressive disclosure and directory navigation.
- Normally contains no frontmatter.
- Groups entries under headings and links to concepts or subdirectories.
- Entries should carry the linked concept's description.
- A bundle-root index may use frontmatter only to declare `okf_version: "0.1"`.

### `log.md`

- Optional at any directory level.
- Records updates newest first.
- Uses `## YYYY-MM-DD` headings.
- Entries are prose; labels such as **Update**, **Creation**, or **Deprecation** are conventions.

Neither reserved filename may be used as an ordinary concept document.

## Concept frontmatter

```yaml
---
type: Playbook
title: Incident response for stale orders
description: Triage steps for the orders freshness alert.
resource: https://example.com/runbooks/orders
tags: [oncall, orders]
timestamp: 2026-07-12T00:00:00Z
---
```

Only `type` is required. It must be a non-empty, descriptive string. There is no central type registry, and consumers must tolerate unknown types.

Recommended fields, in priority order:

1. `title`: human-readable display name.
2. `description`: one-sentence summary for search, indexes, and previews.
3. `resource`: canonical URI for the underlying asset, when one exists.
4. `tags`: YAML list for cross-cutting categorization.
5. `timestamp`: ISO 8601 time of the last meaningful change.

Producers may add fields. Consumers should preserve unknown fields when round-tripping.

## Markdown body

The body has no mandatory sections. Prefer structured Markdown. Conventional headings include:

- `# Schema` for fields or columns.
- `# Examples` for concrete usage.
- `# Citations` for external evidence.

## Cross-linking

- Bundle-relative absolute link: `[Orders](/tables/orders.md)`.
- Relative link: `[Other table](./other.md)`.
- The prose around a link expresses its semantics; the link itself is an untyped directed relationship.
- Broken links are tolerated by consumers and do not make a bundle malformed.

## Citations

Claims derived from external sources should end with numbered entries under `# Citations`:

```markdown
# Citations

[1] [Authoritative schema](https://example.com/schema)
```

Citations may be external URLs, bundle-relative links, or first-class reference concepts.

## Strict conformance

An OKF v0.1 bundle is conformant when:

1. Every non-reserved `.md` file has parseable YAML frontmatter.
2. Every concept frontmatter has a non-empty `type`.
3. Every present `index.md` and `log.md` follows its reserved structure.

Consumers should not reject a bundle for missing optional fields, unknown type values, unknown extension keys, broken links, or missing indexes.

## Goals and non-goals

OKF standardizes a small interoperability surface so knowledge can be written and consumed by humans, agents, exporters, catalogs, search indexes, and viewers without translation. It does not define a fixed taxonomy, prescribe infrastructure, or replace domain schemas.
