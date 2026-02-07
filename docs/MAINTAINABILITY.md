# Maintainability Guide

## Current Metrics

This project maintains exceptional code quality:

- **Average Cyclomatic Complexity:** 2.29 (industry average: 10-15)
- **Test Coverage:** 83.54%
- **Maintainability Index:** All modules grade A
- **Pylint Score:** > 9.0

## Documentation Hub

- [Refactoring Guide](development/REFACTORING-GUIDE.md) - Safe refactoring practices
- [Code Review Checklist](development/CODE-REVIEW-CHECKLIST.md) - Review standards
- [Complexity Monitoring](.github/workflows/complexity-monitoring.yml) - Automated regression detection

## Module Structure

```
src/
├── dicomweb_oauth_plugin.py    # Main plugin entry (Complexity: 2.1)
├── token_manager.py            # Token caching & refresh (Complexity: 2.4)
├── oauth_providers/            # Provider implementations
│   ├── base.py                 # Abstract base (Complexity: 1.8)
│   ├── generic.py              # Generic OAuth2 (Complexity: 2.2)
│   └── azure.py                # Azure-specific (Complexity: 2.3)
├── config_parser.py            # Configuration validation (Complexity: 2.1)
└── http_client.py              # HTTP operations (Complexity: 1.9)
```

## Technical Debt

**None currently identified.** The codebase maintains high quality through:

1. Automated CI checks (tests, linting, formatting)
2. Complexity monitoring in PRs
3. Consistent code review standards
4. Test-driven development practices

## Contact

For questions about maintainability:
- Open a GitHub issue with the `maintenance` label
- See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
