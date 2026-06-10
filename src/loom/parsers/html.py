from pathlib import Path

from bs4 import BeautifulSoup

from loom.models import ParsedDocument

_BOILERPLATE = ["script", "style", "nav", "footer", "header", "aside"]


def parse_html(path: Path, assets_dir: Path) -> ParsedDocument:
    """剔除脚本/样式/导航等样板，优先取 <article>/<main> 正文；title 取自 <title>。"""
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    title = soup.title.get_text(strip=True) if soup.title else ""
    for tag in soup(_BOILERPLATE):
        tag.decompose()
    main = soup.find("article") or soup.find("main") or soup.body or soup
    text = main.get_text("\n", strip=True)
    metadata = {"title": title} if title else {}
    return ParsedDocument(source_path=str(path), text=text, metadata=metadata, assets=[])
