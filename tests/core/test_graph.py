from loom.core.graph import GraphIndex
from tests.conftest import page_md


def seed_linked(loom):
    loom.write_page("a", page_md(type="concept", title="A", body="链接 [[b]] 与 [[c]]"))
    loom.write_page("b", page_md(type="concept", title="B", body="回链 [[a]]，另指 [[ghost]]"))
    loom.write_page("c", page_md(type="concept", title="C", body="无出链"))
    loom.write_page("lonely", page_md(type="concept", title="孤独", body="谁也不连"))


def test_subgraph_depth1(loom):
    seed_linked(loom)
    g = loom.graph("a", depth=1)
    assert {n.name for n in g.nodes} == {"a", "b", "c"}
    assert ("a", "b") in {(e.src, e.dst) for e in g.edges}


def test_subgraph_depth_expands_via_in_and_out_edges(loom):
    seed_linked(loom)
    # c 无出链，但 a 链入 c：depth=1 应含入边邻居 a；depth=2 经 a 再到 b
    g1 = loom.graph("c", depth=1)
    assert {n.name for n in g1.nodes} == {"c", "a"}
    g2 = loom.graph("c", depth=2)
    assert {n.name for n in g2.nodes} == {"c", "a", "b"}


def test_full_graph_when_no_name(loom):
    seed_linked(loom)
    g = loom.graph()
    assert {n.name for n in g.nodes} == {"a", "b", "c", "lonely"}


def test_orphans_and_broken_links(loom):
    seed_linked(loom)
    gi = GraphIndex.build(loom.store)
    assert gi.orphans() == ["lonely"]  # 无入无出
    assert gi.broken_links() == [("b", "ghost")]  # 指向不存在页
