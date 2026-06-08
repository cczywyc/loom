from pathlib import Path

from loom.config import LoomPaths
from loom.core.hash import register_source
from loom.core.scaffold import init_wiki
from loom.core.store import WikiStore
from loom.errors import NotFound
from loom.models import ParsedDocument, PageSummary, Patch, SourceRef, WikiPage, WriteResult
from loom.parsers import parse_file


def _read_or_notfound(path: Path) -> str:
    if not path.exists():
        raise NotFound(f"'{path.name}' not found; run 'loom init' first")
    return path.read_text(encoding="utf-8")


class Loom:
    """确定性原语门面（架构 §五）。推理留在宿主 agent；本类只做确定性的活。

    M0 暴露已实现的原语；search / find_related / graph / lint_* 留待 M2/M4。
    """

    init_wiki = staticmethod(init_wiki)

    def __init__(self, root: Path | str):
        self.paths = LoomPaths(root=Path(root))
        self.store = WikiStore(self.paths)

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
        return self.store.write_page(name, content, base_hash=base_hash)

    def update_page(self, name: str, patch: Patch, base_hash: str | None = None) -> WriteResult:
        return self.store.update_page(name, patch, base_hash=base_hash)

    def get_index(self) -> str:
        return _read_or_notfound(self.paths.index_md)

    def get_schema(self) -> str:
        return _read_or_notfound(self.paths.schema_md)

    def get_purpose(self) -> str:
        return _read_or_notfound(self.paths.purpose_md)
