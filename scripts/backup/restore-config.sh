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
