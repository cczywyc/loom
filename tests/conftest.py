import pytest
import yaml


def page_md(*, type: str, title: str, body: str = "", **extra) -> str:
    """构造一份合法页面的 markdown 文本（frontmatter + body）。"""
    meta = {
        "type": type,
        "title": title,
        "summary": extra.pop("summary", ""),
        "sources": extra.pop("sources", []),
        "source_hashes": extra.pop("source_hashes", {}),
        "created": "2026-06-05",
        "updated": "2026-06-05",
        "tags": extra.pop("tags", []),
        **extra,
    }
    return "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\n" + body


@pytest.fixture
def wiki_root(tmp_path):
    from loom.api import Loom

    Loom.init_wiki(tmp_path / "kb", template="blank")
    return tmp_path / "kb"


@pytest.fixture
def loom(wiki_root):
    from loom.api import Loom

    return Loom(wiki_root)
