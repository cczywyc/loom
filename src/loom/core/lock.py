from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock, Timeout

from loom.errors import LockTimeout


@contextmanager
def page_lock(loom_dir: Path, name: str, timeout: float = 10.0):
    """per-page 文件锁。每次新建 FileLock 且 thread_local=False，保证同进程内不可重入。"""
    lock_path = loom_dir / "locks" / f"{name}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(lock_path), timeout=timeout, thread_local=False)
    try:
        with lock:
            yield
    except Timeout as e:
        raise LockTimeout(f"page '{name}' is locked by another writer") from e
