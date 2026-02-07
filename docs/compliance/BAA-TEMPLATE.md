# Business Associate Agreement (BAA) Template

> **Note:** This template is provided for informational purposes. Consult legal counsel before using in production.

## Overview

A Business Associate Agreement (BAA) is required under HIPAA when a covered entity shares Protected Health Information (PHI) with a business associate. This template covers the minimum required provisions per 45 CFR § 164.504(e).

## Required BAAs for Orthanc OAuth Deployment

When deploying Orthanc with OAuth plugin in a HIPAA environment, you need BAAs with:

1. **Cloud Infrastructure Provider** (AWS, Azure, GCP)
2. **OAuth/Identity Provider** (Azure AD, Google Cloud Identity, AWS IAM)
3. **Redis Provider** (if using managed Redis)
4. **Log Aggregation Service** (if using third-party)
5. **Backup Service Provider** (if using third-party)
6. **Monitoring Service** (if using third-party)

## BAA Template

---

**BUSINESS ASSOCIATE AGREEMENT**

This Business Associate Agreement ("Agreement") is entered into as of \_\_\_\_\_\_\_\_\_\_ ("Effective Date") by and between:

**COVERED ENTITY:**
- Name: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
- Address: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
- Contact: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**BUSINESS ASSOCIATE:**
- Name: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
- Address: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
- Contact: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

### 1. DEFINITIONS

**1.1 General Definitions**

Terms used but not otherwise defined in this Agreement shall have the meanings established in the HIPAA Rules at 45 CFR Parts 160 and 164.

**1.2 Specific Definitions**

- **"PHI"** means Protected Health Information as defined in 45 CFR § 160.103.
- **"HIPAA Rules"** means the Privacy, Security, Breach Notification, and Enforcement Rules at 45 CFR Parts 160 and 164.
- **"Services"** means [describe services provided by Business Associate].

### 2. OBLIGATIONS OF BUSINESS ASSOCIATE

**2.1 Permitted Uses and Disclosures**

Business Associate may use or disclose PHI only:
- As necessary to perform the Services
- As required by law
- As permitted by this Agreement
- As directed by Covered Entity

**2.2 Safeguards**

Business Associate shall:
- Implement administrative, physical, and technical safeguards that reasonably and appropriately protect the confidentiality, integrity, and availability of PHI
- Comply with Subpart C of 45 CFR Part 164 (Security Rule) with respect to electronic PHI
- Report to Covered Entity any use or disclosure of PHI not permitted by this Agreement
- Report to Covered Entity any security incident of which it becomes aware

**2.3 Breach Notification**

Business Associate shall:
- Report to Covered Entity any breach of unsecured PHI within **ten (10) business days** of discovery
- Provide all information necessary for Covered Entity to comply with breach notification obligations under 45 CFR § 164.410

**2.4 Subcontractors**

Business Associate shall:
- Ensure that any subcontractors that create, receive, maintain, or transmit PHI on behalf of Business Associate agree to the same restrictions and conditions that apply to Business Associate
- Obtain satisfactory assurances from subcontractors in the form of a written agreement

**2.5 Individual Rights**

Business Associate shall:
- Provide access to PHI to Covered Entity or individual within **fifteen (15) days** of request
- Make available PHI for amendment and incorporate amendments as directed by Covered Entity within **thirty (30) days**
- Provide an accounting of disclosures as required by 45 CFR § 164.528 within **thirty (30) days**
- Make internal practices, books, and records relating to use and disclosure of PHI available to HHS for compliance investigation

**2.6 Minimum Necessary**

Business Associate shall:
- Use, disclose, and request only the minimum amount of PHI necessary to accomplish the intended purpose
- Limit access to PHI to workforce members who need access to perform their duties

### 3. OBLIGATIONS OF COVERED ENTITY

**3.1 Permissible Requests**

Covered Entity shall not request Business Associate to use or disclose PHI in any manner that would not be permissible under the HIPAA Rules if done by Covered Entity.

**3.2 Notice of Privacy Practices**

Covered Entity shall provide Business Associate with any limitations in its Notice of Privacy Practices that affect Business Associate's use or disclosure of PHI.

**3.3 Changes in Permission**

Covered Entity shall notify Business Associate of any changes in, or revocation of, permission by individual to use or disclose PHI if such changes affect Business Associate's permitted uses or disclosures.

### 4. TERM AND TERMINATION

**4.1 Term**

This Agreement shall be effective as of the Effective Date and shall terminate on the earlier of:
- Termination of the underlying service agreement
- Written notice by either party with **ninety (90) days** advance notice
- Immediate termination for material breach as provided below

**4.2 Termination for Breach**

If either party determines the other has materially breached this Agreement:
- The non-breaching party shall provide written notice
- The breaching party shall have **thirty (30) days** to cure the breach
- If the breach is not cured within thirty (30) days, the non-breaching party may immediately terminate this Agreement

**4.3 Effect of Termination**

Upon termination:
- Business Associate shall return or destroy all PHI received from Covered Entity
- If return or destruction is not feasible, Business Associate shall extend protections of this Agreement to the PHI and limit further uses and disclosures
- Business Associate shall certify in writing that it has returned or destroyed PHI or that such return or destruction is not feasible

### 5. INDEMNIFICATION

**5.1 By Business Associate**

Business Associate shall indemnify, defend, and hold harmless Covered Entity from and against any claims, damages, liabilities, costs, and expenses (including reasonable attorneys' fees) arising from:
- Business Associate's breach of this Agreement
- Business Associate's use or disclosure of PHI not permitted by this Agreement
- Business Associate's failure to comply with HIPAA Rules

**5.2 Limitations**

Indemnification obligations shall not apply to the extent that claims arise from:
- Covered Entity's breach of this Agreement
- Covered Entity's failure to comply with HIPAA Rules
- Acts or omissions of Covered Entity

### 6. LIABILITY AND RISK OF LOSS

**6.1 Limitation of Liability**

Except for obligations under Section 5 (Indemnification), neither party shall be liable for consequential, incidental, punitive, or special damages, including lost profits.

**6.2 Insurance**

Business Associate shall maintain:
- Cyber liability insurance with minimum coverage of $\_\_\_\_\_\_\_\_\_\_\_
- Errors and omissions insurance with minimum coverage of $\_\_\_\_\_\_\_\_\_\_\_
- Certificates of insurance shall be provided to Covered Entity annually

### 7. MISCELLANEOUS PROVISIONS

**7.1 Regulatory Changes**

The parties agree to take such action as is necessary to amend this Agreement to comply with changes in HIPAA Rules or other applicable laws.

**7.2 Survival**

The obligations of Business Associate under Sections 2.3 (Breach Notification) and 4.3 (Effect of Termination) shall survive termination of this Agreement.

**7.3 Amendment**

This Agreement may be amended only by written agreement signed by both parties.

**7.4 Interpretation**

Any ambiguity in this Agreement shall be resolved to permit Covered Entity to comply with HIPAA Rules.

**7.5 Governing Law**

This Agreement shall be governed by the laws of \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_.

**7.6 Entire Agreement**

This Agreement constitutes the entire agreement between the parties with respect to the subject matter and supersedes all prior agreements.

**7.7 Counterparts**

This Agreement may be executed in counterparts, each of which shall be deemed an original.

---

**COVERED ENTITY:**

Signature: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Name: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Title: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Date: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**BUSINESS ASSOCIATE:**

Signature: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Name: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Title: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

Date: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

---

## Vendor-Specific BAA Guidance

### AWS

**AWS BAA Coverage:**
- Covers: EC2, S3, RDS, ElastiCache, CloudWatch, Lambda, and most AWS services
- Sign BAA through AWS Artifact (in AWS Console)
- Designate which AWS accounts are covered
- Review annually

**Key Considerations:**
- Enable encryption at rest for all services storing PHI
- Enable CloudTrail logging for all API calls
- Use VPC for network isolation
- Enable S3 bucket encryption and versioning

### Azure

**Azure BAA Coverage:**
- Covers: Virtual Machines, Storage, SQL Database, Cache for Redis, Monitor
- BAA available through Microsoft Trust Center
- Add Azure subscription IDs to BAA
- Review annually

**Key Considerations:**
- Enable Azure Security Center
- Use Azure Key Vault for secrets
- Enable diagnostic logging
- Use Private Endpoints for services

### Google Cloud

**Google Cloud BAA Coverage:**
- Covers: Compute Engine, Cloud Storage, Cloud SQL, Memorystore, Cloud Logging
- Sign BAA through GCP Console (Admin > Settings)
- List specific GCP projects covered
- Review annually

**Key Considerations:**
- Enable VPC Service Controls
- Use Cloud KMS for encryption keys
- Enable Cloud Audit Logs
- Use Private Google Access

## Checklist for BAA Execution

- [ ] Identify all business associates handling PHI
- [ ] Obtain BAA template from each vendor
- [ ] Review BAA terms with legal counsel
- [ ] Negotiate terms if needed
- [ ] Execute BAA with all parties
- [ ] Maintain copies of all signed BAAs
- [ ] Review BAAs annually
- [ ] Update BAAs when services change
- [ ] Verify vendor compliance annually
- [ ] Document BAA relationships in risk analysis

## Common BAA Issues

**Issue:** Vendor won't sign BAA
- **Solution:** Find alternative vendor willing to sign BAA, or don't store PHI with that vendor

**Issue:** BAA terms are unfavorable
- **Solution:** Negotiate terms, escalate to vendor account team, or find alternative vendor

**Issue:** Vendor claims they don't need BAA
- **Solution:** If vendor accesses PHI, BAA is required. Find compliant vendor.

**Issue:** Subcontractor doesn't have BAA
- **Solution:** Require your business associate to obtain BAA from all subcontractors

**Issue:** BAA expired or not reviewed
- **Solution:** Implement annual BAA review process, set calendar reminders

## Resources

- [HHS BAA Sample](https://www.hhs.gov/hipaa/for-professionals/covered-entities/sample-business-associate-agreement-provisions/index.html)
- [HIPAA Business Associate Requirements](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/business-associates/index.html)
- [AWS HIPAA Compliance](https://aws.amazon.com/compliance/hipaa-compliance/)
- [Azure HIPAA Compliance](https://azure.microsoft.com/en-us/explore/trusted-cloud/compliance/hipaa/)
- [Google Cloud HIPAA Compliance](https://cloud.google.com/security/compliance/hipaa)
