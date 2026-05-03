from app.services.codebase import parse_symbols


def test_python_parser_extracts_functions_and_docstrings():
    symbols = parse_symbols('"""module"""\nimport os\n\ndef run(value):\n    """Run demo."""\n    return value\n', "python")
    names = {symbol["name"] for symbol in symbols}
    assert "os" in names
    assert "run" in names
    assert any(symbol.get("docstring") == "Run demo." for symbol in symbols)


def test_typescript_parser_extracts_exports():
    symbols = parse_symbols('import x from "pkg";\nexport function run(input: string) { return input; }\nexport class Worker {}\n', "typescript")
    names = {symbol["name"] for symbol in symbols}
    assert "pkg" in names
    assert "run" in names
    assert "Worker" in names

