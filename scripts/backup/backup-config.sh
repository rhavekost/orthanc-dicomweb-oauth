#!/bin/bash
# Automated backup for Orthanc OAuth plugin configuration
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
# Uncomment and configure if using AWS S3
# aws s3 sync "$BACKUP_DIR/$DATE" s3://backup-bucket/orthanc-oauth-plugin/$DATE/

# Keep last 30 days of local backups
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null

echo "Backup completed: $DATE"
