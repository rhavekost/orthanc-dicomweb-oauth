# HIPAA Risk Analysis Framework

This document provides a framework for conducting HIPAA-required risk analysis for deployments of Orthanc with OAuth plugin.

## Overview

**Requirement:** 45 CFR § 164.308(a)(1)(ii)(A) requires covered entities and business associates to conduct an accurate and thorough assessment of potential risks and vulnerabilities to the confidentiality, integrity, and availability of electronic protected health information (ePHI).

**Frequency:** Annually, or whenever significant changes occur (new systems, new threats, security incidents).

## Risk Analysis Process

### Step 1: Scope Definition

Define the scope of your risk analysis:

**System Components:**
- [ ] Orthanc DICOM server instances
- [ ] OAuth plugin
- [ ] OAuth identity provider (Azure AD, Google, AWS)
- [ ] Redis cache (if using distributed caching)
- [ ] Load balancers
- [ ] Network infrastructure (VPC, subnets, firewalls)
- [ ] Storage systems (databases, file systems, backups)
- [ ] Monitoring and logging systems
- [ ] Admin access systems (VPN, bastion hosts)

**ePHI Flows:**
- [ ] DICOMweb client → Orthanc (HTTPS)
- [ ] Orthanc → OAuth provider (token validation)
- [ ] Orthanc → Redis (token caching)
- [ ] Orthanc → Storage (DICOM data persistence)
- [ ] Orthanc → Logging system (audit logs)
- [ ] Admin → Orthanc (configuration, maintenance)

**Boundaries:**
- Network perimeter
- Application layer
- Data storage layer
- Administrative access

### Step 2: Asset Identification

Identify all assets that create, receive, maintain, or transmit ePHI:

| Asset | Description | ePHI Stored? | Criticality |
|-------|-------------|--------------|-------------|
| Orthanc Server | DICOM server with DICOMweb API | Yes | Critical |
| OAuth Plugin | Authentication/authorization | No (tokens only) | High |
| Redis Cache | Token cache | No (tokens only) | Medium |
| PostgreSQL DB | DICOM metadata storage | Yes | Critical |
| S3/Blob Storage | DICOM image storage | Yes | Critical |
| CloudWatch/Logs | Audit logs | Metadata only | High |
| Load Balancer | Traffic routing | No | High |
| VPC/Network | Network isolation | No | High |

### Step 3: Threat Identification

Identify potential threats to ePHI:

#### 3.1 External Threats

| Threat | Description | Likelihood | Impact |
|--------|-------------|------------|--------|
| **Unauthorized Access** | Attacker gains access to ePHI via compromised credentials | Medium | High |
| **DDoS Attack** | Denial of service disrupts availability | Medium | Medium |
| **Man-in-the-Middle** | Attacker intercepts network traffic | Low | High |
| **SQL Injection** | Attacker exploits database vulnerabilities | Low | High |
| **OAuth Token Theft** | Stolen tokens used for unauthorized access | Medium | High |
| **Ransomware** | Malware encrypts ePHI and demands payment | Medium | Critical |
| **Data Exfiltration** | Attacker steals large volumes of ePHI | Low | Critical |

#### 3.2 Internal Threats

| Threat | Description | Likelihood | Impact |
|--------|-------------|------------|--------|
| **Insider Misuse** | Authorized user accesses ePHI inappropriately | Low | High |
| **Accidental Disclosure** | User accidentally shares ePHI publicly | Medium | High |
| **Configuration Error** | Misconfiguration exposes ePHI | Medium | High |
| **Insufficient Access Controls** | Overly permissive access grants | Medium | Medium |
| **Lost/Stolen Devices** | Device with credentials is compromised | Low | Medium |

#### 3.3 Environmental Threats

| Threat | Description | Likelihood | Impact |
|--------|-------------|------------|--------|
| **Hardware Failure** | Server or storage failure causes data loss | Low | High |
| **Power Outage** | Extended outage disrupts service | Low | Medium |
| **Natural Disaster** | Fire, flood, earthquake affects datacenter | Low | Critical |
| **Cloud Provider Outage** | AWS/Azure/GCP regional outage | Low | Medium |

### Step 4: Vulnerability Assessment

Assess vulnerabilities in current implementation:

#### 4.1 Technical Vulnerabilities

| Vulnerability | Affected Asset | Risk Level | Mitigation Status |
|---------------|----------------|------------|-------------------|
| Weak TLS configuration | Load Balancer | Medium | ✅ Mitigated (TLS 1.2+ enforced) |
| Missing OAuth token validation | OAuth Plugin | High | ✅ Mitigated (signature validation) |
| Unencrypted Redis cache | Redis | Medium | ⚠️ Partial (memory only, add TLS) |
| Missing audit logs | Orthanc | High | ✅ Mitigated (structured logging) |
| Overly permissive firewall | Network | High | ⚠️ Needs review |
| No intrusion detection | Network | Medium | ❌ Not implemented |
| Unencrypted backups | Backup Storage | High | ⚠️ Needs verification |
| Missing MFA for admin access | VPN/SSH | High | ⚠️ Depends on org policy |

#### 4.2 Procedural Vulnerabilities

| Vulnerability | Process | Risk Level | Mitigation Status |
|---------------|---------|------------|-------------------|
| No access review process | Access Control | Medium | ❌ Not documented |
| Insufficient security training | Workforce | Medium | ❌ Not implemented |
| No incident response plan | Security Incident | High | ⚠️ Template provided, needs customization |
| Unclear data retention policy | Data Lifecycle | Medium | ❌ Not documented |
| No disaster recovery testing | Business Continuity | High | ❌ Not tested |
| Manual security patching | Patch Management | Medium | ⚠️ Needs automation |

### Step 5: Risk Calculation

Calculate risk scores using the formula: **Risk = Likelihood × Impact**

**Likelihood Scale:**
- 1 = Rare (< 1% chance per year)
- 2 = Unlikely (1-10% chance per year)
- 3 = Possible (10-50% chance per year)
- 4 = Likely (50-90% chance per year)
- 5 = Almost Certain (> 90% chance per year)

**Impact Scale:**
- 1 = Negligible (minimal impact, no ePHI exposure)
- 2 = Minor (limited ePHI exposure, < 100 records)
- 3 = Moderate (significant exposure, 100-1000 records)
- 4 = Major (large-scale exposure, 1000-10000 records)
- 5 = Catastrophic (massive exposure, > 10000 records, reputational damage)

**Risk Matrix:**

| Threat | Likelihood | Impact | Risk Score | Priority |
|--------|-----------|--------|------------|----------|
| Unauthorized access via stolen OAuth token | 3 | 4 | 12 | High |
| Configuration error exposes S3 bucket | 2 | 5 | 10 | High |
| Ransomware attack encrypts database | 2 | 5 | 10 | High |
| Insider misuse of access | 2 | 3 | 6 | Medium |
| DDoS attack disrupts service | 3 | 2 | 6 | Medium |
| Hardware failure causes data loss | 1 | 4 | 4 | Medium |
| Man-in-the-middle attack intercepts traffic | 1 | 4 | 4 | Medium |
| Cloud provider regional outage | 1 | 3 | 3 | Low |

### Step 6: Risk Mitigation

For each identified risk, document mitigation strategy:

#### High Priority Risks

**Risk: Unauthorized access via stolen OAuth token (Score: 12)**

**Mitigation:**
- ✅ Implement: Token expiration (3600s TTL)
- ✅ Implement: JWT signature validation
- ⚠️ Recommend: Enable OAuth provider MFA
- ⚠️ Recommend: Implement token revocation checking
- ⚠️ Recommend: Monitor for unusual access patterns
- **Residual Risk:** 4 (Likelihood: 2, Impact: 2)

**Risk: Configuration error exposes S3 bucket (Score: 10)**

**Mitigation:**
- ✅ Implement: S3 bucket policies restrict public access
- ✅ Implement: IAM roles with least privilege
- ⚠️ Recommend: Enable S3 access logging
- ⚠️ Recommend: Automated configuration scanning (AWS Config, Prowler)
- ⚠️ Recommend: Peer review of infrastructure changes
- **Residual Risk:** 3 (Likelihood: 1, Impact: 3)

**Risk: Ransomware attack encrypts database (Score: 10)**

**Mitigation:**
- ✅ Implement: Automated daily backups
- ✅ Implement: Network segmentation (VPC)
- ⚠️ Recommend: Immutable backups (S3 Object Lock)
- ⚠️ Recommend: Endpoint detection and response (EDR)
- ⚠️ Recommend: Regular backup restoration testing
- **Residual Risk:** 3 (Likelihood: 1, Impact: 3)

#### Medium Priority Risks

**Risk: Insider misuse of access (Score: 6)**

**Mitigation:**
- ✅ Implement: Audit logging with user identity
- ⚠️ Recommend: Quarterly access reviews
- ⚠️ Recommend: Separation of duties
- ⚠️ Recommend: Anomaly detection on audit logs
- **Residual Risk:** 3 (Likelihood: 1, Impact: 3)

**Risk: DDoS attack disrupts service (Score: 6)**

**Mitigation:**
- ✅ Implement: Cloud provider DDoS protection (AWS Shield, Azure DDoS)
- ✅ Implement: Rate limiting (60 req/min)
- ⚠️ Recommend: CDN/WAF for additional protection
- **Residual Risk:** 3 (Likelihood: 1, Impact: 3)

### Step 7: Documentation

Document all findings:

**7.1 Executive Summary**
- Date of analysis
- Scope of analysis
- Key findings
- High-priority recommendations

**7.2 Detailed Findings**
- All identified threats
- All identified vulnerabilities
- Risk scores
- Current mitigations
- Recommended mitigations

**7.3 Remediation Plan**
- Prioritized list of actions
- Assigned owners
- Target completion dates
- Required budget/resources

**7.4 Residual Risk Acceptance**
- Risks that will not be fully mitigated
- Business justification for acceptance
- Approval signatures

### Step 8: Review and Update

**Annual Review:**
- [ ] Conduct full risk analysis annually
- [ ] Document changes in environment
- [ ] Update threat landscape
- [ ] Verify mitigation effectiveness
- [ ] Update risk scores

**Triggered Reviews:**
- [ ] New system components added
- [ ] Security incident occurred
- [ ] New threats identified
- [ ] Regulatory changes
- [ ] Significant architecture changes

## Risk Analysis Template

### Basic Information

| Field | Value |
|-------|-------|
| **Organization** | |
| **Analysis Date** | |
| **Analysis Period** | |
| **Analyst Name** | |
| **Review Date** | |
| **Approval Date** | |

### System Inventory

| System Component | Description | ePHI? | Owner |
|------------------|-------------|-------|-------|
| | | | |
| | | | |

### Risk Register

| Risk ID | Threat | Vulnerability | Likelihood | Impact | Risk Score | Mitigation | Residual Risk |
|---------|--------|---------------|------------|--------|------------|------------|---------------|
| R001 | | | | | | | |
| R002 | | | | | | | |

### Remediation Plan

| Action | Priority | Owner | Due Date | Status | Notes |
|--------|----------|-------|----------|--------|-------|
| | | | | | |
| | | | | | |

### Risk Acceptance

| Risk ID | Risk Description | Justification | Accepted By | Date |
|---------|------------------|---------------|-------------|------|
| | | | | |

## Tools and Resources

**Risk Analysis Tools:**
- [NIST SP 800-30 Guide](https://csrc.nist.gov/publications/detail/sp/800-30/rev-1/final) - Risk assessment methodology
- [HHS Security Risk Assessment Tool](https://www.healthit.gov/topic/privacy-security-and-hipaa/security-risk-assessment-tool) - Free tool for small organizations
- [OCTAVE](https://www.sei.cmu.edu/our-work/projects/display.cfm?customel_datapageid_4050=6633) - Operationally Critical Threat, Asset, and Vulnerability Evaluation

**Vulnerability Scanning:**
- AWS Inspector, Azure Security Center, GCP Security Command Center
- Nessus, Qualys, Rapid7
- OpenVAS (open source)

**Configuration Assessment:**
- AWS Config, Azure Policy, GCP Security Health Analytics
- Prowler (AWS), ScoutSuite (multi-cloud)
- CIS Benchmarks

**Threat Intelligence:**
- US-CERT alerts: https://www.cisa.gov/uscert/ncas/alerts
- HIPAA breach portal: https://ocrportal.hhs.gov/ocr/breach/breach_report.jsf
- Healthcare-specific threat feeds

## Best Practices

1. **Be Thorough:** Don't skip components. Small vulnerabilities can be chained together.

2. **Be Realistic:** Don't underestimate likelihood or impact to make numbers look better.

3. **Prioritize:** Focus on high-risk items first. Don't try to fix everything at once.

4. **Get Buy-In:** Present findings to leadership with business impact and cost justification.

5. **Track Progress:** Maintain risk register, update as mitigations are implemented.

6. **Retest:** Verify that mitigations are effective through testing.

7. **Document Everything:** Risk analysis is a compliance requirement. Keep records.

8. **Use Expertise:** Consider hiring external consultants for initial assessment.

9. **Share Learnings:** Use incidents and near-misses to improve risk analysis.

10. **Stay Current:** Threat landscape changes rapidly. Update analysis regularly.

## Compliance Checklist

- [ ] Risk analysis covers all ePHI systems
- [ ] Analysis considers technical, physical, and administrative safeguards
- [ ] Threats and vulnerabilities documented
- [ ] Risk scores calculated objectively
- [ ] Mitigation plan created with priorities
- [ ] Residual risks identified and accepted
- [ ] Analysis reviewed and approved by management
- [ ] Analysis documented and retained per policy
- [ ] Remediation progress tracked
- [ ] Analysis updated annually or when triggered
