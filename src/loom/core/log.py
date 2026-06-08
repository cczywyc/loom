from pathlib import Path

from loom import clock

# op 取值约定：INIT / REGISTER / WRITE / UPDATE / FIX / REVIEW


class LogWriter:
    """log.md：append-only 操作历史，统一前缀便于 grep。"""

    def __init__(self, path: Path):
        self.path = path

    def append(self, op: str, name: str, detail: str = "") -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("# Log\n\n", encoding="utf-8")
        line = f"- {clock.now_iso()} | {op} | {name} | {detail}\n"
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line)
