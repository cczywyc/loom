from tests.conftest import page_md


def test_contradiction_candidate_pair(loom):
    loom.write_page("x", page_md(type="concept", title="X"))
    loom.write_page("y", page_md(type="concept", title="Y"))
    loom.write_page("a", page_md(type="synthesis", title="观点A", body="[[x]] [[y]]"))
    loom.write_page("b", page_md(type="synthesis", title="观点B", body="[[x]] [[y]]"))
    cands = loom.lint_candidates()
    pair = next(c for c in cands if c.kind == "possible-contradiction")
    assert set(pair.pages) == {"a", "b"} and "share" in pair.reason or "共享" in pair.reason


def test_no_candidates_on_well_linked_wiki(loom):
    loom.write_page("a", page_md(type="concept", title="A", body="[[b|B]]"))
    loom.write_page("b", page_md(type="concept", title="B", body="[[a|A]]"))
    assert loom.lint_candidates() == []


def test_deterministic_ordering(loom):
    loom.write_page("x", page_md(type="concept", title="X"))
    loom.write_page("y", page_md(type="concept", title="Y"))
    loom.write_page("a", page_md(type="synthesis", title="A", body="[[x]] [[y]]"))
    loom.write_page("b", page_md(type="synthesis", title="B", body="[[x]] [[y]]"))
    r1 = [(c.kind, c.pages) for c in loom.lint_candidates()]
    r2 = [(c.kind, c.pages) for c in loom.lint_candidates()]
    assert r1 == r2


def test_sparse_area_candidate(loom):
    # 三个互不相连的孤立 entity（度=0）→ 该类型 >50% 稀疏
    for n in ("e1", "e2", "e3"):
        loom.write_page(n, page_md(type="entity", title=n.upper()))
    cands = loom.lint_candidates()
    assert any(c.kind == "sparse-area" and {"e1", "e2", "e3"} <= set(c.pages) for c in cands)


def test_stale_cluster_candidate(loom, wiki_root, tmp_path):
    doc = tmp_path / "s.md"
    doc.write_text("v1")
    ref = loom.register_source(doc)
    loom.write_page(
        "p",
        page_md(
            type="concept",
            title="P",
            sources=[ref.path],
            source_hashes={ref.path: ref.sha256},
            body="[[q]]",
        ),
    )
    loom.write_page("q", page_md(type="concept", title="Q", body="[[p]]"))
    (wiki_root / ref.path).write_text("v2 改了")
    sc = next(c for c in loom.lint_candidates() if c.kind == "stale-cluster")
    assert "p" in sc.pages and "q" in sc.pages
