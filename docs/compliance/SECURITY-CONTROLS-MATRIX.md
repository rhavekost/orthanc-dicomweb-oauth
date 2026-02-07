# HIPAA Security Controls Matrix

This document maps Orthanc OAuth plugin features to HIPAA Security Rule requirements.

## Overview

The HIPAA Security Rule (45 CFR Part 164, Subpart C) establishes national standards to protect electronic protected health information (ePHI). It requires administrative, physical, and technical safeguards.

**Legend:**
- ✅ **Implemented** - Control is fully implemented by plugin
- ⚠️ **Partial** - Control is partially implemented, additional configuration required
- 🔧 **Configuration** - Control requires customer configuration
- 📋 **Policy** - Control requires organizational policy/procedure
- ❌ **Not Applicable** - Control not applicable to plugin

## Administrative Safeguards (§ 164.308)

| Standard | Implementation Spec | Required (R) / Addressable (A) | Plugin Implementation | Status | Notes |
|----------|-------------------|-------------------------------|---------------------|--------|-------|
| **§ 164.308(a)(1) - Security Management Process** | | | | | |
| | (i) Risk Analysis | R | Not provided by plugin | 📋 | See [RISK-ANALYSIS.md](RISK-ANALYSIS.md) |
| | (ii) Risk Management | R | Not provided by plugin | 📋 | Organization responsibility |
| | (iii) Sanction Policy | R | Not provided by plugin | 📋 | Organization responsibility |
| | (iv) Information System Activity Review | R | Audit logging capabilities provided | ⚠️ | Logging tools provided, review process is organizational |
| **§ 164.308(a)(2) - Assigned Security Responsibility** | | R | Not provided by plugin | 📋 | Organization responsibility |
| **§ 164.308(a)(3) - Workforce Security** | | | | | |
| | (i) Authorization and/or Supervision | A | OAuth provider manages users | ⚠️ | Leverage OAuth provider's user management |
| | (ii) Workforce Clearance Procedure | A | Not provided by plugin | 📋 | Organization responsibility |
| | (iii) Termination Procedures | A | OAuth provider manages access revocation | ⚠️ | Disable user in OAuth provider to revoke access |
| **§ 164.308(a)(4) - Information Access Management** | | | | | |
| | (i) Isolating Health Care Clearinghouse Functions | R | Not applicable | ❌ | Not a clearinghouse |
| | (ii) Access Authorization | A | OAuth2 authentication required | ✅ | All DICOMweb access requires valid OAuth token |
| | (iii) Access Establishment and Modification | A | OAuth provider manages authorization | 🔧 | Configure OAuth provider roles/groups |
| **§ 164.308(a)(5) - Security Awareness and Training** | | | | | |
| | (i) Security Reminders | A | Not provided by plugin | 📋 | Organization responsibility |
| | (ii) Protection from Malicious Software | A | OS/infrastructure responsibility | 🔧 | Deploy antivirus, EDR on hosts |
| | (iii) Log-in Monitoring | A | Failed login attempts logged | ✅ | Audit logs include authentication failures |
| | (iv) Password Management | A | OAuth provider manages passwords | ⚠️ | Enforce strong passwords in OAuth provider |
| **§ 164.308(a)(6) - Security Incident Procedures** | | | | | |
| | (i) Response and Reporting | R | Not provided by plugin | 📋 | See [INCIDENT-RESPONSE.md](INCIDENT-RESPONSE.md) |
| **§ 164.308(a)(7) - Contingency Plan** | | | | | |
| | (i) Data Backup Plan | R | Not provided by plugin | 🔧 | Configure automated backups (EBS snapshots, RDS backups) |
| | (ii) Disaster Recovery Plan | R | Not provided by plugin | 📋 | Organization responsibility |
| | (iii) Emergency Mode Operation Plan | R | Not provided by plugin | 📋 | Define emergency access procedures |
| | (iv) Testing and Revision Procedures | A | Not provided by plugin | 📋 | Test DR plan annually |
| | (v) Applications and Data Criticality Analysis | A | Not provided by plugin | 📋 | Organization responsibility |
| **§ 164.308(a)(8) - Evaluation** | | R | Not provided by plugin | 📋 | Conduct annual compliance evaluation |
| **§ 164.308(b)(1) - Business Associate Contracts** | | R | Not provided by plugin | 📋 | See [BAA-TEMPLATE.md](BAA-TEMPLATE.md) |

## Physical Safeguards (§ 164.310)

| Standard | Implementation Spec | Required (R) / Addressable (A) | Plugin Implementation | Status | Notes |
|----------|-------------------|-------------------------------|---------------------|--------|-------|
| **§ 164.310(a)(1) - Facility Access Controls** | | | | | |
| | (i) Contingency Operations | A | Not applicable (cloud-based) | 🔧 | Cloud provider responsibility |
| | (ii) Facility Security Plan | A | Not applicable (cloud-based) | 🔧 | Cloud provider datacenter security |
| | (iii) Access Control and Validation Procedures | A | Not applicable (cloud-based) | 🔧 | Cloud provider datacenter access |
| | (iv) Maintenance Records | A | Not applicable (cloud-based) | 🔧 | Cloud provider maintenance tracking |
| **§ 164.310(b) - Workstation Use** | | R | Not provided by plugin | 📋 | Define acceptable use policy |
| **§ 164.310(c) - Workstation Security** | | R | Not provided by plugin | 📋 | Secure admin workstations |
| **§ 164.310(d)(1) - Device and Media Controls** | | | | | |
| | (i) Disposal | R | Not provided by plugin | 🔧 | Securely delete EBS volumes, wipe decommissioned hardware |
| | (ii) Media Re-use | R | Not provided by plugin | 🔧 | Encrypt volumes, zero-fill before reuse |
| | (iii) Accountability | A | Not provided by plugin | 📋 | Track media containing ePHI |
| | (iv) Data Backup and Storage | A | Not provided by plugin | 🔧 | Configure encrypted backups (S3, Azure Blob) |

## Technical Safeguards (§ 164.312)

| Standard | Implementation Spec | Required (R) / Addressable (A) | Plugin Implementation | Status | Notes |
|----------|-------------------|-------------------------------|---------------------|--------|-------|
| **§ 164.312(a)(1) - Access Control** | | | | | |
| | (i) Unique User Identification | R | OAuth provider enforces unique identifiers | ✅ | User identity in JWT claims (sub, email, upn) |
| | (ii) Emergency Access Procedure | R | Emergency accounts via OAuth provider | ⚠️ | Create break-glass account in OAuth provider |
| | (iii) Automatic Logoff | A | Token expiration (default 3600s) | ✅ | Tokens expire automatically |
| | (iv) Encryption and Decryption | A | TLS 1.2+, memory encryption | ✅ | All network traffic encrypted, tokens encrypted in memory |
| **§ 164.312(b) - Audit Controls** | | R | Structured audit logging | ✅ | All OAuth events logged with user ID, timestamp, action |
| **§ 164.312(c)(1) - Integrity** | | R | JWT signature validation | ✅ | Prevents token tampering |
| | (i) Mechanism to Authenticate ePHI | A | Not provided by plugin | 🔧 | Use DICOM integrity checks, digital signatures if required |
| **§ 164.312(d) - Person or Entity Authentication** | | R | OAuth2 bearer token authentication | ✅ | JWT signature, expiration, issuer validation |
| **§ 164.312(e)(1) - Transmission Security** | | | | | |
| | (i) Integrity Controls | A | TLS provides transport integrity | ✅ | TLS 1.2+ enforced |
| | (ii) Encryption | A | TLS encryption | ✅ | HTTPS required for all connections |

## Detailed Controls Mapping

### Access Control (§ 164.312(a))

#### Unique User Identification (§ 164.312(a)(2)(i))

**Requirement:** Assign a unique name and/or number for identifying and tracking user identity.

**Implementation:**
```json
{
  "OAuth": {
    "Enabled": true,
    "UserIdentifierClaim": "sub"  // Or "email", "upn", etc.
  }
}
```

**How it Works:**
1. User authenticates to OAuth provider (Azure AD, Google, AWS)
2. OAuth provider issues JWT with unique user identifier in claims
3. Plugin extracts user ID from `sub`, `email`, or `upn` claim
4. User ID included in all audit logs

**Verification:**
```bash
# Decode JWT to verify user ID claim
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq '.sub'
# Output: "user@example.com" or "00000000-0000-0000-0000-000000000000"
```

**Status:** ✅ Implemented

---

#### Emergency Access Procedure (§ 164.312(a)(2)(ii))

**Requirement:** Establish procedures for obtaining necessary ePHI during an emergency.

**Implementation:**
- Create dedicated emergency access account in OAuth provider
- Configure MFA requirement for emergency account
- Document emergency access approval process
- Review emergency access usage within 24 hours

**Configuration:**
```json
{
  "OAuth": {
    "Enabled": true,
    "EmergencyAccess": {
      "AllowedUsers": [
        "breakglass@example.com"
      ],
      "RequireJustification": true,
      "AlertOnUse": true
    }
  }
}
```

**Organizational Procedure:**
1. Emergency occurs (provider needs immediate access to patient record)
2. Provider contacts on-call administrator
3. Administrator verifies legitimacy
4. Administrator provides breakglass credentials
5. Provider accesses ePHI
6. Access logged and reviewed within 24 hours
7. Incident documented

**Status:** ⚠️ Partial (technical capability provided, procedure is organizational)

---

#### Automatic Logoff (§ 164.312(a)(2)(iii))

**Requirement:** Procedures that terminate an electronic session after a predetermined time of inactivity.

**Implementation:**
```json
{
  "OAuth": {
    "TokenLifetime": 3600,  // 1 hour
    "RequireReauthentication": true,
    "NoAutomaticRenewal": true
  }
}
```

**How it Works:**
1. OAuth token issued with `expires_in` value (default: 3600 seconds)
2. Plugin caches token with TTL = expires_in - 60 (safety buffer)
3. After expiration, plugin rejects requests with HTTP 401
4. User must re-authenticate to obtain new token
5. No session state maintained by plugin

**Verification:**
```bash
# Token expires after 3600 seconds
# Wait 1 hour + 1 minute, then try request
curl -H "Authorization: Bearer $EXPIRED_TOKEN" \
  https://orthanc.example.com/dicom-web/studies
# Expected: HTTP 401 Unauthorized
```

**Status:** ✅ Implemented

---

#### Encryption and Decryption (§ 164.312(a)(2)(iv))

**Requirement:** Implement a mechanism to encrypt and decrypt ePHI.

**Implementation:**

**In Transit:**
```json
{
  "OAuth": {
    "RequireHTTPS": true,
    "TLSMinVersion": "1.2",
    "TLSCipherSuites": [
      "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
      "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
    ]
  }
}
```

**In Memory:**
- OAuth tokens encrypted using AES-256-GCM
- Secrets encrypted using Fernet (AES-128-CBC + HMAC-SHA256)
- No plaintext credentials in memory dumps

**At Rest (Infrastructure):**
- EBS volumes: Encrypt with AWS KMS
- RDS databases: Enable encryption at rest
- S3 buckets: Enable default encryption
- Backups: Encrypted with KMS/Key Vault

**Verification:**
```bash
# Verify TLS 1.2+ enforcement
nmap --script ssl-enum-ciphers -p 8042 orthanc.example.com

# Verify no TLS 1.0/1.1
openssl s_client -connect orthanc.example.com:8042 -tls1
# Expected: handshake failure
```

**Status:** ✅ Implemented (in-transit), 🔧 Configuration (at-rest)

---

### Audit Controls (§ 164.312(b))

**Requirement:** Hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use ePHI.

**Implementation:**

**Structured Logging:**
```json
{
  "timestamp": "2026-02-07T15:30:00.123Z",
  "level": "INFO",
  "correlation_id": "abc123-def456",
  "user_id": "user@example.com",
  "source_ip": "203.0.113.45",
  "action": "TOKEN_ACQUIRED",
  "server": "azure-dicomweb",
  "result": "SUCCESS",
  "response_time_ms": 45
}
```

**Events Logged:**
- TOKEN_ACQUIRED - Successful token acquisition
- TOKEN_CACHED - Token cached for future use
- TOKEN_EXPIRED - Token expired and removed from cache
- TOKEN_VALIDATION_FAILED - Invalid token rejected
- AUTHENTICATION_FAILED - Failed authentication attempt
- AUTHORIZATION_FAILED - Valid auth but insufficient permissions
- RATE_LIMIT_EXCEEDED - Too many requests from user/IP
- CONFIGURATION_ERROR - Misconfiguration detected

**Log Attributes:**
- Timestamp (ISO 8601 UTC)
- User identifier (from JWT claims)
- Source IP address
- Action performed
- Affected resource/server
- Result (SUCCESS/FAILURE)
- Error details (if failure)
- Response time

**Log Destinations:**
- CloudWatch Logs (AWS)
- Azure Monitor (Azure)
- Cloud Logging (GCP)
- Syslog (RFC 5424)
- File (JSON lines)

**Log Retention:**
- Default: 90 days
- Recommended: 6 years (HIPAA record retention)

**Status:** ✅ Implemented

See [AUDIT-LOGGING.md](AUDIT-LOGGING.md) for complete audit logging guide.

---

### Integrity (§ 164.312(c)(1))

**Requirement:** Implement policies and procedures to protect ePHI from improper alteration or destruction.

**Implementation:**

**Token Integrity:**
- JWT signature validation prevents token tampering
- HMAC-SHA256 or RS256 signature algorithms
- Public key verification for RS256 tokens
- Reject tokens with invalid signatures

**Configuration Integrity:**
- JSON schema validation on startup
- Required fields validation
- Type checking
- Range validation (ports, timeouts, etc.)
- Fail-safe defaults

**Audit Log Integrity:**
- Append-only log files
- Tamper-evident logging (write-once storage)
- Log shipping to centralized SIEM
- Periodic log integrity verification

**Verification:**
```bash
# Test tampered token detection
# 1. Get valid token
TOKEN="eyJhbGci...valid_signature"

# 2. Modify payload (changes signature)
TAMPERED_TOKEN=$(echo $TOKEN | sed 's/admin/user/g')

# 3. Try to use tampered token
curl -H "Authorization: Bearer $TAMPERED_TOKEN" \
  https://orthanc.example.com/dicom-web/studies
# Expected: HTTP 401 Unauthorized, log entry: TOKEN_VALIDATION_FAILED
```

**Status:** ✅ Implemented

---

### Person or Entity Authentication (§ 164.312(d))

**Requirement:** Implement procedures to verify that a person or entity seeking access to ePHI is the one claimed.

**Implementation:**

**OAuth2 Bearer Token Authentication:**
```
Authorization: Bearer <access_token>
```

**Token Validation Steps:**
1. **Signature Verification:** Verify JWT signature using OAuth provider's public key
2. **Expiration Check:** Verify token not expired (`exp` claim < current time)
3. **Issuer Validation:** Verify token issued by trusted OAuth provider (`iss` claim)
4. **Audience Validation:** Verify token intended for this application (`aud` claim)
5. **Not Before Check:** Verify token is valid now (`nbf` claim <= current time)

**OAuth Providers Supported:**
- Azure Active Directory (Microsoft Entra ID)
- Google Cloud Identity
- AWS IAM Identity Center
- Okta
- Auth0
- Custom OAuth2/OIDC providers

**Multi-Factor Authentication:**
Plugin relies on OAuth provider's MFA:
- Azure AD: Conditional Access policies
- Google: 2-Step Verification
- AWS: MFA enforcement policies

**Verification:**
```bash
# Verify token validation
curl -X GET https://orthanc.example.com/plugins/oauth/validate \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Output:
{
  "valid": true,
  "claims": {
    "sub": "user@example.com",
    "iss": "https://login.microsoftonline.com/...",
    "aud": "api://orthanc-dicomweb",
    "exp": 1709825400,
    "iat": 1709821800
  },
  "user_id": "user@example.com"
}
```

**Status:** ✅ Implemented

---

### Transmission Security (§ 164.312(e)(1))

**Requirement:** Implement technical security measures to guard against unauthorized access to ePHI that is being transmitted over an electronic communications network.

**Implementation:**

**TLS Configuration:**
```json
{
  "TLS": {
    "MinVersion": "1.2",
    "MaxVersion": "1.3",
    "CipherSuites": [
      "TLS_AES_256_GCM_SHA384",
      "TLS_CHACHA20_POLY1305_SHA256",
      "TLS_AES_128_GCM_SHA256",
      "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
      "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
    ],
    "RequireClientCertificate": false,
    "EnforceHTTPS": true
  }
}
```

**Transmission Scenarios:**

| Scenario | Encryption | Status |
|----------|-----------|--------|
| Client → Orthanc | HTTPS (TLS 1.2+) | ✅ Required |
| Orthanc → OAuth Provider | HTTPS (TLS 1.2+) | ✅ Enforced |
| Orthanc → Redis Cache | TLS optional | ⚠️ Configure Redis TLS |
| Orthanc → Database | TLS optional | 🔧 Configure DB TLS |
| Orthanc → Log Aggregator | TLS optional | 🔧 Configure log TLS |

**Certificate Validation:**
- Verify certificate chain
- Check certificate expiration
- Validate hostname (SNI)
- Reject self-signed certificates (production)

**Verification:**
```bash
# Verify TLS version
openssl s_client -connect orthanc.example.com:8042 -tls1_2 < /dev/null
# Expected: Successful handshake

# Verify strong cipher suites
nmap --script ssl-enum-ciphers -p 8042 orthanc.example.com
# Expected: Only A-grade ciphers

# Test HTTP redirect to HTTPS
curl -I http://orthanc.example.com:8042
# Expected: HTTP 301 or 308 redirect to HTTPS
```

**Status:** ✅ Implemented (plugin), 🔧 Configuration (infrastructure)

---

## Compliance Summary

### Fully Implemented (Plugin Features)

- ✅ Unique user identification via OAuth claims
- ✅ Automatic logoff via token expiration
- ✅ Encryption in transit (TLS 1.2+)
- ✅ Encryption of tokens in memory
- ✅ Audit logging with user identity
- ✅ JWT signature validation (integrity)
- ✅ Person/entity authentication (OAuth2)
- ✅ Transmission security (TLS)
- ✅ Access control (OAuth2 required)
- ✅ Rate limiting (brute force protection)

### Partially Implemented (Configuration Required)

- ⚠️ Emergency access procedure (create breakglass account)
- ⚠️ Encryption at rest (enable on infrastructure)
- ⚠️ Redis TLS (configure Redis with TLS)
- ⚠️ Database TLS (enable TLS on RDS/SQL)
- ⚠️ MFA enforcement (configure in OAuth provider)
- ⚠️ Log retention (configure retention policy)

### Organizational Responsibility (Policies/Procedures)

- 📋 Risk analysis
- 📋 Risk management
- 📋 Sanction policy
- 📋 Security awareness training
- 📋 Incident response procedures
- 📋 Contingency plan (backup, DR, emergency mode)
- 📋 Business associate agreements
- 📋 Physical security (datacenter access)
- 📋 Workstation use and security policies
- 📋 Workforce security (hiring, termination)

## Gap Analysis

| Control | Current State | Gap | Remediation | Priority |
|---------|---------------|-----|-------------|----------|
| § 164.312(a)(2)(ii) Emergency Access | Technical capability exists | No documented procedure | Create and document emergency access procedure | High |
| § 164.312(a)(2)(iv) Encryption at Rest | Plugin encrypts in-memory | Infrastructure not encrypted | Enable EBS/RDS/S3 encryption | High |
| § 164.312(b) Audit Log Review | Logs generated | No review process | Implement weekly log review | High |
| § 164.308(a)(1)(ii)(A) Risk Analysis | Template provided | Not conducted | Conduct annual risk analysis | Critical |
| § 164.308(a)(5)(ii) Malicious Software Protection | OS-level protection | Not verified | Deploy and verify antivirus/EDR | Medium |
| § 164.308(a)(7)(i) Data Backup Plan | No automated backups | Missing | Configure automated daily backups | Critical |
| § 164.308(b)(1) Business Associate Agreements | Template provided | Not executed | Sign BAAs with all vendors | Critical |
| § 164.310(d)(1) Secure Disposal | No documented process | Missing | Document secure disposal procedure | Medium |

## Recommendations

### Immediate (Within 30 Days)

1. Enable encryption at rest on all storage (EBS, RDS, S3)
2. Sign Business Associate Agreements with cloud provider and OAuth provider
3. Configure automated daily backups with encryption
4. Document emergency access procedure
5. Enable MFA in OAuth provider for all users

### Short-Term (Within 90 Days)

6. Conduct formal risk analysis
7. Implement weekly audit log review process
8. Deploy antivirus/EDR on all instances
9. Enable TLS for Redis and database connections
10. Create incident response plan

### Long-Term (Within 6 Months)

11. Implement SIEM with automated alerting
12. Conduct security awareness training for all staff
13. Test disaster recovery procedures
14. Engage third-party auditor for compliance assessment
15. Implement intrusion detection system (IDS)

## References

- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [HHS Security Rule Guidance](https://www.hhs.gov/hipaa/for-professionals/security/guidance/index.html)
- [NIST HIPAA Security Rule Toolkit](https://csrc.nist.gov/projects/security-and-privacy-controls)
- [HHS Audit Protocol](https://www.hhs.gov/hipaa/for-professionals/compliance-enforcement/audit/protocol/index.html)
