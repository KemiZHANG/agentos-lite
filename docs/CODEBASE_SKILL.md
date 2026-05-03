# Codebase Intelligence Skill

The MVP indexes local repositories with these ignores:

`node_modules`, `.git`, `dist`, `build`, `__pycache__`, `.venv`, `venv`, `.next`

Python files are parsed with `ast`. TypeScript and JavaScript files use lightweight regex extraction for imports, exports, classes, and functions.

Endpoints support repository questions, relevant-file search, and test suggestions. Citations use file paths.

