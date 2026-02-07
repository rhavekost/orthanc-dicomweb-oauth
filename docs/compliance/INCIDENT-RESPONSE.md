# HIPAA Incident Response Plan

This document provides a framework for responding to security incidents involving Orthanc OAuth plugin deployments in HIPAA-regulated environments.

## Overview

**Requirement:** 45 CFR § 164.308(a)(6) requires implementation of policies and procedures to address security incidents, including identification and response.

**Definition:** A security incident is the attempted or successful unauthorized access, use, disclosure, modification, or destruction of information or interference with system operations in an information system.

## Incident Response Team

### Roles and Responsibilities

| Role | Responsibilities | Contact |
|------|------------------|---------|
| **Incident Response Lead** | Coordinate response, make decisions, communicate with stakeholders | |
| **Security Analyst** | Investigate incident, collect evidence, analyze logs | |
| **System Administrator** | Implement containment, restore services, apply patches | |
| **Legal Counsel** | Advise on legal obligations, breach notification requirements | |
| **Privacy Officer** | Assess ePHI impact, manage breach notifications | |
| **Communications Lead** | Manage external communications, media relations | |
| **Executive Sponsor** | Provide authority, approve major decisions, allocate resources | |

### Contact Information

**Internal:**
- Incident Response Lead: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ (24/7 mobile: \_\_\_\_\_\_\_\_\_\_\_)
- Security Team: security@example.com
- On-Call: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**External:**
- Cloud Provider Support: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
- Forensics Firm: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
- Legal Counsel: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
- Cyber Insurance: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

## Incident Response Process

### Phase 1: Detection and Analysis

**1.1 Incident Detection**

Incidents may be detected through:
- Automated alerts (SIEM, IDS, CloudWatch, Security Center)
- Audit log review
- User reports
- Third-party notifications (cloud provider, vendor)
- Penetration testing or security assessments

**1.2 Initial Assessment (Within 1 Hour)**

When an incident is reported:

1. **Gather Basic Information:**
   - Who reported the incident?
   - When was it discovered?
   - What system/component is affected?
   - Is ePHI involved?
   - Is the incident ongoing?

2. **Classify Severity:**

| Severity | Criteria | Response Time | Examples |
|----------|----------|---------------|----------|
| **Critical** | Active breach of ePHI, widespread impact, ongoing attack | Immediate | Ransomware, active data exfiltration, compromised credentials |
| **High** | Potential ePHI exposure, significant system impact | < 2 hours | Misconfigured S3 bucket, stolen laptop with credentials |
| **Medium** | Limited impact, no confirmed ePHI exposure | < 8 hours | Failed authentication attempts, suspicious log entries |
| **Low** | Minimal impact, false positive likely | < 24 hours | Routine security scan alerts, policy violations |

3. **Determine if Breach:**

A "breach" under HIPAA is an impermissible use or disclosure that compromises the security or privacy of PHI. Consider:
- Was ePHI acquired, accessed, used, or disclosed?
- Was it a violation of HIPAA Privacy Rule?
- Does a breach notification exception apply?

**1.3 Notification (Within Time Limits)**

**Immediate (< 1 hour):**
- Notify Incident Response Lead
- Notify Security Team
- Activate incident response team

**Critical/High Incidents (< 2 hours):**
- Notify Privacy Officer
- Notify Legal Counsel
- Notify Executive Sponsor

**Potential Breach (< 60 days of discovery):**
- Notify affected individuals
- Notify HHS (if > 500 individuals affected)
- Notify media (if > 500 individuals affected)

### Phase 2: Containment

**2.1 Short-Term Containment (Immediate)**

Prevent further damage while maintaining evidence:

**Network Isolation:**
```bash
# Isolate compromised Orthanc instance
aws ec2 modify-instance-attribute \
  --instance-id i-xxxxx \
  --groups sg-isolated

# Or update security group rules
aws ec2 revoke-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol all
```

**Account Suspension:**
```bash
# Disable compromised OAuth client
az ad app update \
  --id <app-id> \
  --set availableToOtherTenants=false

# Revoke all tokens
# (Method varies by OAuth provider)
```

**Access Revocation:**
```bash
# Rotate AWS credentials
aws iam create-access-key --user-name orthanc-service
aws iam delete-access-key --access-key-id AKIAXXXXX --user-name orthanc-service
```

**2.2 Evidence Preservation**

Before containment actions, preserve evidence:

```bash
# Capture instance snapshot
aws ec2 create-snapshot \
  --volume-id vol-xxxxx \
  --description "Incident $(date +%Y%m%d-%H%M%S)"

# Export logs
aws logs create-export-task \
  --log-group-name /aws/orthanc \
  --from $(date -d '24 hours ago' +%s)000 \
  --to $(date +%s)000 \
  --destination incident-evidence-bucket \
  --destination-prefix logs/$(date +%Y%m%d)
```

**2.3 Long-Term Containment**

Implement temporary fixes to restore normal operations:

- Deploy patched version to new instances
- Migrate workload to clean environment
- Implement compensating controls
- Update firewall rules, ACLs
- Enable additional monitoring

### Phase 3: Eradication

**3.1 Root Cause Analysis**

Identify how the incident occurred:

- Review audit logs for unauthorized access
- Analyze network traffic captures
- Examine system configurations
- Review code changes
- Interview relevant personnel

**3.2 Remove Threat**

Eliminate the threat from the environment:

- Delete malware
- Close backdoors
- Patch vulnerabilities
- Remove unauthorized accounts
- Update compromised credentials
- Harden configurations

**3.3 Verification**

Confirm the threat has been removed:

- Scan systems for indicators of compromise (IOCs)
- Verify no unauthorized access
- Test security controls
- Review logs for suspicious activity

### Phase 4: Recovery

**4.1 Restore Operations**

Bring systems back to normal operation:

```bash
# Deploy clean instances
terraform apply -var="environment=production"

# Restore data from clean backup
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier orthanc-prod-restored \
  --db-snapshot-identifier orthanc-clean-backup-20260207

# Update DNS to point to new instances
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456 \
  --change-batch file://dns-update.json
```

**4.2 Validation**

Verify systems are functioning correctly:

- [ ] All services operational
- [ ] Security controls functioning
- [ ] Data integrity verified
- [ ] Performance normal
- [ ] No signs of compromise

**4.3 Monitoring**

Enhanced monitoring for recurrence:

- Increase log retention (90 days)
- Enable detailed audit logging
- Add specific IOC detection rules
- Schedule frequent security scans

### Phase 5: Post-Incident Activity

**5.1 Lessons Learned (Within 7 Days)**

Conduct post-mortem meeting:

**Agenda:**
1. Incident timeline review
2. What went well?
3. What could be improved?
4. Were procedures followed?
5. Were procedures adequate?
6. What security gaps were identified?
7. What actions should be taken?

**Deliverable:** Lessons Learned Report

**5.2 Remediation**

Implement improvements:

| Finding | Action | Owner | Due Date | Status |
|---------|--------|-------|----------|--------|
| OAuth token validation was insufficient | Implement token revocation checking | Security Team | 2026-03-01 | In Progress |
| Incident was detected manually, not automatically | Deploy SIEM with automated alerting | IT Team | 2026-03-15 | Planned |
| No backup restoration procedure | Document and test backup restore process | SysAdmin | 2026-02-28 | Planned |

**5.3 Documentation**

Complete incident documentation:

- [ ] Incident report filed
- [ ] Evidence cataloged and secured
- [ ] Timeline documented
- [ ] Costs calculated
- [ ] Breach notification completed (if applicable)
- [ ] Lessons learned documented
- [ ] Remediation plan created
- [ ] All documentation archived

## Incident Types and Response

### Unauthorized Access

**Indicators:**
- Failed authentication attempts from unusual locations
- Successful login from unexpected IP address
- Access to ePHI by unauthorized user

**Response:**
1. Identify compromised account
2. Disable account immediately
3. Review access logs for ePHI exposure
4. Reset credentials
5. Notify account owner
6. Investigate how credentials were compromised

### Malware/Ransomware

**Indicators:**
- Antivirus alerts
- Files encrypted or modified
- Unusual CPU or network activity
- Ransom note

**Response:**
1. Isolate infected system immediately
2. Do NOT pay ransom
3. Preserve evidence (snapshots, logs)
4. Restore from clean backup
5. Scan all systems for malware
6. Identify entry vector
7. Patch vulnerability

### Data Exfiltration

**Indicators:**
- Large outbound data transfers
- Database dumps
- API abuse (high request rate)
- Unusual S3 bucket access

**Response:**
1. Block outbound connections
2. Identify compromised credentials/access method
3. Determine what data was accessed
4. Revoke credentials
5. Notify affected individuals
6. Report breach to HHS

### Misconfiguration

**Indicators:**
- Public S3 bucket
- Open firewall rules
- Disabled encryption
- Security group allowing 0.0.0.0/0

**Response:**
1. Correct misconfiguration immediately
2. Review logs for unauthorized access
3. Determine if ePHI was exposed
4. Implement configuration monitoring
5. Require peer review for infrastructure changes

### Insider Threat

**Indicators:**
- Excessive data access
- Access outside normal hours
- Data transfer to personal accounts
- Policy violations

**Response:**
1. Document evidence
2. Consult Legal and HR
3. Disable account if appropriate
4. Review all access by individual
5. Determine if ePHI was compromised
6. Follow HR disciplinary procedures

### Lost/Stolen Device

**Indicators:**
- Device reported missing
- Device with stored credentials
- Device with cached ePHI

**Response:**
1. Remotely wipe device if capable
2. Reset credentials stored on device
3. Review access logs for use after loss
4. Determine if ePHI was on device
5. Assess if breach notification required

## Breach Notification Requirements

### HIPAA Breach Notification Rule (45 CFR § 164.400-414)

**Timing:**
- **Individuals:** Within **60 days** of discovery
- **HHS:** Within **60 days** if < 500 individuals; annually if < 500 total
- **Media:** Within **60 days** if ≥ 500 individuals in same state/jurisdiction

**Content of Notification:**
- Brief description of breach
- Types of PHI involved
- Steps individuals should take
- Brief description of investigation
- Contact information

### Exceptions to Breach Notification

Notification not required if low probability of compromise:

1. **Impermissible use/disclosure by workforce member acting in good faith within scope of authority** (if not further disclosed)
2. **Impermissible disclosure to another authorized workforce member** (if not further disclosed)
3. **Disclosure where covered entity has good faith belief recipient could not have retained information**

**Risk Assessment Factors:**
- Nature and extent of PHI involved
- Unauthorized person who used or received PHI
- Whether PHI was actually acquired or viewed
- Extent to which risk has been mitigated

## Testing and Training

### Tabletop Exercises (Quarterly)

Conduct scenario-based discussions:

**Sample Scenario:**
> "At 2:00 AM on a Saturday, your SIEM alerts that a user account has downloaded 10,000 DICOM studies in the past hour. The account belongs to a physician who is on vacation. What do you do?"

**Evaluation:**
- Were correct procedures followed?
- Was response timely?
- Were appropriate people notified?
- Were containment actions effective?

### Incident Response Drills (Annually)

Conduct full-scale incident simulations:

1. Inject realistic incident scenario
2. Activate incident response team
3. Execute response procedures
4. Document actions taken
5. Evaluate effectiveness
6. Update procedures based on findings

### Training (Annually)

All incident response team members must complete:

- [ ] HIPAA Security Rule overview
- [ ] Incident response procedures
- [ ] Breach notification requirements
- [ ] Evidence handling and chain of custody
- [ ] Communication protocols
- [ ] Tool training (SIEM, forensics, etc.)

## Tools and Resources

### Incident Response Tools

**Log Analysis:**
- CloudWatch Insights (AWS)
- Azure Monitor (Azure)
- Cloud Logging (GCP)
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk

**Forensics:**
- AWS Systems Manager Session Manager
- Volatility (memory forensics)
- Sleuth Kit (disk forensics)
- Wireshark (network analysis)

**Incident Management:**
- PagerDuty, VictorOps (alerting)
- JIRA, ServiceNow (ticketing)
- Slack, Teams (communication)

### External Resources

**Guidance:**
- [NIST SP 800-61r2: Computer Security Incident Handling Guide](https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final)
- [SANS Incident Response Process](https://www.sans.org/reading-room/whitepapers/incident/incident-handlers-handbook-33901)
- [HHS Breach Notification Rule](https://www.hhs.gov/hipaa/for-professionals/breach-notification/index.html)

**Reporting:**
- HHS Breach Portal: https://ocrportal.hhs.gov/ocr/breach/wizard_breach.jsf
- US-CERT: https://www.cisa.gov/report

## Incident Report Template

```markdown
# Security Incident Report

## Incident Summary
- **Incident ID:** INC-YYYYMMDD-NNN
- **Severity:** [Critical/High/Medium/Low]
- **Status:** [Detected/Contained/Eradicated/Recovered/Closed]
- **Reported By:**
- **Reported Date/Time:**
- **Detected Date/Time:**
- **Closed Date/Time:**

## Incident Description
[Describe what happened]

## Affected Systems
- System:
- Component:
- ePHI Involved: [Yes/No]
- Number of Records:

## Timeline
| Date/Time | Event | Action Taken |
|-----------|-------|--------------|
| | | |

## Root Cause
[Why did this happen?]

## Impact Assessment
- **ePHI Compromised:** [Yes/No/Unknown]
- **Number of Individuals:**
- **Types of PHI:**
- **Business Impact:**
- **Financial Impact:**

## Response Actions
[What was done to contain, eradicate, and recover?]

## Breach Determination
- **Is this a breach?** [Yes/No]
- **Justification:**
- **Notification Required:** [Yes/No]
- **Notifications Sent:** [List]

## Lessons Learned
- **What went well:**
- **What could improve:**
- **Action items:**

## Attachments
- [ ] Forensic analysis report
- [ ] Log exports
- [ ] Screenshots
- [ ] Breach notification letters
```

## Compliance Checklist

- [ ] Incident response plan documented
- [ ] Incident response team identified
- [ ] Contact information current
- [ ] Procedures tested annually
- [ ] Team trained on procedures
- [ ] Incident response tools available
- [ ] Evidence preservation procedures documented
- [ ] Breach notification procedures documented
- [ ] Post-incident review process defined
- [ ] Incident documentation template available
