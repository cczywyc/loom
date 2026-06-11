import re
from datetime import date, datetime
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

from loom.errors import ValidationFailed

PageType = Literal["entity", "concept", "source", "query", "synthesis", "comparison"]
TYPE_DIRS: dict[str, str] = {
    "entity": "entities",
    "concept": "concepts",
    "source": "sources",
    "query": "queries",
    "synthesis": "synthesis",
    "comparison": "comparisons",
}


class PageMeta(BaseModel):
    type: PageType
    title: str
    summary: str = ""  # index.md 一行摘要
    sources: list[str] = Field(default_factory=list)  # 页级来源（raw/ 相对路径）
    source_hashes: dict[str, str] = Field(default_factory=dict)
    created: str  # ISO date 字符串，序列化稳定
    updated: str
    tags: list[str] = Field(default_factory=list)

    @field_validator("created", "updated", mode="before")
    @classmethod
    def _coerce_date_to_str(cls, v: object) -> object:
        # YAML 会把无引号的 2026-06-08 解析成 date 对象；归一为 ISO 字符串，保持序列化稳定。
        if isinstance(v, datetime):
            return v.date().isoformat()
        if isinstance(v, date):
            return v.isoformat()
        return v


class WikiPage(BaseModel):
    name: str  # kebab-case 文件名（不含 .md），全库唯一
    meta: PageMeta
    body: str
    content_hash: str = ""  # 读取时的磁盘 sha256（OCC 用），构造时为空


class PageSummary(BaseModel):
    name: str
    type: PageType
    title: str
    summary: str = ""
    tags: list[str] = Field(default_factory=list)
    updated: str = ""


class WriteResult(BaseModel):
    ok: bool
    name: str
    path: str
    created: bool
    content_hash: str
    warnings: list[str] = Field(default_factory=list)


class SourceRef(BaseModel):
    path: str
    sha256: str
    is_new: bool


class ParsedDocument(BaseModel):
    source_path: str
    text: str
    metadata: dict = Field(default_factory=dict)
    assets: list[str] = Field(default_factory=list)


class Hit(BaseModel):
    name: str
    title: str
    type: PageType
    score: float
    snippet: str


class PageRef(BaseModel):
    name: str
    title: str
    type: PageType
    score: float
    reason: str


class Patch(BaseModel):
    op: Literal["replace", "append", "add_section", "set_frontmatter"]
    section: str | None = None
    content: str


class GraphNode(BaseModel):
    name: str
    title: str
    type: str


class GraphEdge(BaseModel):
    src: str
    dst: str


class Graph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class Finding(BaseModel):
    kind: Literal[
        "orphan", "broken-link", "bad-frontmatter", "bad-name", "stale", "duplicate-title"
    ]
    page: str
    message: str
    fixable: bool = False


class LintReport(BaseModel):
    findings: list[Finding]

    @property
    def ok(self) -> bool:
        return not self.findings


class Candidate(BaseModel):
    """启发式浮现、交 agent 判断的语义可疑对象（工具不下结论，只给 reason）。"""

    kind: Literal["possible-contradiction", "sparse-area", "stale-cluster"]
    pages: list[str]
    reason: str


class ReviewItem(BaseModel):
    """暂存待人审的高风险改动：apply 时走正常 write_page（含校验+OCC）才真正落盘。"""

    id: str  # <seq>-<name>，即 .loom/review/ 下的文件名
    name: str
    content: str  # 待写入的整页 markdown
    base_hash: str | None = None
    diff: str  # 与当前页的 unified diff（给人看）
    staged_at: str


_FM_DELIM = re.compile(r"^---\s*$", re.M)


def loads_page(name: str, text: str) -> WikiPage:
    if not text.startswith("---"):
        raise ValidationFailed(f"page '{name}': missing frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValidationFailed(f"page '{name}': unterminated frontmatter")
    try:
        meta = PageMeta(**(yaml.safe_load(parts[1]) or {}))
    except (yaml.YAMLError, ValidationError) as e:
        raise ValidationFailed(f"page '{name}': invalid frontmatter: {e}") from e
    return WikiPage(name=name, meta=meta, body=parts[2].strip("\n"))


def dumps_page(page: WikiPage) -> str:
    fm = yaml.safe_dump(page.meta.model_dump(), allow_unicode=True, sort_keys=False)
    return f"---\n{fm}---\n\n{page.body.rstrip()}\n"
