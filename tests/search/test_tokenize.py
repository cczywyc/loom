from loom.search.tokenize import tokenize


def test_chinese_segmentation():
    toks = tokenize("状态管理是 LangGraph 的核心")
    assert "状态" in toks or "状态管理" in toks  # jieba 切分粒度允许二选一
    assert "langgraph" in toks  # 英文统一小写


def test_mixed_and_punct_filtered():
    toks = tokenize("ReAct（推理+行动）模式！")
    assert "react" in toks and "推理" in toks
    assert all(t not in toks for t in ["（", "+", "！"])


def test_deterministic():
    text = "LLM Wiki 把知识编译一次"
    assert tokenize(text) == tokenize(text)
