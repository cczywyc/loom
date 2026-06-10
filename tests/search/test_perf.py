import time

from tests.conftest import page_md


def test_warm_search_under_200ms_on_200_pages(loom):
    for i in range(200):
        loom.write_page(
            f"page-{i}",
            page_md(
                type="concept",
                title=f"主题{i}",
                body=f"这是第 {i} 页，讨论分布式系统与一致性协议的第 {i} 种变体。",
            ),
        )
    loom.search("一致性")  # 首次：触发建索引（不计时）
    t0 = time.perf_counter()
    loom.search("分布式系统")
    assert time.perf_counter() - t0 < 0.2
