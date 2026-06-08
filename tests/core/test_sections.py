import pytest

from loom.core.sections import apply_patch, list_sections
from loom.errors import NotFound
from loom.models import Patch

BODY = "引言段。\n\n## 背景\n\n旧背景。\n\n### 细节\n\n细节内容。\n\n## 争议\n\n暂无。"


def test_replace_section_keeps_rest_intact():
    out = apply_patch(BODY, Patch(op="replace", section="背景", content="新背景。"))
    assert "新背景。" in out and "旧背景" not in out
    assert "### 细节" not in out  # 子节属于"背景"节，一并替换
    assert "## 争议\n\n暂无。" in out  # 其他节逐字保留
    assert out.startswith("引言段。")


def test_append_to_section():
    out = apply_patch(BODY, Patch(op="append", section="争议", content="A 与 B 矛盾 ⚠️"))
    sec = out.split("## 争议")[1]
    assert "暂无。" in sec and "A 与 B 矛盾 ⚠️" in sec


def test_add_section_at_end():
    out = apply_patch(BODY, Patch(op="add_section", section="参考", content="- [[llm-wiki]]"))
    assert out.rstrip().endswith("- [[llm-wiki]]")
    assert "## 参考" in out


def test_missing_section_raises_with_available_list():
    with pytest.raises(NotFound) as ei:
        apply_patch(BODY, Patch(op="replace", section="不存在", content="x"))
    assert "背景" in str(ei.value) and "争议" in str(ei.value)  # 报错附可用节名，agent 可自纠


def test_list_sections():
    assert [s.title for s in list_sections(BODY)] == ["背景", "细节", "争议"]
