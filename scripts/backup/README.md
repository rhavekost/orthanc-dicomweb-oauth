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
- `GPG_RECIPIENT`: Email for GPG encryption (default: `admin@example.com`)
- `S3_BUCKET`: AWS S3 bucket for remote backups (optional, commented out by default)

## Automation

Add to crontab for daily backups at 2 AM:
```cron
0 2 * * * /path/to/backup-config.sh
```

Or use systemd timer:
```bash
# Create timer file
sudo cat > /etc/systemd/system/orthanc-backup.timer <<EOF
[Unit]
Description=Orthanc OAuth Plugin Backup Timer

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start
sudo systemctl enable orthanc-backup.timer
sudo systemctl start orthanc-backup.timer
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

## Prerequisites

- Docker and Docker Compose installed
- GPG installed and configured
- (Optional) AWS CLI configured for S3 backups

## Security Notes

- Backups contain sensitive OAuth credentials
- Always encrypt backups with GPG
- Store GPG private key securely
- Restrict access to backup directory
- Test encryption/decryption regularly

## Troubleshooting

**Issue:** `gpg: no valid OpenPGP data found`
**Solution:** Check GPG recipient email is correct and key exists

**Issue:** `docker cp: No such container`
**Solution:** Verify container name matches your deployment

**Issue:** Backup directory full
**Solution:** Adjust retention period in `backup-config.sh` (default: 30 days)
