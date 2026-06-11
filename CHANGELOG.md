# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project aims for [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-06-11

First closed-out release: the deterministic core, both transports, search/graph, two-tier
linting, cross-process consistency/safety, and the optional standalone edge — all TDD'd and
green (127 tests, no network), plus real-agent end-to-end acceptance via an independent CLI agent.

### Core (deterministic, no LLM)
- `WikiStore`: structure validation, per-file locking, optimistic concurrency control (OCC),
  atomic writes, non-destructive section-level patching; auto-synced `index.md` and append-only `log.md`.
- Page model with frontmatter, content hashing, wikilink extraction; content-addressed source registry.
- Parsers: Markdown, PDF (pdfplumber), HTML (bs4+lxml), **DOCX** (python-docx).

### Transports
- CLI (`loom …`, with `--json`) — init, read/list, write/update, register/parse, search,
  find-related, graph, lint, review, ingest/query (`--auto`), mcp.
- MCP server (`loom mcp`) exposing 14 `wiki_*` primitives one-to-one.

### Search & graph
- Keyword search (BM25 + jieba), field-weighted; wikilink graph (neighborhood, orphans, broken links);
  `find_related` for new-vs-merge dedup.

### Linting
- Six structural checkers (orphan / broken-link / bad-frontmatter / bad-name / stale / duplicate-title),
  never raises; safe `--fix` subset (index resync, mtime/date backfill, source-hash backfill);
  `lint_candidates` heuristics (possible-contradiction / sparse-area / stale-cluster) for agent judgment.

### Consistency & safety
- Cross-process safety: global locks for shared `index.md`/`log.md` (no lost updates under 10-way concurrency);
  flock liveness (auto-release on process death, no stale-lock cleanup needed).
- Actionable OCC conflicts: carry `current_hash` + changed-section diff for one-step recovery.
- Untrusted-source delimiting with zero-width-space spoof neutralization (defense in depth).
- Inline claim-level citations `^[src:file#locator]` → claim-precise staleness.
- Review queue: stage high-risk writes as a diff for human approval (`loom review …`).

### Optional edges (not part of core)
- `[auto]`: `LLMProvider` protocol + Anthropic / OpenAI-compatible providers; `auto_ingest` / `auto_query`
  orchestrate the full SKILL workflow. Lazy-imported; core has zero dependency on it.
- `[vector]`: **intentionally not shipped** — BM25 measured 90% top-3 on the acceptance wiki; reserved
  with a documented re-enable threshold.

### Docs
- `SKILL.md` (ingest/query/lint recipes), three wiki templates (blank/research/personal), README,
  `docs/INTEGRATION.md`, and acceptance/test reports under `docs/test-reports/`.

[0.1.0]: https://github.com/cczywyc/loom/releases/tag/v0.1.0
