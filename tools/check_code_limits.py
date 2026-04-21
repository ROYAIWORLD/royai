#!/usr/bin/env python3
"""Project guardrails: file/function size checks."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_LINES = 500
MAX_PY_FUNCTION_LINES = 120
TARGET_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".css", ".html"}
EXCLUDED_DIRS = {".git", "venv", "__pycache__", ".mypy_cache", ".pytest_cache"}
EXCLUDED_PATH_PREFIXES = {"static/vendor"}


def should_skip(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return True
    return any(rel.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES)


def check_file_line_limit(path: Path, lines: list[str], issues: list[str]) -> None:
    if len(lines) > MAX_FILE_LINES:
        issues.append(
            f"{path.relative_to(ROOT)}: file has {len(lines)} lines (max {MAX_FILE_LINES})"
        )


def check_python_function_limits(path: Path, source: str, issues: list[str]) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        issues.append(f"{path.relative_to(ROOT)}: syntax error while parsing ({exc})")
        return

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.end_lineno:
            fn_len = node.end_lineno - node.lineno + 1
            if fn_len > MAX_PY_FUNCTION_LINES:
                issues.append(
                    f"{path.relative_to(ROOT)}:{node.lineno} {node.name}() is {fn_len} lines "
                    f"(max {MAX_PY_FUNCTION_LINES})"
                )


def main() -> int:
    issues: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in TARGET_SUFFIXES:
            continue
        if should_skip(path):
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        lines = source.splitlines()
        check_file_line_limit(path, lines, issues)
        if path.suffix == ".py":
            check_python_function_limits(path, source, issues)

    if issues:
        print("Code limit violations found:\n")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Code limits OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
