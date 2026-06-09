from loom.core.store import WikiStore
from loom.models import Graph, GraphEdge, GraphNode, WikiPage
from loom.validate import extract_wikilinks


class GraphIndex:
    """从 [[wikilink]] 解析出的内存图谱：出边/入边、子图 BFS、孤儿、坏链。"""

    def __init__(
        self,
        pages: dict[str, WikiPage],
        out: dict[str, set[str]],
        inc: dict[str, set[str]],
        broken: list[tuple[str, str]],
    ):
        self._pages = pages
        self._out = out  # name -> 指向的（已存在）页
        self._inc = inc  # name -> 链入它的页
        self._broken = broken  # (src, 不存在的目标)

    @classmethod
    def build(cls, store: WikiStore) -> "GraphIndex":
        pages: dict[str, WikiPage] = {}
        raw: dict[str, list[str]] = {}
        for page in store.iter_pages():
            pages[page.name] = page
            raw[page.name] = extract_wikilinks(page.body)
        out: dict[str, set[str]] = {name: set() for name in pages}
        inc: dict[str, set[str]] = {name: set() for name in pages}
        broken: list[tuple[str, str]] = []
        for name, links in raw.items():
            for tgt in links:
                if tgt == name:
                    continue
                if tgt in pages:
                    out[name].add(tgt)
                    inc[tgt].add(name)
                else:
                    broken.append((name, tgt))
        return cls(pages, out, inc, broken)

    def orphans(self) -> list[str]:
        """无入边且无出边的页面。"""
        return sorted(n for n in self._pages if not self._out[n] and not self._inc[n])

    def broken_links(self) -> list[tuple[str, str]]:
        """指向不存在页面的链接 (src, 缺失目标)。"""
        return sorted(self._broken)

    def subgraph(self, name: str, depth: int = 1) -> Graph:
        """从 name 出发沿出边+入边做 BFS，返回 depth 层邻域子图。"""
        visited = {name}
        frontier = {name}
        for _ in range(depth):
            nxt: set[str] = set()
            for n in frontier:
                nxt |= self._out.get(n, set()) | self._inc.get(n, set())
            frontier = nxt - visited
            visited |= frontier
            if not frontier:
                break
        return self._to_graph(visited)

    def full_graph(self) -> Graph:
        return self._to_graph(set(self._pages))

    def _to_graph(self, names: set[str]) -> Graph:
        present = sorted(n for n in names if n in self._pages)
        nodes = [
            GraphNode(name=n, title=self._pages[n].meta.title, type=self._pages[n].meta.type)
            for n in present
        ]
        keep = set(present)
        edges = [
            GraphEdge(src=src, dst=dst)
            for src in present
            for dst in sorted(self._out[src])
            if dst in keep
        ]
        return Graph(nodes=nodes, edges=edges)
