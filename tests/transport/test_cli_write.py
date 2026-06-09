import json

from loom.transport.cli import cli
from tests.conftest import page_md


def test_write_from_file_then_conflict_without_base_hash(seeded_wiki, tmp_path):
    runner, root = seeded_wiki
    f = tmp_path / "p.md"
    f.write_text(page_md(type="concept", title="新页"))
    first = runner.invoke(
        cli, ["--wiki-path", str(root), "write", "new-page", "--from-file", str(f)]
    )
    assert first.exit_code == 0
    r = runner.invoke(cli, ["--wiki-path", str(root), "write", "new-page", "--from-file", str(f)])
    assert r.exit_code == 2  # 已存在且无 --base-hash → CONFLICT


def test_update_section_from_stdin(seeded_wiki):
    runner, root = seeded_wiki
    r = runner.invoke(
        cli,
        ["--wiki-path", str(root), "update", "react", "--section", "要点", "--op", "append"],
        input="补充一条。",
    )
    assert r.exit_code == 0


def test_parse_outputs_text(seeded_wiki, tmp_path):
    runner, root = seeded_wiki
    doc = tmp_path / "a.md"
    doc.write_text("---\ntitle: t\n---\n\n你好")
    reg = runner.invoke(cli, ["--wiki-path", str(root), "--json", "register", str(doc)])
    rel = json.loads(reg.output)["path"]
    r = runner.invoke(cli, ["--wiki-path", str(root), "parse", rel])
    assert "你好" in r.output
