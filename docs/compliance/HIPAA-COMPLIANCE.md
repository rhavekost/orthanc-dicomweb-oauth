# HIPAA Compliance Guide

This document provides guidance on using the Orthanc OAuth plugin in HIPAA-regulated environments.

## Compliance Status

**Current Status:** ✅ **Technical Controls Implemented**

The plugin implements required technical safeguards per HIPAA Security Rule. However, HIPAA compliance requires organizational policies and procedures beyond technical controls.

## HIPAA Security Rule Requirements

### § 164.312(a)(1) - Access Control

**Required:** Technical controls to allow only authorized access to ePHI.

**Implementation:**
- ✅ OAuth2 authentication required for all DICOMweb access
- ✅ Token-based access control with expiration
- ✅ Support for Azure AD, Google Cloud, AWS IAM
- ✅ Automatic token refresh and validation
- ✅ Rate limiting to prevent brute force attacks

**Configuration:**
```json
{
  "OAuth": {
    "Enabled": true,
    "AuthenticationRequired": true,
    "TokenValidation": {
      "ValidateSignature": true,
      "ValidateExpiration": true,
      "ValidateIssuer": true
    }
  }
}
```

### § 164.312(a)(2)(i) - Unique User Identification

**Required:** Assign unique identifiers to authorized users.

**Implementation:**
- ✅ OAuth providers enforce unique user identifiers
- ✅ User identity passed in JWT claims (sub, email, upn)
- ✅ Audit logs include user identifier
- ✅ No shared credentials

**Verification:**
```bash
# Check JWT claims include user ID
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8042/plugins/oauth/validate | jq '.claims.sub'
```

### § 164.312(a)(2)(ii) - Emergency Access Procedure

**Required:** Procedures for obtaining ePHI during emergency.

**Implementation:**
- ⚠️ **Organization Responsibility:** Define emergency access procedures
- ✅ Plugin supports emergency break-glass accounts via OAuth provider
- ✅ All access logged for audit review

**Recommended Procedure:**
1. Create emergency access account in OAuth provider
2. Configure MFA requirement for emergency account
3. Document approval process for emergency access
4. Review emergency access logs within 24 hours

### § 164.312(a)(2)(iii) - Automatic Logoff

**Required:** Terminate session after predetermined inactivity period.

**Implementation:**
- ✅ OAuth tokens expire after configurable period
- ✅ Default token lifetime: 3600 seconds (1 hour)
- ✅ No automatic renewal without re-authentication

**Configuration:**
```json
{
  "OAuth": {
    "TokenLifetime": 3600,
    "RequireReauthentication": true
  }
}
```

### § 164.312(a)(2)(iv) - Encryption and Decryption

**Required:** Implement mechanism to encrypt/decrypt ePHI.

**Implementation:**
- ✅ TLS 1.2+ required for all connections
- ✅ OAuth tokens encrypted in memory (AES-256-GCM)
- ✅ Secrets encrypted using Fernet encryption
- ✅ No plaintext credentials in logs

**Verification:**
```bash
# Verify TLS 1.2+ enforcement
openssl s_client -connect localhost:8042 -tls1_1
# Should fail with error

openssl s_client -connect localhost:8042 -tls1_2
# Should succeed
```

### § 164.312(b) - Audit Controls

**Required:** Hardware, software, procedures to record and examine activity.

**Implementation:**
- ✅ Structured audit logging with correlation IDs
- ✅ All OAuth events logged (authentication, authorization, errors)
- ✅ User identity included in logs
- ✅ Timestamp and action logged
- ✅ Log integrity protection (append-only)

**Log Format:**
```json
{
  "timestamp": "2026-02-07T10:30:00Z",
  "level": "INFO",
  "correlation_id": "abc123",
  "user_id": "user@example.com",
  "action": "TOKEN_ACQUIRED",
  "server": "azure-dicomweb",
  "result": "SUCCESS"
}
```

**See:** [AUDIT-LOGGING.md](AUDIT-LOGGING.md) for complete audit logging guide.

### § 164.312(c)(1) - Integrity

**Required:** Implement policies to ensure ePHI is not improperly altered or destroyed.

**Implementation:**
- ✅ JWT signature validation prevents token tampering
- ✅ Configuration validation prevents invalid settings
- ✅ Audit logs detect unauthorized access attempts
- ⚠️ **Organization Responsibility:** Implement backup procedures

**Verification:**
```bash
# Test tampered token detection
curl -H "Authorization: Bearer tampered_token" \
  http://localhost:8042/dicom-web/studies
# Should return 401 Unauthorized
```

### § 164.312(d) - Person or Entity Authentication

**Required:** Verify person or entity seeking access is authorized.

**Implementation:**
- ✅ OAuth2 bearer token authentication
- ✅ JWT signature validation
- ✅ Token expiration enforcement
- ✅ Issuer validation
- ✅ Audience validation

**Authentication Flow:**
```
1. User requests token from OAuth provider
2. OAuth provider authenticates user (MFA supported)
3. OAuth provider issues signed JWT
4. Plugin validates JWT signature, expiration, claims
5. Plugin allows/denies access
```

### § 164.312(e)(1) - Transmission Security

**Required:** Implement technical security measures to guard against unauthorized access.

**Implementation:**
- ✅ TLS 1.2+ enforced for all HTTP traffic
- ✅ Certificate validation enabled
- ✅ OAuth tokens transmitted only over HTTPS
- ✅ No credentials in URL parameters
- ✅ Secure token storage (encrypted memory)

## Organizational Requirements

While the plugin provides technical controls, HIPAA compliance also requires:

### 1. Business Associate Agreement (BAA)

**Required:** Signed BAA with all business associates handling ePHI.

**Action Items:**
- [ ] Sign BAA with cloud provider (AWS/Azure/GCP)
- [ ] Sign BAA with OAuth provider (Azure AD/Google)
- [ ] Document all business associate relationships

**Template:** See [BAA-TEMPLATE.md](BAA-TEMPLATE.md)

### 2. Risk Analysis

**Required:** Regular assessment of security risks to ePHI.

**Action Items:**
- [ ] Conduct annual risk analysis
- [ ] Document identified risks
- [ ] Implement risk mitigation measures
- [ ] Review and update based on changes

**Template:** See [RISK-ANALYSIS.md](RISK-ANALYSIS.md)

### 3. Security Policies and Procedures

**Required:** Written policies covering all HIPAA requirements.

**Action Items:**
- [ ] Access control policy
- [ ] Audit and monitoring policy
- [ ] Incident response plan
- [ ] Disaster recovery plan
- [ ] Security awareness training

### 4. Workforce Training

**Required:** Train all workforce members on security policies.

**Action Items:**
- [ ] Initial security training for new employees
- [ ] Annual refresher training
- [ ] Document training completion
- [ ] Test understanding of policies

### 5. Incident Response

**Required:** Identify and respond to security incidents.

**Action Items:**
- [ ] Define incident response procedures
- [ ] Designate incident response team
- [ ] Document incidents and response
- [ ] Report breaches per HIPAA Breach Notification Rule

**Template:** See [INCIDENT-RESPONSE.md](INCIDENT-RESPONSE.md)

## Security Controls Matrix

See [SECURITY-CONTROLS-MATRIX.md](SECURITY-CONTROLS-MATRIX.md) for complete mapping of plugin features to HIPAA requirements.

## Compliance Checklist

### Technical Controls (Plugin Features)

- [x] Access control with OAuth2 authentication
- [x] Unique user identification via OAuth claims
- [x] Automatic logoff (token expiration)
- [x] Encryption in transit (TLS 1.2+)
- [x] Encryption at rest (memory encryption)
- [x] Audit logging with user identity
- [x] JWT signature validation (integrity)
- [x] Person/entity authentication
- [x] Rate limiting (brute force protection)
- [x] Secure configuration validation

### Organizational Controls (Your Responsibility)

- [ ] Business Associate Agreements signed
- [ ] Risk analysis conducted and documented
- [ ] Security policies and procedures written
- [ ] Workforce training completed
- [ ] Incident response plan established
- [ ] Disaster recovery plan documented
- [ ] Regular security reviews scheduled
- [ ] Audit log review procedures
- [ ] Emergency access procedures
- [ ] Backup and recovery procedures

## Deployment Recommendations

### HIPAA-Ready Configuration

```json
{
  "OAuth": {
    "Enabled": true,
    "TokenValidation": {
      "ValidateSignature": true,
      "ValidateExpiration": true,
      "ValidateIssuer": true,
      "ValidateAudience": true
    },
    "TokenLifetime": 3600,
    "RequireHTTPS": true,
    "RateLimiting": {
      "Enabled": true,
      "RequestsPerMinute": 60
    },
    "AuditLogging": {
      "Enabled": true,
      "IncludeUserIdentity": true,
      "LogLevel": "INFO"
    }
  }
}
```

### Infrastructure Requirements

1. **Network Security:**
   - Private VPC/VNET for Orthanc instances
   - Security groups restricting inbound access
   - VPN or private connectivity for admin access
   - Web Application Firewall (WAF) for public endpoints

2. **Data Protection:**
   - Encrypted storage volumes (BitLocker, LUKS, etc.)
   - Encrypted backups
   - Secure key management (HSM, Key Vault, KMS)
   - Data retention and destruction policies

3. **Monitoring:**
   - Centralized log aggregation (ELK, Splunk, CloudWatch)
   - Real-time alerting on security events
   - Regular log review and analysis
   - Intrusion detection system (IDS)

4. **Backup and Recovery:**
   - Automated daily backups
   - Encrypted backup storage
   - Tested recovery procedures
   - Offsite backup retention

## Third-Party Audits

For full HIPAA compliance certification:

1. **Hire HIPAA compliance consultant** ($15k-$30k)
   - Gap analysis
   - Policy development
   - Training development

2. **Conduct security assessment** ($20k-$50k)
   - Penetration testing
   - Vulnerability assessment
   - Security controls review

3. **Annual compliance review** ($10k-$20k)
   - Policy review and updates
   - Staff training verification
   - Technical controls testing

## Attestation of Compliance

This plugin provides **technical safeguards** required by the HIPAA Security Rule. However, HIPAA compliance is **not solely a technical achievement** - it requires organizational policies, procedures, training, and documentation.

**Statement:**
> The Orthanc OAuth Plugin implements technical controls in accordance with the HIPAA Security Rule § 164.312. Organizations using this plugin in HIPAA-regulated environments must implement additional organizational safeguards including policies, procedures, workforce training, business associate agreements, risk analysis, and incident response plans.

## Support

For HIPAA compliance consulting or technical support:
- Email: support@example.com
- Documentation: https://github.com/rhavekost/orthanc-dicomweb-oauth
- Security issues: security@example.com

## References

- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [HIPAA Breach Notification Rule](https://www.hhs.gov/hipaa/for-professionals/breach-notification/index.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [HITRUST CSF](https://hitrustalliance.net/hitrust-csf/)
