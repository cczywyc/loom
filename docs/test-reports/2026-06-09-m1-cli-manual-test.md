# Loom CLI 手动测试报告（M1）

> 对 M1 交付的 `loom` CLI 做端到端手动验证，覆盖测试指南的 Step 1–7。

## 测试元信息

| 项 | 值 |
|---|---|
| 被测对象 | `loom` CLI（M1 全套命令），经 `.venv/bin/loom` 调用 |
| 测试库 | `~/loom-test`（测试完成后已删除） |
| 源文档 | `~/planning-design-microsoft.md`（Microsoft「Planning Design」课程，270 行，**无 frontmatter**） |
| 调用方式 | 每条命令带 `--wiki-path ~/loom-test`；`--json` 为全局开关，置于子命令前 |
| 测试日期 | 2026-06-09 |
| 总体结论 | **7 / 7 步全部符合预期 ✅，未发现缺陷** |

---

## Step 1 — 建库 + 读上下文

- **测试内容**：`loom init ~/loom-test`；随后 `index` / `schema` / `purpose`。
- **预期结果**：init 退出 0；`index` 为 `# Index` + 六个空的 `## <type>` 节；`schema`/`purpose` 有内容；目录结构完整。
- **实际结果**：
  - `initialized loom wiki at /home/cczywyc/loom-test`，exit 0；
  - `index` 输出 `# Index` 与 `## entities/concepts/sources/queries/synthesis/comparisons` 六空节；
  - `schema` 打印「# Schema —— 本 wiki 的行为契约」，`purpose` 打印「# Purpose —— 本库的目标与演进论点」；
  - 目录含 `.loom`、`.obsidian`、`raw/{sources,assets}`、`wiki/{六类型目录}`。
- **结论**：✅ 符合。

## Step 2 — 摄入来源（register + parse）

- **测试内容**：`--json register ~/planning-design-microsoft.md` 执行两次；`parse raw/sources/planning-design-microsoft.md`。
- **预期结果**：首次 `is_new: true`；二次同 `path` 但 `is_new: false`（按内容 SHA256 去重）；`parse` 输出文档正文。
- **实际结果**：
  - 首次 `{"path": "raw/sources/planning-design-microsoft.md", "sha256": "d619...", "is_new": true}`；
  - 二次 sha256 相同且 `"is_new": false`；
  - `parse` 输出文档原文（含 `# Planning Design`）；文件已拷入 `raw/sources/`。
- **结论**：✅ 符合（去重生效）。
- **说明**：该文档无 frontmatter，故 `parse` 把整篇当正文输出、`metadata` 为空——符合 markdown 解析器设计。

## Step 3 — 写两个互链页面

- **测试内容**：经 stdin 写 `planning-design`（正文链 `[[structured-output]]`），再写 `structured-output`（正文链 `[[planning-design]]`）。
- **预期结果**：两页均 `created`，退出 0；第一页因目标尚未存在而有**悬空链接 warning**，第二页无 warning。
- **实际结果**：
  - `created planning-design (hash abdf...)` + `warning: dangling wikilink: [[structured-output]] (target not found; lint will track it)`；
  - `created structured-output (hash 412e...)`，无 warning。
- **结论**：✅ 符合（悬空告警不拦写入，正是设计意图——避免互链页"先有鸡先有蛋"）。

## Step 4 — 自动记账（index / log / list）

- **测试内容**：`index`；`cat wiki/log.md`；`--json list --type concept`。
- **预期结果**：`index` 的 concepts 节按 name 字典序列出两页带摘要；`log.md` 有 1×REGISTER + 2×WRITE；`list` 返回两页 JSON。
- **实际结果**：
  - concepts 节中 `[[planning-design|…]] — 把复杂任务…` 排在 `[[structured-output|…]]` 之前（字典序正确）；
  - `log.md` 三行齐全（REGISTER + planning-design WRITE + structured-output WRITE）；
  - `list` 返回两个对象，含 `name/type/title/summary/tags/updated`。
- **结论**：✅ 符合（写页副作用自动同步 index + log）。

## Step 5 — 段级更新（非破坏性）

- **测试内容**：`echo "需评估子任务结果并迭代 ⚠️" | loom update planning-design --section 要点 --op append`；随后 `read planning-design`。
- **预期结果**：`updated`，退出 0；「要点」节追加该行，其余（引言、frontmatter）原样保留。
- **实际结果**：`updated planning-design (hash fe11...)`；读回后「要点」节既有原两条 bullet，又新增追加行；引言段与 frontmatter 完整。
- **结论**：✅ 符合（只动目标节，未覆盖全页）。
- **说明**：读回时 frontmatter 日期显示为带引号的 `'2026-06-09'`——这是「日期归一化 + 序列化稳定」的正常往返结果（写入时即便不带引号也会被接受并归一），属预期行为，保证 hash 稳定/OCC 可靠。

## Step 6 — 冲突保护（OCC）⭐ 重点

| 子项 | 测试内容 | 预期结果 | 实际结果 | 结论 |
|---|---|---|---|---|
| 6b | 带**正确** `--base-hash` 覆写 | `updated`，退出 0 | `updated planning-design (hash 1590...)`，exit 0 | ✅ |
| 6c | 已存在页**不带** `--base-hash` 覆写 | `CONFLICT`，退出 2 | `error [CONFLICT]: ...read it first and pass base_hash...`，exit 2 | ✅ |
| 6d | 带**过期** hash + `--json` 覆写 | 结构化 CONFLICT，退出 2 | `{"ok": false, "error": {"code": "CONFLICT", "message": "...changed on disk... re-read and retry"}}`，exit 2 | ✅ |

- **结论**：✅ 符合——OCC 三种情形（正确 / 缺失 / 过期）行为完全正确，退出码与 JSON 错误体均对。

## Step 7 — 错误退出码

| 子项 | 测试内容 | 预期结果 | 实际结果 | 结论 |
|---|---|---|---|---|
| 7a | `read nope`（缺页） | `NOT_FOUND`，退出 1 | `error [NOT_FOUND]: page 'nope' not found`，exit 1 | ✅ |
| 7b | 同上加 `--json` | JSON 错误，退出 1 | `{"ok": false, "error": {"code": "NOT_FOUND", ...}}`，exit 1 | ✅ |
| 7c | `write Bad_Name`（非 kebab） | `VALIDATION_ERROR`，退出 2 | `{"ok": false, "error": {"code": "VALIDATION_ERROR", "message": "name 'Bad_Name' is not kebab-case"}}`，exit 2 | ✅ |

- **结论**：✅ 符合——退出码语义清晰：**0 成功 / 2 数据问题（校验失败或冲突）/ 1 其它错误**。

---

## 汇总

| 步骤 | 主题 | 结论 |
|---|---|---|
| 1 | init + 读上下文 | ✅ |
| 2 | register（去重）+ parse | ✅ |
| 3 | 写互链页 + 悬空告警 | ✅ |
| 4 | index/log/list 自动记账 | ✅ |
| 5 | 段级更新非破坏 | ✅ |
| 6 | OCC 冲突保护 | ✅ |
| 7 | 错误退出码 | ✅ |

**结论**：CLI 全链路（摄入 → 写 / 改 → 查 → 冲突 / 错误处理）在真实文档 `planning-design-microsoft.md` 上工作正常，Step 1–7 全部符合预期，未发现缺陷。

唯一一处「与直觉略不同但正确」的现象：写入时无引号的日期，读回会显示成带引号——这是为保证 hash 稳定 / OCC 可靠而做的归一化，属预期行为。

## 备注

- 本次未覆盖：MCP 传输（需接入 Claude Code 的人工冒烟，见测试指南 Step 8）、检索 `search` / 图谱 `graph` / `find_related`（属 M2，尚未实现）。
- 复现方式：按测试指南 Step 1–7，将源文档替换为 `~/planning-design-microsoft.md` 即可。
