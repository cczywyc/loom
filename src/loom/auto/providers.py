from typing import Protocol, runtime_checkable

from loom.errors import LoomError

_EXTRA_HINT = "需要可选依赖：pip install 'loom-wiki[auto]'"


@runtime_checkable
class LLMProvider(Protocol):
    """编排器对大脑的唯一要求：给 system+user，返回字符串。core 不依赖任何具体实现。"""

    def complete(self, system: str, user: str) -> str: ...


class AnthropicProvider:
    """Claude。anthropic 包惰性 import；缺包时报装 extra（core 零依赖于它）。"""

    def __init__(self, model: str = "claude-opus-4-8", api_key: str | None = None):
        try:
            import anthropic
        except ImportError as e:
            raise LoomError(f"anthropic 未安装；{_EXTRA_HINT}") from e
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, system: str, user: str) -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


class OpenAICompatProvider:
    """OpenAI 兼容端点；base_url 可指 Ollama / vLLM / 任意兼容服务。"""

    def __init__(self, model: str, base_url: str | None = None, api_key: str | None = None):
        try:
            import openai
        except ImportError as e:
            raise LoomError(f"openai 未安装；{_EXTRA_HINT}") from e
        self._client = openai.OpenAI(base_url=base_url, api_key=api_key or "not-needed")
        self._model = model

    def complete(self, system: str, user: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""
