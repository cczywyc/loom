import pytest

from loom.errors import Conflict, ValidationFailed
from tests.conftest import page_md


def test_write_creates_file_index_log(store, wiki_root):
    res = store.write_page(
        "llm-wiki", page_md(type="concept", title="LLM Wiki", summary="持久 wiki")
    )
    assert res.ok and res.created
    assert (wiki_root / "wiki/concepts/llm-wiki.md").exists()
    assert "[[llm-wiki|LLM Wiki]] — 持久 wiki" in (wiki_root / "wiki/index.md").read_text()
    assert "| WRITE | llm-wiki | created" in (wiki_root / "wiki/log.md").read_text()


def test_write_rejects_bad_name(store):
    with pytest.raises(ValidationFailed):
        store.write_page("Bad_Name", page_md(type="concept", title="X"))


def test_write_existing_without_base_hash_conflicts(store):
    store.write_page("react", page_md(type="concept", title="ReAct"))
    with pytest.raises(Conflict):
        store.write_page("react", page_md(type="concept", title="ReAct v2"))


def test_write_existing_with_stale_hash_conflicts(store):
    r1 = store.write_page("react", page_md(type="concept", title="ReAct"))
    store.write_page("react", page_md(type="concept", title="ReAct v2"), base_hash=r1.content_hash)
    with pytest.raises(Conflict):  # r1.content_hash 已过期
        store.write_page(
            "react", page_md(type="concept", title="ReAct v3"), base_hash=r1.content_hash
        )


def test_write_dangling_link_warns_but_succeeds(store):
    res = store.write_page("a", page_md(type="concept", title="A", body="见 [[future-page]]"))
    assert res.ok and any("future-page" in w for w in res.warnings)


def test_write_duplicate_name_across_types_rejected(store):
    store.write_page("react", page_md(type="concept", title="ReAct"))
    with pytest.raises(Conflict):  # 同名不同 type 目录也不行：name 全库唯一
        store.write_page("react", page_md(type="entity", title="React 框架"))
