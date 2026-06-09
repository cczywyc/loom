from tests.conftest import page_md


def test_find_related_surfaces_candidate_with_reason(loom):
    loom.write_page(
        "react-pattern",
        page_md(type="concept", title="ReAct 模式", body="推理与行动交替。"),
    )
    loom.write_page(
        "plan-and-execute",
        page_md(
            type="concept", title="Plan-and-Execute", body="先规划后执行，对比 [[react-pattern]]。"
        ),
    )
    refs = loom.find_related("ReAct 推理模式的一个变体")
    assert refs[0].name == "react-pattern"
    assert refs[0].reason  # 形如 "keyword match: react/推理"
    assert 0 < refs[0].score


def test_find_related_boosts_graph_neighbors(loom):
    # 命中页的图邻居以低分跟随出现（reason="linked from <hit>"）
    loom.write_page(
        "react-pattern", page_md(type="concept", title="ReAct 模式", body="推理与行动。")
    )
    loom.write_page("acting", page_md(type="concept", title="行动", body="见 [[react-pattern]]"))
    names = [r.name for r in loom.find_related("ReAct", limit=5)]
    assert "react-pattern" in names and "acting" in names


def test_find_related_empty_wiki_returns_empty(loom):
    assert loom.find_related("任何文本") == []
