"""Test that required dependencies are installed."""
import importlib.util


def test_flask_limiter_installed() -> None:
    """Verify flask-limiter is installed."""
    spec = importlib.util.find_spec("flask_limiter")
    assert spec is not None, "flask-limiter is not installed"
