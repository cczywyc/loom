# M4 真实 agent Lint 流程验收报告（Task 4.4 Step 3）

> 用独立第三方 agent（Cursor CLI `cursor-agent`，model=auto，headless）按 `SKILL.md` 的 Lint 配方,对一座**人工注入了缺陷**的 wiki 跑完整体检流程,再用命令客观核查。

## 测试元信息

| 项 | 值 |
|---|---|
| 驱动 agent | Cursor CLI `cursor-agent`，`--model auto`，`-p --force --trust` |
| 体检靶库 | `/tmp/loom-lint-demo`（M3 演示库副本 + 注入缺陷） |
| 注入缺陷 | 删 `react.md`（→10 broken-link）、改 `raw/sources/article-a.md`（→1 stale）、加孤儿 `lonely-note`（→1 orphan） |
| 体检前 findings | `{broken-link: 10, stale: 1, orphan: 1}` |
| 测试日期 | 2026-06-10 |
| 总体结论 | **PASS ✅** |

## agent 实际动作（按 SKILL Lint 配方）

1. `loom lint --structural --fix --json` → 自动修：**10 页 source_hashes 回填 + index 重同步**。
2. 逐条处理剩余机械问题：
   - broken-link：判断 `react` 是被误删的核心概念 → **读相关页/来源还原内容、补建 `react` 页** → 一次性消除全部 10 条坏链。
   - orphan：给 `lonely-note` **补 4 条 `[[name|中文]]` 出链**接入网络。
   - stale：复查 `article-a-planning-patterns`、按 v2 来源**更新页面并刷新 source_hashes**。
3. `loom lint --candidates --json` → **17 条 possible-contradiction 逐条甄别,全部判为「共享 hub 页假阳性」排除**（langgraph/react/task-decomposition 等被多页共享但无对立论点）。
4. 产出一份给人看的体检报告（自动修/手工修/候选甄别/下一步阅读建议）。

## 客观核查（命令验证 agent 自述）

| # | 验收项 | 命令证据 | 结论 |
|---|---|---|---|
| 1 | 结构问题清零 | `lint_structural().ok` → **True**；findings `{}` | ✅ |
| 2 | broken-link 已解 | `react` 页已补建（`react` ∈ 页面列表）→ 10 坏链全消 | ✅ |
| 3 | orphan 已解 | `lonely-note` 正文含 **4** 处 `[[…]]` 出链 | ✅ |
| 4 | stale 已解 | 来源页更新 + source_hashes 刷新，无 stale finding | ✅ |
| 5 | 候选交判断 | 17 候选全部由 agent 甄别(排除),工具未代下结论 | ✅ |

体检前 12 项结构 findings → 体检后 **0**；agent 报告的"结构 findings 0 / 库健康良好"与命令核查一致。

## 设计验证

- **"工具浮现、agent 判断"成立**：lint 报机械问题(确定)、candidates 浮现可疑点(启发式)；agent 补页/补链/更新(判断)、并逐条甄别候选。分工清晰。
- **印证 4.3 的噪声观察**：密链库上 possible-contradiction 偏多(17 条),但全是共享 hub 的假阳性——agent 凭 reason 快速排除,正是设计预期(工具不该替它下结论)。
- **`--fix` 安全边界正确**：自动只动 index/source_hashes,broken-link/stale/orphan 留给 agent。

## 结论

**M4 Lint 全链路在真实 agent 上跑通**：注入的三类缺陷被 100% 报出并由 agent 按配方逐一修复,17 条语义候选全部交由 agent 判断,最终结构体检清零。靶库 `/tmp/loom-lint-demo` 保留备查。
