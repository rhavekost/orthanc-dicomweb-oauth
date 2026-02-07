"""Test comment quality in complex code sections."""


def test_code_complexity_acceptable() -> None:
    """Code should maintain acceptable complexity levels."""
    import subprocess

    # Check average across ALL functions
    result = subprocess.run(
        ["radon", "cc", "src/", "-a"], capture_output=True, text=True
    )

    output = result.stdout

    # Average complexity should be A (1-5) or low B (< 7)
    # Extract the average to be more flexible
    if "Average complexity:" in output:
        # Check that average is reasonable (< 7.0)
        import re

        match = re.search(r"Average complexity: [A-F] \(([\d.]+)\)", output)
        if match:
            avg_complexity = float(match.group(1))
            assert (
                avg_complexity < 5.0
            ), f"Average complexity {avg_complexity} is too high (should be < 5.0)"


def test_no_highly_complex_functions() -> None:
    """No functions should have very high complexity (> 10)."""
    import subprocess

    result = subprocess.run(
        ["radon", "cc", "src/", "-n", "C"], capture_output=True, text=True
    )

    # radon with -n C shows only functions with complexity >= C (7+)
    # We allow some B-grade functions (6-7) but nothing worse
    output = result.stdout.strip()

    if output:
        # Check if any functions are above B grade (complexity > 7)
        lines = output.split("\n")
        high_complexity = [
            line
            for line in lines
            if " C " in line or " D " in line or " E " in line or " F " in line
        ]

        assert (
            not high_complexity
        ), "Found highly complex functions that need refactoring:\n" + "\n".join(
            high_complexity
        )
