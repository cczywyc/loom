from collections.abc import Iterator
from datetime import date
from pathlib import Path

import yaml

from loom.core.fsutil import atomic_write_text, sha256_file
from loom.core.store import WikiStore
from loom.errors import ValidationFailed
from loom.models import TYPE_DIRS, PageMeta, Patch, WikiPage, loads_page


def apply_fixes(loom) -> list[str]:
    """只修**绝对安全**的三类机械问题，每笔记 FIX 日志；返回修复描述列表。

    安全集：① 缺失日期从 mtime 回填 ② source_hashes 从当前 raw 回填 ③ index.md 与实际页面失同步。
    其余问题（缺 title、坏名、坏链…）只报告、绝不自动改——那需要 agent 判断。
    """
    store: WikiStore = loom.store
    fixes: list[str] = []
    fixes += _backfill_dates(store)  # 先把缺日期的坏页修成合法（之后才会进 index）
    fixes += _backfill_source_hashes(store)
    fixes += _resync_index(store)
    for desc in fixes:
        store.log.append("FIX", "-", desc)
    return fixes


def _iter_valid(store: WikiStore) -> Iterator[tuple[Path, WikiPage]]:
    for path in store._iter_page_paths():
        try:
            yield path, loads_page(path.stem, path.read_text(encoding="utf-8"))
        except ValidationFailed:
            continue


def _backfill_dates(store: WikiStore) -> list[str]:
    fixed: list[str] = []
    for path in store._iter_page_paths():
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        try:
            meta = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(meta, dict):
            continue
        missing = [k for k in ("created", "updated") if not meta.get(k)]
        if not missing:
            continue
        mtime = date.fromtimestamp(path.stat().st_mtime).isoformat()
        candidate = {**meta, **dict.fromkeys(missing, mtime)}
        try:
            PageMeta(**candidate)  # 仅当补完日期后页面即合法才修；缺别的字段则不碰
        except Exception:
            continue
        fm = yaml.safe_dump(candidate, allow_unicode=True, sort_keys=False)
        atomic_write_text(path, f"---\n{fm}---\n\n{parts[2].lstrip(chr(10)).rstrip()}\n")
        fixed.append(f"backfilled created/updated from mtime on '{path.stem}'")
    return fixed


def _backfill_source_hashes(store: WikiStore) -> list[str]:
    fixed: list[str] = []
    for _, page in _iter_valid(store):
        new = dict(page.meta.source_hashes)
        changed = False
        for src in page.meta.sources:
            f = store.paths.root / src
            if src not in new and f.exists():
                new[src] = sha256_file(f)
                changed = True
        if changed:
            content = yaml.safe_dump({"source_hashes": new}, allow_unicode=True, sort_keys=False)
            store.update_page(page.name, Patch(op="set_frontmatter", content=content))
            fixed.append(f"backfilled source_hashes on '{page.name}'")
    return fixed


def _resync_index(store: WikiStore) -> list[str]:
    expected: dict[str, dict[str, str]] = {sec: {} for sec in TYPE_DIRS.values()}
    for _, page in _iter_valid(store):
        expected[TYPE_DIRS[page.meta.type]][page.name] = store.index._format_line(page)
    if store.index._parse() != expected:
        store.index._write(expected)
        return ["index.md re-synced with actual pages"]
    return []
