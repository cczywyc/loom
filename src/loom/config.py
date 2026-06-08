from dataclasses import dataclass
from pathlib import Path

from loom.errors import NotFound


@dataclass(frozen=True)
class LoomPaths:
    """所有 wiki 内路径的单一真源：给定根目录，派生出各文件/子目录位置。"""

    root: Path

    @property
    def wiki_dir(self) -> Path:
        return self.root / "wiki"

    @property
    def raw_sources(self) -> Path:
        return self.root / "raw" / "sources"

    @property
    def raw_assets(self) -> Path:
        return self.root / "raw" / "assets"

    @property
    def loom_dir(self) -> Path:
        return self.root / ".loom"

    @property
    def index_md(self) -> Path:
        return self.wiki_dir / "index.md"

    @property
    def log_md(self) -> Path:
        return self.wiki_dir / "log.md"

    @property
    def schema_md(self) -> Path:
        return self.root / "schema.md"

    @property
    def purpose_md(self) -> Path:
        return self.root / "purpose.md"


def find_wiki_root(start: Path) -> Path:
    """像 git 一样从 start 向上找第一个含 .loom/ 的目录；找不到抛 NotFound。"""
    start = Path(start).resolve()
    for candidate in (start, *start.parents):
        if (candidate / ".loom").is_dir():
            return candidate
    raise NotFound("not inside a loom wiki; run 'loom init' first")
