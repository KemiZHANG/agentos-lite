# Agent Workflow

Every chat request creates an `agent_runs` record and visible trace steps:

1. Intent detection
2. Planner
3. Memory retrieval
4. RAG retrieval
5. Tool selection
6. Answer generation
7. Verification
8. Final response

Supported intents: `document_qa`, `summarize_document`, `generate_report`, `extract_tasks`, `codebase_question`, `test_generation`, `memory_update`, and `general_chat`.

