"""Test naming convention compliance."""
import ast
import pathlib
from typing import List, Tuple


def test_module_level_constants_are_private() -> None:
    """Module-level constants that are implementation details should be private."""
    src_files = list(pathlib.Path("src").rglob("*.py"))

    violations: List[Tuple[str, str, int]] = []

    for file_path in src_files:
        # Skip error_codes.py as all error codes are public API
        if "error_codes.py" in str(file_path):
            continue
        with open(file_path) as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        # Check for public-looking implementation constants
                        if name.isupper() and not name.startswith("_"):
                            # Known exceptions: __version__, API_VERSION
                            if name not in ["API_VERSION"]:
                                # Check if truly module-private
                                if "AVAILABLE" in name or "MODULE" in name:
                                    violations.append(
                                        (str(file_path), name, node.lineno)
                                    )

    assert not violations, (
        f"Found {len(violations)} module constants that should be private:\n"
        + "\n".join(f"  {f}:{line} - {name}" for f, name, line in violations)
    )
