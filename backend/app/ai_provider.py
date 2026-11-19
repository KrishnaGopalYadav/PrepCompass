"""Free-inference AI provider adapter for PrepCompass.

Supported providers:
- Gemini Developer API (free tier where available)
- GroqCloud (free tier where available)
- Ollama local runtime (no hosted API billing)

No OpenAI endpoint or paid-provider fallback is configured or called.
"""
import json
import os
from typing import Any
from urllib.parse import quote

import httpx


CAPABILITIES = [
    "study_diagnostics",
    "mock_question_drafting",
    "answer_feedback",
    "weekly_magazine_drafting",
]


class AIProviderNotConfigured(RuntimeError):
    """No configured free inference provider is available."""


class AIProviderError(RuntimeError):
    """All configured free inference providers failed."""


def _setting(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _provider_config(provider: str) -> tuple[str, str, str] | None:
    if provider == "gemini":
        key, model = _setting("GEMINI_API_KEY"), _setting("GEMINI_MODEL")
        return (key, model, "https://generativelanguage.googleapis.com/v1beta") if key and model else None
    if provider == "groq":
        key, model = _setting("GROQ_API_KEY"), _setting("GROQ_MODEL")
        return (key, model, "https://api.groq.com/openai/v1") if key and model else None
    if provider == "ollama":
        model = _setting("OLLAMA_MODEL")
        base_url = _setting("OLLAMA_BASE_URL", "http://host.docker.internal:11434/v1").rstrip("/")
        return ("ollama", model, base_url) if model and base_url else None
    return None


def _provider_order() -> list[str]:
    primary = _setting("AI_PROVIDER", "gemini").lower()
    fallbacks = [item.strip().lower() for item in _setting("AI_FALLBACK_PROVIDERS", "groq,ollama").split(",")]
    return list(dict.fromkeys([primary, *fallbacks]))


def provider_status() -> dict[str, Any]:
    providers = []
    for name in _provider_order():
        config = _provider_config(name)
        providers.append({
            "provider": name,
            "configured": config is not None,
            "model": config[1] if config else None,
            "mode": "local" if name == "ollama" else "hosted_free_tier",
        })
    ready = next((item for item in providers if item["configured"]), None)
    return {
        "provider": ready["provider"] if ready else _setting("AI_PROVIDER", "gemini").lower(),
        "configured": ready is not None,
        "model": ready["model"] if ready else None,
        "providers": providers,
        "paid_fallback_enabled": False,
        "capabilities": CAPABILITIES,
    }


def _parse_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[:-3].strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Model output must be a JSON object.")
    return parsed


async def _post_json(url: str, *, headers: dict[str, str], payload: dict[str, Any], params: dict[str, str] | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, params=params, json=payload)
        response.raise_for_status()
        return response.json()


async def _generate_gemini(model: str, key: str, instructions: str, input_data: dict[str, Any], max_output_tokens: int) -> tuple[str, str | None]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model, safe='')}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": instructions + "\nReturn only a valid JSON object. Do not include markdown fences."}]},
        "contents": [{"role": "user", "parts": [{"text": json.dumps(input_data, ensure_ascii=False)}]}],
        "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": max_output_tokens},
    }
    result = await _post_json(url, headers={"Content-Type": "application/json"}, params={"key": key}, payload=payload)
    parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    raw = "".join(part.get("text", "") for part in parts)
    if not raw:
        raise ValueError("Gemini returned no text content.")
    return raw, result.get("responseId")


async def _generate_openai_compatible(provider: str, base_url: str, key: str, model: str, instructions: str, input_data: dict[str, Any], max_output_tokens: int) -> tuple[str, str | None]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": instructions + "\nReturn only a valid JSON object. Do not include markdown fences."},
            {"role": "user", "content": json.dumps(input_data, ensure_ascii=False)},
        ],
        "max_tokens": max_output_tokens,
    }
    if provider == "groq":
        payload["response_format"] = {"type": "json_object"}
    result = await _post_json(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        payload=payload,
    )
    choices = result.get("choices", [])
    raw = choices[0].get("message", {}).get("content") if choices else None
    if not raw:
        raise ValueError(f"{provider} returned no text content.")
    return raw, result.get("id")


async def generate_json(*, instructions: str, input_data: dict[str, Any], max_output_tokens: int = 3000) -> dict[str, Any]:
    """Generate a JSON object, trying only configured free/local providers in order."""
    if not 100 <= max_output_tokens <= 12000:
        raise ValueError("max_output_tokens must be between 100 and 12000")
    configured = [(name, _provider_config(name)) for name in _provider_order()]
    configured = [(name, config) for name, config in configured if config is not None]
    if not configured:
        raise AIProviderNotConfigured(
            "Configure at least one free provider: Gemini, Groq, or local Ollama."
        )

    failures: list[str] = []
    for name, config in configured:
        key, model, base_url = config
        try:
            if name == "gemini":
                raw, response_id = await _generate_gemini(model, key, instructions, input_data, max_output_tokens)
            else:
                raw, response_id = await _generate_openai_compatible(
                    name, base_url, key, model, instructions, input_data, max_output_tokens
                )
            return {
                "data": _parse_object(raw),
                "provider": name,
                "model": model,
                "response_id": response_id,
            }
        except Exception as exc:
            # Keep provider error details out of API responses and logs; they can contain request metadata.
            failures.append(f"{name}:{type(exc).__name__}")

    raise AIProviderError(
        "All configured free AI providers failed (" + ", ".join(failures) + "). "
        "Check provider availability, free-tier quotas, model names, and local Ollama status."
    )
