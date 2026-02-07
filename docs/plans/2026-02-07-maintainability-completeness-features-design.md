# Project Improvements Design: Maintainability, Completeness, and Features

**Date:** 2026-02-07
**Status:** Approved
**Target Sections:** Assessment Report Sections 6, 7, 8

---

## Executive Summary

This design addresses three key areas identified in Project Assessment Report #2:

1. **Maintainability (Section 6):** Document existing excellent practices (92/100 score)
2. **Project Completeness (Section 7):** Add backup/recovery documentation and CLA (75/100 → 85/100)
3. **Feature Coverage (Section 8):** Document OAuth decisions, add provider support (73/100 → 82/100)

**Approach:** Documentation-first with minimal code changes. The project already has strong fundamentals; this design focuses on clarifying decisions, providing operational guides, and extending provider support.

---

## Section 6: Maintainability Improvements

**Current Score:** 92/100 (Grade: A-)
**Target:** Maintain excellence through documentation

### Problem Statement

The codebase has exceptional quality metrics:
- Average cyclomatic complexity: 2.29 (industry average: 10-15)
- Test coverage: 83.54%
- Maintainability Index: All modules grade A

However, these practices are implicit. New contributors or future maintainers need explicit guidelines to maintain this quality.

### Solution: Documentation Over Refactoring

Rather than refactoring already-excellent code, document the patterns that make it excellent.

### Deliverables

#### 1. `docs/MAINTAINABILITY.md` - Overview Document

**Purpose:** Central hub for all maintainability resources

**Contents:**
- Link to current metrics (complexity: 2.29, coverage: 83.54%)
- Overview of module structure and responsibilities
- Links to detailed guides (refactoring, code review)
- Technical debt tracking approach
- Contact points for questions

**Audience:** New contributors, code reviewers, future maintainers

#### 2. `docs/development/REFACTORING-GUIDE.md`

**Purpose:** Safe refactoring practices that preserve quality

**Contents:**

**When to Refactor:**
- Function exceeds complexity B (7) - immediate attention
- Module exceeds 150 LOC - consider splitting
- Test coverage drops below 80% - add tests first
- Code duplication appears 3+ times - extract to function

**When NOT to Refactor:**
- Tests are failing - fix tests first
- No clear improvement - don't change for change's sake
- Breaking public API - coordinate with users

**Safe Refactoring Process:**
1. Write tests for existing behavior (if missing)
2. Run radon before: `radon cc src/ -a`
3. Make incremental changes
4. Run tests after each change
5. Run radon after: verify complexity didn't increase
6. Update documentation

**Handling Global State:**
```python
# Current pattern (acceptable for single-instance plugin)
_plugin_context: Optional[PluginContext] = None

# When to refactor: If multi-instance support needed
# Recommended: Singleton pattern or context manager
```

**Measuring Impact:**
```bash
# Before refactoring
radon cc src/module.py -s > before.txt
pytest tests/ --cov=src

# After refactoring
radon cc src/module.py -s > after.txt
diff before.txt after.txt  # Should show improvement or no change
pytest tests/ --cov=src    # Coverage should not decrease
```

#### 3. `docs/development/CODE-REVIEW-CHECKLIST.md`

**Purpose:** Consistent code review standards

**Contents:**

**Automated Checks (CI enforces these):**
- [ ] All tests pass
- [ ] Code coverage ≥ 77%
- [ ] Pylint score ≥ 9.0
- [ ] Black formatting applied
- [ ] Type hints present

**Manual Review:**

**Complexity:**
- [ ] No functions exceed complexity B (7)
- [ ] New code maintains average complexity < 3
- [ ] Complex logic has explanatory comments

**Design:**
- [ ] Follows existing patterns (Factory, Strategy, etc.)
- [ ] Single Responsibility Principle honored
- [ ] Dependencies injected, not hard-coded
- [ ] No new global variables

**Testing:**
- [ ] New features have tests
- [ ] Edge cases covered
- [ ] Error paths tested
- [ ] Mocks used appropriately (not over-mocked)

**Security:**
- [ ] No secrets in code
- [ ] Input validation present
- [ ] SQL injection prevented (if applicable)
- [ ] Error messages don't leak secrets

**Documentation:**
- [ ] Public functions have docstrings
- [ ] Complex logic explained
- [ ] Configuration changes documented
- [ ] Breaking changes noted in CHANGELOG

#### 4. `.github/workflows/complexity-monitoring.yml`

**Purpose:** Automated complexity regression detection

**Contents:**

```yaml
name: Complexity Monitoring

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  complexity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for comparison

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install radon
        run: pip install radon

      - name: Check current complexity
        id: current
        run: |
          echo "average=$(radon cc src/ -a --total-average | grep 'Average complexity' | awk '{print $3}')" >> $GITHUB_OUTPUT

      - name: Check baseline (main branch)
        if: github.event_name == 'pull_request'
        run: |
          git checkout origin/main
          BASELINE=$(radon cc src/ -a --total-average | grep 'Average complexity' | awk '{print $3}')
          echo "Baseline complexity: $BASELINE"
          echo "baseline=$BASELINE" >> $GITHUB_ENV

      - name: Compare complexity
        if: github.event_name == 'pull_request'
        run: |
          CURRENT=${{ steps.current.outputs.average }}
          BASELINE=${{ env.baseline }}

          # Fail if complexity increased by more than 0.5
          python -c "
          import sys
          current = float('$CURRENT'.strip('()'))
          baseline = float('$BASELINE'.strip('()'))
          increase = current - baseline

          print(f'Current: {current}, Baseline: {baseline}, Increase: {increase}')

          if increase > 0.5:
              print(f'❌ Complexity increased by {increase:.2f} (threshold: 0.5)')
              sys.exit(1)
          else:
              print(f'✅ Complexity acceptable (change: {increase:+.2f})')
          "

      - name: Report complexity
        run: |
          echo "## Complexity Report" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Current Average:** ${{ steps.current.outputs.average }}" >> $GITHUB_STEP_SUMMARY
          radon cc src/ -s >> $GITHUB_STEP_SUMMARY
```

### Implementation Effort

- **Time:** 2-3 days
- **Priority:** Medium (documentation, not blocking)
- **Risk:** Low (no code changes)

### Success Metrics

- All 4 documents created and reviewed
- Complexity monitoring workflow passing on main branch
- At least one PR uses the code review checklist
- Maintainability score remains ≥ 90/100

---

## Section 7: Project Completeness - Backup & Recovery

**Current Score:** 40/100
**Target:** 85/100

### Problem Statement

The plugin handles OAuth credentials and configuration for healthcare systems, but lacks documented backup/recovery procedures. This creates risk:

- Configuration loss during system failures
- No documented recovery procedures
- Unclear integration with Orthanc's backup strategy
- Production deployments need disaster recovery plans

### Key Insight: Plugin-Aware Backup Strategy

This is an **Orthanc plugin**, not a standalone application. Backup/recovery must:
1. Integrate with Orthanc's own backup procedures
2. Focus on plugin-specific configuration
3. Not duplicate Orthanc's DICOM data backup (handled by Orthanc)
4. Coordinate secrets management with Orthanc's security model

### Solution: Comprehensive Operational Guide

**Target Audiences:**
1. **Primary:** Docker Compose users (developers, small deployments)
2. **Secondary:** Kubernetes users (larger institutions, HA deployments)

### Deliverables

#### 1. `docs/operations/BACKUP-RECOVERY.md` - Main Guide

**Structure:**

**Part A: Understanding What to Back Up**

```markdown
## What This Plugin Needs Backed Up

### 1. Plugin Configuration (CRITICAL)
- Location: `orthanc.json` → `DicomWebOAuth` section
- Contains: Server definitions, token endpoints, client IDs
- Frequency: After each configuration change
- Sensitivity: Contains OAuth endpoint URLs (not secrets)

### 2. OAuth Secrets (CRITICAL - HIGH SENSITIVITY)
- Location: Environment variables or `.env` file
- Contains: Client secrets, credentials
- Frequency: After secret rotation
- Security: Encrypt at rest, restrict access

### 3. Plugin State (NOT NEEDED)
- Token cache: In-memory only, rebuilt on startup
- No persistent state to back up

### 4. Orthanc Data (HANDLED BY ORTHANC)
- DICOM studies: Orthanc's responsibility
- Database: Orthanc's responsibility
- This plugin does not manage DICOM data
```

**Part B: Docker Compose Backup Procedures**

```markdown
## Docker Compose Backup

### Quick Backup

```bash
# Back up configuration
docker cp orthanc:/etc/orthanc/orthanc.json ./backup/orthanc.json.$(date +%Y%m%d)

# Back up environment file (contains secrets!)
cp docker/.env ./backup/.env.$(date +%Y%m%d)

# Secure the backup
chmod 600 ./backup/.env.*
```

### Automated Backup (Recommended)

Use provided script: `scripts/backup/backup-config.sh`

```bash
#!/bin/bash
# Run daily via cron: 0 2 * * * /path/to/backup-config.sh

BACKUP_DIR="/backup/orthanc-oauth-plugin"
DATE=$(date +%Y%m%d-%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup plugin configuration from running container
docker cp orthanc:/etc/orthanc/orthanc.json "$BACKUP_DIR/$DATE/"

# Backup environment file (if using Docker Compose)
if [ -f docker/.env ]; then
    cp docker/.env "$BACKUP_DIR/$DATE/"
fi

# Encrypt sensitive files
gpg --encrypt --recipient admin@example.com "$BACKUP_DIR/$DATE/.env"
rm "$BACKUP_DIR/$DATE/.env"  # Remove unencrypted version

# Upload to remote storage (example: AWS S3)
aws s3 sync "$BACKUP_DIR/$DATE" s3://backup-bucket/orthanc-oauth-plugin/$DATE/

# Keep last 30 days of local backups
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $DATE"
```

### Recovery Procedure

**Scenario: Configuration Lost**

1. **Stop Orthanc**
   ```bash
   docker-compose down
   ```

2. **Restore configuration**
   ```bash
   # Retrieve latest backup
   LATEST=$(ls -t backup/ | head -1)

   # Decrypt environment file
   gpg --decrypt backup/$LATEST/.env.gpg > docker/.env

   # Copy configuration to volume
   docker cp backup/$LATEST/orthanc.json orthanc:/etc/orthanc/
   ```

3. **Restart Orthanc**
   ```bash
   docker-compose up -d
   ```

4. **Verify plugin loaded**
   ```bash
   curl http://localhost:8042/dicomweb-oauth/status
   # Expected: {"status": "ok", "servers": [...]}
   ```

5. **Test token acquisition**
   ```bash
   curl -X POST http://localhost:8042/dicomweb-oauth/servers/my-server/test
   # Expected: {"token_acquired": true}
   ```

### Recovery Testing

**Monthly Drill (Recommended):**

1. Create test environment
2. Restore from backup
3. Verify token acquisition works
4. Document recovery time (target: < 15 minutes)

Recovery Time Objective (RTO): 15 minutes
Recovery Point Objective (RPO): 24 hours (daily backups)
```

**Part C: Kubernetes Backup Procedures**

```markdown
## Kubernetes Backup

### What to Back Up

1. **ConfigMaps** - Plugin configuration
2. **Secrets** - OAuth credentials
3. **PersistentVolumeClaims** - Orthanc DICOM data (handled by Orthanc)

### Backup with Velero (Recommended)

```bash
# Install Velero
velero install \
  --provider aws \
  --bucket orthanc-backups \
  --backup-location-config region=us-west-2

# Create backup schedule (daily at 2 AM)
velero schedule create orthanc-daily \
  --schedule="0 2 * * *" \
  --include-namespaces orthanc \
  --include-resources configmap,secret

# Manual backup
velero backup create orthanc-manual-$(date +%Y%m%d)
```

### Manual Backup (No Velero)

```bash
# Backup ConfigMaps
kubectl get configmap orthanc-config -n orthanc -o yaml > backup/configmap.yaml

# Backup Secrets
kubectl get secret orthanc-oauth-secrets -n orthanc -o yaml > backup/secrets.yaml

# Encrypt secrets backup
gpg --encrypt --recipient admin@example.com backup/secrets.yaml
rm backup/secrets.yaml  # Remove unencrypted
```

### Recovery Procedure

**Scenario: Namespace Deleted**

1. **Restore with Velero**
   ```bash
   velero restore create --from-backup orthanc-daily-20260207
   ```

2. **Verify restoration**
   ```bash
   kubectl get pods -n orthanc
   kubectl logs -n orthanc deployment/orthanc
   ```

3. **Test plugin**
   ```bash
   kubectl port-forward -n orthanc svc/orthanc 8042:8042
   curl http://localhost:8042/dicomweb-oauth/status
   ```

**Manual Recovery:**

```bash
# Restore ConfigMap
kubectl apply -f backup/configmap.yaml

# Restore Secrets
gpg --decrypt backup/secrets.yaml.gpg | kubectl apply -f -

# Restart deployment
kubectl rollout restart deployment/orthanc -n orthanc
```

### Disaster Recovery

**Multi-Region Setup:**

```yaml
# Primary region: us-west-2
# Backup region: us-east-1

# Velero configuration for cross-region backup
velero backup-location create secondary \
  --provider aws \
  --bucket orthanc-backups-east \
  --config region=us-east-1
```

**RTO/RPO Targets:**

| Deployment Size | RTO | RPO | Backup Frequency |
|----------------|-----|-----|------------------|
| Small (< 10 users) | 1 hour | 24 hours | Daily |
| Medium (10-100 users) | 30 minutes | 12 hours | Twice daily |
| Large (> 100 users) | 15 minutes | 1 hour | Hourly |
| Critical (24/7 operations) | 5 minutes | 15 minutes | Continuous replication |
```

**Part D: Integration with Orthanc Backup**

```markdown
## Integrating with Orthanc's Backup Strategy

### Complete System Backup

This plugin is ONE component of a complete Orthanc system. A full backup includes:

```
Orthanc System Backup
├── Orthanc Configuration
│   ├── orthanc.json (main config)
│   ├── orthanc-users.json (if using)
│   └── SSL certificates
│
├── Orthanc Data (CRITICAL - LARGE)
│   ├── PostgreSQL database (if using)
│   ├── SQLite database (if using)
│   └── DICOM storage directory
│
├── OAuth Plugin Configuration (THIS PLUGIN)
│   ├── orthanc.json → DicomWebOAuth section
│   └── OAuth secrets (.env or K8s secrets)
│
└── Other Plugins
    └── Their configurations
```

### Backup Order (Important!)

1. **Stop or pause Orthanc** (optional but recommended for consistency)
2. **Backup Orthanc database** (pg_dump or sqlite3 .dump)
3. **Backup DICOM storage** (rsync or volume snapshot)
4. **Backup Orthanc configuration** (orthanc.json)
5. **Backup plugin configurations** (including this plugin)
6. **Resume Orthanc**

### Example: Complete Docker Compose Backup

```bash
#!/bin/bash
# Complete Orthanc system backup

BACKUP_DIR="/backup/orthanc-complete/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 1. Backup PostgreSQL database (if using)
docker exec orthanc-db pg_dump -U orthanc > "$BACKUP_DIR/database.sql"

# 2. Backup DICOM storage
docker cp orthanc:/var/lib/orthanc/db "$BACKUP_DIR/dicom-storage"

# 3. Backup Orthanc configuration
docker cp orthanc:/etc/orthanc/orthanc.json "$BACKUP_DIR/"

# 4. Backup OAuth plugin secrets
cp docker/.env "$BACKUP_DIR/"

# 5. Compress and encrypt
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
gpg --encrypt --recipient admin@example.com "$BACKUP_DIR.tar.gz"

# 6. Upload to remote storage
aws s3 cp "$BACKUP_DIR.tar.gz.gpg" s3://orthanc-backups/

echo "Complete backup saved: $BACKUP_DIR.tar.gz.gpg"
```

### Recovery Testing Matrix

Test each scenario quarterly:

| Scenario | Components | Expected RTO | Last Tested |
|----------|-----------|--------------|-------------|
| Plugin config lost | OAuth plugin only | 15 min | ___ |
| Orthanc config lost | Orthanc + plugins | 30 min | ___ |
| Database corrupted | Orthanc DB + DICOM | 2 hours | ___ |
| Complete server loss | Full system | 4 hours | ___ |
| Region failure (K8s) | Cross-region restore | 1 hour | ___ |

### Monitoring Backup Health

Add to monitoring:

```python
# Check last backup age
BACKUP_MAX_AGE_HOURS = 48

last_backup = get_last_backup_timestamp()
age_hours = (now() - last_backup).total_hours()

if age_hours > BACKUP_MAX_AGE_HOURS:
    alert("Backup is stale! Last backup: {} hours ago".format(age_hours))
```
```

#### 2. Backup Scripts: `scripts/backup/`

**`backup-config.sh`** - Automated backup script (detailed above)

**`restore-config.sh`** - Restore script

```bash
#!/bin/bash
# Restore plugin configuration from backup

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup-date>"
    echo "Example: $0 20260207-140500"
    exit 1
fi

BACKUP_DATE=$1
BACKUP_DIR="/backup/orthanc-oauth-plugin/$BACKUP_DATE"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Backup not found: $BACKUP_DIR"
    exit 1
fi

echo "Restoring from backup: $BACKUP_DATE"

# Decrypt environment file
gpg --decrypt "$BACKUP_DIR/.env.gpg" > docker/.env

# Copy configuration
docker cp "$BACKUP_DIR/orthanc.json" orthanc:/etc/orthanc/

# Restart container to load new config
docker-compose restart orthanc

echo "Restore complete. Verifying..."

# Wait for Orthanc to start
sleep 5

# Verify plugin loaded
if curl -s http://localhost:8042/dicomweb-oauth/status | grep -q "ok"; then
    echo "✅ Plugin verified successfully"
else
    echo "❌ Plugin verification failed"
    exit 1
fi
```

**`verify-backup.sh`** - Validate backup integrity

```bash
#!/bin/bash
# Verify backup integrity

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup-directory>"
    exit 1
fi

echo "Verifying backup: $BACKUP_DIR"

# Check required files exist
REQUIRED_FILES=("orthanc.json" ".env.gpg")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$BACKUP_DIR/$file" ]; then
        echo "❌ Missing: $file"
        exit 1
    fi
done

# Verify GPG encryption
if gpg --list-packets "$BACKUP_DIR/.env.gpg" &>/dev/null; then
    echo "✅ GPG encryption valid"
else
    echo "❌ GPG encryption invalid"
    exit 1
fi

# Verify JSON syntax
if python -m json.tool "$BACKUP_DIR/orthanc.json" &>/dev/null; then
    echo "✅ JSON syntax valid"
else
    echo "❌ JSON syntax invalid"
    exit 1
fi

echo "✅ Backup verification complete"
```

**`README.md`** - Script usage guide

```markdown
# Backup & Recovery Scripts

## Quick Start

### Backup
```bash
./backup-config.sh
```

### Restore
```bash
./restore-config.sh 20260207-140500
```

### Verify
```bash
./verify-backup.sh /backup/orthanc-oauth-plugin/20260207-140500
```

## Configuration

Edit variables in `backup-config.sh`:
- `BACKUP_DIR`: Where to store backups (default: `/backup/orthanc-oauth-plugin`)
- `GPG_RECIPIENT`: Email for GPG encryption
- `S3_BUCKET`: AWS S3 bucket for remote backups (optional)

## Automation

Add to crontab for daily backups at 2 AM:
```cron
0 2 * * * /path/to/backup-config.sh
```

## Testing

Test recovery monthly:
```bash
# Create test environment
docker-compose -f docker-compose.test.yml up -d

# Restore backup to test environment
./restore-config.sh <backup-date>

# Verify functionality
curl http://localhost:8042/dicomweb-oauth/status
```
```

#### 3. Docker Compose Updates

Update `docker/docker-compose.yml` with backup volume examples:

```yaml
version: '3.8'

services:
  orthanc:
    image: orthancteam/orthanc:latest
    volumes:
      - orthanc-storage:/var/lib/orthanc/db
      - ./orthanc.json:/etc/orthanc/orthanc.json:ro
      - ../src:/etc/orthanc/plugins:ro

      # Backup volume (optional)
      # Mount this for easy backup access
      - /backup/orthanc:/backup:rw

    environment:
      # OAuth credentials from .env file
      - OAUTH_CLIENT_ID=${OAUTH_CLIENT_ID}
      - OAUTH_CLIENT_SECRET=${OAUTH_CLIENT_SECRET}

    ports:
      - "8042:8042"

    # Backup-friendly labels
    labels:
      - "backup.enable=true"
      - "backup.frequency=daily"
      - "backup.retention=30d"

volumes:
  orthanc-storage:
    # Use named volume for easy backup
    driver: local
    driver_opts:
      type: none
      device: /var/lib/orthanc-data
      o: bind

# Optional: Backup service
  backup:
    image: offen/docker-volume-backup:latest
    volumes:
      - orthanc-storage:/backup/orthanc-storage:ro
      - /backup:/archive
    environment:
      BACKUP_CRON_EXPRESSION: "0 2 * * *"  # Daily at 2 AM
      BACKUP_FILENAME: orthanc-backup-%Y%m%d-%H%M%S.tar.gz
      BACKUP_RETENTION_DAYS: 30
```

### Implementation Effort

- **Documentation:** 1 day
- **Scripts:** 4-6 hours
- **Testing:** 4 hours (manual recovery testing)
- **Total:** 2 days

### Success Metrics

- Backup/recovery guide published
- All 3 scripts functional
- Recovery tested in Docker Compose environment
- Completeness score increases from 40/100 to 85/100

---

## Section 7: Project Completeness - License & Legal

**Current Score:** 80/100
**Target:** 95/100

### Problem Statement

The project has an MIT license but lacks a Contributor License Agreement (CLA). This creates ambiguity:

- Who owns contributed code?
- Can the license be changed later?
- Are contributors granting patent rights?
- What if a contributor doesn't have the right to contribute?

### What is a CLA?

A **Contributor License Agreement** is a legal document that:

1. **Clarifies ownership** - Who owns the copyright on contributions
2. **Grants licenses** - Permission to use/distribute the code
3. **Provides patent protection** - Contributors won't sue over patents
4. **Includes warranty** - Contributors confirm they can contribute the code

**Two types:**
- **Copyright Assignment**: Contributors transfer copyright to you (strong protection, less common)
- **Copyright License**: Contributors keep copyright, grant you a license (common, balanced)

**Why you might need one:**
- ✅ Want to change license later (e.g., MIT → GPL)
- ✅ Want patent protection
- ✅ Building a commercial product
- ✅ Professional/corporate environment

**Why you might not need one:**
- MIT is already permissive
- Small personal project
- Adds friction for contributors
- LICENSE file already defines terms

### Recommendation: Create a Simple CLA (Optional to Enforce)

Create a friendly, Apache-style CLA that clarifies terms without creating barriers to contribution. You can decide later whether to require it.

### Deliverables

#### 1. `CLA.md` - Individual Contributor License Agreement

```markdown
# Individual Contributor License Agreement ("Agreement")

Thank you for your interest in contributing to **orthanc-dicomweb-oauth** (the "Project").

This Contributor License Agreement clarifies the terms under which you contribute code, documentation, or other materials to the Project. It protects both you and the Project maintainers.

## Why We Have This Agreement

This CLA:
- ✅ Clarifies that you own your contributions
- ✅ Grants the Project permission to use your contributions
- ✅ Protects the Project from patent claims
- ✅ Confirms you have the right to contribute

**You keep full ownership of your contributions.** This is a license grant, not a copyright transfer.

---

## Terms

By submitting a contribution to this Project, you agree to the following terms:

### 1. Definitions

- **"You"**: The individual or legal entity making this Agreement
- **"Contribution"**: Any code, documentation, or other material you submit to the Project
- **"Submit"**: Any form of communication sent to the Project (pull request, email, etc.)

### 2. Grant of Copyright License

You grant the Project and its users a perpetual, worldwide, non-exclusive, royalty-free, irrevocable copyright license to:

- Reproduce, prepare derivative works of, publicly display, publicly perform, sublicense, and distribute your Contributions and derivative works under the MIT License or any other open source license.

**You retain ownership of your contributions.**

### 3. Grant of Patent License

You grant the Project and its users a perpetual, worldwide, non-exclusive, royalty-free, irrevocable patent license to make, use, sell, and otherwise transfer your Contribution, where such license applies only to patent claims licensable by you that are necessarily infringed by your Contribution alone or by combination of your Contribution with the Project.

**In plain English:** You won't sue the Project or its users for patent infringement based on your contributions.

### 4. You Have the Right to Grant This License

You represent that:

- ✅ You are legally entitled to grant the above licenses
- ✅ Your contribution is your original work (or you have permission from the copyright owner)
- ✅ Your contribution does not violate any third-party rights
- ✅ If your employer has rights to intellectual property you create, you have received permission to make the contribution

### 5. You Provide Contributions "AS IS"

Your contributions are provided without warranties or conditions of any kind. You are not expected to provide support for your contributions unless you choose to do so.

### 6. Notification of Inaccuracies

You agree to notify the Project if any of the above representations become inaccurate.

---

## How to Sign This Agreement

### For Individual Contributors

Add the following to your pull request description:

```
I agree to the terms of the Contributor License Agreement (CLA.md).
```

**First-time contributors:** Add your name to the [CLA signatories list](#cla-signatories).

### For Corporate Contributors

If you are contributing on behalf of your employer, your employer must sign a separate Corporate CLA. Contact the Project maintainers.

---

## CLA Signatories

The following individuals have agreed to this CLA:

| Name | GitHub Username | Date | PR |
|------|-----------------|------|-----|
| Ryan Havekost | @rhavekost | 2026-02-07 | Initial |
| | | | |

---

## Questions?

If you have questions about this CLA, please open an issue or contact the maintainers.

---

## Attribution

This CLA is based on the [Apache Software Foundation Individual Contributor License Agreement](https://www.apache.org/licenses/icla.pdf), adapted for simplicity and clarity.

## License

This CLA is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
```

#### 2. Update `CONTRIBUTING.md`

Add CLA section to existing contributing guide:

```markdown
# Contributing to orthanc-dicomweb-oauth

## Contributor License Agreement (CLA)

### Do I Need to Sign?

**Currently optional.** We have a CLA available but are not requiring it yet. We may require it in the future for:
- Patent protection
- License flexibility
- Corporate contributions

### How to Sign

If you choose to sign the CLA now (recommended for regular contributors):

1. Read the [CLA](CLA.md)
2. Add this to your PR description:
   ```
   I agree to the terms of the Contributor License Agreement (CLA.md).
   ```
3. Add your name to the [CLA signatories list](CLA.md#cla-signatories)

### What the CLA Means

- ✅ You keep ownership of your contributions
- ✅ You grant the Project permission to use your contributions
- ✅ You confirm you have the right to contribute
- ✅ You provide patent protection to users

**It's friendly!** Read it at [CLA.md](CLA.md) - we've written it in plain English.

## Questions About the CLA?

Open an issue and we'll clarify. We want contributing to be easy, not scary.

---

[Rest of existing CONTRIBUTING.md content...]
```

### Decision Point: When to Require CLA

**Require CLA signing if:**
- ✅ You plan to commercialize the project
- ✅ You want patent protection
- ✅ You might change the license later
- ✅ Corporate contributors are involved

**Keep it optional if:**
- Personal/research project
- Want to minimize contribution friction
- MIT license meets all needs
- Community is small and trusted

### Implementation Effort

- **Writing CLA:** 2 hours (using Apache template)
- **Updating CONTRIBUTING.md:** 30 minutes
- **Legal review (recommended):** Optional, consult attorney
- **Total:** 3 hours

### Success Metrics

- CLA document created and clear
- CONTRIBUTING.md updated with CLA section
- At least one maintainer has signed
- Completeness score increases from 80/100 to 95/100

---

## Section 8: Feature Coverage

**Current Score:** 73/100
**Target:** 82/100

### Problem Areas

1. **OAuth flow documentation** - ADR 001 exists but is technical; need user-friendly explanation
2. **Provider support** - Only Generic and Azure providers; missing Google, AWS
3. **Missing features** - Not documented what's excluded and why

### Solution: Document Decisions + Extend Provider Support

### Deliverables

#### 1. `docs/OAUTH-FLOWS.md` - OAuth Flow Decisions (User-Friendly)

**Purpose:** Explain to users (not just developers) why only client credentials flow is supported.

```markdown
# OAuth2 Flows: What's Supported and Why

## What This Plugin Supports

✅ **Client Credentials Flow** - Service-to-service authentication

This is the **only** OAuth2 flow this plugin implements.

## What This Means for You

### You CAN Use This Plugin If:

- ✅ Your OAuth provider supports client credentials flow
- ✅ You have a service account (client ID + secret)
- ✅ Your DICOMweb server accepts service account tokens
- ✅ You're connecting Orthanc (server) to a DICOMweb server (server-to-server)

### You CANNOT Use This Plugin If:

- ❌ You need user-interactive login (browser-based authentication)
- ❌ You need to authenticate individual users (not service accounts)
- ❌ Your OAuth provider only supports authorization code flow
- ❌ You need device code flow (rare in healthcare)

## Why Only Client Credentials?

### The Short Answer

**Orthanc is a server, not a user application.** It needs to connect to DICOMweb automatically without human interaction.

### The Detailed Answer

**1. DICOM Workflows Are Automatic**

When a CT scanner sends an image to Orthanc, Orthanc needs to:
1. Receive the image (DICOM C-STORE)
2. Immediately forward it to a cloud DICOMweb server
3. No time to ask a user to log in

**2. Servers Don't Have Users Present**

- Orthanc runs as a background service
- No web browser for login redirects
- No user to type credentials
- Needs to work 24/7 without supervision

**3. Healthcare Providers Support This**

All major healthcare cloud providers support client credentials:
- ✅ Azure Health Data Services (Microsoft Entra ID)
- ✅ Google Cloud Healthcare API (service accounts)
- ✅ AWS HealthImaging (OAuth2 client credentials)

**4. Simplicity and Security**

- Single authentication flow = less code = fewer bugs
- No need to manage sessions, redirects, PKCE, state parameters
- Easier to audit and secure

## What About Other OAuth Flows?

### Authorization Code Flow

**What it is:** User logs in via browser, gets redirected back to app

**Why not supported:**
- Requires web UI for login
- Needs redirect URIs
- User must be present
- Orthanc has no login UI

**When you'd need it:** User-facing DICOM viewer, not server-to-server

### Refresh Token Flow

**What it is:** Long-lived token that gets new access tokens

**Why not supported:**
- Client credentials flow doesn't use refresh tokens
- Access tokens are requested directly each time
- Simpler: one flow instead of two

**Provider behavior:** Azure, Google don't issue refresh tokens for client credentials

### Device Code Flow

**What it is:** User enters code on separate device to authenticate

**Why not supported:**
- Requires user interaction (same problem as authorization code)
- Rare in healthcare
- Not needed for server-to-server

**When you'd need it:** Medical devices without browsers (not typical DICOM scenario)

## What If I Need Interactive Login?

If you need users to log in interactively to access DICOM data, you need a different solution:

### Option 1: Use Orthanc's Built-in Authentication

Orthanc supports:
- HTTP Basic Auth
- Custom authentication plugins
- Reverse proxy authentication (Nginx, Apache)

### Option 2: Build a Separate Web Application

```
[User Browser]
    ↓ OAuth2 authorization code flow
[Your Web App]
    ↓ Session cookie
[Orthanc]
    ↓ HTTP Basic or API key
[DICOMweb Server]
```

### Option 3: Use a DICOM Viewer

Many DICOM viewers handle user authentication:
- OHIF Viewer (supports OAuth2)
- Orthanc Web Viewer (supports Orthanc auth)
- Commercial viewers

## Summary

| Flow | Supported | Use Case | Why Not Supported |
|------|-----------|----------|-------------------|
| **Client Credentials** | ✅ Yes | Service-to-service | Supported! |
| Authorization Code | ❌ No | User login | No web UI in Orthanc |
| Refresh Token | ❌ No | Long sessions | Not used with client credentials |
| Device Code | ❌ No | Limited devices | No use case in DICOM |
| Implicit | ❌ No | Browser apps | Deprecated (insecure) |
| Password Grant | ❌ No | Legacy | Deprecated (insecure) |

## Technical Details

For developers and architects, see:
- [ADR 001: Client Credentials Flow Only](adr/001-client-credentials-flow.md)
- [OAuth 2.0 RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)
```

#### 2. `docs/PROVIDER-SUPPORT.md` - Provider Coverage

**Purpose:** Document current and new provider support with comparison matrix.

```markdown
# OAuth2 Provider Support

## Supported Providers

This plugin supports any OAuth2-compliant provider through two approaches:

1. **Generic Provider** - Works with any OAuth2 provider (Keycloak, Auth0, Okta, etc.)
2. **Specialized Providers** - Optimized classes for major cloud providers

## Provider Comparison Matrix

| Provider | Class | Auto-detection | Optimizations | Validation | Setup Complexity |
|----------|-------|----------------|---------------|------------|------------------|
| **Azure Entra ID** | `AzureProvider` | ✅ Yes | ✅ Tenant/scope | ✅ JWT validation | Low |
| **Google Cloud** | `GoogleProvider` | ✅ Yes | ✅ Service account | ✅ Token info API | Low |
| **AWS HealthImaging** | `AWSProvider` | ✅ Yes | ✅ Signature v4 | ✅ AWS validation | Medium |
| **Keycloak** | `GenericProvider` | ❌ No | - | ❌ Generic | Low |
| **Auth0** | `GenericProvider` | ❌ No | - | ❌ Generic | Low |
| **Okta** | `GenericProvider` | ❌ No | - | ❌ Generic | Low |
| **Custom OAuth2** | `GenericProvider` | ❌ No | - | ❌ Generic | Varies |

## When to Use Which Provider

### Use Specialized Provider If:
- ✅ Your provider is Azure, Google, or AWS
- ✅ You want automatic configuration
- ✅ You want provider-specific token validation
- ✅ You need better error messages

### Use Generic Provider If:
- ✅ Your provider is not Azure/Google/AWS
- ✅ Your provider follows OAuth2 spec exactly
- ✅ You want maximum flexibility
- ✅ You're using a custom OAuth2 server

## Provider Details

### Azure Entra ID (Microsoft)

**Class:** `AzureProvider`

**Optimizations:**
- Automatic tenant detection from token endpoint
- Azure-specific scope formatting (`{resource}/.default`)
- JWT signature validation using Microsoft keys
- Multi-tenant support

**Configuration:**

```json
{
  "ProviderType": "azure",
  "TokenEndpoint": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
  "ClientId": "${AZURE_CLIENT_ID}",
  "ClientSecret": "${AZURE_CLIENT_SECRET}",
  "Scope": "https://dicom.healthcareapis.azure.com/.default"
}
```

**Quick Start:** [Azure Quick Start Guide](quickstart-azure.md)

---

### Google Cloud Healthcare API

**Class:** `GoogleProvider`

**Optimizations:**
- Service account JWT token creation
- Google OAuth2 token endpoint (`https://oauth2.googleapis.com/token`)
- Token validation via Google's tokeninfo endpoint
- Automatic scope formatting for Healthcare API

**Configuration:**

```json
{
  "ProviderType": "google",
  "TokenEndpoint": "https://oauth2.googleapis.com/token",
  "ClientId": "${GOOGLE_CLIENT_ID}",
  "ClientSecret": "${GOOGLE_CLIENT_SECRET}",
  "Scope": "https://www.googleapis.com/auth/cloud-healthcare"
}
```

**Alternative: Service Account JSON**

```json
{
  "ProviderType": "google",
  "ServiceAccountJson": "${GOOGLE_SERVICE_ACCOUNT_JSON}",
  "Scope": "https://www.googleapis.com/auth/cloud-healthcare"
}
```

**Quick Start:** [Google Cloud Quick Start Guide](quickstart-google.md)

---

### AWS HealthImaging

**Class:** `AWSProvider`

**Optimizations:**
- AWS Signature Version 4 signing
- IAM role integration
- Token validation via AWS STS
- Region-specific endpoint support

**Configuration:**

```json
{
  "ProviderType": "aws",
  "Region": "us-west-2",
  "ClientId": "${AWS_ACCESS_KEY_ID}",
  "ClientSecret": "${AWS_SECRET_ACCESS_KEY}",
  "Scope": "medical-imaging:*"
}
```

**Alternative: IAM Role (Recommended for EC2/ECS)**

```json
{
  "ProviderType": "aws",
  "Region": "us-west-2",
  "UseInstanceProfile": true
}
```

**Quick Start:** [AWS Quick Start Guide](quickstart-aws.md)

---

### Keycloak

**Class:** `GenericProvider`

**Configuration:**

```json
{
  "ProviderType": "generic",
  "TokenEndpoint": "https://keycloak.example.com/realms/healthcare/protocol/openid-connect/token",
  "ClientId": "${KEYCLOAK_CLIENT_ID}",
  "ClientSecret": "${KEYCLOAK_CLIENT_SECRET}",
  "Scope": "dicomweb-api"
}
```

**Quick Start:** [Keycloak Quick Start Guide](quickstart-keycloak.md)

---

### Auth0

**Class:** `GenericProvider`

**Configuration:**

```json
{
  "ProviderType": "generic",
  "TokenEndpoint": "https://your-tenant.auth0.com/oauth/token",
  "ClientId": "${AUTH0_CLIENT_ID}",
  "ClientSecret": "${AUTH0_CLIENT_SECRET}",
  "Scope": "read:dicom",
  "Audience": "https://dicom-api.example.com"
}
```

**Note:** Auth0 requires the `audience` parameter for client credentials.

---

### Okta

**Class:** `GenericProvider`

**Configuration:**

```json
{
  "ProviderType": "generic",
  "TokenEndpoint": "https://your-domain.okta.com/oauth2/default/v1/token",
  "ClientId": "${OKTA_CLIENT_ID}",
  "ClientSecret": "${OKTA_CLIENT_SECRET}",
  "Scope": "dicom:read dicom:write"
}
```

---

## Auto-Detection

Specialized providers are automatically detected by token endpoint URL:

```python
# Azure: Any URL containing "login.microsoftonline.com"
if "login.microsoftonline.com" in token_endpoint:
    provider = AzureProvider(config)

# Google: Any URL containing "googleapis.com"
if "googleapis.com" in token_endpoint or "google" in token_endpoint:
    provider = GoogleProvider(config)

# AWS: Region-specific endpoint or STS endpoint
if "amazonaws.com" in token_endpoint:
    provider = AWSProvider(config)

# Default: Generic OAuth2
provider = GenericProvider(config)
```

**Override auto-detection:**

```json
{
  "ProviderType": "generic",  // Force generic even if URL matches Azure
  "TokenEndpoint": "https://login.microsoftonline.com/..."
}
```

## Provider Feature Comparison

| Feature | Azure | Google | AWS | Generic |
|---------|-------|--------|-----|---------|
| **Auto-detection** | ✅ | ✅ | ✅ | - |
| **JWT validation** | ✅ | ✅ | ✅ | ❌ |
| **Token refresh** | ✅ | ✅ | ✅ | ✅ |
| **Retry logic** | ✅ | ✅ | ✅ | ✅ |
| **Error messages** | Azure-specific | Google-specific | AWS-specific | Generic |
| **Setup complexity** | Low | Low | Medium | Low |
| **Dependencies** | None extra | None extra | boto3 | None |

## Troubleshooting by Provider

### Azure

**Common Issues:**
- **"Invalid scope"**: Use `{resource}/.default` format, not just scope name
- **"Tenant not found"**: Check tenant ID in token endpoint URL
- **"Invalid client"**: Verify client ID/secret in Azure Portal → App registrations

### Google

**Common Issues:**
- **"Invalid scope"**: Use full scope URL (e.g., `https://www.googleapis.com/auth/cloud-healthcare`)
- **"Invalid grant"**: Service account needs Cloud Healthcare API permissions
- **"Token expired"**: Check system clock (JWT validation is time-sensitive)

### AWS

**Common Issues:**
- **"Signature does not match"**: Check access key and secret
- **"Region mismatch"**: Specify correct region in configuration
- **"Access denied"**: IAM policy needs `medical-imaging:*` permissions

### Generic Providers

**Common Issues:**
- **"Invalid client"**: Check client ID/secret exactly as shown in provider
- **"Unsupported grant type"**: Verify provider supports client credentials flow
- **"Invalid scope"**: Check provider documentation for exact scope format

## Testing Your Provider

Test token acquisition:

```bash
curl -X POST http://localhost:8042/dicomweb-oauth/servers/your-server/test
```

Expected response:
```json
{
  "token_acquired": true,
  "provider": "azure",
  "expires_in": 3600
}
```

## Adding a New Provider

See [CONTRIBUTING.md](CONTRIBUTING.md#adding-a-new-provider) for how to create a specialized provider class.
```

#### 3. `docs/MISSING-FEATURES.md` - Explicitly Document Exclusions

**Purpose:** Clearly state what's NOT included and why, preventing repeated feature requests.

```markdown
# Missing Features & Future Work

This document explicitly lists features that are **not implemented** in this plugin, explains why, and describes when they might be needed.

## OAuth2 Flows

### ❌ Authorization Code Flow

**What it is:** User logs in via browser, gets redirected to application

**Why not included:**
- Orthanc is a server, not a web application
- No web UI for OAuth redirects
- DICOM workflows can't pause for user login
- See [ADR 001](adr/001-client-credentials-flow.md)

**When you'd need it:**
- Building a user-facing DICOM viewer
- Interactive web application (not Orthanc plugin)

**Alternative:**
- Use Orthanc's built-in authentication
- Build separate web app with OAuth2, connect to Orthanc

---

### ❌ Refresh Token Flow

**What it is:** Long-lived token that gets new access tokens without re-authenticating

**Why not included:**
- Client credentials flow doesn't use refresh tokens
- Providers (Azure, Google) don't issue refresh tokens for client credentials
- Access tokens are requested directly when expired

**When you'd need it:**
- Interactive user sessions (authorization code flow)
- Not applicable to service accounts

**Alternative:**
- Current implementation already handles token refresh (request new access token)

---

### ❌ Device Code Flow

**What it is:** User enters code on separate device to authenticate

**Why not included:**
- Requires user interaction
- Rare in DICOM/healthcare workflows
- Not supported by most healthcare APIs

**When you'd need it:**
- Medical devices without web browsers
- Very specialized embedded systems

**Alternative:**
- Use client credentials with service account
- Most medical devices don't need this

---

### ❌ Implicit Flow

**What it is:** Browser-based flow returning token directly (deprecated)

**Why not included:**
- **Deprecated** by OAuth2 spec (security risk)
- Not recommended by any provider
- No use case in server-to-server

**Alternative:**
- Use authorization code flow with PKCE (if you need browser-based auth)

---

### ❌ Password Grant Flow

**What it is:** User provides username/password directly to application (deprecated)

**Why not included:**
- **Deprecated** by OAuth2 spec (security risk)
- Not recommended by any provider
- Anti-pattern for modern authentication

**Alternative:**
- Use client credentials for service accounts
- Use authorization code flow for user authentication

---

## Distributed Caching

### ❌ Redis/Memcached Token Cache

**What it is:** Share tokens across multiple Orthanc instances

**Why not included:**
- Most deployments use single Orthanc instance
- Adds complexity and dependencies
- Token refresh is fast (< 1 second)
- See technical debt in [Assessment Report](PROJECT-ASSESSMENT-REPORT-2.md)

**When you'd need it:**
- Multiple Orthanc instances sharing OAuth config
- High-availability deployments
- Load-balanced Orthanc cluster

**Workaround:**
- Each Orthanc instance gets its own token (acceptable overhead)
- Tokens are cached locally (in-memory)

**Implementation effort:** 2-3 days (if needed)

---

## Horizontal Scaling

### ❌ Multi-Instance Token Coordination

**What it is:** Coordinate token refresh across Orthanc cluster

**Why not included:**
- Current design: in-memory cache per instance
- Requires distributed cache (Redis)
- Most deployments don't need this

**When you'd need it:**
- Orthanc cluster (5+ instances)
- Load-balanced production environment
- Shared token quota limits

**Workaround:**
- Each instance caches independently
- OAuth providers handle concurrent token requests fine

**Implementation effort:** 3-4 days (requires distributed cache)

---

## Advanced Error Handling

### ❌ Circuit Breaker Pattern

**What it is:** Stop calling failing services to prevent cascading failures

**Why not included:**
- Current retry logic with exponential backoff is sufficient
- Adds complexity
- OAuth providers are highly available

**When you'd need it:**
- Unreliable OAuth provider
- Need to fail fast after repeated errors
- Prevent resource exhaustion

**Current alternative:**
- Exponential backoff (3 retries, max 4 seconds)
- Timeout after 30 seconds
- See [RESILIENCE.md](RESILIENCE.md)

**Implementation effort:** 2 days (if needed in future)

---

### ❌ Fallback Authentication

**What it is:** Use backup auth method if OAuth fails

**Why not included:**
- No standard fallback mechanism
- Complicates security model
- OAuth should be reliable enough

**When you'd need it:**
- Critical systems requiring 100% uptime
- Backup to API keys or basic auth

**Security risk:** Having fallback auth reduces security

---

## Provider Optimizations

### ✅ Azure - Implemented
### ✅ Google - Implemented (new)
### ✅ AWS - Implemented (new)

### ❌ Specialized Providers: Okta, Auth0, Keycloak

**Why generic provider is sufficient:**
- These follow OAuth2 spec exactly
- No provider-specific optimizations needed
- Generic provider works perfectly

**When you'd need specialized classes:**
- Provider-specific error handling
- Special token validation logic
- Provider SDK integration

**Implementation effort:** 4-6 hours per provider (if needed)

---

## Token Validation

### ❌ JWT Signature Verification (for Generic Provider)

**What it is:** Verify JWT token signature using provider's public keys

**Why not included (for generic):**
- Only in specialized providers (Azure, Google, AWS)
- Generic provider trusts OAuth provider's response
- Most providers validate on their end

**When you'd need it:**
- Building security-critical application
- Want defense-in-depth
- Regulatory requirements

**Workaround:**
- Use specialized provider class (Azure, Google, AWS) which include validation
- Trust OAuth provider's validation

**Implementation effort:** 1 day per provider

---

## mTLS (Mutual TLS)

### ❌ Certificate-Based Authentication

**What it is:** Use client certificates instead of client secrets

**Why not included:**
- OAuth2 client credentials is standard
- Certificate management complexity
- Not all providers support mTLS
- Out of scope for this plugin

**When you'd need it:**
- Maximum security requirements
- Provider requires mTLS
- Zero-trust architecture

**Alternative:**
- Keep secrets secure (environment variables, secret managers)
- Use short-lived credentials
- Rotate secrets regularly

**Implementation effort:** 1-2 weeks (significant change)

---

## Monitoring & Observability

### ❌ Distributed Tracing (OpenTelemetry)

**What it is:** Trace requests across services

**Why not included:**
- Current structured logging is sufficient
- Adds dependencies (OpenTelemetry SDK)
- Most deployments don't need distributed tracing

**When you'd need it:**
- Microservices architecture
- Complex request flows
- Performance debugging at scale

**Current alternative:**
- Correlation IDs in logs
- Prometheus metrics
- See [METRICS.md](METRICS.md)

**Implementation effort:** 2-3 days

---

### ❌ Custom Metrics Backends (DataDog, New Relic)

**What it is:** Send metrics to commercial monitoring services

**Why not included:**
- Prometheus is standard
- Vendor-specific integration
- Can be added via Prometheus exporters

**When you'd need it:**
- Enterprise monitoring requirements
- Vendor-specific dashboards

**Alternative:**
- Use Prometheus (already supported)
- Export Prometheus to DataDog/New Relic

---

## Configuration

### ❌ Dynamic Configuration Reloading

**What it is:** Change configuration without restarting Orthanc

**Why not included:**
- Orthanc doesn't support plugin config reload
- Requires Orthanc restart anyway
- Adds complexity

**When you'd need it:**
- Frequent config changes
- Zero-downtime config updates

**Workaround:**
- Use environment variables for secrets (can be changed)
- Use rolling restarts in Kubernetes

**Implementation effort:** 3-4 days (limited by Orthanc architecture)

---

### ❌ Web UI for Configuration

**What it is:** Configure plugin via web interface

**Why not included:**
- Orthanc config is JSON-based
- Security risk (exposing secrets)
- Infrastructure-as-code is better practice

**When you'd need it:**
- Non-technical users managing Orthanc
- Visual configuration preference

**Alternative:**
- Edit `orthanc.json` directly (standard practice)
- Use configuration management tools (Ansible, Terraform)

---

## API Features

### ❌ Token Introspection Endpoint

**What it is:** API to check token validity

**Why not included:**
- Tokens are cached internally
- No external need to check token validity
- Would expose token details

**When you'd need it:**
- External services need to check Orthanc's token
- Debugging token issues

**Workaround:**
- Use `/dicomweb-oauth/servers/{name}/test` endpoint

---

### ❌ Token Revocation API

**What it is:** API to manually invalidate cached token

**Why not included:**
- Tokens expire automatically
- Restart Orthanc to clear cache
- Limited use case

**When you'd need it:**
- Suspected token compromise
- Testing token refresh logic

**Workaround:**
- Restart Orthanc container/service
- Wait for token to expire (typically 1 hour)

**Implementation effort:** 2-3 hours (if needed)

---

## Testing

### ❌ Integration Test Suite with Real Providers

**What it is:** Automated tests against actual Azure, Google, AWS

**Why not included:**
- Requires credentials for CI
- Costs money (API calls)
- Security risk (credentials in CI)

**Current alternative:**
- Mock-based unit tests (comprehensive)
- Manual testing against real providers
- Docker-based integration tests

**When you'd need it:**
- Regular provider API changes
- Regression detection across providers

---

## Documentation

### ❌ OpenAPI/Swagger Specification

**What it is:** Machine-readable API documentation

**Why not included:**
- Simple REST API (3 endpoints)
- Documented in [api-reference.md](api-reference.md)
- Limited external API usage

**When you'd need it:**
- Building tools that consume the API
- Automatic client generation

**Implementation effort:** 4-6 hours

---

## Summary: What's NOT Included

| Feature | Reason | Workaround | Effort If Needed |
|---------|--------|------------|------------------|
| Authorization code flow | No web UI in Orthanc | Separate web app | N/A |
| Refresh token flow | Not used with client credentials | Current impl. is sufficient | N/A |
| Distributed caching | Single-instance focus | Per-instance cache | 2-3 days |
| Circuit breaker | Current retry is sufficient | Exponential backoff | 2 days |
| mTLS | Out of scope | Secure secret management | 1-2 weeks |
| JWT validation (generic) | Use specialized providers | Trust OAuth provider | 1 day |
| Dynamic config reload | Orthanc limitation | Restart Orthanc | 3-4 days |
| Web UI config | Security/complexity | Edit JSON config | N/A |
| Distributed tracing | Logging is sufficient | Correlation IDs | 2-3 days |

## Feature Requests Welcome

If you need any of these features:

1. Open an issue explaining your use case
2. Describe why the current workaround doesn't work
3. Consider contributing! See [CONTRIBUTING.md](CONTRIBUTING.md)

We prioritize features based on:
- ✅ Real use cases (not theoretical)
- ✅ Number of users requesting it
- ✅ Alignment with plugin's mission (OAuth2 for DICOMweb)
- ✅ Implementation complexity vs. benefit
```

#### 4. Provider Implementation: Google Healthcare API

**File:** `src/oauth_providers/google.py`

```python
"""Google Cloud Healthcare API OAuth2 provider.

This provider optimizes for Google Cloud's service account authentication,
including automatic scope handling and token validation.
"""

from typing import Dict, Any, Optional
import json
import logging

from .base import OAuthProvider
from ..http_client import HttpClient, HttpResponse

logger = logging.getLogger(__name__)


class GoogleProvider(OAuthProvider):
    """OAuth2 provider for Google Cloud Healthcare API.

    Features:
    - Service account JSON support
    - Automatic scope formatting
    - Token validation via Google's tokeninfo endpoint
    - Google-specific error messages
    """

    provider_name = "google"

    def __init__(
        self,
        config: Dict[str, Any],
        http_client: Optional[HttpClient] = None
    ):
        """Initialize Google provider.

        Args:
            config: Provider configuration with either:
                    - ClientId, ClientSecret (standard OAuth2)
                    - ServiceAccountJson (Google service account)
            http_client: Optional HTTP client for dependency injection
        """
        super().__init__(config, http_client)

        # Google-specific configuration
        self.service_account_json = config.get("ServiceAccountJson")

        # Default Google OAuth2 endpoint if not specified
        if not self.token_endpoint:
            self.token_endpoint = "https://oauth2.googleapis.com/token"

        # Ensure scope includes Google Healthcare API
        if self.scope and "googleapis.com/auth/cloud-healthcare" not in self.scope:
            logger.warning(
                f"Scope '{self.scope}' may not work with Google Healthcare API. "
                "Consider using: https://www.googleapis.com/auth/cloud-healthcare"
            )

    def acquire_token(self) -> Dict[str, Any]:
        """Acquire access token from Google OAuth2.

        Supports two methods:
        1. Client credentials (client ID + secret)
        2. Service account JWT assertion

        Returns:
            Token response with access_token, expires_in, etc.

        Raises:
            OAuthProviderError: If token acquisition fails
        """
        if self.service_account_json:
            return self._acquire_token_with_service_account()
        else:
            return self._acquire_token_with_client_credentials()

    def _acquire_token_with_client_credentials(self) -> Dict[str, Any]:
        """Standard OAuth2 client credentials flow."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        if self.scope:
            data["scope"] = self.scope

        try:
            response = self.http_client.post(
                self.token_endpoint,
                data=data,
                timeout=30
            )

            if response.status_code != 200:
                error_msg = self._parse_google_error(response)
                raise OAuthProviderError(
                    f"Google OAuth2 token acquisition failed: {error_msg}",
                    status_code=response.status_code,
                    provider="google"
                )

            return response.body

        except Exception as e:
            logger.error(f"Google token acquisition failed: {e}")
            raise

    def _acquire_token_with_service_account(self) -> Dict[str, Any]:
        """Acquire token using Google service account JSON.

        Creates a JWT assertion signed with the service account's private key.
        """
        try:
            # Parse service account JSON
            sa_json = json.loads(self.service_account_json)

            # Google service account uses JWT assertion
            data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": self._create_jwt_assertion(sa_json)
            }

            response = self.http_client.post(
                self.token_endpoint,
                data=data,
                timeout=30
            )

            if response.status_code != 200:
                error_msg = self._parse_google_error(response)
                raise OAuthProviderError(
                    f"Google service account token acquisition failed: {error_msg}",
                    status_code=response.status_code,
                    provider="google"
                )

            return response.body

        except json.JSONDecodeError:
            raise OAuthProviderError(
                "Invalid ServiceAccountJson: must be valid JSON",
                provider="google"
            )
        except KeyError as e:
            raise OAuthProviderError(
                f"Invalid ServiceAccountJson: missing field {e}",
                provider="google"
            )

    def _create_jwt_assertion(self, sa_json: Dict[str, Any]) -> str:
        """Create JWT assertion for service account authentication.

        Note: This is a simplified implementation. Production should use
        Google's official SDK (google-auth library) for proper JWT signing.
        """
        import time
        import base64

        # JWT header
        header = {
            "alg": "RS256",
            "typ": "JWT"
        }

        # JWT payload (claims)
        now = int(time.time())
        payload = {
            "iss": sa_json["client_email"],  # Issuer (service account email)
            "sub": sa_json["client_email"],  # Subject (service account email)
            "aud": self.token_endpoint,      # Audience (token endpoint)
            "iat": now,                       # Issued at
            "exp": now + 3600,                # Expires (1 hour)
            "scope": self.scope or "https://www.googleapis.com/auth/cloud-healthcare"
        }

        # Encode header and payload
        header_b64 = base64.urlsafe_b64encode(
            json.dumps(header).encode()
        ).rstrip(b"=").decode()

        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).rstrip(b"=").decode()

        # Sign with private key (simplified - use google-auth in production)
        # This is a placeholder - actual implementation requires proper RSA signing
        signature = self._sign_jwt(
            f"{header_b64}.{payload_b64}",
            sa_json["private_key"]
        )

        signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def _sign_jwt(self, message: str, private_key: str) -> bytes:
        """Sign JWT message with RSA private key.

        Note: This requires the 'cryptography' library.
        In production, use google-auth library instead.
        """
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.backends import default_backend

            # Load private key
            key = serialization.load_pem_private_key(
                private_key.encode(),
                password=None,
                backend=default_backend()
            )

            # Sign message
            signature = key.sign(
                message.encode(),
                padding.PKCS1v15(),
                hashes.SHA256()
            )

            return signature

        except ImportError:
            raise OAuthProviderError(
                "Service account authentication requires 'cryptography' library. "
                "Install with: pip install cryptography",
                provider="google"
            )

    def validate_token(self, token: str) -> bool:
        """Validate token using Google's tokeninfo endpoint.

        Args:
            token: Access token to validate

        Returns:
            True if token is valid, False otherwise
        """
        try:
            response = self.http_client.get(
                f"https://oauth2.googleapis.com/tokeninfo?access_token={token}",
                timeout=10
            )

            if response.status_code == 200:
                # Check if token is for the correct service account
                token_info = response.body
                if self.service_account_json:
                    sa_json = json.loads(self.service_account_json)
                    expected_email = sa_json["client_email"]
                    actual_email = token_info.get("email")

                    if actual_email != expected_email:
                        logger.warning(
                            f"Token email mismatch: expected {expected_email}, "
                            f"got {actual_email}"
                        )
                        return False

                return True
            else:
                logger.warning(f"Token validation failed: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False

    def _parse_google_error(self, response: HttpResponse) -> str:
        """Parse Google-specific error messages.

        Args:
            response: HTTP response from Google OAuth2 endpoint

        Returns:
            Human-readable error message
        """
        try:
            error_body = response.body
            error = error_body.get("error", "unknown_error")
            error_description = error_body.get("error_description", "No description")

            # Google-specific error guidance
            if error == "invalid_client":
                return (
                    f"Invalid client credentials. "
                    f"Check your client_id and client_secret in Google Cloud Console. "
                    f"Details: {error_description}"
                )
            elif error == "invalid_grant":
                return (
                    f"Invalid service account or permissions. "
                    f"Ensure the service account has Cloud Healthcare API access. "
                    f"Details: {error_description}"
                )
            elif error == "invalid_scope":
                return (
                    f"Invalid scope: {self.scope}. "
                    f"Use: https://www.googleapis.com/auth/cloud-healthcare. "
                    f"Details: {error_description}"
                )
            else:
                return f"{error}: {error_description}"

        except (KeyError, AttributeError):
            return f"HTTP {response.status_code}: {response.body}"


class OAuthProviderError(Exception):
    """Exception raised by OAuth providers."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        provider: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.provider = provider
        super().__init__(self.message)
```

#### 5. Provider Implementation: AWS HealthImaging

**File:** `src/oauth_providers/aws.py`

```python
"""AWS HealthImaging OAuth2 provider.

This provider optimizes for AWS authentication using IAM credentials
or instance profiles.
"""

from typing import Dict, Any, Optional
import logging
import hashlib
import hmac
from datetime import datetime
from urllib.parse import urlparse, quote

from .base import OAuthProvider
from ..http_client import HttpClient, HttpResponse

logger = logging.getLogger(__name__)


class AWSProvider(OAuthProvider):
    """OAuth2 provider for AWS HealthImaging.

    Features:
    - AWS Signature Version 4 signing
    - IAM role/instance profile support
    - Region-specific endpoint handling
    - AWS-specific error messages
    """

    provider_name = "aws"

    def __init__(
        self,
        config: Dict[str, Any],
        http_client: Optional[HttpClient] = None
    ):
        """Initialize AWS provider.

        Args:
            config: Provider configuration with either:
                    - ClientId (AWS_ACCESS_KEY_ID), ClientSecret (AWS_SECRET_ACCESS_KEY)
                    - UseInstanceProfile: true (use EC2 instance profile)
            http_client: Optional HTTP client for dependency injection
        """
        super().__init__(config, http_client)

        # AWS-specific configuration
        self.region = config.get("Region", "us-west-2")
        self.use_instance_profile = config.get("UseInstanceProfile", False)
        self.service = "medical-imaging"

        # If using instance profile, get credentials from metadata service
        if self.use_instance_profile:
            self._load_instance_credentials()

    def _load_instance_credentials(self) -> None:
        """Load credentials from EC2 instance metadata service."""
        try:
            # Get IAM role name
            response = self.http_client.get(
                "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
                timeout=5
            )
            role_name = response.body.strip()

            # Get credentials for role
            response = self.http_client.get(
                f"http://169.254.169.254/latest/meta-data/iam/security-credentials/{role_name}",
                timeout=5
            )
            creds = response.body

            self.client_id = creds["AccessKeyId"]
            self.client_secret = creds["SecretAccessKey"]
            self._session_token = creds.get("Token")  # For temporary credentials

            logger.info(f"Loaded instance profile credentials for role: {role_name}")

        except Exception as e:
            raise OAuthProviderError(
                f"Failed to load instance profile credentials: {e}. "
                "Ensure this is running on an EC2 instance with an IAM role.",
                provider="aws"
            )

    def acquire_token(self) -> Dict[str, Any]:
        """Acquire access token for AWS HealthImaging.

        AWS uses Signature Version 4 for authentication, not OAuth2.
        This method returns a signed request that can be used as a "token".

        Returns:
            Token response with access_token (actually a signed request)

        Raises:
            OAuthProviderError: If token acquisition fails
        """
        try:
            # For AWS, we don't get a traditional token
            # Instead, we return credentials that will be used to sign requests

            # Create a pseudo-token that includes signing information
            token_data = {
                "access_token": self._create_aws_signature(),
                "token_type": "AWS4-HMAC-SHA256",
                "expires_in": 3600,  # AWS credentials typically valid for 1 hour
                "region": self.region,
                "service": self.service
            }

            return token_data

        except Exception as e:
            logger.error(f"AWS token acquisition failed: {e}")
            raise OAuthProviderError(
                f"AWS authentication failed: {e}",
                provider="aws"
            )

    def _create_aws_signature(self) -> str:
        """Create AWS Signature Version 4.

        Note: This is a simplified implementation. Production should use
        boto3 or the AWS SDK for proper request signing.
        """
        # For AWS HealthImaging, we need to sign each request
        # This returns the access key which will be used for signing
        # Actual signing happens per-request

        return self.client_id  # Access key ID

    def sign_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: str = ""
    ) -> Dict[str, str]:
        """Sign an AWS request using Signature Version 4.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full request URL
            headers: Request headers
            body: Request body

        Returns:
            Updated headers with Authorization header
        """
        # Parse URL
        parsed = urlparse(url)
        host = parsed.netloc
        canonical_uri = parsed.path or "/"
        canonical_querystring = parsed.query or ""

        # Create timestamp
        t = datetime.utcnow()
        amz_date = t.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = t.strftime("%Y%m%d")

        # Add required headers
        headers = headers.copy()
        headers["Host"] = host
        headers["X-Amz-Date"] = amz_date

        if self._session_token:
            headers["X-Amz-Security-Token"] = self._session_token

        # Create canonical request
        canonical_headers = "\n".join(
            f"{k.lower()}:{v}" for k, v in sorted(headers.items())
        ) + "\n"

        signed_headers = ";".join(sorted(k.lower() for k in headers.keys()))

        payload_hash = hashlib.sha256(body.encode()).hexdigest()

        canonical_request = (
            f"{method}\n"
            f"{canonical_uri}\n"
            f"{canonical_querystring}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{payload_hash}"
        )

        # Create string to sign
        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self.region}/{self.service}/aws4_request"

        string_to_sign = (
            f"{algorithm}\n"
            f"{amz_date}\n"
            f"{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode()).hexdigest()}"
        )

        # Calculate signature
        signing_key = self._get_signature_key(
            self.client_secret,
            date_stamp,
            self.region,
            self.service
        )

        signature = hmac.new(
            signing_key,
            string_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()

        # Create authorization header
        authorization_header = (
            f"{algorithm} "
            f"Credential={self.client_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        headers["Authorization"] = authorization_header

        return headers

    def _get_signature_key(
        self,
        key: str,
        date_stamp: str,
        region: str,
        service: str
    ) -> bytes:
        """Derive signing key from secret access key."""
        k_date = self._sign(f"AWS4{key}".encode(), date_stamp)
        k_region = self._sign(k_date, region)
        k_service = self._sign(k_region, service)
        k_signing = self._sign(k_service, "aws4_request")
        return k_signing

    def _sign(self, key: bytes, msg: str) -> bytes:
        """HMAC-SHA256 signing."""
        return hmac.new(key, msg.encode(), hashlib.sha256).digest()

    def validate_token(self, token: str) -> bool:
        """Validate AWS credentials.

        For AWS, we can validate by making a test request to STS.

        Args:
            token: Access key ID

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            # Use STS GetCallerIdentity to validate credentials
            sts_url = f"https://sts.{self.region}.amazonaws.com/"

            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }

            body = "Action=GetCallerIdentity&Version=2011-06-15"

            # Sign the request
            headers = self.sign_request("POST", sts_url, headers, body)

            response = self.http_client.post(
                sts_url,
                headers=headers,
                data=body,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"AWS credential validation error: {e}")
            return False


class OAuthProviderError(Exception):
    """Exception raised by OAuth providers."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        provider: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.provider = provider
        super().__init__(self.message)
```

#### 6. Provider Configuration Templates

**File:** `config-templates/google-healthcare-api.json`

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "google-healthcare": {
        "DicomWebRoot": "https://healthcare.googleapis.com/v1/projects/{project}/locations/{location}/datasets/{dataset}/dicomStores/{dicomstore}/dicomWeb",
        "ProviderType": "google",
        "TokenEndpoint": "https://oauth2.googleapis.com/token",
        "ServiceAccountJson": "${GOOGLE_SERVICE_ACCOUNT_JSON}",
        "Scope": "https://www.googleapis.com/auth/cloud-healthcare",
        "RefreshBufferSeconds": 300
      }
    }
  }
}
```

**File:** `config-templates/aws-healthimaging.json`

```json
{
  "DicomWebOAuth": {
    "Servers": {
      "aws-healthimaging": {
        "DicomWebRoot": "https://medical-imaging.{region}.amazonaws.com/datastore/{datastore-id}/imageSet",
        "ProviderType": "aws",
        "Region": "us-west-2",
        "ClientId": "${AWS_ACCESS_KEY_ID}",
        "ClientSecret": "${AWS_SECRET_ACCESS_KEY}",
        "UseInstanceProfile": false
      }
    }
  }
}
```

### Implementation Effort

**Phase 1: Documentation (5-6 days)**
- OAuth flows guide: 1 day
- Provider support guide: 1 day
- Missing features guide: 1 day
- CLA creation: 3 hours
- CONTRIBUTING.md updates: 1 hour

**Phase 2: Provider Implementation (4-5 days)**
- Google provider: 2 days (including JWT signing)
- AWS provider: 2 days (Signature v4 complexity)
- Configuration templates: 4 hours
- Tests for new providers: 1 day

**Phase 3: Integration & Testing (2 days)**
- Integration testing
- Documentation review
- Example updates

**Total:** 11-13 days

### Success Metrics

- OAUTH-FLOWS.md clarifies why other flows aren't supported
- PROVIDER-SUPPORT.md provides clear comparison
- MISSING-FEATURES.md prevents repeated feature requests
- Google and AWS providers pass tests
- Configuration templates work with real services
- Feature coverage score increases from 73/100 to 82/100

---

## Implementation Plan Summary

### Phase 1: Documentation (Week 1)
1. Maintainability guides (2-3 days)
2. Backup/recovery documentation (2 days)
3. CLA and legal (3 hours)

### Phase 2: Provider Implementation (Week 2)
1. OAuth flows documentation (1 day)
2. Google provider (2 days)
3. AWS provider (2 days)

### Phase 3: Integration (Week 2-3)
1. Provider support documentation (1 day)
2. Missing features documentation (1 day)
3. Testing and refinement (2 days)

### Total Effort: 2.5-3 weeks

---

## Success Criteria

**Maintainability (Section 6):**
- ✅ All 4 maintainability documents published
- ✅ Complexity monitoring workflow active
- ✅ Score remains ≥ 90/100

**Project Completeness (Section 7):**
- ✅ Backup/recovery guide comprehensive
- ✅ Backup scripts functional and tested
- ✅ CLA created and documented
- ✅ Score increases: 75/100 → 85/100

**Feature Coverage (Section 8):**
- ✅ OAuth flows clearly explained
- ✅ Google and AWS providers implemented
- ✅ Missing features documented
- ✅ Score increases: 73/100 → 82/100

**Overall:**
- ✅ Project score increases: 81.3/100 → 85+/100
- ✅ Production-ready for enterprise deployments
- ✅ Clear contributor guidelines
