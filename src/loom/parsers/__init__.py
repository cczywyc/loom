from pathlib import Path

from loom.core.fsutil import sha256_file
from loom.errors import ValidationFailed
from loom.models import ParsedDocument
from loom.parsers.docx import parse_docx
from loom.parsers.html import parse_html
from loom.parsers.markdown import parse_markdown
from loom.parsers.pdf import parse_pdf
from loom.security.untrusted import wrap_untrusted

PARSERS = {
    ".md": parse_markdown,
    ".markdown": parse_markdown,
    ".pdf": parse_pdf,
    ".html": parse_html,
    ".htm": parse_html,
    ".docx": parse_docx,
}


def parse_file(path: Path, assets_dir: Path, wrap: bool = True) -> ParsedDocument:
    """按扩展名分发到对应解析器；未知扩展名抛 ValidationFailed。

    wrap=True（默认）把产出文本包成「不可信资料」块（prompt-injection 防御纵深，见
    loom.security.untrusted）。需要裸文本时（如再加工）传 wrap=False。
    """
    path = Path(path)
    parser = PARSERS.get(path.suffix.lower())
    if parser is None:
        supported = ", ".join(sorted(PARSERS))
        raise ValidationFailed(f"unsupported file type '{path.suffix}'; supported: {supported}")
    doc = parser(path, assets_dir)
    if wrap:
        wrapped = wrap_untrusted(doc.text, source=doc.source_path, sha=sha256_file(path))
        doc = doc.model_copy(update={"text": wrapped})
    return doc
