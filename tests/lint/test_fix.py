from loom.lint.fix import apply_fixes
from tests.conftest import page_md


def test_fix_resyncs_index(loom, wiki_root):
    loom.write_page("a", page_md(type="concept", title="A"))
    idx = wiki_root / "wiki/index.md"
    idx.write_text(idx.read_text().replace("- [[a|A]]", ""))  # 人为弄丢 index 条目
    fixed = apply_fixes(loom)
    assert any("index" in f for f in fixed)
    assert "[[a|A]]" in idx.read_text()


def test_fix_logs_every_change(loom, wiki_root):
    loom.write_page("a", page_md(type="concept", title="A"))
    (wiki_root / "wiki/index.md").write_text("# Index\n\n## concepts\n")
    apply_fixes(loom)
    assert "| FIX |" in (wiki_root / "wiki/log.md").read_text()


def test_fix_never_touches_page_bodies(loom, wiki_root):
    loom.write_page("a", page_md(type="concept", title="A", body="正文不可动"))
    before = (wiki_root / "wiki/concepts/a.md").read_text()
    apply_fixes(loom)
    assert (wiki_root / "wiki/concepts/a.md").read_text() == before


def test_fix_backfills_source_hashes(loom, tmp_path):
    doc = tmp_path / "n.md"
    doc.write_text("v1")
    ref = loom.register_source(doc)
    loom.write_page("p", page_md(type="concept", title="P", sources=[ref.path]))  # 无 source_hashes
    apply_fixes(loom)
    assert loom.read_page("p").meta.source_hashes.get(ref.path) == ref.sha256


def test_fix_backfills_missing_dates_makes_page_valid(loom, wiki_root):
    # 手工写一个只缺 created/updated 的页（其余合法）→ 回填 mtime 后应能正常读出
    (wiki_root / "wiki/concepts/nodate.md").write_text(
        "---\ntype: concept\ntitle: 无日期\n---\n\n正文"
    )
    apply_fixes(loom)
    page = loom.read_page("nodate")
    assert page.meta.created and page.meta.updated
