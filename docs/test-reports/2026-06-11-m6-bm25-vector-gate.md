# Task 6.3 决策门记录 · `[vector]` 检索后端 —— 跳过

> 计划 Task 6.3 是"可选门":执行到此先用 M3 演示库 + 20 个真实问题评估 BM25 命中率，**≥85% 即跳过 vector 后端**。本文是该门的执行与结论记录。

## 方法

- **靶库**：M3 演示库 `/tmp/loom-demo`（真实 agent 摄入产出的 11 页中文知识：AI Agent 规划、ReAct、Plan-and-Execute、LangGraph、任务分解、反思、结构化输出等）。
- **检索**：`Loom.search(q, limit=5)` —— BM25（rank-bm25）+ jieba 分词，字段加权 title×3/tags×2/body×1。
- **样本**：20 个自然语言问题，每个人工标注「可接受的相关页集合」。
- **命中判据**：相关页出现在 **top-3**（主）/ top-5（辅）。

## 结果

| 指标 | 命中 | 命中率 |
|---|---|---|
| **top-3** | **18 / 20** | **90%** |
| top-5 | 19 / 20 | 95% |

**两个非完美命中：**
1. 「LangGraph 是什么框架」—— langgraph 在 top-5（top-3 外）；
2. 「长任务更稳健 先规划后执行」—— 严格判为 miss，但 top-1 实为 `react-vs-plan-and-execute-diff`（正是讲 Plan-and-Execute 的对比页，属语义相关），故实际可用性更高。

## 结论

**90% top-3 / 95% top-5，均 ≥ 85% 门槛 → 决策门通过 → 跳过 Task 6.3（不实现 vector 后端）。**

个人/单人尺度（数十～数百页）下，**index + BM25 + jieba 的关键词检索已足够**，引入 embedding 端点 + 向量库（`.loom/vectors.json` + 余弦/RRF）属过度工程，且会新增网络/依赖面，违背"窄依赖、可离线"的取向。架构 §九「index+BM25 已足够」的判断得到实测背书。

**重启条件（何时再考虑 vector）：** 库规模显著增大（如 >1000 页）、或出现大量"同义不同词"的查询使关键词召回明显下降时，再按计划预留的形状实现 `search/vector.py`（`mode="vector"/"hybrid"` + FakeEmbedder 测试）。本结论将写入 README「为什么没有向量检索」一节（Task 6.4）。
