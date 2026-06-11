import re
from dataclasses import dataclass

# 行内引用语法：^[src:<来源文件>] 或 ^[src:<来源文件>#<定位符>]（如 #p3、#sec2）
CITE_RE = re.compile(r"\^\[src:([^\]#]+)(?:#([^\]]+))?\]")


@dataclass
class Citation:
    source: str  # 引用的来源文件名（与页面 sources 的 basename 对应）
    locator: str | None  # 页内定位符（页码/小节等），可空
    line: int  # 在 body 中的行号（1 基），用于把 staleness 定位到具体论断行


def extract_citations(body: str) -> list[Citation]:
    """从页面正文按出现顺序抽出全部行内引用，带行号。纯机械、确定。"""
    cites: list[Citation] = []
    for i, line in enumerate(body.split("\n"), start=1):
        for m in CITE_RE.finditer(line):
            cites.append(Citation(source=m.group(1), locator=m.group(2), line=i))
    return cites
