from pathlib import Path

from loom.config import LoomPaths
from loom.core.graph import GraphIndex
from loom.core.hash import register_source
from loom.core.scaffold import init_wiki
from loom.core.store import WikiStore
from loom.errors import NotFound, ValidationFailed
from loom.lint.candidates import lint_candidates as _lint_candidates
from loom.lint.structural import lint_structural as _lint_structural
from loom.models import (
    Candidate,
    Graph,
    Hit,
    LintReport,
    PageRef,
    ParsedDocument,
    PageSummary,
    Patch,
    ReviewItem,
    SourceRef,
    WikiPage,
    WriteResult,
    dumps_page,
    loads_page,
)
from loom.parsers import parse_file
from loom.review.queue import ReviewQueue
from loom.search.keyword import KeywordSearch
from loom.search.related import find_related as _find_related


def _read_or_notfound(path: Path) -> str:
    if not path.exists():
        raise NotFound(f"'{path.name}' not found; run 'loom init' first")
    return path.read_text(encoding="utf-8")


class Loom:
    """确定性原语门面（架构 §五）。推理留在宿主 agent；本类只做确定性的活。

    search 已实现（M2 keyword/BM25）；find_related / graph / lint_* 留待 M2/M4。
    """

    init_wiki = staticmethod(init_wiki)

    def __init__(self, root: Path | str):
        self.paths = LoomPaths(root=Path(root))
        self.store = WikiStore(self.paths)
        self._review = ReviewQueue(self.paths.loom_dir)
        self._search: KeywordSearch | None = None  # 惰性构建，写入后失效
        self._graph: GraphIndex | None = None

    def register_source(self, path: Path | str) -> SourceRef:
        return register_source(self.paths, Path(path))

    def parse(self, path: Path | str, wrap: bool = True) -> ParsedDocument:
        p = Path(path)
        if not p.is_absolute():
            p = self.paths.root / p  # 接受相对 wiki 根的路径（如 register 返回的 raw/sources/…）
        return parse_file(p, assets_dir=self.paths.raw_assets, wrap=wrap)

    def read_page(self, name: str) -> WikiPage:
        return self.store.read_page(name)

    def list_pages(self, type: str | None = None, tag: str | None = None) -> list[PageSummary]:
        return self.store.list_pages(type=type, tag=tag)

    def write_page(self, name: str, content: str, base_hash: str | None = None) -> WriteResult:
        res = self.store.write_page(name, content, base_hash=base_hash)
        self._search = self._graph = None  # 写入后检索/图谱索引失效，下次按需重建
        return res

    # ---- 审核队列（高风险改动可先 staged 成 diff 由人审）----

    def stage_review(self, name: str, content: str, base_hash: str | None = None) -> str:
        """把一次整页写入暂存为待审 diff，不落盘；返回 review id。"""
        existing = self.store._find_existing(name)
        old_text = existing.read_text(encoding="utf-8") if existing else ""
        try:
            new_text = dumps_page(loads_page(name, content))  # 规范化，diff 才干净
        except ValidationFailed:
            new_text = content  # 非法内容也允许 staged，apply 时再报
        return self._review.stage(
            name=name, content=content, base_hash=base_hash, old_text=old_text, new_text=new_text
        ).id

    def stage_update_review(self, name: str, patch: Patch, base_hash: str | None = None) -> str:
        """把一次段级更新的结果暂存为待审 diff。"""
        content, current_hash = self.store.preview_update(name, patch)
        existing = self.store._find_existing(name)
        old_text = existing.read_text(encoding="utf-8") if existing else ""
        return self._review.stage(
            name=name,
            content=content,
            base_hash=base_hash or current_hash,
            old_text=old_text,
            new_text=content,
        ).id

    def list_reviews(self) -> list[ReviewItem]:
        return self._review.list()

    def get_review(self, rid: str) -> ReviewItem:
        return self._review.get(rid)

    def apply_review(self, rid: str) -> WriteResult:
        """落盘 staged 改动：走正常 write_page（完整校验 + OCC），成功后记 REVIEW 日志并出队。"""
        item = self._review.get(rid)
        res = self.write_page(item.name, item.content, base_hash=item.base_hash)
        self.store.log.append("REVIEW", item.name, "applied")
        self._review.remove(rid)
        return res

    def reject_review(self, rid: str) -> None:
        self._review.remove(rid)

    def update_page(self, name: str, patch: Patch, base_hash: str | None = None) -> WriteResult:
        res = self.store.update_page(name, patch, base_hash=base_hash)
        self._search = self._graph = None  # 写入后失效
        return res

    def search(self, query: str, mode: str = "keyword", limit: int = 10) -> list[Hit]:
        if mode != "keyword":
            raise ValidationFailed(
                f"search mode '{mode}' not supported yet (only 'keyword'); vector/hybrid 留待 M6"
            )
        if self._search is None:
            self._search = KeywordSearch(self.store)
        return self._search.search(query, limit=limit)

    def graph(self, name: str | None = None, depth: int = 1) -> Graph:
        if self._graph is None:
            self._graph = GraphIndex.build(self.store)
        if name is None:
            return self._graph.full_graph()
        return self._graph.subgraph(name, depth)

    def find_related(self, text: str, limit: int = 10) -> list[PageRef]:
        if self._search is None:
            self._search = KeywordSearch(self.store)
        if self._graph is None:
            self._graph = GraphIndex.build(self.store)
        return _find_related(self._search, self._graph, text, limit=limit)

    def lint_structural(self) -> LintReport:
        return _lint_structural(self.store)

    def lint_candidates(self) -> list[Candidate]:
        return _lint_candidates(self.store)

    def get_index(self) -> str:
        return _read_or_notfound(self.paths.index_md)

    def get_schema(self) -> str:
        return _read_or_notfound(self.paths.schema_md)

    def get_purpose(self) -> str:
        return _read_or_notfound(self.paths.purpose_md)
