import pytest

from loom.config import LoomPaths
from loom.core.fsutil import atomic_write_text, sha256_file
from loom.core.store import WikiStore
from loom.errors import NotFound
from tests.conftest import page_md


@pytest.fixture
def store(wiki_root):
    return WikiStore(LoomPaths(root=wiki_root))


def seed(wiki_root, name, **kw):
    from loom.models import TYPE_DIRS

    path = wiki_root / "wiki" / TYPE_DIRS[kw.get("type", "concept")] / f"{name}.md"
    atomic_write_text(path, page_md(**kw))
    return path


def test_read_page_returns_content_hash(store, wiki_root):
    path = seed(wiki_root, "react", type="concept", title="ReAct")
    page = store.read_page("react")
    assert page.meta.title == "ReAct"
    assert page.content_hash == sha256_file(path)


def test_read_page_not_found(store):
    with pytest.raises(NotFound):
        store.read_page("nope")


def test_list_pages_filters_by_type_and_tag(store, wiki_root):
    seed(wiki_root, "react", type="concept", title="ReAct", tags=["agent"])
    seed(wiki_root, "karpathy", type="entity", title="Karpathy", tags=["people"])
    assert [p.name for p in store.list_pages(type="concept")] == ["react"]
    assert [p.name for p in store.list_pages(tag="people")] == ["karpathy"]
    assert {p.name for p in store.list_pages()} == {"react", "karpathy"}
