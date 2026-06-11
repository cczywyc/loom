from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock, Timeout

from loom.errors import LockTimeout


@contextmanager
def page_lock(loom_dir: Path, name: str, timeout: float = 10.0):
    """跨进程文件锁（按 name 一把）。每次新建 FileLock 且 thread_local=False，保证同进程内不可重入。

    陈旧锁：filelock 底层是 OS flock，锁随持有进程**死亡即被内核自动释放**——MCP 常驻进程
    被 kill -9 也不会留下死锁，后续进程立刻可获取。故**无需**任何手工陈旧锁清理/超时回收逻辑。
    （由 tests/core/test_concurrency.py::test_lock_auto_released_on_process_death 实证。）

    特殊锁名 `__index__` / `__log__`：保护共享的 index.md / log.md 读改写（见 IndexManager/LogWriter）。
    """
    lock_path = loom_dir / "locks" / f"{name}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(lock_path), timeout=timeout, thread_local=False)
    try:
        with lock:
            yield
    except Timeout as e:
        raise LockTimeout(f"page '{name}' is locked by another writer") from e
