# Configuration Templates

Example configurations for various OAuth2 providers.

## Google Cloud Healthcare API

```bash
cp config-templates/google-healthcare-api.json docker/orthanc.json
# Edit to replace {project}, {location}, {dataset}, {dicomstore}
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
```

See [Google Provider Documentation](../docs/PROVIDER-SUPPORT.md#google-cloud-healthcare-api) for details.

## AWS HealthImaging

```bash
cp config-templates/aws-healthimaging.json docker/orthanc.json
# Edit to replace placeholders
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

See [AWS Provider Documentation](../docs/PROVIDER-SUPPORT.md#aws-healthimaging) for details.

## Azure Health Data Services

See main [README.md](../README.md) for Azure configuration examples.
