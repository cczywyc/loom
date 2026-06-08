from loom.config import LoomPaths
from loom.core.hash import ContentHash, register_source


def test_register_copies_and_dedupes(wiki_root, tmp_path):
    paths = LoomPaths(root=wiki_root)
    doc = tmp_path / "paper.pdf"
    doc.write_bytes(b"%PDF fake")
    r1 = register_source(paths, doc)
    assert r1.is_new and (wiki_root / r1.path).exists()
    assert r1.path.startswith("raw/sources/")
    r2 = register_source(paths, doc)  # 同内容再注册
    assert not r2.is_new and r2.path == r1.path and r2.sha256 == r1.sha256


def test_register_same_name_different_content_gets_suffix(wiki_root, tmp_path):
    paths = LoomPaths(root=wiki_root)
    a = tmp_path / "note.md"
    a.write_text("v1")
    b_dir = tmp_path / "sub"
    b_dir.mkdir()
    b = b_dir / "note.md"
    b.write_text("v2 完全不同")
    r1, r2 = register_source(paths, a), register_source(paths, b)
    assert r1.path != r2.path and r2.is_new  # note.md / note-1.md


def test_changed_sources_detected(wiki_root, tmp_path):
    paths = LoomPaths(root=wiki_root)
    doc = tmp_path / "note.md"
    doc.write_text("v1")
    ref = register_source(paths, doc)
    (wiki_root / ref.path).write_text("被人直接改了")  # 模拟 raw 被外部修改
    ch = ContentHash(paths)
    assert ch.changed_sources() == [ref.path]
