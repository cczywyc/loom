from pathlib import Path

import yaml

from loom.models import ParsedDocument


def parse_markdown(path: Path, assets_dir: Path) -> ParsedDocument:
    """读取 markdown 源：有 frontmatter 则抽成 metadata，正文作为 text。"""
    text = path.read_text(encoding="utf-8")
    metadata: dict = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                loaded = yaml.safe_load(parts[1])
            except yaml.YAMLError:
                loaded = None
            if isinstance(loaded, dict):
                metadata = loaded
                body = parts[2].lstrip("\n")
    return ParsedDocument(source_path=str(path), text=body, metadata=metadata, assets=[])
