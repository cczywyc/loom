from collections.abc import Callable
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from loom.api import Loom
from loom.errors import LoomError
from loom.models import Patch

# 与 build_server 注册的工具一一对应（M0–M4 原语）。
TOOL_NAMES = [
    "wiki_register_source",
    "wiki_parse",
    "wiki_read_page",
    "wiki_list_pages",
    "wiki_write_page",
    "wiki_update_page",
    "wiki_get_index",
    "wiki_get_schema",
    "wiki_get_purpose",
    "wiki_search",
    "wiki_find_related",
    "wiki_graph",
    "wiki_lint_structural",
    "wiki_lint_candidates",
]


def _result(fn: Callable[[], Any]) -> Any:
    """统一出口：成功返回原值；LoomError → 结构化错误，agent 看 code 决定重读/放弃，而非抛裸异常。"""
    try:
        return fn()
    except LoomError as e:
        error = {"code": getattr(e, "code", "LOOM_ERROR"), "message": str(e), **e.details()}
        return {"ok": False, "error": error}


def build_server(wiki_path: Path | str) -> FastMCP:
    """构造一个绑定到 wiki_path 的 FastMCP 服务：每个工具一一映射原语，零推理。"""
    loom = Loom(wiki_path)
    server = FastMCP("loom")

    @server.tool(name="wiki_register_source")
    def wiki_register_source(path: str):
        """Register a source file: copy into raw/sources, hash, dedupe. Returns relative path, sha256, is_new."""
        return _result(lambda: loom.register_source(path).model_dump())

    @server.tool(name="wiki_parse")
    def wiki_parse(path: str):
        """Parse a registered source (path relative to wiki root, e.g. raw/sources/x.pdf) into text + metadata."""
        return _result(lambda: loom.parse(path).model_dump())

    @server.tool(name="wiki_read_page")
    def wiki_read_page(name: str):
        """Read one wiki page. Returns name, meta, body, content_hash. Pass content_hash as base_hash to later overwrite it."""
        return _result(lambda: loom.read_page(name).model_dump())

    @server.tool(name="wiki_list_pages")
    def wiki_list_pages(type: str | None = None, tag: str | None = None):
        """List page summaries, optionally filtered by type and/or tag."""
        return _result(lambda: [p.model_dump() for p in loom.list_pages(type=type, tag=tag)])

    @server.tool(name="wiki_write_page")
    def wiki_write_page(name: str, content: str, base_hash: str | None = None):
        """Create a wiki page (full markdown incl. frontmatter). For an EXISTING page you MUST pass base_hash from a prior wiki_read_page, or use wiki_update_page for section edits. Returns write result with new content_hash and warnings."""
        return _result(lambda: loom.write_page(name, content, base_hash=base_hash).model_dump())

    @server.tool(name="wiki_update_page")
    def wiki_update_page(
        name: str, op: str, content: str, section: str | None = None, base_hash: str | None = None
    ):
        """Non-destructively patch one page. op = replace|append|add_section|set_frontmatter; pass section for section ops. Lock-internal read-modify-write, so it never loses updates."""
        return _result(
            lambda: loom.update_page(
                name, Patch(op=op, section=section, content=content), base_hash=base_hash
            ).model_dump()
        )

    @server.tool(name="wiki_get_index")
    def wiki_get_index():
        """Return index.md (table of contents). Read this first to locate content."""
        return _result(loom.get_index)

    @server.tool(name="wiki_get_schema")
    def wiki_get_schema():
        """Return schema.md (behavior contract: page types, naming, linking, ingest rules). Read before writing."""
        return _result(loom.get_schema)

    @server.tool(name="wiki_get_purpose")
    def wiki_get_purpose():
        """Return purpose.md (goals, key questions, evolving thesis)."""
        return _result(loom.get_purpose)

    @server.tool(name="wiki_search")
    def wiki_search(query: str, mode: str = "keyword", limit: int = 10):
        """Keyword (BM25) search over pages, ranked by relevance. Returns hits with name/title/type/score/snippet."""
        return _result(lambda: [h.model_dump() for h in loom.search(query, mode=mode, limit=limit)])

    @server.tool(name="wiki_find_related")
    def wiki_find_related(text: str, limit: int = 10):
        """Given a snippet or entity name, return possibly-related existing pages + reason. Use during ingest to decide: new page vs merge into an existing one."""
        return _result(lambda: [r.model_dump() for r in loom.find_related(text, limit=limit)])

    @server.tool(name="wiki_graph")
    def wiki_graph(name: str | None = None, depth: int = 1):
        """Wikilink graph. With name: its depth-N neighborhood; without: the full graph. Returns nodes + edges."""
        return _result(lambda: loom.graph(name, depth=depth).model_dump())

    @server.tool(name="wiki_lint_structural")
    def wiki_lint_structural():
        """Structural lint: orphan/broken-link/bad-frontmatter/bad-name/stale/duplicate-title. Never raises. Returns {findings:[{kind,page,message,fixable}]}. These are definite structural problems to handle."""
        return _result(lambda: loom.lint_structural().model_dump())

    @server.tool(name="wiki_lint_candidates")
    def wiki_lint_candidates():
        """Surface semantic-suspect candidates (possible-contradiction/sparse-area/stale-cluster) for YOU to judge — the tool surfaces, you decide. Returns [{kind,pages,reason}]; read the pages before concluding."""
        return _result(lambda: [c.model_dump() for c in loom.lint_candidates()])

    return server
