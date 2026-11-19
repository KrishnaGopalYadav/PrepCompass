"""OpenAI Responses API adapter for PrepCompass.

The API key and model are server-side configuration only. This module deliberately
does not implement unrestricted autonomous tool execution: agent workflows must
call approved application services and validate every model output.
"""
import json
import os
from typing import Any

from openai import AsyncOpenAI


class AIProviderNotConfigured(RuntimeError):
    pass


class AIProviderError(RuntimeError):
    pass


def provider_status() -> dict[str, Any]:
    configured = bool(os.getenv("OPENAI_API_KEY", "").strip() and os.getenv("OPENAI_MODEL", "").strip())
    return {
        "provider": "openai",
        "configured": configured,
        "model": os.getenv("OPENAI_MODEL", "") if configured else None,
        "capabilities": ["study_diagnostics", "mock_question_drafting", "answer_feedback", "weekly_magazine_drafting"],
    }


async def generate_json(*, instructions: str, input_data: dict[str, Any], max_output_tokens: int = 3000) -> dict[str, Any]:
    """Generate a JSON object via Responses API and reject malformed/non-object output."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()
    if not api_key or not model:
        raise AIProviderNotConfigured("Configure OPENAI_API_KEY and OPENAI_MODEL in the backend environment.")
    if not 100 <= max_output_tokens <= 12000:
        raise ValueError("max_output_tokens must be between 100 and 12000")
    try:
        client = AsyncOpenAI(api_key=api_key, timeout=60.0, max_retries=2)
        response = await client.responses.create(
            model=model,
            instructions=instructions + "\\nReturn only a valid JSON object. Do not include markdown fences.",
            input=json.dumps(input_data, ensure_ascii=False),
            max_output_tokens=max_output_tokens,
        )
        raw = response.output_text
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("Model output must be a JSON object.")
        return {"data": parsed, "provider": "openai", "model": model, "response_id": response.id}
    except AIProviderNotConfigured:
        raise
    except Exception as exc:
        raise AIProviderError("OpenAI request failed or returned invalid structured output.") from exc
