from loom.core.graph import GraphIndex
from loom.models import PageRef
from loom.search.keyword import KeywordSearch
from loom.search.tokenize import tokenize

_NEIGHBOR_FACTOR = 0.3  # 图邻居以命中页分数的此比例附加


def find_related(
    search: KeywordSearch, graph: GraphIndex, text: str, limit: int = 10
) -> list[PageRef]:
    """ingest 实体消解供给侧：BM25 主候选 + 命中页的 depth-1 图邻居。纯确定性，工具 propose。"""
    hits = search.search(text, limit=limit)
    qtokens = tokenize(text)
    by_name: dict[str, PageRef] = {}

    # 主候选：关键词命中
    for h in hits:
        pool = set(tokenize(h.title)) | set(tokenize(h.snippet))
        matched = "/".join(dict.fromkeys(t for t in qtokens if t in pool))
        by_name[h.name] = PageRef(
            name=h.name,
            title=h.title,
            type=h.type,
            score=h.score,
            reason=f"keyword match: {matched}" if matched else "keyword match",
        )

    # 前 3 个命中各取 depth-1 图邻居，以低分附加；去重保高分
    for h in hits[:3]:
        for node in graph.subgraph(h.name, depth=1).nodes:
            if node.name == h.name:
                continue
            nscore = h.score * _NEIGHBOR_FACTOR
            existing = by_name.get(node.name)
            if existing is None or existing.score < nscore:
                by_name[node.name] = PageRef(
                    name=node.name,
                    title=node.title,
                    type=node.type,
                    score=nscore,
                    reason=f"linked from {h.name}",
                )

    return sorted(by_name.values(), key=lambda r: r.score, reverse=True)[:limit]
