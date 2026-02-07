# Compliance Documentation

This directory contains compliance documentation for healthcare and enterprise deployments.

## Overview

The Orthanc OAuth plugin implements **technical safeguards** required by the HIPAA Security Rule (45 CFR Part 164, Subpart C). This documentation helps organizations implement the necessary **organizational safeguards** to achieve full HIPAA compliance.

## Compliance Status

**Technical Controls:** ✅ Implemented
- OAuth2 authentication with token validation
- TLS 1.2+ encryption in transit
- Token encryption in memory
- Structured audit logging with user identity
- Rate limiting and brute force protection
- Automatic session termination (token expiration)

**Organizational Controls:** ⚠️ Customer Responsibility
- Risk analysis and risk management
- Security policies and procedures
- Workforce training
- Business associate agreements
- Incident response planning
- Disaster recovery and backup procedures

## Available Documents

### Core Compliance Documents

#### [HIPAA Compliance Guide](HIPAA-COMPLIANCE.md)
**Purpose:** Comprehensive guide to HIPAA Security Rule requirements and plugin implementation.

**Contents:**
- Technical controls mapping (§ 164.312)
- Organizational requirements overview
- HIPAA-ready configuration examples
- Infrastructure security requirements
- Deployment recommendations
- Third-party audit guidance

**Use When:** Starting HIPAA compliance project, conducting gap analysis, preparing for audit.

---

#### [Security Controls Matrix](SECURITY-CONTROLS-MATRIX.md)
**Purpose:** Detailed mapping of HIPAA requirements to plugin features.

**Contents:**
- Administrative safeguards (§ 164.308)
- Physical safeguards (§ 164.310)
- Technical safeguards (§ 164.312)
- Implementation status for each control
- Gap analysis with remediation recommendations

**Use When:** Conducting compliance assessment, responding to audit findings, planning implementation.

---

### Operational Documents

#### [Audit Logging Guide](AUDIT-LOGGING.md)
**Purpose:** Configure and manage HIPAA-compliant audit logging.

**Contents:**
- Required audit events
- Log format and structure
- Configuration examples (CloudWatch, Azure Monitor, Cloud Logging)
- Log retention requirements (6-7 years)
- Log review procedures
- Query examples for investigations
- SIEM integration

**Use When:** Configuring production deployment, investigating security incidents, conducting log reviews.

---

#### [Incident Response Plan](INCIDENT-RESPONSE.md)
**Purpose:** Framework for responding to security incidents.

**Contents:**
- Incident response team roles
- 5-phase response process (Detection, Containment, Eradication, Recovery, Post-Incident)
- Incident types and response procedures
- HIPAA breach notification requirements (60-day rule)
- Incident report template
- Tabletop exercise scenarios

**Use When:** Security incident occurs, conducting incident response drills, developing IR procedures.

---

#### [Risk Analysis Framework](RISK-ANALYSIS.md)
**Purpose:** Annual HIPAA-required risk assessment process.

**Contents:**
- 8-step risk analysis process
- Asset identification
- Threat and vulnerability assessment
- Risk scoring methodology
- Mitigation planning
- Risk acceptance documentation
- Risk analysis template

**Use When:** Conducting annual risk analysis, significant system changes, post-incident review.

---

### Legal Documents

#### [Business Associate Agreement Template](BAA-TEMPLATE.md)
**Purpose:** Template for BAAs with vendors handling ePHI.

**Contents:**
- Complete BAA template with required provisions (45 CFR § 164.504(e))
- Vendor-specific guidance (AWS, Azure, GCP)
- Checklist for BAA execution
- Subcontractor requirements
- Breach notification obligations

**Use When:** Engaging cloud provider, OAuth provider, or any vendor accessing ePHI.

---

## Quick Start Guide

### For New Deployments

1. **Review Requirements** (1-2 hours)
   - Read [HIPAA-COMPLIANCE.md](HIPAA-COMPLIANCE.md)
   - Review [SECURITY-CONTROLS-MATRIX.md](SECURITY-CONTROLS-MATRIX.md)
   - Identify gaps in current implementation

2. **Sign Business Associate Agreements** (1-2 weeks)
   - Use [BAA-TEMPLATE.md](BAA-TEMPLATE.md) as reference
   - Sign BAA with cloud provider (AWS/Azure/GCP)
   - Sign BAA with OAuth provider
   - Document all business associate relationships

3. **Conduct Risk Analysis** (2-4 weeks)
   - Follow [RISK-ANALYSIS.md](RISK-ANALYSIS.md) framework
   - Document identified risks
   - Create remediation plan
   - Obtain management approval

4. **Configure Audit Logging** (1 week)
   - Follow [AUDIT-LOGGING.md](AUDIT-LOGGING.md)
   - Configure log retention (6-7 years)
   - Set up log monitoring and alerting
   - Document log review procedures

5. **Develop Incident Response Plan** (1-2 weeks)
   - Customize [INCIDENT-RESPONSE.md](INCIDENT-RESPONSE.md) template
   - Identify incident response team
   - Conduct tabletop exercise
   - Document procedures

6. **Deploy with HIPAA-Ready Configuration** (1-2 weeks)
   - Use configuration examples from [HIPAA-COMPLIANCE.md](HIPAA-COMPLIANCE.md)
   - Enable encryption at rest (EBS, RDS, S3)
   - Configure TLS 1.2+ for all connections
   - Enable MFA in OAuth provider
   - Set up automated backups

7. **Establish Ongoing Compliance** (Ongoing)
   - Weekly audit log reviews
   - Quarterly access reviews
   - Annual risk analysis
   - Annual workforce training
   - Annual compliance evaluation

**Total Time to Compliance:** 6-12 weeks

**Estimated Cost:** $15k-$50k (consulting, auditing, tools)

---

## Compliance Checklist

Use this checklist to track compliance implementation:

### Technical Controls (Plugin Features)

- [x] OAuth2 authentication for all access
- [x] Unique user identification (JWT claims)
- [x] Automatic logoff (token expiration)
- [x] Encryption in transit (TLS 1.2+)
- [x] Encryption of tokens in memory
- [x] Audit logging with user identity
- [x] JWT signature validation (integrity)
- [x] Person/entity authentication
- [x] Rate limiting (brute force protection)
- [x] Secure configuration validation

### Infrastructure Configuration

- [ ] Encryption at rest enabled (EBS, RDS, S3)
- [ ] TLS configured for Redis cache
- [ ] TLS configured for database connections
- [ ] MFA enabled in OAuth provider
- [ ] Automated daily backups configured
- [ ] Backup encryption enabled
- [ ] Network isolation (VPC/VNET)
- [ ] Security groups restrict inbound access
- [ ] Firewall rules reviewed and documented
- [ ] Intrusion detection system deployed (optional)

### Organizational Safeguards

- [ ] Business Associate Agreements signed
  - [ ] Cloud provider (AWS/Azure/GCP)
  - [ ] OAuth provider
  - [ ] Redis provider (if managed service)
  - [ ] Log aggregation provider (if third-party)
  - [ ] Backup provider (if third-party)

- [ ] Risk Analysis completed and documented
  - [ ] Assets identified
  - [ ] Threats and vulnerabilities assessed
  - [ ] Risk scores calculated
  - [ ] Mitigation plan created
  - [ ] Residual risks accepted
  - [ ] Management approval obtained

- [ ] Security Policies and Procedures written
  - [ ] Access control policy
  - [ ] Audit and monitoring policy
  - [ ] Password/authentication policy
  - [ ] Data retention and disposal policy
  - [ ] Acceptable use policy
  - [ ] Remote access policy

- [ ] Incident Response Plan established
  - [ ] Incident response team identified
  - [ ] Contact information documented
  - [ ] Response procedures documented
  - [ ] Breach notification procedures
  - [ ] Plan tested (tabletop exercise)

- [ ] Workforce Training completed
  - [ ] HIPAA Security Rule overview
  - [ ] Organization policies and procedures
  - [ ] Incident reporting procedures
  - [ ] Security awareness (phishing, social engineering)
  - [ ] Training documented

- [ ] Contingency Planning
  - [ ] Data backup plan
  - [ ] Disaster recovery plan
  - [ ] Emergency mode operation plan
  - [ ] Plans tested annually

- [ ] Ongoing Compliance
  - [ ] Weekly audit log reviews
  - [ ] Quarterly access reviews
  - [ ] Annual risk analysis
  - [ ] Annual workforce training
  - [ ] Annual compliance evaluation
  - [ ] Annual contingency plan testing

---

## Frequently Asked Questions

### General

**Q: Does using this plugin make me HIPAA compliant?**

A: No. The plugin provides required **technical safeguards**, but HIPAA compliance also requires **organizational safeguards** including policies, procedures, workforce training, business associate agreements, risk analysis, and incident response planning.

**Q: How long does it take to become HIPAA compliant?**

A: For a new deployment, expect 6-12 weeks to implement all required technical and organizational safeguards. For existing deployments, it depends on current maturity.

**Q: How much does HIPAA compliance cost?**

A: Budget $15k-$50k for initial compliance (consulting, policies, training, auditing) plus ongoing costs for annual reviews, training, and potential third-party audits.

**Q: Do I need a third-party audit?**

A: Not required by HIPAA, but highly recommended for high-risk environments or to demonstrate compliance to business partners. Expect $20k-$50k for a comprehensive security assessment.

### Business Associate Agreements

**Q: Who needs a BAA?**

A: Any vendor that creates, receives, maintains, or transmits ePHI on your behalf. This includes cloud providers (AWS/Azure/GCP), OAuth providers, managed Redis services, log aggregation services, and backup providers.

**Q: What if a vendor won't sign a BAA?**

A: Find a different vendor. If a vendor handles ePHI, a BAA is legally required under HIPAA. Major cloud providers (AWS, Azure, GCP) all offer BAAs.

**Q: How often should BAAs be reviewed?**

A: Annually, or whenever services change significantly.

### Risk Analysis

**Q: How often must risk analysis be conducted?**

A: Annually, and whenever there are significant changes to systems, threats, or vulnerabilities.

**Q: Can I use automated tools for risk analysis?**

A: Yes, but automated tools should supplement, not replace, a thorough manual analysis. Use tools like AWS Security Hub, Azure Security Center, or Prowler.

**Q: What if I identify high risks I can't mitigate?**

A: Document the residual risk, justification for acceptance, and obtain management approval. Implement compensating controls where possible.

### Audit Logging

**Q: How long must audit logs be retained?**

A: Minimum 6 years from creation or last effective date. Recommend 7 years to align with statute of limitations.

**Q: What if logs contain patient identifiers?**

A: Logs containing ePHI must be protected with same safeguards as ePHI (encryption, access controls, retention).

**Q: Can I delete old audit logs?**

A: Only after retention period expires. Use retention locks to prevent accidental deletion.

### Incident Response

**Q: What constitutes a HIPAA "breach"?**

A: An impermissible use or disclosure of ePHI that compromises its security or privacy. Not all security incidents are breaches - conduct a risk assessment for each incident.

**Q: What is the breach notification deadline?**

A: Within **60 days** of discovery. Notify affected individuals, HHS (if ≥500 individuals), and media (if ≥500 in same state).

**Q: What if I'm not sure if it's a breach?**

A: Consult legal counsel and conduct a risk assessment. Document the analysis even if you determine it's not a breach.

---

## Support and Resources

### Documentation

- **Project Documentation:** [Main README](../../README.md)
- **Security Documentation:** [docs/security/](../security/)
- **Operations Documentation:** [docs/operations/](../operations/)
- **Deployment Guides:** [docs/deployment/](../deployment/)

### External Resources

**HIPAA Guidance:**
- [HHS HIPAA for Professionals](https://www.hhs.gov/hipaa/for-professionals/index.html)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [HIPAA Breach Notification Rule](https://www.hhs.gov/hipaa/for-professionals/breach-notification/index.html)

**Standards and Frameworks:**
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [NIST SP 800-53: Security and Privacy Controls](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [HITRUST CSF](https://hitrustalliance.net/hitrust-csf/)
- [CIS Critical Security Controls](https://www.cisecurity.org/controls/)

**Cloud Provider HIPAA Resources:**
- [AWS HIPAA Compliance](https://aws.amazon.com/compliance/hipaa-compliance/)
- [Azure HIPAA Compliance](https://azure.microsoft.com/en-us/explore/trusted-cloud/compliance/hipaa/)
- [Google Cloud HIPAA Compliance](https://cloud.google.com/security/compliance/hipaa)

### Getting Help

**Technical Support:**
- GitHub Issues: https://github.com/rhavekost/orthanc-dicomweb-oauth/issues
- Email: support@example.com

**Security Issues:**
- Email: security@example.com
- PGP Key: [link to PGP public key]

**Compliance Consulting:**
- Email: compliance@example.com

---

## Change History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-07 | 1.0 | Initial compliance documentation release |

---

## License

This compliance documentation is provided for informational purposes only and does not constitute legal advice. Consult with qualified legal counsel for guidance on HIPAA compliance specific to your organization.

Copyright © 2026. All rights reserved.
