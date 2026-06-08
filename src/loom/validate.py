import re

from loom.models import WikiPage

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# [[target]] / [[target|alias]] / [[target#anchor]] / [[target#anchor|alias]]
WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]")


def is_kebab(name: str) -> bool:
    return bool(KEBAB_RE.fullmatch(name))


def extract_wikilinks(body: str) -> list[str]:
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(body)]


def validate_page(page: WikiPage, known_names: set[str]) -> tuple[list[str], list[str]]:
    """返回 (硬错误 problems, 软告警 warnings)。problems 非空 → write_page 拒绝。"""
    problems: list[str] = []
    warnings: list[str] = []
    if not is_kebab(page.name):
        problems.append(f"name '{page.name}' is not kebab-case")
    if not page.meta.title.strip():
        problems.append("title must be non-empty")
    for link in extract_wikilinks(page.body):
        if link != page.name and link not in known_names:
            warnings.append(f"dangling wikilink: [[{link}]] (target not found; lint will track it)")
    return problems, warnings
