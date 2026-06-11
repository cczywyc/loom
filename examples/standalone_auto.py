"""无 agent 跑 loom 的最小示例：让内置 LLMProvider 临时扮演大脑，做一次 ingest + query。

这是 loom 的「可选边缘」——正常用法是宿主 agent 编排原语；没有 agent 时才走这条便利出口。

前置：
    pip install 'loom-wiki[auto]'
    export ANTHROPIC_API_KEY=sk-...        # 或用 OpenAI 兼容端点（见下）

运行：
    python examples/standalone_auto.py /path/to/article.md "这篇文章讲了什么？"
"""

import sys
from pathlib import Path

from loom.api import Loom
from loom.auto.orchestrator import auto_ingest, auto_query
from loom.auto.providers import AnthropicProvider, OpenAICompatProvider


def make_provider():
    import os

    # OpenAI 兼容端点（含本地 Ollama / vLLM）：设 LOOM_AUTO_BASE_URL 即走这条
    if os.environ.get("LOOM_AUTO_BASE_URL"):
        return OpenAICompatProvider(
            model=os.environ.get("LOOM_AUTO_MODEL", "gpt-4o-mini"),
            base_url=os.environ["LOOM_AUTO_BASE_URL"],
        )
    return AnthropicProvider(model=os.environ.get("LOOM_AUTO_MODEL", "claude-opus-4-8"))


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    question = sys.argv[2] if len(sys.argv) > 2 else "这座库里有什么？"

    wiki = Path("/tmp/loom-auto-demo")
    Loom.init_wiki(wiki, template="research")
    loom = Loom(wiki)
    provider = make_provider()

    if src:
        report = auto_ingest(loom, src, provider)
        print("写入页面：", report.pages_written, "| purpose 更新：", report.purpose_updated)

    print("\n回答：\n", auto_query(loom, question, provider))


if __name__ == "__main__":
    main()
