"""Configuration schema validation."""
import json
from pathlib import Path
from typing import Any, Dict, cast

try:
    import jsonschema
    from jsonschema import ValidationError

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception  # Fallback


def get_schema_path() -> Path:
    """Get path to configuration schema file."""
    # Schema is in schemas/ directory at project root
    current_file = Path(__file__)
    project_root = current_file.parent.parent
    return project_root / "schemas" / "config-schema.json"


def load_schema() -> Dict[str, Any]:
    """
    Load configuration schema from file.

    Returns:
        Schema dictionary

    Raises:
        FileNotFoundError: If schema file not found
    """
    schema_path = get_schema_path()

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r") as f:
        return cast(Dict[str, Any], json.load(f))


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration against JSON Schema.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ValidationError: If configuration is invalid
        ImportError: If jsonschema library not installed
    """
    if not JSONSCHEMA_AVAILABLE:
        raise ImportError(
            "jsonschema library required for validation. "
            "Install with: pip install jsonschema"
        )

    schema = load_schema()

    try:
        jsonschema.validate(instance=config, schema=schema)
    except ValidationError as e:
        # Make error message more user-friendly
        error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
        raise ValidationError(
            f"Configuration validation failed at '{error_path}': {e.message}"
        ) from e
