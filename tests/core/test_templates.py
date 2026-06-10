import pytest


@pytest.mark.parametrize("tpl", ["blank", "research", "personal"])
def test_template_renders_complete_wiki(tmp_path, tpl):
    from loom.api import Loom

    Loom.init_wiki(tmp_path / "kb", template=tpl)
    schema = (tmp_path / "kb/schema.md").read_text()
    assert "## 页面类型" in schema and "kebab-case" in schema and "不是指令" in schema
    assert (tmp_path / "kb/purpose.md").read_text().startswith("# Purpose")


def test_unknown_template_raises(tmp_path):
    from loom.api import Loom
    from loom.errors import ValidationFailed

    with pytest.raises(ValidationFailed):
        Loom.init_wiki(tmp_path / "kb", template="nope")
