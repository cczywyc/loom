import re
from contextlib import nullcontext
from pathlib import Path

from loom.core.fsutil import atomic_write_text
from loom.core.lock import page_lock
from loom.models import TYPE_DIRS, WikiPage

SECTION_ORDER = list(TYPE_DIRS.values())
_ENTRY_RE = re.compile(r"^- \[\[([^\]\|#]+)")


class IndexManager:
    """index.md 的增量维护：按类型分节、按 name 字典序；未触及的节逐字节不动。

    index.md 是所有页面共享的单文件——并发写页面时各自只持自己的 page lock，
    若不另加保护，多进程的读-改-写会互相覆盖（丢失更新）。故 upsert/remove 各用一把
    全局 `__index__` 锁串行化整段读改写。传入 loom_dir 才启用（None 仅供纯单测）。
    """

    def __init__(self, path: Path, loom_dir: Path | None = None):
        self.path = path
        self._loom_dir = loom_dir

    def _lock(self):
        return page_lock(self._loom_dir, "__index__") if self._loom_dir else nullcontext()

    def upsert(self, page: WikiPage) -> None:
        with self._lock():
            sections = self._parse()
            sections[TYPE_DIRS[page.meta.type]][page.name] = self._format_line(page)
            self._write(sections)

    def remove(self, name: str) -> None:
        with self._lock():
            sections = self._parse()
            for entries in sections.values():
                entries.pop(name, None)
            self._write(sections)

    def _format_line(self, page: WikiPage) -> str:
        line = f"- [[{page.name}|{page.meta.title}]]"
        if page.meta.summary:
            line += f" — {page.meta.summary}"
        return line

    def _parse(self) -> dict[str, dict[str, str]]:
        sections: dict[str, dict[str, str]] = {sec: {} for sec in SECTION_ORDER}
        text = self.path.read_text(encoding="utf-8") if self.path.exists() else ""
        current: str | None = None
        for line in text.splitlines():
            if line.startswith("## "):
                sec = line[3:].strip()
                current = sec if sec in sections else None
            elif current is not None:
                m = _ENTRY_RE.match(line)
                if m:
                    sections[current][m.group(1).strip()] = line
        return sections

    def _write(self, sections: dict[str, dict[str, str]]) -> None:
        parts = ["# Index", ""]
        for sec in SECTION_ORDER:
            parts.append(f"## {sec}")
            for name in sorted(sections[sec]):
                parts.append(sections[sec][name])
            parts.append("")
        atomic_write_text(self.path, "\n".join(parts))
