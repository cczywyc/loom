# Loom 检索与图谱手动测试报告（M2）

> 对 M2 交付的检索/图谱能力做端到端手动验证：CLI 的 `search` / `find-related` / `graph` 三命令，外加 MCP 的三个新工具。

## 测试元信息

| 项 | 值 |
|---|---|
| 被测对象 | `loom search` / `loom find-related` / `loom graph`；MCP `wiki_search` / `wiki_find_related` / `wiki_graph` |
| 测试库 | `~/loom-test-m2`（5 个互链概念页；测试后已删除） |
| 源文档 | `~/planning-design-microsoft.md`（注册入库作来源） |
| 调用方式 | `.venv/bin/loom --wiki-path ~/loom-test-m2 <cmd>`；`--json` 为全局开关，置于子命令前 |
| 测试日期 | 2026-06-09 |
| 总体结论 | **全部符合预期 ✅，未发现缺陷** |

### 测试库结构（5 页互链）

```
planning-design   ──▶ structured-output, task-decomposition
structured-output ──▶ planning-design
task-decomposition──▶ planning-design, iteration
iteration         ──▶ task-decomposition
multi-agent       ──▶ planning-design
```

---

## Step A — `search`（BM25 关键词检索）

| 子项 | 测试内容 | 预期 | 实际 | 结论 |
|---|---|---|---|---|
| A1 | `search "任务分解"` | `task-decomposition` 排第一，带 snippet | `2.35 task-decomposition …` 居首，其后 planning-design / iteration | ✅ |
| A2 | `--json search "结构化输出"` | `structured-output` 排第一 | `4.59 structured-output`，iteration 次之 | ✅ |
| A3 | `search "规划" --limit 2` | 只返回 2 条 | 返回 planning-design / multi-agent 两条 | ✅ |
| A4 | `--json search "zzz不存在词xyzzy"` | 返回 `[]`，不报错 | `output=[]` | ✅ |
| A5 | `--json search "任务" --mode vector` | `VALIDATION_ERROR`，退出 2 | `{"code":"VALIDATION_ERROR",...vector/hybrid 留待 M6}`，exit 2 | ✅ |

**结论**：✅ 中文查询排序正确、字段加权使标题命中优先、`--limit` 生效、无命中返回空数组、未实现模式被挡（退出码 2）。

## Step B — `find-related`（实体消解供给侧）

| 子项 | 测试内容 | 预期 | 实际 | 结论 |
|---|---|---|---|---|
| B1 | `find-related "如何把复杂任务分解成有序的子任务"` | 关键词命中 + 图邻居，各带 reason | 见下 | ✅ |
| B2 | 同上 `--json` 看 `reason` 字段 | 区分 "keyword match" / "linked from" | 见下 | ✅ |
| B3 | `--json find-related "完全无关的内容 qqqq"` | 仍返回数组（不报错） | `type: list` | ✅ |

实际输出（B1/B2）：
```
3.510  task-decomposition   reason='keyword match: 复杂/任务/分解/的/子'
1.137  planning-design      reason='keyword match: 复杂/任务/的/子'
1.053  iteration            reason='linked from task-decomposition'
0.341  structured-output    reason='linked from planning-design'
0.341  multi-agent          reason='linked from planning-design'
```

**结论**：✅ 两路信号都正确浮现——直接关键词命中（task-decomposition / planning-design，reason 列出命中 token）与命中页的图邻居（iteration / structured-output / multi-agent，reason="linked from …"，按 0.3 降权），并按分排序。这正是 ingest 时"新建 vs 并入"判断的候选供给。

## Step C — `graph`（wikilink 图谱）

| 子项 | 测试内容 | 预期 | 实际 | 结论 |
|---|---|---|---|---|
| C1 | `graph`（全图） | 5 节点 + 全部边 | 5 节点、7 条有向边 | ✅ |
| C2 | `graph planning-design --depth 1` | 仅 depth-1 邻居（不含 iteration） | `{multi-agent, planning-design, structured-output, task-decomposition}` | ✅ |
| C3 | `graph planning-design --depth 2` | 扩展到含 iteration | 5 节点全含 | ✅ |
| C4 | `--json graph planning-design --depth 1` | nodes + edges，只含子图内部边 | nodes 4 个、edges 仅子图内 5 条 | ✅ |

**结论**：✅ 全图/子图正确；depth-1 只取出边+入边一层邻居（`iteration` 距 planning-design 2 跳故被排除），depth-2 才纳入；`--json` 输出可直接喂 agent 的 `{nodes, edges}`，且只画子图内部边（无悬空边）。

## Step D — MCP（三个新工具，真实 stdio 子进程）

| 子项 | 测试内容 | 预期 | 实际 | 结论 |
|---|---|---|---|---|
| D1 | 工具总数 | 12（M0/M1 的 9 + M2 的 3） | `total tools: 12` | ✅ |
| D2 | 三个 M2 工具存在 | `wiki_search`/`wiki_find_related`/`wiki_graph` | `M2 tools present: True` | ✅ |
| D3 | `wiki_search` 往返 | 命中 task-decomposition | `True` | ✅ |
| D4 | `wiki_find_related` 往返 | 返回相关页 | `True` | ✅ |
| D5 | `wiki_graph` 往返 | 返回 nodes/edges | `True` | ✅ |

**结论**：✅ 通过真实 `loom mcp` stdio 子进程（即 Claude Code 走的同一条协议）验证，三个 M2 原语在 MCP 侧同样可达、行为一致。

---

## 汇总

| 步骤 | 主题 | 结论 |
|---|---|---|
| A | `search`（排序/json/limit/no-hits/mode 闸门） | ✅ |
| B | `find-related`（关键词 + 图邻居 + reason） | ✅ |
| C | `graph`（全图/子图/depth/json） | ✅ |
| D | MCP 三工具（stdio 子进程往返） | ✅ |

**结论**：M2 检索与图谱能力在 5 页真实互链库上工作正常，CLI 三命令与 MCP 三工具全部符合预期，未发现缺陷。检索排序合理（字段加权使标题命中优先）、find-related 双路候选与理由清晰、图谱子图遍历正确，CLI 与 MCP 行为一致（同一 `Loom` 代码路径）。

## 备注

- 自动化测试同步全绿：`uv run pytest -q` → 81 passed；其中 `test_perf` 验证 200 页库 warm `search` <200ms（架构 §九"index+BM25 已足够"实证）。
- 已知特性（非缺陷）：写入时无引号日期读回带引号（序列化稳定）；极小语料（≤2 页）下 BM25 已由 IDF 下限钳位修复，本次 5 页库不触及。
- 复现方式：按本报告 Setup 建 5 页互链库，依次执行 Step A–D 命令即可。
