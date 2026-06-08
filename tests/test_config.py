import pytest

from loom.config import LoomPaths, find_wiki_root
from loom.errors import NotFound


def test_paths_layout(tmp_path):
    p = LoomPaths(root=tmp_path)
    assert p.wiki_dir == tmp_path / "wiki"
    assert p.raw_sources == tmp_path / "raw" / "sources"
    assert p.raw_assets == tmp_path / "raw" / "assets"
    assert p.loom_dir == tmp_path / ".loom"
    assert p.index_md == tmp_path / "wiki" / "index.md"
    assert p.log_md == tmp_path / "wiki" / "log.md"
    assert p.schema_md == tmp_path / "schema.md"
    assert p.purpose_md == tmp_path / "purpose.md"


def test_find_wiki_root_walks_up(tmp_path):
    (tmp_path / ".loom").mkdir()
    deep = tmp_path / "wiki" / "concepts"
    deep.mkdir(parents=True)
    assert find_wiki_root(deep) == tmp_path


def test_find_wiki_root_not_found_raises(tmp_path):
    with pytest.raises(NotFound):
        find_wiki_root(tmp_path)
