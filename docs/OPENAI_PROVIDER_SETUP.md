# OpenAI provider setup

PrepCompass uses OpenAI as its primary AI provider through the official Python SDK and Responses API. The integration is server-side only.

## Local configuration

1. Copy `backend/.env.example` to `backend/.env` (or merge the two OpenAI entries into your existing file).
2. Set `OPENAI_API_KEY` to an API key created in your OpenAI developer account.
3. Set `OPENAI_MODEL` to a model available to that API project.
4. Never put the key in frontend environment variables, source control, screenshots, logs or chat.
5. Rebuild the backend container after changing environment configuration.

## Readiness endpoint

After signing in, call `GET /api/ai/status`. It reports provider name, configured status, selected model and supported application capabilities. It never returns the API key.

A configured provider does not mean all agent features are implemented. PYQ ingestion, exam-specific mock blueprints, descriptive evaluation, current-affairs research, magazine publishing and adaptive planning are delivered in separate tested milestones. Until then, do not describe them as live.

## Security and operations

- Keep API calls on the FastAPI backend.
- Use a dedicated API project/key for PrepCompass and set project budget/usage alerts.
- Restrict access to the local machine/network as appropriate.
- Rotate/revoke exposed keys immediately.
- Store model, prompt version, request ID, usage and output validation status for future agent-run auditing.
- Use bounded workflows and approved application services; do not allow unrestricted model tool execution.
