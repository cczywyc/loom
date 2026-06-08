import hashlib
import json
from pathlib import Path

from loom.config import LoomPaths
from loom.core.fsutil import atomic_write_text, sha256_file
from loom.core.log import LogWriter
from loom.models import SourceRef

_ARCHIVE_NAME = "hashes.json"


def _archive_path(paths: LoomPaths) -> Path:
    return paths.loom_dir / _ARCHIVE_NAME


def _load_archive(paths: LoomPaths) -> dict[str, str]:
    p = _archive_path(paths)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _save_archive(paths: LoomPaths, archive: dict[str, str]) -> None:
    text = json.dumps(archive, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    atomic_write_text(_archive_path(paths), text)


def _unique_dest(paths: LoomPaths, filename: str, archive: dict[str, str]) -> str:
    """同名异内容时退避到 name-1 / name-2 …，避免互相覆盖。"""
    stem, suffix = Path(filename).stem, Path(filename).suffix
    candidate = f"raw/sources/{filename}"
    i = 0
    while candidate in archive or (paths.root / candidate).exists():
        i += 1
        candidate = f"raw/sources/{stem}-{i}{suffix}"
    return candidate


def register_source(paths: LoomPaths, src: Path) -> SourceRef:
    """拷入 raw/sources、算 SHA256、按内容去重；返回 SourceRef(相对路径, sha256, is_new)。"""
    src = Path(src)
    data = src.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    archive = _load_archive(paths)
    for rel, existing in archive.items():
        if existing == sha:  # 同内容已注册 → 复用，不再拷贝
            return SourceRef(path=rel, sha256=sha, is_new=False)
    dest_rel = _unique_dest(paths, src.name, archive)
    dest = paths.root / dest_rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    archive[dest_rel] = sha
    _save_archive(paths, archive)
    LogWriter(paths.log_md).append("REGISTER", src.name, sha)
    return SourceRef(path=dest_rel, sha256=sha, is_new=True)


class ContentHash:
    """基于 .loom/hashes.json 档案的来源过期检测。"""

    def __init__(self, paths: LoomPaths):
        self.paths = paths

    def changed_sources(self) -> list[str]:
        """重算每个已注册来源的当前 hash 与档案比对，返回内容已变的相对路径。"""
        archive = _load_archive(self.paths)
        changed: list[str] = []
        for rel, old in archive.items():
            f = self.paths.root / rel
            if f.exists() and sha256_file(f) != old:
                changed.append(rel)
        return changed
