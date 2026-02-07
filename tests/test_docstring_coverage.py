"""Test docstring coverage for public functions and classes."""
import ast
from pathlib import Path


def get_docstring_coverage(file_path: Path) -> tuple[int, int, list]:
    """
    Calculate docstring coverage for a Python file.

    Args:
        file_path: Path to Python file

    Returns:
        Tuple of (documented_count, total_count, missing_docstrings)
    """
    with open(file_path) as f:
        tree = ast.parse(f.read())

    total = 0
    documented = 0
    missing = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            # Skip private/internal functions
            if node.name.startswith("_") and not node.name.startswith("__"):
                continue

            total += 1
            docstring = ast.get_docstring(node)

            if docstring and len(docstring.strip()) > 10:
                documented += 1
            else:
                missing.append(f"{file_path.name}:{node.lineno} - {node.name}")

    return documented, total, missing


def test_dicomweb_oauth_plugin_docstring_coverage():
    """Main plugin file should have >80% docstring coverage."""
    file_path = Path("src/dicomweb_oauth_plugin.py")
    documented, total, missing = get_docstring_coverage(file_path)

    coverage = (documented / total * 100) if total > 0 else 0

    assert coverage >= 80, (
        f"Docstring coverage is {coverage:.1f}%, need 80%.\n"
        f"Missing docstrings:\n" + "\n".join(missing)
    )


def test_token_manager_docstring_coverage():
    """Token manager should have >80% docstring coverage."""
    file_path = Path("src/token_manager.py")
    documented, total, missing = get_docstring_coverage(file_path)

    coverage = (documented / total * 100) if total > 0 else 0

    assert coverage >= 80, (
        f"Docstring coverage is {coverage:.1f}%, need 80%.\n"
        f"Missing docstrings:\n" + "\n".join(missing)
    )


def test_config_parser_docstring_coverage():
    """Config parser should have >80% docstring coverage."""
    file_path = Path("src/config_parser.py")
    documented, total, missing = get_docstring_coverage(file_path)

    coverage = (documented / total * 100) if total > 0 else 0

    assert coverage >= 80, (
        f"Docstring coverage is {coverage:.1f}%, need 80%.\n"
        f"Missing docstrings:\n" + "\n".join(missing)
    )


def test_overall_docstring_coverage():
    """Overall project should have >77% docstring coverage."""
    src_dir = Path("src")
    total_documented = 0
    total_count = 0

    for py_file in src_dir.glob("**/*.py"):
        if py_file.name == "__init__.py":
            continue

        documented, count, _ = get_docstring_coverage(py_file)
        total_documented += documented
        total_count += count

    coverage = (total_documented / total_count * 100) if total_count > 0 else 0

    assert coverage >= 77, f"Overall docstring coverage is {coverage:.1f}%, need 77%"
