from tests.conftest import page_md


def seed3(loom):
    loom.write_page(
        "langgraph-state",
        page_md(
            type="concept",
            title="LangGraph 状态管理",
            tags=["langgraph"],
            body="LangGraph 用 StateGraph 管理状态，检查点机制支持持久化。",
        ),
    )
    loom.write_page(
        "react-pattern",
        page_md(type="concept", title="ReAct 模式", body="推理与行动交替进行。"),
    )
    loom.write_page(
        "karpathy",
        page_md(type="entity", title="Andrej Karpathy", body="提出 LLM Wiki。"),
    )


def test_chinese_query_ranks_relevant_first(loom):
    seed3(loom)
    hits = loom.search("LangGraph 状态管理")
    assert hits[0].name == "langgraph-state"
    assert hits[0].snippet  # 命中片段非空


def test_title_match_beats_body_mention(loom):
    seed3(loom)
    # react-pattern 是标题命中（×3 加权），mentions-react 只是 body 顺带一提，前者须排前
    loom.write_page(
        "mentions-react",
        page_md(type="entity", title="某人", body="此人也讨论过 ReAct，但只是顺带一提。"),
    )
    hits = loom.search("ReAct 模式")
    assert hits[0].name == "react-pattern"


def test_index_invalidated_after_write(loom):
    seed3(loom)
    assert all(h.name != "new-topic" for h in loom.search("全新主题"))
    loom.write_page("new-topic", page_md(type="concept", title="全新主题", body="刚刚写入。"))
    assert any(h.name == "new-topic" for h in loom.search("全新主题"))


def test_no_hits_returns_empty_not_error(loom):
    assert loom.search("绝不存在的词汇组合 xyzzy") == []
