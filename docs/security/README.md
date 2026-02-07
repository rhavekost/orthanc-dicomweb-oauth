# Security Documentation

This directory contains security-related documentation for the Orthanc OAuth plugin.

## Overview

The Orthanc OAuth plugin implements enterprise-grade security controls for authenticating and authorizing access to DICOM data via DICOMweb APIs.

## Security Features

### Authentication
- OAuth2/OpenID Connect bearer token authentication
- Support for major identity providers (Azure AD, Google Cloud, AWS IAM)
- JWT signature validation (HMAC-SHA256, RS256)
- Token expiration enforcement
- Issuer and audience validation

### Authorization
- Token-based access control
- Scope-based permissions (read, write, admin)
- Server-specific access control
- Rate limiting (60 requests/minute default)

### Encryption
- TLS 1.2+ required for all connections
- Strong cipher suites (AES-256-GCM, ChaCha20-Poly1305)
- Token encryption in memory (AES-256-GCM)
- Secret encryption (Fernet)
- Certificate validation

### Audit & Monitoring
- Structured audit logging (JSON)
- User identity tracking
- Correlation IDs for request tracing
- Failed authentication logging
- Rate limit violation logging
- Metrics for Prometheus/CloudWatch

### Defense in Depth
- Input validation
- Configuration validation
- Error handling without information disclosure
- Secure defaults
- Principle of least privilege

## Security Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTPS (TLS 1.2+)
       │
┌──────▼────────────────────────────┐
│  Orthanc + OAuth Plugin           │
│  ┌──────────────────────────────┐ │
│  │  1. TLS Termination          │ │
│  │  2. OAuth Token Validation   │ │
│  │  3. Rate Limiting            │ │
│  │  4. Authorization Check      │ │
│  │  5. Audit Logging            │ │
│  └──────────────────────────────┘ │
└──────┬────────────────────────────┘
       │
       ├─► OAuth Provider (Azure AD, Google, AWS)
       ├─► Redis Cache (optional, TLS)
       ├─► Database (PostgreSQL, TLS)
       └─► Log Aggregator (CloudWatch, Azure Monitor, GCP)
```

## Security Documentation

### Core Security Documents

- **[SECURITY.md](../../SECURITY.md)** - Security policy, vulnerability reporting
- **[Threat Model](THREAT-MODEL.md)** - Security threats and mitigations (if exists)
- **[Security Best Practices](SECURITY-BEST-PRACTICES.md)** - Deployment security guidance (if exists)

### Compliance Documentation

For healthcare deployments and HIPAA compliance:

- **[HIPAA Compliance Guide](../compliance/HIPAA-COMPLIANCE.md)** - Complete HIPAA compliance overview
- **[Security Controls Matrix](../compliance/SECURITY-CONTROLS-MATRIX.md)** - Mapping to HIPAA requirements
- **[Audit Logging Guide](../compliance/AUDIT-LOGGING.md)** - HIPAA audit logging requirements
- **[Risk Analysis Framework](../compliance/RISK-ANALYSIS.md)** - Annual risk assessment process
- **[Incident Response Plan](../compliance/INCIDENT-RESPONSE.md)** - Security incident procedures
- **[Business Associate Agreement Template](../compliance/BAA-TEMPLATE.md)** - BAA for vendors

See [docs/compliance/](../compliance/) for complete compliance documentation.

## Security Best Practices

### Deployment

1. **Always use TLS 1.2 or higher**
   - Configure strong cipher suites
   - Use valid certificates from trusted CA
   - Enable HSTS (HTTP Strict Transport Security)

2. **Enable MFA in OAuth Provider**
   - Azure AD: Conditional Access policies
   - Google: 2-Step Verification
   - AWS: MFA enforcement

3. **Use Strong Token Configuration**
   - Token lifetime: 3600 seconds (1 hour)
   - Enable signature validation
   - Enable expiration checking
   - Enable issuer validation
   - Enable audience validation

4. **Enable Audit Logging**
   - Log all authentication events
   - Include user identity in logs
   - Ship logs to centralized SIEM
   - Retain logs for 6-7 years (HIPAA)

5. **Network Security**
   - Deploy in private VPC/VNET
   - Use security groups to restrict access
   - Enable Web Application Firewall (WAF)
   - Use VPN or private connectivity for admin access

6. **Data Protection**
   - Enable encryption at rest (EBS, RDS, S3)
   - Encrypt backups
   - Use secure key management (KMS, Key Vault, HSM)
   - Implement data retention policies

7. **Monitoring**
   - Enable real-time alerting
   - Monitor failed authentication attempts
   - Monitor rate limit violations
   - Track cache hit rates
   - Monitor token validation errors

### Development

1. **Secure Coding**
   - Input validation on all external data
   - Use parameterized queries (SQL injection prevention)
   - Avoid eval() and exec()
   - Use safe deserialization
   - Handle errors without exposing internals

2. **Dependency Management**
   - Keep dependencies up to date
   - Scan for known vulnerabilities (Dependabot, Snyk)
   - Pin dependency versions
   - Review license compatibility

3. **Testing**
   - Security unit tests
   - Integration tests with invalid tokens
   - Penetration testing (annual)
   - Vulnerability scanning

4. **Code Review**
   - Security-focused code review
   - Static analysis (Bandit, SonarQube)
   - Peer review before merge

## Common Security Issues and Solutions

### Issue: Token Validation Failing

**Symptoms:**
- HTTP 401 Unauthorized
- Log: TOKEN_VALIDATION_FAILED

**Possible Causes:**
- Expired token
- Invalid signature
- Wrong issuer
- Clock skew

**Solutions:**
```bash
# 1. Check token expiration
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq '.exp'

# 2. Verify signature algorithm
echo $TOKEN | cut -d'.' -f1 | base64 -d | jq '.alg'

# 3. Check issuer
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq '.iss'

# 4. Verify time sync
ntpq -p
```

### Issue: Rate Limiting Triggered

**Symptoms:**
- HTTP 429 Too Many Requests
- Log: RATE_LIMIT_EXCEEDED

**Solutions:**
- Increase rate limit if legitimate traffic
- Implement token caching on client side
- Investigate if attack (block IP if malicious)
- Use distributed caching (Redis) to share limits across instances

### Issue: TLS Connection Fails

**Symptoms:**
- SSL handshake failure
- Certificate validation error

**Solutions:**
```bash
# 1. Verify TLS version
openssl s_client -connect server:8042 -tls1_2

# 2. Check certificate validity
openssl s_client -connect server:8042 -showcerts

# 3. Verify certificate chain
curl -v https://server:8042

# 4. Check system CA certificates
ls /etc/ssl/certs/
```

## Security Reporting

**Found a security vulnerability?**

Please report security issues responsibly:

1. **Do NOT** create public GitHub issues for security vulnerabilities
2. Email: security@example.com
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

We will respond within 48 hours and work with you to address the issue.

## Security Metrics

Track these security metrics:

**Authentication:**
- Failed authentication attempts
- Successful authentications
- Average authentication latency
- Token validation success rate

**Authorization:**
- Authorization failures
- Rate limit violations
- Unusual access patterns

**Encryption:**
- TLS version usage (should be 100% TLS 1.2+)
- Cipher suite usage
- Certificate expiration dates

**Audit:**
- Audit log volume
- Log shipping lag
- Log retention compliance

## Security Checklist

Use this checklist for production deployments:

### Pre-Deployment

- [ ] TLS 1.2+ configured
- [ ] Valid certificate from trusted CA
- [ ] OAuth provider configured with MFA
- [ ] Token validation enabled (signature, expiration, issuer)
- [ ] Rate limiting configured
- [ ] Audit logging enabled
- [ ] Log retention configured (6-7 years)
- [ ] Secrets encrypted (not in plaintext config)
- [ ] Network security groups configured
- [ ] Firewall rules restrict inbound access

### Post-Deployment

- [ ] Verify TLS connection works
- [ ] Verify OAuth authentication works
- [ ] Verify token validation works
- [ ] Verify rate limiting works
- [ ] Verify audit logs are generated
- [ ] Verify logs shipped to SIEM
- [ ] Verify monitoring alerts work
- [ ] Conduct security testing
- [ ] Document configuration
- [ ] Train operations team

### Ongoing

- [ ] Weekly audit log review
- [ ] Quarterly access review
- [ ] Annual penetration testing
- [ ] Annual vulnerability scanning
- [ ] Patch management (monthly)
- [ ] Certificate renewal (before expiration)
- [ ] Dependency updates (monthly)

## References

**OWASP:**
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

**Standards:**
- [OAuth 2.0 RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)
- [JWT RFC 7519](https://datatracker.ietf.org/doc/html/rfc7519)
- [TLS 1.3 RFC 8446](https://datatracker.ietf.org/doc/html/rfc8446)

**NIST:**
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [NIST SP 800-53: Security Controls](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [NIST SP 800-63B: Digital Identity Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)

**Cloud Security:**
- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)
- [Azure Security Best Practices](https://learn.microsoft.com/en-us/azure/security/fundamentals/best-practices-and-patterns)
- [GCP Security Best Practices](https://cloud.google.com/security/best-practices)

## License

Copyright © 2026. All rights reserved.
