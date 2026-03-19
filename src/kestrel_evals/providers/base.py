from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    """Provider abstraction.

    Phase 1: OpenAI.
    Phase 2: add other providers without rewriting eval logic.
    """

    @abstractmethod
    async def generate(self, *, model: str, system: Optional[str], user: str) -> str:
        raise NotImplementedError
