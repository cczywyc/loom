---
title: Agent 工作流：ReAct 与 Plan-and-Execute 对比
author: 测试用原创文章
---

# Agent 工作流：ReAct 与 Plan-and-Execute 对比

在构建 agent 工作流时，**ReAct** 与 **Plan-and-Execute** 是两条常见路线，各有取舍。本文做一个并列对比。

## ReAct

ReAct 让模型在每一步交替进行推理（reasoning）与行动（acting），边走边调整。它灵活、对突发输入反应快，但缺乏全局规划，长任务下容易跑偏。

## Plan-and-Execute

Plan-and-Execute 先一次性产出完整计划，再逐项执行。它对长任务更稳健，本质上依赖良好的**任务分解**。执行过程中常配合**反思**（reflection）：评估子任务结果、必要时回炉重规划。

## 工程落地

两条路线都可用 LangGraph 这类状态图框架实现：把每个推理/执行步骤建成节点，用边表达控制流，并在节点间共享状态。选哪条取决于任务长度与对可控性的要求。
