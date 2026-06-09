from rank_bm25 import BM25Okapi

from loom.core.store import WikiStore
from loom.models import Hit, WikiPage
from loom.search.tokenize import tokenize

# 小语料下 BM25 的 IDF 可能为负/零，会让真实匹配被 score<=0 滤掉、甚至排序反转。
# 把 IDF 钳到这个小正数下限：保留"稀有词权重更高"的相对关系，又保证任何真实匹配恒为正分。
_IDF_FLOOR = 0.01


class KeywordSearch:
    """内存 BM25 检索：字段加权 title×3 / tags×2 / body×1。按需 build，写入后由 Loom 失效。"""

    def __init__(self, store: WikiStore):
        self.store = store
        self._bm25: BM25Okapi | None = None
        self._pages: list[WikiPage] = []

    def build(self) -> None:
        self._pages = []
        corpus: list[list[str]] = []
        for page in self.store.iter_pages():
            tokens = (
                tokenize(page.meta.title) * 3
                + tokenize(" ".join(page.meta.tags)) * 2
                + tokenize(page.body)
            )
            self._pages.append(page)
            corpus.append(tokens)
        self._bm25 = BM25Okapi(corpus) if corpus else None
        if self._bm25 is not None:
            self._bm25.idf = {t: max(idf, _IDF_FLOOR) for t, idf in self._bm25.idf.items()}

    def search(self, query: str, limit: int = 10) -> list[Hit]:
        if self._bm25 is None:
            self.build()
        if self._bm25 is None or not self._pages:
            return []
        q = tokenize(query)
        if not q:
            return []
        scores = self._bm25.get_scores(q)
        ranked = sorted(
            zip(scores, self._pages, strict=True), key=lambda pair: pair[0], reverse=True
        )
        hits: list[Hit] = []
        for score, page in ranked:
            if score <= 0:  # 无任何 query token 命中
                continue
            hits.append(
                Hit(
                    name=page.name,
                    title=page.meta.title,
                    type=page.meta.type,
                    score=float(score),
                    snippet=self._snippet(page.body, q),
                )
            )
            if len(hits) >= limit:
                break
        return hits

    @staticmethod
    def _snippet(body: str, query_tokens: list[str]) -> str:
        """body 中首个含任一 query token 的行（截 120 字符）。"""
        qset = set(query_tokens)
        for line in body.splitlines():
            if set(tokenize(line)) & qset:
                return line.strip()[:120]
        stripped = body.strip()
        return stripped.splitlines()[0][:120] if stripped else ""
