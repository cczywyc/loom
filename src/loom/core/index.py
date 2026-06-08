import re
from pathlib import Path

from loom.core.fsutil import atomic_write_text
from loom.models import TYPE_DIRS, WikiPage

SECTION_ORDER = list(TYPE_DIRS.values())
_ENTRY_RE = re.compile(r"^- \[\[([^\]\|#]+)")


class IndexManager:
    """index.md 的增量维护：按类型分节、按 name 字典序；未触及的节逐字节不动。"""

    def __init__(self, path: Path):
        self.path = path

    def upsert(self, page: WikiPage) -> None:
        sections = self._parse()
        sections[TYPE_DIRS[page.meta.type]][page.name] = self._format_line(page)
        self._write(sections)

    def remove(self, name: str) -> None:
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
