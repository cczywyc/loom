from loom.core.log import LogWriter


def test_append_format_is_greppable(tmp_path, monkeypatch):
    monkeypatch.setattr("loom.clock.now_iso", lambda: "2026-06-05T10:00:00Z")
    log = LogWriter(tmp_path / "log.md")
    log.append("WRITE", "llm-wiki", "created")
    log.append("UPDATE", "llm-wiki", "section=争议")
    lines = (tmp_path / "log.md").read_text().splitlines()
    assert lines[-2] == "- 2026-06-05T10:00:00Z | WRITE | llm-wiki | created"
    assert lines[-1] == "- 2026-06-05T10:00:00Z | UPDATE | llm-wiki | section=争议"


def test_append_creates_file_with_header(tmp_path):
    log = LogWriter(tmp_path / "log.md")
    log.append("INIT", "-", "wiki created")
    assert (tmp_path / "log.md").read_text().startswith("# Log\n")
