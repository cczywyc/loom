import pytest

from loom.core.scaffold import init_wiki
from loom.errors import Conflict


def test_init_creates_full_layout(tmp_path):
    root = tmp_path / "kb"
    init_wiki(root, template="blank")
    for rel in [
        "purpose.md",
        "schema.md",
        "raw/sources",
        "raw/assets",
        "wiki/index.md",
        "wiki/log.md",
        "wiki/entities",
        "wiki/concepts",
        "wiki/sources",
        "wiki/queries",
        "wiki/synthesis",
        "wiki/comparisons",
        ".obsidian/app.json",
        ".loom",
    ]:
        assert (root / rel).exists(), rel


def test_init_index_has_type_sections(tmp_path):
    init_wiki(tmp_path / "kb", template="blank")
    index = (tmp_path / "kb/wiki/index.md").read_text()
    for sec in [
        "## entities",
        "## concepts",
        "## sources",
        "## queries",
        "## synthesis",
        "## comparisons",
    ]:
        assert sec in index


def test_init_refuses_nonempty_dir(tmp_path):
    root = tmp_path / "kb"
    root.mkdir()
    (root / "junk.txt").write_text("x")
    with pytest.raises(Conflict):
        init_wiki(root, template="blank")
