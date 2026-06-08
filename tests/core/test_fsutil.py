import pytest

from loom.core.fsutil import atomic_write_text, sha256_file, sha256_text
from loom.core.lock import page_lock
from loom.errors import LockTimeout


def test_atomic_write_and_hash(tmp_path):
    p = tmp_path / "a.md"
    atomic_write_text(p, "hello 中文")
    assert p.read_text(encoding="utf-8") == "hello 中文"
    assert sha256_file(p) == sha256_text("hello 中文")


def test_atomic_write_no_tmp_residue_on_failure(tmp_path, monkeypatch):
    import os

    p = tmp_path / "a.md"
    monkeypatch.setattr(os, "replace", lambda *a: (_ for _ in ()).throw(OSError("boom")))
    with pytest.raises(OSError):
        atomic_write_text(p, "data")
    assert not p.exists()
    assert list(tmp_path.iterdir()) == []  # 无 .tmp 残留


def test_page_lock_times_out_when_held(tmp_path):
    with page_lock(tmp_path, "some-page", timeout=0.1):
        with pytest.raises(LockTimeout):
            with page_lock(tmp_path, "some-page", timeout=0.1):
                pass
