# Tool Risk Policy

AgentOS Lite tools are grouped by risk level.

## Safe

Safe tools can run immediately because they only read local indexed data or transform supplied text.

Examples:

- `search_knowledge_base`
- `extract_task_list`
- `search_codebase`
- `generate_test_suggestions`

## Approval Required

Approval-required tools pause and create an approval request. A human must approve or reject the action before it completes.

Examples:

- `save_memory`
- `generate_markdown_report`

## Blocked

Blocked tools never execute in the MVP. They exist to demonstrate explicit guardrails.

Blocked operations:

- Shell commands from user input
- File deletion
- Sending emails
- Destructive filesystem operations

The blocked placeholder tool `dangerous_shell_command` always returns `blocked` and records the attempt in tool-call logs.
