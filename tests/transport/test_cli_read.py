import json

import pytest
from click.testing import CliRunner

from loom.api import Loom
from loom.transport.cli import cli
from tests.conftest import page_md


@pytest.fixture
def seeded_wiki(tmp_path):
    """(runner, root)：先用 CLI init，再用 Loom API 种两页（react 概念页 + karpathy 实体页）。"""
    root = tmp_path / "kb"
    runner = CliRunner()
    runner.invoke(cli, ["init", str(root)])
    loom = Loom(root)
    loom.write_page("react", page_md(type="concept", title="ReAct", summary="推理+行动"))
    loom.write_page("karpathy", page_md(type="entity", title="Karpathy"))
    return runner, root


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
