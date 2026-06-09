import json
from pathlib import Path

import click

from loom.api import Loom
from loom.config import find_wiki_root
from loom.errors import Conflict, LoomError, NotFound, ValidationFailed


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
            if ctx.obj and ctx.obj.get("json"):
                payload = {"ok": False, "error": {"code": code, "message": str(e)}}
                click.echo(json.dumps(payload, ensure_ascii=False))
            else:
                click.echo(f"error [{code}]: {e}", err=True)
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
