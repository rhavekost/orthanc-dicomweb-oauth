"""Test linting tools configuration and checks."""
import subprocess


def test_pylint_configuration_exists() -> None:
    """Pylint should be configured in pyproject.toml."""
    import tomllib

    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)

    assert "tool" in config, "pyproject.toml should have [tool] section"
    assert "pylint" in config["tool"], "pyproject.toml should have [tool.pylint]"


def test_pylint_passes_on_source() -> None:
    """Source code should pass pylint checks."""
    result = subprocess.run(
        ["pylint", "src/", "--rcfile=pyproject.toml"],
        capture_output=True,
        text=True,
    )

    # Pylint score should be >= 9.0
    output = result.stdout
    if "Your code has been rated at" in output:
        import re

        match = re.search(r"rated at ([\d.]+)/10", output)
        if match:
            score = float(match.group(1))
            assert score >= 9.0, f"Pylint score {score}/10 is too low (need >= 9.0/10)"


def test_radon_complexity_tool_available() -> None:
    """Radon tool should be available for complexity analysis."""
    result = subprocess.run(["radon", "--version"], capture_output=True, text=True)

    assert result.returncode == 0, "radon should be installed and accessible"


def test_vulture_finds_minimal_dead_code() -> None:
    """Vulture should find minimal dead code in source."""
    result = subprocess.run(
        ["vulture", "src/", "--min-confidence", "80"],
        capture_output=True,
        text=True,
    )

    # Vulture returns non-zero when dead code is found
    # We allow some false positives but should be minimal
    output = result.stdout.strip()

    if output:
        lines = output.split("\n")
        # Filter out known false positives
        real_issues = [
            line
            for line in lines
            if line
            and "unused" in line.lower()
            and "_ORTHANC_AVAILABLE" not in line
            and "_JSONSCHEMA_AVAILABLE" not in line
        ]

        # Should have < 5 real dead code issues
        assert (
            len(real_issues) < 5
        ), f"Found {len(real_issues)} dead code issues:\n" + "\n".join(real_issues)
