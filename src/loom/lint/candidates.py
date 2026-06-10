from itertools import combinations

from loom.core.fsutil import sha256_file
from loom.core.store import WikiStore
from loom.lint.structural import WikiSnapshot
from loom.models import Candidate


def lint_candidates(store: WikiStore) -> list[Candidate]:
    """三类纯结构启发式，浮现值得 agent 看的对象。确定性、可解释、固定排序。"""
    snap = WikiSnapshot.collect(store)
    cands: list[Candidate] = []
    cands += _contradictions(snap)
    cands += _sparse_areas(snap)
    cands += _stale_clusters(snap)
    cands.sort(key=lambda c: (c.kind, tuple(c.pages)))  # 固定排序：同库多次调用结果一致
    return cands


def _contradictions(snap: WikiSnapshot) -> list[Candidate]:
    """共享 ≥2 个出链目标、但彼此无链接的页对：关注同批事物却互不相认。"""
    out = snap.graph._out
    names = sorted(snap.graph._pages)
    cands: list[Candidate] = []
    for p, q in combinations(names, 2):
        shared = out.get(p, set()) & out.get(q, set())
        if len(shared) >= 2 and q not in out.get(p, set()) and p not in out.get(q, set()):
            tgts = ", ".join(sorted(shared))
            cands.append(
                Candidate(
                    kind="possible-contradiction",
                    pages=[p, q],
                    reason=f"两页共享出链 [{tgts}] 却互不链接（share ≥2 targets but don't link each other）",
                )
            )
    return cands


def _sparse_areas(snap: WikiSnapshot) -> list[Candidate]:
    """某类型目录下入度+出度 ≤1 的页占比 >50%：这片知识没织进网。"""
    out, inc = snap.graph._out, snap.graph._inc
    by_type: dict[str, list[str]] = {}
    for page in snap.valid_pages:
        by_type.setdefault(page.meta.type, []).append(page.name)
    cands: list[Candidate] = []
    for typ, names in by_type.items():
        low = [n for n in names if len(out.get(n, set())) + len(inc.get(n, set())) <= 1]
        if names and len(low) / len(names) > 0.5:
            cands.append(
                Candidate(
                    kind="sparse-area",
                    pages=sorted(low),
                    reason=f"类型 '{typ}' 下 {len(low)}/{len(names)} 页入度+出度≤1，这片知识没织进网",
                )
            )
    return cands


def _stale_clusters(snap: WikiSnapshot) -> list[Candidate]:
    """stale 页及其 depth-1 邻居打包：过期可能沿链扩散。"""
    cands: list[Candidate] = []
    for page in snap.valid_pages:
        is_stale = any(
            (snap.root / rel).exists() and sha256_file(snap.root / rel) != recorded
            for rel, recorded in page.meta.source_hashes.items()
        )
        if not is_stale:
            continue
        cluster = snap.graph.subgraph(page.name, depth=1)
        cands.append(
            Candidate(
                kind="stale-cluster",
                pages=sorted(n.name for n in cluster.nodes),
                reason=f"页 '{page.name}' 因来源变更过期，其 depth-1 邻域可能受影响",
            )
        )
    return cands
