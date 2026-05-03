from app.services.agent import detect_intent


def test_agent_intent_routing():
    assert detect_intent("Which files are related to document upload?") == "codebase_question"
    assert detect_intent("Generate test suggestions for this function") == "test_generation"
    assert detect_intent("remember that I prefer mock mode") == "memory_update"

