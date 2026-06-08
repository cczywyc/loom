from loom.validate import is_kebab, extract_wikilinks, validate_page
from loom.models import loads_page
from tests.conftest import page_md


def test_is_kebab():
    assert is_kebab("llm-wiki")
    assert is_kebab("react2025")
    assert not is_kebab("LLM-Wiki")  # 大写
    assert not is_kebab("llm_wiki")  # 下划线
    assert not is_kebab("中文名")  # 非 ASCII：name 必须 kebab，中文放 title
    assert not is_kebab("-bad")


def test_extract_wikilinks_handles_alias_and_anchor():
    body = "见 [[llm-wiki|LLM Wiki 模式]] 与 [[andrej-karpathy]]，另见 [[loom#架构|本工具]]。"
    assert extract_wikilinks(body) == ["llm-wiki", "andrej-karpathy", "loom"]


def test_validate_page_dangling_link_is_warning_not_error():
    page = loads_page("a", page_md(type="concept", title="A", body="链接 [[not-exist-yet]]"))
    problems, warnings = validate_page(page, known_names={"a"})
    assert problems == []
    assert any("not-exist-yet" in w for w in warnings)


def test_validate_page_bad_name_is_error():
    page = loads_page("Bad_Name", page_md(type="concept", title="X"))
    problems, _ = validate_page(page, known_names=set())
    assert any("kebab" in p for p in problems)
