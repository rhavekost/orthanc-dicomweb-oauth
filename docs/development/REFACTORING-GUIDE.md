# Refactoring Guide

## Purpose

Safe refactoring practices that preserve code quality and prevent complexity regression.

## When to Refactor

- **Function exceeds complexity B (7)** - immediate attention required
- **Module exceeds 150 LOC** - consider splitting into smaller modules
- **Test coverage drops below 80%** - add tests first before refactoring
- **Code duplication appears 3+ times** - extract to function or module

## When NOT to Refactor

- **Tests are failing** - fix tests first before attempting refactoring
- **No clear improvement** - don't change for change's sake
- **Breaking public API** - coordinate with users and plan migration

## Safe Refactoring Process

1. **Write tests for existing behavior** (if missing)
2. **Run radon before:** `radon cc src/ -a`
3. **Make incremental changes** - small steps, not big rewrites
4. **Run tests after each change** - ensure behavior is preserved
5. **Run radon after:** verify complexity didn't increase
6. **Update documentation** - reflect any API or behavior changes

## Complexity Thresholds

Following Radon's cyclomatic complexity grades:

| Grade | Complexity | Action |
|-------|-----------|--------|
| A | 1-5 | Excellent - maintain this |
| B | 6-10 | Good - acceptable |
| C | 11-20 | Moderate - consider refactoring |
| D | 21-30 | High - refactor recommended |
| E | 31-40 | Very high - refactor required |
| F | 41+ | Extremely high - urgent refactoring |

**Project standard:** Maintain average complexity at A (< 5), individual functions at B or better (< 10).

## Handling Global State

```python
# Current pattern (acceptable for single-instance plugin)
_plugin_context: Optional[PluginContext] = None

# When to refactor: If multi-instance support needed
# Recommended: Singleton pattern or context manager
```

**Note:** Global state is currently acceptable because Orthanc loads plugins as single instances. Only refactor if multi-instance support becomes a requirement.

## Measuring Impact

```bash
# Before refactoring
radon cc src/module.py -s > before.txt
pytest tests/ --cov=src

# After refactoring
radon cc src/module.py -s > after.txt
diff before.txt after.txt  # Should show improvement or no change
pytest tests/ --cov=src    # Coverage should not decrease
```

## Common Refactoring Patterns

### Extract Function

**Before:**
```python
def process_request():
    # 20 lines of validation
    # 30 lines of processing
    # 15 lines of response formatting
```

**After:**
```python
def process_request():
    validate_request()
    result = process_data()
    return format_response(result)
```

### Extract Class

**Before:**
```python
def token_operation1():
    # uses global state

def token_operation2():
    # uses global state
```

**After:**
```python
class TokenManager:
    def operation1(self):
        # uses instance state

    def operation2(self):
        # uses instance state
```

## Testing During Refactoring

1. **Ensure tests exist** - if not, write them first
2. **Run tests frequently** - after every small change
3. **Don't skip CI checks** - linting, formatting, type checking
4. **Measure coverage** - should not decrease

## When in Doubt

- **Ask for review** - second pair of eyes helps
- **Make it work, make it right, make it fast** - in that order
- **Simpler is better** - don't over-engineer

## Contact

Questions about refactoring decisions? Open a GitHub issue with the `refactoring` label.
