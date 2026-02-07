# Git Workflow Guide

## Overview

This project follows a streamlined Git workflow optimized for healthcare software development with emphasis on security, traceability, and collaboration.

## Branching Strategy

### Main Branches

- **main** - Production-ready code, always deployable
- **develop** (optional) - Integration branch for features (if using Gitflow)

### Feature Branches

```
feature/add-okta-support
bugfix/token-refresh-race-condition
hotfix/critical-security-vuln
docs/api-reference
chore/update-dependencies
```

**Naming Convention:**
```
<type>/<short-description>
```

**Types:**
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical fixes for production
- `docs/` - Documentation only
- `chore/` - Maintenance (deps, config)
- `refactor/` - Code refactoring
- `test/` - Test improvements

### Branch Lifecycle

1. **Create** from main (or develop)
2. **Develop** with frequent commits
3. **Test** thoroughly (local + CI)
4. **PR** to main (or develop)
5. **Review** by at least one other developer
6. **Merge** via squash or merge commit
7. **Delete** branch after merge

## Commit Messages

### Format: Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Code style (formatting, no logic change)
- **refactor**: Code refactoring (no feature change)
- **perf**: Performance improvement
- **test**: Add or update tests
- **chore**: Maintenance (deps, config, etc.)
- **ci**: CI/CD changes
- **security**: Security fix

### Scope (Optional)

Indicates which component is affected:

- `token`: Token management
- `config`: Configuration
- `api`: REST API
- `http`: HTTP client
- `logging`: Logging system
- `docs`: Documentation
- `ci`: CI/CD

### Examples

**Good Commits:**

```
feat(token): add token validation with JWT verification

Implement JWT signature validation for enhanced security.
Uses PyJWT library to validate tokens from Azure and Keycloak.

Fixes #42
```

```
fix(config): handle missing optional fields gracefully

Previously crashed when VerifySSL was not in config.
Now defaults to true for security.

Fixes #56
```

```
docs: add troubleshooting guide for Azure setup

Include common errors and solutions:
- Invalid scope format
- Incorrect tenant ID
- SSL verification issues
```

```
chore: update dependencies to latest versions

- requests 2.31.0 → 2.32.0
- pytest 7.4.0 → 7.4.3
- No breaking changes

Dependabot PR #123
```

**Bad Commits:**

```
❌ fix stuff
❌ WIP
❌ asdf
❌ Fixed the bug
❌ Updated files
```

### Subject Line Rules

1. **Use imperative mood**: "add feature" not "added feature"
2. **No period** at the end
3. **50 characters or less**
4. **Capitalize first letter**
5. **Be specific**: Say what changed, not that something changed

### Body Guidelines

1. **72 characters per line** (wrap text)
2. **Explain WHY**, not what (code shows what)
3. **Include context** for future developers
4. **Reference issues**: Fixes #123, Closes #456
5. **List breaking changes** if any

### Footer

```
Fixes #123
Closes #456
Related to #789

BREAKING CHANGE: Configuration field renamed from X to Y

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## Co-Authorship

When pair programming or accepting AI assistance:

```
git commit -m "feat: implement new feature

<description>

Co-Authored-By: Developer Name <developer@example.com>
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Note:** All commits written with AI assistance should include Claude as co-author for transparency.

## Pull Requests

### Before Creating PR

- [ ] All tests pass locally
- [ ] Coverage meets 77% threshold
- [ ] Pre-commit hooks pass
- [ ] No secrets in code
- [ ] Branch is up to date with main
- [ ] Commits are clean and logical

### PR Title

Use same format as commit messages:

```
feat(token): add JWT signature validation
fix(config): handle missing optional fields
docs: add API reference documentation
```

### PR Description

Use the template in `.github/PULL_REQUEST_TEMPLATE.md`:

1. **Description**: What and why
2. **Type of change**: Feature, fix, etc.
3. **Testing**: What you tested
4. **Security**: Any security implications
5. **Documentation**: What docs updated
6. **Checklist**: Ensure all items checked

### Review Process

1. **Self-review first**: Check your own code
2. **Request review**: At least one reviewer
3. **Address feedback**: Respond to all comments
4. **Update as needed**: Push new commits or fixups
5. **Squash if messy**: Clean up commit history
6. **Merge when approved**: Use appropriate merge strategy

### Merge Strategies

**Squash and Merge** (Recommended for most PRs)
- Condenses multiple commits into one
- Keeps main branch clean
- Good for feature branches with many WIP commits

```
git merge --squash feature/new-feature
```

**Merge Commit** (For release branches)
- Preserves all individual commits
- Maintains full history
- Good for important milestones

```
git merge --no-ff feature/new-feature
```

**Rebase and Merge** (For clean linear history)
- Replays commits on top of main
- No merge commit created
- Good for small, clean PRs

```
git rebase main
git merge --ff-only feature/new-feature
```

## Commit Signing (GPG)

### Why Sign Commits?

- **Verification**: Prove you wrote the commit
- **Security**: Prevent impersonation
- **Trust**: Show commits are authentic
- **Compliance**: Some orgs require signed commits

### Setup GPG Signing

```bash
# Generate GPG key
gpg --full-generate-key

# List keys
gpg --list-secret-keys --keyid-format=long

# Get key ID (after sec rsa4096/)
# Example: sec rsa4096/ABC123DEF456 -> key ID is ABC123DEF456

# Configure Git
git config --global user.signingkey ABC123DEF456
git config --global commit.gpgsign true

# Add GPG key to GitHub
gpg --armor --export ABC123DEF456
# Paste into GitHub Settings > SSH and GPG keys
```

### Signing Commits

```bash
# Automatic (if commit.gpgsign = true)
git commit -m "feat: add feature"

# Manual
git commit -S -m "feat: add feature"

# Verify signature
git log --show-signature
```

### Troubleshooting GPG

```bash
# "Failed to sign the data"
export GPG_TTY=$(tty)

# Add to ~/.bashrc or ~/.zshrc
echo 'export GPG_TTY=$(tty)' >> ~/.zshrc
```

## Branch Protection Rules

### Recommended Settings for Main Branch

**On GitHub:**
1. Go to Settings > Branches > Branch protection rules
2. Add rule for `main` branch

**Enable:**
- [x] Require pull request reviews before merging (1+ approver)
- [x] Dismiss stale reviews when new commits are pushed
- [x] Require status checks to pass before merging
  - [x] CI / test
  - [x] CI / lint
  - [x] CI / security
- [x] Require branches to be up to date before merging
- [x] Require signed commits (optional but recommended)
- [x] Include administrators (enforce rules for everyone)
- [x] Restrict who can push to matching branches (optional)

## Workflow Examples

### Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/add-okta-support

# 2. Make changes and commit frequently
git add src/oauth_providers/okta.py
git commit -m "feat(providers): add Okta OAuth provider

Implement OktaOAuthProvider class with:
- Custom token endpoint handling
- Okta-specific error handling
- Domain validation

Relates to #67"

# 3. Keep branch updated
git fetch origin
git rebase origin/main

# 4. Push to remote
git push origin feature/add-okta-support

# 5. Create PR on GitHub
# 6. Address review feedback
# 7. Merge when approved
# 8. Delete branch
git branch -d feature/add-okta-support
```

### Bug Fix

```bash
# 1. Create bugfix branch from main
git checkout main
git pull origin main
git checkout -b bugfix/token-refresh-race

# 2. Fix the bug with test
git add src/token_manager.py tests/test_token_manager.py
git commit -m "fix(token): prevent race condition in token refresh

Added lock scope around expiration check to prevent
multiple threads from refreshing token simultaneously.

Fixes #89"

# 3. Push and PR
git push origin bugfix/token-refresh-race

# 4. Merge when reviewed
```

### Hotfix (Critical Production Bug)

```bash
# 1. Branch from main (or production tag)
git checkout main
git checkout -b hotfix/critical-security-CVE-2024-1234

# 2. Fix immediately
git add src/token_manager.py
git commit -m "security(token): fix token validation bypass

CVE-2024-1234: Tokens were not validated in certain conditions.
Now all tokens are validated before use.

CRITICAL: Deploy immediately
Fixes #999"

# 3. PR with URGENT label
# 4. Fast-track review (security team)
# 5. Merge and deploy
# 6. Tag release
git tag -a v2.0.1 -m "Security hotfix for CVE-2024-1234"
git push origin v2.0.1
```

## Best Practices

### DO

✅ Commit frequently (logical units)
✅ Write clear commit messages
✅ Test before committing
✅ Keep branches short-lived (< 2 weeks)
✅ Rebase on main regularly
✅ Sign commits with GPG
✅ Include issue references
✅ Document breaking changes
✅ Co-author when collaborating

### DON'T

❌ Commit broken code
❌ Mix unrelated changes
❌ Use "WIP" or "fix" as messages
❌ Commit secrets or tokens
❌ Force push to shared branches
❌ Let branches get stale
❌ Skip CI checks
❌ Merge without review

## Tools

### Pre-commit Hooks

Already configured in `.pre-commit-config.yaml`:

- Black (code formatting)
- isort (import sorting)
- flake8 (linting)
- mypy (type checking)
- bandit (security)

### Commit Message Validation

Optional: Use commitlint to enforce conventional commits

```bash
npm install -g @commitlint/cli @commitlint/config-conventional
```

### GitHub CLI

```bash
# Create PR from command line
gh pr create --fill

# View PR status
gh pr status

# Checkout PR for review
gh pr checkout 123
```

## Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Commit Best Practices](https://chris.beams.io/posts/git-commit/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Signing Commits](https://docs.github.com/en/authentication/managing-commit-signature-verification)
