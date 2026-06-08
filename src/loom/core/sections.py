import re
from dataclasses import dataclass

from loom.errors import NotFound
from loom.models import Patch

HEADING_RE = re.compile(r"^(#{2,6})\s+(.*?)\s*$")


@dataclass
class Section:
    level: int
    title: str
    start: int  # 标题行下标
    end: int  # 区段结束（下一个同级或更高级标题的下标；无则到文末）


def list_sections(body: str) -> list[Section]:
    """返回 body 内全部 ## ~ ###### 标题（含子节），按出现顺序。"""
    lines = body.split("\n")
    heads: list[tuple[int, int, str]] = []
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
    sections: list[Section] = []
    for idx, (start, level, title) in enumerate(heads):
        end = len(lines)
        for nxt_start, nxt_level, _ in heads[idx + 1 :]:
            if nxt_level <= level:  # 子节随父节走：只在遇到同级/更高级标题时收尾
                end = nxt_start
                break
        sections.append(Section(level=level, title=title, start=start, end=end))
    return sections


def apply_patch(body: str, patch: Patch) -> str:
    """对 body 做段级补丁，返回新 body。set_frontmatter 不在此处理（由 store 层做）。"""
    if patch.op == "add_section":
        return f"{body.rstrip()}\n\n## {patch.section}\n\n{patch.content}"

    sections = list_sections(body)
    target = next((s for s in sections if s.title == patch.section), None)
    if target is None:
        available = ", ".join(s.title for s in sections)
        raise NotFound(f"section '{patch.section}' not found; available: {available}")

    lines = body.split("\n")
    if patch.op == "replace":
        # 保留标题行，替换其下全部内容（含子节）
        new_lines = lines[: target.start + 1] + ["", patch.content, ""] + lines[target.end :]
    elif patch.op == "append":
        # 追加到本节内容末尾（子节之后）
        new_lines = lines[: target.end] + ["", patch.content, ""] + lines[target.end :]
    else:
        raise ValueError(f"unsupported patch op for body: {patch.op}")
    return "\n".join(new_lines).strip("\n")
