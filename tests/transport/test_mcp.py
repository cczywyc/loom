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
