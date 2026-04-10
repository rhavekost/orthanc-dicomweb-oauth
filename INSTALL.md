# Installing the Orthanc DICOMweb OAuth Plugin

## Requirements

- Orthanc with Python plugin support (`orthanc-python` package installed)
- Python 3.11+
- pip

## Installation Steps

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Copy plugin files to your Orthanc plugins directory

```bash
cp -r src/ /etc/orthanc/plugins/
cp -r schemas/ /etc/orthanc/plugins/
```

The default plugins directory is `/etc/orthanc/plugins/` on Linux.
Check your `orthanc.json` → `"PluginsExplorer"` for the actual path on your system.

### 3. Add to your orthanc.json

```json
{
  "Plugins": [
    "/etc/orthanc/plugins/src/dicomweb_oauth_plugin.py"
  ],
  "DicomWebOAuth": {
    "Servers": {
      "my-cloud-dicom": {
        "Url": "https://dicom.example.com/v2/",
        "TokenEndpoint": "https://login.example.com/oauth2/token",
        "ClientId": "${OAUTH_CLIENT_ID}",
        "ClientSecret": "${OAUTH_CLIENT_SECRET}",
        "Scope": "https://dicom.example.com/.default"
      }
    }
  }
}
```

Set credentials via environment variables before starting Orthanc:

```bash
export OAUTH_CLIENT_ID=your-client-id
export OAUTH_CLIENT_SECRET=your-client-secret
```

### 4. Restart Orthanc

```bash
sudo systemctl restart orthanc
# or: sudo service orthanc restart
```

Verify the plugin loaded:

```bash
curl http://localhost:8042/dicomweb-oauth/status
```

## Upgrading

Re-run steps 1–2 with the new version's files, then restart Orthanc.

## Full Documentation

See the project README at https://github.com/rhavekost/orthanc-dicomweb-oauth for full configuration reference, provider setup guides, and troubleshooting.
