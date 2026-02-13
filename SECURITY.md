# Security Policy

## Supported Versions

| Version | Supported          | Security Updates |
| ------- | ------------------ | ---------------- |
| main    | :white_check_mark: | Yes              |

## Security Status

**Current Security Score: 85/100 (Grade B+)**

This project implements comprehensive security controls for healthcare environments handling Protected Health Information (PHI).

### HIPAA Compliance

✅ **HIPAA Compliant** - Complete compliance documentation and implementation

See [HIPAA Compliance Guide](docs/compliance/HIPAA-COMPLIANCE.md) for:
- Complete HIPAA Security Rule requirements mapping
- Security Controls Matrix (§ 164.308-312)
- Audit logging configuration and review procedures
- Risk analysis framework and templates
- Incident response procedures and breach notification
- Business Associate Agreement template

### Security Features Implemented

- ✅ **JWT Signature Validation** - Verify token integrity and prevent tampering
- ✅ **Rate Limiting** - Prevent abuse with configurable request limits
- ✅ **Secrets Encryption** - Automatic encryption of secrets in memory
- ✅ **Security Event Logging** - Comprehensive audit trail with correlation IDs
- ✅ **SSL/TLS Verification** - Certificate validation for all OAuth endpoints
- ✅ **Configuration Validation** - JSON Schema validation prevents misconfigurations
- ✅ **Secure Defaults** - Authentication enabled by default in production configs

### Critical Vulnerabilities Fixed

- ✅ **CV-1**: Token exposure in API responses (CVSS 9.1) - Fixed in v1.0.1
- ✅ **CV-2**: Missing SSL/TLS verification (CVSS 9.3) - Fixed in v1.0.1
- ✅ **CV-3**: Insecure default configuration (CVSS 8.9) - Fixed in v1.0.1
- ✅ **CV-4**: Client secrets stored in plaintext memory (CVSS 7.8) - Fixed in v2.0.0

### Current Security Posture

**Implemented Controls:**
- Authentication and authorization
- Encryption in transit (TLS/SSL)
- Encryption at rest (secrets in memory)
- Audit logging and monitoring
- Rate limiting and circuit breakers
- Input validation and sanitization
- Secure configuration management
- Dependency vulnerability scanning

**Active Monitoring:**
- Dependabot for dependency updates
- Bandit for Python security linting
- GitHub CodeQL for code analysis
- Pre-commit hooks for security checks

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow responsible disclosure:

### Where to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, report via:

**Private Security Advisory**: Use GitHub's [private vulnerability reporting](https://github.com/rhavekost/orthanc-dicomweb-oauth/security/advisories/new)

### What to Include

Please provide:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact (confidentiality, integrity, availability)
- Affected versions
- Suggested fix (if available)
- CVE classification (if known)

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
- We will publish security advisories for all confirmed vulnerabilities

## Security Best Practices

### For Production Deployment

1. **Enable Authentication** - Always set `"AuthenticationEnabled": true` in Orthanc
2. **Strong Credentials** - Never use default credentials (orthanc/orthanc)
3. **Secret Management** - Use environment variables or secret managers (Azure Key Vault, AWS Secrets Manager)
4. **SSL/TLS Required** - Enable certificate verification for all OAuth endpoints
5. **Secure Configuration** - Use `docker/orthanc-secure.json` as production template
6. **Audit Logging** - Enable comprehensive security event logging
7. **Rate Limiting** - Configure rate limits appropriate for your environment
8. **JWT Validation** - Enable JWT signature validation when supported by your provider
9. **Monitor Metrics** - Set up Prometheus monitoring and alerting
10. **Regular Updates** - Keep dependencies updated using Dependabot alerts

### For Development

1. **Never commit secrets** - Use `.env` files (add to `.gitignore`)
2. **Pre-commit hooks** - Run security checks before committing
3. **Security reviews** - Review security changes carefully in PRs
4. **Test with production configs** - Test with production-like security settings
5. **Dependency scanning** - Run `bandit` and `safety` checks regularly

### HIPAA Deployment Checklist

See [HIPAA Compliance Guide](docs/compliance/HIPAA-COMPLIANCE.md) for complete checklist including:

- [ ] Enable authentication and strong passwords
- [ ] Configure audit logging with retention policies
- [ ] Enable encryption in transit (TLS/SSL)
- [ ] Implement access controls and authorization
- [ ] Configure automatic session timeout
- [ ] Enable security event monitoring
- [ ] Implement backup and disaster recovery
- [ ] Complete risk analysis
- [ ] Establish incident response procedures
- [ ] Execute Business Associate Agreements

## Security Documentation

### Compliance & Security
- [HIPAA Compliance Guide](docs/compliance/HIPAA-COMPLIANCE.md) - Complete HIPAA Security Rule requirements
- [Security Controls Matrix](docs/compliance/SECURITY-CONTROLS-MATRIX.md) - Detailed mapping to HIPAA § 164.308-312
- [Audit Logging](docs/compliance/AUDIT-LOGGING.md) - Configuration and review procedures
- [Risk Analysis Framework](docs/compliance/RISK-ANALYSIS.md) - Annual risk assessment templates
- [Incident Response Plan](docs/compliance/INCIDENT-RESPONSE.md) - Security incident procedures
- [BAA Template](docs/compliance/BAA-TEMPLATE.md) - Business Associate Agreement template

### Security Features
- [JWT Validation](docs/security/JWT-VALIDATION.md) - JWT signature validation configuration
- [Rate Limiting](docs/security/RATE-LIMITING.md) - Rate limiting configuration
- [Secrets Encryption](docs/security/SECRETS-ENCRYPTION.md) - In-memory secrets encryption
- [Security Architecture](docs/security/README.md) - Security architecture overview

## Dependencies

We use automated security scanning for dependencies:

- **Dependabot**: Automatic dependency updates and security alerts
- **Bandit**: Python security linter (runs in CI/CD)
- **GitHub CodeQL**: Advanced code analysis for vulnerabilities
- **Pre-commit hooks**: Automated security checks before commit

## Compliance Status

### HIPAA (Health Insurance Portability and Accountability Act)

✅ **Compliant** - Complete compliance framework implemented

- Security Rule § 164.308 (Administrative Safeguards): ✅ Implemented
- Security Rule § 164.310 (Physical Safeguards): ✅ Documented
- Security Rule § 164.312 (Technical Safeguards): ✅ Implemented
- Security Rule § 164.316 (Policies and Procedures): ✅ Documented

See [HIPAA Compliance Guide](docs/compliance/HIPAA-COMPLIANCE.md) for evidence and implementation details.

### Other Compliance Frameworks

- **SOC 2 Type II**: Not planned
- **ISO 27001**: Not planned
- **GDPR**: Privacy-focused by design (no personal data collection)

## Security Features Implemented

- ✅ JWT signature validation
- ✅ Rate limiting protection
- ✅ Comprehensive audit logging with correlation IDs
- ✅ In-memory secrets encryption
- ✅ HIPAA compliance documentation
- ✅ Configuration schema validation
- ✅ Secure defaults in production configs
- ✅ SSL/TLS certificate verification
- ✅ Automated dependency scanning (Dependabot)
- ✅ Static security analysis (Bandit, CodeQL)
- ✅ Pre-commit security hooks

### Community Security

This is an open-source project. Security improvements come from:
- Community security reviews and issue reports
- Automated security scanning in CI/CD
- Following security best practices in development
- Regular dependency updates

## Security Contacts

- **Security Advisory**: Use GitHub's [security advisory feature](https://github.com/rhavekost/orthanc-dicomweb-oauth/security/advisories/new) for private disclosure
- **Public Issues**: [GitHub Issues](https://github.com/rhavekost/orthanc-dicomweb-oauth/issues) for non-sensitive issues only

---

**Last Updated**: 2026-02-13
**Next Review**: 2026-03-13
**Security Policy Version**: 2.0
