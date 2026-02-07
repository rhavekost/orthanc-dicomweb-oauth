# Code Review Checklist

## Purpose

Consistent code review standards to maintain code quality and prevent regressions.

## Automated Checks (CI enforces these)

CI pipeline automatically validates:

- [ ] All tests pass
- [ ] Code coverage ≥ 77%
- [ ] Pylint score ≥ 9.0
- [ ] Black formatting applied
- [ ] Type hints present

**Note:** If CI fails, address automated checks before manual review.

## Manual Review

### Complexity

- [ ] No functions exceed complexity B (7)
- [ ] New code maintains average complexity < 3
- [ ] Complex logic has explanatory comments
- [ ] Nested loops/conditions minimized

**Check with:** `radon cc src/changed_file.py -s`

### Design

- [ ] Follows existing patterns (Factory, Strategy, etc.)
- [ ] Single Responsibility Principle honored
- [ ] Dependencies injected, not hard-coded
- [ ] No new global variables (unless absolutely necessary)
- [ ] Appropriate use of inheritance vs composition
- [ ] Clear separation of concerns

### Testing

- [ ] New features have tests
- [ ] Edge cases covered
- [ ] Error paths tested
- [ ] Mocks used appropriately (not over-mocked)
- [ ] Test names clearly describe what they test
- [ ] Tests are independent (no shared state)
- [ ] Tests are deterministic (no random/time dependencies)

### Security

- [ ] No secrets in code
- [ ] Input validation present
- [ ] SQL injection prevented (if applicable)
- [ ] Error messages don't leak secrets
- [ ] Authentication/authorization checked
- [ ] Sensitive data logged appropriately (never log tokens/passwords)

### Documentation

- [ ] Public functions have docstrings
- [ ] Complex logic explained
- [ ] Configuration changes documented
- [ ] Breaking changes noted in CHANGELOG
- [ ] README updated if needed
- [ ] API changes reflected in examples

## Review Levels

### Minor Changes (< 50 lines)
- Focus on automated checks + manual review
- Single reviewer sufficient

### Major Changes (50-200 lines)
- Full checklist required
- Consider two reviewers for critical areas

### Large Changes (> 200 lines)
- Should be split into smaller PRs if possible
- Multiple reviewers recommended
- Extra attention to design and testing

## Common Issues to Watch For

1. **Hardcoded values** - should be configuration or constants
2. **Missing error handling** - what happens when things fail?
3. **Incomplete logging** - sufficient context for debugging?
4. **Breaking API changes** - coordinated with users?
5. **Performance implications** - new loops in hot paths?
6. **Resource leaks** - files/connections closed properly?

## Questions to Ask

- Does this change make the codebase better or just different?
- Would I understand this code in 6 months?
- Is there a simpler way to achieve the same result?
- Are we solving the right problem?
- What could go wrong with this change?

## Providing Feedback

- Be specific and constructive
- Link to style guide or documentation when applicable
- Distinguish between "must fix" and "nice to have"
- Recognize good work and improvements
- Ask questions when unclear rather than assuming

## Responding to Feedback

- Address all comments (fix, explain, or discuss)
- Don't take feedback personally
- Ask for clarification if needed
- Push back respectfully if you disagree
- Thank reviewers for their time

## Contact

Questions about code review process? Open a GitHub issue with the `process` label.
