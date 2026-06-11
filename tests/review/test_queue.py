import pytest

from loom.errors import Conflict
from tests.conftest import page_md


def test_review_stages_instead_of_writing(loom, wiki_root):
    loom.write_page("a", page_md(type="concept", title="A", body="原文"))
    h = loom.read_page("a").content_hash
    rid = loom.stage_review("a", page_md(type="concept", title="A", body="重写全文"), base_hash=h)
    assert "原文" in loom.read_page("a").body  # 尚未生效
    items = loom.list_reviews()
    assert items[0].id == rid and "-原文" in items[0].diff and "+重写全文" in items[0].diff


def test_apply_review_writes_with_occ(loom, wiki_root):
    loom.write_page("a", page_md(type="concept", title="A", body="原文"))
    h = loom.read_page("a").content_hash
    rid = loom.stage_review("a", page_md(type="concept", title="A", body="新文"), base_hash=h)
    res = loom.apply_review(rid)
    assert res.ok and loom.read_page("a").body.strip() == "新文"  # 生效
    assert "| REVIEW | a | applied" in (wiki_root / "wiki/log.md").read_text()
    assert loom.list_reviews() == []  # 已出队


def test_apply_review_conflicts_if_disk_moved(loom):
    loom.write_page("a", page_md(type="concept", title="A", body="原文"))
    h = loom.read_page("a").content_hash
    rid = loom.stage_review("a", page_md(type="concept", title="A", body="审核版"), base_hash=h)
    loom.write_page("a", page_md(type="concept", title="A", body="他人改"), base_hash=h)  # 磁盘前移
    with pytest.raises(Conflict):
        loom.apply_review(rid)  # base_hash 已失效


def test_reject_review_discards(loom):
    loom.write_page("a", page_md(type="concept", title="A", body="原文"))
    h = loom.read_page("a").content_hash
    rid = loom.stage_review("a", page_md(type="concept", title="A", body="不要的改动"), base_hash=h)
    loom.reject_review(rid)
    assert loom.list_reviews() == []
    assert loom.read_page("a").body.strip() == "原文"  # 页面未变
