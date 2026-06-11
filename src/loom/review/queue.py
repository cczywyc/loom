import difflib
import json
from pathlib import Path

from loom import clock
from loom.core.fsutil import atomic_write_text
from loom.errors import NotFound
from loom.models import ReviewItem


class ReviewQueue:
    """`.loom/review/<seq>-<name>.json` 的暂存队列：staged → 人审 → apply/reject。"""

    def __init__(self, loom_dir: Path):
        self._dir = loom_dir / "review"

    def stage(
        self, name: str, content: str, base_hash: str | None, old_text: str, new_text: str
    ) -> ReviewItem:
        self._dir.mkdir(parents=True, exist_ok=True)
        rid = f"{self._next_seq()}-{name}"
        diff = "\n".join(
            difflib.unified_diff(
                old_text.splitlines(),
                new_text.splitlines(),
                fromfile=f"{name} (current)",
                tofile=f"{name} (staged)",
                lineterm="",
            )
        )
        item = ReviewItem(
            id=rid,
            name=name,
            content=content,
            base_hash=base_hash,
            diff=diff,
            staged_at=clock.now_iso(),
        )
        atomic_write_text(
            self._dir / f"{rid}.json", json.dumps(item.model_dump(), ensure_ascii=False, indent=2)
        )
        return item

    def list(self) -> list[ReviewItem]:
        if not self._dir.is_dir():
            return []
        items = [
            ReviewItem(**json.loads(p.read_text(encoding="utf-8")))
            for p in self._dir.glob("*.json")
        ]
        return sorted(items, key=lambda it: int(it.id.split("-")[0]))

    def get(self, rid: str) -> ReviewItem:
        p = self._dir / f"{rid}.json"
        if not p.exists():
            raise NotFound(f"review item '{rid}' not found")
        return ReviewItem(**json.loads(p.read_text(encoding="utf-8")))

    def remove(self, rid: str) -> None:
        (self._dir / f"{rid}.json").unlink(missing_ok=True)

    def _next_seq(self) -> int:
        seqs = [
            int(p.stem.split("-")[0])
            for p in self._dir.glob("*.json")
            if p.stem.split("-")[0].isdigit()
        ]
        return max(seqs, default=0) + 1
