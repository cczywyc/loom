from contextlib import nullcontext
from pathlib import Path

from loom import clock
from loom.core.lock import page_lock

# op 取值约定：INIT / REGISTER / WRITE / UPDATE / FIX / REVIEW


class LogWriter:
    """log.md：append-only 操作历史，统一前缀便于 grep。

    与 index 同理：log.md 是共享单文件，多进程并发追加需串行化（含首次建头的 TOCTOU），
    故用全局 `__log__` 锁。传入 loom_dir 才启用（None 仅供纯单测）。
    """

    def __init__(self, path: Path, loom_dir: Path | None = None):
        self.path = path
        self._loom_dir = loom_dir

    def append(self, op: str, name: str, detail: str = "") -> None:
        lock = page_lock(self._loom_dir, "__log__") if self._loom_dir else nullcontext()
        with lock:
            if not self.path.exists():
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_text("# Log\n\n", encoding="utf-8")
            line = f"- {clock.now_iso()} | {op} | {name} | {detail}\n"
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line)
