"""Test that code quality tooling is properly configured."""
import subprocess


def test_mypy_strict_configuration() -> None:
    """Mypy should be configured in strict mode."""
    # Read pyproject.toml
    import tomllib

    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)

    mypy_config = config["tool"]["mypy"]

    # Strict mode requirements
    assert (
        mypy_config["disallow_untyped_defs"] is True
    ), "mypy must disallow untyped function definitions"
    assert (
        mypy_config.get("no_strict_optional", False) is False
    ), "mypy must enforce strict optional checking"
    assert mypy_config["warn_return_any"] is True, "mypy must warn on returning Any"
    assert (
        mypy_config["warn_unused_configs"] is True
    ), "mypy must warn on unused configs"
    assert (
        mypy_config.get("strict", False) is True
    ), "mypy strict mode should be enabled"


def test_mypy_passes_on_all_source() -> None:
    """All source code must pass mypy type checking."""
    result = subprocess.run(["mypy", "src/"], capture_output=True, text=True)

    assert (
        result.returncode == 0
    ), f"mypy found type errors:\n{result.stdout}\n{result.stderr}"
