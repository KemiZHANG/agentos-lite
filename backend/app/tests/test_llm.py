from app.services.llm import MockLLMProvider


def test_mock_llm_project_overview_is_feature_specific():
    result = MockLLMProvider().generate("", task_type="project_overview")
    assert "web chat" in result.content
    assert "RAG citations" in result.content
    assert "codebase intelligence" in result.content


def test_mock_llm_summarizes_chunks_with_labels():
    result = MockLLMProvider().generate(
        "",
        task_type="summarize_document",
        context={
            "retrieved_chunks": [
                {
                    "document_name": "product_brief.md",
                    "content": "AgentOS Lite supports web chat. It includes memory and approvals.",
                }
            ],
            "memories": [],
        },
    )
    assert "Summary of product_brief.md" in result.content
    assert "[D1]" in result.content


def test_mock_llm_no_context_is_honest():
    result = MockLLMProvider().generate("", task_type="document_qa", context={"retrieved_chunks": []})
    assert "No relevant local document context" in result.content

