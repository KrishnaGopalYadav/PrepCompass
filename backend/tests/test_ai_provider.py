import asyncio

import pytest

from app import ai_provider


def test_provider_status_never_exposes_secrets(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("AI_FALLBACK_PROVIDERS", "groq,ollama")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-secret")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")
    monkeypatch.setenv("GROQ_API_KEY", "groq-secret")
    monkeypatch.setenv("GROQ_MODEL", "groq-test")
    monkeypatch.setenv("OLLAMA_MODEL", "local-test")

    result = ai_provider.provider_status()

    assert result["configured"] is True
    assert result["provider"] == "gemini"
    assert result["paid_fallback_enabled"] is False
    assert [item["provider"] for item in result["providers"]] == ["gemini", "groq", "ollama"]
    assert "gemini-secret" not in str(result)
    assert "groq-secret" not in str(result)


def test_provider_status_unconfigured_without_any_provider(monkeypatch):
    for name in ("GEMINI_API_KEY", "GEMINI_MODEL", "GROQ_API_KEY", "GROQ_MODEL", "OLLAMA_MODEL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("AI_FALLBACK_PROVIDERS", "groq,ollama")

    result = ai_provider.provider_status()

    assert result["configured"] is False
    assert result["model"] is None


def test_provider_order_deduplicates_and_honors_order(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "groq")
    monkeypatch.setenv("AI_FALLBACK_PROVIDERS", "gemini,groq,ollama")
    assert ai_provider._provider_order() == ["groq", "gemini", "ollama"]


def test_parse_object_accepts_json_fence():
    assert ai_provider._parse_object('''\x60\x60\x60json
{"ok": true}
\x60\x60\x60''') == {"ok": True}


def test_parse_object_rejects_non_object():
    with pytest.raises(ValueError):
        ai_provider._parse_object('[1, 2, 3]')


def test_generate_json_falls_back_from_gemini_to_groq(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("AI_FALLBACK_PROVIDERS", "groq,ollama")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-gemini-model")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("GROQ_MODEL", "test-groq-model")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    async def fail_gemini(*args, **kwargs):
        raise RuntimeError("quota exhausted")

    async def succeed_groq(*args, **kwargs):
        return '{"status":"ok"}', "test-response"

    monkeypatch.setattr(ai_provider, "_generate_gemini", fail_gemini)
    monkeypatch.setattr(ai_provider, "_generate_openai_compatible", succeed_groq)

    result = asyncio.run(ai_provider.generate_json(
        instructions="Return status.",
        input_data={"test": True},
        max_output_tokens=200,
    ))

    assert result["data"] == {"status": "ok"}
    assert result["provider"] == "groq"
    assert result["model"] == "test-groq-model"


def test_generate_json_never_uses_unconfigured_or_paid_provider(monkeypatch):
    for name in ("GEMINI_API_KEY", "GEMINI_MODEL", "GROQ_API_KEY", "GROQ_MODEL", "OLLAMA_MODEL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_FALLBACK_PROVIDERS", "")

    with pytest.raises(ai_provider.AIProviderNotConfigured):
        asyncio.run(ai_provider.generate_json(instructions="x", input_data={}))
