from loom.models import Patch
from tests.conftest import page_md


def test_update_page_patches_section_bumps_updated_logs(store, wiki_root, monkeypatch):
    monkeypatch.setattr("loom.clock.today", lambda: "2026-06-07")
    store.write_page("react", page_md(type="concept", title="ReAct", body="## 要点\n\n旧。"))
    store.update_page("react", Patch(op="replace", section="要点", content="新。"))
    page = store.read_page("react")
    assert "新。" in page.body and "旧。" not in page.body
    assert page.meta.updated == "2026-06-07"  # 工具自动碰 updated，agent 不必记得
    assert "| UPDATE | react | replace section=要点" in (wiki_root / "wiki/log.md").read_text()


def test_update_set_frontmatter_merges_only_given_keys(store):
    store.write_page("react", page_md(type="concept", title="ReAct", tags=["agent"]))
    store.update_page("react", Patch(op="set_frontmatter", content='summary: "推理+行动"'))
    page = store.read_page("react")
    assert page.meta.summary == "推理+行动"
    assert page.meta.tags == ["agent"]  # 未提及字段不动
