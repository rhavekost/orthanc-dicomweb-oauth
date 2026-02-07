"""Test code quality standards."""
import ast
from pathlib import Path


def test_no_magic_numbers_in_token_manager():
    """Token manager should use named constants instead of magic numbers."""
    file_path = Path("src/token_manager.py")

    with open(file_path) as f:
        content = f.read()

    # Check that constants are defined at module level
    assert (
        "MAX_TOKEN_ACQUISITION_RETRIES" in content
    ), "Missing MAX_TOKEN_ACQUISITION_RETRIES constant"
    assert (
        "INITIAL_RETRY_DELAY_SECONDS" in content
    ), "Missing INITIAL_RETRY_DELAY_SECONDS constant"
    assert (
        "TOKEN_REQUEST_TIMEOUT_SECONDS" in content
    ), "Missing TOKEN_REQUEST_TIMEOUT_SECONDS constant"
    assert (
        "DEFAULT_TOKEN_EXPIRY_SECONDS" in content
    ), "Missing DEFAULT_TOKEN_EXPIRY_SECONDS constant"

    # Check that magic numbers are not used inline
    # Parse and check _acquire_token method
    tree = ast.parse(content)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_acquire_token":
            # Check for inline numeric literals
            for child in ast.walk(node):
                if isinstance(child, ast.Constant) and isinstance(child.value, int):
                    # Acceptable: 0, 1 (for range/indexing), not 3, 30, 3600
                    if child.value in [3, 30, 3600]:
                        raise AssertionError(
                            f"Magic number {child.value} found at line "
                            f"{child.lineno}. Use named constant instead."
                        )
