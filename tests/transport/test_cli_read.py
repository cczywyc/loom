import json

from loom.transport.cli import cli

# `seeded_wiki` fixture 由 tests/transport/conftest.py 提供（read / write 测试共用）。


def test_read_outputs_full_page(seeded_wiki):
    runner, root = seeded_wiki
    r = runner.invoke(cli, ["--wiki-path", str(root), "read", "react"])
    assert r.exit_code == 0 and "ReAct" in r.output and "---" in r.output  # 原文含 frontmatter


def test_read_json_includes_content_hash(seeded_wiki):
    runner, root = seeded_wiki
    r = runner.invoke(cli, ["--wiki-path", str(root), "--json", "read", "react"])
    data = json.loads(r.output)
    assert data["name"] == "react" and len(data["content_hash"]) == 64


def test_list_filters(seeded_wiki):
    runner, root = seeded_wiki
    r = runner.invoke(cli, ["--wiki-path", str(root), "--json", "list", "--type", "concept"])
    assert all(p["type"] == "concept" for p in json.loads(r.output))


def test_read_missing_page_exit_1(seeded_wiki):
    runner, root = seeded_wiki
    assert runner.invoke(cli, ["--wiki-path", str(root), "read", "nope"]).exit_code == 1
