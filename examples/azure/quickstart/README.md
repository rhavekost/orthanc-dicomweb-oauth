# Azure Quickstart Deployment

Deploy Orthanc with OAuth plugin to Azure Container Apps with client credentials authentication.

## Overview

- **Platform**: Azure Container Apps
- **Authentication**: OAuth client credentials
- **Networking**: Public endpoints with firewall rules
- **Cost**: ~$66/month
- **Setup Time**: ~15 minutes

## Prerequisites

- Azure subscription
- Azure CLI 2.50+
- Docker (for building custom image)
- Contributor + User Access Administrator role

## Building the Docker Image

**IMPORTANT:** When building for Azure Container Apps (or any cloud service), you MUST specify the target platform:

```bash
# Build for linux/amd64 (required for Azure Container Apps)
docker buildx build --platform linux/amd64 -t <registry>/<image>:<tag> -f examples/azure/quickstart/Dockerfile .

# Note: Build context is repository root (.), not examples/azure/quickstart/
```

**Why this matters:**
- M1/M2/M3 Macs build arm64 images by default
- Azure Container Apps runs on amd64 Linux
- An arm64 image will fail with "ImagePullFailure: not found"

## Documentation

Full documentation coming soon.

## Quick Start

```bash
# 1. Create app registration
./scripts/setup-app-registration.sh

# 2. Configure parameters
cp parameters.json.template parameters.json
# Edit parameters.json with your values

# 3. Deploy
./scripts/deploy.sh --resource-group rg-orthanc-demo --location eastus

# 4. Test
./scripts/test-deployment.sh
```
