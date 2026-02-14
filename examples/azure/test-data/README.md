# Azure Deployment Test Data

Synthetic DICOM data for testing Azure deployments.

## Contents

- **sample-study/** - A complete study with multiple series
  - Study: Chest CT
  - Patient: TEST^PATIENT^001 (synthetic)
  - Series 1: Axial CT (10 images)
  - Series 2: Coronal CT (10 images)
  - Total: 20 DICOM files

## Generating Test Data

### Using DICOM Toolkit (dcmtk)

```bash
# Install dcmtk
brew install dcmtk  # macOS
# or
apt-get install dcmtk  # Ubuntu

# Generate synthetic CT images
cd examples/azure/test-data
./generate-test-data.sh
```

### Using Python (pydicom)

```bash
# Install pydicom
pip install pydicom numpy pillow

# Generate synthetic DICOM files
python3 generate-synthetic-dicom.py
```

## Uploading Test Data

### To Quickstart Deployment

```bash
# After deploying quickstart
cd examples/azure/quickstart
ORTHANC_URL=$(jq -r '.containerAppUrl' deployment-details.json)
ORTHANC_PASSWORD=$(jq -r '.orthancPassword' deployment-details.json)

# Upload test study
cd ../test-data/sample-study
for file in *.dcm; do
  curl -X POST \
    -u admin:$ORTHANC_PASSWORD \
    --data-binary @$file \
    https://$ORTHANC_URL/instances
done
```

### To Production Deployment

```bash
# After deploying production
cd examples/azure/production
ORTHANC_URL=$(jq -r '.containerAppUrl' deployment-details.json)
ORTHANC_PASSWORD=$(jq -r '.orthancPassword' deployment-details.json)

# Upload test study (same as above)
cd ../test-data/sample-study
for file in *.dcm; do
  curl -X POST \
    -u admin:$ORTHANC_PASSWORD \
    --data-binary @$file \
    https://$ORTHANC_URL/instances
done
```

## Verifying Upload

```bash
# Check studies
curl -u admin:$ORTHANC_PASSWORD https://$ORTHANC_URL/studies

# Check that OAuth forwarding works (requires DICOM service setup)
curl -u admin:$ORTHANC_PASSWORD https://$ORTHANC_URL/dicom-web/studies
```

## Data Specifications

All synthetic data follows DICOM standards:
- Transfer Syntax: Explicit VR Little Endian (1.2.840.10008.1.2.1)
- Patient ID: De-identified (TEST-001, TEST-002, etc.)
- No PHI (Protected Health Information)
- Safe for public repositories

## Cleaning Up Test Data

```bash
# Delete all instances from Orthanc
curl -X DELETE -u admin:$ORTHANC_PASSWORD \
  https://$ORTHANC_URL/instances/{instance-id}

# Or delete entire study
STUDY_ID=$(curl -u admin:$ORTHANC_PASSWORD \
  https://$ORTHANC_URL/studies | jq -r '.[0]')
curl -X DELETE -u admin:$ORTHANC_PASSWORD \
  https://$ORTHANC_URL/studies/$STUDY_ID
```
