from collections.abc import Iterator
from pathlib import Path

import yaml

from loom import clock
from loom.config import LoomPaths
from loom.core.fsutil import atomic_write_text, sha256_file, sha256_text
from loom.core.index import IndexManager
from loom.core.lock import page_lock
from loom.core.log import LogWriter
from loom.core.sections import apply_patch
from loom.errors import Conflict, NotFound, ValidationFailed
from loom.models import TYPE_DIRS, Patch, PageSummary, WikiPage, WriteResult, dumps_page, loads_page
from loom.validate import validate_page


class WikiStore:
    """wiki 目录读写抽象：read/list（0.9）+ write_page（0.10：校验+锁+OCC+原子写+自动记账）。"""

    def __init__(self, paths: LoomPaths):
        self.paths = paths
        self.index = IndexManager(paths.index_md)
        self.log = LogWriter(paths.log_md)

    # ---- 读取面 ----

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

    def _path_for(self, page: WikiPage) -> Path:
        return self.paths.wiki_dir / TYPE_DIRS[page.meta.type] / f"{page.name}.md"

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

    # ---- 写入面 ----

    def write_page(self, name: str, content: str, base_hash: str | None = None) -> WriteResult:
        """校验结构 → 加锁 → OCC 比对 → 原子落盘 → 副作用同步 index/log。不合规则拒绝。

        OCC：新建无需 base_hash；覆写已存在页必须带读取时的 base_hash 且与磁盘一致，否则 Conflict。
        """
        page = loads_page(name, content)
        problems, warnings = validate_page(page, self.known_names() | {name})
        if problems:
            raise ValidationFailed("; ".join(problems))
        path = self._path_for(page)
        existing = self._find_existing(name)
        with page_lock(self.paths.loom_dir, name):
            if existing and existing != path:
                raise Conflict(f"name '{name}' already used at {existing}")
            if path.exists():
                disk = sha256_file(path)
                if base_hash is None:
                    raise Conflict(
                        f"page '{name}' exists; read it first and pass base_hash, or use update_page"
                    )
                if disk != base_hash:
                    raise Conflict(
                        f"page '{name}' changed on disk since you read it; re-read and retry"
                    )
            created = not path.exists()
            text = dumps_page(page)
            atomic_write_text(path, text)
            self.index.upsert(page)
            self.log.append("WRITE", name, "created" if created else "updated")
        return WriteResult(
            ok=True,
            name=name,
            path=str(path),
            created=created,
            content_hash=sha256_text(text),
            warnings=warnings,
        )

    def update_page(self, name: str, patch: Patch, base_hash: str | None = None) -> WriteResult:
        """非破坏性段级更新：锁内 read→改→写，天然无丢失更新；可选 base_hash 走 OCC。"""
        with page_lock(self.paths.loom_dir, name):
            page = self.read_page(name)  # 缺页抛 NotFound
            if base_hash is not None and page.content_hash != base_hash:
                raise Conflict(
                    f"page '{name}' changed on disk since you read it; re-read and retry"
                )
            if patch.op == "set_frontmatter":
                updates = yaml.safe_load(patch.content) or {}
                page.meta = page.meta.model_copy(update=updates)
                detail = "set_frontmatter"
            else:
                page.body = apply_patch(page.body, patch)
                detail = f"{patch.op} section={patch.section}"
            page.meta.updated = clock.today()  # 工具自动碰 updated
            problems, warnings = validate_page(page, self.known_names() | {name})
            if problems:
                raise ValidationFailed("; ".join(problems))
            path = self._path_for(page)
            text = dumps_page(page)
            atomic_write_text(path, text)
            self.index.upsert(page)
            self.log.append("UPDATE", name, detail)
        return WriteResult(
            ok=True,
            name=name,
            path=str(path),
            created=False,
            content_hash=sha256_text(text),
            warnings=warnings,
        )
