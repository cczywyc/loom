from pathlib import Path

from loom.config import LoomPaths
from loom.core.hash import register_source
from loom.core.scaffold import init_wiki
from loom.core.store import WikiStore
from loom.errors import NotFound, ValidationFailed
from loom.models import Hit, ParsedDocument, PageSummary, Patch, SourceRef, WikiPage, WriteResult
from loom.parsers import parse_file
from loom.search.keyword import KeywordSearch


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
        self._search: KeywordSearch | None = None  # 惰性构建，写入后失效

    def register_source(self, path: Path | str) -> SourceRef:
        return register_source(self.paths, Path(path))

    def parse(self, path: Path | str) -> ParsedDocument:
        p = Path(path)
        if not p.is_absolute():
            p = self.paths.root / p  # 接受相对 wiki 根的路径（如 register 返回的 raw/sources/…）
        return parse_file(p, assets_dir=self.paths.raw_assets)

    def read_page(self, name: str) -> WikiPage:
        return self.store.read_page(name)

    def list_pages(self, type: str | None = None, tag: str | None = None) -> list[PageSummary]:
        return self.store.list_pages(type=type, tag=tag)

    def write_page(self, name: str, content: str, base_hash: str | None = None) -> WriteResult:
        res = self.store.write_page(name, content, base_hash=base_hash)
        self._search = None  # 写入后失效，下次 search 重建索引
        return res

    def update_page(self, name: str, patch: Patch, base_hash: str | None = None) -> WriteResult:
        res = self.store.update_page(name, patch, base_hash=base_hash)
        self._search = None  # 写入后失效
        return res

    def search(self, query: str, mode: str = "keyword", limit: int = 10) -> list[Hit]:
        if mode != "keyword":
            raise ValidationFailed(
                f"search mode '{mode}' not supported yet (only 'keyword'); vector/hybrid 留待 M6"
            )
        if self._search is None:
            self._search = KeywordSearch(self.store)
        return self._search.search(query, limit=limit)

    def get_index(self) -> str:
        return _read_or_notfound(self.paths.index_md)

    def get_schema(self) -> str:
        return _read_or_notfound(self.paths.schema_md)

    def get_purpose(self) -> str:
        return _read_or_notfound(self.paths.purpose_md)
