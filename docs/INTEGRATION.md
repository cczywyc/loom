# Integrating Loom into your agent

Loom 是无内置大脑的工具:**你的 agent 是大脑,Loom 是双手**。接入有两条传输,选一条即可——能力完全等价。

## 一、选型:MCP 模式 vs CLI shell-out 模式

| | **MCP 模式**(常驻 server) | **CLI shell-out 模式** |
|---|---|---|
| 形态 | `loom mcp` 常驻进程,agent 经 MCP 协议调 14 个 `wiki_*` 工具 | agent 直接跑 `loom ...` 命令(`--json` 取结构化输出) |
| 适合 | 支持 MCP 的 agent(Claude Code、Cursor…);**密集 ingest/query 循环** | 任何能跑 shell 的 agent / 脚本 / cron;一次性任务 |
| 性能 | **更快**:进程常驻 → 暖搜索索引、暖图谱、文件锁都在内存;jieba 词典只加载一次 | 每次冷启动(重开索引、重读文件、重载 jieba ~1s) |
| 并发 | 常驻进程是天然的写串行化点 | 多进程并发安全(跨进程文件锁 + OCC),但无暖缓存 |
| 配置 | 需在 agent 里登记 MCP server(见下) | 零配置,给 agent 工具运行权限即可 |
| 退出码/错误 | 结构化错误体 `{ok:false,error:{code,message,…}}` | 退出码 0/2/1 + `--json` 错误体;冲突体含 `current_hash`、`changed_sections` |

**经验法则:** 用 MCP 的 agent → 走 MCP(更快、更稳);写脚本或临时跑 → CLI。两者可混用(同一座库)。

### 接 MCP

Claude Code:
```bash
claude mcp add loom -- loom mcp --wiki-path /abs/path/to/my-wiki
```
Cursor(`~/.cursor/mcp.json`):
```json
{ "mcpServers": { "loom": { "command": "loom", "args": ["mcp", "--wiki-path", "/abs/path/to/my-wiki"] } } }
```

### 走 CLI

给 agent 工具运行权限,让它调 `loom --wiki-path <根> <子命令> [--json]`。全局选项 `--wiki-path` / `--json` 放在子命令**之前**;`--base-hash` 等命令选项放在子命令**之后**。

## 二、把 `SKILL.md` 装进 agent

`SKILL.md`(随包分发,也在仓库根)是把 Loom 原语编排成 ingest/query/lint **工作流的配方**——它告诉 agent 何时调哪个原语、哪步是"你(agent)判断"、哪步是工具记账。**没有它,agent 只有零件没有图纸。**

- **Claude Code**:作为 Agent Skill 安装(放进技能目录),或在系统提示/项目说明里引用其内容。
- **Cursor / 其它**:把 `SKILL.md` 内容粘进项目规则(rules)或对话上下文。
- **自建 agent**:把 `SKILL.md` 拼进 system prompt;它已写明"先读 `schema.md` 与 `purpose.md` 再动笔"。

> wiki 自带的 `schema.md` 是该库的**行为契约**(页面类型、命名、链接、引用规则)。agent 每次动笔前都应先读它——`SKILL.md` 第一步就是这个。

## 三、`--auto` 何时用、何时不用

`loom ingest --auto <PATH>` / `loom query --auto "<问题>"` 让**工具内置一个 LLMProvider 临时扮演大脑**,跑完整工作流。这是**可选边缘**,需 `pip install 'loom-wiki[auto]'`。

**该用:**
- 你**没有**宿主 agent(纯脚本 / cron / 批处理),又想要"喂一个文件、自动建页"的便利;
- 想**显式把活委托给一个便宜模型**(设 `LOOM_AUTO_PROVIDER=openai`、`LOOM_AUTO_BASE_URL` 指向本地 Ollama/vLLM)。

**不该用:**
- 你**已经在**一个能力强的宿主 agent 里(Claude Code/Cursor)——那时让宿主 agent 直接编排原语,质量更高、上下文更全,`--auto` 反而是把判断降级给一个旁路模型。

配置(环境变量):`LOOM_AUTO_PROVIDER=anthropic|openai`、`LOOM_AUTO_MODEL`、`LOOM_AUTO_BASE_URL`(OpenAI 兼容端点,含 Ollama/vLLM)。例子见 `examples/standalone_auto.py`。

> 即便走 `--auto`,源文本也先被包成**不可信数据块**才喂给 provider——同一条防注入纵深。
