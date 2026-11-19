# Free hybrid AI provider setup

PrepCompass uses a free-inference-only provider router. It does not call OpenAI and has no paid-provider fallback.

## Hosted model safety allowlist

To prevent accidental paid inference, the application accepts only these hosted model IDs:

- Gemini: `gemini-2.5-flash`, `gemini-2.5-flash-lite` (Google lists these on the free tier; access is account/region/availability dependent).
- Groq: `openai/gpt-oss-120b`, `openai/gpt-oss-20b` (use the Groq Free plan, not the paid Developer plan).

Other hosted model IDs are rejected by configuration validation. The allowlist must be reviewed when providers change their free-tier catalog. Ollama models are local and are not subject to this hosted model allowlist.

## Provider order

Set `AI_PROVIDER` to the primary provider and `AI_FALLBACK_PROVIDERS` to an ordered comma-separated list:

- `gemini`: Google Gemini Developer API. Free-tier availability, model access, rate limits and data-use terms are controlled by Google and can change.
- `groq`: GroqCloud hosted inference. Use only models currently available on its free developer tier; limits can change.
- `ollama`: local inference on your own Mac. No hosted inference charge; model downloads use disk space and generation uses local memory/CPU/GPU.

When a provider fails (including quota/rate-limit errors), the router tries the next configured provider. If all configured providers fail, the API returns a safe provider error. It never falls back to a paid OpenAI endpoint.

## Configuration

Copy `backend/.env.example` to `backend/.env` or merge these settings into the existing file. Preserve your database and Google OAuth settings.

```env
AI_PROVIDER=gemini
AI_FALLBACK_PROVIDERS=groq,ollama

GEMINI_API_KEY=
GEMINI_MODEL=

GROQ_API_KEY=
GROQ_MODEL=

OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
OLLAMA_MODEL=
```

Get a Gemini key from [Google AI Studio](https://aistudio.google.com/). Get a Groq key from [Groq Console](https://console.groq.com/). Select model IDs that are currently available to your account and free tier; model availability and quotas are not guaranteed. Do not paste keys into chat, frontend variables, source control or logs.

## Ollama on macOS with Docker

1. Install and start [Ollama](https://ollama.com/).
2. Pull a model suitable for your Mac's available memory, for example with `ollama pull qwen2.5:3b` (choose a model appropriate to your hardware).
3. Set `OLLAMA_MODEL` to the exact model tag shown by `ollama list`.
4. Keep `OLLAMA_BASE_URL=http://host.docker.internal:11434/v1`. This lets the API container reach Ollama running on the Mac host.
5. Confirm Ollama is reachable from the host with `curl http://localhost:11434/api/tags`.

## Apply configuration

After editing `backend/.env`, recreate the API container:

```bash
docker compose up -d --build --force-recreate api
```

Sign in and open `http://localhost:8011/api/ai/status`. It reports provider readiness and model names, never credentials. Readiness means configuration exists; it does not guarantee provider quota or network availability.

## Live smoke test

```bash
docker compose exec api python -c 'import asyncio; from app.ai_provider import generate_json; print(asyncio.run(generate_json(instructions="Return a JSON object with status set to ok.", input_data={"test":"connectivity"}, max_output_tokens=200)))'
```

A successful result includes `data`, the provider actually used, and its model. If hosted free quotas are exhausted, the router attempts the next configured provider, including Ollama if it is configured and running.

## Privacy and exam-content quality

Do not send passwords, session tokens, API keys or unnecessary personal data to an AI provider. Review each provider's current free-tier data-use and retention terms before sending study records. AI-generated questions and feedback are drafts, not official PYQs or authoritative exam notifications. Validate exam facts against official UPSC/UPPSC sources.
