from pathlib import Path

from loom.errors import ValidationFailed
from loom.models import ParsedDocument
from loom.parsers.html import parse_html
from loom.parsers.markdown import parse_markdown
from loom.parsers.pdf import parse_pdf

PARSERS = {
    ".md": parse_markdown,
    ".markdown": parse_markdown,
    ".pdf": parse_pdf,
    ".html": parse_html,
    ".htm": parse_html,
}


def parse_file(path: Path, assets_dir: Path) -> ParsedDocument:
    """按扩展名分发到对应解析器；未知扩展名抛 ValidationFailed。"""
    path = Path(path)
    parser = PARSERS.get(path.suffix.lower())
    if parser is None:
        supported = ", ".join(sorted(PARSERS))
        raise ValidationFailed(f"unsupported file type '{path.suffix}'; supported: {supported}")
    return parser(path, assets_dir)
