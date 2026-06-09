import pytest
from click.testing import CliRunner

from loom.api import Loom
from loom.transport.cli import cli
from tests.conftest import page_md


@pytest.fixture
def seeded_wiki(tmp_path):
    """(runner, root)：CLI init 后用 Loom API 种两页。react 含「要点」节供 update 测试。"""
    root = tmp_path / "kb"
    runner = CliRunner()
    runner.invoke(cli, ["init", str(root)])
    loom = Loom(root)
    loom.write_page(
        "react",
        page_md(type="concept", title="ReAct", summary="推理+行动", body="## 要点\n\n初始要点。"),
    )
    loom.write_page("karpathy", page_md(type="entity", title="Karpathy"))
    return runner, root
