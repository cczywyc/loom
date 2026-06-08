import pytest

from loom.errors import ValidationFailed
from loom.parsers import parse_file


def test_parse_markdown_extracts_text_and_meta(tmp_path):
    f = tmp_path / "note.md"
    f.write_text("---\ntitle: 笔记\n---\n\n# 标题\n\n正文内容。")
    doc = parse_file(f, assets_dir=tmp_path / "assets")
    assert "正文内容" in doc.text
    assert doc.metadata.get("title") == "笔记"


def test_parse_pdf_extracts_text(tmp_path):
    from fpdf import FPDF  # dev 依赖，仅测试用

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.cell(text="Attention is all you need")
    pdf.output(str(tmp_path / "p.pdf"))
    doc = parse_file(tmp_path / "p.pdf", assets_dir=tmp_path / "assets")
    assert "Attention" in doc.text
    assert doc.metadata["pages"] == 1


def test_unsupported_extension_raises(tmp_path):
    f = tmp_path / "x.xyz"
    f.write_text("?")
    with pytest.raises(ValidationFailed):
        parse_file(f, assets_dir=tmp_path / "assets")
