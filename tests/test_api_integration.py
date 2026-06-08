from loom.api import Loom
from loom.models import Patch
from tests.conftest import page_md


def test_full_deterministic_ingest_path(tmp_path):
    root = tmp_path / "kb"
    Loom.init_wiki(root, template="blank")
    loom = Loom(root)
    # 1. 注册来源
    src = tmp_path / "article.md"
    src.write_text("---\ntitle: LLM Wiki\n---\n\nKarpathy 提出了 LLM Wiki。")
    ref = loom.register_source(src)
    assert ref.is_new
    # 2. 解析
    doc = loom.parse(ref.path)
    assert "Karpathy" in doc.text
    # 3.（agent 判断后）写两个互链页面
    loom.write_page(
        "andrej-karpathy",
        page_md(
            type="entity",
            title="Andrej Karpathy",
            sources=[ref.path],
            body="提出 [[llm-wiki|LLM Wiki]] 模式。",
        ),
    )
    loom.write_page(
        "llm-wiki",
        page_md(
            type="concept",
            title="LLM Wiki",
            sources=[ref.path],
            body="由 [[andrej-karpathy]] 提出。\n\n## 争议\n\n暂无。",
        ),
    )
    # 4. 段级更新
    loom.update_page("llm-wiki", Patch(op="append", section="争议", content="与 RAG 路线之争 ⚠️"))
    # 5. 记账自动完成
    index = loom.get_index()
    log = (root / "wiki/log.md").read_text()
    assert "[[andrej-karpathy|Andrej Karpathy]]" in index and "[[llm-wiki|LLM Wiki]]" in index
    assert log.count("| WRITE |") == 2 and "| UPDATE | llm-wiki" in log and "| REGISTER |" in log
    # 6. 读回验证
    page = loom.read_page("llm-wiki")
    assert "RAG 路线之争" in page.body and page.meta.sources == [ref.path]
