import pytest

from loom.models import loads_page, dumps_page, TYPE_DIRS
from loom.errors import ValidationFailed

from tests.conftest import page_md


def test_loads_dumps_roundtrip():
    text = page_md(
        type="concept", title="LLM Wiki 模式", tags=["agent"], body="正文。\n\n## 要点\n\n内容。"
    )
    page = loads_page("llm-wiki", text)
    assert page.name == "llm-wiki"
    assert page.meta.type == "concept"
    assert page.meta.title == "LLM Wiki 模式"
    assert "## 要点" in page.body
    assert loads_page("llm-wiki", dumps_page(page)).body == page.body  # 序列化稳定


def test_loads_page_missing_frontmatter_raises():
    with pytest.raises(ValidationFailed):
        loads_page("x", "没有 frontmatter 的裸文本")


def test_loads_page_missing_required_field_raises():
    with pytest.raises(ValidationFailed) as ei:
        loads_page("x", "---\ntype: concept\n---\n\nbody")  # 缺 title/created/updated
    assert "title" in str(ei.value)


def test_type_dirs_cover_all_page_types():
    assert set(TYPE_DIRS) == {"entity", "concept", "source", "query", "synthesis", "comparison"}


def test_loads_page_accepts_unquoted_yaml_dates():
    # YAML 把无引号的 2026-06-08 解析成 date 对象；created/updated 需容忍并归一为字符串
    # （scaffold 的 schema.md 示例正是无引号日期，agent 会照写）。
    text = "---\ntype: concept\ntitle: X\ncreated: 2026-06-08\nupdated: 2026-06-08\n---\n\nbody"
    page = loads_page("x", text)
    assert page.meta.created == "2026-06-08"
    assert page.meta.updated == "2026-06-08"
