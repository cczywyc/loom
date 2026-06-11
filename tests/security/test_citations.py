from loom.security.citations import Citation, extract_citations
from tests.conftest import page_md


def test_extract_citations():
    body = "注意力即一切 ^[src:attention.pdf#p3]。另一论断 ^[src:blog.md]。"
    cites = extract_citations(body)
    assert cites == [
        Citation(source="attention.pdf", locator="p3", line=1),
        Citation(source="blog.md", locator=None, line=1),
    ]


def test_lint_reports_claim_level_staleness(loom, wiki_root, tmp_path):
    doc = tmp_path / "n.md"
    doc.write_text("v1")
    ref = loom.register_source(doc)
    fname = ref.path.split("/")[-1]
    loom.write_page(
        "p",
        page_md(
            type="concept",
            title="P",
            sources=[ref.path],
            source_hashes={ref.path: ref.sha256},
            body=f"论断甲 ^[src:{fname}]。\n\n无引用的论断乙。",
        ),
    )
    (wiki_root / ref.path).write_text("v2")
    stale = next(f for f in loom.lint_structural().findings if f.kind == "stale")
    assert "论断甲" in stale.message and "论断乙" not in stale.message  # 精确到论断


def test_lint_flags_citation_to_unlisted_source(loom):
    # ^[src:ghost.pdf] 引用了不在页面 sources 中的来源 → broken-link（注明是 citation）
    loom.write_page("p", page_md(type="concept", title="P", body="论断 ^[src:ghost.pdf]。"))
    findings = loom.lint_structural().findings
    assert any(f.kind == "broken-link" and "ghost.pdf" in f.message for f in findings)
