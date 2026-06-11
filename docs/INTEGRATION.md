# Integrating Loom into your agent

**English** · [简体中文](INTEGRATION.zh-CN.md)

Loom is a brainless tool: **your agent is the brain, Loom is the hands.** There are two transports to connect through — pick either one; their capabilities are identical.

## 1. Choosing: MCP mode vs CLI shell-out mode

| | **MCP mode** (resident server) | **CLI shell-out mode** |
|---|---|---|
| Shape | `loom mcp` runs as a resident process; the agent calls 14 `wiki_*` tools over MCP | the agent runs `loom ...` commands directly (`--json` for structured output) |
| Good for | MCP-capable agents (Claude Code, Cursor…); **dense ingest/query loops** | any agent / script / cron that can run a shell; one-off tasks |
| Performance | **faster**: process stays warm → warm search index, warm graph, file locks all in memory; the jieba dictionary loads once | cold start each time (reopen the index, reread files, reload jieba ~1s) |
| Concurrency | the resident process is a natural write-serialization point | multi-process safe (cross-process file locks + OCC), but no warm caches |
| Config | must register the MCP server in the agent (see below) | zero config; just give the agent permission to run the tool |
| Exit codes / errors | structured error body `{ok:false,error:{code,message,…}}` | exit codes 0/2/1 + `--json` error body; conflicts carry `current_hash`, `changed_sections` |

**Rule of thumb:** MCP-capable agent → use MCP (faster, sturdier); writing a script or running ad hoc → CLI. The two can be mixed (against the same wiki).

### Connecting via MCP

Claude Code:
```bash
claude mcp add loom -- loom mcp --wiki-path /abs/path/to/my-wiki
```
Cursor (`~/.cursor/mcp.json`):
```json
{ "mcpServers": { "loom": { "command": "loom", "args": ["mcp", "--wiki-path", "/abs/path/to/my-wiki"] } } }
```

### Via CLI

Give the agent permission to run the tool and let it call `loom --wiki-path <root> <subcommand> [--json]`. Global options `--wiki-path` / `--json` go **before** the subcommand; command options like `--base-hash` go **after** it.

## 2. Installing `SKILL.md` into the agent

`SKILL.md` (shipped with the package, also at the repo root) is the **recipe** that orchestrates Loom's primitives into the ingest/query/lint **workflows** — it tells the agent when to call which primitive, which step is "you (the agent) judge," and which is the tool's bookkeeping. **Without it, the agent has parts but no blueprint.**

- **Claude Code**: install it as an Agent Skill (drop it into the skills directory), or reference its content in the system prompt / project instructions.
- **Cursor / others**: paste `SKILL.md` into project rules or the conversation context.
- **Your own agent**: concatenate `SKILL.md` into the system prompt; it already states "read `schema.md` and `purpose.md` before writing."

> The wiki's own `schema.md` is that library's **behavioral contract** (page types, naming, linking, citation rules). The agent should read it before every write — and that's literally `SKILL.md`'s first step.

## 3. When to use `--auto`, and when not to

`loom ingest --auto <PATH>` / `loom query --auto "<question>"` let **a built-in LLMProvider play the brain temporarily** and run the full workflow. This is an **optional edge**; it requires `pip install 'loom-wiki[auto]'`.

**Use it when:**
- You **don't have** a host agent (pure script / cron / batch job) and still want the convenience of "feed a file, get pages built";
- You want to **explicitly delegate the work to a cheap model** (set `LOOM_AUTO_PROVIDER=openai` and `LOOM_AUTO_BASE_URL` to a local Ollama/vLLM).

**Don't use it when:**
- You're **already inside** a capable host agent (Claude Code/Cursor) — there, let the host agent orchestrate the primitives directly: higher quality, fuller context. `--auto` would instead demote the judgment to a side-channel model.

Configuration (environment variables): `LOOM_AUTO_PROVIDER=anthropic|openai`, `LOOM_AUTO_MODEL`, `LOOM_AUTO_BASE_URL` (OpenAI-compatible endpoint, including Ollama/vLLM). See `examples/standalone_auto.py`.

> Even via `--auto`, source text is first wrapped as an **untrusted data block** before being fed to the provider — the same prompt-injection defense in depth.
