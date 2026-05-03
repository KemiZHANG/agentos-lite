# Security and Guardrails

MVP guardrails:

- No hardcoded secrets.
- Mock providers by default.
- Risky tools require approval.
- Blocked tools never execute.
- The agent never executes shell commands from user input.
- The MVP never deletes files.
- The MVP never sends emails.
- Document answers without citations are marked low confidence.

Authentication is deferred; data uses default local user `local-user`.

