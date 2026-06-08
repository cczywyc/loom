from loom.core.index import IndexManager
from loom.models import loads_page
from tests.conftest import page_md


def make_index(tmp_path):
    p = tmp_path / "index.md"
    p.write_text(
        "# Index\n\n## entities\n\n## concepts\n\n## sources\n\n## queries\n\n## synthesis\n\n## comparisons\n"
    )
    return IndexManager(p)


def test_upsert_inserts_sorted_line(tmp_path):
    idx = make_index(tmp_path)
    idx.upsert(loads_page("react", page_md(type="concept", title="ReAct", summary="推理+行动范式")))
    idx.upsert(
        loads_page("llm-wiki", page_md(type="concept", title="LLM Wiki", summary="持久 wiki 模式"))
    )
    text = (tmp_path / "index.md").read_text()
    sec = text.split("## concepts")[1].split("## sources")[0]
    assert sec.index("[[llm-wiki|LLM Wiki]]") < sec.index("[[react|ReAct]]")  # 字典序
    assert "— 持久 wiki 模式" in sec


def test_upsert_replaces_existing_entry_in_place(tmp_path):
    idx = make_index(tmp_path)
    idx.upsert(loads_page("react", page_md(type="concept", title="ReAct", summary="旧摘要")))
    idx.upsert(loads_page("react", page_md(type="concept", title="ReAct", summary="新摘要")))
    text = (tmp_path / "index.md").read_text()
    assert text.count("[[react|") == 1
    assert "新摘要" in text and "旧摘要" not in text


def test_remove_entry(tmp_path):
    idx = make_index(tmp_path)
    idx.upsert(loads_page("react", page_md(type="concept", title="ReAct")))
    idx.remove("react")
    assert "react" not in (tmp_path / "index.md").read_text()


def test_other_sections_untouched_byte_identical(tmp_path):
    idx = make_index(tmp_path)
    idx.upsert(loads_page("karpathy", page_md(type="entity", title="Andrej Karpathy")))
    before = (tmp_path / "index.md").read_text()
    idx.upsert(loads_page("react", page_md(type="concept", title="ReAct")))
    after = (tmp_path / "index.md").read_text()
    assert before.split("## concepts")[0] == after.split("## concepts")[0]  # entities 节逐字节未动
