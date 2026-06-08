from collections.abc import Iterator
from pathlib import Path

from loom.config import LoomPaths
from loom.core.fsutil import sha256_file
from loom.errors import NotFound
from loom.models import TYPE_DIRS, PageSummary, WikiPage, loads_page


class WikiStore:
    """wiki 目录读写抽象。本任务（0.9）只实现读取面；写入面在 0.10/0.11 补。"""

    def __init__(self, paths: LoomPaths):
        self.paths = paths

    def _iter_page_paths(self) -> Iterator[Path]:
        """遍历六个类型目录下的所有 .md 页面（index.md/log.md 不在其中，天然排除）。"""
        for dir_name in TYPE_DIRS.values():
            d = self.paths.wiki_dir / dir_name
            if d.is_dir():
                yield from sorted(d.glob("*.md"))

    def _find_existing(self, name: str) -> Path | None:
        for p in self._iter_page_paths():
            if p.stem == name:
                return p
        return None

    def known_names(self) -> set[str]:
        return {p.stem for p in self._iter_page_paths()}

    def read_page(self, name: str) -> WikiPage:
        path = self._find_existing(name)
        if path is None:
            raise NotFound(f"page '{name}' not found")
        page = loads_page(name, path.read_text(encoding="utf-8"))
        page.content_hash = sha256_file(path)  # OCC 协议起点：读到的磁盘 hash
        return page

    def list_pages(self, type: str | None = None, tag: str | None = None) -> list[PageSummary]:
        result: list[PageSummary] = []
        for p in self._iter_page_paths():
            page = loads_page(p.stem, p.read_text(encoding="utf-8"))
            if type is not None and page.meta.type != type:
                continue
            if tag is not None and tag not in page.meta.tags:
                continue
            result.append(
                PageSummary(
                    name=p.stem,
                    type=page.meta.type,
                    title=page.meta.title,
                    summary=page.meta.summary,
                    tags=page.meta.tags,
                    updated=page.meta.updated,
                )
            )
        return result
