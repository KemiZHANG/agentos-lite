# Security and Guardrails

MVP guardrails:

- No hardcoded secrets.
- Provider API keys are read from environment variables only.
- Settings may show whether a key is configured, but never displays secret values.
- LLMOps records provider/model/status/errors/fallback state, never API keys.
- Mock providers by default.
- Gemini is optional and only enabled with `LLM_PROVIDER=gemini`.
- Provider health checks call Gemini only when the user clicks `Test Provider`.
- Public demos should use `DEMO_MODE=true`, `MAX_LLM_CALLS_PER_USER_PER_DAY=5`, and `DEMO_FALLBACK_TO_MOCK=true`.
- Hosted demo sessions use an anonymous cookie and never expose the raw session id in LLMOps.
- Risky tools require approval.
- Blocked tools never execute.
- The agent never executes shell commands from user input.
- The MVP never deletes files.
- The MVP never sends emails.
- Document answers without citations are marked low confidence.

Authentication is deferred; data uses default local user `local-user`.
