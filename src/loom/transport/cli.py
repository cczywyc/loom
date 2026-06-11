import json
from pathlib import Path

import click

from loom.api import Loom
from loom.config import find_wiki_root
from loom.errors import Conflict, LoomError, NotFound, ValidationFailed
from loom.models import Patch, dumps_page


def _exit_code(err: LoomError) -> int:
    # 0.3 约定：ValidationFailed/Conflict → 2（agent 可机械区分、应重读再试）；其余 → 1。
    return 2 if isinstance(err, ValidationFailed | Conflict) else 1


class LoomGroup(click.Group):
    """统一错误出口：捕获任意子命令抛出的 LoomError → --json 错误 JSON + 退出码 2/1。"""

    def invoke(self, ctx: click.Context):
        try:
            return super().invoke(ctx)
        except LoomError as e:
            code = getattr(e, "code", "LOOM_ERROR")
            error = {"code": code, "message": str(e), **e.details()}
            if ctx.obj and ctx.obj.get("json"):
                click.echo(json.dumps({"ok": False, "error": error}, ensure_ascii=False))
            else:
                click.echo(f"error [{code}]: {e}", err=True)
                if error.get("current_hash"):
                    click.echo(f"  current_hash: {error['current_hash']}", err=True)
            ctx.exit(_exit_code(e))


@click.group(cls=LoomGroup)
@click.option("--wiki-path", default=None, help="wiki 根目录；省略则从当前目录向上查找 .loom/")
@click.option("--json", "as_json", is_flag=True, help="以 JSON 输出，便于 agent 解析")
@click.pass_context
def cli(ctx: click.Context, wiki_path: str | None, as_json: bool):
    """Loom —— 让 agent 维护一座互相链接的 Markdown 知识库。"""
    ctx.obj = {"wiki_path": wiki_path, "json": as_json}


def _get_loom(ctx: click.Context) -> Loom:
    """解析 wiki 根并返回 Loom；--wiki-path 必须指向真实 wiki，否则从 cwd 向上找。"""
    wiki_path = ctx.obj.get("wiki_path")
    if wiki_path:
        root = Path(wiki_path)
        if not (root / ".loom").is_dir():
            raise NotFound(f"'{root}' is not a loom wiki; run 'loom init' first")
    else:
        root = find_wiki_root(Path.cwd())
    return Loom(root)


@cli.command()
@click.argument("path")
@click.option("--template", default="blank", help="模板：目前仅 blank")
@click.pass_context
def init(ctx: click.Context, path: str, template: str):
    """在 PATH 初始化一座新的 loom wiki。"""
    Loom.init_wiki(path, template=template)
    if ctx.obj.get("json"):
        click.echo(json.dumps({"ok": True, "path": str(path)}, ensure_ascii=False))
    else:
        click.echo(f"initialized loom wiki at {path}")


@cli.command()
@click.pass_context
def index(ctx: click.Context):
    """打印 index.md（内容目录）。"""
    click.echo(_get_loom(ctx).get_index())


@cli.command()
@click.argument("name")
@click.pass_context
def read(ctx: click.Context, name: str):
    """读取单页：默认输出完整 markdown；--json 输出结构化页面（含 content_hash）。"""
    page = _get_loom(ctx).read_page(name)
    if ctx.obj.get("json"):
        click.echo(json.dumps(page.model_dump(), ensure_ascii=False))
    else:
        click.echo(dumps_page(page))


@cli.command(name="list")
@click.option("--type", "type_", default=None, help="按页面类型过滤")
@click.option("--tag", default=None, help="按标签过滤")
@click.pass_context
def list_(ctx: click.Context, type_: str | None, tag: str | None):
    """列出页面摘要（可按 --type / --tag 过滤）。"""
    pages = _get_loom(ctx).list_pages(type=type_, tag=tag)
    if ctx.obj.get("json"):
        click.echo(json.dumps([p.model_dump() for p in pages], ensure_ascii=False))
    else:
        for p in pages:
            click.echo(f"[{p.type}] {p.name} — {p.title}")


@cli.command()
@click.pass_context
def schema(ctx: click.Context):
    """打印 schema.md（wiki 行为契约）。"""
    click.echo(_get_loom(ctx).get_schema())


@cli.command()
@click.pass_context
def purpose(ctx: click.Context):
    """打印 purpose.md（目标与演进论点）。"""
    click.echo(_get_loom(ctx).get_purpose())


def _read_content(from_file: str | None) -> str:
    """内容来源：--from-file 优先，否则读 stdin。"""
    if from_file:
        return Path(from_file).read_text(encoding="utf-8")
    return click.get_text_stream("stdin").read()


def _emit_write_result(ctx: click.Context, res) -> None:
    if ctx.obj.get("json"):
        click.echo(json.dumps(res.model_dump(), ensure_ascii=False))
    else:
        action = "created" if res.created else "updated"
        click.echo(f"{action} {res.name} (hash {res.content_hash[:12]}…)")
        for w in res.warnings:
            click.echo(f"  warning: {w}", err=True)


def _emit_staged(ctx: click.Context, rid: str) -> None:
    if ctx.obj.get("json"):
        click.echo(json.dumps({"ok": True, "staged": rid}, ensure_ascii=False))
    else:
        click.echo(f"staged for review: {rid}  (loom review show/apply/reject {rid})")


@cli.command()
@click.argument("name")
@click.option(
    "--from-file", "from_file", type=click.Path(exists=True), help="内容文件；省略读 stdin"
)
@click.option("--base-hash", "base_hash", default=None, help="OCC：覆写已存在页须带读取时的 hash")
@click.option("--review", "review_", is_flag=True, help="不直接写，暂存为待人审的 diff")
@click.pass_context
def write(
    ctx: click.Context, name: str, from_file: str | None, base_hash: str | None, review_: bool
):
    """写整页（新建或覆写）。内容来自 --from-file 或 stdin；--review 暂存待人审。"""
    loom = _get_loom(ctx)
    content = _read_content(from_file)
    if review_:
        _emit_staged(ctx, loom.stage_review(name, content, base_hash=base_hash))
        return
    _emit_write_result(ctx, loom.write_page(name, content, base_hash=base_hash))


@cli.command()
@click.argument("name")
@click.option("--section", default=None, help="目标小节（add-section 时为新节名）")
@click.option(
    "--op",
    default="replace",
    type=click.Choice(["replace", "append", "add-section", "set-frontmatter"]),
)
@click.option(
    "--from-file", "from_file", type=click.Path(exists=True), help="内容文件；省略读 stdin"
)
@click.option("--base-hash", "base_hash", default=None)
@click.option("--review", "review_", is_flag=True, help="不直接写，暂存为待人审的 diff")
@click.pass_context
def update(
    ctx: click.Context,
    name: str,
    section: str | None,
    op: str,
    from_file: str | None,
    base_hash: str | None,
    review_: bool,
):
    """段级更新单页。内容来自 --from-file 或 stdin；--review 暂存待人审。"""
    loom = _get_loom(ctx)
    patch = Patch(op=op.replace("-", "_"), section=section, content=_read_content(from_file))
    if review_:
        _emit_staged(ctx, loom.stage_update_review(name, patch, base_hash=base_hash))
        return
    _emit_write_result(ctx, loom.update_page(name, patch, base_hash=base_hash))


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.pass_context
def register(ctx: click.Context, path: str):
    """把来源文件拷入 raw/sources 并登记（按内容去重）。"""
    ref = _get_loom(ctx).register_source(path)
    if ctx.obj.get("json"):
        click.echo(json.dumps(ref.model_dump(), ensure_ascii=False))
    else:
        click.echo(f"{'new' if ref.is_new else 'exists'}: {ref.path}")


@cli.command()
@click.argument("path")
@click.option("--raw", is_flag=True, help="输出裸文本，不包裹不可信分隔（默认包裹以防注入）")
@click.pass_context
def parse(ctx: click.Context, path: str, raw: bool):
    """解析 raw/ 下来源（相对 wiki 根的路径），输出文本（--json 输出完整结构）。

    默认把文本包成「不可信资料」块交给 agent（防 prompt 注入）；--raw 关闭包裹。
    """
    doc = _get_loom(ctx).parse(path, wrap=not raw)
    if ctx.obj.get("json"):
        click.echo(json.dumps(doc.model_dump(), ensure_ascii=False))
    else:
        click.echo(doc.text)


@cli.command()
@click.argument("query")
@click.option("--mode", default="keyword", help="检索模式（目前仅 keyword）")
@click.option("--limit", default=10, type=int)
@click.pass_context
def search(ctx: click.Context, query: str, mode: str, limit: int):
    """关键词检索（BM25），返回按相关性排序的命中。"""
    hits = _get_loom(ctx).search(query, mode=mode, limit=limit)
    if ctx.obj.get("json"):
        click.echo(json.dumps([h.model_dump() for h in hits], ensure_ascii=False))
    else:
        for h in hits:
            click.echo(f"{h.score:.2f}  [{h.type}] {h.name} — {h.snippet}")


@cli.command(name="find-related")
@click.argument("text")
@click.option("--limit", default=10, type=int)
@click.pass_context
def find_related(ctx: click.Context, text: str, limit: int):
    """给一段文本，返回可能相关的已有页 + 理由（供新建 vs 并入判断）。"""
    refs = _get_loom(ctx).find_related(text, limit=limit)
    if ctx.obj.get("json"):
        click.echo(json.dumps([r.model_dump() for r in refs], ensure_ascii=False))
    else:
        for r in refs:
            click.echo(f"{r.score:.2f}  {r.name} — {r.reason}")


@cli.command()
@click.argument("name", required=False)
@click.option("--depth", default=1, type=int)
@click.pass_context
def graph(ctx: click.Context, name: str | None, depth: int):
    """图谱：给 name 取其 depth 层邻域，否则返回全图（nodes + edges）。"""
    g = _get_loom(ctx).graph(name, depth=depth)
    if ctx.obj.get("json"):
        click.echo(json.dumps(g.model_dump(), ensure_ascii=False))
    else:
        click.echo("nodes: " + ", ".join(n.name for n in g.nodes))
        for e in g.edges:
            click.echo(f"  {e.src} -> {e.dst}")


@cli.command()
@click.option(
    "--structural", is_flag=True, help="结构检查（孤儿/坏链/坏 frontmatter/坏名/过期/重名）"
)
@click.option("--candidates", "candidates_", is_flag=True, help="浮现语义可疑对象，交你判断")
@click.option("--fix", is_flag=True, help="先自动修复安全子集（index/日期/source_hashes），再报告")
@click.pass_context
def lint(ctx: click.Context, structural: bool, candidates_: bool, fix: bool):
    """wiki 体检。--structural 报机械问题；--candidates 浮现可疑对象；--fix 修安全子集。"""
    loom = _get_loom(ctx)
    if not structural and not candidates_:
        structural = True  # 未指定模式时默认结构检查
    fixed: list[str] = []
    if fix:
        from loom.lint.fix import apply_fixes

        fixed = apply_fixes(loom)
    report = loom.lint_structural() if structural else None
    cands = loom.lint_candidates() if candidates_ else None
    if ctx.obj.get("json"):
        payload: dict = {}
        if fix:
            payload["fixed"] = fixed
        if report is not None:
            payload["report"] = report.model_dump()
        if cands is not None:
            payload["candidates"] = [c.model_dump() for c in cands]
        click.echo(json.dumps(payload, ensure_ascii=False))
    else:
        for desc in fixed:
            click.echo(f"fixed: {desc}")
        if report is not None:
            if report.ok:
                click.echo("structural lint: ok ✅")
            else:
                for f in report.findings:
                    click.echo(f"  [{f.kind}] {f.page} — {f.message}")
        if cands is not None:
            if not cands:
                click.echo("candidates: none")
            else:
                for c in cands:
                    click.echo(f"  [{c.kind}] {', '.join(c.pages)} — {c.reason}")


@cli.group()
def review():
    """高风险改动的人审队列：list / show / apply / reject。"""


@review.command(name="list")
@click.pass_context
def review_list(ctx: click.Context):
    """列出待审项。"""
    items = _get_loom(ctx).list_reviews()
    if ctx.obj.get("json"):
        click.echo(json.dumps([it.model_dump() for it in items], ensure_ascii=False))
    else:
        for it in items:
            click.echo(f"{it.id}\t{it.name}\tstaged {it.staged_at}")


@review.command(name="show")
@click.argument("rid")
@click.pass_context
def review_show(ctx: click.Context, rid: str):
    """打印某待审项的 diff（--json 输出完整项）。"""
    item = _get_loom(ctx).get_review(rid)
    if ctx.obj.get("json"):
        click.echo(json.dumps(item.model_dump(), ensure_ascii=False))
    else:
        click.echo(item.diff)


@review.command(name="apply")
@click.argument("rid")
@click.pass_context
def review_apply(ctx: click.Context, rid: str):
    """落盘某待审项（走完整校验 + OCC）。"""
    _emit_write_result(ctx, _get_loom(ctx).apply_review(rid))


@review.command(name="reject")
@click.argument("rid")
@click.pass_context
def review_reject(ctx: click.Context, rid: str):
    """丢弃某待审项，页面不变。"""
    _get_loom(ctx).reject_review(rid)
    if ctx.obj.get("json"):
        click.echo(json.dumps({"ok": True, "rejected": rid}, ensure_ascii=False))
    else:
        click.echo(f"rejected {rid}")


def _build_provider():
    """按环境变量构造 LLMProvider；缺 [auto] extra 时抛带安装提示的 LoomError。

    LOOM_AUTO_PROVIDER=anthropic|openai（默认 anthropic）、LOOM_AUTO_MODEL、LOOM_AUTO_BASE_URL。
    """
    import os

    from loom.auto.providers import AnthropicProvider, OpenAICompatProvider

    kind = os.environ.get("LOOM_AUTO_PROVIDER", "anthropic").lower()
    model = os.environ.get("LOOM_AUTO_MODEL")
    if kind == "openai":
        return OpenAICompatProvider(
            model=model or "gpt-4o-mini", base_url=os.environ.get("LOOM_AUTO_BASE_URL")
        )
    return AnthropicProvider(model=model or "claude-opus-4-8")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--auto", is_flag=True, help="用内置 LLMProvider 跑完整编排（无 agent 便利出口）")
@click.pass_context
def ingest(ctx: click.Context, path: str, auto: bool):
    """[auto] 一条命令跑完整 ingest（register→parse→抽取→消解→write→purpose）。"""
    if not auto:
        raise ValidationFailed(
            "loom 默认由宿主 agent 编排；无 agent 时用 `loom ingest --auto <PATH>`"
            "（需 pip install 'loom-wiki[auto]'）"
        )
    from loom.auto.orchestrator import auto_ingest

    report = auto_ingest(_get_loom(ctx), path, _build_provider())
    if ctx.obj.get("json"):
        click.echo(json.dumps(report.model_dump(), ensure_ascii=False))
    else:
        click.echo(f"ingested {len(report.pages_written)} 页：{', '.join(report.pages_written)}")
        if report.purpose_updated:
            click.echo("purpose.md 已更新")


@cli.command()
@click.argument("question")
@click.option("--auto", is_flag=True, help="用内置 LLMProvider 综合作答（无 agent 便利出口）")
@click.pass_context
def query(ctx: click.Context, question: str, auto: bool):
    """[auto] 一条命令回答问题（search→read→综合）。"""
    if not auto:
        raise ValidationFailed(
            "无 agent 时用 `loom query --auto \"<问题>\"`（需 pip install 'loom-wiki[auto]'）"
        )
    from loom.auto.orchestrator import auto_query

    click.echo(auto_query(_get_loom(ctx), question, _build_provider()))


@cli.command()
@click.option(
    "--wiki-path", "wiki_path_opt", default=None, help="wiki 根目录（也可用全局 --wiki-path）"
)
@click.pass_context
def mcp(ctx: click.Context, wiki_path_opt: str | None):
    """以 stdio 运行 MCP server（常驻进程；暖索引、文件锁的天然串行化点）。"""
    from loom.transport.mcp import build_server  # 惰性导入：非 mcp 命令无需加载 MCP SDK

    wiki_path = wiki_path_opt or ctx.obj.get("wiki_path")
    root = Path(wiki_path) if wiki_path else find_wiki_root(Path.cwd())
    build_server(root).run(transport="stdio")
