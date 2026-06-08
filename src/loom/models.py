import re
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError

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
