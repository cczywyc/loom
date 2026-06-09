import re

import jieba

_WORD = re.compile(r"^[a-z0-9]+$")
_HAS_CJK = re.compile(r"[一-鿿]")


def tokenize(text: str) -> list[str]:
    """中英混排分词：jieba 切中文，英文/数字统一小写，丢弃标点。

    jieba 首次加载词典约 0.5–1s（模块级懒加载）：CLI 冷启动可接受，MCP 常驻进程摊销。
    """
    out: list[str] = []
    for tok in jieba.cut_for_search(text.lower()):
        tok = tok.strip()
        if not tok:
            continue
        if _WORD.fullmatch(tok) or _HAS_CJK.search(tok):
            out.append(tok)
    return out
