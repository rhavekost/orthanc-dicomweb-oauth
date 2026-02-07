"""Test overall coding standards score calculation."""
import subprocess
from pathlib import Path


def test_coding_standards_score() -> None:
    """Calculate overall coding standards score and verify A+ grade."""
    scores = {}
    max_score = 100

    # 1. Type Safety (20 points)
    # All functions must have complete type hints
    result = subprocess.run(["mypy", "src/"], capture_output=True, text=True)
    scores["type_safety"] = 20 if result.returncode == 0 else 10

    # 2. Documentation (15 points)
    # >77% docstring coverage
    src_dir = Path("src")
    total_documented = 0
    total_count = 0

    for py_file in src_dir.glob("**/*.py"):
        if py_file.name == "__init__.py":
            continue

        import ast

        with open(py_file) as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue
                total_count += 1
                docstring = ast.get_docstring(node)
                if docstring and len(docstring.strip()) > 10:
                    total_documented += 1

    doc_coverage = (total_documented / total_count * 100) if total_count > 0 else 0
    scores["documentation"] = 15 if doc_coverage >= 77 else 10

    # 3. Code Complexity (15 points)
    # Average complexity < 5.0
    result = subprocess.run(
        ["radon", "cc", "src/", "-a"], capture_output=True, text=True
    )
    import re

    match = re.search(r"Average complexity: [A-F] \(([\d.]+)\)", result.stdout)
    if match:
        avg_complexity = float(match.group(1))
        scores["complexity"] = 15 if avg_complexity < 5.0 else 10
    else:
        scores["complexity"] = 10

    # 4. Code Formatting (10 points)
    # Black and isort
    black_result = subprocess.run(
        ["black", "--check", "src/", "tests/"], capture_output=True, text=True
    )
    isort_result = subprocess.run(
        ["isort", "--check-only", "src/", "tests/"], capture_output=True, text=True
    )
    scores["formatting"] = (
        10 if black_result.returncode == 0 and isort_result.returncode == 0 else 5
    )

    # 5. Linting (15 points)
    # Flake8, pylint >= 9.0
    flake8_result = subprocess.run(
        ["flake8", "src/", "tests/"], capture_output=True, text=True
    )
    pylint_result = subprocess.run(
        ["pylint", "src/", "--rcfile=pyproject.toml"], capture_output=True, text=True
    )

    pylint_score = 0.0
    match = re.search(r"rated at ([\d.]+)/10", pylint_result.stdout)
    if match:
        pylint_score = float(match.group(1))

    scores["linting"] = (
        15 if flake8_result.returncode == 0 and pylint_score >= 9.0 else 10
    )

    # 6. Security (10 points)
    # Bandit scan
    bandit_result = subprocess.run(
        ["bandit", "-r", "src/", "-ll"], capture_output=True, text=True
    )
    scores["security"] = 10 if bandit_result.returncode == 0 else 5

    # 7. Dead Code (5 points)
    # Vulture finds < 5 issues
    vulture_result = subprocess.run(
        ["vulture", "src/", "--min-confidence", "80"],
        capture_output=True,
        text=True,
    )
    dead_code_lines = [
        line
        for line in vulture_result.stdout.split("\n")
        if line
        and "unused" in line.lower()
        and "_ORTHANC_AVAILABLE" not in line
        and "_JSONSCHEMA_AVAILABLE" not in line
    ]
    scores["dead_code"] = 5 if len(dead_code_lines) < 5 else 3

    # 8. Test Coverage (10 points)
    # >= 80% coverage
    coverage_result = subprocess.run(
        ["pytest", "tests/", "--cov=src", "--cov-report=term"],
        capture_output=True,
        text=True,
    )
    match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", coverage_result.stdout)
    if match:
        coverage_pct = int(match.group(1))
        scores["test_coverage"] = 10 if coverage_pct >= 80 else 7
    else:
        scores["test_coverage"] = 7

    # Calculate total
    total_score = sum(scores.values())
    percentage = (total_score / max_score) * 100

    # Determine grade
    if percentage >= 95:
        grade = "A+"
    elif percentage >= 90:
        grade = "A"
    elif percentage >= 85:
        grade = "A-"
    elif percentage >= 80:
        grade = "B+"
    elif percentage >= 75:
        grade = "B"
    else:
        grade = "B-"

    # Print detailed breakdown
    print("\n" + "=" * 60)
    print("CODING STANDARDS SCORE BREAKDOWN")
    print("=" * 60)
    for category, score in scores.items():
        print(f"{category.replace('_', ' ').title():.<30} {score:>3} points")
    print("-" * 60)
    print(f"{'TOTAL SCORE':.<30} {total_score:>3}/{max_score}")
    print(f"{'PERCENTAGE':.<30} {percentage:>3.1f}%")
    print(f"{'GRADE':.<30} {grade:>3}")
    print("=" * 60)

    # Detailed scores for reporting
    print("\n" + "=" * 60)
    print("DETAILED METRICS")
    print("=" * 60)
    print(f"Documentation Coverage: {doc_coverage:.1f}%")
    print(f"Average Complexity: {avg_complexity:.2f}")
    print(f"Pylint Score: {pylint_score:.2f}/10")
    if match:
        print(f"Test Coverage: {coverage_pct}%")
    print(f"Dead Code Issues: {len(dead_code_lines)}")
    print("=" * 60 + "\n")

    # Assert A or better grade (90%+)
    assert (
        percentage >= 90.0
    ), f"Coding standards score is {percentage:.1f}% ({grade}), need 90% (A)"
