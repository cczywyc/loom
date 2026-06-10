from tests.conftest import page_md


def test_orphan_detected(loom):
    loom.write_page("lonely", page_md(type="concept", title="孤独页"))
    kinds = {(f.kind, f.page) for f in loom.lint_structural().findings}
    assert ("orphan", "lonely") in kinds


def test_broken_link_detected(loom):
    loom.write_page("a", page_md(type="concept", title="A", body="[[ghost]]"))
    assert any(
        f.kind == "broken-link" and "ghost" in f.message for f in loom.lint_structural().findings
    )


def test_bad_frontmatter_detected_on_handedited_file(loom, wiki_root):
    (wiki_root / "wiki/concepts/broken.md").write_text(
        "---\ntype: concept\n---\n裸文本"
    )  # 缺 title 等
    assert any(
        f.kind == "bad-frontmatter" and f.page == "broken" for f in loom.lint_structural().findings
    )


def test_bad_name_detected(loom, wiki_root):
    (wiki_root / "wiki/concepts/Bad_Name.md").write_text(page_md(type="concept", title="X"))
    assert any(f.kind == "bad-name" for f in loom.lint_structural().findings)


def test_stale_page_detected_when_source_changed(loom, wiki_root, tmp_path):
    doc = tmp_path / "n.md"
    doc.write_text("v1")
    ref = loom.register_source(doc)
    loom.write_page(
        "p",
        page_md(
            type="concept",
            title="P",
            sources=[ref.path],
            source_hashes={ref.path: ref.sha256},
            body="基于 v1",
        ),
    )
    (wiki_root / ref.path).write_text("v2 改了")
    assert any(f.kind == "stale" and f.page == "p" for f in loom.lint_structural().findings)


def test_duplicate_title_detected(loom):
    loom.write_page("a1", page_md(type="concept", title="同名", body="[[a2]]"))
    loom.write_page("a2", page_md(type="concept", title="同名", body="[[a1]]"))
    assert any(f.kind == "duplicate-title" for f in loom.lint_structural().findings)


def test_clean_wiki_reports_ok(loom):
    loom.write_page("a", page_md(type="concept", title="A", body="[[b|乙]]"))
    loom.write_page("b", page_md(type="concept", title="B", body="[[a|甲]]"))
    assert loom.lint_structural().ok
