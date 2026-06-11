import pytest

from loom.transport.mcp import TOOL_NAMES, build_server
from tests.conftest import page_md

M0_M1_TOOLS = {
    "wiki_register_source",
    "wiki_parse",
    "wiki_read_page",
    "wiki_list_pages",
    "wiki_write_page",
    "wiki_update_page",
    "wiki_get_index",
    "wiki_get_schema",
    "wiki_get_purpose",
}


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_all_current_primitives_exposed(wiki_root):
    build_server(wiki_root)
    assert M0_M1_TOOLS <= set(TOOL_NAMES)


@pytest.mark.anyio
async def test_write_then_read_via_mcp(wiki_root):
    # mcp SDK 当前版本：进程内 client 是单个 ClientSession（已 initialize），不是 (client, _) 元组
    from mcp.shared.memory import create_connected_server_and_client_session as connect

    server = build_server(wiki_root)
    async with connect(server._mcp_server) as client:
        res = await client.call_tool(
            "wiki_write_page",
            {"name": "react", "content": page_md(type="concept", title="ReAct")},
        )
        assert "react" in str(res)
        res = await client.call_tool("wiki_read_page", {"name": "react"})
        assert "ReAct" in str(res)


@pytest.mark.anyio
async def test_error_returns_structured_code(wiki_root):
    from mcp.shared.memory import create_connected_server_and_client_session as connect

    server = build_server(wiki_root)
    async with connect(server._mcp_server) as client:
        res = await client.call_tool("wiki_read_page", {"name": "nope"})
        assert "NOT_FOUND" in str(res)


M4_TOOLS = {"wiki_lint_structural", "wiki_lint_candidates"}


def test_m4_lint_tools_exposed(wiki_root):
    build_server(wiki_root)
    assert M4_TOOLS <= set(TOOL_NAMES)


@pytest.mark.anyio
async def test_lint_via_mcp(wiki_root):
    from mcp.shared.memory import create_connected_server_and_client_session as connect

    server = build_server(wiki_root)
    async with connect(server._mcp_server) as client:
        await client.call_tool(
            "wiki_write_page",
            {"name": "a", "content": page_md(type="concept", title="A", body="[[ghost]]")},
        )
        res = await client.call_tool("wiki_lint_structural", {})
        assert "broken-link" in str(res)  # 坏链被报出
        res = await client.call_tool("wiki_lint_candidates", {})
        assert "sparse-area" in str(res)  # 单页孤立 → 稀疏区候选


@pytest.mark.anyio
async def test_write_conflict_includes_current_hash_via_mcp(wiki_root):
    from mcp.shared.memory import create_connected_server_and_client_session as connect

    from loom.api import Loom

    loom = Loom(wiki_root)
    r1 = loom.write_page("p", page_md(type="concept", title="P", body="v1"))
    loom.write_page("p", page_md(type="concept", title="P", body="v2"), base_hash=r1.content_hash)
    server = build_server(wiki_root)
    async with connect(server._mcp_server) as client:
        res = await client.call_tool(
            "wiki_write_page",
            {
                "name": "p",
                "content": page_md(type="concept", title="P", body="v3"),
                "base_hash": r1.content_hash,
            },
        )
        assert "CONFLICT" in str(res) and "current_hash" in str(res)
