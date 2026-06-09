import json

from click.testing import CliRunner

from loom.transport.cli import cli


def test_init_creates_wiki(tmp_path):
    r = CliRunner().invoke(cli, ["init", str(tmp_path / "kb")])
    assert r.exit_code == 0
    assert (tmp_path / "kb" / ".loom").exists()


def test_init_nonempty_dir_exits_2_with_json_error(tmp_path):
    (tmp_path / "kb").mkdir()
    (tmp_path / "kb" / "x").write_text("x")
    r = CliRunner().invoke(cli, ["--json", "init", str(tmp_path / "kb")])
    assert r.exit_code == 2
    err = json.loads(r.output)
    assert err["ok"] is False and err["error"]["code"] == "CONFLICT"


def test_command_outside_wiki_exits_1(tmp_path):
    # --wiki-path 指向一个不含 .loom/ 的空目录，模拟"不在 wiki 内"
    r = CliRunner().invoke(cli, ["--wiki-path", str(tmp_path), "index"])
    assert r.exit_code == 1
