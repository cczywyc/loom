import importlib.resources
import json
from pathlib import Path

from loom.errors import Conflict, ValidationFailed
from loom.models import TYPE_DIRS

TEMPLATES = ("blank", "research", "personal")
_OBSIDIAN_APP = {"useMarkdownLinks": False, "newLinkFormat": "shortest"}


def _template_text(template: str, filename: str) -> str:
    """读取打包在 loom/templates/<template>/ 下的契约文档（editable 与 wheel 均可用）。"""
    return (
        importlib.resources.files("loom")
        .joinpath("templates", template, filename)
        .read_text(encoding="utf-8")
    )


def init_wiki(root: Path, template: str = "blank") -> Path:
    """生成一座符合架构 §十一 的完整 wiki 目录；模板未知抛 ValidationFailed，目标非空抛 Conflict。"""
    if template not in TEMPLATES:
        raise ValidationFailed(f"unknown template '{template}'; choose from {', '.join(TEMPLATES)}")
    root = Path(root)
    if root.exists() and any(root.iterdir()):
        raise Conflict(f"target directory '{root}' exists and is not empty")

    (root / "raw" / "sources").mkdir(parents=True, exist_ok=True)
    (root / "raw" / "assets").mkdir(parents=True, exist_ok=True)
    (root / ".loom").mkdir(parents=True, exist_ok=True)
    (root / ".obsidian").mkdir(parents=True, exist_ok=True)

    wiki = root / "wiki"
    for dir_name in TYPE_DIRS.values():
        (wiki / dir_name).mkdir(parents=True, exist_ok=True)

    sections = "\n\n".join(f"## {dir_name}" for dir_name in TYPE_DIRS.values())
    (wiki / "index.md").write_text(f"# Index\n\n{sections}\n", encoding="utf-8")
    (wiki / "log.md").write_text("# Log\n", encoding="utf-8")

    (root / "schema.md").write_text(_template_text(template, "schema.md"), encoding="utf-8")
    (root / "purpose.md").write_text(_template_text(template, "purpose.md"), encoding="utf-8")
    (root / ".obsidian" / "app.json").write_text(
        json.dumps(_OBSIDIAN_APP, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return root
