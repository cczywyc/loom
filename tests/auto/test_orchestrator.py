import json
import sys

import pytest

from loom.auto.orchestrator import auto_ingest


class FakeProvider:
    """脚本化应答：按调用次序返回预置 JSON，不联网。"""

    def __init__(self, scripted: list[str]):
        self.scripted = list(scripted)
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self.scripted.pop(0)


def _page(name: str, title: str, kind: str) -> str:
    return (
        f"---\ntype: {kind}\ntitle: {title}\ncreated: 2026-06-11\nupdated: 2026-06-11\n---\n\n"
        f"关于 {title} 的说明。"
    )


def test_auto_ingest_full_flow(loom, tmp_path):
    src = tmp_path / "a.md"
    src.write_text("---\ntitle: t\n---\n\nKarpathy 提出 LLM Wiki。")
    fake = FakeProvider(
        [
            json.dumps(
                {
                    "items": [
                        {"kind": "entity", "name": "andrej-karpathy", "title": "Andrej Karpathy"},
                        {"kind": "concept", "name": "llm-wiki", "title": "LLM Wiki"},
                    ]
                }
            ),
            json.dumps(
                {
                    "decision": "create",
                    "content": _page("andrej-karpathy", "Andrej Karpathy", "entity"),
                }
            ),
            json.dumps({"decision": "create", "content": _page("llm-wiki", "LLM Wiki", "concept")}),
            json.dumps({"purpose_update": None}),
        ]
    )
    report = auto_ingest(loom, src, provider=fake)
    assert set(report.pages_written) >= {"andrej-karpathy", "llm-wiki"}
    assert any("UNTRUSTED" in u for _, u in fake.calls)  # 源文本以 untrusted 包裹喂给 provider


def test_auto_unavailable_without_extra(monkeypatch, tmp_path):
    from loom.errors import LoomError
    from loom.transport.cli import _build_provider

    monkeypatch.setitem(sys.modules, "anthropic", None)  # 让 import anthropic 失败
    monkeypatch.setitem(sys.modules, "openai", None)
    with pytest.raises(LoomError, match=r"loom-wiki\[auto\]"):
        _build_provider()

    from click.testing import CliRunner

    from loom.transport.cli import cli

    root = tmp_path / "kb"
    CliRunner().invoke(cli, ["init", str(root)])
    src = tmp_path / "a.md"
    src.write_text("内容")
    res = CliRunner().invoke(cli, ["--wiki-path", str(root), "ingest", str(src), "--auto"])
    assert res.exit_code == 1  # 缺 extra → 退出 1
