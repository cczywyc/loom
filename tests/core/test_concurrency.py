import multiprocessing as mp
import time

from loom.api import Loom
from loom.errors import Conflict, LockTimeout
from tests.conftest import page_md


def _writer(root, name, i, results):
    try:
        page_name = f"{name}-{i}" if name == "distinct" else name
        Loom(root).write_page(page_name, page_md(type="concept", title=f"T{i}"))
        results.put(("ok", i))
    except (Conflict, LockTimeout):
        results.put(("conflict", i))


def test_two_processes_same_new_page_exactly_one_wins(wiki_root):
    q = mp.Queue()
    ps = [mp.Process(target=_writer, args=(wiki_root, "same-page", i, q)) for i in range(2)]
    for p in ps:
        p.start()
    for p in ps:
        p.join(timeout=30)
    outcomes = sorted(q.get()[0] for _ in range(2))
    assert outcomes == ["conflict", "ok"]  # 恰好一个成功（第二个撞 OCC：页已存在）


def test_ten_processes_distinct_pages_all_succeed_index_consistent(wiki_root):
    q = mp.Queue()
    ps = [mp.Process(target=_writer, args=(wiki_root, "distinct", i, q)) for i in range(10)]
    for p in ps:
        p.start()
    for p in ps:
        p.join(timeout=60)
    assert all(q.get()[0] == "ok" for _ in range(10))
    index = Loom(wiki_root).get_index()
    assert all(f"[[distinct-{i}|" in index for i in range(10))  # index 无丢失更新


def _hold_lock(loom_dir, name, acquired):
    from loom.core.lock import page_lock

    with page_lock(loom_dir, name):
        acquired.set()  # 通知父进程：锁已持有
        time.sleep(30)  # 一直持有，直到被 kill


def test_lock_auto_released_on_process_death(wiki_root):
    # filelock 基于 flock：进程死亡，内核自动释放锁，无需手工清理陈旧锁。
    from loom.core.lock import page_lock

    loom_dir = Loom(wiki_root).paths.loom_dir
    acquired = mp.Event()
    child = mp.Process(target=_hold_lock, args=(loom_dir, "victim", acquired))
    child.start()
    assert acquired.wait(timeout=5)  # 子进程已持锁
    child.kill()  # SIGKILL
    child.join(timeout=5)
    t0 = time.monotonic()
    with page_lock(loom_dir, "victim", timeout=2.0):  # 父进程应几乎立刻拿到
        pass
    assert time.monotonic() - t0 < 1.0
