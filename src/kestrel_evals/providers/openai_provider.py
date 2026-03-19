from __future__ import annotations

from typing import Optional

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self):
        try:
            from openai import AsyncOpenAI  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "OpenAI dependency not installed. Install with: pip install 'kestrel-evals[openai]'"
            ) from e

        self._client = AsyncOpenAI()

    async def generate(self, *, model: str, system: Optional[str], user: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        resp = await self._client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return resp.choices[0].message.content or ""
