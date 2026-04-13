from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    def __init__(self, provider_name: str, model_name: str) -> None:
        self.provider_name = provider_name.strip() or "mock"
        self.model_name = model_name.strip() or "mock-llm"

    @abstractmethod
    def analyze(self, input_text: str, context: dict[str, object]) -> dict[str, object]:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    def analyze(self, input_text: str, context: dict[str, object]) -> dict[str, object]:
        suggestions = ["check regression scope", "review failure clustering"]
        if context.get("project"):
            suggestions.insert(0, f"inspect project {context['project']}")
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "confidence": 0.75,
            "summary": f"analyzed: {input_text}",
            "suggestions": suggestions,
            "context": context,
        }


def build_llm_provider(provider_name: str, model_name: str) -> LLMProvider:
    return MockLLMProvider(provider_name=provider_name, model_name=model_name)
