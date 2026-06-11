from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from loom.core.fsutil import sha256_file
from loom.core.graph import GraphIndex
from loom.core.store import WikiStore
from loom.errors import ValidationFailed
from loom.models import Finding, LintReport, WikiPage, loads_page
from loom.security.citations import extract_citations
from loom.validate import is_kebab


def _source_matches(citation_source: str, rel: str) -> bool:
    """行内引用的来源（文件名）是否对应某个页面 source（相对路径，按 basename/后缀匹配）。"""
    return rel.split("/")[-1] == citation_source or rel.endswith(citation_source)


@dataclass
class WikiSnapshot:
    """一次性收集 lint 所需的全部事实：解析成功/失败的页、所有文件名、图谱。"""

    root: Path
    valid_pages: list[WikiPage]
    bad_frontmatter: list[tuple[str, str]]  # (name, 错误信息)
    stems: list[str]  # 所有页面文件名（不含 .md），含解析失败者
    graph: GraphIndex

    @classmethod
    def collect(cls, store: WikiStore) -> "WikiSnapshot":
        valid: list[WikiPage] = []
        bad_fm: list[tuple[str, str]] = []
        stems: list[str] = []
        for path in store._iter_page_paths():
            stem = path.stem
            stems.append(stem)
            try:
                valid.append(loads_page(stem, path.read_text(encoding="utf-8")))
            except ValidationFailed as e:
                bad_fm.append((stem, str(e)))  # lint 永不抛错，把解析失败转成 Finding
        return cls(
            root=store.paths.root,
            valid_pages=valid,
            bad_frontmatter=bad_fm,
            stems=stems,
            graph=GraphIndex.from_pages(valid),
        )


def _orphans(s: WikiSnapshot) -> list[Finding]:
    return [
        Finding(kind="orphan", page=n, message="孤儿页：无入边也无出边，考虑建立链接")
        for n in s.graph.orphans()
    ]


def _broken_links(s: WikiSnapshot) -> list[Finding]:
    return [
        Finding(kind="broken-link", page=src, message=f"指向不存在的页 [[{tgt}]]")
        for src, tgt in s.graph.broken_links()
    ]


def _bad_frontmatter(s: WikiSnapshot) -> list[Finding]:
    return [
        Finding(kind="bad-frontmatter", page=name, message=msg) for name, msg in s.bad_frontmatter
    ]


def _bad_names(s: WikiSnapshot) -> list[Finding]:
    return [
        Finding(kind="bad-name", page=stem, message=f"文件名 '{stem}' 不是 kebab-case ASCII")
        for stem in s.stems
        if not is_kebab(stem)
    ]


def _stale(s: WikiSnapshot) -> list[Finding]:
    out: list[Finding] = []
    for page in s.valid_pages:
        cites = extract_citations(page.body)
        lines = page.body.split("\n")
        for rel, recorded in page.meta.source_hashes.items():
            f = s.root / rel
            if f.exists() and sha256_file(f) != recorded:
                msg = f"来源 {rel} 已变更，页面可能过期"
                # 论断级溯源：若有行内引用指向该来源，精确点名受影响论断行
                claims = [
                    lines[c.line - 1].strip() for c in cites if _source_matches(c.source, rel)
                ]
                if claims:
                    msg += "；受影响论断：" + " / ".join(claims)
                out.append(Finding(kind="stale", page=page.name, message=msg))
                break
    return out


def _citations(s: WikiSnapshot) -> list[Finding]:
    """行内引用 ^[src:…] 指向的来源必须在页面 sources 中，否则报 broken-link（注明 citation）。"""
    out: list[Finding] = []
    for page in s.valid_pages:
        for c in extract_citations(page.body):
            if not any(_source_matches(c.source, src) for src in page.meta.sources):
                out.append(
                    Finding(
                        kind="broken-link",
                        page=page.name,
                        message=f"行内引用 ^[src:{c.source}]（第 {c.line} 行）的来源不在页面 sources 中",
                    )
                )
    return out


def _duplicate_titles(s: WikiSnapshot) -> list[Finding]:
    by_title: dict[str, list[str]] = {}
    for page in s.valid_pages:
        by_title.setdefault(page.meta.title, []).append(page.name)
    out: list[Finding] = []
    for title, names in by_title.items():
        if len(names) > 1:
            others = ", ".join(names)
            out.extend(
                Finding(
                    kind="duplicate-title", page=n, message=f"标题「{title}」在多页重复：{others}"
                )
                for n in names
            )
    return out


_CHECKERS: list[Callable[[WikiSnapshot], list[Finding]]] = [
    _orphans,
    _broken_links,
    _bad_frontmatter,
    _bad_names,
    _stale,
    _duplicate_titles,
    _citations,
]


def lint_structural(store: WikiStore) -> LintReport:
    """跑全部六个机械检查器，聚合成 LintReport。永不抛错，只报告。"""
    snapshot = WikiSnapshot.collect(store)
    findings: list[Finding] = []
    for check in _CHECKERS:
        findings.extend(check(snapshot))
    return LintReport(findings=findings)
