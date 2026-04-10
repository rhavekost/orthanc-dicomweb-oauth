#!/bin/bash
set -e

# Substitute environment variables in orthanc.json
envsubst < /etc/orthanc/orthanc.json.template > /etc/orthanc/orthanc.json

# Start Orthanc with the generated config
exec Orthanc /etc/orthanc/
