from loom.parsers import parse_file


def test_parse_html_strips_boilerplate(tmp_path):
    f = tmp_path / "a.html"
    f.write_text(
        """<html><head><title>LLM Wiki 解读</title><script>evil()</script>
      <style>.x{}</style></head><body><nav>导航</nav>
      <article><h1>正文标题</h1><p>Karpathy 提出了持久 wiki。</p></article>
      <footer>页脚</footer></body></html>"""
    )
    doc = parse_file(f, assets_dir=tmp_path / "assets")
    assert "Karpathy 提出了持久 wiki" in doc.text
    assert "evil()" not in doc.text and ".x{}" not in doc.text
    assert doc.metadata["title"] == "LLM Wiki 解读"
