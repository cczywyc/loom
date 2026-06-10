import json

from loom.transport.cli import cli


def test_search_json_returns_hit_array(seeded_wiki):
    runner, root = seeded_wiki
    r = runner.invoke(cli, ["--wiki-path", str(root), "--json", "search", "ReAct"])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert isinstance(data, list) and any(h["name"] == "react" for h in data)


def test_graph_json_returns_nodes_and_edges(seeded_wiki):
    runner, root = seeded_wiki
    r = runner.invoke(cli, ["--wiki-path", str(root), "--json", "graph"])
    assert r.exit_code == 0
    g = json.loads(r.output)
    assert "nodes" in g and "edges" in g


def test_find_related_json_returns_array(seeded_wiki):
    runner, root = seeded_wiki
    r = runner.invoke(cli, ["--wiki-path", str(root), "--json", "find-related", "ReAct 推理"])
    assert r.exit_code == 0
    assert isinstance(json.loads(r.output), list)


def test_mcp_tool_names_include_m2():
    from loom.transport.mcp import TOOL_NAMES

    assert {"wiki_search", "wiki_find_related", "wiki_graph"} <= set(TOOL_NAMES)
