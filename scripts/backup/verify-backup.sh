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
