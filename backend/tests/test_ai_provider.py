import os

from app.ai_provider import provider_status


def test_provider_status_never_exposes_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    result = provider_status()
    assert result["provider"] == "openai"
    assert result["configured"] is True
    assert result["model"] == "test-model"
    assert "test-secret-value" not in str(result)


def test_provider_status_reports_unconfigured_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    result = provider_status()
    assert result["configured"] is False
    assert result["model"] is None


def test_provider_status_reports_unconfigured_without_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-value")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    result = provider_status()
    assert result["configured"] is False
    assert result["model"] is None
