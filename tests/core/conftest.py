import pytest

from loom.config import LoomPaths
from loom.core.store import WikiStore


@pytest.fixture
def store(wiki_root):
    return WikiStore(LoomPaths(root=wiki_root))
