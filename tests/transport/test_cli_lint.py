import json

from click.testing import CliRunner

from loom.api import Loom
from loom.transport.cli import cli
from tests.conftest import page_md


def _init(tmp_path):
    root = tmp_path / "kb"
    CliRunner().invoke(cli, ["init", str(root)])
    return root


def test_lint_structural_json_reports_broken_link(tmp_path):
    root = _init(tmp_path)
    Loom(root).write_page("a", page_md(type="concept", title="A", body="[[ghost]]"))
    r = CliRunner().invoke(cli, ["--wiki-path", str(root), "--json", "lint", "--structural"])
    assert r.exit_code == 0
    kinds = {f["kind"] for f in json.loads(r.output)["report"]["findings"]}
    assert "broken-link" in kinds


def test_lint_candidates_json_reports_contradiction(tmp_path):
    root = _init(tmp_path)
    loom = Loom(root)
    loom.write_page("x", page_md(type="concept", title="X"))
    loom.write_page("y", page_md(type="concept", title="Y"))
    loom.write_page("a", page_md(type="synthesis", title="A", body="[[x]] [[y]]"))
    loom.write_page("b", page_md(type="synthesis", title="B", body="[[x]] [[y]]"))
    r = CliRunner().invoke(cli, ["--wiki-path", str(root), "--json", "lint", "--candidates"])
    assert r.exit_code == 0
    kinds = {c["kind"] for c in json.loads(r.output)["candidates"]}
    assert "possible-contradiction" in kinds


def test_lint_fix_resyncs_index_via_cli(tmp_path):
    root = _init(tmp_path)
    Loom(root).write_page("a", page_md(type="concept", title="A"))
    idx = root / "wiki/index.md"
    idx.write_text(idx.read_text().replace("- [[a|A]]", ""))
    r = CliRunner().invoke(
        cli, ["--wiki-path", str(root), "--json", "lint", "--structural", "--fix"]
    )
    assert r.exit_code == 0
    assert json.loads(r.output)["fixed"]  # 有修复记录
    assert "[[a|A]]" in idx.read_text()
