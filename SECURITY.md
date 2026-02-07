# Security Policy

## Supported Versions

| Version | Supported          | Security Updates |
| ------- | ------------------ | ---------------- |
| 1.0.x   | :white_check_mark: | Yes              |
| < 1.0   | :x:                | No               |

## Known Security Issues

**Current Security Score: 62/100 (Grade D)**

We are actively working to improve the security posture of this project. See [Comprehensive Project Assessment](docs/comprehensive-project-assessment.md) for details.

### Critical Vulnerabilities Fixed (As of 2026-02-06)

- ✅ **CV-1**: Token exposure in API responses (CVSS 9.1) - Fixed in v1.0.1
- ✅ **CV-2**: Missing SSL/TLS verification (CVSS 9.3) - Fixed in v1.0.1
- ✅ **CV-3**: Insecure default configuration (CVSS 8.9) - Fixed in v1.0.1

### Known Issues (In Progress)

- ⚠️ **CV-4**: Client secrets stored in plaintext memory (CVSS 7.8) - Target: v1.1.0
- ⚠️ No JWT signature validation - Target: v1.1.0
- ⚠️ No rate limiting on token endpoints - Target: v1.1.0
- ⚠️ Insufficient security event logging - Target: v1.2.0

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow responsible disclosure:

### Where to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, report via:

1. **Email**: [Insert security contact email]
2. **Private Security Advisory**: Use GitHub's [private vulnerability reporting](https://github.com/[username]/orthanc-dicomweb-oauth/security/advisories/new)

### What to Include

Please provide:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact (confidentiality, integrity, availability)
- Affected versions
- Suggested fix (if available)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Severity Assessment**: Within 5 business days
- **Fix Timeline**:
  - Critical (CVSS 9.0-10.0): 7 days
  - High (CVSS 7.0-8.9): 30 days
  - Medium (CVSS 4.0-6.9): 90 days
  - Low (CVSS 0.1-3.9): Next release

### Disclosure Policy

- We will confirm receipt of your report within 48 hours
- We will provide regular updates on our progress
- We will credit you in the security advisory (unless you prefer anonymity)
- We request that you do not publicly disclose the issue until we've issued a fix

## Security Best Practices

### For Deployment

1. **Always enable authentication** in Orthanc configuration
2. **Never use default credentials** in production
3. **Store secrets securely** using environment variables or secret managers
4. **Enable SSL/TLS** for all OAuth endpoints
5. **Use secure defaults** from `docker/orthanc-secure.json`
6. **Monitor security logs** for suspicious activity
7. **Keep dependencies updated** using Dependabot alerts

### For Development

1. **Never commit secrets** to version control
2. **Use `.env` files** for local development (add to `.gitignore`)
3. **Review security changes** carefully in PRs
4. **Run security scans** before committing (`pre-commit run --all-files`)
5. **Test with production-like configurations** before deploying

## Security Roadmap

### Immediate (Completed)
- ✅ Remove token exposure from API
- ✅ Enable SSL/TLS verification
- ✅ Secure default configuration
- ✅ Create SECURITY.md

### Short-term (Month 1)
- [ ] Implement JWT signature validation
- [ ] Add rate limiting protection
- [ ] Implement comprehensive audit logging
- [ ] Secure memory for client secrets

### Medium-term (Months 2-3)
- [ ] HIPAA compliance documentation
- [ ] Third-party security audit
- [ ] Penetration testing
- [ ] Security certifications

## Dependencies

We use automated security scanning for dependencies:

- **Dependabot**: Automatic dependency updates
- **Bandit**: Python security linter
- **Safety**: Python dependency security checker

## Compliance

This plugin is being developed for use in healthcare environments with the following compliance goals:

- **HIPAA** (Health Insurance Portability and Accountability Act): Target Month 6
- **SOC 2 Type II**: Target Month 6+

**Current Status**: Not HIPAA compliant. See [Project Assessment](docs/comprehensive-project-assessment.md#5-security-62100--critical-issues) for details.

## Security Contacts

- Security Email: [Insert security contact email]
- Project Maintainer: [Insert maintainer contact]
- Security Advisory: https://github.com/[username]/orthanc-dicomweb-oauth/security/advisories

---

**Last Updated**: 2026-02-06
**Next Review**: 2026-03-06
