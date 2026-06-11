import json

import pytest
from click.testing import CliRunner

from loom.api import Loom
from loom.errors import Conflict
from loom.models import Patch
from loom.transport.cli import cli
from tests.conftest import page_md


def _seed(tmp_path):
    root = tmp_path / "kb"
    CliRunner().invoke(cli, ["init", str(root)])
    return root


def test_cli_write_stale_base_hash_exits_2_with_current_hash(tmp_path):
    root = _seed(tmp_path)
    loom = Loom(root)
    r1 = loom.write_page("p", page_md(type="concept", title="P", body="v1"))
    loom.write_page("p", page_md(type="concept", title="P", body="v2"), base_hash=r1.content_hash)
    f = tmp_path / "c.md"
    f.write_text(page_md(type="concept", title="P", body="v3"))
    res = CliRunner().invoke(
        cli,
        [
            "--wiki-path",
            str(root),
            "--json",
            "write",
            "p",
            "--from-file",
            str(f),
            "--base-hash",
            r1.content_hash,
        ],
    )
    assert res.exit_code == 2
    err = json.loads(res.output)["error"]
    assert err["code"] == "CONFLICT"
    assert err["current_hash"]  # 冲突体携带当前 hash → agent 一步恢复


def test_update_passes_base_hash_through_to_occ(tmp_path):
    root = _seed(tmp_path)
    loom = Loom(root)
    r1 = loom.write_page("p", page_md(type="concept", title="P", body="## 甲\n\na"))
    loom.update_page("p", Patch(op="append", section="甲", content="b"), base_hash=r1.content_hash)
    with pytest.raises(Conflict) as ei:
        loom.update_page(
            "p", Patch(op="append", section="甲", content="c"), base_hash=r1.content_hash
        )
    assert ei.value.current_hash  # update 也透传 base_hash 并附当前 hash


def test_conflict_message_names_changed_sections(tmp_path):
    root = _seed(tmp_path)
    loom = Loom(root)
    body = "## 甲\n\n原甲\n\n## 乙\n\n原乙"
    r1 = loom.write_page("p", page_md(type="concept", title="P", body=body))
    loom.update_page(
        "p", Patch(op="replace", section="甲", content="新甲"), base_hash=r1.content_hash
    )
    with pytest.raises(Conflict) as ei:
        loom.write_page(
            "p", page_md(type="concept", title="P", body=body), base_hash=r1.content_hash
        )
    assert "甲" in str(ei.value)  # 信息点名变了的节
    assert "甲" in (ei.value.changed_sections or [])
    assert "乙" not in (ei.value.changed_sections or [])  # 没变的节不报
