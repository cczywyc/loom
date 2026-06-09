# Agent via CLI —— shell-out 原语调用示例

本文件给**通过 shell 调用 loom 的 agent**看：每条命令是一个确定性原语，`--json` 让输出可机械解析。
推理（抽取/判断/综合/写作）由你这个宿主 agent 做；loom 只做解析/检索/存储/校验/记账。

> 约定：`--json` 是全局开关，放在子命令前（`loom --json read X`）。
> 退出码：`0` 成功；`2` = 校验失败 / 冲突（`VALIDATION_ERROR` / `CONFLICT`，应重读再试）；`1` 其他错误。
> wiki 定位：在库目录树内任意位置直接调用即可（自动向上找 `.loom/`），或用全局 `--wiki-path PATH`。

## 0. 建库（一次）

```bash
loom init ./my-wiki          # 生成 wiki 骨架（raw/ wiki/ schema.md purpose.md .loom/ ...）
cd ./my-wiki
```

## 1. 取上下文（动笔前先读）

```bash
loom index                   # 内容目录（index.md），先读它定位已有内容
loom schema                  # 行为契约：页面类型、命名、链接、ingest 规则
loom purpose                 # 目标与演进论点
loom --json list --type concept          # 列页面摘要（可按 --type / --tag 过滤）
# loom --json search "查询词"             # 关键词检索（M2 实现后可用）
```

## 2. 摄入来源（ingest 的确定性部分）

```bash
loom --json register papers/attention.pdf
# → {"path": "raw/sources/attention.pdf", "sha256": "...", "is_new": true}
loom parse raw/sources/attention.pdf      # 抽出纯文本 + 元数据（--json 出完整结构）
# —— 然后由你（agent）阅读 parsed 文本，抽实体/概念/论点，判断新建 vs 并入 ——
```

## 3. 写页面（OCC：先读取 hash，再覆写）

```bash
# 新建页面：内容可来自文件或 stdin
loom write andrej-karpathy --from-file page.md
cat page.md | loom write andrej-karpathy        # 等价：从 stdin 读

# 覆写已存在页面：必须带上一次读到的 content_hash 作为 --base-hash
H=$(loom --json read llm-wiki | jq -r .content_hash)
loom write llm-wiki --from-file new.md --base-hash "$H"
# 若中途别人改过该页 → 退出码 2 + CONFLICT，重新 read 取新 hash 再试
```

## 4. 段级更新（非破坏，只动一节）

```bash
echo "与 RAG 路线之争 ⚠️" | loom update llm-wiki --section 争议 --op append
loom update llm-wiki --section 争议 --op replace --from-file note.md
loom update llm-wiki --op add-section --section 参考 --from-file refs.md
echo 'summary: "持久增量编译的个人知识库"' | loom update llm-wiki --op set-frontmatter
# update 在锁内 read-modify-write，天然无丢失更新；可选 --base-hash 再加一层 OCC
```

## 典型 ingest 序列（M3 的 SKILL.md 会正式编排，这里是骨架）

```
register → parse → [agent 读+抽取] → (每个候选) find_related(M2) →
[agent 判断新建/并入] → write / update（工具自动同步 index.md + log.md）
```
