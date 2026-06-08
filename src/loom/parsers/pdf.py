from pathlib import Path

import pdfplumber

from loom.models import ParsedDocument


def parse_pdf(path: Path, assets_dir: Path) -> ParsedDocument:
    """pdfplumber 逐页抽取文本（页间空行分隔），metadata 记录页数与原始 PDF 元数据。"""
    texts: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        pages = len(pdf.pages)
        for page in pdf.pages:
            texts.append(page.extract_text() or "")
        metadata = {"pages": pages, **(pdf.metadata or {})}
    # 图片提取暂缓：从任意 PDF 图片流稳健重建格式复杂且常失败，且当前无测试覆盖（见计划备注）。
    return ParsedDocument(
        source_path=str(path), text="\n\n".join(texts), metadata=metadata, assets=[]
    )
