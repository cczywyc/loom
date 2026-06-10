# M3 真实 agent 端到端验收报告（agent-driven ingest）

> 用一个**独立的第三方 agent**（Cursor CLI `cursor-agent`，model=auto，headless `-p` 模式）按 `SKILL.md` 的配方实际驱动 loom CLI 完成 ingest/query 全流程，再用命令客观核查产出。

## 测试元信息

| 项 | 值 |
|---|---|
| 驱动 agent | Cursor CLI `cursor-agent` 2026.06.04，`--model auto`，`-p --force --trust`（非交互、自动批准工具） |
| 工具接入方式 | CLI shell-out：agent 自行 `cat SKILL.md` 后按配方调 `loom ...` 命令 |
| 演示库 | `/tmp/loom-demo`（research 模板） |
| 来源 | `article-a.md`、`article-b.md`（共享实体）、（PDF 本轮未要求） |
| 测试日期 | 2026-06-10 |
| 总体结论 | **PASS ✅，全部客观核查项通过** |

> 说明：M3 DoD 原文写「真实 Claude Code」，本次用了同样独立的 Cursor CLI——比"自己建工具的 agent"更独立，更能检验配方对任意宿主 agent 的可执行性。

## agent 实际产出（11 页）

| type | 页面 |
|---|---|
| entity | `andrej-karpathy`、`langgraph` |
| concept | `agent-planning-design`、`plan-and-execute`、`react`、`reflection`、`structured-output`、`task-decomposition` |
| source | `article-a-planning-patterns`、`article-b-react-vs-plan-execute` |
| query | `react-vs-plan-and-execute-diff` |

## 客观核查结果

| # | 验收项 | 命令证据 | 结论 |
|---|---|---|---|
| 1 | 页面分布 | 11 页：2 entity / 6 concept / 2 source / 1 query；source≥1 ✓，entity+concept≥3 ✓ | ✅ |
| 2 | 自动记账 | `log.md`：2× REGISTER、11× WRITE、3× UPDATE | ✅ |
| 3 | **重叠实体并入而非重建** | `react` / `langgraph` / `task-decomposition` 均有 `UPDATE … add_section`；目录中**无** `*-1.md` 重复页 | ✅ |
| 4 | 链接格式 | 抽查得 `[[langgraph\|LangGraph]]`、`[[plan-and-execute\|Plan-and-Execute]]` 等 `[[name\|中文]]` 形态 | ✅ |
| 5 | query 沉淀 + 引用 | `wiki/queries/react-vs-plan-and-execute-diff.md` 存在，含 `[[react]] [[plan-and-execute]] [[article-b-…]]` 等引用 | ✅ |
| 6 | 图谱连通 | `graph --json`：**11/11 节点连通 → 一张网**，47 条边（A/B 经共享实体连成整体，无孤岛） | ✅ |
| 7 | purpose 回路 | `purpose.md`「演进中的论点」由「（暂无）」替换为 5 条带 `[[来源页]]` 的判断 | ✅ |

### 关键项详证（#3 去重并入）
```
| UPDATE | react | add_section section=工作流视角
| UPDATE | langgraph | add_section section=工作流实现
| UPDATE | task-decomposition | add_section section=与 Plan-and-Execute 的关系
```
吸收 article-b 时，三个与 article-a 重叠的实体/概念都**经 find-related 找到已有页、用 update 追加新节并入**，没有重建重复页——这是整套配方最关键的"实体消解"行为，真实 agent 真正做到了。

## 未覆盖项（headless 模式固有限制）

- SKILL「先与用户讨论关键收获再动笔」：非交互 `-p` 模式无人在环，无法演示。其余步骤全部覆盖并通过。

## 过程备注（踩坑记录）

- 直接用 `--workspace /tmp` 会让 cursor-agent 报 `Cannot use this model`；去掉即可。
- `cursor-agent` 的 `--model auto` 在额度紧张时，小请求可过、大任务被挡（`out of usage`）；额度恢复后整套流程一次跑通。
- Antigravity CLI（`agy`）单条 shell 命令可执行，但本轮一把梭的大 prompt 未稳定完成多步建页；最终以 cursor-agent 跑通。

## 结论

**M3 端到端验收 PASS。** 一个独立第三方 agent 仅凭 `SKILL.md` + loom CLI，就完成了"两篇文章摄入（含重叠实体并入）+ 跨文章带引用问答 + 沉淀 query 页 + 更新 purpose 论点"，且产出经命令逐项核查无误。演示库 `/tmp/loom-demo`（11 页、47 边、一张连通图）保留，作为 M4 lint 的验收靶子。
