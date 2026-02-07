# Backup and Recovery Guide

## Overview

This guide covers backup and recovery procedures for the DICOMweb OAuth plugin, including both standalone plugin backups and integration with complete Orthanc system backups.

## What This Plugin Needs Backed Up

### 1. Plugin Configuration (CRITICAL)
- **Location:** `orthanc.json` → `DicomWebOAuth` section
- **Contains:** Server definitions, token endpoints, client IDs
- **Frequency:** After each configuration change
- **Sensitivity:** Contains OAuth endpoint URLs (not secrets)

### 2. OAuth Secrets (CRITICAL - HIGH SENSITIVITY)
- **Location:** Environment variables or `.env` file
- **Contains:** Client secrets, credentials
- **Frequency:** After secret rotation
- **Security:** Encrypt at rest, restrict access

### 3. Plugin State (NOT NEEDED)
- **Token cache:** In-memory only, rebuilt on startup
- **No persistent state to back up**

### 4. Orthanc Data (HANDLED BY ORTHANC)
- **DICOM studies:** Orthanc's responsibility
- **Database:** Orthanc's responsibility
- **This plugin does not manage DICOM data**

---

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

**Targets:**
- **Recovery Time Objective (RTO):** 15 minutes
- **Recovery Point Objective (RPO):** 24 hours (daily backups)

---

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

```bash
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

---

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

---

## Security Considerations

### Backup Encryption

**Always encrypt backups containing:**
- OAuth client secrets
- Environment files
- Kubernetes secrets

**Recommended tools:**
- GPG for file encryption
- Velero with encryption enabled
- Cloud provider encryption (AWS KMS, Azure Key Vault, Google KMS)

### Access Control

**Backup storage should:**
- Require authentication
- Use role-based access control (RBAC)
- Enable audit logging
- Support versioning (protect against accidental deletion)

### Secret Rotation After Recovery

**After disaster recovery:**
1. Verify all systems operational
2. Rotate OAuth client secrets
3. Update backup encryption keys
4. Review access logs for anomalies

---

## Automation

### Cron Job Example

```bash
# /etc/cron.d/orthanc-backup
# Run backup daily at 2 AM
0 2 * * * /opt/scripts/backup/backup-config.sh >> /var/log/orthanc-backup.log 2>&1
```

### Systemd Timer Example

```ini
# /etc/systemd/system/orthanc-backup.timer
[Unit]
Description=Orthanc OAuth Plugin Backup Timer

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

### Monitoring Automation

Use the provided verification script:

```bash
# Run weekly to verify backup integrity
0 3 * * 0 /opt/scripts/backup/verify-backup.sh
```

---

## Troubleshooting

### Backup Fails

**Issue:** `docker cp` fails with "No such container"
**Solution:** Ensure container name matches your deployment

**Issue:** GPG encryption fails
**Solution:** Verify GPG key exists and is trusted

### Recovery Fails

**Issue:** Plugin doesn't load after restore
**Solution:** Check Orthanc logs for configuration errors

**Issue:** Token acquisition fails after recovery
**Solution:** Verify OAuth secrets were restored correctly

### Performance Impact

**Issue:** Backups slow down Orthanc
**Solution:**
- Run backups during low-traffic periods
- Use volume snapshots instead of file copies
- Consider read replicas for large databases

---

## Contact

For questions about backup and recovery:
- Open a GitHub issue with the `operations` label
- See [CONTRIBUTING.md](../../CONTRIBUTING.md)
