# M3 真实 agent 端到端验收清单

> 工具 + 配方的最终裁判，只能是**真实 agent 跑真实工作流**。本清单由人工执行（用 Claude Code 之类的宿主 agent），逐项打勾。
> 产出的演示库（`/tmp/loom-demo`）随后还会作为 M4 lint 的验收靶子，请勿急着删。

测试材料（本目录 `fixtures/`）：
- `article-a.md`、`article-b.md`：两篇中文技术文章，**故意共享实体**（ReAct、LangGraph、任务分解），用于检验 find_related 去重/并入。
- `article-c.pdf`：一篇英文短文（同主题），用于检验 PDF 摄入与跨语言连图。

---

## Step 1 · 准备

```bash
export PATH="$HOME/.local/bin:$PATH"
REPO=/home/cczywyc/workspace/code/personal_projects/loom

# 1) 用 research 模板建一座演示库
"$REPO/.venv/bin/loom" init /tmp/loom-demo --template research

# 2) 把 fixtures 拷到手边（agent 会 register 它们）
cp "$REPO"/tests/e2e/fixtures/article-*.{md,pdf} /tmp/

# 3) 把 loom 接进 Claude Code（MCP），指向这座库
claude mcp add loom -- "$REPO/.venv/bin/loom" mcp --wiki-path /tmp/loom-demo
```

- [ ] 演示库已 `init`（`/tmp/loom-demo/.loom` 存在）
- [ ] loom MCP 已接入 Claude Code（或改用 CLI shell-out 亦可）
- [ ] 已把 `SKILL.md` 提供给 agent（配为技能 / 粘进上下文）

## Step 2 · 执行 + 逐项检查

### 2.1 摄入文章 A（对 agent 说「按 SKILL 吸收 /tmp/article-a.md」）
- [ ] **先讨论再动笔**：agent 先列了 3–5 条关键收获并和你确认侧重点，才开始写
- [ ] 建了 1 个 `source` 摘要页 + **≥3 个** 实体/概念页（如 react、langgraph、task-decomposition…）
- [ ] 正文链接用 `[[name|中文显示名]]` 形式
- [ ] `index.md` 与 `log.md` 已自动更新（`loom --wiki-path /tmp/loom-demo index` / `cat .../wiki/log.md`）

### 2.2 摄入文章 B（与 A 有重叠实体）
- [ ] 重叠实体（ReAct / LangGraph / 任务分解）走了 `find_related` 并**并入已有页**（update），**而非重建**重复页
- [ ] 新实体（Plan-and-Execute / 反思）才建了新页

### 2.3 跨 A/B 提问（如「ReAct 和 Plan-and-Execute 有什么区别？」）
- [ ] 答案**只基于 wiki 页面**，且逐条带 `[[引用页]]`
- [ ] 有价值的回答被沉淀进 `wiki/queries/`

### 2.4 看图谱
- [ ] `loom --wiki-path /tmp/loom-demo graph --json`：A/B（+C）的页面**连成一张网**，不是两座孤岛

### 2.5 演进论点
- [ ] agent 摄入后**评估并（按需）更新了** `purpose.md` 的「演进中的论点」

### 2.6（可选）PDF
- [ ] 摄入 `/tmp/article-c.pdf` 成功，其页面与已有图谱相连（ReAct/LangGraph 等）

## Step 3 · 记录结果

| 检查项 | 结果（✅/❌） | 备注 / 暴露的配方问题 |
|---|---|---|
| 2.1 先讨论再动笔 | | |
| 2.1 source + ≥3 页 | | |
| 2.1 链接格式 | | |
| 2.1 index/log 同步 | | |
| 2.2 重叠实体并入 | | |
| 2.3 引用 + 沉淀 | | |
| 2.4 连图非孤岛 | | |
| 2.5 purpose 更新 | | |
| 2.6 PDF（可选） | | |

> 若某项暴露出**配方问题**（agent 行为不符预期），多半是 `SKILL.md` 措辞不够无歧义：记下来，回改 `SKILL.md` 的相应步骤，再重跑。这正是本步骤的价值——用真实 agent 打磨配方。

## 结论

- [ ] 全部必检项通过 → M3 端到端验收 PASS，保留 `/tmp/loom-demo` 供 M4 lint 验收
