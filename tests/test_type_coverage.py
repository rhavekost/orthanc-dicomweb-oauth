"""Test type hint coverage across all modules."""
import ast
from pathlib import Path
from typing import Dict


def get_function_signature_coverage(file_path: Path) -> Dict[str, bool]:
    """Check if functions have complete type annotations."""
    with open(file_path) as f:
        tree = ast.parse(f.read())

    results = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Skip private test helpers
            if node.name.startswith("_test_"):
                continue

            # Check if function has return annotation
            has_return = node.returns is not None

            # Check if all arguments have annotations (except self, cls)
            has_arg_annotations = all(
                arg.annotation is not None
                for arg in node.args.args
                if arg.arg not in ["self", "cls"]
            )

            results[node.name] = has_return and has_arg_annotations

    return results


def test_dicomweb_oauth_plugin_type_coverage() -> None:
    """All functions in dicomweb_oauth_plugin.py must have complete type hints."""
    file_path = Path("src/dicomweb_oauth_plugin.py")
    coverage = get_function_signature_coverage(file_path)

    untyped = [name for name, typed in coverage.items() if not typed]

    assert (
        not untyped
    ), f"Functions missing complete type hints in {file_path}:\n" + "\n".join(
        f"  - {name}" for name in untyped
    )


def test_token_manager_type_coverage() -> None:
    """All functions in token_manager.py must have complete type hints."""
    file_path = Path("src/token_manager.py")
    coverage = get_function_signature_coverage(file_path)

    untyped = [name for name, typed in coverage.items() if not typed]

    # _acquire_token already has types, but verify
    assert (
        not untyped
    ), f"Functions missing complete type hints in {file_path}:\n" + "\n".join(
        f"  - {name}" for name in untyped
    )


def test_config_parser_type_coverage() -> None:
    """All functions in config_parser.py must have complete type hints."""
    file_path = Path("src/config_parser.py")
    coverage = get_function_signature_coverage(file_path)

    untyped = [name for name, typed in coverage.items() if not typed]

    assert (
        not untyped
    ), f"Functions missing complete type hints in {file_path}:\n" + "\n".join(
        f"  - {name}" for name in untyped
    )
