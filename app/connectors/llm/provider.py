from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod

from app.core.exceptions import ValidationError


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
    provider = provider_name.strip().lower() or "mock"
    if provider in {"mock", "rule-based"}:
        return MockLLMProvider(provider_name=provider, model_name=model_name)
    if provider in {"openai", "openai-compatible", "openai_compatible"}:
        return OpenAICompatibleLLMProvider(provider_name=provider, model_name=model_name)
    raise ValidationError(f"Unsupported AI provider: {provider_name}")


class OpenAICompatibleLLMProvider(LLMProvider):
    def __init__(self, provider_name: str, model_name: str) -> None:
        super().__init__(provider_name=provider_name, model_name=model_name)
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.timeout_seconds = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))

    def _build_request(self, input_text: str, context: dict[str, object]) -> urllib.request.Request:
        if not self.api_key:
            raise ValidationError("OPENAI_API_KEY is required for openai provider")

        payload = json.dumps(
            {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a QA analysis assistant that returns concise JSON-ready insights.",
                    },
                    {
                        "role": "user",
                        "content": json.dumps({"input_text": input_text, "context": context}, ensure_ascii=False),
                    },
                ],
                "temperature": 0.2,
            }
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        return urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers=headers,
            method="POST",
        )

    @staticmethod
    def _extract_content(response_json: dict[str, object]) -> str:
        choices = response_json.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            return ""
        message = first_choice.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content
        text = first_choice.get("text")
        return text if isinstance(text, str) else ""

    def analyze(self, input_text: str, context: dict[str, object]) -> dict[str, object]:
        request = self._build_request(input_text, context)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # pragma: no cover - network errors are integration handled
            body = exc.read().decode("utf-8", errors="ignore")
            raise ValidationError(f"AI provider request failed: {exc.code} {body or exc.reason}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network errors are integration handled
            raise ValidationError(f"AI provider request failed: {exc.reason}") from exc

        content = self._extract_content(payload)
        if not content:
            raise ValidationError("AI provider response did not include content")

        summary = content.strip()
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "confidence": 0.9,
            "summary": summary,
            "suggestions": [summary] if summary else [],
            "context": context,
        }
